import os, sys, base64
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_services import AIRouter, update_registry_cache

update_registry_cache()

router = AIRouter()

# Create dummy base64 audio
fake_audio = {
    "data": "data:audio/webm;base64,UklGRiQAAABXRUJNRm10IAIAAAABAAEAQB8AAAB9AAACABAAZGF0YQAAAAA=", 
    "mime_type": "audio/webm",
    "name": "test.webm"
}

print("\n--- SIMULATING AUDIO UPLOAD ---")
stream = router.stream_completion(
    system_prompt="You are a helpful assistant.",
    user_prompt="Say hello and describe the audio.",
    audio=[fake_audio],
    files=[]
)

try:
    for chunk in stream:
        print(f"[{chunk.get('type')}] {chunk.get('chunk', '')[:100]} | provider: {chunk.get('provider')}/{chunk.get('model')}")
except Exception as e:
    print(f"EXCEPTION: {e}")
