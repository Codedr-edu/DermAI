from django.apps import AppConfig
import os


class DermalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Dermal'

    def ready(self):
        """
        Pre-load model when Django starts up.
        
        This prevents timeout issues on Render free tier where:
        1. Instance spins down with inactivity (~50s cold start)
        2. If model loads during first request, total time > 80s
        3. HTTP request times out (usually 30-60s)
        
        By pre-loading here, first request only needs to run inference.
        """
        # Only preload in production/server processes, not during migrations
        # Check if we're in a management command (like migrate, makemigrations)
        import sys
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0] or 'uvicorn' in sys.argv[0]:
            # Check if model preloading is enabled (default: True)
            preload = os.getenv('PRELOAD_MODEL', 'true').lower() in ('true', '1', 'yes')
            
            if preload:
                print("🚀 Pre-loading AI model to avoid timeout on first request...")
                try:
                    from . import AI_detection
                    # This will load the model into memory
                    model = AI_detection.get_model()
                    print(f"✅ Model pre-loaded successfully: {type(model).__name__}")
                except Exception as e:
                    print(f"⚠️ Failed to pre-load model (will lazy load on first request): {e}")
            else:
                print("ℹ️ Model pre-loading disabled (PRELOAD_MODEL=false)")
