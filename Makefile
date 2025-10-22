# Makefile для системы нейросетевых инвестиций

.PHONY: help install setup run train backtest status validate clean test

# Цвета для вывода
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)Система нейросетевых инвестиций$(NC)"
	@echo ""
	@echo "Доступные команды:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Установить зависимости
	@echo "$(GREEN)📦 Установка зависимостей...$(NC)"
	pip install -r requirements.txt

setup: ## Первоначальная настройка проекта
	@echo "$(GREEN)🔧 Настройка проекта...$(NC)"
	@mkdir -p logs models data config
	@if [ ! -f config/main.yaml ]; then \
		echo "$(YELLOW)📋 Создание базовой конфигурации...$(NC)"; \
		cp config/examples/beginners.yaml config/main.yaml; \
		echo "$(GREEN)✅ Базовая конфигурация создана$(NC)"; \
	fi
	@echo "$(GREEN)✅ Настройка завершена$(NC)"

run: ## Запустить торговую систему
	@echo "$(GREEN)💰 Запуск торговой системы...$(NC)"
	python run.py --mode trading

train: ## Обучение моделей
	@echo "$(GREEN)🧠 Обучение нейросетей...$(NC)"
	python run.py --mode train

backtest: ## Бэктестинг (используйте: make backtest START=2023-01-01 END=2023-12-31)
	@echo "$(GREEN)📊 Запуск бэктестинга...$(NC)"
	python run.py --mode backtest --start $(START) --end $(END)

status: ## Показать статус системы
	@echo "$(GREEN)📊 Проверка статуса...$(NC)"
	python run.py --status

validate: ## Проверить конфигурацию
	@echo "$(GREEN)🔍 Проверка конфигурации...$(NC)"
	python run.py --validate

test: ## Запустить тесты
	@echo "$(GREEN)🧪 Запуск тестов...$(NC)"
	python -m pytest tests/ -v

clean: ## Очистить временные файлы
	@echo "$(YELLOW)🧹 Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "$(GREEN)✅ Очистка завершена$(NC)"

logs: ## Показать последние логи
	@echo "$(GREEN)📋 Последние логи:$(NC)"
	@tail -n 20 logs/investment_system.log 2>/dev/null || echo "$(YELLOW)Логи не найдены$(NC)"

# Windows команды
run-windows: ## Запуск на Windows
	@echo "$(GREEN)💰 Запуск на Windows...$(NC)"
	run.bat

train-windows: ## Обучение на Windows
	@echo "$(GREEN)🧠 Обучение на Windows...$(NC)"
	run.bat --mode train

# Linux/macOS команды
run-linux: ## Запуск на Linux/macOS
	@echo "$(GREEN)💰 Запуск на Linux/macOS...$(NC)"
	./run.sh

train-linux: ## Обучение на Linux/macOS
	@echo "$(GREEN)🧠 Обучение на Linux/macOS...$(NC)"
	./run.sh --mode train





