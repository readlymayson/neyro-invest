#!/usr/bin/env python3
"""
Утилита для смены конфигурации торговой системы
"""

import sys
import os
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == "win32":
    import codecs
    import io
    # Создаем новые потоки с правильной кодировкой
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Добавление корневой директории в путь
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from src.utils.config_selector import ConfigSelector


def main():
    """
    Главная функция утилиты смены конфигурации
    """
    try:
        print("🔧 УТИЛИТА СМЕНЫ КОНФИГУРАЦИИ")
        print("Выберите новую конфигурацию для торговой системы\n")
        
        # Создание селектора
        selector = ConfigSelector()
        
        # Выбор конфигурации
        selected_config = selector.select_config()
        
        if selected_config:
            # Получение информации о выбранной конфигурации
            config_info = selector.get_config_info(selected_config)
            
            print(f"\n✅ Выбрана конфигурация: {config_info['name']}")
            print(f"📄 Файл: {selected_config}")
            print(f"📝 Описание: {config_info['description']}")
            
            print(f"\n⚙️ Параметры:")
            for feature in config_info['features']:
                print(f"   • {feature}")
            
            print(f"\n🚀 Для запуска с этой конфигурацией используйте:")
            print(f"   python run.py --config \"{selected_config}\"")
            
            # Предложение сохранить как основную конфигурацию
            if selected_config != str(root_dir / "config" / "main.yaml"):
                print(f"\n💾 Хотите сделать эту конфигурацию основной? (y/N): ", end="")
                choice = input().strip().lower()
                
                if choice in ['y', 'yes', 'да', 'д']:
                    try:
                        import shutil
                        main_config = root_dir / "config" / "main.yaml"
                        backup_config = root_dir / "config" / "main.yaml.backup"
                        
                        # Создание резервной копии
                        if main_config.exists():
                            shutil.copy2(main_config, backup_config)
                            print(f"📋 Создана резервная копия: {backup_config}")
                        
                        # Копирование новой конфигурации
                        shutil.copy2(selected_config, main_config)
                        print(f"✅ Конфигурация сохранена как основная: {main_config}")
                        print(f"🚀 Теперь можно запускать просто: python run.py")
                        
                    except Exception as e:
                        print(f"❌ Ошибка сохранения конфигурации: {e}")
                else:
                    print("📝 Конфигурация не сохранена как основная")
            
        else:
            print("❌ Конфигурация не выбрана")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n❌ Прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
