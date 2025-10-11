# 🐍 HƯỚNG DẪN DEPLOY LÊN PYTHONANYWHERE

## ⚠️ QUAN TRỌNG: ĐỌC TRƯỚC KHI DEPLOY!

**PythonAnywhere khác Render rất nhiều:**

| Feature | PythonAnywhere | Render |
|---------|----------------|--------|
| **Timeout** | 300s (5 phút) ✅ | 30-60s ❌ |
| **Spin Down** | KHÔNG (chạy 24/7) ✅ | CÓ (sau 15 phút) |
| **RAM Free** | 512MB | 512MB |
| **Pre-load cần thiết?** | **KHÔNG!** ✅ | **CÓ!** ❌ |

**KẾT LUẬN:**
- ✅ **PythonAnywhere KHÔNG CẦN pre-load model!**
- ✅ Timeout 300s đủ để load model (60s) + inference (5s)
- ✅ Không spin down → Request đầu tiên không chậm hơn

---

## 🚨 VẤN ĐỀ CHÍNH: RAM, KHÔNG PHẢI TIMEOUT

### Tính toán RAM usage:

```
Django base:       ~100 MB
TensorFlow:        ~200 MB
Model (loaded):    ~1000 MB (tùy model size)
Inference buffer:  ~200 MB
────────────────────────────
Total:             ~1500 MB >>> 512 MB ❌ OVER LIMIT!
```

**Nếu vượt quá 512MB:**
- Worker process bị KILL ngay lập tức
- App crash với error "Killed" (no traceback)
- Phải restart lại

---

## ⚙️ CẤU HÌNH RECOMMENDED CHO PYTHONANYWHERE FREE (512MB)

### 1. **TẮT PRE-LOADING** (QUAN TRỌNG!)

Trên PythonAnywhere Web UI → Files → Edit `.env`:

```bash
# TẮT model pre-loading (tiết kiệm RAM khi khởi động)
PRELOAD_MODEL=false

# TẮT Grad-CAM để tiết kiệm RAM (~200MB)
ENABLE_GRADCAM=false

# TensorFlow optimizations
TF_CPP_MIN_LOG_LEVEL=3
TF_ENABLE_ONEDNN_OPTS=0
OMP_NUM_THREADS=1
```

**Kết quả:**
- App khởi động nhanh
- RAM thấp lúc đầu (~300MB)
- Model chỉ load khi có request đầu tiên
- Request đầu tiên: ~60-70s (OK, không timeout vì có 300s!)
- Các request sau: ~3-5s

### 2. Nếu vẫn bị OOM (Out of Memory):

**Option A: Quantize Model**

```bash
# Chuyển model từ FP32 → FP16
python Dermal/quantize_model.py
```

Giảm size từ ~1GB → ~500MB

**Option B: Upgrade Plan**

- Free: 512MB RAM
- Hacker: $5/month, 1GB RAM ✅ RECOMMENDED!
- Web Dev: $12/month, 3GB RAM

---

## 📝 BƯỚC DEPLOY

### Bước 1: Upload Code

```bash
# Option 1: Git clone
cd /home/yourusername/
git clone https://github.com/your-repo/dermai.git

# Option 2: Upload ZIP qua Web UI
# Dashboard → Files → Upload
```

### Bước 2: Install Dependencies

```bash
# Mở Bash console trên PythonAnywhere
cd ~/dermai
pip install --user -r requirements.txt
```

### Bước 3: Config Environment Variables

Tạo file `.env`:

```bash
# ~/dermai/.env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourusername.pythonanywhere.com

# QUAN TRỌNG: TẮT pre-loading cho 512MB RAM
PRELOAD_MODEL=false
ENABLE_GRADCAM=false

# TensorFlow optimizations
TF_CPP_MIN_LOG_LEVEL=3
OMP_NUM_THREADS=1
```

### Bước 4: Migrations

```bash
cd ~/dermai
python manage.py migrate
python manage.py collectstatic --no-input
```

### Bước 5: Config WSGI File

Dashboard → Web → WSGI configuration file:

```python
# /var/www/yourusername_pythonanywhere_com_wsgi.py

import os
import sys

# Add your project directory to the sys.path
project_home = '/home/yourusername/dermai'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'dermai.settings'

# Load .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# IMPORTANT: Signal that we're in server mode
# (but keep PRELOAD_MODEL=false in .env!)
os.environ['DJANGO_SERVER_MODE'] = 'true'

# Load Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Bước 6: Config Web App Settings

Dashboard → Web → Configuration:

- **Source code:** `/home/yourusername/dermai`
- **Working directory:** `/home/yourusername/dermai`
- **Python version:** 3.10 (hoặc cao hơn)
- **Virtualenv:** (Optional, recommended: `/home/yourusername/.virtualenvs/dermai`)

### Bước 7: Static Files

Dashboard → Web → Static files:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/dermai/staticfiles/` |
| `/media/` | `/home/yourusername/dermai/media/` |

### Bước 8: Reload Web App

Dashboard → Web → **Reload** button (màu xanh lá)

---

## 🧪 TEST SAU KHI DEPLOY

### Test 1: Health Check

```bash
curl https://yourusername.pythonanywhere.com/health?verbose=1

# Response mong đợi:
{
  "status": "ok",
  "model_loaded": false,  ← FALSE vì lazy loading
  "message": "Model will load on first request"
}
```

### Test 2: Upload Ảnh (Request đầu tiên)

- Lần đầu tiên sẽ chậm (~60-70s) vì phải load model
- **ĐÂY LÀ BÌNH THƯỜNG!** Timeout 300s nên không sao
- Browser sẽ hiển thị loading spinner

### Test 3: Upload Ảnh (Lần 2)

- Nhanh (~3-5s) vì model đã được load
- Check health lại:

```bash
curl https://yourusername.pythonanywhere.com/health?verbose=1

# Response:
{
  "status": "ok",
  "model_loaded": true,  ← TRUE sau request đầu tiên
  "message": "Model pre-loaded, ready for inference"
}
```

### Test 4: Memory Status

```bash
curl https://yourusername.pythonanywhere.com/memory-status

# Response:
{
  "status": "ok",
  "memory": {
    "rss_mb": 487.3,  ← Nếu < 512 = OK ✅
    "percent": 95.2
  },
  "model_loaded": true
}
```

**Nếu rss_mb > 512MB:**
- App sẽ bị kill ngay
- Phải tắt Grad-CAM hoặc quantize model

---

## 🐛 TROUBLESHOOTING

### Vấn đề 1: App bị kill với "Killed" message

**Nguyên nhân:** RAM > 512MB

**Giải pháp:**
```bash
# .env
ENABLE_GRADCAM=false  # Tiết kiệm ~200MB
```

Hoặc quantize model xuống < 500MB.

### Vấn đề 2: Request đầu tiên timeout

**Kiểm tra:**
- Timeout setting trên PA (mặc định 300s)
- Model có quá lớn không? (> 2GB → load > 300s)

**Giải pháp:**
- Quantize model
- Hoặc enable pre-loading (nếu có đủ RAM):
  ```bash
  PRELOAD_MODEL=true
  ```

### Vấn đề 3: Model không load

**Kiểm tra error log:**
Dashboard → Web → Error log

**Có thể là:**
- Model file không tồn tại
- Path không đúng
- TensorFlow version không compatible

### Vấn đề 4: Static files không load

**Fix:**
```bash
python manage.py collectstatic --no-input
```

Và check Static files mapping trong Web UI.

---

## 📊 SO SÁNH HIỆU SUẤT

### PythonAnywhere Free (với lazy loading):

| Metric | Value |
|--------|-------|
| **Request đầu tiên** | 60-70s (load model) |
| **Request tiếp theo** | 3-5s |
| **Timeout limit** | 300s ✅ |
| **RAM usage (idle)** | ~300MB |
| **RAM usage (loaded)** | ~800-1200MB |
| **Uptime** | 24/7 (không sleep) ✅ |

### So với Render Free (với pre-loading):

| Metric | PythonAnywhere | Render |
|--------|----------------|--------|
| **Cold start** | Không có (24/7) | 50s |
| **Request đầu tiên** | 60-70s | 3-5s (nếu pre-load) |
| **Timeout** | 300s ✅ | 30-60s |
| **RAM strategy** | Lazy load | Pre-load |

**PythonAnywhere lợi thế:**
- ✅ Không spin down (24/7 uptime)
- ✅ Timeout cao (300s)
- ✅ Lazy loading OK
- ✅ Tiết kiệm RAM khi idle

**Render lợi thế:**
- ✅ Request đầu tiên nhanh hơn (nếu pre-load)
- ✅ Auto deploy from Git

---

## ✅ CHECKLIST CUỐI CÙNG

Trước khi deploy production:

- [ ] Set `PRELOAD_MODEL=false` trong `.env`
- [ ] Set `ENABLE_GRADCAM=false` (nếu RAM hạn chế)
- [ ] Set `DEBUG=False`
- [ ] Set `ALLOWED_HOSTS=yourusername.pythonanywhere.com`
- [ ] Run `python manage.py collectstatic`
- [ ] Run `python manage.py migrate`
- [ ] Check model file exists: `ls -lh Dermal/*.keras`
- [ ] Test health endpoint
- [ ] Test upload ảnh (chấp nhận lần đầu chậm)
- [ ] Monitor RAM usage qua `/memory-status`

---

## 🎯 TÓM TẮT

**PythonAnywhere Free:**
- ✅ Lazy loading là chiến lược TỐT NHẤT
- ✅ Request đầu tiên chậm (60s) là BÌNH THƯỜNG
- ⚠️ Phải quản lý RAM cẩn thận (512MB limit)
- ✅ Không cần lo timeout (300s là quá đủ)

**Code đã sẵn sàng!**
- ✅ Detection logic hỗ trợ mod_wsgi (PythonAnywhere)
- ✅ Environment variable control (PRELOAD_MODEL)
- ✅ Graceful fallback nếu load fail
- ✅ Memory monitoring built-in

**Deploy ngay!** 🚀
