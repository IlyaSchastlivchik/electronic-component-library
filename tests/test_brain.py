#!/usr/bin/env python3
"""
Тестирование brain.py
"""

import sys
import os
sys.path.append('.')

def test_brain_directly():
    """Прямое тестирование brain.py"""
    print("🧪 Прямое тестирование brain.py...")
    print("="*60)
    
    try:
        from brain import ComponentLibraryBrain
        brain = ComponentLibraryBrain()
        
        test_queries = [
            "Покажи все компоненты",
            "Найди биполярные транзисторы",
            "Советские компоненты",
            "Характеристики 2N3904",
            "Самый мощный транзистор"
        ]
        
        for query in test_queries:
            print(f"\n📝 Тест запроса: '{query}'")
            result = brain.process_query(query)
            
            if result.get("success"):
                count = result.get('result', {}).get('count', 0)
                print(f"   ✅ Успех! Найдено компонентов: {count}")
                
                if count > 0 and 'components' in result['result']:
                    for comp in result['result']['components'][:3]:  # Показать первые 3
                        print(f"      • {comp['id']} ({comp['name']})")
            else:
                error = result.get('result', {}).get('error', 'Неизвестная ошибка')
                print(f"   ❌ Ошибка: {error}")
                
    except ImportError as e:
        print(f"❌ Не удалось импортировать brain.py: {e}")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        print(traceback.format_exc())

def test_api_directly():
    """Прямое тестирование API endpoints"""
    print("\n" + "="*60)
    print("🌐 Тестирование API endpoints...")
    print("="*60)
    
    import requests
    
    endpoints = [
        "http://localhost:8000/api/components",
        "http://localhost:8000/api/components/2N3904",
        "http://localhost:8000/api/components/2N3904/characteristics"
    ]
    
    for url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            print(f"\n📡 {url}")
            print(f"   Статус: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Успех")
            else:
                print(f"   ❌ Ошибка: {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ Не удалось подключиться: {e}")

if __name__ == "__main__":
    print("🔍 Тестирование системы AI Component Library")
    print("="*60)
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("   Создайте файл .env с переменными:")
        print("   OPENROUTER_API_KEY=ваш_ключ")
        print("   OPENROUTER_MODEL=deepseek/deepseek-chat")
        print("   API_BASE_URL=http://localhost:8000")
    else:
        print("✅ Файл .env найден")
    
    # Тестируем brain.py
    test_brain_directly()
    
    # Тестируем API
    test_api_directly()
    
    print("\n" + "="*60)
    print("🎯 Инструкция по запуску:")
    print("1. Убедитесь, что web_app.py запущен")
    print("2. Откройте http://localhost:8000 в браузере")
    print("3. Перейдите на страницу ИИ-поиска")
    print("4. Введите запрос, например: 'Покажи все компоненты'")
    print("="*60)