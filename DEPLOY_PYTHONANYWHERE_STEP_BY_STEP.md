# 🚀 DEPLOY LÊN PYTHONANYWHERE - TỪNG BƯỚC

## ✅ THÔNG TIN QUAN TRỌNG

**Model size:** 95MB (cực nhỏ, hoàn hảo!)  
**Peak memory:** ~400MB < 512MB ✅  
**Config:** ENABLE_GRADCAM=true (BẬT được!)  
**Timeout:** 300s (dư thừa!)

---

## 📋 BƯỚC 1: TẠO TÀI KHOẢN PYTHONANYWHERE

1. Truy cập: https://www.pythonanywhere.com/
2. Click "Pricing & signup" → "Create a Beginner account"
3. Đăng ký miễn phí (cung cấp email)
4. Verify email và login

**Username của bạn sẽ là:** `yourusername` (thay bằng username thực)  
**URL app sẽ là:** `https://yourusername.pythonanywhere.com`

---

## 📋 BƯỚC 2: UPLOAD CODE

### Option A: Dùng Git (Recommended)

1. Mở **Bash console** trong PythonAnywhere:
   - Dashboard → Consoles → Start a new console → Bash

2. Clone repository:
```bash
cd ~
git clone https://github.com/your-username/your-repo.git dermai
cd dermai

# Verify
ls -la
# Phải thấy: manage.py, Dermal/, dermai/, requirements.txt, etc.
```

### Option B: Upload ZIP

1. Nén project thành ZIP (trên máy local)
2. Dashboard → Files → Upload a file
3. Upload file ZIP
4. Mở Bash console:
```bash
cd ~
unzip your-project.zip -d dermai
cd dermai
ls -la
```

---

## 📋 BƯỚC 3: TẠO VIRTUAL ENVIRONMENT & INSTALL DEPENDENCIES

Trong Bash console:

```bash
cd ~/dermai

# Tạo virtualenv với Python 3.10
mkvirtualenv --python=/usr/bin/python3.10 dermai_env

# Activate (tự động activate sau khi tạo, nhưng để chắc chắn)
workon dermai_env

# Upgrade pip
pip install --upgrade pip

# Install dependencies (mất ~5-10 phút)
pip install -r requirements.txt

# Verify TensorFlow installed
python -c "import tensorflow as tf; print(tf.__version__)"
# Phải thấy: 2.18.0
```

**Lưu ý:** 
- Nếu bị lỗi "No space left", PythonAnywhere free có giới hạn disk
- Có thể cần xóa cache: `pip cache purge`

---

## 📋 BƯỚC 4: TẠO FILE .env

```bash
cd ~/dermai

# Tạo file .env
cat > .env << 'EOF'
# Django settings
SECRET_KEY=your-secret-key-here-change-this-to-random-string
DEBUG=False
ALLOWED_HOSTS=yourusername.pythonanywhere.com

# Model loading (QUAN TRỌNG!)
PRELOAD_MODEL=false
ENABLE_GRADCAM=true
DJANGO_SERVER_MODE=true

# TensorFlow optimizations
TF_CPP_MIN_LOG_LEVEL=3
TF_ENABLE_ONEDNN_OPTS=0
OMP_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1

# Gemini API (nếu có)
GEMINI_API_KEY=your_gemini_key_here_if_needed
EOF

# Verify
cat .env
```

**⚠️ QUAN TRỌNG:**
- Thay `yourusername` bằng username thực của bạn
- Thay `SECRET_KEY` bằng một chuỗi random:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

---

## 📋 BƯỚC 5: RUN MIGRATIONS & COLLECTSTATIC

```bash
cd ~/dermai
workon dermai_env

# Migrations
python manage.py migrate

# Tạo superuser (để vào admin)
python manage.py createsuperuser
# Username: admin
# Email: your@email.com
# Password: [nhập password]

# Collect static files
python manage.py collectstatic --no-input

# Verify static files
ls -la staticfiles/
```

---

## 📋 BƯỚC 6: CONFIG WEB APP

### 6.1: Tạo Web App

1. Dashboard → Web → Add a new web app
2. Choose: **Manual configuration** (không phải Django template!)
3. Select: **Python 3.10**
4. Click Next

### 6.2: Config Source Code

Trong Web tab:

**Code section:**
- **Source code:** `/home/yourusername/dermai`
- **Working directory:** `/home/yourusername/dermai`

### 6.3: Config Virtualenv

**Virtualenv section:**
- Enter path: `/home/yourusername/.virtualenvs/dermai_env`
- Click ✅ (checkmark)

### 6.4: Config WSGI File

Click vào link **WSGI configuration file** (màu xanh)

**XÓA HẾT** nội dung hiện tại và thay bằng:

```python
# +++++++++++ DJANGO +++++++++++
import os
import sys

# === Path setup ===
project_home = '/home/yourusername/dermai'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# === Load environment variables ===
from dotenv import load_dotenv
env_path = os.path.join(project_home, '.env')
load_dotenv(env_path)

# === Django settings ===
os.environ['DJANGO_SETTINGS_MODULE'] = 'dermai.settings'
os.environ['DJANGO_SERVER_MODE'] = 'true'  # Signal to apps.py

# === WSGI application ===
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**⚠️ QUAN TRỌNG:**
- Thay `yourusername` bằng username thực của bạn (3 chỗ!)
- Save file (Ctrl+S hoặc click Save)

---

## 📋 BƯỚC 7: CONFIG STATIC FILES

Trong Web tab, scroll xuống **Static files** section:

Click **Add a new static file mapping:**

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/dermai/staticfiles/` |
| `/media/` | `/home/yourusername/dermai/media/` |

**Lưu ý:** Thay `yourusername` bằng username thực

---

## 📋 BƯỚC 8: RELOAD WEB APP

1. Scroll lên đầu trang Web tab
2. Click nút **Reload yourusername.pythonanywhere.com** (màu xanh lá to to)
3. Đợi ~10-30 giây

---

## 📋 BƯỚC 9: KIỂM TRA

### 9.1: Check Error Log

Trong Web tab:
- Scroll xuống **Log files** section
- Click vào **Error log**

**Mong đợi thấy:**
```
ℹ️ Model pre-loading disabled (PRELOAD_MODEL=false)
[timestamp] [info] Application startup complete.
```

**KHÔNG nên thấy:**
- Python errors
- Import errors
- "Killed" message

### 9.2: Test Health Endpoint

Mở browser hoặc trong Bash console:

```bash
curl https://yourusername.pythonanywhere.com/health?verbose=1
```

**Mong đợi:**
```json
{
  "status": "ok",
  "model_loaded": false,
  "message": "Model will load on first request",
  "gradcam_enabled": true
}
```

### 9.3: Test Memory Status

```bash
curl https://yourusername.pythonanywhere.com/memory-status
```

**Mong đợi:**
```json
{
  "status": "ok",
  "memory": {
    "rss_mb": 150-200,
    "percent": 30-40
  },
  "model_loaded": false,
  "gradcam_enabled": true
}
```

---

## 📋 BƯỚC 10: TEST UPLOAD ẢNH

### 10.1: Tạo User Account

1. Truy cập: `https://yourusername.pythonanywhere.com/signup`
2. Đăng ký account test
3. Login

### 10.2: Upload Ảnh Lần Đầu

1. Vào trang upload
2. Chọn ảnh da (bất kỳ)
3. Upload

**Mong đợi:**
- Loading ~60-70 giây (BÌNH THƯỜNG! Đang load model)
- Thấy kết quả prediction
- **Thấy heatmap visualization** ✅ (màu đỏ trên ảnh)
- Không bị timeout (vì có 300s)

### 10.3: Upload Ảnh Lần 2

Upload ảnh khác:

**Mong đợi:**
- Nhanh hơn ~8-12 giây (model đã load)
- Vẫn có heatmap
- Smooth!

### 10.4: Check Memory Sau Upload

```bash
curl https://yourusername.pythonanywhere.com/memory-status
```

**Mong đợi:**
```json
{
  "memory": {
    "rss_mb": 280-310,  # Idle sau khi load model
  },
  "model_loaded": true
}
```

**Nếu rss_mb > 450MB:** ⚠️ Nguy hiểm, có thể bị OOM khi inference  
**Nếu rss_mb < 350MB:** ✅ Hoàn hảo!

---

## 🐛 TROUBLESHOOTING

### Lỗi 1: ImportError hoặc ModuleNotFoundError

**Nguyên nhân:** Dependencies chưa được cài đầy đủ

**Fix:**
```bash
workon dermai_env
pip install -r requirements.txt
# Reload web app
```

### Lỗi 2: App bị kill với "Killed" message

**Nguyên nhân:** Memory > 512MB

**Fix:**
```bash
# Edit .env
nano .env

# Tắt Grad-CAM
ENABLE_GRADCAM=false

# Save (Ctrl+X, Y, Enter)
# Reload web app
```

### Lỗi 3: Static files không load (CSS/JS không hiển thị)

**Nguyên nhân:** Static files mapping sai

**Fix:**
1. Check collectstatic đã chạy:
   ```bash
   ls -la ~/dermai/staticfiles/
   ```
2. Check static mapping trong Web tab
3. Đảm bảo path đúng: `/home/yourusername/dermai/staticfiles/`

### Lỗi 4: Request đầu tiên timeout

**Nguyên nhân:** Model quá lớn (không phải case của bạn vì model chỉ 95MB)

**Thực tế:** PythonAnywhere timeout 300s, model 95MB load ~30-40s → OK!

**Nếu vẫn timeout:**
- Check error log xem có lỗi gì không
- Model file có tồn tại không:
  ```bash
  ls -lh ~/dermai/Dermal/*.keras
  ```

### Lỗi 5: CSRF verification failed

**Nguyên nhân:** ALLOWED_HOSTS không đúng

**Fix:**
```bash
# Edit .env
nano .env

# Sửa
ALLOWED_HOSTS=yourusername.pythonanywhere.com

# Save và reload
```

---

## 📊 EXPECTED PERFORMANCE

Với model 95MB trên PythonAnywhere Free:

| Metric | Value |
|--------|-------|
| **App startup** | ~5s |
| **Memory idle** | ~150-200MB |
| **Request đầu tiên** | ~65-70s (load model + Grad-CAM) |
| **Request tiếp theo** | ~8-12s (có Grad-CAM) |
| **Memory sau load** | ~280-310MB |
| **Peak memory** | ~400MB (< 512MB ✅) |
| **Heatmap visualization** | ✅ YES |

---

## ✅ CHECKLIST CUỐI CÙNG

Deploy thành công khi:

- [ ] Health endpoint trả về `{"status": "ok"}`
- [ ] Memory status < 350MB idle
- [ ] Upload ảnh lần 1: ~60-70s, có kết quả + heatmap
- [ ] Upload ảnh lần 2: ~10s, có kết quả + heatmap
- [ ] Không có error trong error log
- [ ] Không thấy "Killed" message
- [ ] Static files load OK (CSS/JS hiển thị)
- [ ] Login/signup hoạt động

---

## 🎉 DONE!

App của bạn đã live tại:
```
https://yourusername.pythonanywhere.com
```

**Tính năng:**
- ✅ Model 95MB load nhanh
- ✅ Grad-CAM enabled (heatmap visualization)
- ✅ Memory safe (~400MB peak < 512MB)
- ✅ Timeout 300s (dư thừa!)

**Nếu cần support:**
- Check error log trong Web tab
- Check file `MEMORY_REALITY_CHECK.md` để hiểu memory usage
- Check file `FINAL_ANSWER.md` để thấy tại sao config này OK

Chúc mừng! 🚀
