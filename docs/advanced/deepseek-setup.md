# Настройка DeepSeek API для нейросетевых инвестиций

## Что такое DeepSeek?

DeepSeek - это мощная языковая модель искусственного интеллекта, которая может анализировать финансовые данные и давать торговые рекомендации. В нашей системе DeepSeek используется для:

- Анализа рыночных паттернов
- Генерации торговых сигналов
- Оценки рисков и возможностей
- Интерпретации технических индикаторов

## Получение API ключа

### 1. Регистрация на платформе DeepSeek

1. Перейдите на https://platform.deepseek.com/
2. Нажмите "Sign Up" или "Регистрация"
3. Заполните форму регистрации:
   - Email адрес
   - Пароль
   - Подтверждение email

### 2. Создание API ключа

1. Войдите в свой аккаунт
2. Перейдите в раздел "API Keys" или "API ключи"
3. Нажмите "Create New Key" или "Создать новый ключ"
4. Дайте название ключу (например, "Investment System")
5. Скопируйте созданный ключ (он больше не будет показан!)

### 3. Настройка переменной окружения

#### Windows (PowerShell):
```powershell
$env:DEEPSEEK_API_KEY="your_api_key_here"
```

#### Windows (Command Prompt):
```cmd
set DEEPSEEK_API_KEY=your_api_key_here
```

#### Linux/Mac:
```bash
export DEEPSEEK_API_KEY="your_api_key_here"
```

#### Постоянная настройка (Linux/Mac):
Добавьте в файл `~/.bashrc` или `~/.zshrc`:
```bash
echo 'export DEEPSEEK_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Проверка настройки

```bash
echo $DEEPSEEK_API_KEY
```

## Настройка в конфигурации

### Базовая конфигурация DeepSeek

```yaml
neural_networks:
  models:
    - name: deepseek_analyzer
      type: deepseek
      weight: 0.4
      enabled: true
      api_key: ${DEEPSEEK_API_KEY}
      base_url: "https://api.deepseek.com/v1"
      model_name: "deepseek-chat"
      max_tokens: 4000
      temperature: 0.3
      analysis_window: 30
```

### Параметры DeepSeek

| Параметр | Описание | Рекомендуемое значение |
|----------|----------|----------------------|
| `api_key` | API ключ DeepSeek | Из переменной окружения |
| `base_url` | URL API | https://api.deepseek.com/v1 |
| `model_name` | Модель для использования | deepseek-chat |
| `max_tokens` | Максимум токенов в ответе | 2000-8000 |
| `temperature` | Креативность (0-1) | 0.2-0.4 |
| `analysis_window` | Дни для анализа | 20-90 |

## Уровни настройки

### Для начинающих (экономичная)

```yaml
- name: deepseek_beginners
  type: deepseek
  weight: 0.3
  enabled: true
  api_key: ${DEEPSEEK_API_KEY}
  max_tokens: 2000        # Меньше токенов
  temperature: 0.2        # Консервативные предсказания
  analysis_window: 20     # Меньше данных
```

### Для опытных (сбалансированная)

```yaml
- name: deepseek_advanced
  type: deepseek
  weight: 0.3
  enabled: true
  api_key: ${DEEPSEEK_API_KEY}
  max_tokens: 4000        # Среднее количество токенов
  temperature: 0.3        # Сбалансированные предсказания
  analysis_window: 30     # Стандартное окно
```

### Для продакшена (максимальная точность)

```yaml
- name: deepseek_production
  type: deepseek
  weight: 0.35
  enabled: true
  api_key: ${DEEPSEEK_API_KEY}
  max_tokens: 8000        # Максимум токенов
  temperature: 0.3        # Стабильные предсказания
  analysis_window: 60     # Больше данных для анализа
```

## Тестирование DeepSeek

### 1. Проверка подключения

```python
import asyncio
from src.neural_networks.deepseek_network import DeepSeekNetwork

async def test_deepseek():
    config = {
        'api_key': 'your_api_key',
        'model_name': 'deepseek-chat',
        'max_tokens': 1000,
        'temperature': 0.3
    }
    
    deepseek = DeepSeekNetwork('test', config)
    await deepseek.initialize()
    print("DeepSeek подключение успешно!")

asyncio.run(test_deepseek())
```

### 2. Проверка анализа данных

```python
import pandas as pd

# Создание тестовых данных
test_data = pd.DataFrame({
    'Close': [100, 101, 102, 101, 100, 99, 98, 99, 100, 101],
    'Volume': [1000, 1100, 1200, 1000, 900, 800, 700, 800, 900, 1000]
})

# Тестирование анализа
async def test_analysis():
    prediction = await deepseek.predict(test_data)
    print(f"Предсказание: {prediction}")

asyncio.run(test_analysis())
```

## Лимиты и стоимость

### Бесплатный план
- **Лимит запросов**: 1000 запросов в месяц
- **Лимит токенов**: 1M токенов в месяц
- **Скорость**: Стандартная

### Платные планы
- **Basic**: $5/месяц - 100K токенов
- **Pro**: $20/месяц - 1M токенов
- **Enterprise**: По запросу

### Оптимизация использования

1. **Кэширование**: Система автоматически кэширует ответы на 5 минут
2. **Эффективные промпты**: Используйте краткие и точные запросы
3. **Ограничение токенов**: Настройте `max_tokens` в зависимости от потребностей
4. **Интервалы анализа**: Увеличьте `analysis_interval` для экономии

## Устранение неполадок

### Ошибка аутентификации
```
ERROR: API вернул статус 401
```
**Решение**: Проверьте правильность API ключа

### Превышение лимитов
```
ERROR: Rate limit exceeded
```
**Решение**: Увеличьте интервалы между запросами

### Таймаут запроса
```
ERROR: Request timeout
```
**Решение**: Уменьшите `max_tokens` или увеличьте таймаут

### Неправильный формат ответа
```
ERROR: Не удалось распарсить ответ API
```
**Решение**: DeepSeek вернет базовое предсказание "HOLD"

## Мониторинг использования

### Проверка статуса DeepSeek

```python
from src.core.investment_system import InvestmentSystem

system = InvestmentSystem("config/main.yaml")
status = system.get_system_status()
print(status['network_manager']['models_status']['deepseek_analyzer'])
```

### Логи DeepSeek

Система ведет подробные логи работы с DeepSeek:
- Успешные запросы
- Ошибки API
- Время ответа
- Использование токенов

## Безопасность

### Защита API ключа

1. **Никогда не коммитьте ключ в код**
2. **Используйте переменные окружения**
3. **Регулярно ротируйте ключи**
4. **Мониторьте использование**

### Ограничение доступа

1. **Используйте IP whitelist** (если доступно)
2. **Настройте уведомления** о подозрительной активности
3. **Ведите логи** всех запросов

## Альтернативы DeepSeek

Если DeepSeek недоступен, можно использовать:

1. **OpenAI GPT-4** - замените в конфигурации
2. **Claude API** - аналогичная интеграция
3. **Локальные модели** - LSTM и XGBoost остаются доступными

## Заключение

DeepSeek значительно расширяет возможности системы нейросетевых инвестиций, предоставляя:

- Качественный анализ рынка
- Интерпретацию сложных паттернов
- Обоснованные торговые рекомендации
- Оценку рисков и возможностей

Правильная настройка DeepSeek поможет получить максимальную отдачу от системы инвестиций.
