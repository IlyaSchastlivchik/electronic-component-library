import requests
import json

# ВАЖНО: Вставьте свой ключ
API_KEY = "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"

def test_openrouter():
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Test App",
    }
    
    # Более надежная модель для теста
    model = "deepseek/deepseek-chat"
    
    print(f"🔍 Тестируем: {model}")
    print(f"Ключ: {API_KEY[:20]}...")
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Скажи 'Привет, я работа!' одной фразой."}
        ],
        "temperature": 0.3,
        "max_tokens": 200  # Увеличили для гарантии ответа
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"\n📊 Статус: {response.status_code}")
    
    # Выводим весь ответ для отладки
    print(f"📄 Полный ответ:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        result = response.json()
        
        # Проверяем, что в ответе есть content
        try:
            content = result["choices"][0]["message"]["content"]
            if content:
                print(f"\n✅ УСПЕХ! Ответ: {content}")
            else:
                print("\n⚠️  Ответ пустой, проверьте параметры запроса")
        except KeyError:
            print("\n❌ Ошибка парсинга ответа")
    else:
        print(f"\n❌ ОШИБКА: {response.text}")

if __name__ == "__main__":
    test_openrouter()