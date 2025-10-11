#!/usr/bin/env python
"""
Test script to verify memory optimizations
Run this before deploying to ensure everything works correctly

Usage:
    python test_memory_optimization.py
"""
import os
import sys
import gc

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dermai.settings')

import django
django.setup()

print("=" * 60)
print("Memory Optimization Test Suite")
print("=" * 60)

def get_memory_mb():
    """Get current memory usage in MB"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        print("⚠️ Install psutil for accurate memory monitoring: pip install psutil")
        return 0

def test_lazy_loading():
    """Test 1: Model should not load on import"""
    print("\n📝 Test 1: Lazy Loading")
    print("-" * 60)
    
    from Dermal import AI_detection
    
    if AI_detection._loaded_model is None:
        print("✅ PASS: Model not loaded on import (lazy loading works)")
        return True
    else:
        print("❌ FAIL: Model loaded on import (lazy loading not working)")
        return False

def test_model_loading():
    """Test 2: Model loads when needed"""
    print("\n📝 Test 2: Model Loading")
    print("-" * 60)
    
    mem_before = get_memory_mb()
    print(f"Memory before loading: {mem_before:.2f} MB")
    
    from Dermal.AI_detection import get_model
    model = get_model()
    
    mem_after = get_memory_mb()
    print(f"Memory after loading: {mem_after:.2f} MB")
    print(f"Model memory: {mem_after - mem_before:.2f} MB")
    
    if model is not None:
        print("✅ PASS: Model loaded successfully")
        return True
    else:
        print("❌ FAIL: Model failed to load")
        return False

def test_prediction():
    """Test 3: Prediction without Grad-CAM"""
    print("\n📝 Test 3: Prediction (no Grad-CAM)")
    print("-" * 60)
    
    from PIL import Image
    import io
    import numpy as np
    from Dermal.AI_detection import predict_skin_with_explanation
    
    # Create a dummy RGB image
    dummy_img = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    pil_img = Image.fromarray(dummy_img)
    
    buf = io.BytesIO()
    pil_img.save(buf, format='JPEG')
    img_bytes = buf.getvalue()
    
    mem_before = get_memory_mb()
    print(f"Memory before prediction: {mem_before:.2f} MB")
    
    try:
        results, heatmap = predict_skin_with_explanation(img_bytes, enable_gradcam=False)
        
        mem_after = get_memory_mb()
        print(f"Memory after prediction: {mem_after:.2f} MB")
        print(f"Prediction overhead: {mem_after - mem_before:.2f} MB")
        
        if results and len(results) > 0:
            print(f"Top prediction: {results[0]['class']} ({results[0]['probability']:.2f}%)")
            print("✅ PASS: Prediction works")
            return True
        else:
            print("❌ FAIL: No predictions returned")
            return False
    except Exception as e:
        print(f"❌ FAIL: Prediction failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gradcam_disabled():
    """Test 4: Grad-CAM can be disabled"""
    print("\n📝 Test 4: Grad-CAM Disabled")
    print("-" * 60)
    
    from PIL import Image
    import io
    import numpy as np
    from Dermal.AI_detection import predict_skin_with_explanation
    
    dummy_img = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    pil_img = Image.fromarray(dummy_img)
    
    buf = io.BytesIO()
    pil_img.save(buf, format='JPEG')
    img_bytes = buf.getvalue()
    
    mem_before = get_memory_mb()
    
    try:
        results, heatmap = predict_skin_with_explanation(img_bytes, enable_gradcam=False)
        
        mem_after = get_memory_mb()
        mem_used = mem_after - mem_before
        
        if heatmap is None:
            print("✅ PASS: Grad-CAM disabled, no heatmap generated")
            print(f"Memory used: {mem_used:.2f} MB")
            return True
        else:
            print("⚠️ WARNING: Heatmap generated even when disabled")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_memory_cleanup():
    """Test 5: Memory cleanup after predictions"""
    print("\n📝 Test 5: Memory Cleanup")
    print("-" * 60)
    
    from PIL import Image
    import io
    import numpy as np
    from Dermal.AI_detection import predict_skin_with_explanation
    
    dummy_img = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    pil_img = Image.fromarray(dummy_img)
    
    buf = io.BytesIO()
    pil_img.save(buf, format='JPEG')
    img_bytes = buf.getvalue()
    
    # Initial memory
    gc.collect()
    mem_initial = get_memory_mb()
    print(f"Initial memory: {mem_initial:.2f} MB")
    
    # Run 3 predictions
    for i in range(3):
        predict_skin_with_explanation(img_bytes, enable_gradcam=False)
    
    # Check memory after
    gc.collect()
    mem_final = get_memory_mb()
    print(f"Final memory: {mem_final:.2f} MB")
    mem_increase = mem_final - mem_initial
    print(f"Memory increase: {mem_increase:.2f} MB")
    
    # Should not increase more than 50MB after 3 predictions
    if mem_increase < 50:
        print("✅ PASS: Memory cleanup working (< 50MB increase)")
        return True
    else:
        print(f"⚠️ WARNING: Memory increased by {mem_increase:.2f} MB (possible leak)")
        return False

def test_env_variables():
    """Test 6: Environment variables"""
    print("\n📝 Test 6: Environment Variables")
    print("-" * 60)
    
    from Dermal import AI_detection
    
    print(f"ENABLE_GRADCAM: {AI_detection.ENABLE_GRADCAM}")
    
    # Check TensorFlow env vars
    tf_vars = [
        'TF_CPP_MIN_LOG_LEVEL',
        'OMP_NUM_THREADS',
        'OPENBLAS_NUM_THREADS',
        'MKL_NUM_THREADS'
    ]
    
    for var in tf_vars:
        value = os.getenv(var, 'not set')
        print(f"{var}: {value}")
    
    print("✅ PASS: Environment variables checked")
    return True

def main():
    """Run all tests"""
    print(f"\nPython: {sys.version}")
    print(f"Django: {django.get_version()}")
    
    try:
        import tensorflow as tf
        print(f"TensorFlow: {tf.__version__}")
    except ImportError:
        print("TensorFlow: not installed")
    
    tests = [
        test_lazy_loading,
        test_model_loading,
        test_prediction,
        test_gradcam_disabled,
        test_memory_cleanup,
        test_env_variables,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Ready to deploy.")
        return 0
    else:
        print(f"⚠️ {total - passed} test(s) failed. Please review.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
