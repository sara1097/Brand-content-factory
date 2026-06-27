"""
Bulletproof vision test - tries multiple methods
"""

import os
import base64
import requests
import json

# Configuration
IMAGE_PATH = os.path.abspath("test.jpg")
MODEL = "qwen3.5:4b"
OLLAMA_URL = "http://localhost:11434"

# Verify image exists
if not os.path.exists(IMAGE_PATH):
    print(f"❌ Image not found: {IMAGE_PATH}")
    exit()

print(f"📁 Image: {IMAGE_PATH}")
print(f"📦 Size: {os.path.getsize(IMAGE_PATH) / 1024:.2f} KB")
print(f"🤖 Model: {MODEL}")
print()

# Encode image to base64
with open(IMAGE_PATH, 'rb') as f:
    image_b64 = base64.b64encode(f.read()).decode('utf-8')

# Make API call
print("🔍 Sending request to Ollama...")
print("-" * 60)

try:
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": [{
                "role": "user",
                "content": "Describe this product in detail. What is it? What category? What features can you see?",
                "images": [image_b64]
            }],
            "stream": False,
            "options": {
                "temperature": 0.3
            }
        },
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result['message']['content']
        
        print("\n✅ SUCCESS!\n")
        print("=" * 60)
        print("📝 MODEL RESPONSE:")
        print("=" * 60)
        print(content)
        print("=" * 60)
        
        # Verify it actually saw the image
        keywords = ['airpods', 'earbuds', 'apple', 'white', 'case', 'wireless', 'audio', 'bluetooth']
        if any(kw in content.lower() for kw in keywords):
            print("\n🎉 VISION IS WORKING! Model correctly saw the image.")
        else:
            print("\n⚠️  Response seems unrelated to image. Vision might still be broken.")
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Ollama. Make sure it's running:")
    print("   - Check system tray for Ollama icon")
    print("   - Or run: ollama serve")
except Exception as e:
    print(f"❌ Error: {e}")