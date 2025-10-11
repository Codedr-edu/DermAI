# Checklist Deploy lên Render.com

## ✅ Các tối ưu đã thực hiện

- [x] **Lazy loading model** - Model chỉ load khi có request đầu tiên
- [x] **Memory cleanup** - Tự động giải phóng RAM sau mỗi prediction
- [x] **Tắt Grad-CAM** - Disable trên production để tiết kiệm ~150MB RAM
- [x] **Gunicorn optimization** - 1 worker, 2 threads, restart sau 100 requests
- [x] **TensorFlow optimization** - Giới hạn threads và logging
- [x] **Django optimization** - Session, upload size, connection pooling
- [x] **Memory monitoring** - Endpoint `/memory/` để theo dõi RAM usage

## 🚀 Bước deploy

### 1. Push code lên GitHub
```bash
git add .
git commit -m "Optimize memory for Render.com deployment"
git push origin cursor/optimize-dermatology-ai-for-memory-c262
```

### 2. Trên Render Dashboard
1. Kết nối GitHub repository
2. Chọn branch: `cursor/optimize-dermatology-ai-for-memory-c262`
3. Render sẽ tự động đọc `render.yaml` và deploy

### 3. Kiểm tra sau khi deploy

#### a) Health check
```bash
curl https://your-app.onrender.com/health/
# Expect: ok
```

#### b) Memory status
```bash
curl https://your-app.onrender.com/memory/
```

Kết quả mong đợi:
```json
{
  "status": "ok",
  "memory": {
    "rss_mb": 350.5,    // Should be < 450MB
    "vms_mb": 890.2,
    "percent": 68.5
  },
  "model_loaded": false,  // false ban đầu (lazy load)
  "gradcam_enabled": false
}
```

#### c) Test prediction
Upload một ảnh qua UI, sau đó check lại `/memory/`:
```json
{
  "model_loaded": true,   // true sau request đầu tiên
  "memory": {
    "rss_mb": 380.2      // Should increase but stay < 450MB
  }
}
```

## 📊 Ngưỡng memory an toàn

| Trạng thái | RAM Usage | Status |
|------------|-----------|--------|
| Idle (chưa load model) | < 150MB | ✅ Rất tốt |
| Model loaded (idle) | 250-350MB | ✅ Tốt |
| During prediction | 350-450MB | ✅ OK |
| > 450MB | Critical | ⚠️ Nguy cơ OOM |
| > 500MB | OOM imminent | ❌ Sắp crash |

## 🔧 Troubleshooting

### Vẫn bị OOM?

#### Option 1: Quantize model (recommended)
```bash
# Trên local
python Dermal/quantize_model.py

# Backup và replace
mv Dermal/dermatology_stage1.keras Dermal/dermatology_stage1_original.keras
mv Dermal/dermatology_stage1_fp16.keras Dermal/dermatology_stage1.keras

# Test trước khi deploy
python manage.py shell
>>> from Dermal.AI_detection import predict_skin_simple
>>> with open('test_image.jpg', 'rb') as f:
...     result = predict_skin_simple(f.read())
>>> print(result)

# Nếu OK, commit và push
git add Dermal/dermatology_stage1.keras
git commit -m "Use quantized model for lower memory usage"
git push
```

#### Option 2: Giảm image size
In `Dermal/AI_detection.py`:
```python
IMG_SIZE_DEFAULT = 224  # Giảm từ 300 → 224
```

#### Option 3: Enable Grad-CAM chỉ khi cần
Trong Render dashboard, thêm query parameter:
```
# Default: Grad-CAM disabled (tiết kiệm RAM)
ENABLE_GRADCAM=false

# Khi cần Grad-CAM, set:
ENABLE_GRADCAM=true
# Nhưng lưu ý: RAM sẽ tăng ~150MB
```

### App khởi động chậm?
- Bình thường! Lần đầu tiên model load sẽ mất 10-30 giây
- Các request sau sẽ nhanh hơn (model đã cached)

### Model predictions sai?
Nếu đã dùng quantized model và accuracy giảm:
1. Restore model gốc
2. Consider upgrade Render plan lên Starter ($7/month, 2GB RAM)

## 📈 Nâng cấp sau này

### Option 1: Model serving riêng
Tách model prediction ra một service riêng (microservices):
- Web app: Handle UI/UX, database
- ML service: Chỉ serve predictions
- Communication: REST API hoặc message queue

### Option 2: Caching predictions
Sử dụng Redis để cache predictions cho ảnh giống nhau:
```python
import hashlib
image_hash = hashlib.md5(image_bytes).hexdigest()
# Check cache trước khi predict
```

### Option 3: Async queue
Sử dụng Celery + Redis:
- User upload ảnh → job vào queue
- Background worker xử lý prediction
- User nhận kết quả qua webhook/polling

## 🎯 Expected Performance

| Metric | Before | After Optimization |
|--------|--------|-------------------|
| RAM (idle) | ~200MB | ~100-150MB |
| RAM (model loaded) | ~650MB | ~300-400MB |
| RAM (during prediction) | ~700MB+ | ~350-450MB |
| First request time | 15s | 20s (lazy load) |
| Subsequent requests | 3-5s | 2-4s |
| OOM errors | Frequent ❌ | Rare/None ✅ |

## 📞 Support

Nếu vẫn gặp vấn đề:
1. Check logs trên Render dashboard
2. Monitor `/memory/` endpoint
3. Xem `OPTIMIZATION_GUIDE.md` để biết thêm chi tiết
4. Consider upgrade plan nếu traffic cao

---
Good luck! 🚀
