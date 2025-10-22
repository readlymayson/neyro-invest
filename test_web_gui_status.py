# -*- coding: utf-8 -*-
"""
Тестирование статуса веб-GUI
Проверяет работу API endpoints
"""

import requests
import json
from datetime import datetime

def test_api_endpoints():
    """Тестирование API endpoints"""
    base_url = "http://127.0.0.1:8001"
    
    print("=" * 70)
    print("🧪 ТЕСТИРОВАНИЕ WEB GUI API")
    print("=" * 70)
    print()
    
    # 1. Проверка health
    print("1️⃣  Проверка /api/health...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Статус: {data.get('status')}")
            print(f"   📅 Время: {data.get('timestamp')}")
            print(f"   🔧 Система доступна: {data.get('system_available')}")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
    print()
    
    # 2. Проверка статуса системы
    print("2️⃣  Проверка /api/system/status...")
    try:
        response = requests.get(f"{base_url}/api/system/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Система запущена: {data.get('is_running')}")
            print(f"   🔧 Режим: {data.get('mode')}")
            print(f"   🆔 Account ID: {data.get('account_id', 'N/A')}")
            print(f"   💰 Баланс: {data.get('balance', 0)}")
            print(f"   ⏰ Обновлено: {data.get('last_update')}")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
    print()
    
    # 3. Проверка портфеля
    print("3️⃣  Проверка /api/portfolio...")
    try:
        response = requests.get(f"{base_url}/api/portfolio", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Общая стоимость: {data.get('total_value'):,.0f} ₽")
            print(f"   💵 Наличные: {data.get('cash_balance'):,.0f} ₽")
            print(f"   📈 Инвестировано: {data.get('invested_value'):,.0f} ₽")
            print(f"   📊 P&L: {data.get('total_pnl'):,.0f} ₽ ({data.get('total_pnl_percent', 0):.2f}%)")
            print(f"   📦 Позиций: {data.get('positions_count', 0)}")
            print(f"   ⏰ Обновлено: {data.get('last_update')}")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
    print()
    
    # 4. Проверка сигналов
    print("4️⃣  Проверка /api/signals...")
    try:
        response = requests.get(f"{base_url}/api/signals?limit=5", timeout=5)
        if response.status_code == 200:
            signals = response.json()
            print(f"   ✅ Всего сигналов: {len(signals)}")
            if signals:
                print("\n   Последние сигналы:")
                for sig in signals[:3]:
                    print(f"   - {sig.get('symbol')}: {sig.get('signal')} (уверенность: {sig.get('confidence', 0)*100:.1f}%)")
            else:
                print("   ℹ️  Сигналов пока нет")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
    print()
    
    # 5. Проверка детальной информации
    print("5️⃣  Проверка /api/system/info...")
    try:
        response = requests.get(f"{base_url}/api/system/info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Система запущена: {data.get('is_running')}")
            print(f"   🔧 InvestmentSystem: {data.get('has_investment_system')}")
            print(f"   💼 PortfolioManager: {data.get('has_portfolio_manager')}")
            print(f"   🧠 NetworkManager: {data.get('has_network_manager')}")
            print(f"   ⚡ TradingEngine: {data.get('has_trading_engine')}")
            print(f"   📡 WebSocket подключений: {data.get('active_websockets', 0)}")
            if data.get('start_time'):
                print(f"   ⏱️  Время запуска: {data.get('start_time')}")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
    print()
    
    print("=" * 70)
    print("✅ Тестирование завершено")
    print("=" * 70)


if __name__ == "__main__":
    test_api_endpoints()

