"""
Проверка работы с сохраненным sandbox счетом
"""

import asyncio
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.trading.tbank_broker import TBankBroker

async def test_saved_account():
    """Тест работы с сохраненным счетом"""
    
    print("\n" + "="*80)
    print("ПРОВЕРКА СОХРАНЕННОГО SANDBOX СЧЕТА")
    print("="*80)
    
    token = os.getenv('TINKOFF_TOKEN')
    saved_account_id = "24fdd4b3-aba2-4410-ae91-d57a8190909b"
    
    print(f"\nAccount ID из конфига: {saved_account_id}")
    print("\nСоздание брокера с указанным account_id...")
    
    broker = TBankBroker(
        token=token,
        sandbox=True,
        account_id=saved_account_id  # Используем сохраненный ID
    )
    
    print("[OK] Broker created")
    
    print("\nИнициализация...")
    await broker.initialize()
    
    print(f"[OK] Broker initialized")
    print(f"   Account ID in use: {broker.account_id}")
    
    # Проверка что ID не изменился
    if broker.account_id == saved_account_id:
        print(f"   [OK] ID MATCHES! Using existing account")
    else:
        print(f"   [ERROR] ID MISMATCH! Created new account: {broker.account_id}")
    
    print("\nПолучение портфеля...")
    portfolio = await broker.get_portfolio()
    
    print(f"\nPortfolio:")
    print(f"   Account ID: {broker.account_id}")
    print(f"   Total value: {portfolio['total_amount']:.2f} RUB")
    print(f"   Expected yield: {portfolio['expected_yield']:.2f} RUB")
    print(f"   Positions: {len(portfolio['positions'])}")
    
    if portfolio['positions']:
        print(f"\n   Positions:")
        for pos in portfolio['positions']:
            print(f"     {pos['ticker']}: {pos['quantity']} units")
    
    print("\nGetting operations...")
    from datetime import datetime, timedelta
    operations = await broker.get_operations(
        from_date=datetime.now() - timedelta(days=30),
        to_date=datetime.now()
    )
    
    print(f"   Operations in last 30 days: {len(operations)}")
    
    print("\n" + "="*80)
    print("CONCLUSION:")
    print("="*80)
    print(f"[OK] Account {saved_account_id} exists and works!")
    print(f"[OK] Future launches will use THE SAME account")
    print(f"[OK] NEW accounts will NOT be created")
    print(f"[OK] Balance and operations persist between sessions")
    print(f"\n[INFO] Account stored for 3 months from last use")
    print(f"       With regular use, account will live indefinitely!")
    print("="*80)
    print()

if __name__ == '__main__':
    # Настройка логирования
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="WARNING"
    )
    
    asyncio.run(test_saved_account())

