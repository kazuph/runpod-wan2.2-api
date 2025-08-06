"""
Global functions for ComfyUI-WanVideoWrapper.
This file provides missing global functions that are imported by other modules.
"""

# Global state storage
_global_state = {
    "enhance_weight": 1.0,
    "num_frames": 1,
    "device": "cuda",
    "dtype": "fp16"
}

def get_enhance_weight():
    """Get the enhance weight value."""
    return _global_state.get("enhance_weight", 1.0)

def set_enhance_weight(weight):
    """Set the enhance weight value."""
    _global_state["enhance_weight"] = weight

def get_num_frames():
    """Get the number of frames."""
    return _global_state.get("num_frames", 1)

def set_num_frames(frames):
    """Set the number of frames."""
    _global_state["num_frames"] = frames

def get_device():
    """Get the device (cuda/cpu)."""
    return _global_state.get("device", "cuda")

def set_device(device):
    """Set the device."""
    _global_state["device"] = device

def get_dtype():
    """Get the data type."""
    return _global_state.get("dtype", "fp16")

def set_dtype(dtype):
    """Set the data type."""
    _global_state["dtype"] = dtype

# Additional utility functions that might be needed
def reset_globals():
    """Reset all global values to defaults."""
    global _global_state
    _global_state = {
        "enhance_weight": 1.0,
        "num_frames": 1,
        "device": "cuda",
        "dtype": "fp16"
    }