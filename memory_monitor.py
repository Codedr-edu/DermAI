#!/usr/bin/env python3
"""
Memory monitoring utility for DermAI application
"""
import psutil
import os
import gc
import sys
from functools import wraps

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        'rss': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
        'vms': memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
        'percent': process.memory_percent(),
    }

def memory_monitor(func):
    """Decorator to monitor memory usage of functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Memory before
        mem_before = get_memory_usage()
        print(f"🔍 {func.__name__} - Memory before: {mem_before['rss']:.1f}MB")
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Force garbage collection
            gc.collect()
            
            # Memory after
            mem_after = get_memory_usage()
            mem_diff = mem_after['rss'] - mem_before['rss']
            print(f"🔍 {func.__name__} - Memory after: {mem_after['rss']:.1f}MB (Δ{mem_diff:+.1f}MB)")
            
            # Warning if memory usage is high
            if mem_after['rss'] > 400:  # Warning at 400MB (80% of 512MB)
                print(f"⚠️ HIGH MEMORY USAGE: {mem_after['rss']:.1f}MB")
            
    return wrapper

def check_system_memory():
    """Check system memory availability"""
    memory = psutil.virtual_memory()
    print(f"💾 System Memory: {memory.total/1024/1024/1024:.1f}GB total, {memory.available/1024/1024:.1f}MB available")
    
    if memory.percent > 90:
        print("⚠️ System memory usage is very high!")
        return False
    return True

def force_cleanup():
    """Force memory cleanup"""
    print("🧹 Forcing memory cleanup...")
    
    # Clear TensorFlow session if available
    try:
        import tensorflow as tf
        tf.keras.backend.clear_session()
        print("  ✅ TensorFlow session cleared")
    except:
        pass
    
    # Force garbage collection multiple times
    for i in range(3):
        collected = gc.collect()
        print(f"  🗑️ GC round {i+1}: {collected} objects collected")
    
    # Get memory after cleanup
    mem_after = get_memory_usage()
    print(f"  📊 Memory after cleanup: {mem_after['rss']:.1f}MB")

if __name__ == "__main__":
    print("Memory Monitor for DermAI")
    print("=" * 40)
    check_system_memory()
    print()
    
    current_mem = get_memory_usage()
    print(f"Current process memory: {current_mem['rss']:.1f}MB ({current_mem['percent']:.1f}%)")
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        force_cleanup()