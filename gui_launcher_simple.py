#!/usr/bin/env python3
"""
Упрощенный launcher для GUI (работает с минимальными зависимостями)
"""

import sys
import os
from pathlib import Path

# Добавление корневой директории проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def show_startup_info():
    """Показ информации о запуске"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║              Нейросетевая система инвестиций                 ║")
    print("║                     Версия 1.0.0                            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print("Запуск графического интерфейса...")
    print()

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print(f"Ошибка: Требуется Python 3.8 или выше")
        print(f"Текущая версия: {sys.version}")
        return False
    return True

def check_tkinter():
    """Проверка наличия tkinter"""
    try:
        import tkinter
        return True
    except ImportError:
        print("Ошибка: tkinter не найден")
        print("Установите tkinter для вашей системы:")
        print("- Ubuntu/Debian: sudo apt-get install python3-tk")
        print("- CentOS/RHEL: sudo yum install tkinter")
        print("- Windows: tkinter включен в стандартную установку Python")
        return False

def create_directories():
    """Создание необходимых директорий"""
    try:
        directories = ["logs", "data", "models", "config"]
        for dir_name in directories:
            dir_path = project_root / dir_name
            dir_path.mkdir(exist_ok=True)
        return True
    except Exception as e:
        print(f"Ошибка создания директорий: {e}")
        return False

def main():
    """Главная функция"""
    try:
        show_startup_info()
        
        # Проверка версии Python
        if not check_python_version():
            input("Нажмите Enter для выхода...")
            return 1
        
        # Проверка tkinter
        if not check_tkinter():
            input("Нажмите Enter для выхода...")
            return 1
        
        # Создание директорий
        if not create_directories():
            print("Предупреждение: Не удалось создать некоторые директории")
        
        # Попытка импорта GUI модулей
        try:
            from src.gui.main_window import MainWindow
            print("✓ GUI модули загружены успешно")
        except ImportError as e:
            print(f"Ошибка импорта GUI модулей: {e}")
            print("\nВозможные решения:")
            print("1. Установите зависимости: python install_gui_deps.py")
            print("2. Или используйте: pip install numpy pandas matplotlib loguru pyyaml")
            input("Нажмите Enter для выхода...")
            return 1
        
        # Настройка базового логирования
        try:
            from loguru import logger
            logs_dir = project_root / "logs"
            logger.add(logs_dir / "gui_simple.log", rotation="10 MB", retention="7 days")
        except ImportError:
            print("Предупреждение: loguru не найден, логирование отключено")
        
        # Запуск GUI
        print("Запуск главного окна...")
        try:
            main_window = MainWindow()
            main_window.run()
            print("GUI завершен нормально")
            return 0
        except Exception as e:
            print(f"Ошибка запуска GUI: {e}")
            
            # Показ простого сообщения об ошибке
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror(
                    "Ошибка запуска", 
                    f"Не удалось запустить GUI:\n\n{e}"
                )
                root.destroy()
            except Exception:
                pass
            
            return 1
    
    except KeyboardInterrupt:
        print("\nЗапуск прерван пользователем")
        return 0
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
