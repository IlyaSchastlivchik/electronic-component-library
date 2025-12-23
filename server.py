from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Electronic Component Library API")

# Разрешаем CORS для локальной разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Загружаем базу компонентов при старте
def load_components():
    try:
        with open('components.json', 'r', encoding='utf-8') as f:
            components = json.load(f)
            logger.info(f"✅ Загружено {len(components)} компонентов")
            for comp in components:
                logger.info(f"   • {comp['id']} (тип: {comp['type']}, происхождение: {comp.get('origin', 'не указано')})")
            return components
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки components.json: {e}")
        return []

components = load_components()

@app.get("/")
def read_root():
    return {
        "message": "Electronic Component Library API",
        "version": "0.1.0",
        "endpoints": {
            "GET /components": "Get all components or filter by parameters",
            "GET /components/{id}": "Get component by ID",
            "GET /components/{id}/characteristics": "Get component characteristics"
        }
    }

@app.get("/components")
def get_components(
    type: str = Query(None, description="Тип компонента (bjt, mosfet, vacuum_tube, diode)"),
    Imax_min: float = Query(None, description="Минимальный ток (A)"),
    Imax_max: float = Query(None, description="Максимальный ток (A)"),
    Uce_min: float = Query(None, description="Минимальное напряжение (V)"),
    Uce_max: float = Query(None, description="Максимальное напряжение (V)"),
    Ptot_min: float = Query(None, description="Минимальная мощность (W)"),
    Ptot_max: float = Query(None, description="Максимальная мощность (W)"),
    origin: str = Query(None, description="Происхождение/страна (soviet, usa, other)"),  # НОВЫЙ ПАРАМЕТР
    search_text: str = Query(None, description="Поиск по названию и описанию"),  # НОВЫЙ ПАРАМЕТР
    sort_by: str = Query(None, description="Поле для сортировки: 'Ptot_desc' (мощность по убыванию), 'Ptot_asc', 'Imax_desc', 'Imax_asc', 'Uce_desc', 'Uce_asc'")
):
    """
    Получить компоненты с фильтрацией по параметрам
    """
    logger.info(f"🔍 Запрос с параметрами: type={type}, origin={origin}, search_text={search_text}, sort_by={sort_by}")
    
    filtered = components.copy()
    
    # Применяем фильтры, если они указаны
    if type:
        original_count = len(filtered)
        filtered = [c for c in filtered if c['type'] == type]
        logger.info(f"   Фильтр по типу '{type}': {original_count} → {len(filtered)} компонентов")
    
    if origin:
        original_count = len(filtered)
        filtered = [c for c in filtered if c.get('origin', '').lower() == origin.lower()]
        logger.info(f"   Фильтр по происхождению '{origin}': {original_count} → {len(filtered)} компонентов")
    
    if search_text:
        original_count = len(filtered)
        search_lower = search_text.lower()
        filtered = [
            c for c in filtered 
            if search_lower in c.get('name', '').lower() 
            or search_lower in c.get('description', '').lower()
            or search_lower in c.get('id', '').lower()
        ]
        logger.info(f"   Текстовый поиск '{search_text}': {original_count} → {len(filtered)} компонентов")
    
    if Imax_min is not None:
        original_count = len(filtered)
        filtered = [c for c in filtered if c['params']['Imax'] >= Imax_min]
        logger.info(f"   Фильтр по Imax_min={Imax_min}: {original_count} → {len(filtered)} компонентов")
    
    if Imax_max is not None:
        original_count = len(filtered)
        filtered = [c for c in filtered if c['params']['Imax'] <= Imax_max]
        logger.info(f"   Фильтр по Imax_max={Imax_max}: {original_count} → {len(filtered)} компонентов")
    
    if Uce_min is not None:
        original_count = len(filtered)
        filtered = [c for c in filtered if c['params']['Uce_max'] >= Uce_min]
        logger.info(f"   Фильтр по Uce_min={Uce_min}: {original_count} → {len(filtered)} компонентов")
    
    if Uce_max is not None:
        original_count = len(filtered)
        filtered = [c for c in filtered if c['params']['Uce_max'] <= Uce_max]
        logger.info(f"   Фильтр по Uce_max={Uce_max}: {original_count} → {len(filtered)} компонентов")
    
    if Ptot_min is not None:
        original_count = len(filtered)
        filtered = [c for c in filtered if c['params']['Ptot'] >= Ptot_min]
        logger.info(f"   Фильтр по Ptot_min={Ptot_min}: {original_count} → {len(filtered)} компонентов")
    
    if Ptot_max is not None:
        original_count = len(filtered)
        filtered = [c for c in filtered if c['params']['Ptot'] <= Ptot_max]
        logger.info(f"   Фильтр по Ptot_max={Ptot_max}: {original_count} → {len(filtered)} компонентов")
    
    # СОРТИРОВКА
    if sort_by:
        try:
            # Разделяем sort_by на поле и порядок (например, "Ptot_desc" -> поле="Ptot", порядок="desc")
            if '_' in sort_by:
                sort_field, sort_order = sort_by.split('_')
            else:
                sort_field, sort_order = sort_by, 'asc'
            
            reverse_order = (sort_order.lower() == 'desc')
            
            # Сортируем по указанному полу в параметрах
            filtered.sort(key=lambda x: x['params'].get(sort_field, 0), reverse=reverse_order)
            logger.info(f"   Отсортировано по {sort_field} в порядке {sort_order}")
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка сортировки по {sort_by}: {e}")
    
    logger.info(f"✅ Возвращаю {len(filtered)} компонентов")
    
    return {
        "count": len(filtered),
        "components": filtered
    }

@app.get("/components/{component_id}")
def get_component(component_id: str):
    """
    Получить компонент по ID
    """
    logger.info(f"🔍 Запрос компонента: {component_id}")
    
    component = next((c for c in components if c['id'] == component_id), None)
    
    if not component:
        logger.warning(f"❌ Компонент '{component_id}' не найден")
        return {"error": f"Component '{component_id}' not found"}
    
    logger.info(f"✅ Компонент '{component_id}' найден")
    return component

@app.get("/components/{component_id}/characteristics")
def get_characteristics(component_id: str):
    """
    Получить характеристики (ВАХ) компонента
    """
    logger.info(f"🔍 Запрос характеристик для: {component_id}")
    
    component = next((c for c in components if c['id'] == component_id), None)
    
    if not component:
        logger.warning(f"❌ Компонент '{component_id}' не найден")
        return {"error": f"Component '{component_id}' not found"}
    
    file_path = component.get('characteristics_file')
    
    if not file_path or not os.path.exists(file_path):
        logger.warning(f"❌ Файл характеристик для '{component_id}' не найден: {file_path}")
        return {"error": f"Characteristics file for '{component_id}' not found"}
    
    try:
        # Пробуем разные кодировки для чтения файлов
        encodings_to_try = ['utf-8', 'windows-1251', 'cp866', 'cp1251', 'latin-1']
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    data = f.read()
                logger.info(f"✅ Файл прочитан в кодировке {encoding}")
                break
            except UnicodeDecodeError:
                continue
        else:
            # Если ни одна кодировка не подошла, используем бинарный режим с игнорированием ошибок
            with open(file_path, 'rb') as f:
                data = f.read().decode('utf-8', errors='ignore')
            logger.warning(f"⚠️ Использован игнорирующий декодер для {file_path}")
        
        # Парсим данные (формат: напряжение, ток)
        lines = data.strip().split('\n')
        characteristics = []
        
        for line in lines:
            # Пропускаем комментарии и пустые строки
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Заменяем запятые на пробелы и разбиваем
            parts = line.replace(',', ' ').split()
            
            if len(parts) >= 2:
                try:
                    voltage = float(parts[0])
                    current = float(parts[1])
                    
                    characteristics.append({
                        "voltage": voltage,
                        "current": current
                    })
                except ValueError as e:
                    logger.warning(f"⚠️ Ошибка парсинга строки '{line}': {e}")
                    continue
        
        logger.info(f"✅ Загружено {len(characteristics)} точек ВАХ для '{component_id}'")
        
        return {
            "component_id": component_id,
            "characteristics": characteristics
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка чтения характеристик: {str(e)}")
        return {"error": f"Error reading characteristics: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("🚀 Запуск сервера библиотеки компонентов (с поиском по происхождению)")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8000)