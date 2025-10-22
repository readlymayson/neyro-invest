"""
Скрипт для проверки статуса запущенной торговой системы
Читает экспортированные данные из data/portfolio.json и data/signals.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Установка кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def format_time_ago(timestamp_str: str) -> str:
    """Форматирование времени 'X минут назад'"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        delta = datetime.now() - timestamp
        
        if delta.total_seconds() < 60:
            return f"{int(delta.total_seconds())} сек назад"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)} мин назад"
        elif delta.total_seconds() < 86400:
            return f"{int(delta.total_seconds() / 3600)} ч назад"
        else:
            return f"{int(delta.total_seconds() / 86400)} дн назад"
    except:
        return timestamp_str


def check_system_status():
    """Проверка статуса системы"""
    
    print("=" * 80)
    print("📊 СТАТУС ТОРГОВОЙ СИСТЕМЫ")
    print("=" * 80)
    print()
    
    # Проверка портфеля
    portfolio_file = Path("data/portfolio.json")
    if portfolio_file.exists():
        try:
            with open(portfolio_file, 'r', encoding='utf-8') as f:
                portfolio = json.load(f)
            
            print("1️⃣  ПОРТФЕЛЬ")
            print("-" * 80)
            
            total_value = portfolio.get('total_value', 0)
            cash = portfolio.get('cash_balance', 0)
            timestamp = portfolio.get('timestamp', 'unknown')
            
            print(f"  💰 Общая стоимость:  {total_value:>15,.2f} ₽")
            print(f"  💵 Доступно средств: {cash:>15,.2f} ₽")
            print(f"  ⏰ Обновлено:        {format_time_ago(timestamp)}")
            print()
            
            positions = portfolio.get('positions', {})
            if positions:
                print("  ПОЗИЦИИ:")
                print(f"  {'Тикер':<8} {'Кол-во':<10} {'Цена':<12} {'Стоимость':<15} {'P&L %':<10}")
                print("  " + "-" * 70)
                
                total_pnl = 0
                for symbol, pos in positions.items():
                    quantity = pos.get('quantity', 0)
                    price = pos.get('price', 0)
                    value = pos.get('value', 0)
                    pnl_percent = pos.get('pnl_percent', 0)
                    pnl = pos.get('pnl', 0)
                    total_pnl += pnl
                    
                    pnl_str = f"{pnl_percent:+.2f}%"
                    color = "🟢" if pnl_percent >= 0 else "🔴"
                    
                    print(f"  {symbol:<8} {quantity:<10.0f} {price:<12.2f} {value:<15,.2f} {color} {pnl_str:<10}")
                
                print("  " + "-" * 70)
                print(f"  {'ИТОГО P&L:':<45} {total_pnl:>+15,.2f} ₽")
            else:
                print("  Нет открытых позиций")
            
        except Exception as e:
            print(f"❌ Ошибка чтения портфеля: {e}")
    else:
        print("❌ Файл портфеля не найден (система не запущена?)")
    
    print()
    
    # Проверка сигналов
    signals_file = Path("data/signals.json")
    if signals_file.exists():
        try:
            with open(signals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Сигналы могут быть списком или словарем
            if isinstance(data, list):
                signals = data
                timestamp = 'unknown'
            else:
                signals = data.get('signals', [])
                timestamp = data.get('timestamp', 'unknown')
            
            print("2️⃣  ТОРГОВЫЕ СИГНАЛЫ")
            print("-" * 80)
            print(f"  Всего сигналов: {len(signals)}")
            print(f"  Обновлено: {format_time_ago(timestamp)}")
            print()
            
            if signals:
                # Группируем по типу
                buy_signals = [s for s in signals if s.get('signal') == 'BUY']
                sell_signals = [s for s in signals if s.get('signal') == 'SELL']
                hold_signals = [s for s in signals if s.get('signal') == 'HOLD']
                
                print(f"  🟢 BUY:  {len(buy_signals)}")
                print(f"  🔴 SELL: {len(sell_signals)}")
                print(f"  ⚪ HOLD: {len(hold_signals)}")
                print()
                
                # Показываем активные сигналы (не HOLD)
                active_signals = [s for s in signals if s.get('signal') != 'HOLD']
                if active_signals:
                    print("  АКТИВНЫЕ СИГНАЛЫ:")
                    print(f"  {'Тикер':<8} {'Сигнал':<8} {'Уверенность':<15} {'Источник':<20}")
                    print("  " + "-" * 70)
                    
                    for sig in active_signals[:10]:  # Первые 10
                        symbol = sig.get('symbol', '?')
                        signal = sig.get('signal', '?')
                        confidence = sig.get('confidence', 0) * 100
                        source = sig.get('source', '?')
                        
                        icon = "🟢" if signal == 'BUY' else "🔴"
                        print(f"  {symbol:<8} {icon} {signal:<6} {confidence:>12.1f}% {source:<20}")
                    
                    if len(active_signals) > 10:
                        print(f"  ... и еще {len(active_signals) - 10}")
            
        except Exception as e:
            print(f"❌ Ошибка чтения сигналов: {e}")
    else:
        print("⚠️  Файл сигналов не найден")
    
    print()
    
    # Проверка логов
    log_file = Path("logs/investment_system.log")
    if log_file.exists():
        print("3️⃣  ПОСЛЕДНЯЯ АКТИВНОСТЬ")
        print("-" * 80)
        
        try:
            # Читаем последние строки с обработкой ошибок кодировки
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                last_lines = lines[-5:]  # Последние 5 строк
                
                for line in last_lines:
                    # Убираем ANSI коды
                    clean_line = line.strip()
                    if clean_line:
                        print(f"  {clean_line[:75]}")
        except Exception as e:
            print(f"  ⚠️  Не удалось прочитать логи: {e}")
    
    print()
    print("=" * 80)
    
    # Общая оценка статуса
    if portfolio_file.exists() and signals_file.exists():
        print("✅ СИСТЕМА РАБОТАЕТ")
        print("   Данные обновляются, торговля активна")
    elif portfolio_file.exists():
        print("⚠️  СИСТЕМА ЧАСТИЧНО РАБОТАЕТ")
        print("   Портфель есть, но нет сигналов")
    else:
        print("❌ СИСТЕМА НЕ ЗАПУЩЕНА")
        print("   Запустите: run_web_gui.bat")
    
    print("=" * 80)


if __name__ == '__main__':
    check_system_status()

