from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
import logging
from typing import Optional
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Создаем веб-приложение
app = FastAPI(title="AI Component Library Web Interface")

# Монтируем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Загружаем базу компонентов
def load_components():
    try:
        with open('components.json', 'r', encoding='utf-8') as f:
            components = json.load(f)
            logger.info(f"✅ Загружено {len(components)} компонентов")
            return components
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки components.json: {e}")
        return []

components = load_components()

# ==================== ИНИЦИАЛИЗАЦИЯ ИИ-МОДУЛЯ ====================
# ИСПРАВЛЕНО: Используем асинхронную версию напрямую
try:
    from brain_fixed import ComponentLibraryBrain
    brain = ComponentLibraryBrain()
    brain_available = True
    logger.info("✅ ИИ-модуль (асинхронный) успешно загружен")
except ImportError as e:
    logger.warning(f"⚠️ brain_fixed.py не найден. ИИ-функциональность недоступна: {e}")
    brain_available = False
    brain = None
except Exception as e:
    logger.error(f"❌ Ошибка инициализации brain: {e}")
    brain_available = False
    brain = None

# ==================== ВЕБ-ИНТЕРФЕЙС ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница"""
    # Получаем статистику
    stats = {
        "total_components": len(components),
        "bjt_count": len([c for c in components if c['type'] == 'bjt']),
        "mosfet_count": len([c for c in components if c['type'] == 'mosfet']),
        "tube_count": len([c for c in components if c['type'] == 'vacuum_tube']),
        "diode_count": len([c for c in components if c['type'] == 'diode']),
        "soviet_count": len([c for c in components if c.get('origin') == 'soviet']),
        "usa_count": len([c for c in components if c.get('origin') == 'usa'])
    }
    
    # Берем несколько компонентов для показа на главной
    featured_components = components[:6]
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats,
        "featured_components": featured_components,
        "brain_available": brain_available
    })

@app.get("/components", response_class=HTMLResponse)
async def components_page(
    request: Request,
    type: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("Ptot_desc")
):
    """Страница поиска компонентов"""
    # Фильтрация компонентов
    filtered = components.copy()
    
    # Применяем фильтры
    if type:
        filtered = [c for c in filtered if c['type'] == type]
    
    if origin:
        filtered = [c for c in filtered if c.get('origin', '').lower() == origin.lower()]
    
    if search_text:
        search_lower = search_text.lower()
        filtered = [
            c for c in filtered 
            if search_lower in c.get('name', '').lower() 
            or search_lower in c.get('description', '').lower()
            or search_lower in c.get('id', '').lower()
        ]
    
    # Сортировка
    if sort_by:
        try:
            if '_' in sort_by:
                sort_field, sort_order = sort_by.split('_')
            else:
                sort_field, sort_order = sort_by, 'asc'
            
            reverse_order = (sort_order.lower() == 'desc')
            filtered.sort(key=lambda x: x['params'].get(sort_field, 0), reverse=reverse_order)
        except Exception as e:
            logger.warning(f"Ошибка сортировки: {e}")
    
    return templates.TemplateResponse("search.html", {
        "request": request,
        "components": filtered,
        "count": len(filtered),
        "filters": {
            "type": type,
            "origin": origin,
            "search_text": search_text,
            "sort_by": sort_by
        },
        "brain_available": brain_available
    })

@app.get("/component/{component_id}", response_class=HTMLResponse)
async def component_detail(request: Request, component_id: str):
    """Страница компонента"""
    # Находим компонент
    component = next((c for c in components if c['id'] == component_id), None)
    
    if not component:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_code": 404,
            "error_title": "Компонент не найден",
            "error_message": f"Компонент '{component_id}' не найден в базе данных",
            "brain_available": brain_available
        })
    
    # Загружаем характеристики если есть
    characteristics = None
    file_path = component.get('characteristics_file')
    
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = f.read()
            
            # Парсим данные
            lines = data.strip().split('\n')
            characteristics = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.replace(',', ' ').split()
                if len(parts) >= 2:
                    try:
                        voltage = float(parts[0])
                        current = float(parts[1])
                        characteristics.append({"voltage": voltage, "current": current})
                    except ValueError:
                        continue
                        
        except Exception as e:
            logger.error(f"Ошибка чтения характеристик: {e}")
    
    return templates.TemplateResponse("component.html", {
        "request": request,
        "component": component,
        "characteristics": characteristics,
        "brain_available": brain_available
    })

@app.get("/ai-query", response_class=HTMLResponse)
async def ai_query_page(request: Request):
    """Страница ИИ-запросов"""
    return templates.TemplateResponse("ai_query.html", {
        "request": request,
        "brain_available": brain_available
    })

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """Страница о проекте"""
    return templates.TemplateResponse("about.html", {
        "request": request,
        "brain_available": brain_available
    })

# ==================== API ENDPOINTS ====================

@app.get("/api/components")
async def api_get_components(
    type: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None)
):
    """API: Получение компонентов"""
    filtered = components.copy()
    
    if type:
        filtered = [c for c in filtered if c['type'] == type]
    
    if origin:
        filtered = [c for c in filtered if c.get('origin', '').lower() == origin.lower()]
    
    if search_text:
        search_lower = search_text.lower()
        filtered = [
            c for c in filtered 
            if search_lower in c.get('name', '').lower() 
            or search_lower in c.get('description', '').lower()
            or search_lower in c.get('id', '').lower()
        ]
    
    if sort_by:
        try:
            if '_' in sort_by:
                sort_field, sort_order = sort_by.split('_')
            else:
                sort_field, sort_order = sort_by, 'asc'
            
            reverse_order = (sort_order.lower() == 'desc')
            filtered.sort(key=lambda x: x['params'].get(sort_field, 0), reverse=reverse_order)
        except Exception as e:
            logger.warning(f"Ошибка сортировки: {e}")
    
    return {
        "count": len(filtered),
        "components": filtered
    }

@app.get("/api/components/{component_id}")
async def api_get_component(component_id: str):
    """API: Получение компонента по ID"""
    component = next((c for c in components if c['id'] == component_id), None)
    
    if not component:
        raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found")
    
    return component

@app.get("/api/components/{component_id}/characteristics")
async def api_get_characteristics(component_id: str):
    """API: Получение характеристик компонента"""
    component = next((c for c in components if c['id'] == component_id), None)
    
    if not component:
        raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found")
    
    file_path = component.get('characteristics_file')
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Characteristics file for '{component_id}' not found")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()
        
        lines = data.strip().split('\n')
        characteristics = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.replace(',', ' ').split()
            if len(parts) >= 2:
                try:
                    voltage = float(parts[0])
                    current = float(parts[1])
                    characteristics.append({
                        "voltage": voltage,
                        "current": current
                    })
                except ValueError:
                    continue
        
        return {
            "component_id": component_id,
            "characteristics": characteristics
        }
        
    except Exception as e:
        logger.error(f"Ошибка чтения характеристик: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading characteristics: {str(e)}")

@app.post("/api/ai-query")
async def api_process_ai_query(request: Request):
    """API: Обработка ИИ-запроса"""
    if not brain_available or not brain:
        logger.error("ИИ-модуль недоступен")
        return JSONResponse({
            "success": False,
            "error": "ИИ-модуль недоступен"
        }, status_code=503)
    
    try:
        data = await request.json()
        user_query = data.get("query", "")
        
        logger.info(f"🔍 ИИ-запрос получен: '{user_query}'")
        
        if not user_query:
            logger.warning("Пустой ИИ-запрос")
            return JSONResponse({
                "success": False,
                "error": "Пустой запрос"
            }, status_code=400)
        
        # ИСПРАВЛЕНО: Добавляем await для асинхронного вызова
        logger.info("⏳ Обработка запроса через brain...")
        result = await brain.process_query(user_query)  # ВОТ ЗДЕСЬ ДОБАВЬ AWAIT!
        logger.info(f"✅ Результат обработки: успех={result.get('success')}")
        
        return JSONResponse(result)
        
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON в запросе: {e}")
        return JSONResponse({
            "success": False,
            "error": "Некорректный JSON в запросе"
        }, status_code=400)
    except Exception as e:
        logger.error(f"Ошибка обработки ИИ-запроса: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            "success": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }, status_code=500)

# ==================== ОБРАБОТЧИКИ ОШИБОК ====================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error_code": 404,
        "error_title": "Страница не найдена",
        "error_message": f"Страница {request.url.path} не существует",
        "brain_available": brain_available
    }, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error_code": 500,
        "error_title": "Внутренняя ошибка сервера",
        "error_message": "Произошла внутренняя ошибка сервера",
        "brain_available": brain_available
    }, status_code=500)

# ==================== ЗАПУСК СЕРВЕРА ====================

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("🌐 Запуск веб-интерфейса AI Component Library")
    print("📡 API доступен на: http://localhost:8000/api")
    print("🌍 Веб-интерфейс: http://localhost:8000")
    print("📚 Документация API: http://localhost:8000/docs")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8000)