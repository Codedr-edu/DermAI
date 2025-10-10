# Memory Optimization Guide

## Vấn đề
Model AI chẩn đoán bệnh da liễu sử dụng EfficientNetV2S bị lỗi "out of memory" khi deploy lên Render.com.

## Nguyên nhân
1. **Model size lớn**: EfficientNetV2S là model khá nặng (~50-100MB)
2. **Grad-CAM computation**: Tốn nhiều memory để tính gradient
3. **Image processing**: Ảnh 300x300 tốn nhiều memory
4. **Render.com free plan**: Chỉ có 512MB RAM

## Giải pháp đã áp dụng

### 1. Lazy Loading Model
- Model chỉ được load khi cần thiết
- Sử dụng `get_model()` function thay vì load ngay khi import

### 2. Giảm Image Size
- Từ 300x300 xuống 224x224 (giảm ~45% memory)
- Sử dụng BILINEAR resize thay vì LANCZOS (nhanh hơn)

### 3. Memory Management
- Sử dụng `float16` thay vì `float32` (giảm 50% memory)
- Thêm `gc.collect()` sau mỗi operation
- Cleanup tensors và variables sau khi sử dụng

### 4. TensorFlow Optimization
- Mixed precision training (`mixed_float16`)
- Memory growth enabled
- Giới hạn số threads

### 5. Django Middleware
- Tự động cleanup memory sau mỗi request
- Monitor memory usage

### 6. Render.com Configuration
- Upgrade từ free plan lên starter plan (1GB RAM)
- Tối ưu Gunicorn settings
- Giới hạn số threads và workers

## Cấu hình Render.com

```yaml
services:
  - type: web
    name: DermAI
    env: python
    region: singapore
    plan: starter  # Upgrade từ free
    startCommand: "gunicorn dermai.wsgi:application --workers 1 --threads 2 --timeout 300 --max-requests 100 --max-requests-jitter 10 --preload"
    envVars:
      - key: TF_CPP_MIN_LOG_LEVEL
        value: "2"
      - key: OMP_NUM_THREADS
        value: "2"
      - key: MKL_NUM_THREADS
        value: "2"
```

## Test Memory Usage

Chạy script test:
```bash
python test_memory.py
```

## Monitoring

Script sẽ hiển thị:
- Memory usage trước và sau khi load model
- Memory overhead của prediction
- Thời gian prediction
- Cảnh báo nếu memory usage quá cao

## Kết quả mong đợi

- Memory usage < 400MB sau cleanup
- Prediction time < 5s
- Không còn lỗi "out of memory"
- Model vẫn hoạt động chính xác

## Troubleshooting

Nếu vẫn gặp lỗi memory:

1. **Kiểm tra model size**:
   ```bash
   ls -lh Dermal/dermatology_stage1.keras
   ```

2. **Test local**:
   ```bash
   python test_memory.py
   ```

3. **Monitor logs** trên Render.com để xem memory usage

4. **Cân nhắc**:
   - Sử dụng model nhỏ hơn (MobileNet, EfficientNet-B0)
   - Implement model quantization
   - Sử dụng external API cho AI inference

## Files đã thay đổi

- `Dermal/AI_detection.py`: Tối ưu memory
- `Dermal/middleware.py`: Memory management middleware
- `tensorflow_config.py`: TensorFlow configuration
- `render.yaml`: Render.com configuration
- `requirements.txt`: Thêm psutil
- `test_memory.py`: Memory testing script