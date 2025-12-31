import json
import os
import requests
import re
from typing import Dict, Optional

class SimpleQueryParser:
    """Простой парсер запросов для работы без OpenRouter API"""
    
    @staticmethod
    def parse_query(user_question: str) -> Dict:
        question = user_question.lower()
        args = {}
        
        # Определяем тип компонента
        if 'транзистор' in question:
            if 'биполяр' in question or 'bjt' in question:
                args['type'] = 'bjt'
            elif 'полевой' in question or 'mosfet' in question:
                args['type'] = 'mosfet'
            else:
                args['type'] = 'bjt'
        elif 'лампа' in question or 'tube' in question:
            args['type'] = 'vacuum_tube'
        elif 'диод' in question:
            args['type'] = 'diode'
        
        # Определяем происхождение
        if 'советск' in question or 'отечествен' in question:
            args['origin'] = 'soviet'
        elif 'американ' in question or 'usa' in question:
            args['origin'] = 'usa'
        elif 'япон' in question:
            args['origin'] = 'japan'
        elif 'европ' in question:
            args['origin'] = 'europe'
        
        # Парсим числовые параметры
        # Мощность
        power_match = re.search(r'мощность[^\d]*(\d+\.?\d*)', question)
        if power_match:
            args['min_power'] = float(power_match.group(1))
        
        # Ток
        current_match = re.search(r'ток[^\d]*(\d+\.?\d*)\s*а', question)
        if current_match:
            args['min_current'] = float(current_match.group(1))
        
        # Напряжение
        voltage_match = re.search(r'напряжен[^\d]*(\d+\.?\d*)\s*в', question)
        if voltage_match:
            args['min_voltage'] = float(voltage_match.group(1))
        
        # Если в запросе есть "мощный" или "большая мощность", устанавливаем минимальную мощность 10 Вт
        if 'мощн' in question or 'большая мощность' in question:
            args['min_power'] = 10.0
        
        # Если в запросе есть "высокое напряжение", устанавливаем минимальное напряжение 100 В
        if 'высокое напряжение' in question:
            args['min_voltage'] = 100.0
        
        # Если в запросе есть "большой ток", устанавливаем минимальный ток 1 А
        if 'большой ток' in question:
            args['min_current'] = 1.0
        
        return {
            "command": "search_components",
            "args": args,
            "explanation": "Поиск по ключевым словам (режим без ИИ)"
        }


class ComponentLibraryBrain:
    def __init__(self):
        # Модель по умолчанию
        self.model = "deepseek/deepseek-chat"
        
        # Настройки приложения
        self.app_name = "Electronic Component Library"
        
        # 🔧 ВАЖНО: Базовый URL для API с поддержкой Render
        render_port = os.environ.get("PORT", "8000")
        if "RENDER" in os.environ:
            # Внутри контейнера Render используем 0.0.0.0
            self.base_url = f"http://0.0.0.0:{render_port}"
            print(f"🌍 Обнаружена среда Render, использую {self.base_url}")
        else:
            # Для локальной разработки используем localhost
            self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
            print(f"🏠 Локальная среда, использую {self.base_url}")
        
        # 🔧 ОБНОВЛЕННАЯ КОНФИГУРАЦИЯ БИБЛИОТЕКИ ДЛЯ НОВОЙ СТРУКТУРЫ
        self.library_schema = {
            "name": "Electronic Component Library",
            "description": "Библиотека электронных компонентов с параметрами и характеристиками",
            "available_commands": {
                "search_components": {
                    "description": "Поиск компонентов по параметрам",
                    "parameters": {
                        "type": {"description": "Тип компонента", "type": "string", "example": "bjt"},
                        "component_type": {"description": "Тип компонента (расширенный)", "type": "string", "example": "bjt_npn"},
                        "origin": {"description": "Происхождение/страна", "type": "string", "example": "soviet"},
                        "search_text": {"description": "Поиск по названию и описанию", "type": "string", "example": "мощный"},
                        # Новые параметры мощности
                        "min_power": {"description": "Минимальная мощность (Вт)", "type": "float", "example": 0.5},
                        "max_power": {"description": "Максимальная мощность (Вт)", "type": "float", "example": 10},
                        # Новые параметры напряжения
                        "min_voltage": {"description": "Минимальное напряжение (В)", "type": "float", "example": 20},
                        "max_voltage": {"description": "Максимальное напряжение (В)", "type": "float", "example": 100},
                        # Новые параметры тока
                        "min_current": {"description": "Минимальный ток (А)", "type": "float", "example": 0.1},
                        "max_current": {"description": "Максимальный ток (А)", "type": "float", "example": 1.0},
                        # Параметры тегов и классификации
                        "application": {"description": "Тег области применения", "type": "string", "example": "audio"},
                        "application_tag": {"description": "Тег применения (синоним application)", "type": "string", "example": "switching"},
                        "frequency_range": {"description": "Частотный диапазон", "type": "string", "example": "HF"}
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
            "component_types_extended": ["bjt_npn", "bjt_pnp", "mosfet_n_channel", "vacuum_tube_dual_triode", "diode_switching", "transformer_output"],
            "origin_types": ["soviet", "usa", "generic"],
            "tag_types": {
                "application_tags": ["audio", "switching", "amplification", "power", "RF"],
                "technology_tags": ["silicon", "germanium", "mosfet", "vacuum_tube"],
                "role_tags": ["amplifier", "switch", "preamplifier", "power_switch"]
            }
        }
    
    def create_prompt(self, user_question: str) -> str:
        """Создание промпта для ИИ на основе вопроса пользователя"""
        prompt = f"""
Ты - система поиска электронных компонентов. Твоя задача - анализировать запросы пользователей и преобразовывать их в команды поиска.

Доступные команды:
1. search_components - поиск компонентов по параметрам
2. get_component_details - получение детальной информации о компоненте
3. get_characteristics - получение характеристик (ВАХ) компонента

Схема библиотеки:
{json.dumps(self.library_schema, ensure_ascii=False, indent=2)}

Запрос пользователя: "{user_question}"

Верни ответ в формате JSON:
{{
    "command": "имя_команды",
    "args": {{параметры}},
    "explanation": "Пояснение на русском языке, что будет сделано"
}}

Примеры:
1. Запрос: "Найди советские транзисторы с током больше 0.1А"
   Ответ: {{
        "command": "search_components",
        "args": {{"origin": "soviet", "min_current": 0.1, "type": "bjt"}},
        "explanation": "Поиск советских биполярных транзисторов с током более 0.1А"
   }}

2. Запрос: "Покажи мощные MOSFET на 100В"
   Ответ: {{
        "command": "search_components",
        "args": {{"type": "mosfet", "min_voltage": 50, "max_voltage": 150, "min_power": 50}},
        "explanation": "Поиск мощных MOSFET с напряжением 50-150В и мощностью от 50Вт"
   }}

3. Запрос: "Найди лампы для аудио усилителей"
   Ответ: {{
        "command": "search_components",
        "args": {{"type": "vacuum_tube", "application": "audio"}},
        "explanation": "Поиск вакуумных ламп для аудио применений"
   }}

Теперь обработай запрос пользователя и верни JSON:
"""
        return prompt
    
    def ask_openrouter(self, prompt: str, api_key: Optional[str]) -> str:
        """Отправка запроса к OpenRouter для DeepSeek Chat"""
        # Если нет API ключа, возвращаем команду по умолчанию для поиска
        if not api_key:
            print("⚠️  API ключ отсутствует, использую режим поиска по умолчанию")
            return json.dumps({
                "command": "search_components",
                "args": {},
                "explanation": "Поиск компонентов в локальной базе данных"
            })
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.base_url,
            "X-Title": self.app_name
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": "Ты возвращаешь только валидный JSON без пояснений. ВСЕГДА используй формат: {\"command\": \"...\", \"args\": {...}, \"explanation\": \"...\"}"
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        try:
            print(f"🤖 Запрос к {self.model}...")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            print(f"✅ Получен ответ: {content[:100]}...")
            return content
            
        except Exception as e:
            print(f"❌ Ошибка OpenRouter: {e}")
            return json.dumps({
                "command": "search_components", 
                "args": {}, 
                "explanation": f"Ошибка ИИ, выполнен поиск по умолчанию"
            })
    
    def parse_command(self, json_response: str) -> Dict:
        """Парсинг JSON ответа от ИИ"""
        try:
            # Убираем возможные markdown и лишние символы
            json_response = json_response.strip()
            if json_response.startswith("```json"):
                json_response = json_response[7:]
            if json_response.endswith("```"):
                json_response = json_response[:-3]
            if json_response.startswith("```"):
                json_response = json_response[3:]
            
            data = json.loads(json_response)
            
            # Проверяем обязательные поля
            if "command" not in data:
                data["command"] = "search_components"
            if "args" not in data:
                data["args"] = {}
            if "explanation" not in data:
                data["explanation"] = "Поиск компонентов"
            
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            print(f"Ответ ИИ: {json_response[:200]}")
            
            # Попробуем извлечь JSON из текста
            import re
            json_pattern = r'\{.*\}'
            matches = re.findall(json_pattern, json_response, re.DOTALL)
            
            if matches:
                try:
                    data = json.loads(matches[0])
                    return data
                except:
                    pass
            
            # Возвращаем команду по умолчанию
            return {
                "command": "search_components",
                "args": {},
                "explanation": "Поиск компонентов по запросу пользователя"
            }
        except Exception as e:
            print(f"❌ Ошибка обработки ответа ИИ: {e}")
            return {
                "command": "search_components",
                "args": {},
                "explanation": "Поиск компонентов"
            }
    
    def execute_command(self, command_data: Dict) -> Dict:
        """Выполнение команды на сервере с улучшенной обработкой ошибок"""
        # Защита от None
        if not command_data:
            command_data = {
                "command": "search_components",
                "args": {},
                "explanation": "Поиск компонентов"
            }
        
        command = command_data.get("command", "search_components")
        args = command_data.get("args", {})
        
        try:
            print(f"\n🔧 Выполняю команду: {command}")
            print(f"📝 Аргументы: {args}")
            
            if command == "search_components":
                params = {k: v for k, v in args.items() if v is not None and v != ""}
                
                # 🔧 ПРЕОБРАЗОВАНИЕ ТИПОВ ДЛЯ API
                for key in ['min_power', 'max_power', 'min_voltage', 'max_voltage', 'min_current', 'max_current']:
                    if key in params:
                        try:
                            params[key] = float(params[key])
                        except (ValueError, TypeError):
                            # Если не удалось преобразовать, удаляем параметр
                            params.pop(key, None)
                
                # 🔧 ИСПРАВЛЕНИЕ: Используем /api/components/search/extended для расширенного поиска
                # Но также можно использовать /api/components для базового поиска.
                # Проверим, есть ли расширенные параметры (мощность, напряжение, ток, application).
                # Если есть хотя бы один из них, используем extended endpoint.
                extended_params = ['min_power', 'max_power', 'min_voltage', 'max_voltage', 
                                   'min_current', 'max_current', 'application', 'frequency_range']
                
                if any(param in params for param in extended_params):
                    url = f"{self.base_url}/api/components/search/extended"
                else:
                    url = f"{self.base_url}/api/components"
                
                print(f"🌐 Запрос к: {url}")
                print(f"📊 Параметры: {params}")
                
                response = requests.get(url, params=params, timeout=15)
                print(f"📡 Код ответа: {response.status_code}")
                print(f"📄 Заголовки ответа: {response.headers.get('content-type', 'unknown')}")
                
                if response.status_code == 200:
                    # Проверяем, что ответ JSON
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        result = response.json()
                        print(f"✅ Получено {result.get('count', 0)} компонентов")
                        return result
                    else:
                        print(f"⚠️  Ответ не JSON: {response.text[:200]}")
                        # Попробуем распарсить как JSON, даже если заголовок неправильный
                        try:
                            result = response.json()
                            print(f"✅ Получено {result.get('count', 0)} компонентов (парсинг несмотря на заголовок)")
                            return result
                        except:
                            # Если не удалось распарсить, возвращаем ошибку
                            return {
                                "success": False,
                                "error": "Сервер вернул не JSON данные",
                                "details": f"Content-Type: {content_type}, первые 200 символов: {response.text[:200]}"
                            }
                else:
                    print(f"❌ Ошибка API: {response.status_code}")
                    print(f"Текст ошибки: {response.text[:200]}")
                    return {
                        "success": False,
                        "error": f"Ошибка API: {response.status_code}",
                        "details": response.text[:200]
                    }
            
            elif command in ["get_component_details", "get_characteristics"]:
                component_id = args.get("component_id")
                if not component_id:
                    return {
                        "success": False,
                        "error": "Не указан ID компонента"
                    }
                
                if command == "get_component_details":
                    url = f"{self.base_url}/api/components/{component_id}"
                else:
                    url = f"{self.base_url}/api/components/{component_id}/characteristics"
                
                print(f"🌐 Запрос к: {url}")
                
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Для характеристики добавляем ID компонента
                    if command == "get_characteristics":
                        result = {
                            "component_id": component_id,
                            "characteristics": result.get("characteristics", [])
                        }
                    
                    return result
                else:
                    return {
                        "success": False,
                        "error": f"Ошибка {response.status_code}",
                        "details": response.text[:200]
                    }
            
            return {
                "success": False,
                "error": f"Неизвестная команда: {command}"
            }
            
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Ошибка подключения: {e}")
            return {
                "success": False,
                "error": f"Сервер недоступен: {self.base_url}",
                "details": str(e)
            }
        except Exception as e:
            print(f"❌ Ошибка выполнения: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Ошибка выполнения: {str(e)}",
                "details": traceback.format_exc()
            }
    
    def process_query(self, user_question: str, user_api_key: Optional[str] = None) -> Dict:
        """Основной метод обработки запроса пользователя"""
        try:
            print(f"\n🎯 Обрабатываю запрос: '{user_question}'")
            print(f"🔑 Ключ предоставлен: {'Да' if user_api_key else 'Нет'}")
            
            # Если ключ не предоставлен, используем простой парсер
            if not user_api_key:
                print("🔧 Использую SimpleQueryParser для локального поиска")
                command_data = SimpleQueryParser.parse_query(user_question)
                print(f"📋 Команда (локальная): {command_data.get('command')}")
                print(f"💡 Объяснение: {command_data.get('explanation')}")
            else:
                # Создаем промпт для ИИ
                prompt = self.create_prompt(user_question)
                print(f"📝 Промпт создан ({len(prompt)} символов)")
                
                # Запрашиваем ответ у ИИ
                json_response = self.ask_openrouter(prompt, user_api_key)
                print(f"🤖 Ответ ИИ получен")
                
                # Парсим команду
                command_data = self.parse_command(json_response)
                print(f"📋 Команда: {command_data.get('command')}")
                print(f"💡 Объяснение: {command_data.get('explanation')}")
            
            # Выполняем команду
            result = self.execute_command(command_data)
            print(f"✅ Результат получен")
            
            # Формируем финальный ответ
            response = {
                "success": True,
                "command": command_data,
                "result": result,
                "mode": "openrouter" if user_api_key else "local_parser"
            }
            
            # Если результат содержит ошибку, помечаем как неуспешный
            if isinstance(result, dict) and result.get("success") is False:
                response["success"] = False
                response["error"] = result.get("error", "Неизвестная ошибка")
            
            return response
            
        except Exception as e:
            print(f"❌ Критическая ошибка в process_query: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": f"Внутренняя ошибка: {str(e)}",
                "details": traceback.format_exc(),
                "mode": "error"
            }

# 🔧 АВТОТЕСТ ПРИ ЗАПУСКЕ
if __name__ == "__main__":
    print("🧪 Тестирование brain.py...")
    try:
        brain = ComponentLibraryBrain()
        print("✅ Brain инициализирован успешно")
        print(f"   Модель: {brain.model}")
        print(f"   Базовый URL: {brain.base_url}")
        
        # Тестовый запрос без ключа
        test_query = "Найди советские транзисторы"
        print(f"\n🧪 Тестовый запрос (без ключа): '{test_query}'")
        
        result = brain.process_query(test_query, None)
        print(f"🎯 Результат: успех={result.get('success')}, режим={result.get('mode')}")
        
        if result.get("success"):
            print(f"📊 Найдено компонентов: {result.get('result', {}).get('count', 0)}")
        else:
            print(f"❌ Ошибка: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")