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
from functools import lru_cache


MODEL_PATH = os.path.join(os.path.dirname(__file__), "dermatology_stage1.keras")
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

# Global model cache - only load when needed
_model_cache = None
_model_input_info = None

def get_model():
    """Lazy load model with memory optimization"""
    global _model_cache, _model_input_info
    
    if _model_cache is None:
        print("🔄 Loading model from:", MODEL_PATH)
        
        # Configure TensorFlow for memory efficiency
        tf.config.experimental.enable_memory_growth = True
        
        # Load model with memory optimization
        _model_cache = keras.models.load_model(MODEL_PATH, compile=False)
        
        # Extract input info once
        try:
            orig_input_tensor = _model_cache.inputs[0]
            orig_dtype = orig_input_tensor.dtype
            orig_shape = orig_input_tensor.shape.as_list()[1:]
            _model_input_info = {
                'shape': orig_shape,
                'dtype': orig_dtype,
                'img_size': orig_shape[0] if orig_shape[0] else IMG_SIZE_DEFAULT
            }
            print(f"Model input info: shape={orig_shape}, dtype={orig_dtype}")
        except Exception as e:
            print(f"⚠️ Error extracting input info: {e}")
            _model_input_info = {
                'shape': [IMG_SIZE_DEFAULT, IMG_SIZE_DEFAULT, 3],
                'dtype': tf.float32,
                'img_size': IMG_SIZE_DEFAULT
            }
        
        # Warm up with smaller dummy input
        dummy_input = tf.zeros((1,) + tuple(_model_input_info['shape']), dtype=_model_input_info['dtype'])
        _ = _model_cache(dummy_input, training=False)
        print("✅ Model loaded and warmed up")
        
        # Clean up
        del dummy_input
        gc.collect()
    
    return _model_cache, _model_input_info

def clear_model_cache():
    """Clear model from memory when not needed"""
    global _model_cache, _model_input_info
    if _model_cache is not None:
        del _model_cache
        _model_cache = None
        _model_input_info = None
        gc.collect()
        print("🗑️ Model cache cleared")

@lru_cache(maxsize=32)
def pil_to_np_cached(img_bytes_hash, img_size):
    """Cached image preprocessing to avoid recomputation"""
    return True  # Just for cache key, actual processing done separately

def pil_to_np(img_pil, img_size):
    """Convert PIL image to numpy array with memory optimization"""
    # Use LANCZOS for better quality but consider BILINEAR for speed
    img = img_pil.resize((img_size, img_size), Image.LANCZOS)
    arr = np.array(img, dtype=np.uint8)  # Keep as uint8 initially
    return arr

def optimized_preprocess(np_img, target_dtype, img_size):
    """Memory-optimized preprocessing"""
    # Convert to float32 only when needed
    arr = np_img.astype(np.float32)
    
    # EfficientNetV2 preprocessing (preferred)
    try:
        processed = eff_preprocess(arr)
        
        # Convert to target dtype if needed
        if hasattr(target_dtype, 'as_numpy_dtype'):
            if target_dtype.as_numpy_dtype == np.float16:
                processed = processed.astype(np.float16)
        
        return np.expand_dims(processed, axis=0)
    except Exception as e:
        print(f"⚠️ EfficientNet preprocessing failed: {e}")
        # Fallback to simple normalization
        processed = arr / 255.0
        if hasattr(target_dtype, 'as_numpy_dtype'):
            if target_dtype.as_numpy_dtype == np.float16:
                processed = processed.astype(np.float16)
        return np.expand_dims(processed, axis=0)

def find_target_layer_for_gradcam_optimized(model):
    """Optimized layer search for Grad-CAM"""
    target_layer_name = None
    
    # First check for common EfficientNet layer names (faster)
    efficient_net_layers = ['top_conv', 'block7', 'block6', 'block5']
    for layer_name in efficient_net_layers:
        for layer in model.layers:
            if layer_name in layer.name:
                return layer.name
    
    # Fallback to general search
    def search_layers(m):
        nonlocal target_layer_name
        for layer in reversed(m.layers):  # Start from end for better layers
            if isinstance(layer, (Conv2D, DepthwiseConv2D, SeparableConv2D)):
                target_layer_name = layer.name
                return target_layer_name
            if isinstance(layer, tf.keras.Model):
                result = search_layers(layer)
                if result:
                    return result
        return target_layer_name
    
    return search_layers(model)

def get_layer_by_name_optimized(model, layer_name):
    """Optimized layer search with caching"""
    # Use a simple cache for layer lookups
    if not hasattr(get_layer_by_name_optimized, '_layer_cache'):
        get_layer_by_name_optimized._layer_cache = {}
    
    cache_key = f"{id(model)}_{layer_name}"
    if cache_key in get_layer_by_name_optimized._layer_cache:
        return get_layer_by_name_optimized._layer_cache[cache_key]
    
    def find_layer(m):
        for layer in m.layers:
            if layer.name == layer_name:
                return layer
            if isinstance(layer, tf.keras.Model):
                found = find_layer(layer)
                if found is not None:
                    return found
        return None
    
    result = find_layer(model)
    get_layer_by_name_optimized._layer_cache[cache_key] = result
    return result

def compute_gradcam_optimized(batch_np, model, target_layer_name, pred_index=None):
    """
    Memory-optimized Grad-CAM computation
    """
    model_input_dtype = model.inputs[0].dtype
    
    # Convert to tensor with memory optimization
    x = tf.convert_to_tensor(batch_np, dtype=model_input_dtype)
    
    # Find target layer
    target_layer = get_layer_by_name_optimized(model, target_layer_name)
    if target_layer is None:
        raise RuntimeError(f"Could not find layer '{target_layer_name}' in model")
    
    print(f"  ✅ Target: {target_layer.name}")
    
    # Use context manager for automatic cleanup
    conv_outputs = None
    original_call = target_layer.call
    
    def wrapped_call(inputs, *args, **kwargs):
        output = original_call(inputs, *args, **kwargs)
        nonlocal conv_outputs
        conv_outputs = output
        return output
    
    target_layer.call = wrapped_call
    
    try:
        # Use tf.function for better performance
        @tf.function
        def forward_pass(x_input):
            with tf.GradientTape() as tape:
                tape.watch(x_input)
                predictions = model(x_input, training=False)
                return predictions, tape
        
        predictions, tape = forward_pass(x)
        
        if conv_outputs is None:
            raise RuntimeError(f"Failed to capture {target_layer_name}")
        
        # Get target class
        if pred_index is None:
            pred_index = tf.argmax(predictions[0])
        
        class_channel = predictions[0, pred_index]
        
        # Compute gradients
        grads = tape.gradient(class_channel, conv_outputs)
        
    finally:
        # Always restore
        target_layer.call = original_call
    
    if grads is None:
        raise RuntimeError("Gradients are None!")
    
    # Optimized heatmap computation
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    heatmap = tf.reduce_sum(conv_outputs[0] * pooled_grads, axis=-1)
    
    # Normalize
    heatmap = tf.maximum(heatmap, 0)
    heatmap_max = tf.reduce_max(heatmap)
    
    if heatmap_max > 1e-10:
        heatmap = heatmap / heatmap_max
    else:
        heatmap = tf.abs(heatmap)
        heatmap_max = tf.reduce_max(heatmap)
        if heatmap_max > 1e-10:
            heatmap = heatmap / heatmap_max
    
    print(f"  ✅ Heatmap computed: {heatmap.shape}")
    
    # Convert to numpy and clean up
    heatmap_np = heatmap.numpy()
    predictions_np = predictions.numpy()
    
    # Clean up tensors
    del x, predictions, grads, conv_outputs, heatmap
    gc.collect()
    
    return heatmap_np, predictions_np

def predict_skin_with_explanation_optimized(image_bytes, top_k=7, enable_gradcam=True):
    """
    Memory-optimized prediction with optional Grad-CAM
    """
    start_time = time.time()
    
    try:
        # Get model (lazy loading)
        model, model_info = get_model()
        img_size = model_info['img_size']
        
        # Load and preprocess image
        with Image.open(io.BytesIO(image_bytes)) as pil:
            pil = pil.convert("RGB")
            np_img = pil_to_np(pil, img_size)
        
        # Preprocess for prediction
        batch = optimized_preprocess(np_img, model_info['dtype'], img_size)
        
        # Make prediction
        preds = model(batch, training=False).numpy()
        
        # Format results
        preds_vect = preds[0]
        results = [
            {
                "class": (CLASS_NAMES[i] if i < len(CLASS_NAMES) else f"class_{i}"),
                "probability": float(preds_vect[i]) * 100,
            }
            for i in range(len(preds_vect))
        ]
        results = sorted(results, key=lambda x: x["probability"], reverse=True)[:top_k]
        
        print(f"\n📊 Top prediction: {results[0]['class']} ({results[0]['probability']:.2f}%)")
        
        # Generate Grad-CAM only if requested and memory allows
        heatmap_base64 = None
        if enable_gradcam:
            try:
                print("\n🔥 Computing Grad-CAM...")
                target_layer_name = find_target_layer_for_gradcam_optimized(model)
                
                if target_layer_name:
                    heatmap, _ = compute_gradcam_optimized(batch, model, target_layer_name)
                    
                    # Create visualization with memory optimization
                    original_img = pil.resize((img_size, img_size))
                    
                    # Resize heatmap efficiently
                    heatmap_resized = tf.image.resize(
                        tf.expand_dims(heatmap, -1), 
                        [img_size, img_size], 
                        method='bilinear'
                    ).numpy().squeeze()
                    
                    # Apply colormap
                    colormap = cm.get_cmap("jet")
                    colored_heatmap = colormap(heatmap_resized)[:, :, :3]
                    colored_heatmap_uint8 = np.uint8(255 * colored_heatmap)
                    
                    # Blend images
                    superimposed = Image.blend(
                        original_img.convert("RGBA"),
                        Image.fromarray(colored_heatmap_uint8).convert("RGBA"),
                        alpha=0.4,
                    )
                    
                    # Encode to base64
                    buf = io.BytesIO()
                    superimposed.save(buf, format="PNG", optimize=True, quality=85)
                    heatmap_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                    
                    print("✅ Grad-CAM generated!")
                    
                    # Clean up
                    del heatmap, heatmap_resized, colored_heatmap, superimposed
                    gc.collect()
                    
            except Exception as e:
                print(f"❌ Grad-CAM failed: {e}")
                heatmap_base64 = None
        
        elapsed = time.time() - start_time
        print(f"\n⏱️ Time: {elapsed:.2f}s | Heatmap: {'✅' if heatmap_base64 else '❌'}\n")
        
        # Clean up
        del batch, preds
        gc.collect()
        
        return results, heatmap_base64
        
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        traceback.print_exc()
        # Clear model cache on error to free memory
        clear_model_cache()
        raise

def predict_skin_simple_optimized(image_bytes, top_k=7):
    """Simple prediction without Grad-CAM to save memory"""
    return predict_skin_with_explanation_optimized(image_bytes, top_k=top_k, enable_gradcam=False)

# Compatibility functions for existing code
def predict_skin_with_explanation(image_bytes, top_k=7):
    """Wrapper for backward compatibility"""
    return predict_skin_with_explanation_optimized(image_bytes, top_k, enable_gradcam=True)

def predict_skin_simple(image_bytes, top_k=7):
    """Wrapper for backward compatibility"""
    return predict_skin_simple_optimized(image_bytes, top_k)