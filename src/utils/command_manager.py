"""
Менеджер внутренних команд системы
Позволяет выполнять команды через help и интерактивный интерфейс
"""

import asyncio
import sys
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from loguru import logger
from dataclasses import dataclass
from enum import Enum

class CommandType(Enum):
    """Типы команд"""
    INFO = "info"           # Информационные команды
    TRADE = "trade"         # Торговые команды
    ANALYSIS = "analysis"   # Аналитические команды
    SYSTEM = "system"       # Системные команды
    EMERGENCY = "emergency" # Экстренные команды

@dataclass
class Command:
    """Класс команды"""
    name: str
    description: str
    command_type: CommandType
    handler: Callable
    requires_system: bool = False
    requires_broker: bool = False
    requires_portfolio: bool = False

class CommandManager:
    """
    Менеджер внутренних команд системы
    """
    
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.system = None
        self.portfolio = None
        self._register_commands()
    
    def set_system_components(self, system=None, portfolio=None):
        """Установка компонентов системы"""
        self.system = system
        self.portfolio = portfolio
        logger.info("Компоненты системы установлены в CommandManager")
    
    def _register_commands(self):
        """Регистрация всех команд"""
        
        # Информационные команды
        self._register_command(
            "help", 
            "Показать список всех доступных команд",
            CommandType.INFO,
            self._cmd_help
        )
        
        self._register_command(
            "portfolio", 
            "Показать информацию о портфеле",
            CommandType.INFO,
            self._cmd_portfolio,
            requires_portfolio=True
        )
        
        self._register_command(
            "balance", 
            "Показать баланс счета",
            CommandType.INFO,
            self._cmd_balance,
            requires_broker=True
        )
        
        self._register_command(
            "positions", 
            "Показать текущие позиции",
            CommandType.INFO,
            self._cmd_positions,
            requires_portfolio=True
        )
        
        self._register_command(
            "cooldowns", 
            "Показать отчет по кулдаунам",
            CommandType.INFO,
            self._cmd_cooldowns,
            requires_system=True
        )
        
        self._register_command(
            "status", 
            "Показать статус системы",
            CommandType.INFO,
            self._cmd_status,
            requires_system=True
        )
        
        # Торговые команды
        self._register_command(
            "analyze", 
            "Запустить анализ рынка (без ожидания интервала)",
            CommandType.TRADE,
            self._cmd_analyze,
            requires_system=True
        )
        
        self._register_command(
            "trade", 
            "Запустить торговлю (без ожидания интервала)",
            CommandType.TRADE,
            self._cmd_trade,
            requires_system=True
        )
        
        self._register_command(
            "sell_all", 
            "Продать все позиции в портфеле",
            CommandType.EMERGENCY,
            self._cmd_sell_all,
            requires_system=True,
            requires_portfolio=True
        )
        
        self._register_command(
            "buy", 
            "Купить инструмент (buy SYMBOL QUANTITY)",
            CommandType.TRADE,
            self._cmd_buy,
            requires_system=True,
            requires_portfolio=True
        )
        
        self._register_command(
            "sell", 
            "Продать инструмент (sell SYMBOL QUANTITY)",
            CommandType.TRADE,
            self._cmd_sell,
            requires_system=True,
            requires_portfolio=True
        )
        
        # Аналитические команды
        self._register_command(
            "signals", 
            "Показать последние торговые сигналы",
            CommandType.ANALYSIS,
            self._cmd_signals,
            requires_system=True
        )
        
        self._register_command(
            "models", 
            "Показать статус моделей нейросетей",
            CommandType.ANALYSIS,
            self._cmd_models,
            requires_system=True
        )
        
        # Системные команды
        self._register_command(
            "restart", 
            "Перезапустить систему",
            CommandType.SYSTEM,
            self._cmd_restart,
            requires_system=True
        )
        
        self._register_command(
            "stop", 
            "Остановить торговлю",
            CommandType.SYSTEM,
            self._cmd_stop,
            requires_system=True
        )
        
        self._register_command(
            "start", 
            "Запустить торговлю",
            CommandType.SYSTEM,
            self._cmd_start,
            requires_system=True
        )
        
        logger.info(f"Зарегистрировано {len(self.commands)} команд")
    
    def _register_command(self, name: str, description: str, command_type: CommandType, 
                         handler: Callable, requires_system: bool = False, 
                         requires_broker: bool = False, requires_portfolio: bool = False):
        """Регистрация команды"""
        self.commands[name] = Command(
            name=name,
            description=description,
            command_type=command_type,
            handler=handler,
            requires_system=requires_system,
            requires_broker=requires_broker,
            requires_portfolio=requires_portfolio
        )
    
    async def execute_command(self, command_line: str) -> bool:
        """
        Выполнение команды
        
        Args:
            command_line: Строка команды
            
        Returns:
            True если команда выполнена успешно
        """
        try:
            parts = command_line.strip().split()
            if not parts:
                return False
            
            command_name = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            if command_name not in self.commands:
                logger.warning(f"Неизвестная команда: {command_name}")
                await self._cmd_help()
                return False
            
            command = self.commands[command_name]
            
            # Проверка требований
            if command.requires_system and not self.system:
                logger.error("Команда требует инициализированную систему")
                return False
            
            if command.requires_portfolio and not self.portfolio:
                logger.error("Команда требует инициализированный портфель")
                return False
            
            # Выполнение команды
            logger.info(f"Выполнение команды: {command_name}")
            result = await command.handler(args)
            return result
            
        except Exception as e:
            logger.error(f"Ошибка выполнения команды '{command_line}': {e}")
            return False
    
    async def _cmd_help(self, args: List[str] = None) -> bool:
        """Показать справку по командам"""
        print("\n" + "="*60)
        print("📋 ДОСТУПНЫЕ КОМАНДЫ СИСТЕМЫ NEYRO-INVEST")
        print("="*60)
        
        # Группировка команд по типам
        command_groups = {}
        for cmd in self.commands.values():
            if cmd.command_type.value not in command_groups:
                command_groups[cmd.command_type.value] = []
            command_groups[cmd.command_type.value].append(cmd)
        
        # Вывод команд по группам
        for group_name, commands in command_groups.items():
            print(f"\n🔹 {group_name.upper()} КОМАНДЫ:")
            for cmd in commands:
                print(f"  {cmd.name:<15} - {cmd.description}")
        
        print("\n" + "="*60)
        print("💡 Использование: введите команду в интерактивном режиме")
        print("💡 Примеры: help, portfolio, analyze, trade, sell_all")
        print("="*60)
        return True
    
    async def _cmd_portfolio(self, args: List[str] = None) -> bool:
        """Показать информацию о портфеле"""
        try:
            if not self.portfolio:
                logger.error("Портфель не инициализирован")
                return False
            
            print("\n" + "="*60)
            print("📊 ИНФОРМАЦИЯ О ПОРТФЕЛЕ")
            print("="*60)
            
            # Проверяем тип брокера
            if hasattr(self.system, 'trading_engine') and self.system.trading_engine:
                broker_type = self.system.trading_engine.broker_type
                
                if broker_type in ['tbank', 'tinkoff']:
                    # Используем PortfolioManager как единый источник данных
                    print("🏦 Получение данных через PortfolioManager...")
                    
                    try:
                        # Синхронизация с T-Bank (если необходимо)
                        if hasattr(self.portfolio, 'tbank_broker') and self.portfolio.tbank_broker:
                            await self.portfolio.sync_with_tbank()
                        
                        # Получение метрик портфеля
                        metrics = await self.portfolio.get_portfolio_metrics()
                        if metrics:
                            print(f"💰 Общая стоимость: {metrics.total_value:,.2f} ₽")
                            print(f"💵 Денежные средства: {metrics.cash_balance:,.2f} ₽")
                            print(f"📈 Инвестировано: {metrics.invested_value:,.2f} ₽")
                            print(f"📊 Общий P&L: {metrics.total_pnl:+,.2f} ₽ ({metrics.total_pnl_percent:+.2f}%)")
                            print(f"✅ Реализованный P&L: {metrics.realized_pnl:+,.2f} ₽ ({metrics.realized_pnl_percent:+.2f}%)")
                            print(f"⏳ Нереализованный P&L: {metrics.unrealized_pnl:+,.2f} ₽ ({metrics.unrealized_pnl_percent:+.2f}%)")
                            print(f"📈 Дневной P&L: {metrics.daily_pnl:+,.2f} ₽ ({metrics.daily_pnl_percent:+.2f}%)")
                        else:
                            print("❌ Метрики портфеля недоступны")
                            return False
                        
                        # Позиции
                        positions = await self.portfolio.get_positions()
                        if positions:
                            print(f"\n📋 ПОЗИЦИИ ({len(positions)}):")
                            print(f"{'Тикер':<8} {'Акции':<10} {'Лоты':<8} {'Ср.цена':<12} {'Тек.цена':<12} {'Стоимость':<12} {'P&L %':>8}")
                            print("-" * 70)
                            for pos in positions:
                                # Получаем размер лота для инструмента
                                lot_size = 1  # По умолчанию
                                if hasattr(self.system.trading_engine, 'tbank_broker') and self.system.trading_engine.tbank_broker:
                                    lot_size = self.system.trading_engine.tbank_broker.get_lot_size(pos.symbol)
                                
                                # Рассчитываем количество лотов
                                shares = abs(pos.quantity)
                                lots = shares / lot_size if lot_size > 0 else shares
                                
                                print(f"{pos.symbol:<8} {shares:<10.0f} {lots:<8.1f} {pos.average_price:<12.2f} "
                                      f"{pos.current_price:<12.2f} {pos.market_value:<12.2f} {pos.unrealized_pnl_percent:>+7.2f}%")
                        else:
                            print("\n📋 Нет открытых позиций")
                        
                        # История операций (последние 10)
                        if hasattr(self.portfolio, 'transactions') and self.portfolio.transactions:
                            print(f"\n📜 ПОСЛЕДНИЕ ОПЕРАЦИИ ({min(10, len(self.portfolio.transactions))}):")
                            print(f"{'Время':<20} {'Тип':<8} {'Символ':<8} {'Кол-во':<10} {'Цена':<12} {'Сумма':<15}")
                            print("-" * 80)
                            
                            # Сортируем по времени (новые сверху) и берем последние 10
                            recent_transactions = sorted(self.portfolio.transactions, key=lambda x: x.timestamp, reverse=True)[:10]
                            
                            for txn in recent_transactions:
                                time_str = txn.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                                txn_type = "ПОКУПКА" if txn.type.value == "buy" else "ПРОДАЖА" if txn.type.value == "sell" else txn.type.value.upper()
                                total_amount = txn.quantity * txn.price
                                
                                print(f"{time_str:<20} {txn_type:<8} {txn.symbol:<8} {txn.quantity:<10.2f} "
                                      f"{txn.price:<12.2f} {total_amount:<15.2f}")
                        else:
                            print("\n📜 Нет операций")
                        
                    except Exception as e:
                        logger.error(f"Ошибка получения данных портфеля: {e}")
                        print("❌ Не удалось получить данные портфеля")
                        return False
                        
                else:
                    # Локальный портфель для paper брокера
                    print("📄 Использование локального портфеля...")
                    
                    # Получение метрик портфеля
                    metrics = await self.portfolio.get_portfolio_metrics()
                    if metrics:
                        print(f"💰 Общая стоимость: {metrics.total_value:,.2f} ₽")
                        print(f"💵 Денежные средства: {metrics.cash_balance:,.2f} ₽")
                        print(f"📈 Инвестировано: {metrics.invested_value:,.2f} ₽")
                        print(f"📊 P&L: {metrics.total_pnl:+,.2f} ₽ ({metrics.total_pnl_percent:+.2f}%)")
                        print(f"📈 Дневной P&L: {metrics.daily_pnl:+,.2f} ₽ ({metrics.daily_pnl_percent:+.2f}%)")
                    else:
                        print("❌ Метрики портфеля недоступны")
                        return False
                    
                    # Позиции
                    positions = await self.portfolio.get_positions()
                    if positions:
                        print(f"\n📋 ПОЗИЦИИ ({len(positions)}):")
                        print(f"{'Тикер':<8} {'Кол-во':<10} {'Цена':<12} {'Стоимость':<12} {'P&L %':>8}")
                        print("-" * 60)
                        for pos in positions:
                            print(f"{pos.symbol:<8} {pos.quantity:<10.2f} "
                                  f"{pos.current_price:<12.2f} {pos.market_value:<12.2f} "
                                  f"{pos.unrealized_pnl_percent:>+7.2f}%")
                    else:
                        print("\n📋 Нет открытых позиций")
                    
                    # История операций для локального портфеля
                    if hasattr(self.portfolio, 'transactions') and self.portfolio.transactions:
                        print(f"\n📜 ПОСЛЕДНИЕ ОПЕРАЦИИ ({min(10, len(self.portfolio.transactions))}):")
                        print(f"{'Время':<20} {'Тип':<8} {'Символ':<8} {'Кол-во':<10} {'Цена':<12} {'Сумма':<15}")
                        print("-" * 80)
                        
                        # Сортируем по времени (новые сверху) и берем последние 10
                        recent_transactions = sorted(self.portfolio.transactions, key=lambda x: x.timestamp, reverse=True)[:10]
                        
                        for txn in recent_transactions:
                            time_str = txn.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                            txn_type = "ПОКУПКА" if txn.type.value == "buy" else "ПРОДАЖА" if txn.type.value == "sell" else txn.type.value.upper()
                            total_amount = txn.quantity * txn.price
                            
                            print(f"{time_str:<20} {txn_type:<8} {txn.symbol:<8} {txn.quantity:<10.2f} "
                                  f"{txn.price:<12.2f} {total_amount:<15.2f}")
                    else:
                        print("\n📜 Нет операций")
                        
            else:
                print("❌ Торговый движок не инициализирован")
                return False
            
            print("="*60)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о портфеле: {e}")
            return False
    
    async def _cmd_balance(self, args: List[str] = None) -> bool:
        """Показать баланс счета"""
        try:
            if not self.portfolio:
                logger.error("Портфель не инициализирован")
                return False
            
            print("\n" + "="*50)
            print("💰 БАЛАНС СЧЕТА")
            print("="*50)
            
            # Синхронизация с T-Bank (если необходимо)
            if hasattr(self.portfolio, 'tbank_broker') and self.portfolio.tbank_broker:
                await self.portfolio.sync_with_tbank()
            
            # Получение метрик портфеля
            metrics = await self.portfolio.get_portfolio_metrics()
            if metrics:
                print(f"RUB: {metrics.cash_balance:,.2f}")
                print(f"Общая стоимость: {metrics.total_value:,.2f} ₽")
                print(f"Инвестировано: {metrics.invested_value:,.2f} ₽")
            else:
                print("❌ Метрики портфеля недоступны")
                return False
            
            print("="*50)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return False
    
    async def _cmd_positions(self, args: List[str] = None) -> bool:
        """Показать текущие позиции"""
        try:
            if not self.portfolio:
                logger.error("Портфель не инициализирован")
                return False
            
            print("\n" + "="*60)
            print("📋 ТЕКУЩИЕ ПОЗИЦИИ")
            print("="*60)
            
            positions = await self.portfolio.get_positions()
            if positions:
                print(f"{'Тикер':<8} {'Акции':<10} {'Лоты':<8} {'Ср.цена':<12} {'Тек.цена':<12} {'Стоимость':<12} {'P&L %':>8}")
                print("-" * 70)
                for pos in positions:
                    # Получаем размер лота для инструмента
                    lot_size = 1  # По умолчанию
                    if hasattr(self.system, 'trading_engine') and self.system.trading_engine:
                        if hasattr(self.system.trading_engine, 'tbank_broker') and self.system.trading_engine.tbank_broker:
                            lot_size = self.system.trading_engine.tbank_broker.get_lot_size(pos.symbol)
                    
                    # Рассчитываем количество лотов
                    shares = abs(pos.quantity)
                    lots = shares / lot_size if lot_size > 0 else shares
                    
                    # Показываем тип позиции (длинная/короткая)
                    position_type = "LONG" if pos.quantity > 0 else "SHORT" if pos.quantity < 0 else "ZERO"
                    
                    print(f"{pos.symbol:<8} {shares:<10.0f} {lots:<8.1f} {pos.average_price:<12.2f} "
                          f"{pos.current_price:<12.2f} {pos.market_value:<12.2f} {pos.unrealized_pnl_percent:>+7.2f}% ({position_type})")
            else:
                print("Нет открытых позиций")
            
            print("="*60)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка получения позиций: {e}")
            return False
    
    async def _cmd_cooldowns(self, args: List[str] = None) -> bool:
        """Показать отчет по кулдаунам"""
        try:
            if not self.system or not self.portfolio:
                logger.error("Система или портфель не инициализированы")
                return False
            
            print("\n" + "="*60)
            print("📊 ОТЧЕТ ПО КУЛДАУНАМ")
            print("="*60)
            
            # Получаем отчет по кулдаунам
            cooldown_report = self.portfolio.get_cooldown_report(self.system.trading_engine)
            print(cooldown_report)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка получения отчета по кулдаунам: {e}")
            return False
    
    async def _cmd_status(self, args: List[str] = None) -> bool:
        """Показать статус системы"""
        try:
            print("\n" + "="*50)
            print("🔧 СТАТУС СИСТЕМЫ")
            print("="*50)
            
            print(f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🔄 Система: {'Активна' if self.system else 'Не инициализирована'}")
            print(f"📊 Портфель: {'Инициализирован' if self.portfolio else 'Не инициализирован'}")
            
            # Проверка типа брокера через систему
            broker_type = "Не определен"
            if self.system and hasattr(self.system, 'trading_engine') and self.system.trading_engine:
                broker_type = self.system.trading_engine.broker_type
                if broker_type in ['tbank', 'tinkoff']:
                    broker_type = f"T-Bank ({'Sandbox' if hasattr(self.system.trading_engine, 'tbank_broker') and self.system.trading_engine.tbank_broker and self.system.trading_engine.tbank_broker.sandbox else 'Production'})"
                elif broker_type == 'paper':
                    broker_type = "Paper Trading"
            
            print(f"🏦 Брокер: {broker_type}")
            
            if self.system:
                # Проверка статуса нейросетей
                neural_status = "Не активны"
                if hasattr(self.system, 'network_manager') and self.system.network_manager:
                    models_count = len(self.system.network_manager.models)
                    if models_count > 0:
                        neural_status = f"Активны ({models_count} моделей)"
                
                print(f"🤖 Нейросети: {neural_status}")
                print(f"📈 Торговля: {'Активна' if hasattr(self.system, 'trading_engine') else 'Не активна'}")
                
                # Краткая информация о кулдаунах
                if self.portfolio and hasattr(self.system, 'trading_engine') and self.system.trading_engine:
                    cooldown_status = self.portfolio.get_cooldown_status(self.system.trading_engine)
                    active_cooldowns = sum(1 for status in cooldown_status.values() if status.is_active)
                    total_symbols = len(cooldown_status)
                    
                    if total_symbols > 0:
                        print(f"⏰ Кулдауны: {active_cooldowns}/{total_symbols} активных")
                    else:
                        print("⏰ Кулдауны: Нет данных")
            
            print("="*50)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return False
    
    async def _cmd_analyze(self, args: List[str] = None) -> bool:
        """Запустить анализ рынка"""
        try:
            if not self.system:
                logger.error("Система не инициализирована")
                return False
            
            print("\n🔍 Запуск анализа рынка...")
            
            # Запуск анализа через систему
            if hasattr(self.system, 'network_manager') and self.system.network_manager:
                # Получение данных для анализа
                market_data = await self.system.data_provider.get_latest_data()
                
                # Анализ нейросетями с условной передачей портфельных данных
                use_portfolio = False
                try:
                    use_portfolio = self.system.config.get('neural_networks', {}).get('enable_portfolio_features', True)
                except Exception:
                    use_portfolio = True
                predictions = await self.system.network_manager.analyze(
                    market_data,
                    portfolio_manager=self.system.portfolio_manager if use_portfolio else None,
                    news_data=market_data.get('news', {})
                )
                
                # Обновляем предсказания в торговом движке, чтобы сформировать trading_signals
                if hasattr(self.system, 'trading_engine') and self.system.trading_engine:
                    await self.system.trading_engine.update_predictions(predictions)
                
                # Экспорт сигналов после обновления предсказаний
                await self.system._export_signals_data()
                
                print(f"✅ Анализ завершен. Получено {len(predictions)} предсказаний")
                
                # Показ результатов анализа
                if predictions and 'ensemble_predictions' in predictions:
                    ensemble_predictions = predictions['ensemble_predictions']
                    if ensemble_predictions:
                        print("\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА:")
                        print("-" * 50)
                        for symbol, prediction in ensemble_predictions.items():
                            if isinstance(prediction, dict):
                                signal = prediction.get('signal', 'HOLD')
                                confidence = prediction.get('confidence', 0)
                                trend = prediction.get('trend', 'unknown')
                                reasoning = prediction.get('reasoning', '')
                            else:
                                signal = 'HOLD'
                                confidence = 0.0
                                trend = 'unknown'
                                reasoning = ''
                            
                            # Форматирование сигнала с эмодзи
                            signal_emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "🟡"
                            trend_emoji = "📈" if trend == "bullish" else "📉" if trend == "bearish" else "➡️"
                            
                            print(f"{signal_emoji} {symbol}: {signal} (уверенность: {confidence:.2f}) {trend_emoji} {trend}")
                            if reasoning:
                                print(f"   💭 {reasoning}")
                        print("-" * 50)
                        
                        # Показ статистики
                        symbols_analyzed = predictions.get('symbols_analyzed', [])
                        models_used = predictions.get('models_used', [])
                        print(f"📈 Проанализировано символов: {len(symbols_analyzed)}")
                        print(f"🤖 Использовано моделей: {len(models_used)}")
                        print(f"⏰ Время анализа: {predictions.get('analysis_time', 'N/A')}")
                    else:
                        print("ℹ️ Нет предсказаний для отображения")
                else:
                    print("ℹ️ Нет сигналов для торговли")
            else:
                print("❌ Нейросети не доступны")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}")
            return False
    
    async def _cmd_trade(self, args: List[str] = None) -> bool:
        """Запустить торговлю"""
        try:
            if not self.system:
                logger.error("Система не инициализирована")
                return False
            
            print("\n📈 Запуск торговли...")
            
            # Запуск торговли через систему
            if hasattr(self.system, 'trading_engine'):
                # Сначала запускаем анализ для получения сигналов
                print("🔍 Получение данных для анализа...")
                market_data = await self.system.data_provider.get_latest_data()
                
                print("🤖 Анализ нейросетями...")
                predictions = await self.system.network_manager.analyze(market_data)
                
                # Обновляем предсказания в торговом движке
                await self.system.trading_engine.update_predictions(predictions)
                
                # Экспорт сигналов после обновления предсказаний
                await self.system._export_signals_data()
                
                # Получение торговых сигналов
                signals = await self.system.trading_engine.get_trading_signals()
                
                if signals:
                    print(f"📊 Найдено {len(signals)} торговых сигналов")
                    
                    # Показ сигналов
                    for signal in signals:
                        signal_emoji = "🟢" if signal.signal == "BUY" else "🔴" if signal.signal == "SELL" else "🟡"
                        print(f"  {signal_emoji} {signal.symbol}: {signal.signal} (уверенность: {signal.confidence:.2f})")
                    
                    # Выполнение торговых операций
                    await self.system.trading_engine.execute_trades(signals)
                    print("✅ Торговые операции выполнены")
                else:
                    print("ℹ️ Нет торговых сигналов для выполнения")
                    print("💡 Возможные причины:")
                    print("   - Сигналы не соответствуют минимальной уверенности")
                    print("   - Достигнуто максимальное количество позиций")
                    print("   - Сигналы устарели (старше 5 минут)")
                
                print("✅ Торговый цикл завершен")
            else:
                print("❌ Торговый движок не доступен")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка торговли: {e}")
            return False
    
    async def _cmd_sell_all(self, args: List[str] = None) -> bool:
        """Продать все позиции"""
        try:
            if not self.system or not self.portfolio:
                logger.error("Не все компоненты инициализированы")
                return False
            
            print("\n⚠️  ПРОДАЖА ВСЕХ ПОЗИЦИЙ")
            print("="*50)
            
            # Синхронизация с T-Bank (если необходимо)
            if hasattr(self.portfolio, 'tbank_broker') and self.portfolio.tbank_broker:
                await self.portfolio.sync_with_tbank()
            
            # Получение позиций через PortfolioManager
            positions = await self.portfolio.get_positions()
            if not positions:
                print("📋 Нет позиций для продажи")
                return True
            
            print(f"📊 Найдено позиций: {len(positions)}")
            
            # Показ текущего баланса
            cash_balance = self.portfolio.cash_balance
            print(f"💰 Текущий баланс: {cash_balance:,.2f} ₽")
            
            # Показ позиций для продажи
            print("\n📋 Позиции для продажи:")
            total_value = 0
            for position in positions:
                if position.quantity > 0:
                    print(f"  {position.symbol}: {position.quantity:.2f} шт × {position.current_price:.2f} ₽ = {position.market_value:,.2f} ₽")
                    total_value += position.market_value
            
            print(f"\n💵 Общая стоимость позиций: {total_value:,.2f} ₽")
            print(f"💰 Ожидаемый баланс после продажи: {cash_balance + total_value:,.2f} ₽")
            
            # Подтверждение
            print("\n❓ Подтвердите продажу всех позиций (yes/no): ", end="")
            try:
                confirm = input().lower()
            except EOFError:
                print("\n❌ Операция отменена (нет ввода)")
                return False
            
            if confirm != 'yes':
                print("❌ Операция отменена")
                return False
            
            # Продажа позиций через TradingEngine
            sold_count = 0
            for position in positions:
                if position.quantity > 0:
                    try:
                        print(f"\n🔄 Продажа {position.symbol}: {position.quantity:.2f} шт...")
                        
                        # Создание ордера через TradingEngine
                        if hasattr(self.system, 'trading_engine') and self.system.trading_engine:
                            # Создаем ордер напрямую для продажи всей позиции
                            from src.trading.trading_engine import Order, OrderSide, OrderType
                            
                            order = Order(
                                symbol=position.symbol,
                                side=OrderSide.SELL,
                                quantity=position.quantity,
                                order_type=OrderType.MARKET,
                                price=None
                            )
                            
                            # Выполняем ордер
                            await self.system.trading_engine._submit_order(order)
                            print(f"✅ {position.symbol} продан: {position.quantity:.2f} шт")
                            sold_count += 1
                        else:
                            print(f"❌ TradingEngine не доступен")
                            
                    except Exception as e:
                        print(f"❌ Ошибка продажи {position.symbol}: {e}")
            
            print(f"\n📊 Продано позиций: {sold_count}/{len(positions)}")
            
            # Обновляем портфель после продаж
            if hasattr(self.portfolio, 'tbank_broker') and self.portfolio.tbank_broker:
                await self.portfolio.sync_with_tbank()
                print(f"💰 Новый баланс: {self.portfolio.cash_balance:,.2f} ₽")
            
            print("="*50)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка продажи позиций: {e}")
            return False
    
    async def _cmd_buy(self, args: List[str] = None) -> bool:
        """Купить инструмент"""
        if len(args) < 2:
            print("❌ Использование: buy SYMBOL QUANTITY")
            return False
        
        if not self.system or not self.portfolio:
            logger.error("Не все компоненты инициализированы")
            return False
        
        symbol = args[0].upper()
        try:
            quantity = float(args[1])
        except ValueError:
            print("❌ Неверное количество")
            return False
        
        print(f"🔄 Покупка {symbol}: {quantity} лотов...")
        
        # Создание ордера через TradingEngine
        if hasattr(self.system, 'trading_engine') and self.system.trading_engine:
            try:
                # Создаем ордер напрямую для покупки
                from src.trading.trading_engine import Order, OrderSide, OrderType
                
                order = Order(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    order_type=OrderType.MARKET,
                    price=None
                )
                
                # Выполняем ордер
                await self.system.trading_engine._submit_order(order)
                print(f"✅ {symbol} куплен: {quantity} шт")
                return True
                
            except Exception as e:
                print(f"❌ Ошибка покупки {symbol}: {e}")
                return False
        else:
            print("❌ TradingEngine не доступен")
            return False
    
    async def _cmd_sell(self, args: List[str] = None) -> bool:
        """Продать инструмент"""
        if len(args) < 2:
            print("❌ Использование: sell SYMBOL QUANTITY")
            return False
        
        if not self.system or not self.portfolio:
            logger.error("Не все компоненты инициализированы")
            return False
        
        symbol = args[0].upper()
        try:
            quantity = float(args[1])
        except ValueError:
            print("❌ Неверное количество")
            return False
        
        print(f"🔄 Продажа {symbol}: {quantity} шт...")
        
        # Создание ордера через TradingEngine
        if hasattr(self.system, 'trading_engine') and self.system.trading_engine:
            try:
                # Создаем ордер напрямую для продажи
                from src.trading.trading_engine import Order, OrderSide, OrderType
                
                order = Order(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    quantity=quantity,
                    order_type=OrderType.MARKET,
                    price=None
                )
                
                # Выполняем ордер
                await self.system.trading_engine._submit_order(order)
                print(f"✅ {symbol} продан: {quantity} шт")
                return True
                
            except Exception as e:
                print(f"❌ Ошибка продажи {symbol}: {e}")
                return False
        else:
            print("❌ TradingEngine не доступен")
            return False
    
    async def _cmd_signals(self, args: List[str] = None) -> bool:
        """Показать последние сигналы"""
        print("\n📊 ПОСЛЕДНИЕ ТОРГОВЫЕ СИГНАЛЫ")
        print("="*50)
        print("Функция в разработке...")
        return True
    
    async def _cmd_models(self, args: List[str] = None) -> bool:
        """Показать статус моделей"""
        print("\n🤖 СТАТУС МОДЕЛЕЙ НЕЙРОСЕТЕЙ")
        print("="*50)
        print("Функция в разработке...")
        return True
    
    async def _cmd_restart(self, args: List[str] = None) -> bool:
        """Перезапустить систему"""
        print("\n🔄 ПЕРЕЗАПУСК СИСТЕМЫ")
        print("="*50)
        print("Функция в разработке...")
        return True
    
    async def _cmd_stop(self, args: List[str] = None) -> bool:
        """Остановить торговлю"""
        print("\n⏹️  ОСТАНОВКА ТОРГОВЛИ")
        print("="*50)
        print("Функция в разработке...")
        return True
    
    async def _cmd_start(self, args: List[str] = None) -> bool:
        """Запустить торговлю"""
        print("\n▶️  ЗАПУСК ТОРГОВЛИ")
        print("="*50)
        print("Функция в разработке...")
        return True
    
    def get_available_commands(self) -> List[str]:
        """Получить список доступных команд"""
        return list(self.commands.keys())
    
    def get_commands_by_type(self, command_type: CommandType) -> List[Command]:
        """Получить команды по типу"""
        return [cmd for cmd in self.commands.values() if cmd.command_type == command_type]
