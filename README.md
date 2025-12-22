echo # 🤖 Электронная библиотека компонентов с ИИ-ассистентом > README.md
echo. >> README.md
echo **ИИ понимает запросы на естественном языке и ищет электронные компоненты в локальной базе** >> README.md
echo. >> README.md
echo ## 🎯 Что это такое? >> README.md
echo. >> README.md
echo Прототип системы, которая позволяет: >> README.md
echo - Задавать вопросы на русском языке о электронных компонентах >> README.md
echo - Автоматически искать компоненты по параметрам (ток, напряжение, мощность) >> README.md
echo - Просматривать характеристики (ВАХ) компонентов >> README.md
echo - Расширять базу данных коллективными усилиями >> README.md
echo. >> README.md
echo ## 🚀 Быстрый старт >> README.md
echo. >> README.md
echo ### 1. Установка >> README.md
echo ```bash >> README.md
echo # Клонируйте репозиторий >> README.md
echo git clone https://github.com/ваш-логин/ai-component-library.git >> README.md
echo cd ai-component-library >> README.md
echo. >> README.md
echo # Установите зависимости >> README.md
echo pip install -r requirements.txt >> README.md
echo. >> README.md
echo # Создайте файл .env с вашим API-ключом >> README.md
echo echo DEEPSEEK_API_KEY=ваш_ключ_тут ^> .env >> README.md
echo ``` >> README.md
echo. >> README.md
echo ### 2. Получите API-ключ DeepSeek >> README.md
echo 1. Зарегистрируйтесь на [platform.deepseek.com](https://platform.deepseek.com) >> README.md
echo 2. Создайте API-ключ в разделе API Keys >> README.md
echo 3. Добавьте его в файл `.env` >> README.md
echo. >> README.md
echo ### 3. Запуск >> README.md
echo ```bash >> README.md
echo # В первом терминале запустите сервер >> README.md
echo python server.py >> README.md
echo. >> README.md
echo # Во втором терминале запустите клиент >> README.md
echo python main.py >> README.md
echo ``` >> README.md
echo. >> README.md
echo ## 📖 Примеры использования >> README.md
echo. >> README.md
echo ``` >> README.md
echo Вопрос: "Найди биполярные транзисторы с током больше 0.1А" >> README.md
echo Ответ: Система найдет все NPN/PNP транзисторы с Imax > 0.1A >> README.md
echo. >> README.md
echo Вопрос: "Покажи характеристики 2N3904" >> README.md
echo Ответ: Система покажет ВАХ транзистора 2N3904 >> README.md
echo. >> README.md
echo Вопрос: "Какие мощные компоненты есть?" >> README.md
echo Ответ: Система найдет компоненты с Ptot > 1W >> README.md
echo ``` >> README.md