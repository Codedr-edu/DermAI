#!/usr/bin/env python3
"""
Script để test memory usage của model AI
"""
import os
import sys
import psutil
import gc
import time

# Add project root to path
sys.path.append('/workspace')

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process()
    memory_info = process.memory_info()
    return memory_info.rss / 1024 / 1024

def test_model_loading():
    """Test memory usage khi load model"""
    print("🧪 Testing model loading...")
    
    initial_memory = get_memory_usage()
    print(f"📊 Initial memory: {initial_memory:.2f} MB")
    
    try:
        # Import và load model
        from Dermal.AI_detection import get_model, predict_skin_simple
        
        after_import_memory = get_memory_usage()
        print(f"📊 After import: {after_import_memory:.2f} MB (+{after_import_memory - initial_memory:.2f} MB)")
        
        # Load model
        model = get_model()
        after_model_memory = get_memory_usage()
        print(f"📊 After model load: {after_model_memory:.2f} MB (+{after_model_memory - after_import_memory:.2f} MB)")
        
        # Test prediction với ảnh mẫu
        print("\n🧪 Testing prediction...")
        
        # Tạo ảnh test đơn giản
        from PIL import Image
        import io
        
        # Tạo ảnh test 224x224
        test_img = Image.new('RGB', (224, 224), color='red')
        img_buffer = io.BytesIO()
        test_img.save(img_buffer, format='JPEG')
        img_bytes = img_buffer.getvalue()
        
        # Test prediction
        start_time = time.time()
        results = predict_skin_simple(img_bytes)
        prediction_time = time.time() - start_time
        
        after_prediction_memory = get_memory_usage()
        print(f"📊 After prediction: {after_prediction_memory:.2f} MB (+{after_prediction_memory - after_model_memory:.2f} MB)")
        print(f"⏱️ Prediction time: {prediction_time:.2f}s")
        print(f"📋 Results: {results[0] if results else 'No results'}")
        
        # Cleanup
        del model, test_img, img_buffer, img_bytes, results
        gc.collect()
        
        final_memory = get_memory_usage()
        print(f"📊 After cleanup: {final_memory:.2f} MB")
        
        return {
            'initial': initial_memory,
            'after_import': after_import_memory,
            'after_model': after_model_memory,
            'after_prediction': after_prediction_memory,
            'final': final_memory,
            'prediction_time': prediction_time
        }
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Starting memory test...")
    print(f"🐍 Python version: {sys.version}")
    print(f"💾 Available memory: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f} GB")
    print(f"💾 Available memory: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.2f} GB")
    print("-" * 50)
    
    results = test_model_loading()
    
    if results:
        print("\n📊 Memory Test Summary:")
        print(f"  Initial: {results['initial']:.2f} MB")
        print(f"  Model load overhead: {results['after_model'] - results['initial']:.2f} MB")
        print(f"  Prediction overhead: {results['after_prediction'] - results['after_model']:.2f} MB")
        print(f"  Memory after cleanup: {results['final']:.2f} MB")
        print(f"  Prediction time: {results['prediction_time']:.2f}s")
        
        # Check if memory usage is reasonable
        if results['final'] > 500:  # 500MB threshold
            print("⚠️ WARNING: High memory usage detected!")
        else:
            print("✅ Memory usage looks good!")