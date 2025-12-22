import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

# Добавьте отладку, чтобы убедиться, что ключ загружен
print(f"Ключ загружен: {api_key[:20]}...")  # Должно начинаться с "sk-or-v1-"

def test_openrouter():
    url = "https://openrouter.ai/api/v1/chat/completions"  # ✅ Без пробела в конце!
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Test App",  # Рекомендуется для идентификации
    }
    
    models_to_test = [
        "deepseek/deepseek-v3.2",
        "deepseek/deepseek-chat",
        "tngtech/deepseek-r1t2-chimera:free"
    ]
    
    for model in models_to_test:
        print(f"\n🔍 Тестируем модель: {model}")
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Привет! Ответь 'Работает' если ты доступен."}
            ],
            "temperature": 0.1,
            "max_tokens": 50
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            print(f"✅ Модель отвечает: {answer}")
            
            if "usage" in result:
                tokens = result["usage"]["total_tokens"]
                print(f"📊 Использовано токенов: {tokens}")
                
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP ошибка ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"❌ Ошибка с моделью {model}: {str(e)}")

if __name__ == "__main__":
    print("🧪 Тестирование подключения к OpenRouter...")
    test_openrouter()