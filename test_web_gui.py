"""
Простой тест Web GUI
"""

print("=" * 70)
print("ТЕСТ WEB GUI")
print("=" * 70)

# Тест 1: Импорт модуля
print("\n[1/4] Проверка импорта...")
try:
    from src.gui.web_app import app
    print("✓ Модуль web_app импортирован успешно")
except Exception as e:
    print(f"✗ Ошибка импорта: {e}")
    exit(1)

# Тест 2: Проверка app
print("\n[2/4] Проверка приложения...")
try:
    print(f"✓ App создан: {app.title}")
    print(f"✓ Версия: {app.version}")
except Exception as e:
    print(f"✗ Ошибка: {e}")
    exit(1)

# Тест 3: Проверка routes
print("\n[3/4] Проверка routes...")
try:
    routes = [route.path for route in app.routes]
    print(f"✓ Найдено {len(routes)} routes")
    
    important_routes = ['/api/health', '/api/system/status', '/api/portfolio', '/api/signals']
    for route in important_routes:
        if route in routes:
            print(f"  ✓ {route}")
        else:
            print(f"  ✗ {route} - НЕ НАЙДЕН!")
except Exception as e:
    print(f"✗ Ошибка: {e}")
    exit(1)

# Тест 4: Запуск сервера
print("\n[4/4] Запуск тестового сервера...")
try:
    import uvicorn
    print("✓ Uvicorn доступен")
    print("\nЗапуск сервера на http://127.0.0.1:8000...")
    print("Нажмите Ctrl+C для остановки")
    print("=" * 70)
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    
except KeyboardInterrupt:
    print("\n\n✓ Сервер остановлен")
except Exception as e:
    print(f"\n✗ Ошибка запуска: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

