# Pre-loading Model để tránh Timeout trên Render Free Tier

## Vấn đề

Khi deploy lên Render free tier, instance sẽ "spin down" (tắt) sau 15 phút không hoạt động. Khi có request mới:

1. **Cold start**: Server khởi động lại (~50 giây)
2. **Model loading**: Load model TensorFlow vào RAM (~30-60 giây với model lớn)
3. **Inference**: Xử lý dự đoán (~2-5 giây)

**Tổng thời gian: 80-115 giây** ❌

Nhưng HTTP request timeout thường chỉ **30-60 giây** → Request bị **502/504 timeout**!

## Giải pháp

### 1. Pre-load Model khi App Khởi động

File `Dermal/apps.py` đã được cấu hình để tự động load model khi Django khởi động:

```python
class DermalConfig(AppConfig):
    def ready(self):
        # Load model ngay khi server start
        model = AI_detection.get_model()
```

**Ưu điểm:**
- Request đầu tiên chỉ mất ~2-5s (chỉ inference, không load model)
- Không bị timeout
- User experience tốt hơn

**Timeline mới:**
1. Cold start: ~50s
2. **Model đã được load sẵn** ✅
3. Request đầu tiên: ~2-5s → **Thành công!** ✅

### 2. Environment Variable

Có thể bật/tắt pre-loading bằng biến môi trường:

```bash
# Bật pre-loading (mặc định)
PRELOAD_MODEL=true

# Tắt pre-loading (nếu cần tiết kiệm RAM)
PRELOAD_MODEL=false
```

### 3. Health Check

Endpoint `/health` giờ sẽ báo model đã load chưa:

```bash
# Simple check
curl https://your-app.onrender.com/health
# Response: ok (model: loaded)

# Verbose check
curl https://your-app.onrender.com/health?verbose=1
# Response: {"status": "ok", "model_loaded": true, "message": "Model pre-loaded, ready for inference"}
```

### 4. Memory Status

Endpoint `/memory-status` để monitor RAM usage:

```bash
curl https://your-app.onrender.com/memory-status
```

## Lưu ý

### RAM Usage
- Model chiếm ~500MB-2GB RAM (tùy model size)
- Render free tier có **512MB RAM** → Có thể không đủ nếu model quá lớn
- Giải pháp:
  - Quantize model (FP16 thay vì FP32)
  - Tắt Grad-CAM nếu không cần: `ENABLE_GRADCAM=false`
  - Upgrade lên Render paid tier (có 2GB+ RAM)

### Cold Start vẫn chậm
- Pre-loading chỉ giải quyết vấn đề **timeout**
- Cold start vẫn mất ~50s (do Render spin up container)
- User vẫn phải đợi ~50-55s cho request đầu tiên (nhưng không bị timeout)
- Các request tiếp theo sẽ nhanh (<5s) cho đến khi instance sleep lại

### Development
- Trong development, có thể tắt pre-loading để khởi động nhanh hơn:
  ```bash
  PRELOAD_MODEL=false python manage.py runserver
  ```

## Kiểm tra

### Test Pre-loading hoạt động

1. **Start server và xem log:**
   ```bash
   python manage.py runserver
   ```
   
   Bạn sẽ thấy:
   ```
   🚀 Pre-loading AI model to avoid timeout on first request...
   🔄 Loading model from: /path/to/model.keras
   ✅ Loaded model: Functional name: model
   ✅ Model warmed up
   ✅ Model pre-loaded successfully: Functional
   ```

2. **Kiểm tra health:**
   ```bash
   curl http://localhost:8000/health?verbose=1
   ```
   
   Kết quả mong đợi:
   ```json
   {
     "status": "ok",
     "model_loaded": true,
     "message": "Model pre-loaded, ready for inference"
   }
   ```

3. **Test request đầu tiên nhanh:**
   - Upload ảnh lần đầu tiên
   - Response time nên < 10 giây (thay vì 30-60s)

## Kết luận

✅ **Trước đây**: Request đầu tiên bị timeout vì load model trong request (>80s)

✅ **Bây giờ**: Model được load sẵn khi server start, request đầu tiên chỉ mất vài giây

⚠️ **Trade-off**: Tốn nhiều RAM hơn (model luôn ở trong memory), có thể cần upgrade plan nếu model quá lớn
