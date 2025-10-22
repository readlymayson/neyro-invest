#!/usr/bin/env python3
"""
Скрипт для перезапуска виртуального окружения
Удаляет старое venv и создает новое с чистой установкой зависимостей
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_header():
    """Печать заголовка"""
    print("=" * 60)
    print("              Перезапуск виртуального окружения")
    print("                     Система инвестиций")
    print("=" * 60)
    print()

def check_python():
    """Проверка версии Python"""
    print("Проверка версии Python...")
    if sys.version_info < (3, 8):
        print(f"[ERROR] Ошибка: Требуется Python 3.8 или выше")
        print(f"Текущая версия: {sys.version}")
        return False
    
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - OK")
    return True

def remove_old_venv():
    """Удаление старого виртуального окружения"""
    print("\nУдаление старого виртуального окружения...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        try:
            shutil.rmtree(venv_path)
            print("[OK] Старое виртуальное окружение удалено")
        except Exception as e:
            print(f"[ERROR] Ошибка удаления venv: {e}")
            return False
    else:
        print("[INFO] Старое виртуальное окружение не найдено")
    
    return True

def create_new_venv():
    """Создание нового виртуального окружения"""
    print("\nСоздание нового виртуального окружения...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "venv", "venv"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[OK] Новое виртуальное окружение создано")
            return True
        else:
            print(f"[ERROR] Ошибка создания venv: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Ошибка создания venv: {e}")
        return False

def get_venv_commands():
    """Получение команд активации для разных ОС"""
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate.bat"
        pip_cmd = "venv\\Scripts\\pip.exe"
        python_cmd = "venv\\Scripts\\python.exe"
    else:  # Linux/macOS
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    return activate_cmd, pip_cmd, python_cmd

def upgrade_pip():
    """Обновление pip в виртуальном окружении"""
    print("\nОбновление pip...")
    
    _, pip_cmd, _ = get_venv_commands()
    
    try:
        result = subprocess.run([
            pip_cmd, "install", "--upgrade", "pip"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[OK] pip обновлен")
            return True
        else:
            print(f"[WARNING] Предупреждение: не удалось обновить pip: {result.stderr}")
            return True  # Не критично
    except Exception as e:
        print(f"[WARNING] Предупреждение: ошибка обновления pip: {e}")
        return True  # Не критично

def install_dependencies():
    """Установка зависимостей"""
    print("\nУстановка зависимостей...")
    
    _, pip_cmd, _ = get_venv_commands()
    
    # Список файлов зависимостей для попытки установки
    requirements_files = [
        "requirements_gui_minimal.txt",
        "requirements_gui.txt", 
        "requirements_minimal.txt",
        "requirements.txt"
    ]
    
    installed = False
    
    for req_file in requirements_files:
        if Path(req_file).exists():
            print(f"Попытка установки из {req_file}...")
            try:
                result = subprocess.run([
                    pip_cmd, "install", "-r", req_file
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"[OK] Зависимости установлены из {req_file}")
                    installed = True
                    break
                else:
                    print(f"[ERROR] Ошибка установки из {req_file}: {result.stderr}")
            except Exception as e:
                print(f"[ERROR] Ошибка установки из {req_file}: {e}")
    
    if not installed:
        print("Попытка установки базовых зависимостей...")
        basic_packages = ["numpy", "pandas", "matplotlib", "loguru", "pyyaml", "requests"]
        
        for package in basic_packages:
            try:
                result = subprocess.run([
                    pip_cmd, "install", package
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"[OK] {package} установлен")
                else:
                    print(f"[ERROR] Ошибка установки {package}")
            except Exception as e:
                print(f"[ERROR] Ошибка установки {package}: {e}")
    
    return installed

def verify_installation():
    """Проверка установки"""
    print("\nПроверка установки...")
    
    _, _, python_cmd = get_venv_commands()
    
    test_imports = [
        ("tkinter", "GUI framework"),
        ("numpy", "Numerical computing"),
        ("pandas", "Data analysis"),
        ("matplotlib", "Plotting"),
        ("loguru", "Logging"),
        ("yaml", "YAML parsing")
    ]
    
    success_count = 0
    
    for module, description in test_imports:
        try:
            result = subprocess.run([
                python_cmd, "-c", f"import {module}; print('{module} OK')"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"[OK] {module} ({description}) - OK")
                success_count += 1
            else:
                print(f"[ERROR] {module} ({description}) - ОШИБКА")
        except Exception as e:
            print(f"[ERROR] {module} ({description}) - ОШИБКА: {e}")
    
    print(f"\nРезультат: {success_count}/{len(test_imports)} модулей работают")
    return success_count >= 3  # Минимум 3 модуля должны работать

def show_usage_instructions():
    """Показ инструкций по использованию"""
    print("\n" + "="*60)
    print("ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ")
    print("="*60)
    
    activate_cmd, _, _ = get_venv_commands()
    
    print(f"\n1. Активация виртуального окружения:")
    if os.name == 'nt':
        print(f"   {activate_cmd}")
    else:
        print(f"   {activate_cmd}")
    
    print(f"\n2. Запуск GUI:")
    print(f"   python gui_launcher_simple.py")
    print(f"   # или")
    print(f"   python gui_launcher.py")
    
    print(f"\n3. Запуск через скрипты:")
    if os.name == 'nt':
        print(f"   run_gui.bat")
    else:
        print(f"   ./run_gui.sh")
    
    print(f"\n4. Деактивация окружения:")
    print(f"   deactivate")

def main():
    """Главная функция"""
    try:
        print_header()
        
        # Проверка Python
        if not check_python():
            return 1
        
        # Удаление старого venv
        if not remove_old_venv():
            return 1
        
        # Создание нового venv
        if not create_new_venv():
            return 1
        
        # Обновление pip
        upgrade_pip()
        
        # Установка зависимостей
        if not install_dependencies():
            print("[WARNING] Предупреждение: не все зависимости установлены")
        
        # Проверка установки
        if verify_installation():
            print("\n[SUCCESS] Виртуальное окружение успешно перезапущено!")
            show_usage_instructions()
            return 0
        else:
            print("\n[WARNING] Виртуальное окружение создано, но некоторые модули не работают")
            print("Попробуйте установить зависимости вручную:")
            print("pip install numpy pandas matplotlib loguru pyyaml")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n[ERROR] Операция прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    
    if exit_code == 0:
        print("\n[SUCCESS] Готово! Теперь можно запускать GUI.")
    else:
        print("\n[ERROR] Произошли ошибки. Проверьте сообщения выше.")
    
    input("\nНажмите Enter для выхода...")
    sys.exit(exit_code)
