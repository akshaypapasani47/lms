
import importlib.util
import sys

print("Python:", sys.version)

modules = [
    "transformers",
    "tokenizers",
    "torch",
    "sentencepiece",
    "safetensors",
    "PIL",
    "cv2",
    "soundfile",
    "librosa",
    "whisper",
    "faster_whisper",
    "TTS",
    "edge_tts",
]

print("\n=== MODULE AVAILABILITY ===")

for name in modules:
    try:
        available = importlib.util.find_spec(name) is not None
        print(f"{name}: {'INSTALLED' if available else 'MISSING'}")
    except (ImportError, ValueError):
        print(f"{name}: CHECK FAILED")

print("\n=== CHECK COMPLETE ===")
