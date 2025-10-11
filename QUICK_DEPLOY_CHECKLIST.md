# ✅ QUICK DEPLOY CHECKLIST

In ra checklist này và tick ✅ từng bước khi deploy!

---

## 🎯 PRE-DEPLOYMENT

- [ ] Đã có account PythonAnywhere (www.pythonanywhere.com)
- [ ] Username PythonAnywhere: `________________`
- [ ] Đã đọc `DEPLOY_PYTHONANYWHERE_STEP_BY_STEP.md`
- [ ] Model file tồn tại: `Dermal/dermatology_stage1.keras` (95MB)

---

## 📦 BƯỚC 1: UPLOAD CODE

- [ ] Mở Bash console trên PythonAnywhere
- [ ] Clone repo: `git clone https://github.com/...`
- [ ] Hoặc upload ZIP và unzip
- [ ] Code ở: `/home/yourusername/dermai`
- [ ] Verify: `ls ~/dermai/manage.py` (phải tồn tại)

---

## 🐍 BƯỚC 2: SETUP VIRTUALENV

```bash
cd ~/dermai
mkvirtualenv --python=/usr/bin/python3.10 dermai_env
pip install --upgrade pip
pip install -r requirements.txt
```

- [ ] Virtualenv tạo thành công
- [ ] Dependencies installed (mất ~5-10 phút)
- [ ] Test: `python -c "import tensorflow; print('OK')"`

---

## ⚙️ BƯỚC 3: TẠO .ENV FILE

Sử dụng template `.env.pythonanywhere.template`:

```bash
cd ~/dermai
nano .env
```

Copy nội dung từ template và sửa:

- [ ] `SECRET_KEY` = [generate random string]
- [ ] `ALLOWED_HOSTS` = `yourusername.pythonanywhere.com`
- [ ] `PRELOAD_MODEL` = `false`
- [ ] `ENABLE_GRADCAM` = `true`
- [ ] Save file (Ctrl+X, Y, Enter)

**Generate SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🗄️ BƯỚC 4: DATABASE & STATIC

```bash
cd ~/dermai
workon dermai_env
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --no-input
```

- [ ] Migrations complete
- [ ] Superuser created (username: `______`, password: `______`)
- [ ] Static files collected
- [ ] Verify: `ls ~/dermai/staticfiles/` (có files)

---

## 🌐 BƯỚC 5: CONFIG WEB APP

### 5.1: Tạo Web App
- [ ] Dashboard → Web → Add a new web app
- [ ] Manual configuration → Python 3.10
- [ ] Web app created

### 5.2: Config Paths
- [ ] Source code: `/home/yourusername/dermai`
- [ ] Working directory: `/home/yourusername/dermai`
- [ ] Virtualenv: `/home/yourusername/.virtualenvs/dermai_env`

### 5.3: Config WSGI
- [ ] Click WSGI configuration file
- [ ] XÓA HẾT nội dung cũ
- [ ] Copy từ `wsgi_template.py`
- [ ] Thay `yourusername` (3 chỗ!)
- [ ] Save file

### 5.4: Static Files Mapping
Add 2 mappings:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/dermai/staticfiles/` |
| `/media/` | `/home/yourusername/dermai/media/` |

- [ ] Static mapping `/static/` added
- [ ] Media mapping `/media/` added

---

## 🚀 BƯỚC 6: RELOAD & TEST

- [ ] Click "Reload" button (màu xanh lá to)
- [ ] Đợi 10-30 giây

### Check Error Log
- [ ] Scroll xuống Log files → Error log
- [ ] KHÔNG thấy Python errors
- [ ] Thấy: `ℹ️ Model pre-loading disabled` (OK!)

### Test Health Endpoint
```bash
curl https://yourusername.pythonanywhere.com/health?verbose=1
```

- [ ] Response: `{"status": "ok", "model_loaded": false, "gradcam_enabled": true}`

### Test Memory Status
```bash
curl https://yourusername.pythonanywhere.com/memory-status
```

- [ ] Response shows: `rss_mb: 150-200` (idle state)

---

## 🖼️ BƯỚC 7: TEST UPLOAD ẢNH

### Upload Lần 1 (Load Model)
- [ ] Truy cập: `https://yourusername.pythonanywhere.com`
- [ ] Signup/Login
- [ ] Upload ảnh da
- [ ] Đợi ~60-70 giây (BÌNH THƯỜNG!)
- [ ] Thấy kết quả prediction
- [ ] **Thấy heatmap visualization (màu đỏ/vàng trên ảnh)** ✅

### Upload Lần 2 (Model Đã Load)
- [ ] Upload ảnh khác
- [ ] Nhanh hơn (~8-12 giây)
- [ ] Vẫn có heatmap
- [ ] Response smooth

### Check Memory Sau Upload
```bash
curl https://yourusername.pythonanywhere.com/memory-status
```

- [ ] `rss_mb: 280-350` (sau khi load model)
- [ ] `model_loaded: true`
- [ ] Nếu > 450MB → ⚠️ Cân nhắc tắt Grad-CAM

---

## 🎉 DEPLOYMENT COMPLETE!

✅ **App đang live tại:**
```
https://yourusername.pythonanywhere.com
```

### Final Checks:
- [ ] Health endpoint works
- [ ] Memory < 350MB idle
- [ ] Upload ảnh có heatmap
- [ ] Không có errors trong log
- [ ] CSS/JS load correctly
- [ ] Login/signup works

---

## 📊 EXPECTED METRICS

| Metric | Expected Value |
|--------|----------------|
| Memory idle | 150-200 MB ✅ |
| Memory after load | 280-310 MB ✅ |
| Peak memory | ~400 MB < 512 MB ✅ |
| Request đầu | 65-70s ✅ |
| Request sau | 8-12s ✅ |
| Grad-CAM | Enabled ✅ |
| Heatmap | Visible ✅ |

---

## 🐛 NẾU CÓ LỖI

### App bị kill ("Killed" trong error log)
→ Edit `.env`: `ENABLE_GRADCAM=false`, reload

### Static files không load
→ Check static mapping, chạy lại `collectstatic`

### Import errors
→ `workon dermai_env`, `pip install -r requirements.txt`

### CSRF errors
→ Check `ALLOWED_HOSTS` trong `.env`

---

## 📚 TÀI LIỆU THAM KHẢO

- `DEPLOY_PYTHONANYWHERE_STEP_BY_STEP.md` - Chi tiết từng bước
- `FINAL_ANSWER.md` - Giải thích tại sao config này OK
- `MEMORY_REALITY_CHECK.md` - Hiểu memory usage
- `wsgi_template.py` - Template WSGI file
- `.env.pythonanywhere.template` - Template .env

---

**Good luck! 🚀**
