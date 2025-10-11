# Hướng dẫn Tối ưu hóa Memory cho Render.com

## Vấn đề
Model EfficientNetV2S + Grad-CAM tốn quá nhiều RAM trên Render.com free tier (512MB RAM).

## Các tối ưu đã thực hiện

### 1. **Lazy Loading Model** ✅
- Model chỉ được load khi có request đầu tiên, không load khi khởi động app
- Tiết kiệm ~200-300MB RAM khi idle
- Code: `AI_detection.py` - hàm `get_model()`

### 2. **Memory Cleanup** ✅
- Tự động clear TensorFlow session và garbage collection sau mỗi prediction
- Giải phóng bộ nhớ từ tensors và gradients
- Code: `AI_detection.py` - hàm `cleanup_memory()`

### 3. **Tắt Grad-CAM trên Production** ✅
- Grad-CAM tốn ~100-150MB RAM mỗi lần tính toán
- Có thể tắt bằng biến môi trường `ENABLE_GRADCAM=false`
- Code: Đã cấu hình trong `render.yaml`

### 4. **Gunicorn Optimization** ✅
- Giảm từ 1 worker/4 threads → 1 worker/2 threads
- Worker restart sau 100 requests để giải phóng memory leaks
- Sử dụng `/dev/shm` cho worker temp files (faster)
- Code: `render.yaml` - `startCommand`

### 5. **TensorFlow Optimization** ✅
- Tắt verbose logging: `TF_CPP_MIN_LOG_LEVEL=3`
- Giới hạn số threads: `OMP_NUM_THREADS=1`
- Tắt oneDNN optimizations: `TF_ENABLE_ONEDNN_OPTS=0`
- Code: `render.yaml` - environment variables

### 6. **Model Quantization (Optional)** 📝
- Convert model sang float16 để giảm 50% kích thước
- Chạy script: `python Dermal/quantize_model.py`
- ⚠️ **Lưu ý**: Có thể giảm accuracy nhẹ (~1-2%)

## Cách sử dụng

### Trên Local Development (với Grad-CAM)
```bash
export ENABLE_GRADCAM=true
python manage.py runserver
```

### Trên Production Render.com (tiết kiệm memory)
Đã cấu hình sẵn trong `render.yaml`:
- `ENABLE_GRADCAM=false` - Tắt Grad-CAM
- Optimized Gunicorn config

### Quantize Model (Optional)
```bash
# 1. Chạy script quantization
python Dermal/quantize_model.py

# 2. Backup model gốc
mv Dermal/dermatology_stage1.keras Dermal/dermatology_stage1_original.keras

# 3. Sử dụng model đã quantize
mv Dermal/dermatology_stage1_fp16.keras Dermal/dermatology_stage1.keras

# 4. Test model
python manage.py shell
>>> from Dermal.AI_detection import predict_skin_simple
>>> # Test với một ảnh
```

## Ước tính Memory Usage

| Cấu hình | RAM Usage | Ghi chú |
|----------|-----------|---------|
| **Trước tối ưu** | ~650MB | Vượt quá 512MB limit |
| **Sau tối ưu (no Grad-CAM)** | ~350-400MB | ✅ Chạy được trên free tier |
| **Sau tối ưu (có Grad-CAM)** | ~450-550MB | ⚠️ Có thể vẫn bị OOM |
| **Với quantization** | ~300-350MB | ✅✅ An toàn nhất |

## Giám sát Memory

Thêm endpoint để monitor memory usage:

```python
# Trong views.py
import psutil
import os

@login_required
def memory_status(request):
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return JsonResponse({
        'rss_mb': mem_info.rss / (1024 * 1024),
        'vms_mb': mem_info.vms / (1024 * 1024),
    })
```

## Troubleshooting

### Vẫn bị OOM (Out of Memory)?

1. **Tắt Grad-CAM hoàn toàn** (đã làm)
2. **Quantize model** (chạy script trên)
3. **Giảm image size**:
   ```python
   # Trong AI_detection.py
   IMG_SIZE_DEFAULT = 224  # Giảm từ 300 → 224
   ```
4. **Upgrade Render plan** lên Starter ($7/month) với 512MB → 2GB RAM

### Model load chậm?
- Bình thường, lần đầu tiên sẽ chậm vì phải load model
- Các request sau sẽ nhanh hơn vì model đã cached

### Làm sao để enable Grad-CAM lại?
```bash
# Trong Render dashboard, đổi environment variable:
ENABLE_GRADCAM=true
```

## Các cải tiến khác có thể làm

1. **Sử dụng Redis cache** cho model predictions
2. **Model serving riêng** (tách API prediction ra service khác)
3. **TensorFlow Lite** (nhỏ hơn nhưng phức tạp hơn để setup)
4. **Async prediction queue** (Celery + Redis)

## Kết luận

Với các tối ưu trên, app nên chạy được trên Render.com free tier (512MB). Nếu vẫn gặp vấn đề:
1. Tắt Grad-CAM (đã làm)
2. Quantize model (chạy script)
3. Consider upgrade plan

---
*Tạo ngày: 2025-10-10*
*Branch: cursor/optimize-dermatology-ai-for-memory-c262*
