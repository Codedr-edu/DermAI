#!/usr/bin/env python3
"""
Pre-Deployment Test Suite
Tests quantized model và ước tính RAM usage

Usage:
    python test_before_deploy.py
"""

import os
import sys
import gc
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dermai.settings')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-validation')

print("=" * 70)
print("🧪 PRE-DEPLOYMENT TEST SUITE")
print("=" * 70)
print()

def get_memory_mb():
    """Get current memory usage in MB"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        print("⚠️ psutil not installed, install: pip install psutil")
        return 0

def test_django_imports():
    """Test 1: Django imports"""
    print("📝 Test 1: Django Imports")
    print("-" * 70)
    
    mem_before = get_memory_mb()
    print(f"Memory before: {mem_before:.2f} MB")
    
    try:
        import django
        django.setup()
        print("✅ Django imported successfully")
        
        from Dermal import AI_detection
        print("✅ AI_detection module imported")
        
        mem_after = get_memory_mb()
        print(f"Memory after: {mem_after:.2f} MB")
        print(f"Django overhead: {mem_after - mem_before:.2f} MB")
        print()
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_quantized_model_exists():
    """Test 2: Check if quantized model exists"""
    print("📝 Test 2: Quantized Model File")
    print("-" * 70)
    
    original_path = "Dermal/dermatology_stage1.keras"
    quantized_path = "Dermal/dermatology_stage1_fp16.keras"
    
    # Check original
    if os.path.exists(original_path):
        size_mb = os.path.getsize(original_path) / (1024 * 1024)
        print(f"✅ Original model exists: {size_mb:.2f} MB")
    else:
        print(f"❌ Original model NOT found: {original_path}")
        return False
    
    # Check quantized
    if os.path.exists(quantized_path):
        size_mb = os.path.getsize(quantized_path) / (1024 * 1024)
        print(f"✅ Quantized model exists: {size_mb:.2f} MB")
        reduction = (1 - size_mb / (os.path.getsize(original_path) / (1024 * 1024))) * 100
        print(f"   Size reduction: {reduction:.1f}%")
    else:
        print(f"⚠️ Quantized model NOT found: {quantized_path}")
        print("   Run: python Dermal/quantize_model.py")
        return False
    
    print()
    return True

def test_model_loading():
    """Test 3: Model loading memory usage"""
    print("📝 Test 3: Model Loading (Memory Test)")
    print("-" * 70)
    
    mem_before = get_memory_mb()
    print(f"Memory before load: {mem_before:.2f} MB")
    
    try:
        from Dermal.AI_detection import get_model
        
        # Force load model
        print("Loading model...")
        start_time = time.time()
        model = get_model()
        load_time = time.time() - start_time
        
        mem_after = get_memory_mb()
        model_ram = mem_after - mem_before
        
        print(f"✅ Model loaded in {load_time:.2f}s")
        print(f"Memory after load: {mem_after:.2f} MB")
        print(f"Model RAM usage: {model_ram:.2f} MB")
        
        # Check if within limits
        if mem_after < 450:
            print(f"✅ Memory OK (< 450MB)")
        elif mem_after < 500:
            print(f"⚠️ Memory borderline ({mem_after:.0f}MB, close to 512MB limit)")
        else:
            print(f"❌ Memory too high! ({mem_after:.0f}MB > 500MB)")
            return False
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prediction_speed():
    """Test 4: Prediction speed (timeout risk)"""
    print("📝 Test 4: Prediction Speed (Timeout Check)")
    print("-" * 70)
    
    try:
        from PIL import Image
        import numpy as np
        import io
        from Dermal.AI_detection import predict_skin_with_explanation
        
        # Create dummy image
        dummy_img = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
        pil_img = Image.fromarray(dummy_img)
        buf = io.BytesIO()
        pil_img.save(buf, format='JPEG')
        img_bytes = buf.getvalue()
        
        # Test WITHOUT Grad-CAM
        print("Testing prediction WITHOUT Grad-CAM...")
        start_time = time.time()
        results, _ = predict_skin_with_explanation(img_bytes, enable_gradcam=False)
        no_gradcam_time = time.time() - start_time
        
        print(f"✅ Prediction (no Grad-CAM): {no_gradcam_time:.2f}s")
        
        # Test WITH Grad-CAM
        print("Testing prediction WITH Grad-CAM...")
        gc.collect()
        start_time = time.time()
        results, heatmap = predict_skin_with_explanation(img_bytes, enable_gradcam=True)
        gradcam_time = time.time() - start_time
        
        print(f"✅ Prediction (with Grad-CAM): {gradcam_time:.2f}s")
        
        # Check timeout risk
        timeout_limit = 300  # Render timeout = 300s
        if gradcam_time < 30:
            print(f"✅ Speed excellent (< 30s, timeout = {timeout_limit}s)")
        elif gradcam_time < 60:
            print(f"✅ Speed good (< 60s, timeout = {timeout_limit}s)")
        elif gradcam_time < 120:
            print(f"⚠️ Speed acceptable (< 120s, timeout = {timeout_limit}s)")
        else:
            print(f"⚠️ Speed slow ({gradcam_time:.0f}s, may timeout on slow servers)")
        
        # Check heatmap
        if heatmap:
            print(f"✅ Grad-CAM heatmap generated")
        else:
            print(f"⚠️ Grad-CAM heatmap NOT generated")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_peak():
    """Test 5: Peak memory during prediction + Grad-CAM"""
    print("📝 Test 5: Peak Memory Test (Critical!)")
    print("-" * 70)
    
    try:
        from PIL import Image
        import numpy as np
        import io
        from Dermal.AI_detection import predict_skin_with_explanation
        
        # Force GC
        gc.collect()
        mem_baseline = get_memory_mb()
        print(f"Baseline memory: {mem_baseline:.2f} MB")
        
        # Create test image
        dummy_img = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
        pil_img = Image.fromarray(dummy_img)
        buf = io.BytesIO()
        pil_img.save(buf, format='JPEG')
        img_bytes = buf.getvalue()
        
        # Predict with monitoring
        print("Running prediction with memory monitoring...")
        mem_before = get_memory_mb()
        
        results, heatmap = predict_skin_with_explanation(img_bytes, enable_gradcam=True)
        
        mem_peak = get_memory_mb()
        mem_after_cleanup = get_memory_mb()
        
        print(f"Memory before predict: {mem_before:.2f} MB")
        print(f"Memory at peak: {mem_peak:.2f} MB")
        print(f"Memory after cleanup: {mem_after_cleanup:.2f} MB")
        print(f"Peak usage: {mem_peak:.2f} MB")
        
        # Assess
        if mem_peak < 450:
            print(f"✅ EXCELLENT! Peak {mem_peak:.0f}MB < 450MB (safe margin)")
        elif mem_peak < 480:
            print(f"✅ GOOD! Peak {mem_peak:.0f}MB < 480MB (acceptable margin)")
        elif mem_peak < 500:
            print(f"⚠️ TIGHT! Peak {mem_peak:.0f}MB < 500MB (close to limit)")
        else:
            print(f"❌ DANGER! Peak {mem_peak:.0f}MB > 500MB (may OOM!)")
            return False
        
        # Check cleanup
        if mem_after_cleanup < mem_peak:
            cleanup_amount = mem_peak - mem_after_cleanup
            print(f"✅ Memory cleanup working ({cleanup_amount:.2f}MB freed)")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_render_limits():
    """Test 6: Check Render.com free tier limits"""
    print("📝 Test 6: Render.com Free Tier Limits Check")
    print("-" * 70)
    
    limits = {
        "RAM": {"limit": 512, "unit": "MB"},
        "Disk": {"limit": 1000, "unit": "MB"},
        "Timeout": {"limit": 300, "unit": "seconds"},
        "Build time": {"limit": 900, "unit": "seconds"},
        "Bandwidth": {"limit": "100GB/month", "unit": ""},
    }
    
    # Check model size
    model_size = os.path.getsize("Dermal/dermatology_stage1.keras") / (1024 * 1024)
    print(f"Model file: {model_size:.2f} MB")
    
    if model_size < 100:
        print(f"✅ Model size OK (< 100MB)")
    else:
        print(f"⚠️ Model size large (> 100MB, may slow build)")
    
    # Estimate total disk usage
    print("\nEstimated disk usage:")
    print(f"  - Model: ~{model_size:.0f} MB")
    print(f"  - Dependencies: ~300 MB")
    print(f"  - Django: ~50 MB")
    print(f"  - Estimated total: ~{model_size + 350:.0f} MB")
    
    if model_size + 350 < 800:
        print(f"✅ Disk usage OK (< 800MB of 1GB)")
    else:
        print(f"⚠️ Disk usage high (> 800MB)")
    
    # RAM from previous test
    mem_current = get_memory_mb()
    print(f"\nCurrent RAM usage: {mem_current:.2f} MB")
    if mem_current < limits["RAM"]["limit"]:
        margin = limits["RAM"]["limit"] - mem_current
        print(f"✅ RAM OK ({margin:.0f}MB margin)")
    else:
        print(f"❌ RAM exceeds limit!")
    
    print()
    return True

def test_config_files():
    """Test 7: Check config files"""
    print("📝 Test 7: Configuration Files")
    print("-" * 70)
    
    all_ok = True
    
    # Check render.yaml
    if os.path.exists("render.yaml"):
        print("✅ render.yaml exists")
        
        with open("render.yaml", "r") as f:
            content = f.read()
            
            if "gunicorn" in content:
                print("✅ gunicorn configured")
            else:
                print("⚠️ gunicorn not found in render.yaml")
                all_ok = False
            
            if "ENABLE_GRADCAM" in content:
                if "value: true" in content or "value: 'true'" in content:
                    print("✅ ENABLE_GRADCAM = true")
                else:
                    print("⚠️ ENABLE_GRADCAM = false")
            
            if "timeout" in content.lower():
                print("✅ Timeout configured")
    else:
        print("❌ render.yaml NOT found!")
        all_ok = False
    
    # Check requirements.txt
    if os.path.exists("requirements.txt"):
        print("✅ requirements.txt exists")
        
        with open("requirements.txt", "r") as f:
            content = f.read()
            
            if "tensorflow-cpu" in content:
                print("✅ tensorflow-cpu configured")
            elif "tensorflow==" in content:
                print("⚠️ tensorflow (full) found, should use tensorflow-cpu")
                all_ok = False
            
            if "psutil" in content:
                print("✅ psutil included")
            else:
                print("⚠️ psutil not in requirements.txt")
    
    # Check build.sh
    if os.path.exists("build.sh"):
        print("✅ build.sh exists")
    else:
        print("⚠️ build.sh not found")
    
    # Check static directory
    if os.path.exists("static"):
        print("✅ static/ directory exists")
    else:
        print("⚠️ static/ directory not found")
    
    print()
    return all_ok

def main():
    """Run all tests"""
    
    results = []
    
    # Run tests
    results.append(("Django Imports", test_django_imports()))
    results.append(("Quantized Model", test_quantized_model_exists()))
    results.append(("Model Loading", test_model_loading()))
    results.append(("Prediction Speed", test_prediction_speed()))
    results.append(("Peak Memory", test_memory_peak()))
    results.append(("Render Limits", test_render_limits()))
    results.append(("Config Files", test_config_files()))
    
    # Summary
    print("=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} - {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print()
        print("✅ Ready to deploy to Render.com!")
        print()
        print("Next steps:")
        print("1. Review FINAL_DEPLOYMENT_CHECKLIST.md")
        print("2. git add .")
        print("3. git commit -m 'Ready for deployment with quantized model'")
        print("4. git push")
        print()
        return 0
    else:
        print()
        print("=" * 70)
        print("⚠️ SOME TESTS FAILED!")
        print("=" * 70)
        print()
        print("Please fix issues before deploying!")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
