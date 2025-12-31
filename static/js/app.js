// Основные функции веб-интерфейса библиотеки компонентов

// Функция для экранирования HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Функция для показа уведомлений
function showNotification(message, type = 'info') {
    let notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notification-container';
        notificationContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            width: 300px;
        `;
        document.body.appendChild(notificationContainer);
    }

    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.style.cssText = `
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease-out;
    `;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'warning' ? 'exclamation-triangle' : 
                 type === 'danger' ? 'times-circle' : 'info-circle';
    
    notification.innerHTML = `
        <i class="fas fa-${icon} me-2"></i>
        ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    notificationContainer.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => notification.parentNode.removeChild(notification), 300);
        }
    }, 5000);
}

// Управление API-ключом OpenRouter пользователя
const ApiKeyManager = {
    saveKey: function() {
        const apiKeyInput = document.getElementById('openrouter-api-key');
        const key = apiKeyInput?.value?.trim();
        
        if (!key) {
            showNotification('⚠️ Введите API-ключ', 'warning');
            return false;
        }

        if (!key.startsWith('sk-or-')) {
            showNotification('❌ Неверный формат ключа. Ключ OpenRouter начинается с "sk-or-"', 'danger');
            return false;
        }

        localStorage.setItem('user_openrouter_api_key', key);
        
        const maskedKey = key.substring(0, 12) + '...' + key.substring(key.length - 4);
        
        this.updateKeyStatus(`✅ Ключ сохранен (${maskedKey})`, 'success');
        
        if (apiKeyInput) {
            apiKeyInput.type = 'password';
        }
        
        showNotification('API-ключ сохранен в вашем браузере', 'success');
        
        // Обновляем статус системы
        AiStatusManager.updateStatus();
        
        return true;
    },
    
    loadKey: function() {
        const savedKey = localStorage.getItem('user_openrouter_api_key');
        const apiKeyInput = document.getElementById('openrouter-api-key');
        
        if (savedKey && apiKeyInput) {
            apiKeyInput.value = savedKey;
            const maskedKey = savedKey.substring(0, 12) + '...' + savedKey.substring(savedKey.length - 4);
            this.updateKeyStatus(`🔑 Используется сохраненный ключ (${maskedKey})`, 'info');
            return savedKey;
        }
        return null;
    },
    
    getKey: function() {
        return localStorage.getItem('user_openrouter_api_key');
    },
    
    hasKey: function() {
        return !!this.getKey();
    },
    
    updateKeyStatus: function(message, type = 'info') {
        const statusDiv = document.getElementById('key-status');
        if (statusDiv) {
            statusDiv.className = `alert alert-${type}`;
            statusDiv.innerHTML = `<i class="fas fa-info-circle"></i> ${escapeHtml(message)}`;
            statusDiv.style.display = 'block';
        }
    },
    
    clearKey: function() {
        localStorage.removeItem('user_openrouter_api_key');
        const apiKeyInput = document.getElementById('openrouter-api-key');
        if (apiKeyInput) {
            apiKeyInput.value = '';
            apiKeyInput.type = 'text';
        }
        this.updateKeyStatus('Ключ удален. Введите новый ключ для использования ИИ.', 'warning');
        showNotification('API-ключ удален', 'info');
        
        // Обновляем статус системы
        AiStatusManager.updateStatus();
    }
};

// Менеджер статуса ИИ системы
const AiStatusManager = {
    updateStatus: function() {
        // Получаем информацию о доступности brain.py из data-атрибута body
        const hasBrain = document.body.dataset.brainAvailable === 'true';
        const hasKey = ApiKeyManager.hasKey();
        
        let status = "unknown";
        let badgeClass = "bg-secondary";
        let message = "";
        
        if (hasBrain && hasKey) {
            status = "full";
            badgeClass = "bg-success";
            message = "Полный доступ к ИИ (поиск + чат)";
        } else if (hasBrain && !hasKey) {
            status = "local_only";
            badgeClass = "bg-warning";
            message = "Только локальный поиск (без чата с ИИ)";
        } else if (!hasBrain && hasKey) {
            status = "chat_only";
            badgeClass = "bg-info";
            message = "Только чат с ИИ (без интеллектуального поиска компонентов)";
        } else {
            status = "none";
            badgeClass = "bg-danger";
            message = "ИИ недоступен. Используйте ручной поиск.";
        }
        
        // Обновляем индикатор в шапке
        this.updateHeaderIndicator(status, badgeClass, message);
        
        // Обновляем панель статуса на странице ai-query
        this.updateStatusPanel(hasBrain, hasKey, status, message);
        
        return { status, message, hasBrain, hasKey };
    },
    
    updateHeaderIndicator: function(status, badgeClass, message) {
        // Находим или создаем индикатор в шапке
        let indicator = document.getElementById('ai-status-indicator');
        
        if (!indicator) {
            // Если индикатора нет в DOM, ищем место для вставки
            const navbarBrand = document.querySelector('.navbar-brand');
            if (navbarBrand && navbarBrand.parentNode) {
                indicator = document.createElement('div');
                indicator.id = 'ai-status-indicator';
                indicator.style.cssText = 'display: inline-block; margin-left: 10px;';
                navbarBrand.parentNode.insertBefore(indicator, navbarBrand.nextSibling);
            }
        }
        
        if (indicator) {
            const statusText = {
                "full": "ИИ: Полный",
                "local_only": "ИИ: Локальный",
                "chat_only": "ИИ: Чат",
                "none": "ИИ: Выкл",
                "unknown": "ИИ: ?"
            };
            
            indicator.innerHTML = `
                <span class="badge ${badgeClass}" title="${escapeHtml(message)}" style="cursor: help;">
                    <i class="fas fa-robot"></i> ${statusText[status] || status}
                </span>
            `;
        }
    },
    
    updateStatusPanel: function(hasBrain, hasKey, status, message) {
        const statusPanel = document.getElementById('ai-system-status-panel');
        if (!statusPanel) return;
        
        // Обновляем иконки статусов
        const brainStatus = document.getElementById('brain-status');
        if (brainStatus) {
            brainStatus.className = hasBrain ? 'badge bg-success' : 'badge bg-danger';
            brainStatus.textContent = hasBrain ? 'Доступен' : 'Недоступен';
        }
        
        const keyStatus = document.getElementById('api-key-status');
        if (keyStatus) {
            if (hasKey) {
                keyStatus.className = 'badge bg-success';
                keyStatus.textContent = 'Сохранён';
            } else {
                keyStatus.className = 'badge bg-warning';
                keyStatus.textContent = 'Отсутствует';
            }
        }
        
        const modeStatus = document.getElementById('ai-mode-status');
        if (modeStatus) {
            modeStatus.className = `badge bg-${status === 'full' ? 'success' : 
                                   status === 'local_only' ? 'warning' : 
                                   status === 'chat_only' ? 'info' : 'danger'}`;
            modeStatus.textContent = {
                "full": "Полный",
                "local_only": "Локальный поиск",
                "chat_only": "Только чат",
                "none": "Отключен"
            }[status] || "Неизвестно";
        }
    },
    
    checkApiKeyValidity: async function(apiKey) {
        if (!apiKey) {
            return { valid: false, error: "Нет ключа для проверки" };
        }
        
        try {
            // Простой тестовый запрос к OpenRouter для проверки ключа
            const response = await fetch('https://openrouter.ai/api/v1/auth/key', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${apiKey}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                return { 
                    valid: true, 
                    data: data,
                    model: data.data?.model || "deepseek/deepseek-chat"
                };
            } else {
                return { 
                    valid: false, 
                    error: `Ключ недействителен (код: ${response.status})` 
                };
            }
        } catch (error) {
            return { 
                valid: false, 
                error: "Ошибка проверки ключа: " + error.message 
            };
        }
    }
};

// Функция для анализа типа запроса
function analyzeQueryType(userQuestion) {
    const question = userQuestion.toLowerCase();
    
    // Ключевые слова для поиска компонентов
    const searchKeywords = [
        'найди', 'поиск', 'покажи', 'какие', 'характеристики', 'вах', 'график',
        'параметры', 'компонент', 'транзистор', 'диод', 'лампа', 'микросхема',
        'мощность', 'ток', 'напряжение', 'параметр', 'сопротивление',
        'емкость', 'индуктивность', 'фильтр', 'усилитель', 'генератор',
        'преобразователь', 'подбери', 'выбери', 'сравни', 'аналоги',
        'советский', 'импортный', 'зарубежный', 'отечественный',
        'максимальный', 'минимальный', 'номинальный', 'типовой',
        'вольт-амперная', 'вольтамперная', 'вольт амперная'
    ];
    
    // Ключевые слова для общих вопросов
    const chatKeywords = [
        'объясни', 'расскажи', 'как работает', 'что такое', 'почему',
        'зачем', 'чем отличается', 'в чем разница', 'какой принцип',
        'какова схема', 'как подключить', 'как рассчитать',
        'теория', 'принцип', 'работа', 'устройство', 'конструкция',
        'применение', 'использование', 'пример', 'схема', 'схемотехника'
    ];
    
    // Проверяем наличие ключевых слов
    const hasSearchKeywords = searchKeywords.some(keyword => question.includes(keyword));
    const hasChatKeywords = chatKeywords.some(keyword => question.includes(keyword));
    
    // Если есть ключевые слова для поиска, но нет для чата - это поиск
    if (hasSearchKeywords && !hasChatKeywords) {
        return 'search';
    }
    
    // Если есть ключевые слова для чата, но нет для поиска - это чат
    if (hasChatKeywords && !hasSearchKeywords) {
        return 'chat';
    }
    
    // Если есть оба типа ключевых слов или ни одного - используем эвристику
    // По умолчанию считаем, что если запрос короткий (менее 20 символов) - это поиск
    // Если длинный и содержит вопросительные слова - это чат
    if (question.length < 20) {
        return 'search';
    }
    
    // Проверяем наличие конкретных идентификаторов компонентов
    const componentPatterns = [
        /2n\d+/i, /kt\d+/i, /bc\d+/i, /irf\d+/i, /tip\d+/i,
        /6п\d+/i, /6п1п/i, /6ж4п/i, /г\d+/i, /д\d+/i
    ];
    
    if (componentPatterns.some(pattern => pattern.test(question))) {
        return 'search';
    }
    
    // По умолчанию - чат
    return 'chat';
}

// Функция для отправки запроса к OpenRouter через прокси
async function sendOpenRouterQuery(userQuestion) {
    const userApiKey = ApiKeyManager.getKey();
    
    if (!userApiKey) {
        showNotification('❌ Для режима чата с ИИ необходим API-ключ OpenRouter.', 'danger');
        return { success: false, error: 'API ключ не указан', mode: 'no_key' };
    }

    // Создаем системный промпт для ИИ
    const messages = [
        {
            "role": "system",
            "content": `Ты — ассистент для библиотеки электронных компонентов. 
                        Библиотека содержит следующие типы компонентов: биполярные транзисторы (bjt), 
                        полевые транзисторы (mosfet), электронные лампы (vacuum_tube), диоды (diode).
                        
                        Пользователи могут искать компоненты по параметрам:
                        - Imax (максимальный ток, А)
                        - Uce_max (максимальное напряжение, В)
                        - Ptot (максимальная мощность, Вт)
                        - origin (происхождение: soviet, usa, other)
                        - type (тип компонента)
                        
                        Также система может отображать ВАХ (вольт-амперные характеристики) компонентов
                        в виде графиков и таблиц.
                        
                        Отвечай на вопросы о компонентах, их параметрах и применении.
                        Если запрос подразумевает поиск компонентов, предложи пользователю использовать 
                        систему фильтров на странице поиска.`
        },
        {
            "role": "user",
            "content": userQuestion
        }
    ];

    try {
        const response = await fetch('/api/openrouter/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-OpenRouter-API-Key': userApiKey
            },
            body: JSON.stringify({
                model: 'deepseek/deepseek-chat',
                messages: messages,
                temperature: 0.1,
                max_tokens: 1000
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            let errorMessage = `Ошибка API: ${response.status}`;
            try {
                const errorData = JSON.parse(errorText);
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                errorMessage = errorText.substring(0, 200);
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        return {
            success: true,
            response: data.choices?.[0]?.message?.content || 'Нет ответа от ИИ',
            mode: 'openrouter_chat'
        };

    } catch (error) {
        console.error('Ошибка при запросе к OpenRouter:', error);
        return {
            success: false,
            error: error.message,
            mode: 'openrouter_error'
        };
    }
}

// Функция для отправки запроса к brain.py (поиск компонентов)
async function sendBrainQuery(userQuestion) {
    const userApiKey = ApiKeyManager.getKey();  // 🔑 Берем ключ из localStorage
    
    try {
        const response = await fetch('/api/ai-query', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify({ 
                query: userQuestion,
                api_key: userApiKey  // 🔑 Передаем ключ на сервер
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Ошибка brain.py запроса:', error);
        return { 
            success: false, 
            error: error.message,
            mode: "brain_error"
        };
    }
}

// Основная функция отправки ИИ-запроса (автоматически выбирает нужный эндпоинт)
async function sendAiQuery(userQuestion) {
    const queryType = analyzeQueryType(userQuestion);
    console.log(`Определен тип запроса: ${queryType}`);
    
    if (queryType === 'chat') {
        return await sendOpenRouterQuery(userQuestion);
    } else {
        return await sendBrainQuery(userQuestion);
    }
}

// Функция для отображения ответа от OpenRouter
function displayOpenRouterResponse(question, result) {
    const resultsDiv = document.getElementById('ai-results');
    
    if (!result.success) {
        displayAiError(result.error);
        return;
    }
    
    const html = `
        <div class="ai-response">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5><i class="fas fa-robot text-success"></i> Ответ ИИ (общий вопрос)</h5>
                <div>
                    <span class="badge bg-success">Режим: Чат с ИИ</span>
                    <button class="btn btn-sm btn-outline-secondary ms-2" onclick="copyAiResponse(this)">
                        <i class="fas fa-copy"></i> Копировать
                    </button>
                </div>
            </div>
            
            <div class="card mb-3">
                <div class="card-header bg-light">
                    <strong><i class="fas fa-question-circle"></i> Ваш вопрос:</strong>
                </div>
                <div class="card-body">
                    <p class="mb-0">${escapeHtml(question)}</p>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header bg-success text-white">
                    <strong><i class="fas fa-comment-dots"></i> Ответ:</strong>
                </div>
                <div class="card-body">
                    <div class="ai-response-content">
                        ${formatAiResponse(result.response)}
                    </div>
                </div>
            </div>
            
            <div class="mt-3 text-center">
                <button class="btn btn-outline-primary me-2" onclick="useResponseAsQuery('${escapeHtml(question)}')">
                    <i class="fas fa-redo"></i> Задать уточняющий вопрос
                </button>
                <a href="/components" class="btn btn-outline-success">
                    <i class="fas fa-search"></i> Перейти к поиску компонентов
                </a>
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
}

// Функция для создания графика ВАХ с использованием Chart.js
function createVahChart(points, canvasId = 'vahChart') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    
    const ctx = canvas.getContext('2d');
    
    // Подготовка данных
    const voltages = points.map(p => p.voltage);
    const currents = points.map(p => p.current);
    
    // Уничтожаем предыдущий график, если есть
    if (window.currentChart) {
        window.currentChart.destroy();
    }
    
    // Создаем новый график
    window.currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: voltages,
            datasets: [{
                label: 'Ток, А',
                data: currents,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'ВАХ (Вольт-Амперная Характеристика)'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Напряжение: ${context.label} В, Ток: ${context.parsed.y.toExponential(3)} А`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Напряжение, В'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Ток, А'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    type: 'logarithmic',
                    min: Math.max(1e-12, Math.min(...currents.filter(c => c > 0)) * 0.1),
                    max: Math.max(...currents) * 10
                }
            }
        }
    });
    
    return window.currentChart;
}

// Функция для отображения результатов brain.py (поиск компонентов)
function displayBrainResponse(question, result) {
    const resultsDiv = document.getElementById('ai-results');
    
    if (!result.success) {
        displayAiError(result.error);
        return;
    }
    
    const mode = result.mode || 'unknown';
    const modeBadge = mode === 'openrouter' ? '<span class="badge bg-success">Режим: ИИ-поиск</span>' :
                     mode === 'local_parser' ? '<span class="badge bg-warning">Режим: Локальный поиск</span>' :
                     '<span class="badge bg-secondary">Режим: Поиск</span>';
    
    let html = `
        <div class="ai-response">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5><i class="fas fa-search text-info"></i> Результат поиска компонентов</h5>
                <div>
                    ${modeBadge}
                    <button class="btn btn-sm btn-outline-secondary ms-2" onclick="copyQueryResult(this)">
                        <i class="fas fa-copy"></i> Копировать
                    </button>
                </div>
            </div>
            
            ${result.command?.explanation ? `<div class="alert alert-info mb-3"><i class="fas fa-info-circle"></i> ${escapeHtml(result.command.explanation)}</div>` : ''}
            
            <div class="card mb-3">
                <div class="card-header bg-light">
                    <strong><i class="fas fa-question-circle"></i> Ваш запрос:</strong>
                </div>
                <div class="card-body">
                    <p class="mb-0">${escapeHtml(question)}</p>
                </div>
            </div>
    `;
    
    if (result.result?.components) {
        const count = result.result.count || 0;
        html += `
            <div class="alert alert-info">
                <i class="fas fa-microchip"></i> Найдено компонентов: <strong>${count}</strong>
                ${mode === 'local_parser' ? '<br><small class="text-muted">(используется локальный поиск по ключевым словам)</small>' : ''}
            </div>
        `;
        
        if (count > 0) {
            html += `<div class="row mt-3">`;
            
            result.result.components.slice(0, 8).forEach(component => {
                html += `
                    <div class="col-md-6 col-lg-4 mb-3">
                        <div class="card h-100">
                            <div class="card-body">
                                <h6 class="card-title">${escapeHtml(component.id)}</h6>
                                <p class="card-text small text-muted">${escapeHtml(component.name)}</p>
                                <div class="mt-2">
                                    <span class="badge bg-secondary">${escapeHtml(component.type)}</span>
                                    ${component.origin ? `<span class="badge bg-info ms-1">${escapeHtml(component.origin.toUpperCase())}</span>` : ''}
                                </div>
                                <div class="mt-2">
                                    <small>
                                        <strong>Параметры:</strong><br>
                                        I<sub>max</sub>: ${component.params?.Imax || 0} А<br>
                                        U<sub>ce</sub>: ${component.params?.Uce_max || 0} В<br>
                                        P<sub>tot</sub>: ${component.params?.Ptot || 0} Вт
                                    </small>
                                </div>
                            </div>
                            <div class="card-footer">
                                <div class="d-flex justify-content-between">
                                    <a href="/component/${encodeURIComponent(component.id)}" class="btn btn-sm btn-outline-primary">
                                        <i class="fas fa-eye"></i> Подробнее
                                    </a>
                                    <button class="btn btn-sm btn-outline-success ms-1" onclick="showComponentVah('${escapeHtml(component.id)}')">
                                        <i class="fas fa-chart-line"></i> ВАХ
                                    </button>
                                    <button class="btn btn-sm btn-outline-info ms-1" onclick="askAboutComponent('${escapeHtml(component.id)}')">
                                        <i class="fas fa-robot"></i> Спросить
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `</div>`;
            
            if (count > 8) {
                html += `
                    <div class="mt-3 text-center">
                        <a href="/components" class="btn btn-outline-secondary">
                            <i class="fas fa-external-link-alt"></i> Показать все ${count} компонентов
                        </a>
                    </div>
                `;
            }
        }
    } else if (result.result?.characteristics) {
        const componentId = result.result.component_id || 'Неизвестный';
        const points = result.result.characteristics || [];
        
        html += `
            <div class="alert alert-success">
                <div class="d-flex align-items-center">
                    <div class="me-3">
                        <i class="fas fa-chart-line fa-2x"></i>
                    </div>
                    <div>
                        <h5 class="mb-0">ВАХ компонента <strong>${escapeHtml(componentId)}</strong></h5>
                        <p class="mb-0">Количество точек данных: ${points.length}</p>
                    </div>
                </div>
            </div>
        `;
        
        if (points.length > 0) {
            // Добавляем canvas для графика
            html += `
                <div class="card mb-3">
                    <div class="card-header bg-dark text-white">
                        <i class="fas fa-chart-area"></i> Графическое представление ВАХ
                    </div>
                    <div class="card-body">
                        <div class="chart-container" style="position: relative; height:400px; width:100%">
                            <canvas id="vahChart"></canvas>
                        </div>
                    </div>
                </div>
            `;
            
            html += `
                <div class="card">
                    <div class="card-header bg-secondary text-white">
                        <i class="fas fa-table"></i> Таблица данных ВАХ
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm table-striped">
                                <thead class="table-dark">
                                    <tr>
                                        <th>#</th>
                                        <th>Напряжение (V)</th>
                                        <th>Ток (A)</th>
                                        <th>Ток (мА)</th>
                                        <th>Ток (мкА)</th>
                                    </tr>
                                </thead>
                                <tbody>
            `;
            
            points.slice(0, 20).forEach((point, index) => {
                html += `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${point.voltage?.toFixed(3) || '0.000'}</td>
                        <td>${point.current ? point.current.toExponential(3) : '0.000e+0'}</td>
                        <td>${point.current ? (point.current * 1000).toExponential(3) : '0.000e+0'}</td>
                        <td>${point.current ? (point.current * 1000000).toExponential(3) : '0.000e+0'}</td>
                    </tr>
                `;
            });
            
            html += `
                                </tbody>
                            </table>
                        </div>
            `;
            
            if (points.length > 20) {
                html += `<p class="text-muted mt-2">... и еще ${points.length - 20} точек данных</p>`;
            }
            
            html += `
                    </div>
                </div>
            `;
        }
    } else {
        html += `
            <div class="alert alert-secondary">
                <i class="fas fa-database"></i> <strong>Результат:</strong>
                <pre class="mt-2 mb-0">${escapeHtml(JSON.stringify(result.result, null, 2))}</pre>
            </div>
        `;
    }
    
    html += `</div>`;
    resultsDiv.innerHTML = html;
    
    // Если есть характеристики, создаем график
    if (result.result?.characteristics && result.result.characteristics.length > 0) {
        // Даем время на отрисовку DOM
        setTimeout(() => {
            createVahChart(result.result.characteristics);
        }, 100);
    }
}

// Форматирование ответа ИИ (простая поддержка Markdown)
function formatAiResponse(text) {
    let formatted = escapeHtml(text);
    
    // Заменяем Markdown на HTML
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/`([^`]+)`/g, '<code class="bg-light p-1 rounded">$1</code>');
    
    // Обработка списков
    formatted = formatted.replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul class="mb-2">$1</ul>');
    
    // Обработка заголовков
    formatted = formatted.replace(/^###\s+(.+)$/gm, '<h5 class="mt-3">$1</h5>');
    formatted = formatted.replace(/^##\s+(.+)$/gm, '<h4 class="mt-3">$1</h4>');
    formatted = formatted.replace(/^#\s+(.+)$/gm, '<h3 class="mt-3">$1</h3>');
    
    // Обработка параграфов и переносов строк
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    formatted = formatted.replace(/\n/g, '<br>');
    
    return `<p>${formatted}</p>`;
}

// Функция для показа ВАХ компонента
async function showComponentVah(componentId) {
    try {
        showNotification(`Загрузка характеристик компонента ${componentId}...`, 'info');
        
        const response = await fetch(`/api/components/${encodeURIComponent(componentId)}/characteristics`);
        
        if (!response.ok) {
            throw new Error(`Ошибка загрузки характеристик: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Отображаем характеристики
        const resultsDiv = document.getElementById('ai-results');
        const html = `
            <div class="ai-response">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5><i class="fas fa-chart-line text-success"></i> ВАХ компонента ${escapeHtml(componentId)}</h5>
                    <div>
                        <button class="btn btn-sm btn-outline-secondary" onclick="window.history.back()">
                            <i class="fas fa-arrow-left"></i> Назад
                        </button>
                    </div>
                </div>
                
                <div class="alert alert-success">
                    <div class="d-flex align-items-center">
                        <div class="me-3">
                            <i class="fas fa-chart-line fa-2x"></i>
                        </div>
                        <div>
                            <h5 class="mb-0">ВАХ компонента <strong>${escapeHtml(componentId)}</strong></h5>
                            <p class="mb-0">Количество точек данных: ${data.characteristics.length}</p>
                        </div>
                    </div>
                </div>
                
                <div class="card mb-3">
                    <div class="card-header bg-dark text-white">
                        <i class="fas fa-chart-area"></i> Графическое представление ВАХ
                    </div>
                    <div class="card-body">
                        <div class="chart-container" style="position: relative; height:400px; width:100%">
                            <canvas id="vahChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header bg-secondary text-white">
                        <i class="fas fa-table"></i> Таблица данных ВАХ
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm table-striped">
                                <thead class="table-dark">
                                    <tr>
                                        <th>#</th>
                                        <th>Напряжение (V)</th>
                                        <th>Ток (A)</th>
                                        <th>Ток (мА)</th>
                                    </tr>
                                </thead>
                                <tbody>
        `;
        
        data.characteristics.slice(0, 15).forEach((point, index) => {
            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${point.voltage?.toFixed(3) || '0.000'}</td>
                    <td>${point.current ? point.current.toExponential(3) : '0.000e+0'}</td>
                    <td>${point.current ? (point.current * 1000).toFixed(3) : '0.000'}</td>
                </tr>
            `;
        });
        
        html += `
                                </tbody>
                            </table>
                        </div>
        `;
        
        if (data.characteristics.length > 15) {
            html += `<p class="text-muted mt-2">... и еще ${data.characteristics.length - 15} точек данных</p>`;
        }
        
        html += `
                    </div>
                </div>
            </div>
        `;
        
        resultsDiv.innerHTML = html;
        
        // Создаем график
        setTimeout(() => {
            createVahChart(data.characteristics);
        }, 100);
        
    } catch (error) {
        console.error('Ошибка при загрузке ВАХ:', error);
        showNotification(`Ошибка загрузки характеристик: ${error.message}`, 'danger');
    }
}

// Функция для копирования ответа ИИ
function copyAiResponse(button) {
    const responseContent = button.closest('.ai-response')?.querySelector('.ai-response-content');
    if (responseContent) {
        const textToCopy = responseContent.textContent || responseContent.innerText;
        navigator.clipboard.writeText(textToCopy).then(() => {
            showNotification('Ответ ИИ скопирован в буфер обмена!', 'success');
        });
    }
}

// Функция для копирования результатов поиска
function copyQueryResult(button) {
    const responseContent = button.closest('.ai-response')?.querySelector('.alert-secondary pre') ||
                           button.closest('.ai-response');
    if (responseContent) {
        const textToCopy = responseContent.textContent || responseContent.innerText;
        navigator.clipboard.writeText(textToCopy.substring(0, 5000)).then(() => {
            showNotification('Результаты скопированы в буфер обмена!', 'success');
        });
    }
}

// Использовать ответ как новый запрос
function useResponseAsQuery(originalQuery) {
    const input = document.getElementById('ai-query-input');
    if (input) {
        input.value = `Уточняющий вопрос по теме: ${originalQuery}`;
        input.focus();
        showNotification('Готово для уточняющего вопроса', 'info');
    }
}

// Функция для запроса ИИ о конкретном компоненте
function askAboutComponent(componentId) {
    const input = document.getElementById('ai-query-input');
    if (input) {
        input.value = `Расскажи подробно о компоненте ${componentId}, его параметрах, характеристиках и типичном применении в электронных схемах`;
        input.focus();
        showNotification('Запрос подготовлен. Нажмите "Отправить" для получения ответа.', 'info');
    }
}

// Функция для обработки ошибок ИИ
function displayAiError(error) {
    const resultsDiv = document.getElementById('ai-results');
    
    let errorMessage = 'Неизвестная ошибка';
    let errorType = 'danger';
    
    if (typeof error === 'string') {
        errorMessage = error;
    } else if (error?.message) {
        errorMessage = error.message;
    }
    
    if (errorMessage.includes('ключ') || errorMessage.includes('API key') || errorMessage.includes('401')) {
        errorType = 'warning';
        errorMessage = 'Проблема с API-ключом OpenRouter. Проверьте ключ и попробуйте снова.';
    } else if (errorMessage.includes('сеть') || errorMessage.includes('интернет')) {
        errorType = 'info';
    } else if (errorMessage.includes('model ID') || errorMessage.includes('модель')) {
        errorType = 'warning';
        errorMessage = 'Некорректная модель ИИ. Пожалуйста, используйте другую модель.';
    }
    
    const html = `
        <div class="alert alert-${errorType}">
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <i class="fas fa-exclamation-triangle fa-2x"></i>
                </div>
                <div>
                    <h5 class="alert-heading">Ошибка при обработке запроса</h5>
                    <p class="mb-0">${escapeHtml(errorMessage)}</p>
                </div>
            </div>
            
            <div class="mt-3">
                <strong>Что можно сделать:</strong>
                <ul class="mb-0">
                    <li>Проверьте правильность API-ключа OpenRouter (для режима чата)</li>
                    <li>Убедитесь, что на счету есть средства (бесплатные запросы доступны на <a href="https://openrouter.ai" target="_blank">OpenRouter</a>)</li>
                    <li>Попробуйте более простой запрос</li>
                    <li>Используйте обычный поиск через <a href="/components">фильтры</a></li>
                </ul>
            </div>
        </div>
        
        <div class="text-center mt-3">
            <button class="btn btn-outline-primary me-2" onclick="document.getElementById('openrouter-api-key').focus()">
                <i class="fas fa-key"></i> Проверить API-ключ
            </button>
            <a href="https://openrouter.ai/keys" target="_blank" class="btn btn-outline-success">
                <i class="fas fa-external-link-alt"></i> Получить ключ OpenRouter
            </a>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
}

// Функция для очистки поля запроса
function clearAiQuery() {
    document.getElementById('ai-query-input').value = '';
    document.getElementById('ai-results').innerHTML = '';
    showNotification('Запрос и результаты очищены', 'info');
}

// Функция для загрузки примера запроса
function loadExample(element) {
    const text = element.textContent || element.innerText;
    document.getElementById('ai-query-input').value = text.trim();
    document.getElementById('ai-query-input').focus();
    showNotification('Пример запроса загружен', 'info');
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // 1. Инициализация tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 2. Сохраняем статус brain.py в data-атрибут для использования в JavaScript
    const brainAvailableElement = document.querySelector('[data-brain-available]');
    if (brainAvailableElement) {
        document.body.dataset.brainAvailable = brainAvailableElement.dataset.brainAvailable;
    }
    
    // 3. Обработка формы фильтров (если есть на странице)
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalHtml = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Поиск...';
                submitBtn.disabled = true;
                
                setTimeout(() => {
                    submitBtn.innerHTML = originalHtml;
                    submitBtn.disabled = false;
                }, 3000);
            }
        });
    }
    
    // 4. Инициализация управления API-ключом
    ApiKeyManager.loadKey();
    
    const saveKeyBtn = document.getElementById('save-api-key-btn');
    if (saveKeyBtn) {
        saveKeyBtn.addEventListener('click', () => ApiKeyManager.saveKey());
    }
    
    const clearKeyBtn = document.getElementById('clear-api-key-btn');
    if (clearKeyBtn) {
        clearKeyBtn.addEventListener('click', () => ApiKeyManager.clearKey());
    }
    
    const apiKeyInput = document.getElementById('openrouter-api-key');
    if (apiKeyInput) {
        apiKeyInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                ApiKeyManager.saveKey();
            }
        });
    }
    
    // 5. Обработка формы ИИ-запросов
    const aiQueryForm = document.getElementById('ai-query-form');
    if (aiQueryForm) {
        aiQueryForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const queryInput = document.getElementById('ai-query-input');
            const submitBtn = document.getElementById('ai-query-submit');
            const resultsDiv = document.getElementById('ai-results');
            const loadingDiv = document.getElementById('ai-loading');
            
            const userQuestion = queryInput.value.trim();
            
            if (!userQuestion) {
                showNotification('Пожалуйста, введите запрос', 'warning');
                return;
            }
            
            // Анализируем тип запроса
            const queryType = analyzeQueryType(userQuestion);
            showNotification(`Обработка ${queryType === 'chat' ? 'общего вопроса' : 'поискового запроса'}...`, 'info');
            
            // Показываем индикатор загрузки
            if (submitBtn) {
                const originalHtml = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Обработка...';
                submitBtn.disabled = true;
            }
            if (loadingDiv) loadingDiv.style.display = 'block';
            if (resultsDiv) resultsDiv.innerHTML = '';
            
            try {
                const result = await sendAiQuery(userQuestion);
                
                if (result) {
                    if (result.success) {
                        if (queryType === 'chat') {
                            displayOpenRouterResponse(userQuestion, result);
                        } else {
                            displayBrainResponse(userQuestion, result);
                        }
                        saveToHistory(userQuestion, result, queryType);
                    } else {
                        displayAiError(result.error);
                    }
                }
                
            } catch (error) {
                console.error('Ошибка при обработке ИИ-запроса:', error);
                displayAiError(error.message || 'Неизвестная ошибка');
            } finally {
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Отправить';
                    submitBtn.disabled = false;
                }
                if (loadingDiv) loadingDiv.style.display = 'none';
            }
        });
    }
    
    // 6. Автозаполнение ИИ-запроса из URL параметра
    const urlParams = new URLSearchParams(window.location.search);
    const componentParam = urlParams.get('component');
    if (componentParam && document.getElementById('ai-query-input')) {
        document.getElementById('ai-query-input').value = 
            `Расскажи о компоненте ${escapeHtml(componentParam)}: его параметрах, характеристиках и применении в схемах`;
    }
    
    // 7. Загрузка истории запросов
    loadQueryHistory();
    
    // 8. Обновление статуса системы
    AiStatusManager.updateStatus();
});

// Функция для сохранения запроса в истории
function saveToHistory(query, result, type) {
    try {
        const history = JSON.parse(localStorage.getItem('ai_query_history') || '[]');
        
        history.unshift({
            query: query,
            type: type,
            mode: result.mode || 'unknown',
            response: result.response ? result.response.substring(0, 200) + '...' : 'Результаты поиска',
            timestamp: new Date().toISOString(),
            success: result.success
        });
        
        if (history.length > 20) {
            history.length = 20;
        }
        
        localStorage.setItem('ai_query_history', JSON.stringify(history));
        
        loadQueryHistory();
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
            let html = '<h6><i class="fas fa-history"></i> История запросов:</h6><div class="list-group">';
            
            history.slice(0, 5).forEach((item, index) => {
                const date = new Date(item.timestamp);
                const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const dateStr = date.toLocaleDateString();
                const typeIcon = item.type === 'chat' ? 'fa-comments text-success' : 'fa-search text-info';
                const typeText = item.type === 'chat' ? 'Чат' : 'Поиск';
                const modeBadge = item.mode === 'local_parser' ? '<span class="badge bg-warning ms-1">Лок.</span>' : 
                                 item.mode === 'openrouter' ? '<span class="badge bg-success ms-1">ИИ</span>' : '';
                
                html += `
                    <a href="javascript:void(0)" class="list-group-item list-group-item-action" onclick="loadHistoryQuery(${index})">
                        <div class="d-flex w-100 justify-content-between">
                            <small class="text-truncate" style="max-width: 200px;" title="${escapeHtml(item.query)}">
                                <i class="fas ${typeIcon} me-1"></i> ${escapeHtml(item.query)}
                                ${modeBadge}
                            </small>
                            <small class="text-${item.success ? 'success' : 'danger'}">
                                <i class="fas fa-${item.success ? 'check' : 'times'}"></i>
                            </small>
                        </div>
                        <div class="d-flex justify-content-between align-items-center mt-1">
                            <small class="text-muted">${dateStr} ${timeStr}</small>
                            <small class="badge bg-${item.type === 'chat' ? 'success' : 'info'}">${typeText}</small>
                        </div>
                    </a>
                `;
            });
            
            html += '</div>';
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

// Экспортируем функции для глобального использования
window.ApiKeyManager = ApiKeyManager;
window.AiStatusManager = AiStatusManager;
window.askAboutComponent = askAboutComponent;
window.showNotification = showNotification;
window.loadHistoryQuery = loadHistoryQuery;
window.clearAiQuery = clearAiQuery;
window.loadExample = loadExample;
window.useResponseAsQuery = useResponseAsQuery;
window.copyAiResponse = copyAiResponse;
window.copyQueryResult = copyQueryResult;
window.showComponentVah = showComponentVah;
window.createVahChart = createVahChart;