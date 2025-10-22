"""
Менеджер портфеля для управления инвестициями
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum


class TransactionType(Enum):
    """Типы транзакций"""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    COMMISSION = "commission"


@dataclass
class Position:
    """Класс позиции в портфеле"""
    symbol: str
    quantity: float
    average_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    last_updated: datetime


@dataclass
class Transaction:
    """Класс транзакции"""
    id: str
    symbol: str
    type: TransactionType
    quantity: float
    price: float
    commission: float
    timestamp: datetime
    notes: Optional[str] = None


@dataclass
class PortfolioMetrics:
    """Метрики портфеля"""
    total_value: float
    cash_balance: float
    invested_value: float
    total_pnl: float
    total_pnl_percent: float
    daily_pnl: float
    daily_pnl_percent: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    last_updated: datetime


class PortfolioManager:
    """
    Менеджер портфеля для управления инвестициями
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация менеджера портфеля
        
        Args:
            config: Конфигурация менеджера портфеля
        """
        self.config = config
        self.initial_capital = config.get('initial_capital', 1000000)
        self.max_risk_per_trade = config.get('max_risk_per_trade', 0.02)
        self.max_portfolio_risk = config.get('max_portfolio_risk', 0.1)
        self.update_interval = config.get('update_interval', 300)
        self.rebalance_threshold = config.get('rebalance_threshold', 0.05)
        
        # Данные портфеля
        self.cash_balance = self.initial_capital
        self.positions: Dict[str, Position] = {}
        self.transactions: List[Transaction] = []
        self.portfolio_history: List[Dict] = []
        
        # Метрики
        self.current_metrics: Optional[PortfolioMetrics] = None
        self.risk_metrics: Dict[str, float] = {}
        
        # Провайдер данных (будет установлен через set_data_provider)
        self.data_provider = None
        
        logger.info(f"Менеджер портфеля инициализирован с капиталом {self.initial_capital}")
    
    async def initialize(self):
        """
        Инициализация менеджера портфеля
        """
        logger.info("Инициализация менеджера портфеля")
        
        # Загрузка истории транзакций
        await self._load_transaction_history()
        
        # Расчет текущих позиций
        await self._calculate_positions()
        
        # Расчет метрик портфеля
        await self.update_portfolio()
        
        logger.info("Менеджер портфеля инициализирован")
    
    async def _load_transaction_history(self):
        """
        Загрузка истории транзакций
        """
        # В реальной реализации здесь будет загрузка из базы данных
        logger.debug("Загрузка истории транзакций")
    
    async def _calculate_positions(self):
        """
        Расчет текущих позиций на основе транзакций
        """
        try:
            logger.debug("Расчет текущих позиций")
            
            # Группировка транзакций по символам
            symbol_transactions = {}
            for transaction in self.transactions:
                if transaction.symbol not in symbol_transactions:
                    symbol_transactions[transaction.symbol] = []
                symbol_transactions[transaction.symbol].append(transaction)
            
            # Расчет позиций для каждого символа
            for symbol, transactions in symbol_transactions.items():
                position = await self._calculate_symbol_position(symbol, transactions)
                if position and position.quantity != 0:
                    self.positions[symbol] = position
            
            logger.debug(f"Рассчитано {len(self.positions)} позиций")
            
        except Exception as e:
            logger.error(f"Ошибка расчета позиций: {e}")
    
    async def _calculate_symbol_position(self, symbol: str, transactions: List[Transaction]) -> Optional[Position]:
        """
        Расчет позиции по символу
        
        Args:
            symbol: Тикер инструмента
            transactions: Список транзакций
            
        Returns:
            Позиция или None
        """
        try:
            total_quantity = 0.0
            total_cost = 0.0
            total_commission = 0.0
            
            # Сортировка транзакций по времени
            sorted_transactions = sorted(transactions, key=lambda x: x.timestamp)
            
            for transaction in sorted_transactions:
                if transaction.type == TransactionType.BUY:
                    total_quantity += transaction.quantity
                    total_cost += transaction.quantity * transaction.price
                    total_commission += transaction.commission
                elif transaction.type == TransactionType.SELL:
                    total_quantity -= transaction.quantity
                    total_cost -= transaction.quantity * transaction.price
                    total_commission += transaction.commission
            
            if total_quantity == 0:
                return None
            
            # Расчет средней цены покупки
            average_price = (total_cost + total_commission) / total_quantity if total_quantity > 0 else 0
            
            # Получение текущей цены (здесь нужна интеграция с провайдером данных)
            current_price = await self._get_current_price(symbol)
            
            # Расчет метрик позиции
            market_value = total_quantity * current_price
            unrealized_pnl = market_value - (total_cost + total_commission)
            unrealized_pnl_percent = (unrealized_pnl / (total_cost + total_commission)) * 100 if total_cost > 0 else 0
            
            return Position(
                symbol=symbol,
                quantity=total_quantity,
                average_price=average_price,
                current_price=current_price,
                market_value=market_value,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_percent=unrealized_pnl_percent,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Ошибка расчета позиции для {symbol}: {e}")
            return None
    
    async def _get_current_price(self, symbol: str) -> float:
        """
        Получение текущей цены инструмента
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            Текущая цена
        """
        try:
            # Получение цены из провайдера данных
            if self.data_provider:
                realtime_data = await self.data_provider.get_latest_data(symbol)
                price = realtime_data.get('realtime', {}).get('price', 0.0)
                if price > 0:
                    return price
                logger.warning(f"Не удалось получить реальную цену для {symbol}, используем последнюю известную")
            
            # Если нет провайдера или данных - используем среднюю цену покупки
            if symbol in self.positions:
                return self.positions[symbol].average_price
            
            # Fallback - возвращаем 100
            logger.warning(f"Нет данных о цене для {symbol}, используем 100.0")
            return 100.0
            
        except Exception as e:
            logger.error(f"Ошибка получения цены для {symbol}: {e}")
            # В случае ошибки возвращаем последнюю известную цену
            if symbol in self.positions:
                return self.positions[symbol].current_price
            return 100.0
    
    def set_data_provider(self, data_provider):
        """
        Установка провайдера данных
        
        Args:
            data_provider: Провайдер данных
        """
        self.data_provider = data_provider
        logger.debug("Провайдер данных установлен в менеджере портфеля")
    
    async def add_transaction(self, transaction_data: Dict[str, Any]):
        """
        Добавление транзакции в портфель
        
        Args:
            transaction_data: Данные транзакции
        """
        try:
            # Создание объекта транзакции
            transaction = Transaction(
                id=transaction_data.get('id', f"txn_{datetime.now().timestamp()}"),
                symbol=transaction_data['symbol'],
                type=TransactionType(transaction_data['side']),
                quantity=transaction_data['quantity'],
                price=transaction_data['price'],
                commission=transaction_data.get('commission', 0.0),
                timestamp=transaction_data.get('timestamp', datetime.now()),
                notes=transaction_data.get('notes')
            )
            
            # Добавление транзакции
            self.transactions.append(transaction)
            
            # Обновление баланса денежных средств
            await self._update_cash_balance(transaction)
            
            # Пересчет позиций
            await self._calculate_positions()
            
            logger.info(f"Добавлена транзакция {transaction.id}: {transaction.type.value} {transaction.quantity} {transaction.symbol}")
            
        except Exception as e:
            logger.error(f"Ошибка добавления транзакции: {e}")
    
    async def _update_cash_balance(self, transaction: Transaction):
        """
        Обновление баланса денежных средств
        
        Args:
            transaction: Транзакция
        """
        try:
            if transaction.type == TransactionType.BUY:
                # Покупка - уменьшение денежных средств
                cost = transaction.quantity * transaction.price + transaction.commission
                self.cash_balance -= cost
            elif transaction.type == TransactionType.SELL:
                # Продажа - увеличение денежных средств
                proceeds = transaction.quantity * transaction.price - transaction.commission
                self.cash_balance += proceeds
            
            logger.debug(f"Обновлен баланс денежных средств: {self.cash_balance}")
            
        except Exception as e:
            logger.error(f"Ошибка обновления баланса денежных средств: {e}")
    
    async def update_portfolio(self):
        """
        Обновление портфеля
        """
        try:
            logger.debug("Обновление портфеля")
            
            # Обновление текущих цен позиций
            await self._update_position_prices()
            
            # Расчет метрик портфеля
            await self._calculate_portfolio_metrics()
            
            # Сохранение истории портфеля
            await self._save_portfolio_snapshot()
            
            logger.debug("Портфель обновлен")
            
        except Exception as e:
            logger.error(f"Ошибка обновления портфеля: {e}")
    
    async def _update_position_prices(self):
        """
        Обновление цен позиций
        """
        try:
            for symbol, position in self.positions.items():
                current_price = await self._get_current_price(symbol)
                if current_price > 0:
                    position.current_price = current_price
                    position.market_value = position.quantity * current_price
                    position_cost = abs(position.quantity * position.average_price)
                    position.unrealized_pnl = position.market_value - (position.quantity * position.average_price)
                    position.unrealized_pnl_percent = (position.unrealized_pnl / position_cost) * 100 if position_cost > 0 else 0
                    position.last_updated = datetime.now()
            
        except Exception as e:
            logger.error(f"Ошибка обновления цен позиций: {e}")
    
    async def _calculate_portfolio_metrics(self):
        """
        Расчет метрик портфеля
        """
        try:
            # Расчет общей стоимости портфеля
            invested_value = sum(position.market_value for position in self.positions.values())
            total_value = self.cash_balance + invested_value
            
            # Расчет общей прибыли/убытка
            total_pnl = sum(position.unrealized_pnl for position in self.positions.values())
            total_pnl_percent = (total_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0
            
            # Расчет дневной прибыли/убытка
            daily_pnl = 0.0  # Здесь нужна логика расчета дневного P&L
            daily_pnl_percent = 0.0
            
            # Расчет коэффициента Шарпа
            sharpe_ratio = await self._calculate_sharpe_ratio()
            
            # Расчет максимальной просадки
            max_drawdown = await self._calculate_max_drawdown()
            
            # Расчет волатильности
            volatility = await self._calculate_volatility()
            
            self.current_metrics = PortfolioMetrics(
                total_value=total_value,
                cash_balance=self.cash_balance,
                invested_value=invested_value,
                total_pnl=total_pnl,
                total_pnl_percent=total_pnl_percent,
                daily_pnl=daily_pnl,
                daily_pnl_percent=daily_pnl_percent,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                volatility=volatility,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Ошибка расчета метрик портфеля: {e}")
    
    async def _calculate_sharpe_ratio(self) -> float:
        """
        Расчет коэффициента Шарпа
        
        Returns:
            Коэффициент Шарпа
        """
        try:
            if len(self.portfolio_history) < 2:
                return 0.0
            
            # Получение исторических значений портфеля
            portfolio_values = [snapshot['total_value'] for snapshot in self.portfolio_history[-252:]]  # Последний год
            
            if len(portfolio_values) < 2:
                return 0.0
            
            # Расчет доходности
            returns = np.diff(portfolio_values) / portfolio_values[:-1]
            
            # Расчет коэффициента Шарпа (предполагаем безрисковую ставку = 0)
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0.0
            
            return float(sharpe_ratio)
            
        except Exception as e:
            logger.error(f"Ошибка расчета коэффициента Шарпа: {e}")
            return 0.0
    
    async def _calculate_max_drawdown(self) -> float:
        """
        Расчет максимальной просадки
        
        Returns:
            Максимальная просадка в процентах
        """
        try:
            if len(self.portfolio_history) < 2:
                return 0.0
            
            portfolio_values = [snapshot['total_value'] for snapshot in self.portfolio_history]
            
            # Расчет максимальной просадки
            peak = portfolio_values[0]
            max_drawdown = 0.0
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            return float(max_drawdown * 100)  # В процентах
            
        except Exception as e:
            logger.error(f"Ошибка расчета максимальной просадки: {e}")
            return 0.0
    
    async def _calculate_volatility(self) -> float:
        """
        Расчет волатильности портфеля
        
        Returns:
            Волатильность в процентах
        """
        try:
            if len(self.portfolio_history) < 2:
                return 0.0
            
            portfolio_values = [snapshot['total_value'] for snapshot in self.portfolio_history[-252:]]  # Последний год
            
            if len(portfolio_values) < 2:
                return 0.0
            
            # Расчет доходности
            returns = np.diff(portfolio_values) / portfolio_values[:-1]
            
            # Расчет волатильности (годовая)
            volatility = np.std(returns) * np.sqrt(252) * 100  # В процентах
            
            return float(volatility)
            
        except Exception as e:
            logger.error(f"Ошибка расчета волатильности: {e}")
            return 0.0
    
    async def _save_portfolio_snapshot(self):
        """
        Сохранение снимка портфеля в историю
        """
        try:
            if not self.current_metrics:
                return
            
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'total_value': self.current_metrics.total_value,
                'cash_balance': self.current_metrics.cash_balance,
                'invested_value': self.current_metrics.invested_value,
                'total_pnl': self.current_metrics.total_pnl,
                'total_pnl_percent': self.current_metrics.total_pnl_percent,
                'positions_count': len(self.positions)
            }
            
            self.portfolio_history.append(snapshot)
            
            # Ограничение размера истории (последние 1000 записей)
            if len(self.portfolio_history) > 1000:
                self.portfolio_history = self.portfolio_history[-1000:]
            
        except Exception as e:
            logger.error(f"Ошибка сохранения снимка портфеля: {e}")
    
    async def check_risks(self):
        """
        Проверка рисков портфеля
        """
        try:
            logger.debug("Проверка рисков портфеля")
            
            # Проверка максимального риска портфеля
            await self._check_portfolio_risk()
            
            # Проверка риска отдельных позиций
            await self._check_position_risks()
            
            # Проверка необходимости ребалансировки
            await self._check_rebalancing()
            
            logger.debug("Проверка рисков завершена")
            
        except Exception as e:
            logger.error(f"Ошибка проверки рисков: {e}")
    
    async def _check_portfolio_risk(self):
        """
        Проверка общего риска портфеля
        """
        try:
            if not self.current_metrics:
                return
            
            # Проверка максимальной просадки
            if self.current_metrics.max_drawdown > self.max_portfolio_risk * 100:
                logger.warning(f"Превышена максимальная просадка: {self.current_metrics.max_drawdown:.2f}%")
            
            # Проверка волатильности
            if self.current_metrics.volatility > 30:  # 30% волатильность
                logger.warning(f"Высокая волатильность портфеля: {self.current_metrics.volatility:.2f}%")
            
        except Exception as e:
            logger.error(f"Ошибка проверки риска портфеля: {e}")
    
    async def _check_position_risks(self):
        """
        Проверка рисков отдельных позиций
        """
        try:
            for symbol, position in self.positions.items():
                # Проверка убытков по позиции
                if position.unrealized_pnl_percent < -10:  # Убыток более 10%
                    logger.warning(f"Большой убыток по позиции {symbol}: {position.unrealized_pnl_percent:.2f}%")
                
                # Проверка концентрации риска
                position_weight = position.market_value / self.current_metrics.total_value if self.current_metrics.total_value > 0 else 0
                if position_weight > 0.2:  # Более 20% портфеля в одной позиции
                    logger.warning(f"Высокая концентрация в позиции {symbol}: {position_weight*100:.2f}%")
            
        except Exception as e:
            logger.error(f"Ошибка проверки рисков позиций: {e}")
    
    async def _check_rebalancing(self):
        """
        Проверка необходимости ребалансировки
        """
        try:
            if not self.current_metrics:
                return
            
            # Проверка отклонения от целевых весов
            # Здесь должна быть логика проверки целевых весов позиций
            
        except Exception as e:
            logger.error(f"Ошибка проверки ребалансировки: {e}")
    
    async def get_portfolio_value(self) -> float:
        """
        Получение общей стоимости портфеля
        
        Returns:
            Общая стоимость портфеля
        """
        if self.current_metrics:
            return self.current_metrics.total_value
        return self.cash_balance
    
    async def get_positions(self) -> List[Position]:
        """
        Получение списка позиций
        
        Returns:
            Список позиций
        """
        return list(self.positions.values())
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """
        Получение позиции по символу
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            Позиция или None
        """
        return self.positions.get(symbol)
    
    async def get_portfolio_metrics(self) -> Optional[PortfolioMetrics]:
        """
        Получение метрик портфеля
        
        Returns:
            Метрики портфеля или None
        """
        return self.current_metrics
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса менеджера портфеля
        
        Returns:
            Словарь со статусом
        """
        return {
            'initial_capital': self.initial_capital,
            'current_value': self.current_metrics.total_value if self.current_metrics else 0,
            'cash_balance': self.cash_balance,
            'positions_count': len(self.positions),
            'transactions_count': len(self.transactions),
            'total_pnl_percent': self.current_metrics.total_pnl_percent if self.current_metrics else 0,
            'max_drawdown': self.current_metrics.max_drawdown if self.current_metrics else 0,
            'last_update': self.current_metrics.last_updated.isoformat() if self.current_metrics else None
        }
