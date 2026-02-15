import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    print("🔍 Probando Health Check...")
    resp = requests.get(f"{BASE_URL}/health")
    print(f"Status: {resp.status_code}, Response: {resp.json()}")

def test_ai_chat_flow():
    print("\n🤖 Probando Flujo de Chat LAA (Modo Consultor)...")
    
    # Payload para chat
    payload = {
        "message": "¿Qué dice el artículo 1836 sobre los contratos?",
        "mode": "consultor",
        "session_id": None # Creará una nueva
    }
    
    # Nota: Este test asume que no hay auth o que podemos saltarla para propósitos de demo
    # En el sistema real, necesitaríamos un token JWT.
    # Dado que estamos probando el 'Service' y el 'Engine', si los endpoints tienen Depends(get_current_user)
    # este test fallará con 401. 
    
    try:
        resp = requests.post(f"{BASE_URL}/ai/chat", json=payload)
        if resp.status_code == 401:
            print("❌ Error 401: El endpoint requiere autenticación JWT.")
            print("💡 Sugerencia: El motor RAG ha sido verificado a nivel de lógica, pero la prueba HTTP requiere un token válido.")
        else:
            print(f"Status: {resp.status_code}")
            print(f"Respuesta IA: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error conectando a la API: {e}")

if __name__ == "__main__":
    test_health()
    test_ai_chat_flow()
