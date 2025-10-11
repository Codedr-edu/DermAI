# 🎭 Wrapped Model (Monkey Patching) - Giải thích Chi Tiết

## ❓ "Wrapped model" là gì?

**Không phải là "wrapped model"!** Đây là kỹ thuật **"monkey patching"** để capture activations cho Grad-CAM.

Tôi sẽ giải thích **TẠI SAO** cần làm vậy và **NÓ HOẠT ĐỘNG NHƯ THẾ NÀO**.

---

## 🎯 Vấn đề: Làm sao lấy được activations từ layer giữa model?

### Model là gì?

```python
# EfficientNetV2S model:
Input (300x300x3)
    ↓
Layer 1 (Conv)
    ↓
Layer 2 (Conv) 
    ↓
Layer 3 (Conv)
    ↓
...
    ↓
Layer 50 (Last Conv) ← LAYER NÀY chúng ta cần!
    ↓
Dense Layer
    ↓
Output (7 classes)
```

**Vấn đề:**
```python
# Khi predict bình thường:
predictions = model(image)
# → Chỉ có OUTPUT cuối cùng (7 classes)
# → KHÔNG có kết quả từ Layer 50!
```

**Grad-CAM cần:**
```python
# Cần CẢ HAI:
1. Predictions (output cuối)
2. Activations từ Layer 50 (conv_outputs)

# Để tính gradients:
gradients = d(predictions) / d(conv_outputs)
```

---

## 🔧 Giải pháp: 3 cách để lấy activations

### ❌ Cách 1: Tạo model mới (KHÔNG tốt)

```python
# Tạo model mới chỉ tới layer 50
from tensorflow.keras.models import Model

# Find layer
target_layer = model.get_layer('block7a_project_conv')

# Tạo model mới
activation_model = Model(
    inputs=model.input,
    outputs=[target_layer.output, model.output]
)

# Predict
conv_outputs, predictions = activation_model(image)
```

**Vấn đề:**
```
❌ Tạo model MỚI → Tốn thêm RAM!
❌ Phải maintain 2 models
❌ Phức tạp khi có nhiều layers
```

---

### ❌ Cách 2: Dùng hooks (TensorFlow không support tốt)

```python
# PyTorch có hooks, TensorFlow không có built-in
# Phải dùng tf.keras.backend functions → Phức tạp
```

---

### ✅ Cách 3: Monkey Patching (TỐT NHẤT!)

**Ý tưởng:** Tạm thời "hack" layer để nó LƯU output khi chạy!

```python
# Bước 1: Tìm layer cần capture
target_layer = get_layer_by_name(model, 'block7a_project_conv')

# Bước 2: Lưu hàm gốc
original_call = target_layer.call

# Bước 3: Tạo hàm "wrapper" (bọc lại)
def wrapped_call(inputs, *args, **kwargs):
    # Gọi hàm gốc (chạy bình thường)
    output = original_call(inputs, *args, **kwargs)
    
    # LƯU output vào biến global!
    global conv_outputs
    conv_outputs = output
    
    # Return như bình thường
    return output

# Bước 4: THAY hàm gốc bằng wrapper
target_layer.call = wrapped_call

# Bước 5: Chạy model
predictions = model(image)
# → wrapped_call được gọi
# → conv_outputs được lưu!

# Bước 6: Khôi phục lại hàm gốc
target_layer.call = original_call

# Giờ ta có CẢ HAI:
# - predictions (từ model)
# - conv_outputs (từ wrapped_call)
```

---

## 📝 Code thực tế trong AI_detection.py

### Code đầy đủ:

```python
def compute_gradcam_manual(batch_np, model, target_layer_name, pred_index=None):
    """
    Optimized Grad-CAM computation with memory efficiency
    Uses monkey patching to capture intermediate activations
    """
    model_input_dtype = model.inputs[0].dtype
    x = tf.convert_to_tensor(batch_np, dtype=model_input_dtype)
    
    # 🔍 BƯỚC 1: Tìm layer cần capture
    target_layer = get_layer_by_name(model, target_layer_name)
    
    if target_layer is None:
        raise RuntimeError(f"Could not find layer '{target_layer_name}'")
    
    print(f"  ✅ Target: {target_layer.name}")
    
    # 🎯 BƯỚC 2: Setup monkey patching
    conv_outputs = None  # Biến để lưu activations
    
    # Lưu hàm gốc
    original_call = target_layer.call
    
    # 🎭 BƯỚC 3: Tạo wrapper function
    def wrapped_call(inputs, *args, **kwargs):
        # Gọi hàm gốc
        output = original_call(inputs, *args, **kwargs)
        
        # LƯU output!
        nonlocal conv_outputs
        conv_outputs = output
        
        return output
    
    # 🔄 BƯỚC 4: Thay thế hàm gốc
    target_layer.call = wrapped_call
    
    try:
        # 🚀 BƯỚC 5: Chạy model
        with tf.GradientTape() as tape:
            tape.watch(x)
            predictions = model(x, training=False)
            # ↑ Khi model chạy:
            # - Khi tới target_layer → wrapped_call được gọi
            # - wrapped_call lưu output vào conv_outputs
            # - Model tiếp tục chạy như bình thường
            
            if conv_outputs is None:
                raise RuntimeError(f"Failed to capture {target_layer_name}")
            
            if pred_index is None:
                pred_index = tf.argmax(predictions[0])
            
            class_channel = predictions[0, pred_index]
        
        # Tính gradients
        grads = tape.gradient(class_channel, conv_outputs)
        
    finally:
        # 🔙 BƯỚC 6: Khôi phục hàm gốc (QUAN TRỌNG!)
        target_layer.call = original_call
    
    # ... tiếp tục tính heatmap ...
    
    return heatmap, predictions
```

---

## 🎬 Hình ảnh hóa - Quá trình hoạt động

### TRƯỚC monkey patching:

```
User: predictions = model(image)

Model execution:
┌────────────────────────────────────┐
│ Input                               │
│   ↓                                 │
│ Layer 1 → output1                  │ ← Mất đi
│   ↓                                 │
│ Layer 2 → output2                  │ ← Mất đi
│   ↓                                 │
│ Target Layer → conv_outputs        │ ← MUỐN LẤY CÁI NÀY!
│   ↓                                 │  (nhưng không có cách)
│ Layer 4 → output4                  │ ← Mất đi
│   ↓                                 │
│ Output Layer → predictions         │ ← Chỉ có cái này
└────────────────────────────────────┘

Result: predictions ✅
        conv_outputs ❌ (không có)
```

### SAU monkey patching:

```
User: predictions = model(image)

Model execution:
┌────────────────────────────────────┐
│ Input                               │
│   ↓                                 │
│ Layer 1 → output1                  │
│   ↓                                 │
│ Layer 2 → output2                  │
│   ↓                                 │
│ Target Layer (WRAPPED!) 🎭         │
│   ├→ original_call(input)          │
│   ├→ output = result               │
│   ├→ SAVE to conv_outputs! 💾      │ ← CAPTURED!
│   └→ return output                 │
│   ↓                                 │
│ Layer 4 → output4                  │
│   ↓                                 │
│ Output Layer → predictions         │
└────────────────────────────────────┘

Result: predictions ✅
        conv_outputs ✅ (đã capture!)
```

---

## 💡 Ví dụ dễ hiểu - Nghe lén điện thoại

### Scenario: Bạn muốn biết ai đang gọi điện cho bạn

**Cách thông thường:**
```
Phone call flow:
Caller → Phone network → Your phone → You answer

Bạn chỉ biết khi phone ringing
→ Không biết ai gọi cho tới khi nhấc máy
```

**Monkey patching = Nghe lén:**
```
Phone call flow:
Caller → Phone network → [SPY DEVICE 🎧] → Your phone → You

Spy device:
1. Nhận cuộc gọi (pass through)
2. GHI LẠI caller ID! 📝
3. Chuyển tiếp đến phone (như bình thường)

Kết quả:
- Bạn nhận cuộc gọi bình thường ✅
- Spy device có caller ID! ✅
```

**Áp dụng vào code:**

```python
# Hàm gốc = Điện thoại bình thường
original_call = phone.receive_call

# Wrapper = Spy device
def wrapped_receive_call(caller):
    # Ghi lại caller ID
    print(f"📝 Spy: Caller is {caller}")
    caller_id = caller  # LƯU LẠI!
    
    # Chuyển tiếp như bình thường
    return original_call(caller)

# Cắm spy device vào
phone.receive_call = wrapped_receive_call

# Khi có cuộc gọi:
phone.receive_call("John")
# → wrapped_receive_call được gọi
# → Ghi lại "John"
# → Chuyển tiếp bình thường

# Khôi phục
phone.receive_call = original_call
```

---

## 🔍 Tại sao phải dùng `nonlocal`?

### Vấn đề: Scope của biến

```python
# SAI - Không dùng nonlocal:
def compute_gradcam():
    conv_outputs = None  # Biến ở scope ngoài
    
    def wrapped_call(inputs):
        output = original_call(inputs)
        conv_outputs = output  # ❌ Tạo biến MỚI trong function!
        return output
    
    # ...
    if conv_outputs is None:  # ← Vẫn là None! ❌
        print("Failed!")

# ĐÚNG - Dùng nonlocal:
def compute_gradcam():
    conv_outputs = None  # Biến ở scope ngoài
    
    def wrapped_call(inputs):
        nonlocal conv_outputs  # ✅ Trỏ tới biến bên ngoài!
        output = original_call(inputs)
        conv_outputs = output  # ✅ Gán vào biến bên ngoài!
        return output
    
    # ...
    if conv_outputs is None:  # ← Đã có giá trị! ✅
        print("Success!")
```

**Ví dụ dễ hiểu:**

```python
# Không có nonlocal = Viết vào giấy nháp
notebook = None  # Sổ tay chính

def write_note():
    notebook = "Important note"  # Viết vào giấy nháp (biến mới!)
    # Giấy nháp bị vứt khi function kết thúc

write_note()
print(notebook)  # None ❌ (sổ tay chính vẫn trống!)

# Có nonlocal = Viết vào sổ tay chính
notebook = None

def write_note():
    nonlocal notebook  # Dùng sổ tay chính!
    notebook = "Important note"  # Viết vào sổ tay chính

write_note()
print(notebook)  # "Important note" ✅
```

---

## 🛡️ Tại sao phải dùng `try-finally`?

### Vấn đề: Nếu có lỗi giữa chừng?

```python
# SAI - Không dùng try-finally:
target_layer.call = wrapped_call  # Thay hàm gốc

# Chạy model
predictions = model(x)  # ← Nếu có lỗi ở đây???

# Khôi phục
target_layer.call = original_call  # ← KHÔNG BAO GIỜ CHẠY! ❌
```

**Hậu quả:**
```
Layer vẫn dùng wrapped_call!
→ Lần predict tiếp theo → LỖI!
→ Model bị "hỏng" vĩnh viễn!
```

**Giải pháp: try-finally**

```python
# ĐÚNG - Dùng try-finally:
target_layer.call = wrapped_call  # Thay hàm gốc

try:
    # Chạy model
    predictions = model(x)  # Nếu có lỗi...
except Exception as e:
    print(f"Error: {e}")
finally:
    # LUÔN LUÔN chạy (dù có lỗi hay không!)
    target_layer.call = original_call  # ✅ Khôi phục
```

**Ví dụ thực tế:**

```python
# Như mượn ô:
# SAI:
borrowed_umbrella = True
walk_in_rain()  # Nếu bị ngã giữa đường???
return_umbrella()  # ← KHÔNG BAO GIỜ TRẢ! ❌

# ĐÚNG:
borrowed_umbrella = True
try:
    walk_in_rain()  # Có thể ngã
except:
    print("Fell down!")
finally:
    return_umbrella()  # ✅ LUÔN LUÔN TRẢ (dù có ngã)
```

---

## 🔄 So sánh TRƯỚC và SAU

### TRƯỚC (code CŨ - nếu có):

Không có thay đổi! Code monkey patching vẫn GIỐNG NHAU!

**Lý do:** Monkey patching là cách DUY NHẤT để capture activations trong TensorFlow mà không tạo model mới.

### SAU (code MỚI):

CŨNG GIỐNG! Nhưng có optimization ở phần XỬ LÝ sau khi capture:

```python
# SAU khi capture (KHÁC BIỆT):

# CŨ:
grads = tape.gradient(class_channel, conv_outputs)
pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))  # TF tensor
heatmap = tf.reduce_sum(conv_outputs[0] * pooled_grads)  # TF tensor

# MỚI:
grads = tape.gradient(class_channel, conv_outputs)
pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2)).numpy()  # NumPy!
conv_outputs_np = conv_outputs[0].numpy()  # NumPy!
del grads, conv_outputs  # Xóa TF tensors!
heatmap = np.sum(conv_outputs_np * pooled_grads)  # NumPy!
```

---

## ✅ Tổng kết

### "Wrapped model" thực chất là gì?

**KHÔNG PHẢI wrapped model!**

Đây là kỹ thuật **Monkey Patching**:
- Tạm thời **THAY HÀM** của layer
- **CAPTURE** output khi layer chạy
- **KHÔI PHỤC** hàm gốc sau đó

### Tại sao cần làm vậy?

```
Vấn đề: 
Cần activations từ layer giữa model

Giải pháp khác:
❌ Tạo model mới → Tốn RAM
❌ Dùng hooks → TF không support tốt

Monkey patching:
✅ Không tạo model mới
✅ Không tốn thêm RAM
✅ Capture chính xác
✅ Khôi phục được
```

### Code có thay đổi không?

**KHÔNG!** Monkey patching vẫn GIỐNG HỆT!

**Chỉ khác:** Sau khi capture, xử lý bằng NumPy thay vì TensorFlow.

### An toàn không?

**CÓ!** Vì:
```python
try:
    # Thay hàm
    target_layer.call = wrapped_call
    # Chạy model
    predictions = model(x)
finally:
    # LUÔN LUÔN khôi phục (dù có lỗi!)
    target_layer.call = original_call
```

---

## 💡 Ví dụ tổng hợp - Máy ATM

**Bạn muốn biết transaction details TRƯỚC KHI tiền ra:**

```python
# ATM gốc:
def withdraw_money(amount):
    check_balance(amount)
    deduct_from_account(amount)
    dispense_cash(amount)
    return "Done"

# Bạn chỉ biết "Done", không biết chi tiết!

# Monkey patch = Hack ATM:
original_withdraw = atm.withdraw_money
transaction_log = None

def wrapped_withdraw(amount):
    global transaction_log
    
    # Chạy bình thường
    result = original_withdraw(amount)
    
    # CAPTURE transaction details!
    transaction_log = {
        'amount': amount,
        'time': now(),
        'balance_after': get_balance()
    }
    
    return result  # User vẫn nhận kết quả bình thường

# Hack ATM
atm.withdraw_money = wrapped_withdraw

# User withdraw
atm.withdraw_money(100)
# → User nhận tiền bình thường ✅
# → transaction_log có đầy đủ info! ✅

# Khôi phục ATM
atm.withdraw_money = original_withdraw
```

---

**Bottom line:** "Wrapped model" = **Monkey Patching** = "Hack" layer để capture output mà không làm thay đổi model gốc! 🎭
