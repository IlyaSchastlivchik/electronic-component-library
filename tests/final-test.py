import requests

# ВАЖНО: Вставьте свой ключ между кавычек
API_KEY = "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"

def test_openrouter():
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
    }
    
    model = "tngtech/deepseek-r1t2-chimera:free"
    
    print(f"🔍 Тестируем: {model}")
    print(f"Ключ: {API_KEY[:20]}...")
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Test"}],
        "max_tokens": 50
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"\nСтатус: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        answer = result["choices"][0]["message"]["content"]
        print(f"\n✅ УСПЕХ! Ответ: {answer}")
    else:
        print(f"❌ ОШИБКА: {response.text}")

if __name__ == "__main__":
    test_openrouter()