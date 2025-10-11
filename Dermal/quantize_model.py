#!/usr/bin/env python3
"""
Quantize TensorFlow model từ FP32 sang FP16

Usage:
    python Dermal/quantize_model.py

Notes:
    - Chỉ nên chạy nếu model > 500MB
    - Model 95MB không cần quantize!
    - Quantization có thể giảm 1-2% accuracy
"""

import tensorflow as tf
import os
import sys

def check_model_dtype(model_path):
    """Check xem model đã quantize chưa"""
    try:
        model = tf.keras.models.load_model(model_path, compile=False)
        
        # Check dtype của layer đầu tiên
        for layer in model.layers:
            if hasattr(layer, 'weights') and layer.weights:
                dtype = layer.weights[0].dtype
                print(f"🔍 Model dtype: {dtype}")
                
                if 'float16' in str(dtype):
                    return 'FP16'
                elif 'float32' in str(dtype):
                    return 'FP32'
                elif 'int8' in str(dtype):
                    return 'INT8'
                break
        
        return 'UNKNOWN'
    except Exception as e:
        print(f"⚠️ Cannot check dtype: {e}")
        return 'UNKNOWN'

def quantize_model(input_path, output_path=None):
    """
    Quantize model using TFLite converter
    
    Args:
        input_path: Path to input model (.keras)
        output_path: Path to output model (.tflite), auto-generated if None
    """
    
    # Validate input
    if not os.path.exists(input_path):
        print(f"❌ Model không tồn tại: {input_path}")
        return False
    
    # Get original size
    original_size_mb = os.path.getsize(input_path) / (1024 * 1024)
    print(f"\n📦 Original model: {original_size_mb:.1f} MB")
    
    # Check dtype
    dtype = check_model_dtype(input_path)
    if dtype == 'FP16':
        print(f"✅ Model đã là FP16 rồi!")
        print(f"   Không cần quantize thêm.")
        return False
    elif dtype == 'INT8':
        print(f"✅ Model đã là INT8 rồi!")
        print(f"   Không cần quantize thêm.")
        return False
    
    # Check if model is small enough
    if original_size_mb < 200:
        print(f"\n✅ Model đã đủ nhỏ ({original_size_mb:.1f} MB < 200 MB)")
        print(f"   Peak memory ước tính: ~{original_size_mb * 3 + 200:.0f} MB")
        
        response = input("\n❓ Vẫn muốn quantize? (y/N): ").strip().lower()
        if response != 'y':
            print("   Bỏ qua quantization.")
            return False
    
    print("\n🔄 Đang quantize model...")
    print("   (Có thể mất vài phút...)")
    
    try:
        # Load model
        print("   Loading model...")
        model = tf.keras.models.load_model(input_path, compile=False)
        
        # Convert to TFLite with FP16 quantization
        print("   Converting to TFLite...")
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        
        # Enable optimizations
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # Use FP16 quantization
        converter.target_spec.supported_types = [tf.float16]
        
        # Convert
        print("   Quantizing...")
        tflite_model = converter.convert()
        
        # Generate output path if not provided
        if output_path is None:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}_quantized.tflite"
        
        # Save
        print(f"   Saving to: {output_path}")
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        # Calculate stats
        quantized_size_mb = len(tflite_model) / (1024 * 1024)
        reduction_percent = (1 - quantized_size_mb / original_size_mb) * 100
        
        print(f"\n✅ Quantization hoàn tất!")
        print(f"📦 Original:  {original_size_mb:.1f} MB (FP32)")
        print(f"📦 Quantized: {quantized_size_mb:.1f} MB (FP16)")
        print(f"📉 Giảm:      {reduction_percent:.1f}%")
        print(f"💾 Output:    {output_path}")
        
        print(f"\n💡 Lưu ý:")
        print(f"   - File .tflite cần dùng TFLite interpreter")
        print(f"   - Có thể giảm 1-2% accuracy")
        print(f"   - Peak memory ước tính: ~{quantized_size_mb * 3 + 200:.0f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Quantization thất bại: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    
    print("=" * 60)
    print("🔢 TENSORFLOW MODEL QUANTIZATION")
    print("=" * 60)
    
    # Default paths
    INPUT_PATH = "Dermal/dermatology_stage1.keras"
    OUTPUT_PATH = "Dermal/dermatology_stage1_quantized.tflite"
    
    # Check if custom path provided
    if len(sys.argv) > 1:
        INPUT_PATH = sys.argv[1]
    
    if len(sys.argv) > 2:
        OUTPUT_PATH = sys.argv[2]
    
    # Run quantization
    success = quantize_model(INPUT_PATH, OUTPUT_PATH)
    
    if success:
        print("\n🎉 Done! Model đã được quantize.")
    else:
        print("\n⚠️ Quantization bị bỏ qua hoặc thất bại.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
