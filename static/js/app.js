// Основные функции веб-интерфейса

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Обработка формы фильтров (асинхронная загрузка)
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            // Показываем индикатор загрузки при отправке формы фильтров
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Поиск...';
                submitBtn.disabled = true;
                
                // Восстанавливаем кнопку через 2 секунды (на всякий случай)
                setTimeout(() => {
                    submitBtn.innerHTML = '<i class="fas fa-search"></i> Применить фильтры';
                    submitBtn.disabled = false;
                }, 2000);
            }
        });
    }
    
    // Обработка ИИ-запросов
    const aiQueryForm = document.getElementById('ai-query-form');
    if (aiQueryForm) {
        aiQueryForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const queryInput = document.getElementById('ai-query-input');
            const submitBtn = document.getElementById('ai-query-submit');
            const resultsDiv = document.getElementById('ai-results');
            const loadingDiv = document.getElementById('ai-loading');
            
            if (!queryInput.value.trim()) {
                showNotification('Пожалуйста, введите запрос', 'warning');
                return;
            }
            
            // Показываем индикатор загрузки
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Обработка...';
            submitBtn.disabled = true;
            if (loadingDiv) loadingDiv.style.display = 'block';
            resultsDiv.innerHTML = '';
            
            try {
                const response = await fetch('/api/ai-query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: queryInput.value
                    })
                });
                
                const data = await response.json();
                
                // Проверяем статус ответа
                if (!response.ok) {
                    throw new Error(data.error || `Ошибка сервера: ${response.status}`);
                }
                
                // Отображаем результаты
                displayAiResults(data);
                
                // Сохраняем историю запросов
                saveToHistory(queryInput.value, data);
                
            } catch (error) {
                console.error('Ошибка ИИ-запроса:', error);
                displayAiError(error);
            } finally {
                // Восстанавливаем кнопку
                submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Отправить';
                submitBtn.disabled = false;
                if (loadingDiv) loadingDiv.style.display = 'none';
            }
        });
    }
    
    // Автозаполнение ИИ-запроса из URL параметра
    const urlParams = new URLSearchParams(window.location.search);
    const componentParam = urlParams.get('component');
    if (componentParam && document.getElementById('ai-query-input')) {
        document.getElementById('ai-query-input').value = 
            `Расскажи о компоненте ${componentParam} и его характеристиках`;
    }
    
    // Загрузка истории запросов
    loadQueryHistory();
    
    // Инициализация кнопок "копировать ссылку"
    initCopyButtons();
});

// Функция для отображения результатов ИИ-запроса
function displayAiResults(data) {
    const resultsDiv = document.getElementById('ai-results');
    
    if (!data.success) {
        displayAiError(data.error || 'Неизвестная ошибка обработки запроса');
        return;
    }
    
    let html = `
        <div class="ai-response">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5><i class="fas fa-robot"></i> Результат запроса</h5>
                <button class="btn btn-sm btn-outline-secondary" onclick="copyQueryResult(this)">
                    <i class="fas fa-copy"></i> Копировать
                </button>
            </div>
            ${data.command?.explanation ? `<p class="text-muted mb-3"><small>${data.command.explanation}</small></p>` : ''}
            <hr>
    `;
    
    // Обрабатываем разные типы результатов
    if (data.result.components) {
        // Список компонентов
        const count = data.result.count || 0;
        html += `
            <div class="alert alert-info">
                <i class="fas fa-microchip"></i> Найдено компонентов: <strong>${count}</strong>
            </div>
        `;
        
        if (count > 0) {
            html += `<div class="row mt-3">`;
            
            data.result.components.slice(0, 6).forEach(component => {
                html += `
                    <div class="col-md-6 mb-3">
                        <div class="card h-100">
                            <div class="card-body">
                                <h6 class="card-title">${escapeHtml(component.id)}</h6>
                                <p class="card-text small">${escapeHtml(component.name)}</p>
                                <div class="mt-2">
                                    <span class="badge bg-secondary">${escapeHtml(component.type)}</span>
                                    ${component.origin ? `<span class="badge bg-info">${escapeHtml(component.origin.toUpperCase())}</span>` : ''}
                                </div>
                                <div class="mt-2">
                                    <small class="text-muted">
                                        I<sub>max</sub>: ${component.params?.Imax || 0}A<br>
                                        U<sub>ce</sub>: ${component.params?.Uce_max || 0}V<br>
                                        P<sub>tot</sub>: ${component.params?.Ptot || 0}W
                                    </small>
                                </div>
                            </div>
                            <div class="card-footer">
                                <a href="/component/${encodeURIComponent(component.id)}" class="btn btn-sm btn-outline-primary">
                                    <i class="fas fa-eye"></i> Подробнее
                                </a>
                                <button class="btn btn-sm btn-outline-info ms-1" onclick="askAboutComponent('${escapeHtml(component.id)}')">
                                    <i class="fas fa-robot"></i> Спросить ИИ
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `</div>`;
            
            if (count > 6) {
                html += `
                    <div class="mt-3 text-center">
                        <a href="/components" class="btn btn-outline-secondary">
                            Показать все ${count} компонентов
                        </a>
                    </div>
                `;
            }
        }
        
    } else if (data.result.characteristics) {
        // Характеристики компонента
        const componentId = data.result.component_id || 'Неизвестный';
        const points = data.result.characteristics || [];
        
        html += `
            <div class="alert alert-success">
                <i class="fas fa-chart-line"></i> Характеристики компонента <strong>${escapeHtml(componentId)}</strong>
            </div>
        `;
        
        if (points.length > 0) {
            html += `
                <h6>ВАХ (вольт-амперная характеристика):</h6>
                <div class="table-responsive">
                    <table class="table table-sm table-striped">
                        <thead class="table-dark">
                            <tr>
                                <th>Напряжение (V)</th>
                                <th>Ток (A)</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            points.slice(0, 15).forEach(point => {
                html += `
                    <tr>
                        <td>${point.voltage?.toFixed(3) || 'N/A'}</td>
                        <td>${point.current ? point.current.toExponential(3) : 'N/A'}</td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
            
            if (points.length > 15) {
                html += `<p class="text-muted">... и еще ${points.length - 15} точек</p>`;
            }
            
            html += `
                <div class="mt-3">
                    <a href="/component/${encodeURIComponent(componentId)}" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Перейти к графику ВАХ
                    </a>
                </div>
            `;
        } else {
            html += `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Нет данных о характеристиках
                </div>
            `;
        }
        
    } else if (data.result.id) {
        // Информация о компоненте
        const component = data.result;
        html += `
            <div class="card mb-3">
                <div class="card-header bg-primary text-white">
                    <i class="fas fa-info-circle"></i> Информация о компоненте
                </div>
                <div class="card-body">
                    <h5>${escapeHtml(component.id)} - ${escapeHtml(component.name)}</h5>
                    <p>${escapeHtml(component.description || '')}</p>
                    
                    <div class="row mt-3">
                        <div class="col-md-6">
                            <h6>Основные данные:</h6>
                            <ul class="list-unstyled">
                                <li><strong>Тип:</strong> <span class="badge bg-secondary">${escapeHtml(component.type)}</span></li>
                                ${component.origin ? `<li><strong>Происхождение:</strong> <span class="badge bg-info">${escapeHtml(component.origin.toUpperCase())}</span></li>` : ''}
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Параметры:</h6>
                            <ul class="list-unstyled">
                                ${component.params?.Imax ? `<li><strong>Макс. ток:</strong> ${component.params.Imax} A</li>` : ''}
                                ${component.params?.Uce_max ? `<li><strong>Макс. напряжение:</strong> ${component.params.Uce_max} V</li>` : ''}
                                ${component.params?.Ptot ? `<li><strong>Макс. мощность:</strong> ${component.params.Ptot} W</li>` : ''}
                            </ul>
                        </div>
                    </div>
                    
                    <div class="mt-3">
                        <a href="/component/${encodeURIComponent(component.id)}" class="btn btn-primary me-2">
                            <i class="fas fa-chart-line"></i> График ВАХ
                        </a>
                        <button class="btn btn-success" onclick="askAboutComponent('${escapeHtml(component.id)}')">
                            <i class="fas fa-robot"></i> Спросить ИИ о компоненте
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else {
        // Произвольный ответ от ИИ
        html += `
            <div class="alert alert-secondary">
                <pre class="mb-0">${escapeHtml(JSON.stringify(data.result, null, 2))}</pre>
            </div>
        `;
    }
    
    html += `</div>`;
    resultsDiv.innerHTML = html;
}

// Функция для обработки ошибок ИИ
function displayAiError(error) {
    const resultsDiv = document.getElementById('ai-results');
    
    let errorMessage = 'Неизвестная ошибка';
    let errorDetails = '';
    let errorType = 'danger';
    
    if (error && error.message) {
        errorMessage = error.message;
        errorDetails = error.stack || '';
    } else if (typeof error === 'string') {
        errorMessage = error;
    } else if (error && typeof error === 'object') {
        errorMessage = error.error || 'Ошибка обработки запроса';
        errorDetails = JSON.stringify(error, null, 2);
    }
    
    // Определяем тип ошибки по содержанию
    if (errorMessage.includes('недоступен') || errorMessage.includes('отключен')) {
        errorType = 'warning';
    } else if (errorMessage.includes('не найден') || errorMessage.includes('отсутствует')) {
        errorType = 'info';
    }
    
    let html = `
        <div class="alert alert-${errorType}">
            <div class="d-flex">
                <div class="me-3">
                    <i class="fas fa-exclamation-triangle fa-2x"></i>
                </div>
                <div>
                    <h5 class="alert-heading">Ошибка ИИ-обработки</h5>
                    <p class="mb-2">${escapeHtml(errorMessage)}</p>
                    <hr>
                    
                    <div class="small">
                        <strong>Возможные причины:</strong>
                        <ul class="mb-2">
                            <li>API ключ не указан или неверный</li>
                            <li>Сервер ИИ недоступен (OpenRouter/DeepSeek)</li>
                            <li>Проблема с интернет-соединением</li>
                            <li>Некорректный формат запроса</li>
                            <li>Лимит запросов к API исчерпан</li>
                        </ul>
                        
                        <strong>Что можно сделать:</strong>
                        <ol class="mb-0">
                            <li>Проверьте наличие файла .env с API ключом</li>
                            <li>Убедитесь, что сервер запущен (<a href="http://localhost:8000">localhost:8000</a>)</li>
                            <li>Попробуйте более простой запрос</li>
                            <li>Используйте обычный поиск через <a href="/components">фильтры</a></li>
                        </ol>
                    </div>
    `;
    
    if (errorDetails && errorDetails.length < 1000) {
        html += `
            <div class="mt-3">
                <details>
                    <summary class="btn btn-sm btn-outline-${errorType}">
                        <i class="fas fa-code"></i> Технические детали
                    </summary>
                    <div class="mt-2">
                        <pre class="bg-dark text-light p-2 rounded small"><code>${escapeHtml(errorDetails)}</code></pre>
                    </div>
                </details>
            </div>
        `;
    }
    
    html += `
                </div>
            </div>
        </div>
        
        <div class="text-center mt-3">
            <a href="/components" class="btn btn-outline-primary me-2">
                <i class="fas fa-search"></i> Поиск компонентов
            </a>
            <a href="/" class="btn btn-outline-secondary">
                <i class="fas fa-home"></i> На главную
            </a>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
    
    // Показываем уведомление
    showNotification('Ошибка при обработке ИИ-запроса', errorType);
}

// Функция для копирования API ссылок
function copyApiLink(url) {
    navigator.clipboard.writeText(url).then(() => {
        showNotification('Ссылка скопирована в буфер обмена!', 'success');
    }).catch(err => {
        showNotification('Ошибка копирования: ' + err.message, 'danger');
    });
}

// Функция для копирования результата запроса
function copyQueryResult(button) {
    const resultDiv = button.closest('.ai-response');
    if (!resultDiv) return;
    
    const textToCopy = resultDiv.innerText;
    navigator.clipboard.writeText(textToCopy).then(() => {
        showNotification('Результат скопирован в буфер обмена!', 'success');
    }).catch(err => {
        showNotification('Ошибка копирования: ' + err.message, 'danger');
    });
}

// Функция для запроса ИИ о конкретном компоненте
function askAboutComponent(componentId) {
    const input = document.getElementById('ai-query-input');
    if (input) {
        input.value = `Расскажи подробно о компоненте ${componentId}, его параметрах и применении`;
        input.focus();
        
        // Автоматически отправляем запрос через 500мс
        setTimeout(() => {
            const submitBtn = document.getElementById('ai-query-submit');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.click();
            }
        }, 500);
    } else {
        // Если страница с ИИ-запросами не открыта, переходим на нее
        window.location.href = `/ai-query?component=${encodeURIComponent(componentId)}`;
    }
}

// Функция для показа уведомлений
function showNotification(message, type = 'info') {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : type === 'danger' ? 'times-circle' : 'info-circle'} me-2"></i>
        ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Добавляем уведомление в body
    document.body.appendChild(notification);
    
    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => notification.parentNode.removeChild(notification), 300);
        }
    }, 5000);
}

// Функция для сохранения запроса в истории
function saveToHistory(query, result) {
    try {
        const history = JSON.parse(localStorage.getItem('ai_query_history') || '[]');
        
        history.unshift({
            query: query,
            timestamp: new Date().toISOString(),
            success: result.success,
            resultCount: result.result?.count || 0
        });
        
        // Сохраняем только последние 20 запросов
        if (history.length > 20) {
            history.length = 20;
        }
        
        localStorage.setItem('ai_query_history', JSON.stringify(history));
    } catch (e) {
        console.warn('Не удалось сохранить историю запросов:', e);
    }
}

// Функция для загрузки истории запросов
function loadQueryHistory() {
    try {
        const history = JSON.parse(localStorage.getItem('ai_query_history') || '[]');
        const historyElement = document.getElementById('query-history');
        
        if (historyElement && history.length > 0) {
            let html = '<h6>История запросов:</h6><ul class="list-group small">';
            
            history.slice(0, 5).forEach((item, index) => {
                const date = new Date(item.timestamp);
                const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const dateStr = date.toLocaleDateString();
                
                html += `
                    <li class="list-group-item list-group-item-action" onclick="loadHistoryQuery(${index})">
                        <div class="d-flex justify-content-between">
                            <span class="text-truncate" style="max-width: 250px;">${escapeHtml(item.query)}</span>
                            <span class="badge bg-${item.success ? 'success' : 'danger'}">${item.resultCount || 0}</span>
                        </div>
                        <small class="text-muted">${dateStr} ${timeStr}</small>
                    </li>
                `;
            });
            
            html += '</ul>';
            historyElement.innerHTML = html;
        }
    } catch (e) {
        console.warn('Не удалось загрузить историю запросов:', e);
    }
}

// Функция для загрузки запроса из истории
function loadHistoryQuery(index) {
    try {
        const history = JSON.parse(localStorage.getItem('ai_query_history') || '[]');
        if (history[index]) {
            const input = document.getElementById('ai-query-input');
            if (input) {
                input.value = history[index].query;
                input.focus();
                showNotification('Запрос загружен из истории', 'info');
            }
        }
    } catch (e) {
        console.warn('Не удалось загрузить запрос из истории:', e);
    }
}

// Функция для экранирования HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Функция для инициализации кнопок копирования
function initCopyButtons() {
    // Находим все кнопки копирования API ссылок
    document.querySelectorAll('[data-copy-url]').forEach(button => {
        button.addEventListener('click', function() {
            const url = this.getAttribute('data-copy-url');
            if (url) {
                copyApiLink(url);
            }
        });
    });
}

// Экспортируем функции для глобального использования
window.copyApiLink = copyApiLink;
window.displayAiResults = displayAiResults;
window.displayAiError = displayAiError;
window.askAboutComponent = askAboutComponent;
window.copyQueryResult = copyQueryResult;
window.loadHistoryQuery = loadHistoryQuery;
window.showNotification = showNotification;