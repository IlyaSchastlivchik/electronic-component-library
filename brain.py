import json
import os
import requests
from typing import Dict
from dotenv import load_dotenv

# Загружаем переменные окружения с принудительным перезаписыванием
load_dotenv(override=True)

class ComponentLibraryBrain:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
        
        if not self.api_key:
            raise ValueError("❌ OPENROUTER_API_KEY не найден в .env файле!")
        else:
            print(f"✅ API-ключ загружен: {self.api_key[:20]}...")
        
        self.library_schema = {
            "name": "Electronic Component Library",
            "description": "Библиотека электронных компонентов с параметрами и характеристиками",
            "available_commands": {
                "search_components": {
                    "description": "Поиск компонентов по параметрам",
                    "parameters": {
                        "type": {"description": "Тип компонента", "type": "string", "example": "bjt"},
                        "Imax_min": {"description": "Минимальный ток", "type": "float", "example": 0.1},
                        "Imax_max": {"description": "Максимальный ток", "type": "float", "example": 1.0},
                        "Uce_min": {"description": "Минимальное напряжение", "type": "float", "example": 20},
                        "Uce_max": {"description": "Максимальное напряжение", "type": "float", "example": 100},
                        "Ptot_min": {"description": "Минимальная мощность", "type": "float", "example": 0.5},
                        "Ptot_max": {"description": "Максимальная мощность", "type": "float", "example": 10}
                    }
                },
                "get_component_details": {
                    "description": "Получить детальную информацию о компоненте",
                    "parameters": {
                        "component_id": {"description": "ID компонента", "type": "string", "required": True}
                    }
                },
                "get_characteristics": {
                    "description": "Получить характеристики (ВАХ) компонента",
                    "parameters": {
                        "component_id": {"description": "ID компонента", "type": "string", "required": True}
                    }
                }
            },
            "component_types": ["bjt", "mosfet", "vacuum_tube", "diode", "transformer"]
        }
    
    def create_prompt(self, user_question: str) -> str:
        prompt = f"""Ты — ассистент для библиотеки электронных компонентов.
        
Информация о библиотеке:
{json.dumps(self.library_schema, ensure_ascii=False, indent=2)}

Запрос пользователя: "{user_question}"

Ответь ТОЛЬКО валидным JSON без лишнего текста.

Примеры:
Вопрос: "Найди транзисторы с током от 0.1А"
Ответ: {{"command": "search_components", "args": {{"Imax_min": 0.1}}, "explanation": "Ищу транзисторы"}}

Вопрос: "Характеристики 2N3904"
Ответ: {{"command": "get_characteristics", "args": {{"component_id": "2N3904"}}, "explanation": "Получаю ВАХ"}}

Теперь ответь на: "{user_question}"

JSON ответ:"""
        return prompt
    
    def ask_openrouter(self, prompt: str) -> str:
        """Отправка запроса к OpenRouter"""
        # ИСПРАВЛЕНО: Убран пробел в URL
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Component Library"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Ты возвращаешь только валидный JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        try:
            print(f"🤖 Запрос к модели {self.model}...")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            if not content:
                raise ValueError("Пустой ответ от модели")
            
            print(f"✅ Получен ответ: {content[:150]}...")
            return content
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return json.dumps({"error": str(e), "command": None, "args": {}, "explanation": "Ошибка модели"})
    
    def parse_command(self, json_response: str) -> Dict:
        """Парсинг JSON ответа"""
        try:
            cleaned = json_response.strip()
            if cleaned.startswith("```json"): cleaned = cleaned[7:]
            if cleaned.endswith("```"): cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            return {"command": "search_components", "args": {}, "explanation": "Показываю все компоненты"}
    
    def execute_command(self, command_data: Dict) -> Dict:
        """Выполнение команды на локальном сервере"""
        command = command_data.get("command", "search_components")
        args = command_data.get("args", {})
        
        try:
            print(f"🔧 Выполняю: {command} с параметрами {args}")
            
            if command == "search_components":
                params = {k: v for k, v in args.items() if v is not None}
                
                # ДОБАВЛЕНО: Отладочный вывод
                print(f"📤 Отправляю GET запрос с параметрами: {params}")
                
                # Логируем полный URL
                url = f"{self.base_url}/components"
                print(f"🌐 URL запроса: {url}")
                
                response = requests.get(url, params=params, timeout=10)
                
                # Логируем статус ответа
                print(f"📥 Получен ответ от сервера: {response.status_code}")
                
                return response.json()
            
            elif command in ["get_component_details", "get_characteristics"]:
                component_id = args.get("component_id")
                if not component_id:
                    return {"error": "Не указан ID компонента"}
                
                # Исправлено: правильные endpoint для сервера
                if command == "get_component_details":
                    url = f"{self.base_url}/components/{component_id}"
                else:  # get_characteristics
                    url = f"{self.base_url}/components/{component_id}/characteristics"
                
                print(f"🌐 URL запроса: {url}")
                response = requests.get(url, timeout=10)
                print(f"📥 Получен ответ от сервера: {response.status_code}")
                
                return response.json()
            
            return {"error": f"Неизвестная команда: {command}"}
            
        except requests.exceptions.ConnectionError:
            return {"error": "Сервер библиотеки недоступен. Запустите его на localhost:8000"}
        except Exception as e:
            return {"error": f"Ошибка: {str(e)}"}
    
    def process_query(self, user_question: str) -> Dict:
        """Основная обработка запроса"""
        print(f"\n📝 Вопрос: {user_question}")
        
        prompt = self.create_prompt(user_question)
        json_response = self.ask_openrouter(prompt)
        command_data = self.parse_command(json_response)
        result = self.execute_command(command_data)
        
        return {
            "user_question": user_question,
            "command": command_data,
            "result": result,
            "success": "error" not in result
        }

if __name__ == "__main__":
    # Тестирование
    brain = ComponentLibraryBrain()
    result = brain.process_query("Найди транзисторы с током от 0.5А")
    print("\n📊 Итоговый результат:")
    print(json.dumps(result, indent=2, ensure_ascii=False))