"""
Script to quantize the model to float16 to reduce memory usage.
Run this script once to convert the model.

Usage:
    python Dermal/quantize_model.py
"""
import tensorflow as tf
from tensorflow import keras
import os
import numpy as np
from PIL import Image
import io

MODEL_PATH = os.path.join(os.path.dirname(__file__), "dermatology_stage1.keras")
QUANTIZED_PATH = os.path.join(os.path.dirname(__file__), "dermatology_stage1_fp16.keras")

print("=" * 70)
print("🔧 MODEL QUANTIZATION SCRIPT")
print("=" * 70)
print()

# Check if original model exists
if not os.path.exists(MODEL_PATH):
    print(f"❌ ERROR: Model not found at {MODEL_PATH}")
    exit(1)

print(f"Loading model from: {MODEL_PATH}")
model = keras.models.load_model(MODEL_PATH, compile=False)

original_size = os.path.getsize(MODEL_PATH) / (1024*1024)
print(f"✅ Original model loaded: {original_size:.2f} MB")
print()

# Test prediction with original model
print("🧪 Testing original model...")
try:
    # Create dummy image
    dummy_img = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    pil_img = Image.fromarray(dummy_img)
    buf = io.BytesIO()
    pil_img.save(buf, format='JPEG')
    
    # Simple preprocess
    img = pil_img.resize((300, 300))
    img_array = np.array(img) / 255.0
    img_batch = np.expand_dims(img_array, axis=0).astype(np.float32)
    
    # Predict
    pred_original = model.predict(img_batch, verbose=0)
    print(f"✅ Original model prediction: {pred_original[0][:3]}")
except Exception as e:
    print(f"⚠️ Warning: Could not test original model: {e}")
    pred_original = None
print()

# Convert to float16
print("🔄 Converting weights to float16...")
converted_layers = 0
for layer in model.layers:
    try:
        if hasattr(layer, 'kernel') and layer.kernel is not None:
            layer.kernel = tf.cast(layer.kernel, tf.float16)
            converted_layers += 1
        if hasattr(layer, 'bias') and layer.bias is not None:
            layer.bias = tf.cast(layer.bias, tf.float16)
    except Exception as e:
        # Some layers may not support float16
        print(f"  ⚠️ Could not convert {layer.name}: {e}")
        continue

print(f"✅ Converted {converted_layers} layers to float16")
print()

# Test prediction with quantized model
print("🧪 Testing quantized model...")
try:
    pred_quantized = model.predict(img_batch, verbose=0)
    print(f"✅ Quantized model prediction: {pred_quantized[0][:3]}")
    
    if pred_original is not None:
        # Compare predictions
        diff = np.abs(pred_original - pred_quantized).max()
        print(f"   Max difference: {diff:.6f}")
        
        if diff < 0.01:
            print(f"   ✅ EXCELLENT! Predictions very similar (< 1%)")
        elif diff < 0.05:
            print(f"   ✅ GOOD! Predictions similar (< 5%)")
        else:
            print(f"   ⚠️ WARNING! Predictions differ by {diff*100:.2f}%")
except Exception as e:
    print(f"⚠️ Warning: Could not test quantized model: {e}")
print()

# Save quantized model
print(f"💾 Saving quantized model to: {QUANTIZED_PATH}")
try:
    model.save(QUANTIZED_PATH)
    quantized_size = os.path.getsize(QUANTIZED_PATH) / (1024*1024)
    
    print(f"✅ Quantized model saved!")
    print()
    print("=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    print(f"Original size:   {original_size:.2f} MB")
    print(f"Quantized size:  {quantized_size:.2f} MB")
    print(f"Reduction:       {original_size - quantized_size:.2f} MB ({(1-quantized_size/original_size)*100:.1f}%)")
    print()
    
    # Estimate RAM savings
    ram_original = original_size * 2.4  # Rough estimate: file × 2.4 = RAM
    ram_quantized = quantized_size * 2.4
    print(f"Estimated RAM usage:")
    print(f"  Original:      ~{ram_original:.0f} MB")
    print(f"  Quantized:     ~{ram_quantized:.0f} MB")
    print(f"  RAM savings:   ~{ram_original - ram_quantized:.0f} MB")
    print()
    
    print("=" * 70)
    print("✅ QUANTIZATION COMPLETE!")
    print("=" * 70)
    print()
    print("Next steps:")
    print()
    print("1. TEST the quantized model:")
    print("   python test_before_deploy.py")
    print()
    print("2. If accuracy is acceptable:")
    print("   # Backup original")
    print("   mv Dermal/dermatology_stage1.keras Dermal/dermatology_stage1_original.keras")
    print()
    print("   # Use quantized")
    print("   mv Dermal/dermatology_stage1_fp16.keras Dermal/dermatology_stage1.keras")
    print()
    print("3. Commit and deploy:")
    print("   git add Dermal/dermatology_stage1.keras")
    print("   git commit -m 'Use quantized model for lower memory usage'")
    print("   git push")
    print()
    
except Exception as e:
    print(f"❌ ERROR saving model: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
