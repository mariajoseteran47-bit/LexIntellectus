import os
import google.generativeai as genai
from app.core.config import settings

def list_models():
    api_key = settings.GOOGLE_API_KEY if hasattr(settings, 'GOOGLE_API_KEY') else os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    print("📋 Modelos disponibles para esta API Key:")
    try:
        for m in genai.list_models():
            if 'embedContent' in m.supported_generation_methods:
                print(f"   [Embed] {m.name}")
            if 'generateContent' in m.supported_generation_methods:
                print(f"   [Chat]  {m.name}")
    except Exception as e:
        print(f"❌ Error listando modelos: {e}")

if __name__ == "__main__":
    list_models()
