"""
Script to quantize the model to float16 to reduce memory usage.
Run this script once to convert the model.

Usage:
    python Dermal/quantize_model.py
"""
import tensorflow as tf
from tensorflow import keras
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "dermatology_stage1.keras")
QUANTIZED_PATH = os.path.join(os.path.dirname(__file__), "dermatology_stage1_fp16.keras")

print(f"Loading model from: {MODEL_PATH}")
model = keras.models.load_model(MODEL_PATH, compile=False)

print(f"Original model size: {os.path.getsize(MODEL_PATH) / (1024*1024):.2f} MB")

# Convert to float16
print("Converting to float16...")
for layer in model.layers:
    if hasattr(layer, 'kernel'):
        layer.kernel = tf.cast(layer.kernel, tf.float16)
    if hasattr(layer, 'bias') and layer.bias is not None:
        layer.bias = tf.cast(layer.bias, tf.float16)

# Save quantized model
print(f"Saving quantized model to: {QUANTIZED_PATH}")
model.save(QUANTIZED_PATH)

print(f"Quantized model size: {os.path.getsize(QUANTIZED_PATH) / (1024*1024):.2f} MB")
print("✅ Quantization complete!")
print(f"\nTo use the quantized model, rename it to 'dermatology_stage1.keras' or update MODEL_PATH in AI_detection.py")
