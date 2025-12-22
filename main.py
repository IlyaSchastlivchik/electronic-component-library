#!/usr/bin/env python3
"""
Главный скрипт для демонстрации работы библиотеки компонентов
"""

import json
from brain import ComponentLibraryBrain

def print_result(result: dict):
    """
    Красиво выводит результат
    """
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТ ЗАПРОСА")
    print("="*60)
    
    if not result.get("success"):
        print(f"❌ Ошибка: {result.get('result', {}).get('error', 'Неизвестная ошибка')}")
        return
    
    command = result.get("command", {})
    data = result.get("result", {})
    
    # Выводим объяснение команды
    explanation = command.get("explanation", "")
    if explanation:
        print(f"💡 {explanation}")
    
    # Обрабатываем разные типы результатов
    if "components" in data:
        # Результат поиска компонентов
        count = data.get("count", 0)
        print(f"\n🔍 Найдено компонентов: {count}")
        
        if count > 0:
            print("\n📋 Список компонентов:")
            print("-"*40)
            
            for i, component in enumerate(data["components"], 1):
                print(f"\n{i}. {component['id']} - {component['name']}")
                print(f"   Тип: {component['type']}")
                params = component.get('params', {})
                if params:
                    print(f"   Параметры:")
                    for key, value in params.items():
                        unit = "А" if "Imax" in key else "В" if "Uce" in key else "Вт" if "Ptot" in key else ""
                        print(f"   - {key}: {value}{unit}")
                if component.get('description'):
                    print(f"   Описание: {component['description']}")
    
    elif "characteristics" in data:
        # Характеристики компонента
        component_id = data.get("component_id", "")
        characteristics = data.get("characteristics", [])
        
        print(f"\n📈 Характеристики компонента {component_id}:")
        print("-"*40)
        
        if characteristics:
            print("ВАХ (вольт-амперная характеристика):")
            print(f"{'Напряжение (В)':<15} {'Ток (А)':<15}")
            for point in characteristics[:10]:  # Показываем первые 10 точек
                print(f"{point['voltage']:<15.2f} {point['current']:<15.4f}")
            
            if len(characteristics) > 10:
                print(f"... и еще {len(characteristics) - 10} точек")
        else:
            print("Нет данных о характеристиках")
    
    elif "id" in data:
        # Информация о конкретном компоненте
        print(f"\n📄 Информация о компоненте {data['id']}:")
        print("-"*40)
        for key, value in data.items():
            if key == "params" and isinstance(value, dict):
                print(f"Параметры:")
                for param_key, param_value in value.items():
                    unit = "А" if "Imax" in param_key else "В" if "Uce" in param_key else "Вт" if "Ptot" in param_key else ""
                    print(f"  - {param_key}: {param_value}{unit}")
            elif key not in ["characteristics_file"]:
                print(f"{key}: {value}")
    
    else:
        # Произвольный результат
        print(json.dumps(data, ensure_ascii=False, indent=2))
    
    print("\n" + "="*60)

def main():
    """
    Главная функция
    """
    print("="*60)
    print("🤖 ЭЛЕКТРОННАЯ БИБЛИОТЕКА КОМПОНЕНТОВ С ИИ-АССИСТЕНТОМ")
    print("="*60)
    print("Система понимает запросы на естественном языке и ищет")
    print("компоненты в локальной базе данных.")
    print("\nПримеры запросов:")
    print("1. 'Найди биполярные транзисторы с током больше 0.1А'")
    print("2. 'Покажи все полевые транзисторы'")
    print("3. 'Какие лампы есть в базе?'")
    print("4. 'Найди мощные компоненты'")
    print("5. 'Покажи характеристики 2N3904'")
    print("\nДля выхода введите 'выход' или 'exit'")
    
    try:
        # Инициализируем "мозг" системы
        brain = ComponentLibraryBrain()
        
        while True:
            print("\n" + "-"*40)
            user_input = input("\n🎯 Ваш запрос: ").strip()
            
            if user_input.lower() in ['выход', 'exit', 'quit', 'q']:
                print("\n👋 До свидания!")
                break
            
            if not user_input:
                print("⚠️ Пожалуйста, введите запрос")
                continue
            
            # Обрабатываем запрос
            result = brain.process_query(user_input)
            
            # Выводим результат
            print_result(result)
            
    except KeyboardInterrupt:
        print("\n\n👋 Программа завершена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")
        print("Убедитесь, что:")
        print("1. Сервер запущен: python server.py")
        print("2. API ключ указан в .env файле")
        print("3. Все зависимости установлены")

if __name__ == "__main__":
    main()