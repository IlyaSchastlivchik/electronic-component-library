import json
import os
import requests
from typing import Dict
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv(override=True)

class SimpleComponentLibraryBrain:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "http://localhost:8000/api"
        self.model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
        
        if not self.api_key:
            raise ValueError("❌ OPENROUTER_API_KEY не найден в .env файле!")
        
        print(f"✅ API-ключ загружен: {self.api_key[:20]}...")
    
    def process_query(self, user_question: str) -> Dict:
        """Простая обработка запроса - только поиск по тексту"""
        print(f"📝 Обработка запроса: '{user_question}'")
        
        try:
            # Простой поиск по тексту
            params = {"search_text": user_question}
            
            response = requests.get(f"{self.base_url}/components", params=params, timeout=10)
            
            if response.status_code != 200:
                return {
                    "user_question": user_question,
                    "command": {"command": "search_components", "args": {}, "explanation": "Простой поиск"},
                    "result": {"error": f"Ошибка сервера: {response.status_code}"},
                    "success": False
                }
            
            data = response.json()
            
            return {
                "user_question": user_question,
                "command": {"command": "search_components", "args": {}, "explanation": "Простой текстовый поиск"},
                "result": data,
                "success": True
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "user_question": user_question,
                "command": {"command": "search_components", "args": {}, "explanation": "Простой поиск"},
                "result": {"error": "Сервер недоступен. Запустите web_app.py"},
                "success": False
            }
        except Exception as e:
            return {
                "user_question": user_question,
                "command": {"command": "search_components", "args": {}, "explanation": "Простой поиск"},
                "result": {"error": f"Ошибка: {str(e)}"},
                "success": False
            }

# Только для тестирования при прямом запуске
if __name__ == "__main__":
    print("🧪 Тестирование SimpleComponentLibraryBrain...")
    brain = SimpleComponentLibraryBrain()
    result = brain.process_query("транзистор")
    print(f"Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")