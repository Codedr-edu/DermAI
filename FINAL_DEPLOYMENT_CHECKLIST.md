# ✅ FINAL DEPLOYMENT CHECKLIST - Render.com

**Date:** 2025-10-10
**Branch:** cursor/optimize-dermatology-ai-for-memory-c262

---

## 📋 PRE-DEPLOYMENT CHECKS

### 1. Model Preparation ✓

```bash
# Run quantization (if not done yet)
□ python Dermal/quantize_model.py

# Verify quantized model
□ ls -lh Dermal/dermatology_stage1_fp16.keras
  Expected: ~48MB (half of original 95MB)

# Test accuracy
□ Run test script to verify predictions

# Decide: Use quantized model?
□ If accuracy OK: 
    mv Dermal/dermatology_stage1.keras Dermal/dermatology_stage1_original.keras
    mv Dermal/dermatology_stage1_fp16.keras Dermal/dermatology_stage1.keras
□ If accuracy NOT OK:
    Keep original model
    Consider upgrade to Render Starter
```

---

### 2. Memory Tests ✓

```bash
# Run comprehensive test
□ python test_before_deploy.py

Expected results:
□ Django imports: < 100MB
□ Model loading: < 150MB
□ Peak during prediction: < 450MB (with quantize) or < 490MB (without)
□ Prediction time: < 10s

If peak > 490MB:
□ MUST quantize model
□ OR upgrade to Starter plan
```

---

### 3. Code Review ✓

**Check files for issues:**

```bash
# Verify no syntax errors
□ python -m py_compile Dermal/*.py
□ python -m py_compile dermai/*.py

# Check imports
□ grep -r "import tensorflow" --include="*.py"
  Should NOT have both tensorflow AND tensorflow-cpu

# Verify settings
□ Check dermai/settings.py:
  □ DEBUG = False parsing correctly
  □ SECRET_KEY has fallback
  □ ALLOWED_HOSTS from env
  □ DB_NAME has default

# Check AI_detection.py
□ Lazy loading implemented
□ Memory cleanup present
□ Grad-CAM optimized (NumPy)
```

---

### 4. Configuration Files ✓

**render.yaml:**
```yaml
□ startCommand correct:
  "gunicorn dermai.wsgi:application --workers 1 --threads 2 --timeout 300 ..."

□ Environment variables set:
  □ ENABLE_GRADCAM = true (or false if want to save RAM)
  □ TF_CPP_MIN_LOG_LEVEL = 3
  □ OMP_NUM_THREADS = 1
  □ OPENBLAS_NUM_THREADS = 1
  □ MKL_NUM_THREADS = 1

□ Health check path: /health/

□ Build command: "./build.sh"
```

**requirements.txt:**
```bash
□ Check for conflicts:
  □ Only tensorflow-cpu (NOT tensorflow)
  □ psutil included
  □ All necessary packages present

□ Verify versions compatible
```

**build.sh:**
```bash
□ Executable: chmod +x build.sh
□ Contains:
  □ pip install --upgrade pip
  □ pip install -r requirements.txt
  □ python manage.py collectstatic --no-input
  □ python manage.py migrate
```

**static/ directory:**
```bash
□ Directory exists: mkdir -p static
□ Has README.md or placeholder file
```

---

### 5. Render.com Free Tier Limits ✓

**Verify we're within limits:**

```
✓ RAM Limit: 512MB
  Our usage (quantized): ~380-450MB peak ✅
  Our usage (original): ~485-510MB peak ⚠️

✓ Disk Limit: 1GB
  Model: ~50-95MB
  Dependencies: ~300MB
  Total: ~400-450MB ✅

✓ Timeout: 300 seconds
  Our prediction: ~5-15s ✅

✓ Build Time: 15 minutes
  Our build: ~3-5 minutes ✅

✓ Bandwidth: 100GB/month
  Depends on traffic ✅

✓ Network: Outbound HTTPS allowed ✅
```

---

### 6. Potential Issues & Solutions ✓

**Issue: OOM (Out of Memory)**

```
If happens:
□ Check /memory/ endpoint: curl https://app.onrender.com/memory/
□ If > 500MB:
  Option 1: Enable quantized model
  Option 2: Disable Grad-CAM (ENABLE_GRADCAM=false)
  Option 3: Reduce threads to 1
  Option 4: Upgrade to Starter ($7/month)
```

**Issue: Timeout on first request**

```
Cause: Lazy loading takes ~10-20s first time

Solution:
□ Add warmup request after deployment:
  curl -X POST https://app.onrender.com/upload/ \
       -F "image=@test.jpg" \
       -H "Authorization: ..."

□ Or accept 10-20s delay for first user
```

**Issue: Build fails**

```
Check build logs:
□ Model file too large? (should be < 100MB)
□ Requirements install failed? (tensorflow-cpu conflicts?)
□ collectstatic failed? (static/ directory exists?)
```

**Issue: App crashes randomly**

```
□ Check logs for OOM
□ Check memory endpoint
□ Consider:
  - Reduce --max-requests (currently 100 → try 50)
  - Disable Grad-CAM
  - Quantize model if not already
```

---

### 7. Deployment Steps ✓

```bash
# Step 1: Final code check
□ git status
□ git diff

# Step 2: Commit changes
□ git add .
□ git commit -m "Final optimization for Render deployment

- Quantized model for memory efficiency
- Lazy loading implemented
- Memory cleanup optimized
- Grad-CAM optimized with NumPy
- All pre-deployment tests passed"

# Step 3: Push to GitHub
□ git push origin cursor/optimize-dermatology-ai-for-memory-c262

# Step 4: On Render Dashboard
□ Connect GitHub repo (if not already)
□ Select branch: cursor/optimize-dermatology-ai-for-memory-c262
□ Render auto-deploys from render.yaml
□ Monitor build logs

# Step 5: Wait for build (~3-5 minutes)
□ Watch for errors in logs
□ Build should complete successfully

# Step 6: Initial health check
□ Wait for "Deploy live" message
□ Check health: curl https://your-app.onrender.com/health/
  Expected: "ok"

# Step 7: Memory check
□ curl https://your-app.onrender.com/memory/
  Expected: 
  {
    "memory": {"rss_mb": 150-180},
    "model_loaded": false,
    "gradcam_enabled": true
  }

# Step 8: First prediction (warmup)
□ Upload test image via UI
□ Wait 10-20s (model loading first time)
□ Check result and heatmap

# Step 9: Memory check after prediction
□ curl https://your-app.onrender.com/memory/
  Expected:
  {
    "memory": {"rss_mb": 380-450},
    "model_loaded": true
  }

# Step 10: Stress test
□ Upload 5-10 images consecutively
□ Monitor memory after each
□ Should stay < 490MB

# Step 11: Monitor for 24 hours
□ Check memory periodically
□ Watch for OOM in logs
□ Test with multiple users if possible
```

---

### 8. Post-Deployment Monitoring ✓

**First Hour:**
```
□ Every 15 min: curl /memory/
□ Watch Render logs for errors
□ Test uploads from different devices
```

**First Day:**
```
□ Morning, afternoon, evening: Check memory
□ Test concurrent uploads (2-3 users)
□ Monitor for crashes
```

**First Week:**
```
□ Daily memory checks
□ Monitor user feedback
□ Check for memory creep (RAM increasing over time)
```

**If Issues Occur:**
```
□ Check logs immediately
□ Check /memory/ endpoint
□ If OOM:
  - Restart app (Render dashboard)
  - Consider quantization/upgrade
□ If slow:
  - Check if model warming up (first request)
  - Check CPU usage in logs
```

---

### 9. Rollback Plan ✓

**If deployment fails:**

```bash
# Option 1: Revert commit
□ git revert HEAD
□ git push

# Option 2: Change Render branch
□ Render dashboard → Settings
□ Change branch to previous working branch

# Option 3: Disable Grad-CAM emergency
□ Render dashboard → Environment
□ Set ENABLE_GRADCAM=false
□ Redeploy

# Option 4: Upgrade to Starter
□ Render dashboard → Settings → Upgrade
□ $7/month, 2GB RAM
□ All problems solved
```

---

### 10. Success Criteria ✓

**Deployment is successful when:**

```
✅ Build completes without errors
✅ Health check returns "ok"
✅ Memory < 490MB peak
✅ Predictions work correctly
✅ Grad-CAM heatmaps display
✅ No OOM errors in logs
✅ Response time < 10s (after first request)
✅ App stable for 24+ hours
```

---

## 📊 Expected Metrics

### With Quantized Model:

```
Metric                  Expected Value
─────────────────────────────────────
Idle RAM                150-180 MB
Model loaded RAM        380-420 MB
Peak RAM (predict)      380-450 MB
First request time      15-20s (model load)
Subsequent requests     3-8s
Build time              3-5 minutes
Model file size         48MB
Total disk usage        ~400MB
Success rate            95%+
```

### Without Quantization (Original):

```
Metric                  Expected Value
─────────────────────────────────────
Idle RAM                150-180 MB
Model loaded RAM        420-450 MB
Peak RAM (predict)      480-510 MB ⚠️
First request time      15-20s
Subsequent requests     3-8s
Build time              4-6 minutes
Model file size         95MB
Total disk usage        ~450MB
Success rate            70-80% (risky!)
```

---

## 🎯 Decision Matrix

```
┌─────────────────────────────────────────────────────┐
│ WHEN TO USE WHAT                                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│ Peak RAM < 450MB after test                         │
│ → ✅ Deploy with quantized model                    │
│                                                      │
│ Peak RAM 450-490MB                                  │
│ → ⚠️ Deploy but monitor closely                     │
│ → Consider Grad-CAM=false for safety                │
│                                                      │
│ Peak RAM > 490MB                                    │
│ → ❌ Do NOT deploy                                  │
│ → Options:                                           │
│   1. Quantize model (if not done)                   │
│   2. Disable Grad-CAM                                │
│   3. Upgrade to Starter                              │
│                                                      │
│ OOM during testing                                  │
│ → ❌ MUST fix before deploy                         │
│ → Quantize + Grad-CAM=false                         │
│ → OR upgrade                                         │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 READY TO DEPLOY?

**Final Checklist:**

```
□ All tests passed (run test_before_deploy.py)
□ Model quantized (optional but recommended)
□ Config files verified
□ Code committed and pushed
□ Render.com account ready
□ Monitoring plan ready
□ Rollback plan understood

If all checked:
→ DEPLOY! 🚀

If any unchecked:
→ FIX FIRST! ⚠️
```

---

**Good luck! 🎉**

Remember:
- Monitor closely first 24h
- Check /memory/ endpoint regularly
- Don't panic if first request is slow (lazy loading)
- Have rollback plan ready

**You got this! 💪**
