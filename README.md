
<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Latin_cross.svg/120px-Latin_cross.svg.png" alt="Bot Logo" height="120" />
</p>

# ✝️ Telegram Bot — TGbot

![Python](https://img.shields.io/badge/python-3.9+-blue?logo=python)
![PTB](https://img.shields.io/badge/telegram--bot-20.6-blue?logo=telegram)
![License](https://img.shields.io/github/license/json-debag/TGbot)

Это простой Telegram‑бот, написанный на Python с использованием библиотеки [python-telegram-bot 20.6](https://docs.python-telegram-bot.org/), который отвечает на команду `/start`.

---

## 📦 Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/json-debag/TGbot.git
cd TGbot
```

### 2. Создать и активировать виртуальное окружение

```powershell
python -m venv venv
.env\Scripts\Activate.ps1      # PowerShell
# или
venv\Scripts\activate.bat        # CMD
```

### 3. Установить зависимости

```bash
pip install python-telegram-bot==20.6 python-dotenv
```

### 4. Создать файл `.env` с токеном бота

Создай `.env` в корне проекта и вставь в него:

```
TOKEN=ваш_токен_от_BotFather
```

⚠️ **Никогда не публикуй этот токен в репозитории!**

### 5. Запустить бота

```bash
python bot.py
```

Бот должен запуститься и слушать команды. Проверь `/start` в Telegram.

---

## 🔐 .gitignore

Убедись, что файл `.gitignore` содержит:

```
.env
venv/
__pycache__/
*.pyc
```

---

## 📌 Возможности (на данный момент)

- `/start` — приветствие
- Хранение токена в `.env` через `python-dotenv`

---

## 🛠️ Планы на развитие

- [ ] Команда `/help` — вывод списка доступных команд
- [ ] Подключение базы данных для логирования пользователей
- [ ] Рассылки подписчикам
- [ ] Хостинг на PythonAnywhere / Fly.io
- [ ] Подключение webhook
- [ ] Библия / духовные размышления

---

## 👨‍💻 Автор

- [json-debag](https://github.com/json-debag)
