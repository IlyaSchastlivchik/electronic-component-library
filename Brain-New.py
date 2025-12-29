import json
import os
import requests
from typing import Dict
from dotenv import load_dotenv

# 🔧 КРИТИЧЕСКАЯ ПРАВКА ДЛЯ RENDER - ЕДИНЫЙ ПУТЬ
# Проверяем все возможные пути к конфигурации
def load_environment():
    env_paths = [
        '/etc/secrets/.env',    # Render Secret Files
        '.env',                  # Локальная разработка
        '../.env',               # Альтернативный локальный путь
        '../../.env'             # Еще один возможный путь
    ]
    
    for path in env_paths:
        if os.path.exists(path):
            load_dotenv(path, override=True)
            print(f"✅ Загружен .env из {path}")
            return True
    
    print("⚠️  .env файл не найден. Использую переменные окружения системы.")
    return False

# Загружаем конфигурацию
load_environment()

class ComponentLibraryBrain:
    def __init__(self):
        # 🔧 ОСНОВНЫЕ ПЕРЕМЕННЫЕ ДЛЯ OPENROUTER И DEEPSEEK V3
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")  # ⬅️ CHAT по умолчанию
        
        # 🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ДЛЯ RENDER
        # На Render нужно использовать localhost с портом из переменной PORT
        render_port = os.environ.get("PORT", "8000")
        if "RENDER" in os.environ:  # Автоматическое определение Render
            self.base_url = f"http://localhost:{render_port}"
            print(f"🌍 Обнаружена среда Render, использую localhost:{render_port}")
        else:
            self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        
        # Настройки приложения
        self.app_name = os.getenv("APP_NAME", "Electronic Component Library")
        self.app_url = os.getenv("APP_URL", f"http://localhost:{render_port}")
        
        # 🔧 ВАЛИДАЦИЯ КОНФИГУРАЦИИ
        if not self.api_key:
            print("⚠️  OPENROUTER_API_KEY не найден! Режим brain.py будет работать только для поиска в локальной базе.")
        else:
            print(f"✅ API-ключ загружен: {self.api_key[:20]}...")
            print(f"🤖 Используется модель: {self.model}")
        
        print(f"🌐 API_BASE_URL: {self.base_url}")
        
        # 🔧 КОНФИГУРАЦИЯ БИБЛИОТЕКИ
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
        "args": {{"origin": "soviet", "Imax_min": 0.1, "type": "bjt"}},
        "explanation": "Поиск советских биполярных транзисторов с током более 0.1А"
   }}

2. Запрос: "Покажи характеристики транзистора 2N3904"
   Ответ: {{
        "command": "get_characteristics",
        "args": {{"component_id": "2N3904"}},
        "explanation": "Получение вольт-амперных характеристик транзистора 2N3904"
   }}

3. Запрос: "Какие мощные полевые транзисторы есть в базе?"
   Ответ: {{
        "command": "search_components",
        "args": {{"type": "mosfet", "Ptot_min": 10}},
        "explanation": "Поиск полевых транзисторов мощностью более 10Вт"
   }}

Теперь обработай запрос пользователя и верни JSON:
"""
        return prompt
    
    def ask_openrouter(self, prompt: str) -> str:
        """Отправка запроса к OpenRouter для DeepSeek Chat"""
        # Если нет API ключа, возвращаем команду по умолчанию для поиска
        if not self.api_key:
            print("⚠️  API ключ отсутствует, использую режим поиска по умолчанию")
            return json.dumps({
                "command": "search_components",
                "args": {},
                "explanation": "Поиск компонентов в локальной базе данных"
            })
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.app_url,
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
                for key in ['Imax_min', 'Imax_max', 'Uce_min', 'Uce_max', 'Ptot_min', 'Ptot_max']:
                    if key in params:
                        try:
                            params[key] = float(params[key])
                        except (ValueError, TypeError):
                            # Если не удалось преобразовать, удаляем параметр
                            params.pop(key, None)
                
                # 🔧 ИСПРАВЛЕНИЕ: Используем /api/components вместо /components
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
    
    def process_query(self, user_question: str) -> Dict:
        """Основной метод обработки запроса пользователя"""
        try:
            print(f"\n🎯 Обрабатываю запрос: '{user_question}'")
            
            # Создаем промпт
            prompt = self.create_prompt(user_question)
            print(f"📝 Промпт создан ({len(prompt)} символов)")
            
            # Запрашиваем ответ у ИИ
            json_response = self.ask_openrouter(prompt)
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
                "result": result
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
                "details": traceback.format_exc()
            }

# 🔧 АВТОТЕСТ ПРИ ЗАПУСКЕ
if __name__ == "__main__":
    print("🧪 Тестирование brain.py...")
    try:
        brain = ComponentLibraryBrain()
        print("✅ Brain инициализирован успешно")
        print(f"   Модель: {brain.model}")
        print(f"   Базовый URL: {brain.base_url}")
        
        # Тестовый запрос
        test_query = "Найди советские транзисторы"
        print(f"\n🧪 Тестовый запрос: '{test_query}'")
        
        result = brain.process_query(test_query)
        print(f"🎯 Результат: успех={result.get('success')}")
        
        if result.get("success"):
            print(f"📊 Найдено компонентов: {result.get('result', {}).get('count', 0)}")
        else:
            print(f"❌ Ошибка: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")

index.html:
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-md-8">
        <div class="jumbotron bg-light p-5 rounded">
            <h1 class="display-4"><i class="fas fa-robot"></i> AI Component Library</h1>
            <p class="lead">Открытая база электронных компонентов с ИИ-ассистентом</p>
            <hr class="my-4">
            <p>Ищите компоненты по параметрам, анализируйте характеристики, получайте рекомендации на естественном языке.</p>
            
            {% if brain_available %}
            <div class="alert alert-success">
                <i class="fas fa-check-circle"></i> ИИ-модуль активен. Используйте естественный язык для поиска!
            </div>
            {% else %}
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i> ИИ-модуль не доступен. Работает только параметрический поиск.
            </div>
            {% endif %}
            
            <a class="btn btn-primary btn-lg" href="/components" role="button">
                <i class="fas fa-search"></i> Начать поиск
            </a>
            {% if brain_available %}
            <a class="btn btn-success btn-lg" href="/ai-query" role="button">
                <i class="fas fa-robot"></i> Задать вопрос ИИ
            </a>
            {% endif %}
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <i class="fas fa-chart-bar"></i> Статистика базы
            </div>
            <div class="card-body">
                <ul class="list-group list-group-flush">
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Всего компонентов:</span>
                        <span class="badge bg-primary rounded-pill">{{ stats.total_components }}</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Биполярные транзисторы:</span>
                        <span class="badge bg-info rounded-pill">{{ stats.bjt_count }}</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Полевые транзисторы:</span>
                        <span class="badge bg-info rounded-pill">{{ stats.mosfet_count }}</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Лампы:</span>
                        <span class="badge bg-info rounded-pill">{{ stats.tube_count }}</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Советские компоненты:</span>
                        <span class="badge bg-warning rounded-pill">{{ stats.soviet_count }}</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Американские компоненты:</span>
                        <span class="badge bg-warning rounded-pill">{{ stats.usa_count }}</span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-12">
        <h3><i class="fas fa-star"></i> Избранные компоненты</h3>
        <div class="row">
            {% for component in featured_components %}
            <div class="col-md-4 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">{{ component.id }}</h5>
                        <h6 class="card-subtitle mb-2 text-muted">{{ component.name }}</h6>
                        <p class="card-text small">{{ component.description[:100] }}...</p>
                        <div class="mt-2">
                            <span class="badge bg-secondary">{{ component.type }}</span>
                            <span class="badge bg-{% if component.origin == 'soviet' %}warning{% else %}info{% endif %}">
                                {{ component.origin|upper }}
                            </span>
                        </div>
                    </div>
                    <div class="card-footer">
                        <a href="/component/{{ component.id }}" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-info-circle"></i> Подробнее
                        </a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}