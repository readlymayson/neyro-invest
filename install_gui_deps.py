#!/usr/bin/env python3
"""
Скрипт установки зависимостей для GUI
"""

import subprocess
import sys
import os

def install_package(package):
    """
    Установка пакета через pip
    
    Args:
        package: Имя пакета для установки
        
    Returns:
        bool: True если установка успешна
    """
    try:
        print(f"Установка {package}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package, "--quiet"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"[OK] {package} установлен успешно")
            return True
        else:
            print(f"[FAIL] Ошибка установки {package}: {result.stderr}")
            return False
    except Exception as e:
        print(f"[FAIL] Ошибка установки {package}: {e}")
        return False

def main():
    """
    Главная функция установки
    """
    print("Установка зависимостей для GUI системы нейросетевых инвестиций")
    print("=" * 60)
    
    # Критически важные пакеты
    critical_packages = [
        "numpy",
        "pandas", 
        "matplotlib",
        "loguru",
        "pyyaml",
        "requests"
    ]
    
    # Дополнительные пакеты
    optional_packages = [
        "pillow",
        "psutil",
        "yfinance"
    ]
    
    print("\nУстановка критически важных пакетов:")
    critical_success = 0
    for package in critical_packages:
        if install_package(package):
            critical_success += 1
    
    print(f"\nКритические пакеты: {critical_success}/{len(critical_packages)} установлены")
    
    if critical_success < len(critical_packages):
        print("[WARNING] Не все критические пакеты установлены!")
        print("GUI может работать некорректно.")
    
    print("\nУстановка дополнительных пакетов:")
    optional_success = 0
    for package in optional_packages:
        if install_package(package):
            optional_success += 1
    
    print(f"\nДополнительные пакеты: {optional_success}/{len(optional_packages)} установлены")
    
    total_success = critical_success + optional_success
    total_packages = len(critical_packages) + len(optional_packages)
    
    print("\n" + "=" * 60)
    print(f"Установка завершена: {total_success}/{total_packages} пакетов")
    
    if critical_success == len(critical_packages):
        print("[SUCCESS] GUI готов к запуску!")
        return 0
    else:
        print("[ERROR] Установка критических пакетов не завершена")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nНажмите Enter для выхода...")
    sys.exit(exit_code)
