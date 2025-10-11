from django.apps import AppConfig
import os
import sys


class DermalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Dermal'
    
    # Class variable to prevent multiple pre-loads
    _model_preloaded = False

    def ready(self):
        """
        Pre-load model when Django starts up (only in production/server mode).
        
        This prevents timeout issues on Render free tier where:
        1. Instance spins down with inactivity (~50s cold start)
        2. If model loads during first request, total time > 80s
        3. HTTP request times out (usually 30-60s)
        
        By pre-loading here, first request only needs to run inference.
        
        SAFETY CHECKS:
        - Skip during migrations/makemigrations (DB not ready)
        - Skip during tests (not needed)
        - Skip during shell/other management commands
        - Prevent duplicate loads (ready() can be called multiple times)
        - Handle TensorFlow + Gunicorn fork() issues
        """
        
        # Prevent duplicate pre-loading (ready() can be called multiple times)
        if DermalConfig._model_preloaded:
            return
        
        # Check if model preloading is enabled (default: True in production)
        preload = os.getenv('PRELOAD_MODEL', 'true').lower() in ('true', '1', 'yes')
        if not preload:
            print("ℹ️ Model pre-loading disabled (PRELOAD_MODEL=false)")
            return
        
        # Detect if we're in a management command that should NOT load model
        # These commands don't need the model and may cause issues
        skip_commands = {
            'migrate', 'makemigrations', 'createsuperuser', 
            'shell', 'shell_plus', 'dbshell', 'test', 'check',
            'collectstatic', 'compilemessages', 'makemessages',
            'flush', 'loaddata', 'dumpdata', 'inspectdb',
            'showmigrations', 'sqlmigrate', 'squashmigrations'
        }
        
        # Check sys.argv for management commands
        if len(sys.argv) > 1:
            command = sys.argv[1]
            if command in skip_commands:
                print(f"ℹ️ Skipping model pre-load (running: {command})")
                return
        
        # Only pre-load in actual server processes
        # Check multiple ways to detect if we're running a server
        # Supports: Gunicorn (Render), mod_wsgi (PythonAnywhere), uWSGI, etc.
        is_server = False
        
        # Method 1: Check argv[0] (script name)
        # Covers: gunicorn, uvicorn, uwsgi, daphne
        if sys.argv and len(sys.argv) > 0:
            argv0_lower = sys.argv[0].lower()
            if any(server in argv0_lower for server in ['gunicorn', 'uvicorn', 'uwsgi', 'daphne', 'wsgi']):
                is_server = True
        
        # Method 2: Check sys.argv for runserver
        if 'runserver' in sys.argv:
            is_server = True
        
        # Method 3: Check environment variable (MOST RELIABLE!)
        # Set this in production: DJANGO_SERVER_MODE=true
        if os.getenv('DJANGO_SERVER_MODE') == 'true':
            is_server = True
        
        # Method 4: Check WSGI environment
        # Gunicorn, mod_wsgi, and uWSGI set these
        if os.getenv('WSGI_APPLICATION') or os.getenv('SERVER_SOFTWARE'):
            is_server = True
        
        # Method 5: Check for mod_wsgi (PythonAnywhere)
        # mod_wsgi embeds Python in Apache
        try:
            import mod_wsgi
            is_server = True
        except ImportError:
            pass
        
        if not is_server:
            # Not a server process, skip pre-loading
            return
        
        # All checks passed, proceed with pre-loading
        print("🚀 Pre-loading AI model to avoid timeout on first request...")
        
        try:
            # IMPORTANT: For Gunicorn with multiple workers, we need to be careful
            # about TensorFlow + fork() issues. 
            # With --preload-app, model loads before fork → all workers share memory (GOOD)
            # Without --preload-app, each worker loads separately (uses more RAM but safer)
            
            from . import AI_detection
            
            # Load the model into memory
            model = AI_detection.get_model()
            
            # Mark as successfully pre-loaded
            DermalConfig._model_preloaded = True
            
            print(f"✅ Model pre-loaded successfully: {type(model).__name__}")
            
            # Optional: Print memory usage if psutil available
            try:
                import psutil
                process = psutil.Process()
                mem_mb = process.memory_info().rss / (1024 * 1024)
                print(f"📊 Memory usage after model load: {mem_mb:.1f} MB")
            except ImportError:
                pass
                
        except Exception as e:
            print(f"⚠️ Failed to pre-load model: {e}")
            print("   Model will be lazy-loaded on first request instead.")
            import traceback
            traceback.print_exc()
