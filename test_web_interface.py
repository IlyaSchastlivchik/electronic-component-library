#!/usr/bin/env python3
"""
Тестирование веб-интерфейса с запросами к ИИ
"""

import requests
import json
import time

def test_web_ai_query():
    """Тест запросов к веб-интерфейсу"""
    print("🧪 Тестирование веб-интерфейса /api/ai-query")
    print("="*60)
    
    base_url = "http://localhost:8000"
    
    # Сначала проверяем доступность сервера
    try:
        resp = requests.get(f"{base_url}/", timeout=5)
        if resp.status_code != 200:
            print("❌ Сервер не отвечает")
            return False
    except:
        print("❌ Сервер не запущен. Запустите: python web_app.py")
        return False
    
    print("✅ Сервер доступен")
    
    # Тестируем простые запросы
    test_queries = [
        "Покажи все компоненты",
        "Найди биполярные транзисторы",
        "Советские компоненты",
        "Характеристики 2N3904"
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n📝 Тест запроса: '{query}'")
        
        try:
            # Отправляем POST запрос к /api/ai-query
            response = requests.post(
                f"{base_url}/api/ai-query",
                json={"query": query},
                timeout=15  # Даем больше времени на обработку
            )
            
            print(f"   Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                success = result.get("success", False)
                
                if success:
                    count = result.get('result', {}).get('count', 0)
                    print(f"   ✅ Успех! Найдено: {count} компонентов")
                    
                    if count > 0 and 'components' in result['result']:
                        for comp in result['result']['components'][:2]:
                            print(f"      • {comp['id']} ({comp['name']})")
                    results.append(True)
                else:
                    error = result.get('error') or result.get('result', {}).get('error', 'Неизвестная ошибка')
                    print(f"   ❌ Ошибка brain: {error}")
                    results.append(False)
            else:
                print(f"   ❌ HTTP ошибка: {response.status_code}")
                print(f"      Текст: {response.text[:200]}")
                results.append(False)
                
        except requests.exceptions.Timeout:
            print("   ⏱️  Таймаут запроса (15 секунд)")
            results.append(False)
        except Exception as e:
            print(f"   💥 Исключение: {e}")
            results.append(False)
        
        # Пауза между запросами
        time.sleep(1)
    
    # Сводка
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 Итог: {success_count}/{total_count} запросов успешно")
    
    if success_count == total_count:
        print("🎉 Веб-интерфейс работает корректно!")
        return True
    else:
        print(f"⚠️  Есть проблемы с {total_count - success_count} запросами")
        return False

def check_api_endpoints():
    """Проверка всех API endpoints"""
    print("\n🌐 Проверка API endpoints...")
    print("="*60)
    
    base_url = "http://localhost:8000"
    endpoints = [
        ("GET /", "Главная страница"),
        ("GET /components", "Поиск компонентов"),
        ("GET /ai-query", "Страница ИИ"),
        ("GET /api/components", "API компонентов"),
        ("POST /api/ai-query", "API ИИ-запросов"),
    ]
    
    for endpoint, description in endpoints:
        try:
            if "POST" in endpoint:
                response = requests.post(
                    f"{base_url}/api/ai-query",
                    json={"query": "тест"},
                    timeout=5
                )
            else:
                url = f"{base_url}{endpoint.split(' ')[1]}"
                response = requests.get(url, timeout=5)
            
            print(f"{'✅' if response.status_code == 200 else '❌'} {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: ошибка - {e}")

if __name__ == "__main__":
    print("🔍 Тестирование интеграции веб-интерфейса и ИИ")
    print("="*60)
    
    # Запускаем тесты
    web_ok = test_web_ai_query()
    check_api_endpoints()
    
    print("\n" + "="*60)
    print("🎯 Рекомендации:")
    
    if not web_ok:
        print("1. ❌ Проблемы с веб-интерфейсом")
        print("   Проверьте:")
        print("   - Импорт brain_fixed.ComponentLibraryBrain в web_app.py")
        print("   - Используете ли вы 'await brain.process_query()'")
        print("   - Логи в консоли при отправке запроса")
    else:
        print("1. ✅ Веб-интерфейс работает")
    
    print("2. 🔍 Откройте DevTools браузера (F12)")
    print("   - Вкладка Console: ошибки JavaScript")
    print("   - Вкладка Network: запросы к /api/ai-query")
    print("3. 📝 Проверьте файл .env с API ключом")
    print("="*60)