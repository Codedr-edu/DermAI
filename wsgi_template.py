# +++++++++++ PYTHONANYWHERE WSGI CONFIGURATION +++++++++++
# Copy nội dung này vào WSGI configuration file trên PythonAnywhere
# Thay 'yourusername' bằng username thực của bạn

import os
import sys

# === Path setup ===
# QUAN TRỌNG: Thay 'yourusername' bằng username PythonAnywhere của bạn!
project_home = '/home/yourusername/dermai'

# Add project to Python path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# === Load environment variables from .env ===
from dotenv import load_dotenv
env_path = os.path.join(project_home, '.env')
load_dotenv(env_path)

print(f"✅ Loaded .env from: {env_path}")

# === Django settings ===
os.environ['DJANGO_SETTINGS_MODULE'] = 'dermai.settings'

# Signal to apps.py that we're in server mode
# (But PRELOAD_MODEL=false in .env, so model won't pre-load)
os.environ['DJANGO_SERVER_MODE'] = 'true'

# === Debug info ===
print(f"📁 Project path: {project_home}")
print(f"🔧 PRELOAD_MODEL: {os.getenv('PRELOAD_MODEL', 'not set')}")
print(f"🎨 ENABLE_GRADCAM: {os.getenv('ENABLE_GRADCAM', 'not set')}")

# === Load WSGI application ===
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

print("✅ WSGI application loaded successfully!")
