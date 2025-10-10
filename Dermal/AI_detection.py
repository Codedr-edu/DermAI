import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.applications.efficientnet_v2 import preprocess_input as eff_preprocess
from tensorflow.keras.layers import Conv2D, DepthwiseConv2D, SeparableConv2D
from PIL import Image
import io
import os
import base64
import matplotlib.cm as cm
import time
import traceback
import gc
import psutil

# Import TensorFlow configuration
try:
    from tensorflow_config import configure_tensorflow
    configure_tensorflow()
except ImportError:
    print("⚠️ tensorflow_config not found, using default TensorFlow settings")

MODEL_PATH = os.path.join(os.path.dirname(
    __file__), "dermatology_stage1.keras")
IMG_SIZE_DEFAULT = 224  # Giảm từ 300 xuống 224 để tiết kiệm memory
CLASS_NAMES = [
    "Acne and Rosacea Photos",
    "Eczema Photos",
    "Heathy",
    "Psoriasis pictures Lichen Planus and related diseases",
    "Scabies Lyme Disease and other Infestations and Bites",
    "Seborrheic Keratoses and other Benign Tumors",
    "Warts Molluscum and other Viral Infections",
]

# Lazy loading - chỉ load model khi cần thiết
_loaded_model = None
_orig_shape = None
_orig_dtype = None
IMG_SIZE = IMG_SIZE_DEFAULT

def get_model():
    """Lazy load model để tiết kiệm memory"""
    global _loaded_model, _orig_shape, _orig_dtype, IMG_SIZE
    
    if _loaded_model is None:
        print("🔄 Loading model from:", MODEL_PATH)
        
        # Cấu hình TensorFlow để tiết kiệm memory
        tf.config.experimental.set_memory_growth(tf.config.list_physical_devices('GPU')[0], True) if tf.config.list_physical_devices('GPU') else None
        
        # Load model với compile=False để tiết kiệm memory
        _loaded_model = keras.models.load_model(MODEL_PATH, compile=False)
        print("✅ Loaded model:", type(_loaded_model))
        
        # Extract input info
        try:
            orig_input_tensor = _loaded_model.inputs[0]
            _orig_dtype = orig_input_tensor.dtype
            _orig_shape = orig_input_tensor.shape.as_list()[1:]
            print(f"Model input info: shape={_orig_shape}, dtype={_orig_dtype}")
        except Exception as e:
            print(f"⚠️ Error extracting input info: {e}")
            _orig_shape = [IMG_SIZE_DEFAULT, IMG_SIZE_DEFAULT, 3]
            _orig_dtype = tf.float32

        IMG_SIZE = _orig_shape[0] if _orig_shape[0] else IMG_SIZE_DEFAULT
        
        # Warm up model với batch size nhỏ
        dummy_input = tf.zeros((1,) + tuple(_orig_shape), dtype=_orig_dtype)
        _ = _loaded_model(dummy_input, training=False)
        print("✅ Model warmed up")
        
        # Force garbage collection
        gc.collect()
    
    return _loaded_model


def pil_to_np(img_pil, img_size):
    """Convert PIL image to numpy array với tối ưu memory"""
    # Resize với thuật toán nhanh hơn
    img = img_pil.resize((img_size, img_size), Image.BILINEAR)
    return np.array(img, dtype=np.uint8)  # Sử dụng uint8 thay vì float32


def candidate_preprocessors(np_img, target_dtype):
    """Generate different preprocessing candidates với tối ưu memory"""
    # Sử dụng float16 thay vì float32 để tiết kiệm memory
    arr = np_img.astype(np.float16)

    # EfficientNetV2 preprocessing
    try:
        processed = eff_preprocess(arr.copy()).astype(np.float16)
        yield "efficientnet_v2_preprocess", np.expand_dims(processed, axis=0)
    except Exception as e:
        print(f"  ⚠️ efficientnet_v2_preprocess failed: {e}")

    # Simple normalization
    try:
        processed = (arr / 255.0).astype(np.float16)
        yield "div255", np.expand_dims(processed, axis=0)
    except Exception as e:
        print(f"  ⚠️ div255 failed: {e}")


def find_target_layer_for_gradcam(model):
    """
    Find suitable layer for Grad-CAM in EfficientNet models.
    Returns layer name (string) instead of layer object.
    """
    target_layer_name = None

    def search_layers(m, path=""):
        nonlocal target_layer_name
        for layer in m.layers:
            layer_path = f"{path}/{layer.name}" if path else layer.name

            # Look for conv layers
            if isinstance(layer, (Conv2D, DepthwiseConv2D, SeparableConv2D)):
                target_layer_name = layer.name
                print(f"  🔍 Found conv: {layer_path}")

            # Recursively search nested models
            if isinstance(layer, tf.keras.Model):
                search_layers(layer, layer_path)

    search_layers(model)

    # For EfficientNet, also check for specific layer names
    if target_layer_name is None:
        for layer in model.layers:
            if 'top_conv' in layer.name or 'block7' in layer.name or 'block6' in layer.name:
                target_layer_name = layer.name
                print(f"  🔍 Using EfficientNet layer: {layer.name}")
                break

    return target_layer_name


def get_layer_by_name(model, layer_name):
    """Recursively find a layer by name in model (including nested models)"""
    for layer in model.layers:
        if layer.name == layer_name:
            return layer
        if isinstance(layer, tf.keras.Model):
            found = get_layer_by_name(layer, layer_name)
            if found is not None:
                return found
    return None


def compute_gradcam_manual(batch_np, model, target_layer_name, pred_index=None):
    """
    Optimized Grad-CAM computation với memory management
    """
    # Sử dụng mixed precision để tiết kiệm memory
    tf.keras.mixed_precision.set_global_policy('mixed_float16')
    
    model_input_dtype = model.inputs[0].dtype

    # Convert to tensor once với memory optimization
    x = tf.convert_to_tensor(batch_np, dtype=model_input_dtype)

    # Find the target layer recursively
    target_layer = get_layer_by_name(model, target_layer_name)

    if target_layer is None:
        raise RuntimeError(
            f"Could not find layer '{target_layer_name}' in model")

    print(f"  ✅ Target: {target_layer.name}")

    # Use non-persistent tape (faster)
    conv_outputs = None

    # Monkey-patch the target layer
    original_call = target_layer.call

    def wrapped_call(inputs, *args, **kwargs):
        output = original_call(inputs, *args, **kwargs)
        nonlocal conv_outputs
        conv_outputs = output
        return output

    target_layer.call = wrapped_call

    try:
        with tf.GradientTape(persistent=False) as tape:
            tape.watch(x)
            predictions = model(x, training=False)

            if conv_outputs is None:
                raise RuntimeError(f"Failed to capture {target_layer_name}")

            # Get target class and compute loss in one step
            if pred_index is None:
                pred_index = tf.argmax(predictions[0])

            class_channel = predictions[0, pred_index]

        # Compute gradients (this is the slow part on CPU)
        grads = tape.gradient(class_channel, conv_outputs)

    finally:
        # Always restore original method
        target_layer.call = original_call
        # Clean up tape
        del tape

    if grads is None:
        raise RuntimeError("Gradients are None!")

    # Optimize heatmap computation - use einsum instead of matmul
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    heatmap = tf.reduce_sum(conv_outputs[0] * pooled_grads, axis=-1)

    # ReLU + normalize in one pass
    heatmap = tf.maximum(heatmap, 0)
    heatmap_max = tf.reduce_max(heatmap)

    if heatmap_max > 1e-10:
        heatmap = heatmap / heatmap_max
    else:
        # Fallback: use absolute values
        heatmap = tf.abs(heatmap)
        heatmap_max = tf.reduce_max(heatmap)
        if heatmap_max > 1e-10:
            heatmap = heatmap / heatmap_max

    print(f"  ✅ Heatmap computed: {heatmap.shape}")

    # Convert to numpy và cleanup
    heatmap_np = heatmap.numpy()
    predictions_np = predictions.numpy()
    
    # Cleanup tensors
    del x, conv_outputs, grads, pooled_grads, heatmap, predictions
    gc.collect()

    return heatmap_np, predictions_np


def predict_skin_with_explanation(image_bytes, top_k=7):
    """
    Predict skin condition with Grad-CAM explanation - Memory optimized
    """
    start_time = time.time()
    
    # Get model (lazy loading)
    model = get_model()
    
    # Load image với memory optimization
    with Image.open(io.BytesIO(image_bytes)) as pil:
        pil = pil.convert("RGB")
        # Resize ngay để tiết kiệm memory
        pil = pil.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
        np_img = pil_to_np(pil, IMG_SIZE)

    # Find target layer
    print("🔍 Searching for target layer...")
    target_layer_name = find_target_layer_for_gradcam(model)

    if target_layer_name is None:
        print("❌ No suitable layer found for Grad-CAM!")
    else:
        print(f"✅ Target layer: {target_layer_name}")

    # Preprocess
    chosen_method = None
    chosen_batch = None
    preds = None

    for name, batch in candidate_preprocessors(np_img, model.inputs[0].dtype):
        try:
            preds = model(batch, training=False).numpy()
            chosen_method = name
            chosen_batch = batch
            print(f"✅ Preprocessing '{name}' works")
            break
        except Exception as e:
            print(f"  ❌ '{name}' failed: {e}")

    if preds is None:
        raise RuntimeError("All preprocessing failed")

    # Format results
    preds_vect = preds[0]
    results = [
        {
            "class": (CLASS_NAMES[i] if i < len(CLASS_NAMES) else f"class_{i}"),
            "probability": float(preds_vect[i]) * 100,
        }
        for i in range(len(preds_vect))
    ]
    results = sorted(results, key=lambda x: x["probability"], reverse=True)[
        :top_k]

    print(
        f"\n📊 Top prediction: {results[0]['class']} ({results[0]['probability']:.2f}%)")

    # Generate Grad-CAM với memory optimization
    heatmap_base64 = None
    if target_layer_name is not None:
        try:
            print("\n🔥 Computing Grad-CAM...")
            heatmap, _ = compute_gradcam_manual(
                chosen_batch, model, target_layer_name
            )

            print(f"  🔍 Heatmap shape: {heatmap.shape}")
            print(
                f"  🔍 Heatmap range: [{heatmap.min():.4f}, {heatmap.max():.4f}]")

            # Create visualization với memory optimization
            original_img = pil  # Đã resize rồi

            # Resize heatmap với thuật toán nhanh
            heatmap_uint8 = np.uint8(255 * heatmap)
            heatmap_img = Image.fromarray(heatmap_uint8).resize(
                (IMG_SIZE, IMG_SIZE), Image.BILINEAR
            )
            heatmap_arr = np.array(heatmap_img, dtype=np.float32) / 255.0

            # Apply colormap
            colormap = cm.get_cmap("jet")
            colored_heatmap = colormap(heatmap_arr)[:, :, :3]
            colored_heatmap_uint8 = np.uint8(255 * colored_heatmap)

            # Blend
            superimposed = Image.blend(
                original_img.convert("RGBA"),
                Image.fromarray(colored_heatmap_uint8).convert("RGBA"),
                alpha=0.4,
            )

            # Encode với compression
            buf = io.BytesIO()
            superimposed.save(buf, format="PNG", optimize=True)
            heatmap_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            print("✅ Grad-CAM generated!")
            
            # Cleanup
            del heatmap, heatmap_uint8, heatmap_img, heatmap_arr, colored_heatmap, colored_heatmap_uint8, superimposed
            buf.close()

        except Exception as e:
            print(f"❌ Grad-CAM failed: {e}")
            traceback.print_exc()
            heatmap_base64 = None

    # Cleanup
    del np_img, chosen_batch, preds, preds_vect
    gc.collect()

    elapsed = time.time() - start_time
    print(
        f"\n⏱️ Time: {elapsed:.2f}s | Method: {chosen_method} | Heatmap: {'✅' if heatmap_base64 else '❌'}\n")

    return results, heatmap_base64


def predict_skin_simple(image_bytes, top_k=7):
    """Simple prediction without explanation - Memory optimized"""
    start_time = time.time()
    
    # Get model (lazy loading)
    model = get_model()
    
    # Load image với memory optimization
    with Image.open(io.BytesIO(image_bytes)) as pil:
        pil = pil.convert("RGB")
        # Resize ngay để tiết kiệm memory
        pil = pil.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
        np_img = pil_to_np(pil, IMG_SIZE)

    # Preprocess
    chosen_method = None
    preds = None

    for name, batch in candidate_preprocessors(np_img, model.inputs[0].dtype):
        try:
            preds = model(batch, training=False).numpy()
            chosen_method = name
            print(f"✅ Preprocessing '{name}' works")
            break
        except Exception as e:
            print(f"  ❌ '{name}' failed: {e}")

    if preds is None:
        raise RuntimeError("All preprocessing failed")

    # Format results
    preds_vect = preds[0]
    results = [
        {
            "class": (CLASS_NAMES[i] if i < len(CLASS_NAMES) else f"class_{i}"),
            "probability": float(preds_vect[i]) * 100,
        }
        for i in range(len(preds_vect))
    ]
    results = sorted(results, key=lambda x: x["probability"], reverse=True)[
        :top_k]

    # Cleanup
    del np_img, preds, preds_vect
    gc.collect()

    elapsed = time.time() - start_time
    print(f"⏱️ Simple prediction time: {elapsed:.2f}s | Method: {chosen_method}")

    return results
