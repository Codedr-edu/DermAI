#!/bin/bash
# Complete Pre-Deployment Check Script

echo "═══════════════════════════════════════════════════════════"
echo "  🔍 COMPREHENSIVE PRE-DEPLOYMENT CHECK"
echo "═══════════════════════════════════════════════════════════"
echo ""

ISSUES=0

# Check 1: Model files
echo "📦 Check 1: Model Files"
echo "─────────────────────────────────────────────────────────"
if [ -f "Dermal/dermatology_stage1.keras" ]; then
    SIZE=$(du -h Dermal/dermatology_stage1.keras | cut -f1)
    echo "✅ Model exists: $SIZE"
else
    echo "❌ Model NOT found!"
    ISSUES=$((ISSUES + 1))
fi

if [ -f "Dermal/dermatology_stage1_fp16.keras" ]; then
    SIZE=$(du -h Dermal/dermatology_stage1_fp16.keras | cut -f1)
    echo "✅ Quantized model exists: $SIZE"
else
    echo "⚠️ Quantized model NOT found (run: python Dermal/quantize_model.py)"
fi
echo ""

# Check 2: Config files
echo "⚙️ Check 2: Configuration Files"
echo "─────────────────────────────────────────────────────────"

if [ -f "render.yaml" ]; then
    echo "✅ render.yaml exists"
    
    # Check for syntax issues
    if grep -q "rty: connectionString" render.yaml 2>/dev/null; then
        echo "❌ Syntax error in render.yaml!"
        ISSUES=$((ISSUES + 1))
    fi
    
    # Check timeout
    if grep -q "timeout 300" render.yaml 2>/dev/null; then
        echo "✅ Timeout configured (300s)"
    else
        echo "⚠️ Timeout not found in render.yaml"
    fi
else
    echo "❌ render.yaml NOT found!"
    ISSUES=$((ISSUES + 1))
fi

if [ -x "build.sh" ]; then
    echo "✅ build.sh is executable"
else
    echo "⚠️ build.sh not executable (run: chmod +x build.sh)"
fi

if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt exists"
    
    # Check for tensorflow conflict
    TF_COUNT=$(grep -c "^tensorflow==" requirements.txt 2>/dev/null || echo 0)
    TF_CPU_COUNT=$(grep -c "^tensorflow-cpu==" requirements.txt 2>/dev/null || echo 0)
    
    if [ "$TF_COUNT" -gt 0 ] && [ "$TF_CPU_COUNT" -gt 0 ]; then
        echo "❌ Both tensorflow AND tensorflow-cpu found!"
        ISSUES=$((ISSUES + 1))
    elif [ "$TF_CPU_COUNT" -gt 0 ]; then
        echo "✅ tensorflow-cpu configured (correct)"
    elif [ "$TF_COUNT" -gt 0 ]; then
        echo "⚠️ tensorflow (full) found, recommend tensorflow-cpu"
    fi
    
    # Check psutil
    if grep -q "psutil" requirements.txt; then
        echo "✅ psutil included (for memory monitoring)"
    else
        echo "⚠️ psutil not in requirements.txt"
    fi
else
    echo "❌ requirements.txt NOT found!"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# Check 3: Static directory
echo "📁 Check 3: Directories"
echo "─────────────────────────────────────────────────────────"
if [ -d "static" ]; then
    echo "✅ static/ directory exists"
else
    echo "⚠️ static/ directory not found (may cause collectstatic issues)"
    echo "   Creating it..."
    mkdir -p static
    echo "# Static files" > static/README.md
    echo "✅ Created static/ directory"
fi

if [ -d "media" ]; then
    echo "✅ media/ directory exists"
else
    echo "⚠️ media/ directory not found"
fi
echo ""

# Check 4: Python syntax
echo "🐍 Check 4: Python Syntax"
echo "─────────────────────────────────────────────────────────"
SYNTAX_ERRORS=0

for file in Dermal/*.py dermai/*.py; do
    if [ -f "$file" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            : # Success, do nothing
        else
            echo "❌ Syntax error in: $file"
            SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
        fi
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo "✅ All Python files compile OK"
else
    echo "❌ Found $SYNTAX_ERRORS file(s) with syntax errors"
    ISSUES=$((ISSUES + SYNTAX_ERRORS))
fi
echo ""

# Check 5: Critical settings
echo "⚙️ Check 5: Django Settings"
echo "─────────────────────────────────────────────────────────"

if grep -q "SECRET_KEY.*=.*os.getenv.*'SECRET_KEY'" dermai/settings.py; then
    if grep -q "SECRET_KEY.*,.*'" dermai/settings.py; then
        echo "✅ SECRET_KEY has fallback"
    else
        echo "⚠️ SECRET_KEY no fallback (may crash if not set)"
    fi
else
    echo "⚠️ SECRET_KEY config not found"
fi

if grep -q "DEBUG.*=.*lower().*in" dermai/settings.py; then
    echo "✅ DEBUG parses correctly"
else
    echo "⚠️ DEBUG parsing may be incorrect"
fi
echo ""

# Check 6: Git status
echo "🔀 Check 6: Git Status"
echo "─────────────────────────────────────────────────────────"
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "✅ Git repository"
    
    BRANCH=$(git branch --show-current)
    echo "   Branch: $BRANCH"
    
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️ Uncommitted changes detected"
        git status --short | head -10
    else
        echo "✅ Working tree clean"
    fi
else
    echo "⚠️ Not a git repository"
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════"
echo "  📊 CHECK SUMMARY"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ $ISSUES -eq 0 ]; then
    echo "✅ ALL CRITICAL CHECKS PASSED!"
    echo ""
    echo "Next steps:"
    echo "1. Quantize model (if not done):"
    echo "   python Dermal/quantize_model.py"
    echo ""
    echo "2. Run comprehensive test:"
    echo "   python test_before_deploy.py"
    echo ""
    echo "3. Review final checklist:"
    echo "   cat FINAL_DEPLOYMENT_CHECKLIST.md"
    echo ""
    echo "4. Deploy:"
    echo "   ./DEPLOY_COMMANDS.sh"
    echo ""
else
    echo "⚠️ FOUND $ISSUES ISSUE(S)!"
    echo ""
    echo "Please fix issues before deploying!"
    echo ""
fi

exit $ISSUES
