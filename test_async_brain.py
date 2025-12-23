import asyncio
import sys
sys.path.append('.')

async def test_brain():
    from brain_fixed import ComponentLibraryBrain
    
    print("🧪 Тестирование асинхронного brain...")
    brain = ComponentLibraryBrain()
    
    test_queries = [
        "Покажи все компоненты",
        "Найди биполярные транзисторы",
        "Советские компоненты",
        "Характеристики 2N3904",
        "Самый мощный транзистор"
    ]
    
    for query in test_queries:
        print(f"\n📝 Тест: '{query}'")
        try:
            result = await brain.process_query(query)
            if result.get("success"):
                count = result.get('result', {}).get('count', 0)
                print(f"   ✅ Успех! Найдено: {count}")
                if count > 0 and 'components' in result['result']:
                    for comp in result['result']['components'][:2]:
                        print(f"      • {comp['id']} ({comp['name']})")
            else:
                error = result.get('result', {}).get('error', 'Неизвестная ошибка')
                print(f"   ❌ Ошибка: {error}")
        except Exception as e:
            print(f"   💥 Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_brain())