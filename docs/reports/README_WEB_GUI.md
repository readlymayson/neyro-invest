# 🌐 Neyro-Invest Web GUI

> Современный веб-интерфейс для нейросетевой торговой системы

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3-blue.svg)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Содержание

- [О проекте](#-о-проекте)
- [Возможности](#-возможности)
- [Быстрый старт](#-быстрый-старт)
- [Скриншоты](#-скриншоты)
- [Документация](#-документация)
- [Технологии](#-технологии)
- [API](#-api)
- [FAQ](#-faq)

---

## 🎯 О проекте

**Neyro-Invest Web GUI** - это современный веб-интерфейс для автоматизированной торговой системы на основе нейросетей. Система интегрируется с **T-Bank Invest API** и позволяет автоматически торговать российскими акциями.

### Что изменилось?

Старый desktop GUI (Tkinter) был **полностью заменен** на современный веб-интерфейс с улучшенным UX/UI и расширенными возможностями.

---

## ✨ Возможности

### 🌐 Веб-интерфейс
- **Браузерный доступ** - работает на любом устройстве
- **Адаптивный дизайн** - поддержка мобильных устройств
- **Real-time обновления** - через WebSocket
- **Интерактивные графики** - Chart.js визуализация

### 📊 Торговля
- **Автоматические сделки** - на основе ML моделей
- **Множество стратегий** - XGBoost, DeepSeek
- **Управление рисками** - защита от больших потерь
- **Песочница** - безопасное тестирование

### 💼 Портфель
- **Реальные данные** - синхронизация с T-Bank
- **Детальная аналитика** - по каждой позиции
- **P&L отчеты** - прибыль и убытки
- **История операций** - полный аудит

### 🔌 API
- **REST API** - полный набор endpoints
- **WebSocket** - real-time обновления
- **Swagger/Redoc** - автодокументация
- **Интеграции** - легко подключить боты

---

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.11+
- pip
- Токен T-Bank Invest API

### Установка

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/your-repo/neyro-invest.git
cd neyro-invest

# 2. Установите зависимости
pip install -r requirements.txt
```

### Запуск

#### Windows

```bash
run_web_gui.bat
```

#### Linux/Mac

```bash
chmod +x run_web_gui.sh
./run_web_gui.sh
```

#### Или напрямую

```bash
python web_launcher.py
```

### Доступ

После запуска откройте в браузере:

- 🏠 **Главная**: http://127.0.0.1:8000
- 📚 **API Docs**: http://127.0.0.1:8000/docs
- 📖 **Redoc**: http://127.0.0.1:8000/redoc

Браузер откроется автоматически!

---

## 📸 Скриншоты

### Дашборд
```
┌─────────────────────────────────────────────────────────┐
│ 📊 ДАШБОРД                                              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  💰 Портфель: 1,000,000 ₽    📈 P&L: +50,000 ₽ (5%)   │
│  💵 Наличные: 100,000 ₽      📦 Позиций: 5             │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ График портфеля  │  │ Распределение    │            │
│  │                  │  │                  │            │
│  └──────────────────┘  └──────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

### Торговля
```
┌─────────────────────────────────────────────────────────┐
│ ⚡ ТОРГОВЛЯ                                             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [▶️ Запустить]  [⏸️ Остановить]                       │
│                                                          │
│  Последние сигналы:                                     │
│  ┌────────────────────────────────────────────┐         │
│  │ 10:30 │ SBER │ BUY  │ 85% │ XGBoost │ ✓   │         │
│  │ 10:25 │ GAZP │ HOLD │ 72% │ DeepSeek│ ⏳  │         │
│  └────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

### Настройки
```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ НАСТРОЙКИ                                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  T-Bank API:                                            │
│  ┌────────────────────────────────────┐                 │
│  │ Токен: [••••••••••••]              │                 │
│  │ ☑ Режим песочницы                  │                 │
│  └────────────────────────────────────┘                 │
│                                                          │
│  [📊 Проверить]  [💰 Получить баланс]                 │
│                                                          │
│  Портфель:                                              │
│  Начальный капитал: [1,000,000] ₽                      │
│  Порог сигнала: [0.70]                                 │
│                                                          │
│  [💾 Сохранить конфигурацию]                           │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 Документация

### Быстрые руководства
- 🚀 [СТАРТ_ВЕБ_GUI.txt](СТАРТ_ВЕБ_GUI.txt) - ASCII инструкция
- 📖 [ЗАПУСК_ВЕБ_GUI.md](ЗАПУСК_ВЕБ_GUI.md) - Полное руководство
- 📝 [WEB_GUI_MIGRATION.md](WEB_GUI_MIGRATION.md) - Отчет о миграции

### Детальная документация
- 📘 [Web Quick Start](docs/gui/web-quick-start.md) - Подробное руководство
- 📗 [T-Bank Integration](docs/tbank/getting-started.md) - Интеграция с брокером
- 📙 [Configuration Guide](docs/configuration/guide.md) - Настройка системы
- 📕 [API Documentation](http://127.0.0.1:8000/docs) - Swagger UI

### Для разработчиков
- 🔧 [Структура проекта](#структура-проекта)
- 🔌 [API Reference](#api-endpoints)
- 💻 [Contributing Guide](CONTRIBUTING.md)

---

## 🛠 Технологии

### Backend
| Технология | Версия | Описание |
|-----------|--------|----------|
| **FastAPI** | 0.104+ | Современный async веб-фреймворк |
| **Uvicorn** | 0.24+ | ASGI сервер |
| **Pydantic** | 2.0+ | Валидация данных |
| **WebSockets** | 12.0+ | Real-time коммуникация |
| **Loguru** | 0.6+ | Продвинутое логирование |

### Frontend
| Технология | Версия | Описание |
|-----------|--------|----------|
| **Vue.js** | 3 | Реактивный фреймворк |
| **Chart.js** | 4 | Графики и визуализация |
| **CSS3** | - | Адаптивный дизайн |
| **WebSocket API** | - | Real-time обновления |

### Интеграции
| Сервис | Описание |
|--------|----------|
| **T-Bank Invest** | Биржевая торговля |
| **XGBoost** | ML модели |
| **DeepSeek** | LLM анализ |

---

## 🔌 API

### Основные endpoints

#### Система
```http
GET  /api/health              # Проверка здоровья
GET  /api/system/status       # Статус системы
POST /api/system/start        # Запуск системы
POST /api/system/stop         # Остановка системы
```

#### Данные
```http
GET  /api/portfolio           # Данные портфеля
GET  /api/signals             # Торговые сигналы
GET  /api/config              # Конфигурация
POST /api/config              # Сохранение конфигурации
GET  /api/logs                # Логи системы
```

#### T-Bank
```http
POST /api/tbank/check         # Проверка подключения
POST /api/tbank/get-balance   # Получение баланса
```

#### WebSocket
```
ws://127.0.0.1:8000/ws        # Real-time обновления
```

### Примеры использования

#### Python
```python
import requests

# Получение портфеля
response = requests.get("http://127.0.0.1:8000/api/portfolio")
portfolio = response.json()
print(f"Портфель: {portfolio['total_value']} ₽")

# Запуск системы
requests.post("http://127.0.0.1:8000/api/system/start")
```

#### JavaScript
```javascript
// REST API
fetch('http://127.0.0.1:8000/api/portfolio')
  .then(res => res.json())
  .then(data => console.log('Портфель:', data));

// WebSocket
const ws = new WebSocket('ws://127.0.0.1:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Обновление:', data);
};
```

#### cURL
```bash
# Проверка здоровья
curl http://127.0.0.1:8000/api/health

# Получение портфеля
curl http://127.0.0.1:8000/api/portfolio

# Запуск системы
curl -X POST http://127.0.0.1:8000/api/system/start
```

Полная документация API: http://127.0.0.1:8000/docs

---

## 📁 Структура проекта

```
neyro-invest/
├── src/
│   └── gui/
│       ├── web_app.py          # FastAPI приложение
│       └── static/
│           ├── index.html       # HTML интерфейс
│           ├── style.css        # Стили
│           └── app.js           # Vue.js логика
├── docs/
│   └── gui/
│       └── web-quick-start.md   # Документация
├── config/
│   └── main.yaml                # Конфигурация
├── logs/
│   └── web_launcher.log         # Логи
├── web_launcher.py              # Launcher
├── run_web_gui.bat              # Windows запуск
├── run_web_gui.sh               # Linux/Mac запуск
└── requirements.txt             # Зависимости
```

---

## ❓ FAQ

### Общие вопросы

**Q: Чем Web GUI лучше старого desktop GUI?**
- Работает в браузере на любом устройстве
- Современный дизайн и UX
- Real-time обновления через WebSocket
- REST API для интеграций
- Адаптивный интерфейс для мобильных

**Q: Безопасно ли использовать Web GUI?**
- Да, при правильной настройке
- Не открывайте в интернет без защиты
- Храните токен в безопасности
- Начинайте с sandbox режима

**Q: Как получить токен T-Bank?**
1. Откройте T-Bank Invest
2. Настройки → API для инвестиций
3. Создать токен
4. Выберите права доступа
5. Скопируйте токен

### Технические вопросы

**Q: Какой порт использует Web GUI?**
- По умолчанию: 8000
- Изменить: `set WEB_GUI_PORT=8080`

**Q: Как запустить на другом хосте?**
```bash
set WEB_GUI_HOST=0.0.0.0
python web_launcher.py
```

**Q: Работает ли старая конфигурация?**
- Да, полная обратная совместимость
- `config/main.yaml` работает без изменений

**Q: Где логи?**
- `logs/web_launcher.log` - запуск
- `logs/investment_system.log` - система
- Также в интерфейсе на вкладке "📝 Логи"

### Проблемы и решения

**Q: Порт уже занят**
```bash
set WEB_GUI_PORT=8080
python web_launcher.py
```

**Q: Модуль не найден**
```bash
pip install --upgrade -r requirements.txt
```

**Q: Не подключается к T-Bank**
1. Проверьте токен
2. Включите sandbox режим
3. Проверьте интернет
4. Смотрите логи

**Q: Браузер не открывается**
- Откройте вручную: http://127.0.0.1:8000

---

## 🎯 Roadmap

### v2.1 (Ближайшее)
- [ ] Темная тема
- [ ] Аутентификация (JWT)
- [ ] Уведомления (Push/Email)
- [ ] Экспорт отчетов (PDF/Excel)

### v2.2 (Среднесрочное)
- [ ] Мультипользовательский режим
- [ ] Telegram бот интеграция
- [ ] Расширенная аналитика
- [ ] Бэктестинг в интерфейсе

### v3.0 (Долгосрочное)
- [ ] Мобильное приложение
- [ ] Социальный трейдинг
- [ ] Маркетплейс стратегий
- [ ] AI ассистент

---

## 🤝 Contributing

Мы приветствуем вклад в проект!

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

Подробнее в [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. [LICENSE](LICENSE) для деталей.

---

## 📞 Поддержка

### Документация
- 📖 [Web Quick Start](docs/gui/web-quick-start.md)
- 📚 [API Docs](http://127.0.0.1:8000/docs)
- 📝 [FAQ](#-faq)

### Сообщество
- 💬 [GitHub Issues](https://github.com/your-repo/neyro-invest/issues)
- 📧 Email: support@neyro-invest.com
- 💭 [Discussions](https://github.com/your-repo/neyro-invest/discussions)

---

## 🙏 Благодарности

- FastAPI за отличный веб-фреймворк
- Vue.js за реактивный UI
- Chart.js за красивые графики
- T-Bank за предоставление API

---

## 📈 Статистика

- ⭐ Stars: [Поставьте звезду!](https://github.com/your-repo/neyro-invest)
- 🍴 Forks: [Fork проекта](https://github.com/your-repo/neyro-invest/fork)
- 🐛 Issues: [Сообщить о проблеме](https://github.com/your-repo/neyro-invest/issues)

---

<div align="center">

**Создано с ❤️ командой Neyro-Invest**

[Документация](docs/) • [API](http://127.0.0.1:8000/docs) • [Issues](https://github.com/your-repo/neyro-invest/issues)

</div>

