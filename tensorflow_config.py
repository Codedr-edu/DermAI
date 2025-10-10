"""
TensorFlow configuration for memory optimization
"""
import os
import tensorflow as tf

def configure_tensorflow():
    """Configure TensorFlow for memory optimization"""
    
    # Set log level to reduce verbosity
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    
    # Configure memory growth for GPU (if available)
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            print("✅ GPU memory growth enabled")
        except RuntimeError as e:
            print(f"⚠️ GPU memory growth setup failed: {e}")
    
    # Configure CPU optimization
    tf.config.threading.set_inter_op_parallelism_threads(2)
    tf.config.threading.set_intra_op_parallelism_threads(2)
    
    # Enable mixed precision for memory efficiency
    tf.keras.mixed_precision.set_global_policy('mixed_float16')
    
    # Configure memory allocation
    tf.config.experimental.enable_memory_growth()
    
    print("✅ TensorFlow configured for memory optimization")

# Auto-configure when imported
configure_tensorflow()