# 🎯 DEPLOY LÊN PYTHONANYWHERE

## ✅ TLDR - ĐỌC CÁI NÀY TRƯỚC!

**Code của bạn SẴN SÀNG deploy!**

- Model: 95MB (nhỏ, hoàn hảo!)
- Memory peak: 400MB < 512MB ✅
- Grad-CAM: BẬT được! ✅
- Timeout: 300s (dư thừa!)

**BẮT ĐẦU TẠI:** `START_HERE.md`

---

## 📂 CÁC FILE QUAN TRỌNG

### 1. BẮT ĐẦU (MUST READ!)
- **`START_HERE.md`** ← ĐỌC ĐẦU TIÊN!
- **`READY_TO_DEPLOY.md`** ← Tổng kết mọi thứ
- **`QUICK_DEPLOY_CHECKLIST.md`** ← Checklist từng bước (IN RA!)

### 2. HƯỚNG DẪN CHI TIẾT
- **`DEPLOY_PYTHONANYWHERE_STEP_BY_STEP.md`** ← Commands đầy đủ

### 3. TEMPLATES (COPY & PASTE)
- **`wsgi_template.py`** ← WSGI config
- **`.env.pythonanywhere.template`** ← Environment variables

### 4. TÀI LIỆU KỸ THUẬT (Optional)
- `FINAL_ANSWER.md` - Tại sao model 95MB OK
- `MEMORY_REALITY_CHECK.md` - Memory analysis
- `RENDER_VS_PYTHONANYWHERE.md` - Platform comparison
- `DEPLOYMENT_FILES_INDEX.md` - Index tất cả files

---

## 🚀 QUICK START (3 BƯỚC)

### 1. ĐỌC
```bash
# Mở file này
START_HERE.md
```

### 2. FOLLOW
```bash
# In ra và tick từng bước
QUICK_DEPLOY_CHECKLIST.md
```

### 3. DEPLOY
```bash
# Tham khảo commands
DEPLOY_PYTHONANYWHERE_STEP_BY_STEP.md
```

**Thời gian:** ~30-45 phút

---

## ⚙️ CONFIG CHÍNH

### .env file:
```bash
PRELOAD_MODEL=false       # Lazy load
ENABLE_GRADCAM=true       # ✅ BẬT!
ALLOWED_HOSTS=yourusername.pythonanywhere.com
```

### WSGI file:
```python
# Copy từ wsgi_template.py
# Nhớ thay 'yourusername'!
```

---

## 📊 KẾT QUẢ MONG ĐỢI

| Metric | Value |
|--------|-------|
| Memory idle | 150-200 MB |
| Memory loaded | 280-310 MB |
| Peak memory | ~400 MB ✅ |
| Request đầu | ~70s |
| Request sau | ~10s |
| Grad-CAM | ✅ Enabled |

---

## ✅ SUCCESS

Deploy thành công khi:
- Health endpoint OK
- Upload ảnh có heatmap
- Memory < 350MB idle
- Không có "Killed" errors

---

## 🐛 PROBLEMS?

**App bị kill?**  
→ Edit `.env`: `ENABLE_GRADCAM=false`

**Import errors?**  
→ `pip install -r requirements.txt`

**Chi tiết troubleshooting:**  
→ Xem trong `DEPLOY_PYTHONANYWHERE_STEP_BY_STEP.md`

---

## 🎯 ACTION ITEMS

- [ ] Đọc `START_HERE.md`
- [ ] In `QUICK_DEPLOY_CHECKLIST.md`
- [ ] Tạo account PythonAnywhere
- [ ] Follow checklist
- [ ] Deploy!
- [ ] Test và verify

---

## 📞 CẦN GIÚP?

1. Đọc `START_HERE.md` - Overview
2. Đọc `FINAL_ANSWER.md` - Hiểu tại sao OK
3. Check error log trên PythonAnywhere
4. Đọc Troubleshooting section

---

## 🎉 LET'S GO!

**Mở file:** `START_HERE.md`

**Deploy:** https://www.pythonanywhere.com

**Good luck!** 🚀
