"""
Утилита для выбора конфигурации торговой системы
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class ConfigSelector:
    """
    Класс для выбора и управления конфигурациями
    """
    
    def __init__(self):
        """
        Инициализация селектора конфигураций
        """
        self.root_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.root_dir / "config"
        
        # Доступные конфигурации
        self.configs = {
            "1": {
                "name": "Тестовый режим",
                "file": "test_config.yaml",
                "description": "Быстрое тестирование с минимальными интервалами",
                "features": [
                    "Обновление данных: каждые 10 секунд",
                    "Анализ нейросетями: каждые 30 секунд",
                    "Проверка сигналов: каждые 15 секунд",
                    "Интервал между сделками: 1 минута",
                    "Размер позиции: 5% от капитала",
                    "Порог сигнала: 50%"
                ]
            },
            "2": {
                "name": "Стандартный режим",
                "file": "main.yaml",
                "description": "Сбалансированная торговля для большинства пользователей",
                "features": [
                    "Обновление данных: каждые 5 минут",
                    "Анализ нейросетями: каждые 30 минут",
                    "Проверка сигналов: каждые 10 минут",
                    "Интервал между сделками: 1 час",
                    "Размер позиции: 10% от капитала",
                    "Порог сигнала: 60%"
                ]
            },
            "3": {
                "name": "Агрессивная торговля",
                "file": "aggressive_trading.yaml",
                "description": "Активная торговля для опытных трейдеров",
                "features": [
                    "Обновление данных: каждую минуту",
                    "Анализ нейросетями: каждые 5 минут",
                    "Проверка сигналов: каждые 2 минуты",
                    "Интервал между сделками: 30 минут",
                    "Размер позиции: 5% от капитала",
                    "Порог сигнала: 55%"
                ]
            },
            "4": {
                "name": "Консервативное инвестирование",
                "file": "conservative_investing.yaml",
                "description": "Долгосрочное инвестирование с минимальными рисками",
                "features": [
                    "Обновление данных: каждый час",
                    "Анализ нейросетями: каждые 2 часа",
                    "Проверка сигналов: каждый час",
                    "Интервал между сделками: 2 часа",
                    "Размер позиции: 20% от капитала",
                    "Порог сигнала: 75%"
                ]
            }
        }
    
    def show_menu(self) -> None:
        """
        Отображение меню выбора конфигурации
        """
        print("\n" + "="*80)
        print("🎯 ВЫБОР РЕЖИМА ТОРГОВОЙ СИСТЕМЫ")
        print("="*80)
        
        for key, config in self.configs.items():
            print(f"\n{key}. {config['name']}")
            print(f"   📄 Файл: {config['file']}")
            print(f"   📝 {config['description']}")
            print("   ⚙️  Параметры:")
            for feature in config['features']:
                print(f"      • {feature}")
        
        print(f"\n5. Пользовательская конфигурация")
        print(f"   📄 Файл: указать путь вручную")
        print(f"   📝 Использовать собственный файл конфигурации")
        
        print(f"\n0. Выход")
        print("="*80)
    
    def get_user_choice(self) -> Optional[str]:
        """
        Получение выбора пользователя
        
        Returns:
            Путь к выбранному файлу конфигурации или None
        """
        while True:
            try:
                self.show_menu()
                choice = input("\n👉 Выберите режим (0-5): ").strip()
                
                if choice == "0":
                    print("❌ Выход из программы")
                    return None
                
                elif choice in self.configs:
                    config = self.configs[choice]
                    config_path = self.config_dir / config['file']
                    
                    if not config_path.exists():
                        print(f"❌ Файл конфигурации не найден: {config_path}")
                        input("Нажмите Enter для продолжения...")
                        continue
                    
                    print(f"\n✅ Выбран режим: {config['name']}")
                    print(f"📄 Конфигурация: {config_path}")
                    return str(config_path)
                
                elif choice == "5":
                    return self._get_custom_config()
                
                else:
                    print("❌ Неверный выбор. Попробуйте снова.")
                    input("Нажмите Enter для продолжения...")
                    
            except KeyboardInterrupt:
                print("\n❌ Прервано пользователем")
                return None
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                input("Нажмите Enter для продолжения...")
    
    def _get_custom_config(self) -> Optional[str]:
        """
        Получение пути к пользовательской конфигурации
        
        Returns:
            Путь к файлу конфигурации или None
        """
        print("\n📁 Пользовательская конфигурация")
        print("Введите путь к файлу конфигурации (или Enter для отмены):")
        
        try:
            path = input("👉 Путь: ").strip()
            
            if not path:
                return None
            
            config_path = Path(path)
            
            # Если путь относительный, делаем его относительно корневой директории
            if not config_path.is_absolute():
                config_path = self.root_dir / path
            
            if not config_path.exists():
                print(f"❌ Файл не найден: {config_path}")
                input("Нажмите Enter для продолжения...")
                return None
            
            if not config_path.suffix.lower() in ['.yaml', '.yml']:
                print(f"❌ Неверный формат файла. Ожидается .yaml или .yml")
                input("Нажмите Enter для продолжения...")
                return None
            
            print(f"✅ Выбрана пользовательская конфигурация: {config_path}")
            return str(config_path)
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            input("Нажмите Enter для продолжения...")
            return None
    
    def select_config(self) -> Optional[str]:
        """
        Основной метод для выбора конфигурации
        
        Returns:
            Путь к выбранному файлу конфигурации или None
        """
        try:
            # Очистка экрана (работает в Windows и Unix)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("🚀 СИСТЕМА НЕЙРОСЕТЕВЫХ ИНВЕСТИЦИЙ")
            print("Добро пожаловать в систему автоматической торговли!")
            
            return self.get_user_choice()
            
        except Exception as e:
            logger.error(f"Ошибка выбора конфигурации: {e}")
            return None
    
    def get_config_info(self, config_path: str) -> Dict[str, Any]:
        """
        Получение информации о выбранной конфигурации
        
        Args:
            config_path: Путь к файлу конфигурации
            
        Returns:
            Словарь с информацией о конфигурации
        """
        try:
            config_file = Path(config_path).name
            
            # Поиск конфигурации в списке
            for config in self.configs.values():
                if config['file'] == config_file:
                    return {
                        'name': config['name'],
                        'description': config['description'],
                        'features': config['features'],
                        'path': config_path
                    }
            
            # Если не найдена в списке, это пользовательская конфигурация
            return {
                'name': 'Пользовательская конфигурация',
                'description': f'Конфигурация из файла {config_file}',
                'features': ['Параметры определяются содержимым файла'],
                'path': config_path
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о конфигурации: {e}")
            return {
                'name': 'Неизвестная конфигурация',
                'description': 'Не удалось определить тип конфигурации',
                'features': [],
                'path': config_path
            }


def select_trading_config() -> Optional[str]:
    """
    Функция для быстрого выбора конфигурации
    
    Returns:
        Путь к выбранному файлу конфигурации или None
    """
    selector = ConfigSelector()
    return selector.select_config()


if __name__ == "__main__":
    # Тестирование селектора
    config_path = select_trading_config()
    if config_path:
        print(f"\n🎯 Выбранная конфигурация: {config_path}")
    else:
        print("\n❌ Конфигурация не выбрана")
