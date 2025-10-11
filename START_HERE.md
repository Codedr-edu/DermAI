# 🚀 BẮT ĐẦU DEPLOY TẠI ĐÂY!

## ✅ CODE ĐÃ SẴN SÀNG!

Tôi đã kiểm tra code của bạn:
- ✅ Model chỉ 95MB (cực nhỏ, hoàn hảo!)
- ✅ Peak memory ~400MB < 512MB
- ✅ Grad-CAM có thể BẬT
- ✅ Code support cả Render và PythonAnywhere
- ✅ Không cần quantize model thêm!

---

## 📚 TÀI LIỆU DEPLOY

### 🎯 ĐỌC THEO THỨ TỰ:

#### 1. **QUICK_DEPLOY_CHECKLIST.md** ← BẮT ĐẦU TẠI ĐÂY!
Checklist nhanh, tick ✅ từng bước. In ra giấy để dễ follow!

#### 2. **DEPLOY_PYTHONANYWHERE_STEP_BY_STEP.md**
Hướng dẫn chi tiết từng bước với commands đầy đủ.

#### 3. **wsgi_template.py**
Template WSGI file, copy vào PythonAnywhere.

#### 4. **.env.pythonanywhere.template**
Template .env file, copy và sửa giá trị.

---

## ⚡ QUICK START (5 PHÚT)

### Bước 1: Tạo account
- Truy cập: https://www.pythonanywhere.com
- Sign up free
- Nhớ username của bạn: `_____________`

### Bước 2: Upload code
```bash
# Trong Bash console của PythonAnywhere
cd ~
git clone https://github.com/your-username/your-repo.git dermai
cd dermai
```

### Bước 3: Setup
```bash
# Virtual environment
mkvirtualenv --python=/usr/bin/python3.10 dermai_env
pip install -r requirements.txt

# Database
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --no-input
```

### Bước 4: Tạo .env
```bash
nano .env
# Copy từ .env.pythonanywhere.template
# Sửa SECRET_KEY và ALLOWED_HOSTS
```

### Bước 5: Config Web App
- Dashboard → Web → Add new web app → Manual config → Python 3.10
- Copy WSGI file từ `wsgi_template.py`
- Add static files mapping
- Reload!

### Bước 6: Test!
```bash
curl https://yourusername.pythonanywhere.com/health?verbose=1
```

---

## 🎯 CONFIG QUAN TRỌNG

### .env File:
```bash
SECRET_KEY=your-random-secret-key
ALLOWED_HOSTS=yourusername.pythonanywhere.com
PRELOAD_MODEL=false          # ← Lazy load
ENABLE_GRADCAM=true          # ← BẬT! Model 95MB, safe!
DJANGO_SERVER_MODE=true
TF_CPP_MIN_LOG_LEVEL=3
```

### Tại sao config này?
- **PRELOAD_MODEL=false:** Tiết kiệm RAM lúc start (~150MB vs ~300MB)
- **ENABLE_GRADCAM=true:** Model nhỏ (95MB), peak ~400MB < 512MB ✅
- Timeout 300s → Đủ thời gian load model (~70s)

---

## 📊 EXPECTED PERFORMANCE

| Metric | Value |
|--------|-------|
| **Memory idle** | 150-200 MB |
| **Memory loaded** | 280-310 MB |
| **Peak memory** | ~400 MB < 512 MB ✅ |
| **Request đầu** | 65-70s (load model) |
| **Request sau** | 8-12s (có Grad-CAM!) |
| **Heatmap** | ✅ Có! |

---

## ✅ SUCCESS CRITERIA

Deploy thành công khi:

✅ Health endpoint: `{"status": "ok", "model_loaded": false}`  
✅ Memory idle: 150-200MB  
✅ Upload ảnh lần 1: ~70s, có heatmap  
✅ Upload ảnh lần 2: ~10s, có heatmap  
✅ Không có "Killed" trong error log  

---

## 🐛 TROUBLESHOOTING NHANH

**App bị kill:**
→ Edit `.env`: `ENABLE_GRADCAM=false`, reload

**Import errors:**
→ `workon dermai_env`, `pip install -r requirements.txt`

**Static files không load:**
→ Check static mapping trong Web tab

**CSRF errors:**
→ Check `ALLOWED_HOSTS` trong `.env`

---

## 📞 CẦN GIÚP?

### Đọc thêm:
- `FINAL_ANSWER.md` - Giải thích tại sao model 95MB OK với Grad-CAM
- `MEMORY_REALITY_CHECK.md` - Hiểu memory usage chi tiết
- `RENDER_VS_PYTHONANYWHERE.md` - So sánh 2 platforms

### Kiểm tra:
```bash
# Model file
ls -lh ~/dermai/Dermal/*.keras
# Phải thấy: 95M

# Memory status
curl https://yourusername.pythonanywhere.com/memory-status

# Error log
# Dashboard → Web → Error log
```

---

## 🎉 SẴN SÀNG?

1. Đọc `QUICK_DEPLOY_CHECKLIST.md`
2. Follow từng bước trong `DEPLOY_PYTHONANYWHERE_STEP_BY_STEP.md`
3. Deploy!

**Tổng thời gian:** ~30-45 phút (nếu follow đúng)

**App sẽ live tại:**
```
https://yourusername.pythonanywhere.com
```

---

## 💡 PRO TIPS

1. **In ra checklist** để dễ theo dõi
2. **Generate SECRET_KEY** bằng:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
3. **Test health endpoint** sau mỗi bước quan trọng
4. **Check error log** nếu có vấn đề
5. **Request đầu chậm (70s) là BÌNH THƯỜNG!** (đang load model)

---

## 🚀 LET'S GO!

Mở file `QUICK_DEPLOY_CHECKLIST.md` và bắt đầu tick ✅!

Good luck! 🎉
