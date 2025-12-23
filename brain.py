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
        self.base_url = "http://localhost:8000/api"  # Важно: с /api в конце
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
                        "Ptot_max": {"description": "Максимальная мощность", "type": "float", "example": 10},
                        "origin": {"description": "Происхождение/страна", "type": "string", "example": "soviet"},
                        "search_text": {"description": "Поиск по названию и описанию", "type": "string", "example": "мощный"},
                        "sort_by": {"description": "Сортировка", "type": "string", "example": "Ptot_desc"}
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
            "component_types": ["bjt", "mosfet", "vacuum_tube", "diode", "transformer"],
            "origin_types": ["soviet", "usa", "other"]
        }
    
    def create_prompt(self, user_question: str) -> str:
        prompt = f"""Ты — ассистент для библиотеки электронных компонентов.
        
Информация о библиотеке:
{json.dumps(self.library_schema, ensure_ascii=False, indent=2)}

Запрос пользователя: "{user_question}"

Ответь ТОЛЬКО валидным JSON без лишнего текста.

ВАЖНОЕ ПРАВИЛО ДЛЯ ПОИСКА:
1. Используй только доступные параметры из схемы.
2. Если тип не указан явно, не используй параметр "type".

Примеры:
Вопрос: "Найди биполярные транзисторы с током от 0.1А"
Ответ: {{"command": "search_components", "args": {{"type": "bjt", "Imax_min": 0.1}}, "explanation": "Ищу биполярные транзисторы с током от 0.1А"}}

Вопрос: "Покажи самый мощный транзистор"
Ответ: {{"command": "search_components", "args": {{"sort_by": "Ptot_desc"}}, "explanation": "Ищу транзисторы, отсортированные по мощности"}}

Вопрос: "Найди советские компоненты"
Ответ: {{"command": "search_components", "args": {{"origin": "soviet"}}, "explanation": "Ищу компоненты советского производства"}}

Вопрос: "Характеристики 2N3904"
Ответ: {{"command": "get_characteristics", "args": {{"component_id": "2N3904"}}, "explanation": "Получаю ВАХ транзистора 2N3904"}}

Теперь ответь на: "{user_question}"

JSON ответ:"""
        return prompt
    
    def ask_openrouter(self, prompt: str) -> str:
        """Отправка запроса к OpenRouter"""
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
                {"role": "system", "content": "Ты возвращаешь только валидный JSON. Не добавляй пояснений, только JSON."},
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
            
            print(f"✅ Получен ответ: {content[:100]}...")
            return content
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка сети при запросе к OpenRouter: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Статус: {e.response.status_code}")
                print(f"   Ответ: {e.response.text[:200]}")
            return json.dumps({"error": f"Ошибка сети: {e}", "command": "search_components", "args": {}, "explanation": "Ошибка соединения с ИИ"})
        except Exception as e:
            print(f"❌ Ошибка в ask_openrouter: {e}")
            return json.dumps({"error": str(e), "command": "search_components", "args": {}, "explanation": "Ошибка модели"})
    
    def parse_command(self, json_response: str) -> Dict:
        """Парсинг JSON ответа"""
        try:
            cleaned = json_response.strip()
            
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            parsed = json.loads(cleaned)
            
            if not isinstance(parsed, dict):
                raise ValueError("Ответ не является объектом JSON")
            
            if "command" not in parsed:
                parsed["command"] = "search_components"
            
            if "args" not in parsed:
                parsed["args"] = {}
            
            if "explanation" not in parsed:
                parsed["explanation"] = "Выполняю запрос"
            
            print(f"✅ Команда распознана: {parsed['command']}")
            print(f"   Аргументы: {parsed['args']}")
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            print(f"   Сырой ответ: {json_response[:200]}")
            return {"command": "search_components", "args": {}, "explanation": "Не удалось распознать запрос"}
        except Exception as e:
            print(f"❌ Другая ошибка при парсинге: {e}")
            return {"command": "search_components", "args": {}, "explanation": "Ошибка обработки запроса"}
    
    def execute_command(self, command_data: Dict) -> Dict:
        """Выполнение команды на локальном сервере"""
        command = command_data.get("command", "search_components")
        args = command_data.get("args", {})
        
        try:
            print(f"\n🔧 Выполняю команду: {command}")
            print(f"   Аргументы: {args}")
            
            if command == "search_components":
                # Подготавливаем параметры для API
                params = {}
                for key, value in args.items():
                    if value is not None:
                        params[key] = value
                
                # Исправляем типы данных
                for float_key in ['Imax_min', 'Imax_max', 'Uce_min', 'Uce_max', 'Ptot_min', 'Ptot_max']:
                    if float_key in params:
                        try:
                            params[float_key] = float(params[float_key])
                        except (ValueError, TypeError):
                            del params[float_key]
                
                print(f"📤 Отправляю запрос с параметрами: {params}")
                
                url = f"{self.base_url}/components"
                print(f"🌐 URL запроса: {url}")
                
                response = requests.get(url, params=params, timeout=10)
                print(f"📥 Статус ответа: {response.status_code}")
                
                if response.status_code != 200:
                    return {"error": f"Ошибка сервера: {response.status_code}", "details": response.text[:200]}
                
                return response.json()
            
            elif command in ["get_component_details", "get_characteristics"]:
                component_id = args.get("component_id")
                if not component_id:
                    return {"error": "Не указан ID компонента"}
                
                if command == "get_component_details":
                    url = f"{self.base_url}/components/{component_id}"
                else:
                    url = f"{self.base_url}/components/{component_id}/characteristics"
                
                print(f"🌐 URL запроса: {url}")
                response = requests.get(url, timeout=10)
                print(f"📥 Статус ответа: {response.status_code}")
                
                if response.status_code != 200:
                    return {"error": f"Ошибка сервера: {response.status_code}", "details": response.text[:200]}
                
                return response.json()
            
            else:
                return {"error": f"Неизвестная команда: {command}", "available_commands": list(self.library_schema["available_commands"].keys())}
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Ошибка соединения с сервером {self.base_url}")
            return {"error": "Сервер библиотеки недоступен. Убедитесь, что web_app.py запущен на localhost:8000"}
        except requests.exceptions.Timeout:
            return {"error": "Таймаут при запросе к серверу"}
        except Exception as e:
            print(f"❌ Ошибка в execute_command: {type(e).__name__}: {e}")
            return {"error": f"Ошибка выполнения: {str(e)}"}
    
    def process_query(self, user_question: str) -> Dict:
        """Основная обработка запроса"""
        print(f"\n" + "="*60)
        print(f"📝 Вопрос пользователя: '{user_question}'")
        print("="*60)
        
        # Создаем промпт для ИИ
        prompt = self.create_prompt(user_question)
        
        # Запрашиваем у OpenRouter
        json_response = self.ask_openrouter(prompt)
        
        # Парсим ответ
        command_data = self.parse_command(json_response)
        
        # Выполняем команду
        result = self.execute_command(command_data)
        
        # Формируем итоговый ответ
        response = {
            "user_question": user_question,
            "command": command_data,
            "result": result,
            "success": "error" not in result
        }
        
        print(f"\n✅ Обработка завершена. Успех: {response['success']}")
        
        return response