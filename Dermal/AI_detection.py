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


MODEL_PATH = os.path.join(os.path.dirname(
    __file__), "dermatology_stage1.keras")
IMG_SIZE_DEFAULT = 300
CLASS_NAMES = [
    "Acne and Rosacea Photos",
    "Eczema Photos",
    "Heathy",
    "Psoriasis pictures Lichen Planus and related diseases",
    "Scabies Lyme Disease and other Infestations and Bites",
    "Seborrheic Keratoses and other Benign Tumors",
    "Warts Molluscum and other Viral Infections",
]

# Global variable to hold the model (lazy loaded)
_loaded_model = None
_model_lock = None

# Check if Grad-CAM should be enabled (can be disabled to save memory)
ENABLE_GRADCAM = os.getenv('ENABLE_GRADCAM', 'true').lower() in ('true', '1', 'yes')


def get_model():
    """
    Lazy load the model only when needed.
    This prevents loading the model on import, saving memory.
    """
    global _loaded_model, _model_lock
    
    if _loaded_model is not None:
        return _loaded_model
    
    # Thread lock for thread-safe loading
    if _model_lock is None:
        import threading
        _model_lock = threading.Lock()
    
    with _model_lock:
        # Double-check locking
        if _loaded_model is not None:
            return _loaded_model
        
        print("🔄 Loading model from:", MODEL_PATH)
        
        # Configure TensorFlow for memory efficiency
        # Limit memory growth
        gpus = tf.config.list_physical_devices('GPU')
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        
        # Load model without compilation to save memory
        _loaded_model = keras.models.load_model(MODEL_PATH, compile=False)
        print("✅ Loaded model:", type(_loaded_model),
              "name:", getattr(_loaded_model, "name", None))
        
        # Extract input info
        try:
            orig_input_tensor = _loaded_model.inputs[0]
            orig_dtype = orig_input_tensor.dtype
            orig_shape = orig_input_tensor.shape.as_list()[1:]
            print(f"Model input info: shape={orig_shape}, dtype={orig_dtype}")
        except Exception as e:
            print(f"⚠️ Error extracting input info: {e}")
        
        # Warm up the model with a small input
        try:
            orig_input_tensor = _loaded_model.inputs[0]
            orig_shape = orig_input_tensor.shape.as_list()[1:]
            dummy_input = tf.zeros((1,) + tuple(orig_shape), dtype=orig_input_tensor.dtype)
            _ = _loaded_model(dummy_input, training=False)
            print("✅ Model warmed up")
            del dummy_input
        except Exception as e:
            print(f"⚠️ Warmup failed: {e}")
        
        return _loaded_model


def get_img_size():
    """Get image size from model"""
    model = get_model()
    try:
        orig_shape = model.inputs[0].shape.as_list()[1:]
        return orig_shape[0] if orig_shape[0] else IMG_SIZE_DEFAULT
    except:
        return IMG_SIZE_DEFAULT


def cleanup_memory():
    """Force garbage collection and clear TF session cache"""
    try:
        # Clear Keras backend session
        tf.keras.backend.clear_session()
        # Force garbage collection
        gc.collect()
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")


def pil_to_np(img_pil, img_size):
    """Convert PIL image to numpy array"""
    img = img_pil.resize((img_size, img_size), Image.LANCZOS)
    return np.array(img)


def candidate_preprocessors(np_img, target_dtype):
    """Generate different preprocessing candidates"""
    arr = np_img.astype(np.float32)

    # EfficientNetV2 preprocessing
    try:
        processed = eff_preprocess(arr.copy()).astype(np.float32)
        if hasattr(target_dtype, 'as_numpy_dtype'):
            if target_dtype.as_numpy_dtype == np.float16:
                processed = processed.astype(np.float16)
        yield "efficientnet_v2_preprocess", np.expand_dims(processed, axis=0)
    except Exception as e:
        print(f"  ⚠️ efficientnet_v2_preprocess failed: {e}")

    # Simple normalization
    try:
        processed = (arr / 255.0).astype(np.float32)
        if hasattr(target_dtype, 'as_numpy_dtype'):
            if target_dtype.as_numpy_dtype == np.float16:
                processed = processed.astype(np.float16)
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

            # Recursively search nested models
            if isinstance(layer, tf.keras.Model):
                search_layers(layer, layer_path)

    search_layers(model)

    # For EfficientNet, also check for specific layer names
    if target_layer_name is None:
        for layer in model.layers:
            if 'top_conv' in layer.name or 'block7' in layer.name or 'block6' in layer.name:
                target_layer_name = layer.name
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
    Optimized Grad-CAM computation with memory efficiency
    Uses mixed precision and aggressive cleanup to minimize RAM usage
    """
    model_input_dtype = model.inputs[0].dtype

    # Convert to tensor once with reduced precision if possible
    x = tf.convert_to_tensor(batch_np, dtype=model_input_dtype)
    
    # Enable memory growth for GPU if available
    try:
        gpus = tf.config.list_physical_devices('GPU')
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except:
        pass

    # Find the target layer recursively
    target_layer = get_layer_by_name(model, target_layer_name)

    if target_layer is None:
        raise RuntimeError(
            f"Could not find layer '{target_layer_name}' in model")

    print(f"  ✅ Target: {target_layer.name}")

    # Use non-persistent tape (faster and less memory)
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
        with tf.GradientTape() as tape:
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

    if grads is None:
        raise RuntimeError("Gradients are None!")

    # Optimize heatmap computation - use reduce_mean instead of complex ops
    # Convert to numpy early to free TF memory
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2)).numpy()
    conv_outputs_np = conv_outputs[0].numpy()
    
    # Free TF tensors immediately
    del grads, conv_outputs
    
    # Compute heatmap in numpy (less memory than TF)
    heatmap = np.sum(conv_outputs_np * pooled_grads, axis=-1)
    del conv_outputs_np, pooled_grads
    
    # ReLU + normalize
    heatmap = np.maximum(heatmap, 0)
    heatmap_max = np.max(heatmap)

    if heatmap_max > 1e-10:
        heatmap = heatmap / heatmap_max
    else:
        # Fallback: use absolute values
        heatmap = np.abs(heatmap)
        heatmap_max = np.max(heatmap)
        if heatmap_max > 1e-10:
            heatmap = heatmap / heatmap_max

    preds_np = predictions.numpy()
    
    # Clean up tensors
    del x, predictions
    
    return heatmap, preds_np


def predict_skin_with_explanation(image_bytes, top_k=7, enable_gradcam=None):
    """
    Predict skin condition with optional Grad-CAM explanation
    
    Args:
        image_bytes: Image data in bytes
        top_k: Number of top predictions to return
        enable_gradcam: Override ENABLE_GRADCAM setting (True/False/None for default)
    """
    start_time = time.time()
    
    # Determine if Grad-CAM should be enabled
    if enable_gradcam is None:
        enable_gradcam = ENABLE_GRADCAM
    
    # Get model (lazy loaded)
    model = get_model()
    img_size = get_img_size()

    # Load image
    pil = None
    np_img = None
    try:
        with Image.open(io.BytesIO(image_bytes)) as pil_temp:
            pil = pil_temp.convert("RGB")
            np_img = pil_to_np(pil, img_size)
    except Exception as e:
        print(f"❌ Error loading image: {e}")
        raise

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

    # Generate Grad-CAM only if enabled
    heatmap_base64 = None
    if enable_gradcam:
        target_layer_name = find_target_layer_for_gradcam(model)
        
        if target_layer_name is not None:
            try:
                print("\n🔥 Computing Grad-CAM...")
                heatmap, _ = compute_gradcam_manual(
                    chosen_batch, model, target_layer_name
                )

                print(f"  🔍 Heatmap shape: {heatmap.shape}")
                print(
                    f"  🔍 Heatmap range: [{heatmap.min():.4f}, {heatmap.max():.4f}]")

                # Create visualization
                original_img = pil.resize((img_size, img_size))

                # Resize heatmap
                heatmap_uint8 = np.uint8(255 * heatmap)
                heatmap_img = Image.fromarray(heatmap_uint8).resize(
                    (img_size, img_size), Image.BILINEAR
                )
                heatmap_arr = np.array(heatmap_img) / 255.0

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

                # Encode
                buf = io.BytesIO()
                superimposed.save(buf, format="PNG")
                heatmap_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                print("✅ Grad-CAM generated!")
                
                # Clean up
                del heatmap, heatmap_uint8, heatmap_img, heatmap_arr
                del colored_heatmap, colored_heatmap_uint8, superimposed, buf

            except Exception as e:
                print(f"❌ Grad-CAM failed: {e}")
                traceback.print_exc()
                heatmap_base64 = None
        else:
            print("❌ No suitable layer found for Grad-CAM!")
    else:
        print("ℹ️ Grad-CAM disabled (to save memory)")

    elapsed = time.time() - start_time
    print(
        f"\n⏱️ Time: {elapsed:.2f}s | Method: {chosen_method} | Heatmap: {'✅' if heatmap_base64 else '❌'}\n")

    # Clean up
    del pil, np_img, chosen_batch, preds, preds_vect
    cleanup_memory()

    return results, heatmap_base64


def predict_skin_simple(image_bytes, top_k=7):
    """Simple prediction without explanation (memory efficient)"""
    res, _ = predict_skin_with_explanation(image_bytes, top_k=top_k, enable_gradcam=False)
    return res
