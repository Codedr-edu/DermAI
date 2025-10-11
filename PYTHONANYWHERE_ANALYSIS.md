# 🔍 PHÂN TÍCH: PythonAnywhere vs Render

## 📊 SO SÁNH

| Feature | Render Free | PythonAnywhere Free |
|---------|-------------|---------------------|
| **RAM** | 512MB | 512MB ✅ Giống nhau |
| **Timeout** | 30-60s | 300s (5 phút) ✅ TỐT HƠN! |
| **Spin Down** | ✅ Yes (15 phút không hoạt động) | ❌ NO (luôn chạy 24/7) |
| **WSGI Server** | Gunicorn (tự cấu hình) | mod_wsgi hoặc uWSGI (cấu hình sẵn) |
| **Workers** | Tự config (1-N workers) | 1 worker (fixed) |
| **Deployment** | Git push (auto deploy) | Manual upload + reload |

---

## 🎯 ĐIỂM KHÁC BIỆT QUAN TRỌNG

### 1. ⚠️ KHÔNG CÓ "SPIN DOWN" ISSUE

**Render Free:**
```
App không hoạt động 15 phút → Spin down
↓
User truy cập → Cold start (50s) + Load model (60s) = 110s
→ TIMEOUT nếu không pre-load model ❌
```

**PythonAnywhere Free:**
```
App luôn chạy 24/7 (không sleep)
↓
User truy cập → Chỉ cần inference (5s)
→ KHÔNG BỊ TIMEOUT ngay cả khi lazy load ✅
```

**➡️ Vấn đề timeout KHÔNG TỒN TẠI trên PythonAnywhere!**

### 2. ⚠️ WSGI SERVER KHÁC NHAU

**Render:**
- Dùng Gunicorn (bạn control mọi thứ)
- Config: `--preload-app`, `--workers`, etc.
- Fork model: Master → Workers

**PythonAnywhere:**
- Dùng **mod_wsgi** (Apache module) hoặc **uWSGI**
- **KHÔNG DÙNG Gunicorn!**
- Config qua Web UI, không phải command line
- Có thể dùng "lazy loading" hoặc "daemon mode"

### 3. ⚠️ RELOAD BEHAVIOR

**Render (Gunicorn):**
```python
# Với --preload-app:
Master process starts
  → Django setup
  → apps.py ready() được gọi ← LOAD MODEL Ở ĐÂY
  → Fork workers
```

**PythonAnywhere (mod_wsgi):**
```python
# Daemon mode (mặc định):
Worker process starts (khi có request đầu tiên)
  → Django setup
  → apps.py ready() được gọi ← LOAD MODEL Ở ĐÂY
  → Handle request

# Hoặc embedded mode:
Apache starts
  → Django setup trong Apache process
  → apps.py ready() được gọi
```

**➡️ ready() VẪN HOẠT ĐỘNG trên PythonAnywhere!** ✅

### 4. ⚠️ RELOAD WEB APP

**PythonAnywhere:**
- Khi click "Reload" button trên Web UI:
  - Kill worker processes
  - Start lại Django
  - `ready()` được gọi lại
  - **Model phải load lại (60s)**

**Render:**
- Mỗi lần deploy:
  - Kill container
  - Build lại
  - Start server mới
  - `ready()` được gọi

---

## 🤔 CODE HIỆN TẠI CÓ HOẠT ĐỘNG TRÊN PYTHONANYWHERE KHÔNG?

### ✅ NHỮNG GÌ HOẠT ĐỘNG TỐT:

1. **`apps.py ready()` method** ✅
   - Django standard, hoạt động trên mọi platform
   - PythonAnywhere support đầy đủ

2. **Environment variables** ✅
   - Set được trong Web UI
   - `os.getenv()` hoạt động bình thường

3. **Model pre-loading logic** ✅
   - TensorFlow load bình thường
   - Thread lock hoạt động
   - Memory management OK

### ⚠️ NHỮNG GÌ CẦN KIỂM TRA:

#### 1. Detection Logic có hoạt động không?

Code hiện tại:
```python
# Method 1: Check argv[0]
if 'gunicorn' in sys.argv[0].lower():  # ← KHÔNG CÓ "gunicorn" trên PA!
    is_server = True

# Method 2: Check argv
if 'runserver' in sys.argv:  # ← KHÔNG CÓ "runserver" trên PA!
    is_server = True

# Method 3: Check env (TỐT!)
if os.getenv('DJANGO_SERVER_MODE') == 'true':  # ← HOẠT ĐỘNG ✅
    is_server = True

# Method 4: Check WSGI
if os.getenv('WSGI_APPLICATION'):  # ← CÓ THỂ HOẠT ĐỘNG
    is_server = True
```

**Trên PythonAnywhere:**
- `sys.argv[0]` có thể là: `"python"`, `"uwsgi"`, hoặc mod_wsgi path
- `WSGI_APPLICATION` - Có thể có, có thể không (tùy config)

**➡️ Method 3 (env var) là RELIABLE NHẤT!** ✅

#### 2. Memory Usage

**PythonAnywhere Free:**
- 512MB RAM hard limit
- Nếu vượt quá → Worker bị kill
- Model ~1GB → **CHẮC CHẮN BỊ KILL!** ❌

**Tính toán:**
```
Django base:     ~100MB
TensorFlow:      ~200MB
Model loaded:    ~1000MB
─────────────────────────
Total:           ~1300MB >>> 512MB ❌
```

**➡️ Model QUÁ LỚN cho 512MB!** ❌

#### 3. Timeout có còn là vấn đề không?

**PythonAnywhere: 300s timeout**

Tình huống xấu nhất (lazy loading):
```
Request arrives → Load model (60s) → Inference (5s) = 65s
```

65s < 300s → **KHÔNG BỊ TIMEOUT!** ✅

**➡️ Lazy loading HOÀN TOÀN OK trên PythonAnywhere!**

---

## 🎯 KẾT LUẬN

### ❌ VẤN ĐỀ CHÍNH: RAM, KHÔNG PHẢI TIMEOUT!

**Render:**
- Vấn đề: Spin down → Request đầu tiên timeout
- Giải pháp: Pre-load model ✅

**PythonAnywhere:**
- Vấn đề: Model quá lớn (1GB) > RAM (512MB) ❌
- Timeout 300s → Không phải vấn đề ✅
- Lazy loading hoàn toàn OK ✅

### 💡 CHIẾN LƯỢC CHO PYTHONANYWHERE

#### Option 1: KHÔNG PRE-LOAD (RECOMMENDED)

**Tại sao:**
- Timeout 300s → Đủ thời gian load model
- Không spin down → Request đầu tiên không chậm hơn các request sau
- Tiết kiệm RAM → Tăng khả năng app không bị kill

**Config:**
```bash
# Trên PythonAnywhere Web UI, set env var:
PRELOAD_MODEL=false
```

**Kết quả:**
- Model load khi có request đầu tiên (~60s)
- Các request sau: nhanh (~5s)
- RAM usage: tăng dần (chỉ khi cần)

#### Option 2: PRE-LOAD (NGUY HIỂM)

**Tại sao:**
- Model load ngay khi app start
- RAM 1.3GB > 512MB → **Bị kill ngay!** ❌

**Chỉ dùng nếu:**
- Model đã được quantize (< 400MB)
- Tắt Grad-CAM
- Upgrade lên paid plan (> 512MB RAM)

---

## 🔧 CODE CẦN SỬA

### Vấn đề: Detection logic không hoạt động trên PythonAnywhere

Code hiện tại rely on `gunicorn` hoặc `runserver` → Không detect được PA!

### Fix: Cải thiện detection

```python
# apps.py
def ready(self):
    # ... existing checks ...
    
    # Only pre-load in actual server processes
    is_server = False
    
    # Method 1: Check argv[0] (works for Gunicorn)
    if sys.argv and len(sys.argv) > 0:
        argv0_lower = sys.argv[0].lower()
        if 'gunicorn' in argv0_lower or 'uvicorn' in argv0_lower or 'uwsgi' in argv0_lower:
            is_server = True
    
    # Method 2: Check sys.argv for runserver
    if 'runserver' in sys.argv:
        is_server = True
    
    # Method 3: Check environment variable (RELIABLE!)
    if os.getenv('DJANGO_SERVER_MODE') == 'true':
        is_server = True
    
    # Method 4: Check WSGI
    if os.getenv('WSGI_APPLICATION') or os.getenv('SERVER_SOFTWARE'):
        is_server = True
    
    # Method 5: Check if mod_wsgi (PythonAnywhere)
    # mod_wsgi sets this variable
    if 'mod_wsgi' in str(sys.modules.get('__main__', '')):
        is_server = True
    
    # Method 6: If wsgi.py is being imported (not manage.py)
    # PythonAnywhere loads via wsgi.py
    if 'wsgi' in sys.argv[0].lower():
        is_server = True
```

---

## 📋 CHECKLIST CHO PYTHONANYWHERE

### Trước khi deploy:

- [ ] Set `PRELOAD_MODEL=false` (RECOMMENDED cho 512MB RAM)
- [ ] Set `ENABLE_GRADCAM=false` (tiết kiệm ~200MB)
- [ ] Set `DJANGO_SERVER_MODE=true` (nếu muốn pre-load)
- [ ] Xem model size: `ls -lh Dermal/dermatology_stage1.keras`
- [ ] Nếu model > 400MB → KHÔNG pre-load!

### Sau khi deploy:

- [ ] Check memory usage trên PA dashboard
- [ ] Test upload ảnh (request đầu tiên có thể chậm, OK!)
- [ ] Nếu app bị kill → Tắt pre-loading hoặc quantize model

---

## 🚨 WARNING

**PYTHONANYWHERE FREE (512MB) + MODEL LỚN (1GB) = KHÔNG TƯƠNG THÍCH!**

**Giải pháp:**
1. ✅ Tắt pre-loading: `PRELOAD_MODEL=false` (lazy load khi cần)
2. ✅ Tắt Grad-CAM: `ENABLE_GRADCAM=false`
3. ✅ Quantize model xuống < 400MB
4. ✅ Upgrade PythonAnywhere plan (Hacker: $5/month, 1GB RAM)

**PythonAnywhere có lợi thế:**
- Timeout 300s (5 phút) vs Render 30-60s
- Không spin down → Lazy loading hoàn toàn OK!
