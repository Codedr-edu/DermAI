#!/bin/bash
# Deployment commands for Render.com

echo "🚀 Deploying to Render.com..."
echo ""

# 1. Add all changes
echo "📦 Adding files..."
git add .

# 2. Commit
echo "💾 Committing changes..."
git commit -m "Fix deployment issues and optimize for Render.com

- Fixed render.yaml syntax error
- Removed tensorflow/tensorflow-cpu conflict
- Fixed DEBUG environment variable parsing
- Added fallback values for env vars
- Created static/ directory
- Fixed database config
- Ready for production deployment with Grad-CAM enabled"

# 3. Push
echo "⬆️ Pushing to GitHub..."
git push origin cursor/optimize-dermatology-ai-for-memory-c262

echo ""
echo "✅ Done! Render will auto-deploy from render.yaml"
echo ""
echo "📊 Next steps:"
echo "  1. Wait for Render build (~5 minutes)"
echo "  2. Check health: curl https://your-app.onrender.com/health/"
echo "  3. Check memory: curl https://your-app.onrender.com/memory/"
echo "  4. Test upload via UI"
echo ""
echo "📖 See PRE_DEPLOYMENT_CHECK.md for details"
