#!/usr/bin/env python3
"""
Скрипт для валидации конфигурации main.yaml
"""

import sys
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any


def validate_config(config_path: str) -> bool:
    """
    Валидация конфигурационного файла
    
    Args:
        config_path: Путь к конфигурационному файлу
        
    Returns:
        True если конфигурация валидна
    """
    try:
        print(f"🔍 Проверка конфигурации: {config_path}")
        
        # Загрузка конфигурации
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        if not config:
            print("❌ Конфигурация пуста")
            return False
        
        # Проверка основных секций
        required_sections = ['data', 'neural_networks', 'trading', 'portfolio']
        for section in required_sections:
            if section not in config:
                print(f"❌ Отсутствует обязательная секция: {section}")
                return False
        
        # Валидация секции data
        if not validate_data_section(config['data']):
            return False
        
        # Валидация секции neural_networks
        if not validate_neural_networks_section(config['neural_networks']):
            return False
        
        # Валидация секции trading
        if not validate_trading_section(config['trading']):
            return False
        
        # Валидация секции portfolio
        if not validate_portfolio_section(config['portfolio']):
            return False
        
        # Валидация логирования
        if 'logging' in config:
            validate_logging_section(config['logging'])
        
        # Валидация уведомлений
        if 'notifications' in config:
            validate_notifications_section(config['notifications'])
        
        print("✅ Конфигурация валидна!")
        return True
        
    except FileNotFoundError:
        print(f"❌ Файл конфигурации не найден: {config_path}")
        return False
    except yaml.YAMLError as e:
        print(f"❌ Ошибка синтаксиса YAML: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False


def validate_data_section(data_config: Dict[str, Any]) -> bool:
    """Валидация секции data"""
    print("📊 Проверка настроек данных...")
    
    # Проверка обязательных параметров
    required_params = ['provider', 'symbols', 'update_interval', 'history_days']
    for param in required_params:
        if param not in data_config:
            print(f"❌ Отсутствует параметр data.{param}")
            return False
    
    # Проверка символов
    symbols = data_config['symbols']
    if not isinstance(symbols, list) or len(symbols) == 0:
        print("❌ data.symbols должен быть непустым списком")
        return False
    
    valid_symbols = ['SBER', 'GAZP', 'LKOH', 'NVTK', 'ROSN', 'NLMK', 'MAGN', 'YNDX', 'MOEX', 'VTBR', 'ALRS', 'AFLT', 'SNGSP', 'MGNT', 'CHMF', 'RUAL', 'FIVE', 'OZON']
    invalid_symbols = [s for s in symbols if s not in valid_symbols]
    if invalid_symbols:
        print(f"⚠️  Неизвестные символы: {invalid_symbols}")
        print(f"Доступные символы: {valid_symbols}")
    
    # Проверка интервалов
    update_interval = data_config['update_interval']
    if not isinstance(update_interval, int) or update_interval < 60:
        print("⚠️  data.update_interval должен быть >= 60 секунд")
    
    history_days = data_config['history_days']
    if not isinstance(history_days, int) or history_days < 90:
        print("⚠️  data.history_days должен быть >= 90 дней")
    
    print("✅ Настройки данных корректны")
    return True


def validate_neural_networks_section(nn_config: Dict[str, Any]) -> bool:
    """Валидация секции neural_networks"""
    print("🧠 Проверка настроек нейросетей...")
    
    # Проверка моделей
    if 'models' not in nn_config:
        print("❌ Отсутствует neural_networks.models")
        return False
    
    models = nn_config['models']
    if not isinstance(models, list) or len(models) == 0:
        print("❌ neural_networks.models должен быть непустым списком")
        return False
    
    total_weight = 0
    enabled_models = 0
    
    for i, model in enumerate(models):
        print(f"  📋 Проверка модели {i+1}: {model.get('name', 'unnamed')}")
        
        # Проверка обязательных параметров модели
        required_model_params = ['name', 'type', 'weight', 'enabled']
        for param in required_model_params:
            if param not in model:
                print(f"❌ Модель {i+1}: отсутствует параметр {param}")
                return False
        
        # Проверка типа модели
        model_type = model['type']
        if model_type not in ['xgboost', 'deepseek', 'transformer']:
            print(f"❌ Модель {i+1}: неизвестный тип {model_type}")
            return False
        
        # Проверка весов
        weight = model['weight']
        if not isinstance(weight, (int, float)) or weight < 0 or weight > 1:
            print(f"❌ Модель {i+1}: вес должен быть от 0 до 1")
            return False
        
        total_weight += weight
        
        if model['enabled']:
            enabled_models += 1
        
        # Специфичные проверки для XGBoost
        if model_type == 'xgboost':
            validate_xgboost_model(model, i+1)
        
        # Специфичные проверки для DeepSeek
        elif model_type == 'deepseek':
            validate_deepseek_model(model, i+1)
    
    # Проверка весов
    if abs(total_weight - 1.0) > 0.01:
        print(f"⚠️  Сумма весов моделей должна быть близка к 1.0, текущая: {total_weight:.3f}")
    
    if enabled_models == 0:
        print("❌ Нет включенных моделей")
        return False
    
    print(f"✅ Настройки нейросетей корректны ({enabled_models} моделей включено)")
    return True


def validate_xgboost_model(model: Dict[str, Any], model_num: int):
    """Валидация XGBoost модели"""
    xgb_params = ['n_estimators', 'max_depth', 'learning_rate', 'subsample', 'colsample_bytree', 'buy_threshold', 'sell_threshold']
    
    for param in xgb_params:
        if param not in model:
            print(f"⚠️  XGBoost модель {model_num}: отсутствует параметр {param}")
    
    # Проверка порогов
    if 'buy_threshold' in model and 'sell_threshold' in model:
        buy_thresh = model['buy_threshold']
        sell_thresh = model['sell_threshold']
        
        if not isinstance(buy_thresh, (int, float)) or buy_thresh <= 0:
            print(f"⚠️  XGBoost модель {model_num}: buy_threshold должен быть положительным")
        
        if not isinstance(sell_thresh, (int, float)) or sell_thresh >= 0:
            print(f"⚠️  XGBoost модель {model_num}: sell_threshold должен быть отрицательным")


def validate_deepseek_model(model: Dict[str, Any], model_num: int):
    """Валидация DeepSeek модели"""
    deepseek_params = ['api_key', 'base_url', 'model_name', 'max_tokens', 'temperature', 'analysis_window']
    
    for param in deepseek_params:
        if param not in model:
            print(f"⚠️  DeepSeek модель {model_num}: отсутствует параметр {param}")
    
    # Проверка API ключа
    if 'api_key' in model:
        api_key = model['api_key']
        if not api_key or api_key == "your_deepseek_api_key":
            print(f"⚠️  DeepSeek модель {model_num}: необходимо указать реальный API ключ")
    
    # Проверка max_tokens
    if 'max_tokens' in model:
        max_tokens = model['max_tokens']
        if not isinstance(max_tokens, int) or max_tokens < 1000 or max_tokens > 8000:
            print(f"⚠️  DeepSeek модель {model_num}: max_tokens должен быть от 1000 до 8000")
    
    # Проверка temperature
    if 'temperature' in model:
        temperature = model['temperature']
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 1:
            print(f"⚠️  DeepSeek модель {model_num}: temperature должен быть от 0 до 1")
    
    # Проверка analysis_window
    if 'analysis_window' in model:
        window = model['analysis_window']
        if not isinstance(window, int) or window < 10 or window > 90:
            print(f"⚠️  DeepSeek модель {model_num}: analysis_window должен быть от 10 до 90 дней")


def validate_trading_section(trading_config: Dict[str, Any]) -> bool:
    """Валидация секции trading"""
    print("💰 Проверка настроек торговли...")
    
    # Проверка обязательных параметров
    required_params = ['broker', 'signal_threshold', 'max_positions', 'position_size']
    for param in required_params:
        if param not in trading_config:
            print(f"❌ Отсутствует параметр trading.{param}")
            return False
    
    # Проверка брокера
    broker = trading_config['broker']
    valid_brokers = ['paper', 'tinkoff', 'sber']
    if broker not in valid_brokers:
        print(f"❌ Неизвестный брокер: {broker}. Доступные: {valid_brokers}")
        return False
    
    # Проверка порога сигналов
    signal_threshold = trading_config['signal_threshold']
    if not isinstance(signal_threshold, (int, float)) or signal_threshold < 0 or signal_threshold > 1:
        print("❌ trading.signal_threshold должен быть от 0 до 1")
        return False
    
    # Проверка количества позиций
    max_positions = trading_config['max_positions']
    if not isinstance(max_positions, int) or max_positions < 1 or max_positions > 50:
        print("⚠️  trading.max_positions рекомендуется от 1 до 50")
    
    # Проверка размера позиции
    position_size = trading_config['position_size']
    if not isinstance(position_size, (int, float)) or position_size <= 0 or position_size > 0.5:
        print("⚠️  trading.position_size рекомендуется от 0 до 0.5")
    
    print("✅ Настройки торговли корректны")
    return True


def validate_portfolio_section(portfolio_config: Dict[str, Any]) -> bool:
    """Валидация секции portfolio"""
    print("📈 Проверка настроек портфеля...")
    
    # Проверка обязательных параметров
    required_params = ['initial_capital', 'max_risk_per_trade', 'max_portfolio_risk']
    for param in required_params:
        if param not in portfolio_config:
            print(f"❌ Отсутствует параметр portfolio.{param}")
            return False
    
    # Проверка начального капитала
    initial_capital = portfolio_config['initial_capital']
    if not isinstance(initial_capital, (int, float)) or initial_capital < 10000:
        print("⚠️  portfolio.initial_capital рекомендуется >= 10000")
    
    # Проверка рисков
    max_risk_per_trade = portfolio_config['max_risk_per_trade']
    if not isinstance(max_risk_per_trade, (int, float)) or max_risk_per_trade <= 0 or max_risk_per_trade > 0.1:
        print("⚠️  portfolio.max_risk_per_trade рекомендуется от 0 до 0.1")
    
    max_portfolio_risk = portfolio_config['max_portfolio_risk']
    if not isinstance(max_portfolio_risk, (int, float)) or max_portfolio_risk <= 0 or max_portfolio_risk > 0.5:
        print("⚠️  portfolio.max_portfolio_risk рекомендуется от 0 до 0.5")
    
    print("✅ Настройки портфеля корректны")
    return True


def validate_logging_section(logging_config: Dict[str, Any]):
    """Валидация секции logging"""
    print("📝 Проверка настроек логирования...")
    
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    level = logging_config.get('level', 'INFO')
    if level not in valid_levels:
        print(f"⚠️  Неизвестный уровень логирования: {level}")
    
    print("✅ Настройки логирования корректны")


def validate_notifications_section(notifications_config: Dict[str, Any]):
    """Валидация секции notifications"""
    print("📧 Проверка настроек уведомлений...")
    
    if notifications_config.get('enabled', False):
        # Проверка email настроек
        if 'email' in notifications_config:
            email_config = notifications_config['email']
            required_email_params = ['smtp_server', 'smtp_port', 'username', 'password', 'to_email']
            for param in required_email_params:
                if param not in email_config:
                    print(f"⚠️  Отсутствует параметр notifications.email.{param}")
        
        # Проверка telegram настроек
        if 'telegram' in notifications_config:
            telegram_config = notifications_config['telegram']
            required_telegram_params = ['bot_token', 'chat_id']
            for param in required_telegram_params:
                if param not in telegram_config:
                    print(f"⚠️  Отсутствует параметр notifications.telegram.{param}")
    
    print("✅ Настройки уведомлений корректны")


def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Использование: python validate_config.py <путь_к_config.yaml>")
        print("Пример: python validate_config.py config/main.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    if not Path(config_path).exists():
        print(f"❌ Файл не найден: {config_path}")
        sys.exit(1)
    
    is_valid = validate_config(config_path)
    
    if is_valid:
        print("\n🎉 Конфигурация готова к использованию!")
        sys.exit(0)
    else:
        print("\n❌ Конфигурация содержит ошибки!")
        sys.exit(1)


if __name__ == "__main__":
    main()
