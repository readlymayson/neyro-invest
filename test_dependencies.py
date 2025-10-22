#!/usr/bin/env python3
"""
Тест зависимостей для проекта нейро-инвестиций
"""

def test_imports():
    """Тестирует импорт основных зависимостей"""
    print("Тестирование импорта зависимостей...")
    print("-" * 40)
    
    dependencies = [
        ("numpy", "Численные вычисления"),
        ("pandas", "Работа с данными"),
        ("sklearn", "Машинное обучение (scikit-learn)"),
        ("xgboost", "XGBoost алгоритм"),
        ("yfinance", "Получение финансовых данных"),
        ("requests", "HTTP запросы"),
        ("loguru", "Логирование"),
        ("matplotlib", "Графики"),
        ("seaborn", "Статистические графики"),
        ("sqlalchemy", "База данных"),
        ("yaml", "YAML конфигурация"),
        ("dotenv", "Переменные окружения")
    ]
    
    results = []
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {module_name:<12} - {description}")
            results.append((module_name, True, ""))
        except ImportError as e:
            print(f"✗ {module_name:<12} - {description}")
            print(f"  Ошибка: {e}")
            results.append((module_name, False, str(e)))
        except Exception as e:
            print(f"? {module_name:<12} - {description}")
            print(f"  Неожиданная ошибка: {e}")
            results.append((module_name, False, str(e)))
    
    print("-" * 40)
    
    # Статистика
    total = len(results)
    installed = sum(1 for _, success, _ in results if success)
    
    print(f"Установлено: {installed}/{total}")
    
    if installed == total:
        print("🎉 Все зависимости установлены!")
    else:
        print("⚠️  Некоторые зависимости отсутствуют.")
        print("\nНеустановленные зависимости:")
        for module_name, success, error in results:
            if not success:
                print(f"  - {module_name}: {error}")
    
    return results

def test_xgboost_functionality():
    """Тестирует функциональность XGBoost"""
    print("\nТестирование XGBoost...")
    print("-" * 40)
    
    try:
        import xgboost as xgb
        import numpy as np
        import pandas as pd
        
        # Создаем тестовые данные
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 3, 100)
        
        # Создаем и обучаем модель
        model = xgb.XGBClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        # Тестируем предсказание
        predictions = model.predict(X[:10])
        probabilities = model.predict_proba(X[:10])
        
        print("✓ XGBoost модель создана и обучена")
        print(f"✓ Предсказания: {predictions}")
        print(f"✓ Вероятности: {probabilities[0]}")
        print("✓ XGBoost работает корректно!")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования XGBoost: {e}")
        return False

def main():
    print("=" * 60)
    print("ТЕСТ ЗАВИСИМОСТЕЙ ПРОЕКТА НЕЙРО-ИНВЕСТИЦИЙ")
    print("=" * 60)
    
    # Тест импортов
    results = test_imports()
    
    # Тест XGBoost функциональности
    if any(name == "xgboost" and success for name, success, _ in results):
        test_xgboost_functionality()
    
    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)

if __name__ == "__main__":
    main()

