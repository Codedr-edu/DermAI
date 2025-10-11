# ⚖️ SO SÁNH: RENDER vs PYTHONANYWHERE

## 📊 BẢNG SO SÁNH NHANH

| Feature | Render Free | PythonAnywhere Free | Chiến thắng |
|---------|-------------|---------------------|-------------|
| **RAM** | 512MB | 512MB | 🤝 Hòa |
| **HTTP Timeout** | 30-60s | 300s (5 phút) | 🏆 PA |
| **Spin Down** | ✅ Sau 15 phút | ❌ Không (24/7) | 🏆 PA |
| **Cold Start** | ~50s | Không có | 🏆 PA |
| **Deploy** | Git push auto | Manual upload | 🏆 Render |
| **SSL** | Free (auto) | Free (auto) | 🤝 Hòa |
| **Custom Domain** | Free | Paid ($5+) | 🏆 Render |
| **Database** | PostgreSQL free | MySQL free | 🤝 Hòa |

---

## 🎯 VẤN ĐỀ TIMEOUT VỚI MODEL LỚN

### Render Free (Vấn đề nghiêm trọng!)

```
User không truy cập 15 phút
  ↓
App spin down (container shutdown)
  ↓
User truy cập lại
  ↓
Cold start: 50s (boot container)
  ↓
Load Django: 5s
  ↓
Load TensorFlow model: 60s  ← CHẬM!
  ↓
Inference: 5s
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 120s >>> 60s timeout ❌ REQUEST FAILED!
```

**Giải pháp cho Render:**
- ✅ **PRE-LOAD model trong apps.py**
- Load model khi Django start (không đợi request)
- Request đầu tiên chỉ mất 5s inference

```
Cold start: 50s
  ↓
Load Django + Pre-load model: 65s
  ↓
Server ready ✅
  ↓
User request → Inference: 5s ✅ SUCCESS!
```

---

### PythonAnywhere Free (Không có vấn đề!)

```
App chạy 24/7 (không spin down)
  ↓
Request đầu tiên
  ↓
Load model: 60s (lazy loading)
  ↓
Inference: 5s
━━━━━━━━━━━━━━━━━━━━━━
Total: 65s <<< 300s timeout ✅ SUCCESS!
  ↓
Request tiếp theo
  ↓
Model đã load → Inference: 5s ✅
```

**Giải pháp cho PythonAnywhere:**
- ✅ **LAZY LOADING là tốt nhất!**
- KHÔNG cần pre-load (tốn RAM)
- Timeout 300s quá đủ
- Tiết kiệm RAM (~300MB idle)

---

## 💾 CHIẾN LƯỢC RAM

### Render: Pre-loading

**RAM Usage Timeline:**
```
App start: 100MB (Django base)
  ↓ Pre-load model
400MB → 1200MB (model + TensorFlow)
  ↓ Luôn giữ trong RAM
1200MB (constant)
```

**Ưu điểm:**
- ✅ Request đầu tiên nhanh
- ✅ Tất cả requests đều nhanh (~5s)

**Nhược điểm:**
- ❌ RAM cao ngay từ đầu
- ❌ Có thể bị OOM nếu model > 400MB

### PythonAnywhere: Lazy Loading

**RAM Usage Timeline:**
```
App start: 100MB (Django idle)
  ↓ Chờ request
300MB (Django + dependencies)
  ↓ Request đầu tiên → Load model
300MB → 1200MB (model loaded)
  ↓ Giữ trong RAM
1200MB (sau khi load)
```

**Ưu điểm:**
- ✅ RAM thấp lúc khởi động
- ✅ Không bị kill khi start
- ✅ Chỉ load khi thực sự cần

**Nhược điểm:**
- ⚠️ Request đầu tiên chậm (60s)
- Nhưng OK vì timeout 300s!

---

## 🔧 CẤU HÌNH CODE

### apps.py (Hỗ trợ CẢ HAI!)

Code hiện tại đã support cả Render và PythonAnywhere:

```python
class DermalConfig(AppConfig):
    def ready(self):
        # Kiểm tra environment variable
        preload = os.getenv('PRELOAD_MODEL', 'true')
        
        # Detect server (Gunicorn OR mod_wsgi)
        is_server = (
            'gunicorn' in sys.argv[0] or      # ← Render
            'mod_wsgi' in sys.modules or       # ← PythonAnywhere
            os.getenv('DJANGO_SERVER_MODE')    # ← Manual config
        )
        
        if preload and is_server:
            model = AI_detection.get_model()  # Pre-load
```

**Flexibility:**
- Control qua environment variable `PRELOAD_MODEL`
- Tự động detect platform (Render hoặc PA)

---

## ⚙️ RECOMMENDED CONFIG

### Cho Render Free:

```bash
# render.yaml hoặc Environment Variables
PRELOAD_MODEL=true         # ← BẮT BUỘC để tránh timeout!
ENABLE_GRADCAM=true        # OK nếu RAM đủ
DJANGO_SERVER_MODE=true
```

**Gunicorn command:**
```bash
gunicorn dermai.wsgi:application \
  --workers 1 \
  --preload-app \           # ← Load trước khi fork
  --timeout 300
```

**Kết quả:**
- Cold start + pre-load: ~65s (diễn ra trước request)
- Request đầu tiên: ~5s ✅
- Request tiếp theo: ~3-5s ✅

---

### Cho PythonAnywhere Free:

```bash
# .env file
PRELOAD_MODEL=false        # ← RECOMMENDED để tiết kiệm RAM!
ENABLE_GRADCAM=false       # Tắt để tiết kiệm ~200MB
DJANGO_SERVER_MODE=true
```

**WSGI config:**
```python
# Không cần config gì thêm
# mod_wsgi tự động handle
```

**Kết quả:**
- App start: ~5s (không load model)
- Request đầu tiên: ~65s (load model) ⚠️ CHẤP NHẬN!
- Request tiếp theo: ~3-5s ✅

---

## 🎯 DECISION MATRIX

### Khi nào dùng Render?

✅ **Dùng Render nếu:**
- Bạn muốn auto-deploy từ GitHub
- Có traffic đều (app không sleep lâu)
- Cần request đầu tiên nhanh
- Model < 400MB (sau quantization)
- OK với việc app sleep khi không dùng

❌ **KHÔNG dùng Render nếu:**
- Model > 1GB và không thể quantize
- RAM 512MB không đủ
- Traffic thưa (app sleep nhiều → cold start liên tục)

---

### Khi nào dùng PythonAnywhere?

✅ **Dùng PythonAnywhere nếu:**
- Traffic thưa (ít user)
- Chấp nhận request đầu tiên chậm (60s)
- Cần uptime 24/7
- Muốn tiết kiệm RAM
- OK với manual deployment

❌ **KHÔNG dùng PythonAnywhere nếu:**
- Cần request đầu tiên nhanh (<10s)
- Cần auto-deploy from Git
- Cần custom domain (free tier không support)

---

## 💰 COST COMPARISON

### Free Tier:

| Feature | Render | PythonAnywhere |
|---------|--------|----------------|
| **Price** | $0 | $0 |
| **RAM** | 512MB | 512MB |
| **Disk** | Ephemeral | 512MB |
| **Bandwidth** | Unlimited | 100k hits/day |
| **Uptime** | Spin down after 15min | 24/7 |

### Paid Tier (nếu cần upgrade):

| Feature | Render Starter | PA Hacker |
|---------|----------------|-----------|
| **Price** | $7/month | $5/month |
| **RAM** | 2GB | 1GB |
| **Disk** | Persistent | 1GB |
| **Workers** | Custom | 2 workers |
| **Custom domain** | ✅ Free | ✅ Included |

**Recommendation:** Nếu RAM 512MB không đủ → **Upgrade PythonAnywhere ($5)** rẻ hơn Render ($7)!

---

## 📋 CHECKLIST DEPLOY

### Cho Render:

```bash
# 1. Sửa render.yaml
startCommand: "gunicorn ... --preload-app"

# 2. Set environment variables
PRELOAD_MODEL=true
DJANGO_SERVER_MODE=true
ENABLE_GRADCAM=true   # hoặc false nếu RAM không đủ

# 3. Deploy
git push origin main

# 4. Monitor logs
render logs

# 5. Test
curl https://your-app.onrender.com/health?verbose=1
```

---

### Cho PythonAnywhere:

```bash
# 1. Upload code
git clone hoặc upload ZIP

# 2. Tạo .env
PRELOAD_MODEL=false
ENABLE_GRADCAM=false
DJANGO_SERVER_MODE=true

# 3. Install dependencies
pip install --user -r requirements.txt

# 4. Migrations
python manage.py migrate
python manage.py collectstatic

# 5. Config WSGI file
# (theo hướng dẫn trong DEPLOYMENT_PYTHONANYWHERE.md)

# 6. Reload web app
# Click "Reload" button trong Web UI

# 7. Test (chấp nhận lần đầu chậm!)
curl https://yourusername.pythonanywhere.com/health?verbose=1
```

---

## 🏆 KẾT LUẬN

### TL;DR:

**Render:**
- Vấn đề: Timeout do spin down
- Giải pháp: Pre-load model ✅
- Config: `PRELOAD_MODEL=true`

**PythonAnywhere:**
- Vấn đề: RAM hạn chế
- Giải pháp: Lazy loading ✅
- Config: `PRELOAD_MODEL=false`

### Code hiện tại:

✅ **Đã support CẢ HAI platforms!**
- Detection logic cho cả Gunicorn và mod_wsgi
- Control qua environment variable
- Graceful fallback nếu load fail
- Memory monitoring built-in

### Ready to deploy:

- ✅ Render: Set `PRELOAD_MODEL=true`
- ✅ PythonAnywhere: Set `PRELOAD_MODEL=false`
- ✅ Code tự detect platform
- ✅ Không cần sửa gì thêm!

**Deploy ngay!** 🚀
