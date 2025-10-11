# 🔢 QUANTIZATION LÀ GÌ VÀ CÁCH HOẠT ĐỘNG

## 🎯 GIẢI THÍCH ĐỆ NHẤT

### Quantization = Giảm độ chính xác số để tiết kiệm RAM

**Ví dụ đơn giản:**

Bạn có 1 con số: **3.14159265358979323846...**

**FP32 (Float32 - 32 bit):**
- Lưu số với độ chính xác cao: `3.14159265`
- Mỗi số chiếm: **4 bytes** (32 bit)

**FP16 (Float16 - 16 bit):**
- Lưu số với độ chính xác thấp hơn: `3.141`
- Mỗi số chiếm: **2 bytes** (16 bit)

**→ Tiết kiệm: 50% memory!**

---

## 💾 ÁP DỤNG VÀO MODEL

### Model là gì?
Model = **HÀNG TRIỆU** con số (weights/parameters)

**Ví dụ:**
```
Model có 10 triệu parameters
```

**FP32:**
```
10,000,000 params × 4 bytes = 40 MB
```

**FP16 (quantized):**
```
10,000,000 params × 2 bytes = 20 MB
→ Tiết kiệm 50%!
```

---

## 🧮 MODEL CỦA BẠN

### Hiện tại:

```bash
$ ls -lh Dermal/dermatology_stage1.keras
95M
```

**→ Model đã CỰC KỲ NHỎ rồi!**

Có thể:
- Đã được quantize từ trước
- Hoặc architecture nhỏ gọn
- Hoặc đã được optimize

**→ KHÔNG CẦN quantize thêm!** ✅

---

## 📊 SO SÁNH

| Type | Size per param | Example Model | Total Size |
|------|----------------|---------------|------------|
| **FP32** | 4 bytes | 100M params | ~400 MB |
| **FP16** | 2 bytes | 100M params | ~200 MB |
| **INT8** | 1 byte | 100M params | ~100 MB |

**Trade-off:**
- Càng giảm độ chính xác → Càng nhỏ
- Nhưng có thể giảm accuracy!

---

## 🔧 CÁCH QUANTIZE (NẾU CẦN)

### Method 1: TensorFlow Lite Converter (Post-training quantization)

```python
import tensorflow as tf

# Load model gốc
model = tf.keras.models.load_model('model.keras')

# Convert sang TFLite với quantization
converter = tf.lite.TFLiteConverter.from_keras_model(model)

# Dynamic range quantization (FP32 → FP16)
converter.optimizations = [tf.lite.Optimize.DEFAULT]

# Convert
tflite_model = converter.convert()

# Save
with open('model_quantized.tflite', 'wb') as f:
    f.write(tflite_model)

print(f"Original size: {os.path.getsize('model.keras') / 1024 / 1024:.1f} MB")
print(f"Quantized size: {len(tflite_model) / 1024 / 1024:.1f} MB")
```

**Kết quả:**
```
Original size: 400.0 MB
Quantized size: 200.0 MB  # Giảm 50%!
```

---

### Method 2: Mixed Precision (Trong TensorFlow)

```python
# Khi train model
from tensorflow.keras import mixed_precision

# Enable mixed precision (FP16)
policy = mixed_precision.Policy('mixed_float16')
mixed_precision.set_global_policy(policy)

# Train model như bình thường
model = create_model()
model.compile(...)
model.fit(...)
```

**Lợi ích:**
- Model tự động dùng FP16 cho tính toán
- Vẫn giữ FP32 cho các operations quan trọng
- Tự động convert

---

### Method 3: Manual Quantization (Advanced)

```python
import tensorflow as tf
import numpy as np

# Load model
model = tf.keras.models.load_model('model.keras')

# Get weights
weights = model.get_weights()

# Quantize mỗi weight từ FP32 → FP16
quantized_weights = []
for w in weights:
    # Convert to FP16
    w_fp16 = w.astype(np.float16)
    quantized_weights.append(w_fp16)

# Set weights mới
model.set_weights(quantized_weights)

# Save
model.save('model_quantized.keras')
```

⚠️ **Lưu ý:** Method này đơn giản nhưng có thể làm giảm accuracy!

---

## 🔬 CHECK MODEL ĐÃ QUANTIZED CHƯA

```python
import tensorflow as tf

# Load model
model = tf.keras.models.load_model('Dermal/dermatology_stage1.keras')

# Check dtype của weights
for layer in model.layers:
    if hasattr(layer, 'weights') and layer.weights:
        for weight in layer.weights:
            print(f"{layer.name}: {weight.dtype}")
            break  # Chỉ check weight đầu
        break  # Chỉ check layer đầu
```

**Output:**
```python
# Nếu FP32 (chưa quantize):
conv2d: <dtype: 'float32'>

# Nếu FP16 (đã quantize):
conv2d: <dtype: 'float16'>
```

---

## 💡 KHI NÀO CẦN QUANTIZE?

### ✅ NÊN quantize nếu:

1. **Model > 500MB**
   ```
   Model: 1000 MB
   RAM limit: 512 MB
   → PHẢI quantize!
   ```

2. **Memory usage quá cao**
   ```
   Peak memory: 600 MB > 512 MB
   → Quantize để giảm xuống
   ```

3. **Deploy lên mobile/edge devices**
   ```
   Mobile RAM: 2-4 GB
   Model FP32: 500 MB
   → Quantize để app mượt hơn
   ```

### ❌ KHÔNG CẦN quantize nếu:

1. **Model đã nhỏ (<200MB)**
   ```
   Model của bạn: 95 MB ✅
   Peak memory: 400 MB < 512 MB ✅
   → KHÔNG CẦN quantize!
   ```

2. **RAM đủ dư**
   ```
   Available: 512 MB
   Usage: 400 MB
   Buffer: 112 MB ✅
   ```

3. **Accuracy quan trọng hơn size**
   ```
   Medical diagnosis model
   → Giữ FP32 để accuracy tối đa
   ```

---

## 📊 QUANTIZATION METHODS COMPARISON

| Method | Size Reduction | Accuracy Loss | Complexity |
|--------|----------------|---------------|------------|
| **FP32 → FP16** | 50% | ~0-2% | Dễ |
| **FP32 → INT8** | 75% | ~2-5% | Trung bình |
| **FP32 → INT4** | 87.5% | ~5-10% | Khó |
| **Pruning + Quant** | 90%+ | ~3-8% | Rất khó |

---

## 🔧 SCRIPT QUANTIZE TỰ ĐỘNG

Tạo file `Dermal/quantize_model.py`:

```python
#!/usr/bin/env python3
"""
Quantize TensorFlow model từ FP32 sang FP16
Chỉ chạy nếu model > 500MB!
"""

import tensorflow as tf
import os

def quantize_model(input_path, output_path):
    """Quantize model using TFLite converter"""
    
    # Check input file
    if not os.path.exists(input_path):
        print(f"❌ Model không tồn tại: {input_path}")
        return
    
    original_size = os.path.getsize(input_path) / (1024 * 1024)
    print(f"📦 Original model: {original_size:.1f} MB")
    
    # Nếu model < 200MB, không cần quantize
    if original_size < 200:
        print(f"✅ Model đã đủ nhỏ ({original_size:.1f} MB < 200 MB)")
        print("   Không cần quantize!")
        return
    
    print("🔄 Đang quantize model...")
    
    # Load model
    model = tf.keras.models.load_model(input_path, compile=False)
    
    # Convert to TFLite with quantization
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    # Float16 quantization
    converter.target_spec.supported_types = [tf.float16]
    
    # Convert
    tflite_model = converter.convert()
    
    # Save
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    
    quantized_size = len(tflite_model) / (1024 * 1024)
    reduction = (1 - quantized_size / original_size) * 100
    
    print(f"✅ Quantized model: {quantized_size:.1f} MB")
    print(f"📉 Giảm: {reduction:.1f}%")
    print(f"💾 Saved to: {output_path}")

if __name__ == "__main__":
    INPUT = "Dermal/dermatology_stage1.keras"
    OUTPUT = "Dermal/dermatology_stage1_quantized.tflite"
    
    quantize_model(INPUT, OUTPUT)
```

**Chạy:**
```bash
python Dermal/quantize_model.py
```

**Output:**
```
📦 Original model: 95.0 MB
✅ Model đã đủ nhỏ (95.0 MB < 200 MB)
   Không cần quantize!
```

---

## 🎯 VỚI MODEL CỦA BẠN

### Model hiện tại: 95MB

```
Django + Python:       70 MB
TensorFlow:           120 MB
Model (95MB):          95 MB
───────────────────────────
Idle:                 285 MB

+ Inference:          +30 MB
+ Grad-CAM:           +85 MB
───────────────────────────
Peak:                ~400 MB < 512 MB ✅
```

**KẾT LUẬN:** KHÔNG CẦN QUANTIZE!

### Nếu quantize xuống 50MB:

```
Model (50MB):          50 MB (thay vì 95MB)
───────────────────────────
Idle:                 240 MB (tiết kiệm 45MB)
Peak:                ~355 MB (tiết kiệm 45MB)
```

**Lợi ích:** Tiết kiệm 45MB  
**Trade-off:** Có thể mất 1-2% accuracy  
**Đáng không?** KHÔNG! Vì đã dư 112MB buffer rồi!

---

## 📝 TÓM LẠI

### Quantization là gì?
→ Giảm độ chính xác số (FP32 → FP16) để tiết kiệm RAM

### Lợi ích?
→ Giảm 50% model size, giảm RAM usage

### Trade-off?
→ Có thể giảm 1-5% accuracy

### Khi nào cần?
→ Khi model > 500MB hoặc RAM không đủ

### Model 95MB của bạn?
→ **KHÔNG CẦN quantize!** Đã đủ nhỏ, peak 400MB < 512MB ✅

---

## 🚀 ACTION

**Với model 95MB:**
```bash
# KHÔNG CẦN chạy quantize script
# Deploy trực tiếp với config:

PRELOAD_MODEL=false
ENABLE_GRADCAM=true     # ✅ BẬT được!
```

**Nếu sau này model lớn hơn (>500MB):**
```bash
# Lúc đó mới chạy
python Dermal/quantize_model.py

# Sau đó deploy với quantized model
```

---

## 💡 HIỂU THÊM

### Tại sao model 95MB nhỏ thế?

Có thể:
1. **Architecture nhỏ:** EfficientNet-B0/B1 (không phải B7)
2. **Đã quantize:** Ai đó đã quantize trước khi train
3. **Few layers:** Model không sâu lắm
4. **Transfer learning:** Chỉ fine-tune layers cuối

### Check architecture:

```python
import tensorflow as tf

model = tf.keras.models.load_model('Dermal/dermatology_stage1.keras')
model.summary()

# Count parameters
total_params = model.count_params()
print(f"Total parameters: {total_params:,}")
print(f"Size per param: {95 * 1024 * 1024 / total_params:.2f} bytes")
```

**Nếu kết quả ~2 bytes/param:**
→ Đã là FP16 rồi! (Đã quantize)

**Nếu kết quả ~4 bytes/param:**
→ Vẫn FP32 (chưa quantize, nhưng architecture nhỏ)

---

Rõ chưa bạn? 😊
