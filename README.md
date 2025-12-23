# 🤖 Electronic Component Library with AI Assistant (Электронная библиотека компонентов с ИИ-ассистентом)

**AI understands natural language queries and searches electronic components in the local database**  
**ИИ понимает запросы на естественном языке и ищет электронные компоненты в локальной базе**

---

## 🎯 Что это такое? / What is this?

### 🇷🇺 На русском:
Прототип системы, которая позволяет:
- Задавать вопросы на русском языке о электронных компонентах
- Автоматически искать компоненты по параметрам (ток, напряжение, мощность)
- Просматривать характеристики (ВАХ) компонентов
- Расширять базу данных коллективными усилиями

### 🇬🇧 In English:
Prototype system that allows you to:
- Ask questions in Russian about electronic components
- Automatically search components by parameters (current, voltage, power)
- View component characteristics (I-V curves)
- Extend the database collaboratively

---

## 🔗 Access from Belarus via OpenRouter

### 🇷🇺 Для работы с DeepSeek/Kimi API из Беларуси используется **OpenRouter** — единый шлюз к ИИ-моделям без региональных ограничений.

### 🇬🇧 For accessing DeepSeek/Kimi API from Belarus, we use **OpenRouter** — a unified gateway to AI models without regional restrictions.

---

## 🚀 Быстрый старт / Quick Start

### 1. Установка / Installation

```bash
# 🇷🇺 Клонируйте репозиторий
# 🇬🇧 Clone the repository
git clone https://github.com/IlyaSchastlivchik/electronic-component-library.git
cd electronic-component-library

# 🇷🇺 Активируйте виртуальное окружение
# 🇬🇧 Activate virtual environment
venv\Scripts\activate

# 🇷🇺 Установите зависимости
# 🇬🇧 Install dependencies
pip install -r requirements.txt

# 🤖 Electronic Component Library with AI Assistant

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**An open-source database of electronic components with AI-powered natural language search**

---

## 🌐 Live Demo
🚀 **[Try it online!](https://your-deployed-url.here)** *(coming soon)*

## 📸 Screenshots
![Main Page](https://via.placeholder.com/800x400?text=AI+Component+Library+Interface)
![Component Search](https://via.placeholder.com/800x400?text=Filter+Components+by+Parameters)

## ✨ Features

### 🔍 Intelligent Search
- **Natural language queries** (Ask: "Find transistors with current > 0.1A")
- **Parameter-based filtering** (Type, origin, voltage, current, power)
- **Soviet/American component database**

### 📊 Visualization
- **Interactive I-V characteristic plots**
- **Component comparison tools**
- **Export data in JSON format**

### 🤖 AI Integration
- **DeepSeek API integration** for natural language processing
- **Automatic parameter extraction** from user queries
- **Component recommendations** based on requirements

### 🌍 Web Interface
- **Modern responsive design** (Bootstrap 5)
- **Real-time filtering** and sorting
- **Detailed component pages** with graphs

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- DeepSeek API key (optional, for AI features)

### Installation
```bash
# 1. Clone repository
git clone https://github.com/IlyaSchastlivchik/electronic-component-library.git
cd electronic-component-library

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment variables
cp .env.example .env
# Edit .env file and add your DeepSeek API key

# 6. Run the server
python web_app.py