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
    
    def __init__(self, config_path: str):
        """
        Инициализация менеджера конфигурации
        
        Args:
            config_path: Путь к конфигурационному файлу
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
    
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
                logger.info(f"Конфигурация загружена из {self.config_path}")
            else:
                logger.warning(f"Файл конфигурации {self.config_path} не найден")
                self.config = self._get_default_config()
                self._save_config()
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            self.config = self._get_default_config()
    
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

