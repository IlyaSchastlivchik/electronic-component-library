import json

def deep_check_components():
    try:
        with open('components.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("="*60)
        print("🔍 ГЛУБОКАЯ ПРОВЕРКА components.json")
        print("="*60)
        print(f"Всего компонентов: {len(data)}\n")
        
        for i, comp in enumerate(data):
            print(f"\n{i+1}. ID: {comp.get('id', 'N/A')}")
            print(f"   Все ключи объекта: {list(comp.keys())}")
            
            # Проверяем наличие и значение origin
            if 'origin' in comp:
                origin_value = comp['origin']
                print(f"   ✅ Поле 'origin' найдено.")
                print(f"      Значение: '{origin_value}' (тип: {type(origin_value)})")
                print(f"      Длина строки: {len(origin_value)}")
                print(f"      Коды символов: {[ord(c) for c in origin_value]}")
                
                # Сравнение
                if origin_value == "soviet":
                    print(f"      🎯 Значение СОВПАДАЕТ со строкой 'soviet'")
                else:
                    print(f"      ❌ Значение НЕ СОВПАДАЕТ со строкой 'soviet'")
            else:
                print(f"   ❌ Поле 'origin' ОТСУТСТВУЕТ в этом объекте!")
            
            # Дополнительно: покажем raw-представление всего объекта
            print(f"   Raw JSON кусок: {json.dumps(comp, ensure_ascii=False)[:100]}...")
        
        print("\n" + "="*60)
        print("Проверка завершена.")
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
    except Exception as e:
        print(f"❌ Другая ошибка: {e}")

if __name__ == "__main__":
    deep_check_components()