from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
import logging
import asyncio
import traceback
from typing import Optional, List, Dict, Any
import requests
import httpx
from collections import defaultdict

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
            
            # ДОБАВЛЯЕМ СТАРЫЕ ПОЛЯ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ
            for component in components:
                params = component.get('params', {})
                
                # Добавляем Imax если нет
                if 'Imax' not in params:
                    # Пытаемся найти максимальный ток в зависимости от типа
                    if 'max_collector_current' in params:
                        params['Imax'] = params['max_collector_current']
                    elif 'max_drain_current' in params:
                        params['Imax'] = params['max_drain_current']
                    elif 'max_forward_current' in params:
                        params['Imax'] = params['max_forward_current']
                    elif 'secondary_max' in component.get('parameters_extended', {}).get('current_ratings', {}):
                        params['Imax'] = component['parameters_extended']['current_ratings']['secondary_max']
                    else:
                        params['Imax'] = 0
                
                # Добавляем Uce_max если нет
                if 'Uce_max' not in params:
                    if 'max_collector_emitter_voltage' in params:
                        params['Uce_max'] = params['max_collector_emitter_voltage']
                    elif 'max_drain_source_voltage' in params:
                        params['Uce_max'] = params['max_drain_source_voltage']
                    elif 'max_reverse_voltage' in params:
                        params['Uce_max'] = params['max_reverse_voltage']
                    elif 'plate_voltage_max' in params:
                        params['Uce_max'] = params['plate_voltage_max']
                    elif 'primary_max' in component.get('parameters_extended', {}).get('voltage_ratings', {}):
                        params['Uce_max'] = component['parameters_extended']['voltage_ratings']['primary_max']
                    else:
                        params['Uce_max'] = 0
                
                # Добавляем Ptot если нет
                if 'Ptot' not in params:
                    if 'max_power_dissipation' in params:
                        params['Ptot'] = params['max_power_dissipation']
                    elif 'power_rating' in params:
                        params['Ptot'] = params['power_rating']
                    elif 'plate_dissipation' in params:
                        params['Ptot'] = params['plate_dissipation']
                    else:
                        params['Ptot'] = 0
                        
            return components
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки components.json: {e}")
        return []

components = load_components()

# ==================== ИНИЦИАЛИЗАЦИЯ ИИ-МОДУЛЯ ====================
brain = None
brain_available = False

try:
    from brain import ComponentLibraryBrain
    brain = ComponentLibraryBrain()
    brain_available = True
    logger.info("✅ ИИ-модуль (brain.py) успешно загружен")
except ImportError as e:
    logger.warning(f"⚠️ brain.py не найден. Поиск компонентов через ИИ недоступен: {e}")
except Exception as e:
    logger.error(f"❌ Ошибка инициализации brain.py: {e}")
    brain_available = False

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ НОВОЙ СТРУКТУРЫ ====================

def get_power_value(component):
    """Получает значение мощности из разных возможных полей"""
    params = component.get('params', {})
    
    # Сначала новые поля
    if 'max_power_dissipation' in params:
        return params['max_power_dissipation']
    elif 'power_rating' in params:
        return params['power_rating']
    elif 'plate_dissipation' in params:
        return params['plate_dissipation']
    elif 'Ptot' in params:
        return params['Ptot']
    return 0

def get_voltage_value(component):
    """Получает значение напряжения из разных возможных полей"""
    params = component.get('params', {})
    
    if 'max_collector_emitter_voltage' in params:
        return params['max_collector_emitter_voltage']
    elif 'max_drain_source_voltage' in params:
        return params['max_drain_source_voltage']
    elif 'max_reverse_voltage' in params:
        return params['max_reverse_voltage']
    elif 'plate_voltage_max' in params:
        return params['plate_voltage_max']
    elif 'Uce_max' in params:
        return params['Uce_max']
    return 0

def get_current_value(component):
    """Получает значение тока из разных возможных полей"""
    params = component.get('params', {})
    
    if 'max_collector_current' in params:
        return params['max_collector_current']
    elif 'max_drain_current' in params:
        return params['max_drain_current']
    elif 'max_forward_current' in params:
        return params['max_forward_current']
    elif 'Imax' in params:
        return params['Imax']
    return 0

# ==================== API ENDPOINTS ДЛЯ НОВОЙ СТРУКТУРЫ ====================

@app.get("/api/components/by-tag/{tag}")
async def api_get_components_by_tag(
    tag: str,
    tag_type: Optional[str] = Query("application_tags", description="Тип тега: application_tags, technology_tags, role_tags"),
    limit: Optional[int] = Query(None, description="Ограничение количества результатов")
):
    """API: Поиск компонентов по тегам"""
    filtered = []
    
    for component in components:
        # Проверяем наличие нужного типа тегов
        if tag_type in component:
            tags = component[tag_type]
            if any(t.lower() == tag.lower() for t in tags):
                filtered.append(component)
    
    if limit and len(filtered) > limit:
        filtered = filtered[:limit]
    
    return {
        "count": len(filtered),
        "tag": tag,
        "tag_type": tag_type,
        "components": filtered
    }

@app.get("/api/components/search/extended")
async def api_search_extended(
    min_power: Optional[float] = Query(None, description="Минимальная мощность (Вт)"),
    max_power: Optional[float] = Query(None, description="Максимальная мощность (Вт)"),
    min_voltage: Optional[float] = Query(None, description="Минимальное напряжение (В)"),
    max_voltage: Optional[float] = Query(None, description="Максимальное напряжение (В)"),
    min_current: Optional[float] = Query(None, description="Минимальный ток (А)"),
    max_current: Optional[float] = Query(None, description="Максимальный ток (А)"),
    application: Optional[str] = Query(None, description="Область применения"),
    component_type: Optional[str] = Query(None, description="Тип компонента"),
    origin: Optional[str] = Query(None, description="Происхождение компонента"),
    limit: Optional[int] = Query(50, description="Ограничение количества результатов")
):
    """Расширенный поиск по параметрам"""
    filtered = []
    
    for component in components:
        # Проверяем соответствие базовым фильтрам
        if component_type and component.get('type') != component_type:
            continue
        if origin and component.get('origin') != origin:
            continue
        
        # Проверяем мощность
        power = get_power_value(component)
        if min_power is not None and power < min_power:
            continue
        if max_power is not None and power > max_power:
            continue
        
        # Проверяем напряжение
        voltage = get_voltage_value(component)
        if min_voltage is not None and voltage < min_voltage:
            continue
        if max_voltage is not None and voltage > max_voltage:
            continue
        
        # Проверяем ток
        current = get_current_value(component)
        if min_current is not None and current < min_current:
            continue
        if max_current is not None and current > max_current:
            continue
        
        # Проверяем тег применения
        if application:
            if not any(app.lower() == application.lower() for app in component.get('application_tags', [])):
                continue
        
        filtered.append(component)
        
        # Останавливаемся при достижении лимита
        if len(filtered) >= limit:
            break
    
    return {
        "count": len(filtered),
        "components": filtered
    }

@app.get("/api/statistics/tags")
async def api_get_tags_statistics(
    tag_type: Optional[str] = Query("application_tags", description="Тип тега для анализа")
):
    """API: Статистика по тегам"""
    tag_counts = defaultdict(int)
    
    for component in components:
        if tag_type in component:
            for tag in component[tag_type]:
                tag_counts[tag] += 1
    
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "tag_type": tag_type,
        "total_tags": len(tag_counts),
        "tags": dict(sorted_tags[:50])
    }

@app.get("/api/components/similar/{component_id}")
async def api_get_similar_components(
    component_id: str,
    max_results: Optional[int] = Query(5, description="Максимальное количество похожих компонентов")
):
    """API: Поиск похожих компонентов"""
    target_component = next((c for c in components if c['id'] == component_id), None)
    if not target_component:
        raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found")
    
    similar_components = []
    
    for component in components:
        if component['id'] == component_id:
            continue
        
        similarity_score = 0
        
        # Сравниваем тип
        if component.get('type') == target_component.get('type'):
            similarity_score += 3
        
        # Сравниваем происхождение
        if component.get('origin') == target_component.get('origin'):
            similarity_score += 1
        
        # Сравниваем теги
        for tag_type in ['application_tags', 'technology_tags', 'role_tags']:
            if tag_type in component and tag_type in target_component:
                common_tags = set(component[tag_type]) & set(target_component[tag_type])
                similarity_score += len(common_tags) * 0.5
        
        if similarity_score > 0:
            similar_components.append({
                "component": component,
                "similarity_score": round(similarity_score, 2)
            })
    
    similar_components.sort(key=lambda x: x["similarity_score"], reverse=True)
    similar_components = similar_components[:max_results]
    
    return {
        "target_component": component_id,
        "similar_count": len(similar_components),
        "similar_components": similar_components
    }

# ==================== КРИТИЧЕСКИЕ ENDPOINTS ДЛЯ ИИ ====================

@app.post("/api/ai-query")
async def api_process_ai_query(request: Request):
    """API: Обработка ИИ-запроса через brain.py (поиск компонентов)"""
    if not brain_available or not brain:
        logger.error("ИИ-модуль (brain.py) недоступен")
        return JSONResponse({
            "success": False,
            "error": "ИИ-модуль для поиска компонентов недоступен"
        }, status_code=503)
    
    try:
        data = await request.json()
        user_query = data.get("query", "")
        
        logger.info(f"🔍 ИИ-запрос получен (brain.py): '{user_query}'")
        
        if not user_query:
            logger.warning("Пустой ИИ-запрос")
            return JSONResponse({
                "success": False,
                "error": "Пустой запрос"
            }, status_code=400)
        
        # Используем asyncio.to_thread для вызова синхронного метода
        logger.info("⏳ Обработка запроса через brain.py...")
        result = await asyncio.to_thread(brain.process_query, user_query)
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
        logger.error(traceback.format_exc())
        return JSONResponse({
            "success": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }, status_code=500)

@app.post("/api/openrouter/chat")
async def proxy_openrouter_chat(request: Request):
    """
    Прокси-эндпоинт для запросов к OpenRouter API.
    Получает ключ пользователя из заголовка и перенаправляет запрос.
    """
    try:
        # 1. Получаем данные и API-ключ из запроса пользователя
        request_data = await request.json()
        user_api_key = request.headers.get("X-OpenRouter-API-Key")

        if not user_api_key:
            logger.warning("Попытка запроса без API-ключа")
            raise HTTPException(
                status_code=400,
                detail="API-ключ OpenRouter не предоставлен. Добавьте его в поле ввода на странице ИИ-поиска."
            )

        # 2. Подготавливаем запрос к OpenRouter
        openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # 2.1. Формируем заголовки, включая ключ ПОЛЬЗОВАТЕЛЯ
        headers = {
            "Authorization": f"Bearer {user_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": str(request.base_url),
            "X-Title": "Electronic Component Library"
        }

        # 2.2. Формируем тело запроса
        payload = {
            "model": request_data.get("model", "deepseek/deepseek-chat"),
            "messages": request_data.get("messages", []),
            "temperature": request_data.get("temperature", 0.1),
            "max_tokens": request_data.get("max_tokens", 1000)
        }

        # 3. Отправляем запрос к OpenRouter
        logger.info(f"Проксируем запрос к OpenRouter для модели {payload['model']}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                openrouter_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

        # 4. Возвращаем результат пользователя
        return JSONResponse(result)

    except httpx.HTTPStatusError as e:
        logger.error(f"Ошибка OpenRouter API: {e.response.status_code} - {e.response.text[:200]}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Ошибка OpenRouter: {e.response.text[:200]}"
        )
    except Exception as e:
        logger.error(f"Ошибка проксирования запроса: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

# ==================== ВЕБ-ИНТЕРФЕЙС ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница"""
    # Считаем статистику по типам
    type_counts = defaultdict(int)
    origin_counts = defaultdict(int)
    tag_counts = defaultdict(int)
    
    for comp in components:
        type_counts[comp.get('type', 'unknown')] += 1
        origin_counts[comp.get('origin', 'unknown')] += 1
        for tag in comp.get('application_tags', []):
            tag_counts[tag] += 1
    
    # Самые популярные теги
    popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Самые мощные компоненты
    powerful_components = sorted(
        components,
        key=lambda x: get_power_value(x),
        reverse=True
    )[:5]
    
    featured_components = components[:6]
    
    stats = {
        "total_components": len(components),
        "type_counts": dict(type_counts),
        "origin_counts": dict(origin_counts),
        "popular_tags": dict(popular_tags)
    }
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats,
        "powerful_components": powerful_components,
        "featured_components": featured_components,
        "brain_available": brain_available,
        "has_openrouter_proxy": True
    })

@app.get("/components", response_class=HTMLResponse)
async def components_page(
    request: Request,
    type: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    application_tag: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("id")
):
    """Страница поиска компонентов"""
    filtered = components.copy()
    
    if type:
        filtered = [c for c in filtered if c.get('type') == type]
    
    if origin:
        filtered = [c for c in filtered if c.get('origin', '').lower() == origin.lower()]
    
    if search_text:
        search_lower = search_text.lower()
        filtered = [
            c for c in filtered 
            if (search_lower in c.get('name', '').lower() 
            or search_lower in c.get('description', '').lower()
            or search_lower in c.get('id', '').lower()
            or any(search_lower in tag.lower() for tag in c.get('application_tags', [])))
        ]
    
    if application_tag:
        filtered = [c for c in filtered if 'application_tags' in c and application_tag in c['application_tags']]
    
    if sort_by:
        try:
            if sort_by == "power":
                filtered.sort(key=lambda x: get_power_value(x), reverse=True)
            elif sort_by == "voltage":
                filtered.sort(key=lambda x: get_voltage_value(x), reverse=True)
            elif sort_by == "current":
                filtered.sort(key=lambda x: get_current_value(x), reverse=True)
            elif sort_by == "id":
                filtered.sort(key=lambda x: x.get('id', ''))
            elif sort_by == "name":
                filtered.sort(key=lambda x: x.get('name', ''))
        except Exception as e:
            logger.warning(f"Ошибка сортировки: {e}")
    
    # Получаем уникальные типы, происхождения и теги для фильтров
    component_types = sorted(set(c.get('type') for c in components if c.get('type')))
    origins = sorted(set(c.get('origin') for c in components if c.get('origin')))
    
    # Собираем все теги применения
    all_application_tags = []
    for component in components:
        all_application_tags.extend(component.get('application_tags', []))
    common_application_tags = sorted(set(all_application_tags))[:15]
    
    return templates.TemplateResponse("search.html", {
        "request": request,
        "components": filtered,
        "count": len(filtered),
        "total_components": len(components),
        "component_types": component_types,
        "origins": origins,
        "common_application_tags": common_application_tags,
        "filters": {
            "type": type,
            "origin": origin,
            "search_text": search_text,
            "application_tag": application_tag,
            "sort_by": sort_by
        },
        "brain_available": brain_available,
        "has_openrouter_proxy": True
    })

@app.get("/component/{component_id}", response_class=HTMLResponse)
async def component_detail(request: Request, component_id: str):
    """Страница компонента"""
    component = next((c for c in components if c['id'] == component_id), None)
    
    if not component:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_code": 404,
            "error_title": "Компонент не найден",
            "error_message": f"Компонент '{component_id}' не найден в базе данных",
            "brain_available": brain_available,
            "has_openrouter_proxy": True
        })
    
    characteristics = None
    file_path = component.get('characteristics_file')
    
    if file_path and os.path.exists(file_path):
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
                        characteristics.append({"voltage": voltage, "current": current})
                    except ValueError:
                        continue
                        
        except Exception as e:
            logger.error(f"Ошибка чтения характеристик: {e}")
    
    return templates.TemplateResponse("component.html", {
        "request": request,
        "component": component,
        "characteristics": characteristics,
        "brain_available": brain_available,
        "has_openrouter_proxy": True
    })

# ==================== НОВЫЙ ENDPOINT: СТРАНИЦА ИИ-ЗАПРОСОВ ====================

@app.get("/ai-query", response_class=HTMLResponse)
async def ai_query_page(request: Request):
    """Страница ИИ-запросов"""
    # Правильный подсчет статистики для новой структуры
    stats = {
        "bjt_count": len([c for c in components if c.get('type') in ['bjt_npn', 'bjt_pnp']]),
        "mosfet_count": len([c for c in components if 'mosfet' in c.get('type', '').lower()]),
        "tube_count": len([c for c in components if 'vacuum_tube' in c.get('type', '').lower()]),
        "diode_count": len([c for c in components if 'diode' in c.get('type', '').lower()]),
        "transformer_count": len([c for c in components if 'transformer' in c.get('type', '').lower()]),
        "total_components": len(components)
    }
    
    return templates.TemplateResponse("ai_query.html", {
        "request": request,
        "brain_available": brain_available,
        "has_openrouter_proxy": True,
        "stats": stats
    })

# ==================== ЗАПУСК СЕРВЕРА ====================

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("🌐 Запуск веб-интерфейса AI Component Library")
    print("📡 API доступен на: http://localhost:8000/api")
    print("🌍 Веб-интерфейс: http://localhost:8000")
    print("📚 Документация API: http://localhost:8000/docs")
    print("🤖 Режим brain.py доступен:", brain_available)
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8000)