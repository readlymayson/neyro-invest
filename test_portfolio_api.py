# -*- coding: utf-8 -*-
"""
Тестирование API портфеля
Проверяет, какие данные возвращает /api/portfolio
"""

import requests
import json
from datetime import datetime

def test_portfolio_api():
    """Тестирование API портфеля"""
    base_url = "http://127.0.0.1:8000"
    
    print("=" * 70)
    print("ТЕСТИРОВАНИЕ API ПОРТФЕЛЯ")
    print("=" * 70)
    print()
    
    try:
        response = requests.get(f"{base_url}/api/portfolio", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            print("Данные портфеля получены:")
            print(f"   Режим: {data.get('mode', 'неизвестно')}")
            print(f"   Общая стоимость: {data.get('total_value', 0):,.2f} руб")
            print(f"   Наличные: {data.get('cash_balance', 0):,.2f} руб")
            print(f"   Инвестировано: {data.get('invested_value', 0):,.2f} руб")
            print(f"   P&L: {data.get('total_pnl', 0):,.2f} руб ({data.get('total_pnl_percent', 0):.2f}%)")
            print(f"   Позиций: {data.get('positions_count', 0)}")
            print(f"   Обновлено: {data.get('last_update')}")
            
            if data.get('positions'):
                print("\nПозиции:")
                for i, pos in enumerate(data['positions'][:5], 1):
                    print(f"   {i}. {pos.get('symbol', 'N/A')}: {pos.get('quantity', 0)} шт, "
                          f"цена {pos.get('current_price', 0):.2f} руб, "
                          f"P&L {pos.get('pnl', 0):.2f} руб ({pos.get('pnl_percent', 0):.2f}%)")
            
            print("\n" + "=" * 70)
            print("Тест завершен успешно")
            print("=" * 70)
            
        else:
            print(f"Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            
    except Exception as e:
        print(f"Ошибка подключения: {e}")

if __name__ == "__main__":
    test_portfolio_api()
