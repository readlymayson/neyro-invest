"""
Менеджер конфигурации системы
"""

import yaml
import os
from typing import Dict, Any
from pathlib import Path
from loguru import logger


class ConfigManager:
    """
    Менеджер для работы с конфигурационными файлами
    """
    
    def __init__(self, config_path: str, validate: bool = True):
        """
        Инициализация менеджера конфигурации
        
        Args:
            config_path: Путь к конфигурационному файлу
            validate: Выполнять валидацию конфигурации при загрузке
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
        if validate:
            self._validate_config()
    
    def _load_config(self):
        """
        Загрузка конфигурации из файла
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    # Подстановка переменных окружения
                    content = self._substitute_env_vars(content)
                    self.config = yaml.safe_load(content)
                    if not self.config:
                        raise ValueError("Конфигурация пуста или невалидна")
                logger.info(f"Конфигурация загружена из {self.config_path}")
            else:
                logger.warning(f"Файл конфигурации {self.config_path} не найден")
                self.config = self._get_default_config()
                self._save_config()
        except yaml.YAMLError as e:
            logger.error(f"Ошибка синтаксиса YAML в конфигурации: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            self.config = self._get_default_config()
    
    def _validate_config(self):
        """
        Валидация загруженной конфигурации
        """
        if not self.config:
            raise ValueError("Конфигурация не загружена")
        
        # Проверка обязательных секций
        required_sections = ['data', 'neural_networks', 'trading', 'portfolio']
        missing_sections = [s for s in required_sections if s not in self.config]
        if missing_sections:
            raise ValueError(f"Отсутствуют обязательные секции конфигурации: {missing_sections}")
        
        # Валидация секции data
        data_config = self.config.get('data', {})
        if not isinstance(data_config.get('symbols'), list) or len(data_config.get('symbols', [])) == 0:
            raise ValueError("data.symbols должен быть непустым списком")
        
        if not isinstance(data_config.get('update_interval'), (int, float)) or data_config.get('update_interval', 0) < 1:
            raise ValueError("data.update_interval должен быть положительным числом")
        
        # Валидация секции neural_networks
        nn_config = self.config.get('neural_networks', {})
        if not isinstance(nn_config.get('models'), list) or len(nn_config.get('models', [])) == 0:
            raise ValueError("neural_networks.models должен быть непустым списком")
        
        # Валидация секции trading
        trading_config = self.config.get('trading', {})
        signal_threshold = trading_config.get('signals', {}).get('min_confidence', trading_config.get('signal_threshold', 0.5))
        if not isinstance(signal_threshold, (int, float)) or not (0 <= signal_threshold <= 1):
            raise ValueError("trading.signals.min_confidence должен быть числом от 0 до 1")
        
        logger.debug("Валидация конфигурации пройдена успешно")
    
    def _substitute_env_vars(self, content: str) -> str:
        """
        Подстановка переменных окружения в конфигурацию
        
        Args:
            content: Содержимое конфигурационного файла
            
        Returns:
            Контент с подставленными переменными окружения
        """
        import re
        
        def replace_env_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) else ''
            return os.getenv(var_name, default_value)
        
        # Паттерн для ${VAR_NAME} или ${VAR_NAME:default_value}
        pattern = r'\$\{([^:}]+)(?::([^}]*))?\}'
        return re.sub(pattern, replace_env_var, content)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Получение конфигурации по умолчанию
        
        Returns:
            Словарь с конфигурацией по умолчанию
        """
        return {
            'data': {
                'provider': 'yfinance',
                'symbols': ['SBER.ME', 'GAZP.ME', 'LKOH.ME', 'NVTK.ME'],
                'update_interval': 60,
                'history_days': 365
            },
            'neural_networks': {
                'models': [
                    {
                        'name': 'deepseek_analyzer',
                        'type': 'deepseek',
                        'weight': 0.5,
                        'enabled': True
                    },
                    {
                        'name': 'xgboost_classifier',
                        'type': 'xgboost',
                        'weight': 0.5,
                        'enabled': True
                    }
                ],
                'analysis_interval': 300,
                'ensemble_method': 'weighted_average'
            },
            'trading': {
                'broker': 'paper',
                'signal_threshold': 0.6,
                'signal_check_interval': 30,
                'max_positions': 10,
                'position_size': 0.1
            },
            'portfolio': {
                'initial_capital': 1000000,
                'max_risk_per_trade': 0.02,
                'max_portfolio_risk': 0.1,
                'update_interval': 300,
                'rebalance_threshold': 0.05
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/investment_system.log',
                'max_size': '10 MB',
                'retention': '30 days'
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """
        Получение конфигурации
        
        Returns:
            Словарь с конфигурацией
        """
        return self.config
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Получение секции конфигурации
        
        Args:
            section: Название секции
            
        Returns:
            Словарь с конфигурацией секции
        """
        return self.config.get(section, {})
    
    def update_config(self, updates: Dict[str, Any]):
        """
        Обновление конфигурации
        
        Args:
            updates: Словарь с обновлениями
        """
        self._deep_update(self.config, updates)
        self._save_config()
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """
        Глубокое обновление словаря
        
        Args:
            base_dict: Базовый словарь
            update_dict: Словарь с обновлениями
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _save_config(self):
        """
        Сохранение конфигурации в файл
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
            logger.info(f"Конфигурация сохранена в {self.config_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")

