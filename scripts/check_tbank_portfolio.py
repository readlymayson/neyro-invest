"""
Скрипт для просмотра полной информации о портфеле в T-Bank sandbox
Показывает: баланс, позиции, операции, доступные средства
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Установка кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

try:
    from tinkoff.invest import AsyncClient
    from tinkoff.invest.constants import INVEST_GRPC_API_SANDBOX
    TINKOFF_AVAILABLE = True
except ImportError:
    TINKOFF_AVAILABLE = False
    print("❌ Библиотека tinkoff-investments не установлена")


def format_money(value) -> str:
    """Форматирование денежного значения"""
    if hasattr(value, 'units') and hasattr(value, 'nano'):
        amount = value.units + value.nano / 1_000_000_000
    else:
        amount = float(value)
    return f"{amount:,.2f}"


def format_quotation(value) -> str:
    """Форматирование Quotation"""
    if hasattr(value, 'units') and hasattr(value, 'nano'):
        amount = value.units + value.nano / 1_000_000_000
    else:
        amount = float(value)
    return f"{amount:,.4f}"


async def get_portfolio_info():
    """Получение полной информации о портфеле"""
    
    if not TINKOFF_AVAILABLE:
        print("❌ Установите библиотеку: pip install tinkoff-investments")
        return
    
    # Получение токена
    token = os.environ.get('TINKOFF_TOKEN')
    if not token:
        # Попытка загрузить из .env
        env_file = '.env'
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                if key.strip() == 'TINKOFF_TOKEN':
                                    token = value.strip().strip('"').strip("'")
                                    break
            except Exception:
                pass
    
    if not token:
        print("❌ TINKOFF_TOKEN не установлен")
        print("Создайте файл .env с содержимым: TINKOFF_TOKEN=ваш_токен")
        return
    
    # Получение account_id из конфига
    account_id = None
    config_file = 'config/test_config.yaml'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'account_id:' in line and '"' in line:
                        account_id = line.split('"')[1]
                        break
        except Exception:
            pass
    
    print("=" * 80)
    print("📊 ПОЛНАЯ ИНФОРМАЦИЯ О ПОРТФЕЛЕ T-BANK SANDBOX")
    print("=" * 80)
    print()
    
    try:
        async with AsyncClient(token, target=INVEST_GRPC_API_SANDBOX) as client:
            
            # 1. Информация о счете
            print("1️⃣  ИНФОРМАЦИЯ О СЧЕТЕ")
            print("-" * 80)
            
            if account_id:
                print(f"Account ID: {account_id}")
            else:
                accounts = await client.users.get_accounts()
                if accounts.accounts:
                    account_id = accounts.accounts[0].id
                    print(f"Account ID: {account_id}")
                else:
                    print("❌ Счета не найдены")
                    return
            
            print()
            
            # 2. Денежные средства
            print("2️⃣  ДЕНЕЖНЫЕ СРЕДСТВА")
            print("-" * 80)
            
            positions_response = await client.sandbox.get_sandbox_positions(
                account_id=account_id
            )
            
            if positions_response.money:
                total_rub = 0
                for money in positions_response.money:
                    amount = format_money(money)
                    currency = money.currency.upper()
                    print(f"  {currency:6s}: {amount:>20s}")
                    if money.currency.lower() == 'rub':
                        total_rub = float(amount.replace(',', ''))
                print()
                print(f"  💰 Доступно для торговли (RUB): {total_rub:,.2f} ₽")
            else:
                print("  Нет денежных средств")
            
            print()
            
            # 3. Портфель (позиции)
            print("3️⃣  ТЕКУЩИЕ ПОЗИЦИИ")
            print("-" * 80)
            
            portfolio_response = await client.sandbox.get_sandbox_portfolio(
                account_id=account_id
            )
            
            if portfolio_response.positions:
                print(f"{'Тикер':<8} {'Кол-во':<10} {'Ср.цена':<15} {'Тек.цена':<15} {'Стоимость':<15} {'P&L %':<10}")
                print("-" * 80)
                
                total_value = 0
                total_pnl = 0
                
                # Получаем маппинг FIGI -> тикер
                shares_response = await client.instruments.shares()
                figi_to_ticker = {share.figi: share.ticker for share in shares_response.instruments}
                
                for position in portfolio_response.positions:
                    ticker = figi_to_ticker.get(position.figi, position.figi[:8])
                    quantity = format_quotation(position.quantity)
                    
                    avg_price = 0
                    if hasattr(position, 'average_position_price'):
                        avg_price_val = format_money(position.average_position_price)
                        avg_price = float(avg_price_val.replace(',', ''))
                    
                    current_price = 0
                    if hasattr(position, 'current_price'):
                        current_price_val = format_money(position.current_price)
                        current_price = float(current_price_val.replace(',', ''))
                    
                    value = float(quantity.replace(',', '')) * current_price
                    total_value += value
                    
                    # Расчет P&L
                    if avg_price > 0:
                        cost = float(quantity.replace(',', '')) * avg_price
                        pnl = ((value - cost) / cost) * 100
                        total_pnl += (value - cost)
                        pnl_str = f"{pnl:+.2f}%"
                    else:
                        pnl_str = "—"
                    
                    print(f"{ticker:<8} {quantity:<10} {avg_price:>14,.2f} {current_price:>14,.2f} {value:>14,.2f} {pnl_str:>10}")
                
                print("-" * 80)
                print(f"{'ИТОГО:':<8} {'':10} {'':15} {'':15} {total_value:>14,.2f} {total_pnl:>+14,.2f}")
                print()
                print(f"  📈 Общая стоимость портфеля: {total_value:,.2f} ₽")
                print(f"  {'📊 Нереализованная прибыль/убыток: ' + f'{total_pnl:+,.2f}'} ₽")
                
            else:
                print("  Нет открытых позиций")
            
            print()
            
            # 4. Общая сводка
            print("4️⃣  ОБЩАЯ СВОДКА")
            print("-" * 80)
            
            if hasattr(portfolio_response, 'total_amount_shares'):
                total_shares = format_money(portfolio_response.total_amount_shares)
                print(f"  Стоимость акций:     {total_shares:>20s} ₽")
            
            if hasattr(portfolio_response, 'total_amount_bonds'):
                total_bonds = format_money(portfolio_response.total_amount_bonds)
                print(f"  Стоимость облигаций: {total_bonds:>20s} ₽")
            
            if hasattr(portfolio_response, 'total_amount_etf'):
                total_etf = format_money(portfolio_response.total_amount_etf)
                print(f"  Стоимость ETF:       {total_etf:>20s} ₽")
            
            if hasattr(portfolio_response, 'expected_yield'):
                expected = format_quotation(portfolio_response.expected_yield)
                print(f"  Ожидаемая доходность: {expected:>19s} ₽")
            
            print()
            
            # 5. Последние операции
            print("5️⃣  ПОСЛЕДНИЕ ОПЕРАЦИИ (за последние 7 дней)")
            print("-" * 80)
            
            from_date = datetime.now() - timedelta(days=7)
            to_date = datetime.now()
            
            operations_response = await client.sandbox.get_sandbox_operations(
                account_id=account_id,
                from_=from_date,
                to=to_date
            )
            
            if operations_response.operations:
                operations = sorted(operations_response.operations, 
                                  key=lambda x: x.date if x.date else datetime.min, 
                                  reverse=True)
                
                print(f"{'Дата':<20} {'Тип':<25} {'Тикер':<8} {'Кол-во':<10} {'Цена':<15} {'Сумма':<15}")
                print("-" * 80)
                
                shown = 0
                for op in operations[:20]:  # Последние 20 операций
                    if op.state.name != 'OPERATION_STATE_EXECUTED':
                        continue
                    
                    date_str = op.date.strftime('%Y-%m-%d %H:%M:%S') if op.date else '—'
                    op_type = op.operation_type.name.replace('OPERATION_TYPE_', '').replace('_', ' ')
                    
                    ticker = '—'
                    if hasattr(op, 'figi') and op.figi:
                        ticker = figi_to_ticker.get(op.figi, op.figi[:8])
                    
                    quantity = str(op.quantity) if hasattr(op, 'quantity') and op.quantity else '—'
                    
                    price_str = '—'
                    if hasattr(op, 'price') and op.price:
                        price_str = format_money(op.price)
                    
                    payment_str = '—'
                    if hasattr(op, 'payment') and op.payment:
                        payment_str = format_money(op.payment)
                    
                    print(f"{date_str:<20} {op_type:<25} {ticker:<8} {quantity:<10} {price_str:<15} {payment_str:<15}")
                    shown += 1
                
                if shown == 0:
                    print("  Нет выполненных операций за последние 7 дней")
                else:
                    print()
                    print(f"  Показано операций: {shown}")
            else:
                print("  Нет операций за последние 7 дней")
            
            print()
            print("=" * 80)
            print("✅ Информация успешно получена")
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(get_portfolio_info())

