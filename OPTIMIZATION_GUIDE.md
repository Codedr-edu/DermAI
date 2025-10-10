# DermAI Memory Optimization Guide

## Vấn đề gốc
- Model EfficientNetV2-S: 98MB
- Render Free Plan: chỉ 512MB RAM
- TensorFlow + Keras tốn nhiều memory
- Grad-CAM computation tốn thêm memory

## Giải pháp đã implement

### 1. Lazy Loading Model
- Model chỉ load khi cần thiết (không load ngay khi import)
- Cache model để tránh load lại nhiều lần
- Function `clear_model_cache()` để giải phóng memory khi cần

### 2. Memory-Optimized Preprocessing
- Sử dụng `uint8` thay vì `float32` ban đầu
- Chỉ convert sang `float32` khi cần thiết
- LRU cache cho image preprocessing

### 3. Optimized Grad-CAM
- Sử dụng `@tf.function` để tối ưu computation
- Cleanup tensors ngay sau khi dùng
- Option để tắt Grad-CAM khi cần tiết kiệm memory

### 4. TensorFlow Configuration
- Enable memory growth
- Force CPU-only (tránh GPU memory issues)
- Set memory limits

### 5. Dependencies Optimization
- Thay `opencv-python` bằng `opencv-python-headless` (nhẹ hơn)
- Loại bỏ các packages không cần thiết
- Sử dụng `tensorflow-cpu` thay vì `tensorflow`

### 6. Gunicorn Configuration
- Giảm workers: 1 worker thay vì nhiều
- Giảm threads: 2 threads thay vì 4
- Thêm `--max-requests` để restart worker định kỳ
- Sử dụng `--preload` để load app một lần

### 7. Memory Monitoring
- Decorator `@memory_monitor` để track memory usage
- Function `force_cleanup()` để dọn dẹp memory
- Warning khi memory > 400MB

## Cách sử dụng

### Option 1: Sử dụng files tối ưu
```bash
# Copy các file tối ưu
cp requirements_optimized.txt requirements.txt
cp Procfile_optimized Procfile
cp render_optimized.yaml render.yaml
cp build_optimized.sh build.sh
cp dermai/settings_optimized.py dermai/settings.py

# Deploy lên Render
```

### Option 2: Upgrade Render Plan
- Nâng cấp từ Free (512MB) lên Starter (1GB)
- Chi phí: ~$7/tháng
- Đáng giá cho ứng dụng production

### Option 3: Model Optimization
```python
# Trong AI_detection_optimized.py
# Tắt Grad-CAM để tiết kiệm memory
results, _ = predict_skin_with_explanation_optimized(
    image_bytes, 
    enable_gradcam=False  # Tắt Grad-CAM
)
```

## Monitoring Memory

```bash
# Chạy memory monitor
python memory_monitor.py

# Force cleanup memory
python memory_monitor.py cleanup
```

## Expected Results
- Giảm memory usage từ ~600MB xuống ~300-400MB
- Faster startup time
- More stable under load
- Better error handling

## Fallback Options

### Nếu vẫn bị OOM:
1. **Tắt Grad-CAM hoàn toàn**
2. **Sử dụng model nhỏ hơn** (EfficientNet-B0 thay vì B4)
3. **Implement model quantization**
4. **Sử dụng external AI service** (Google Vision API, AWS Rekognition)

### Model Quantization (Advanced):
```python
# Convert model to TensorFlow Lite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

# Save quantized model (sẽ nhỏ hơn 4x)
with open('model_quantized.tflite', 'wb') as f:
    f.write(tflite_model)
```

## Deployment Steps

1. **Test locally first:**
```bash
export DJANGO_SETTINGS_MODULE=dermai.settings_optimized
python manage.py runserver
```

2. **Monitor memory usage:**
```bash
python memory_monitor.py
```

3. **Deploy to Render:**
- Sử dụng `render_optimized.yaml`
- Monitor logs để check memory usage
- Có thể cần upgrade plan nếu vẫn bị OOM

## Performance Tips

1. **Preload model on startup** (đã implement)
2. **Use connection pooling** cho database
3. **Enable caching** cho static files
4. **Compress images** trước khi xử lý
5. **Implement request queuing** nếu có nhiều concurrent requests