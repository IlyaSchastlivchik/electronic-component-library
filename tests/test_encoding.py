import os

def test_file_encoding(filename):
    """Тестирует разные кодировки для файла"""
    encodings = ['utf-8', 'windows-1251', 'cp866', 'cp1251', 'latin-1']
    
    print(f"\n🔍 Тестируем файл: {filename}")
    print("-" * 50)
    
    for encoding in encodings:
        try:
            with open(filename, 'r', encoding=encoding) as f:
                content = f.read()
            print(f"✅ {encoding}: {content[:100]}...")
            return encoding, content
        except UnicodeDecodeError as e:
            print(f"❌ {encoding}: Ошибка - {e}")
        except Exception as e:
            print(f"❌ {encoding}: Другая ошибка - {e}")
    
    print("\n⚠️ Ни одна кодировка не подошла, пробуем бинарный режим...")
    with open(filename, 'rb') as f:
        content = f.read()
        print(f"Бинарные данные (первые 100 байт): {content[:100]}")
    
    return None, None

# Тестируем все файлы в characteristics
if __name__ == "__main__":
    files = [
        'characteristics/2n3904_output.txt',
        'characteristics/kt315_output.txt',
        'characteristics/irfz44n_output.txt',
        'characteristics/12ax7_plate.txt'
    ]
    
    for file in files:
        if os.path.exists(file):
            encoding, content = test_file_encoding(file)
            if encoding and content:
                # Сохраняем в UTF-8 если еще не
                if encoding != 'utf-8':
                    with open(file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"📝 Файл пересохранен в UTF-8")
        else:
            print(f"❌ Файл не найден: {file}")