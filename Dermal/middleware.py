"""
Memory management middleware for Django
"""
import gc
import psutil
import os
from django.utils.deprecation import MiddlewareMixin

class MemoryManagementMiddleware(MiddlewareMixin):
    """
    Middleware để quản lý memory và cleanup sau mỗi request
    """
    
    def process_response(self, request, response):
        """Cleanup memory sau mỗi response"""
        try:
            # Force garbage collection
            gc.collect()
            
            # Log memory usage (chỉ trong development)
            if os.getenv('DEBUG', 'False').lower() == 'true':
                memory_info = psutil.Process().memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                print(f"🧠 Memory usage after request: {memory_mb:.2f} MB")
                
                # Warning nếu memory usage quá cao
                if memory_mb > 400:  # 400MB threshold
                    print(f"⚠️ High memory usage detected: {memory_mb:.2f} MB")
                    
        except Exception as e:
            print(f"⚠️ Memory management error: {e}")
            
        return response