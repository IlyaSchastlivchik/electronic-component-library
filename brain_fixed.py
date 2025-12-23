import json
import os
import asyncio
import aiohttp
from typing import Dict
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv(override=True)

class ComponentLibraryBrain:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = base_url
        self.model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
        
        if not self.api_key:
            raise ValueError("❌ OPENROUTER_API_KEY не найден в .env файле!")
        else:
            print(f"✅ API-ключ загружен: {self.api_key[:20]}...")
    
    def create_prompt(self, user_question: str) -> str:
        prompt = f"""Ты — ассистент для библиотеки электронных компонентов.
        
Запрос пользователя: "{user_question}"

Ответь ТОЛЬКО валидным JSON без лишнего текста в формате:
{{"command": "search_components", "args": {{"type": "bjt", "Imax_min": 0.1}}, "explanation": "Пояснение"}}

Доступные параметры для поиска:
- type: bjt (биполярные транзисторы), mosfet (полевые транзисторы), vacuum_tube (лампы), diode (диоды)
- Imax_min: минимальный ток (например: 0.1)
- Imax_max: максимальный ток
- Uce_min: минимальное напряжение
- Uce_max: максимальное напряжение  
- Ptot_min: минимальная мощность
- Ptot_max: максимальная мощность
- origin: soviet (советские), usa (американские)
- search_text: текст для поиска в названии/описании
- sort_by: Ptot_desc (мощность по убыванию), Ptot_asc, Imax_desc, Imax_asc

Примеры:
Вопрос: "Найди биполярные транзисторы с током больше 0.1А"
Ответ: {{"command": "search_components", "args": {{"type": "bjt", "Imax_min": 0.1}}, "explanation": "Ищу биполярные транзисторы с током от 0.1А"}}

Вопрос: "Покажи все советские компоненты"
Ответ: {{"command": "search_components", "args": {{"origin": "soviet"}}, "explanation": "Ищу компоненты советского производства"}}

Вопрос: "Самый мощный транзистор"
Ответ: {{"command": "search_components", "args": {{"sort_by": "Ptot_desc"}}, "explanation": "Ищу транзисторы, отсортированные по мощности"}}

Теперь ответь на: "{user_question}"

JSON ответ:"""
        return prompt
    
    async def ask_openrouter(self, prompt: str) -> str:
        """Асинхронная отправка запроса к OpenRouter"""
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
                {"role": "system", "content": "Ты возвращаешь только валидный JSON без пояснений."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        try:
            print(f"🤖 Запрос к модели {self.model}...")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    if not content:
                        raise ValueError("Пустой ответ от модели")
                    
                    print(f"✅ Получен ответ: {content[:100]}...")
                    return content
                    
        except Exception as e:
            print(f"❌ Ошибка OpenRouter: {e}")
            return json.dumps({
                "command": "search_components", 
                "args": {}, 
                "explanation": f"Ошибка: {str(e)}"
            })
    
    def parse_command(self, json_response: str) -> Dict:
        """Парсинг JSON ответа"""
        try:
            cleaned = json_response.strip()
            # Удаляем ```json и ```
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            parsed = json.loads(cleaned)
            
            # Проверяем структуру
            if "command" not in parsed:
                parsed["command"] = "search_components"
            if "args" not in parsed:
                parsed["args"] = {}
            if "explanation" not in parsed:
                parsed["explanation"] = "Выполняю запрос"
            
            print(f"✅ Команда: {parsed['command']}, Аргументы: {parsed['args']}")
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            print(f"   Сырой ответ: {json_response[:200]}")
            return {"command": "search_components", "args": {}, "explanation": "Не удалось распознать запрос"}
    
    async def execute_command(self, command_data: Dict) -> Dict:
        """Асинхронное выполнение команды"""
        command = command_data.get("command", "search_components")
        args = command_data.get("args", {})
        
        try:
            print(f"🔧 Выполняю: {command}, Аргументы: {args}")
            
            if command == "search_components":
                # Очищаем параметры
                params = {}
                for key, value in args.items():
                    if value is not None:
                        # Преобразуем числовые параметры
                        if key in ['Imax_min', 'Imax_max', 'Uce_min', 'Uce_max', 'Ptot_min', 'Ptot_max']:
                            try:
                                params[key] = float(value)
                            except:
                                continue
                        else:
                            params[key] = value
                
                print(f"📤 Запрос с параметрами: {params}")
                
                # Делаем асинхронный запрос
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/components", params=params, timeout=10) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ Получено {result.get('count', 0)} компонентов")
                            return result
                        else:
                            error_text = await response.text()
                            return {"error": f"Ошибка сервера: {response.status}", "details": error_text[:200]}
            
            elif command in ["get_component_details", "get_characteristics"]:
                component_id = args.get("component_id")
                if not component_id:
                    return {"error": "Не указан ID компонента"}
                
                endpoint = "/characteristics" if command == "get_characteristics" else ""
                url = f"{self.base_url}/components/{component_id}{endpoint}"
                
                print(f"🌐 URL: {url}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            return {"error": f"Ошибка сервера: {response.status}", "details": error_text[:200]}
            
            else:
                return {"error": f"Неизвестная команда: {command}"}
                
        except aiohttp.ClientError as e:
            print(f"❌ Ошибка соединения: {e}")
            return {"error": f"Ошибка соединения: {str(e)}"}
        except Exception as e:
            print(f"❌ Ошибка выполнения: {e}")
            return {"error": f"Внутренняя ошибка: {str(e)}"}
    
    async def process_query(self, user_question: str) -> Dict:
        """Асинхронная обработка запроса"""
        print(f"\n📝 Вопрос: '{user_question}'")
        
        # Шаг 1: Создаем промпт
        prompt = self.create_prompt(user_question)
        
        # Шаг 2: Запрашиваем у OpenRouter
        json_response = await self.ask_openrouter(prompt)
        
        # Шаг 3: Парсим команду
        command_data = self.parse_command(json_response)
        
        # Шаг 4: Выполняем команду
        result = await self.execute_command(command_data)
        
        # Формируем ответ
        response = {
            "user_question": user_question,
            "command": command_data,
            "result": result,
            "success": "error" not in result
        }
        
        print(f"✅ Завершено. Успех: {response['success']}")
        return response

# Синхронная обертка для совместимости
class ComponentLibraryBrainSync:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.brain = ComponentLibraryBrain(base_url)
    
    def process_query(self, user_question: str) -> Dict:
        """Синхронная версия process_query"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.brain.process_query(user_question))
            return result
        finally:
            loop.close()