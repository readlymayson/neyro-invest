"""
Торговый движок для выполнения торговых операций
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from enum import Enum
import pandas as pd

from ..data.data_provider import DataProvider
from ..portfolio.portfolio_manager import PortfolioManager


class OrderType(Enum):
    """Типы ордеров"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Стороны ордера"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Статусы ордеров"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Order:
    """Класс торгового ордера"""
    
    def __init__(self, symbol: str, side: OrderSide, quantity: float, 
                 order_type: OrderType = OrderType.MARKET, price: Optional[float] = None,
                 stop_price: Optional[float] = None, order_id: Optional[str] = None):
        """
        Инициализация ордера
        
        Args:
            symbol: Тикер инструмента
            side: Сторона ордера (покупка/продажа)
            quantity: Количество
            order_type: Тип ордера
            price: Цена (для лимитных ордеров)
            stop_price: Стоп-цена
            order_id: ID ордера
        """
        self.order_id = order_id or f"order_{datetime.now().timestamp()}"
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.price = price
        self.stop_price = stop_price
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()
        self.filled_at = None
        self.filled_price = None
        self.filled_quantity = 0.0
        self.commission = 0.0
        
        logger.debug(f"Создан ордер {self.order_id}: {self.side.value} {self.quantity} {self.symbol}")


class TradingSignal:
    """Класс торгового сигнала"""
    
    def __init__(self, symbol: str, signal: str, confidence: float, 
                 price: Optional[float] = None, strength: float = 0.0,
                 source: str = "neural_network", timestamp: Optional[datetime] = None):
        """
        Инициализация торгового сигнала
        
        Args:
            symbol: Тикер инструмента
            signal: Тип сигнала (BUY/SELL/HOLD)
            confidence: Уверенность в сигнале (0-1)
            price: Цена на момент сигнала
            strength: Сила сигнала
            source: Источник сигнала
            timestamp: Время сигнала
        """
        self.symbol = symbol
        self.signal = signal.upper()
        self.confidence = confidence
        self.price = price
        self.strength = strength
        self.source = source
        self.timestamp = timestamp or datetime.now()
        
        logger.debug(f"Получен сигнал {self.signal} для {self.symbol} с уверенностью {confidence:.3f}")


class TradingEngine:
    """
    Торговый движок для выполнения торговых операций
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация торгового движка
        
        Args:
            config: Конфигурация торгового движка
        """
        self.config = config
        self.broker_type = config.get('broker', 'paper')
        self.signal_threshold = config.get('signal_threshold', 0.6)
        self.signal_check_interval = config.get('signal_check_interval', 30)
        self.max_positions = config.get('max_positions', 10)
        self.position_size = config.get('position_size', 0.1)
        self.min_trade_interval = config.get('min_trade_interval', 3600)  # Читаем из конфига
        
        # Торговые данные
        self.active_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.trading_signals: Dict[str, TradingSignal] = {}
        self.last_signal_check = None
        
        # Защита от частых перепродаж
        self.last_trade_time: Dict[str, datetime] = {}  # Последняя сделка по символу
        
        # Компоненты системы
        self.data_provider: Optional[DataProvider] = None
        self.portfolio_manager: Optional[PortfolioManager] = None
        
        logger.info(f"Торговый движок инициализирован (брокер: {self.broker_type})")
    
    async def initialize(self):
        """
        Инициализация торгового движка
        """
        logger.info("Инициализация торгового движка")
        
        # Инициализация брокера
        await self._initialize_broker()
        
        # Загрузка истории ордеров
        await self._load_order_history()
        
        logger.info("Торговый движок инициализирован")
    
    async def _initialize_broker(self):
        """
        Инициализация брокера
        """
        if self.broker_type == 'paper':
            logger.info("Используется бумажный торговый брокер")
        elif self.broker_type == 'tinkoff':
            logger.info("Инициализация подключения к Tinkoff API")
            # Здесь будет инициализация реального брокера
        elif self.broker_type == 'sber':
            logger.info("Инициализация подключения к Сбербанк Инвестор")
            # Здесь будет инициализация реального брокера
        else:
            logger.warning(f"Неизвестный тип брокера: {self.broker_type}")
    
    async def _load_order_history(self):
        """
        Загрузка истории ордеров
        """
        # В реальной реализации здесь будет загрузка из базы данных
        logger.debug("Загрузка истории ордеров")
    
    def set_components(self, data_provider: DataProvider, portfolio_manager: PortfolioManager):
        """
        Установка компонентов системы
        
        Args:
            data_provider: Провайдер данных
            portfolio_manager: Менеджер портфеля
        """
        self.data_provider = data_provider
        self.portfolio_manager = portfolio_manager
        logger.debug("Компоненты системы установлены в торговый движок")
    
    async def update_predictions(self, predictions: Dict[str, Any]):
        """
        Обновление предсказаний от нейросетей
        
        Args:
            predictions: Предсказания от нейросетей
        """
        try:
            if 'individual_predictions' not in predictions:
                logger.warning("Нет индивидуальных предсказаний в данных")
                return
            
            # Обработка предсказаний каждой модели
            for model_name, model_prediction in predictions['individual_predictions'].items():
                if 'error' in model_prediction:
                    continue
                
                # Создание торгового сигнала
                signal = self._create_trading_signal(model_prediction, model_name)
                if signal:
                    self.trading_signals[model_name] = signal
            
            # Обработка ансамблевого предсказания
            if 'ensemble_prediction' in predictions:
                ensemble_signal = self._create_trading_signal(
                    predictions['ensemble_prediction'], 
                    'ensemble'
                )
                if ensemble_signal:
                    self.trading_signals['ensemble'] = ensemble_signal
            
            logger.debug(f"Обновлено {len(self.trading_signals)} торговых сигналов")
            
        except Exception as e:
            logger.error(f"Ошибка обновления предсказаний: {e}")
    
    def _create_trading_signal(self, prediction: Dict[str, Any], source: str) -> Optional[TradingSignal]:
        """
        Создание торгового сигнала из предсказания
        
        Args:
            prediction: Предсказание модели
            source: Источник предсказания
            
        Returns:
            Торговый сигнал или None
        """
        try:
            if 'error' in prediction:
                return None
            
            # Определение символа (используем первый доступный)
            symbol = 'SBER'  # По умолчанию
            
            # Извлечение сигнала
            signal = prediction.get('signal', 'HOLD')
            confidence = prediction.get('confidence', 0.0)
            price = prediction.get('next_price')
            strength = prediction.get('signal_strength', 0.0)
            
            # Проверка минимальной уверенности
            if confidence < self.signal_threshold:
                return None
            
            return TradingSignal(
                symbol=symbol,
                signal=signal,
                confidence=confidence,
                price=price,
                strength=strength,
                source=source
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания торгового сигнала: {e}")
            return None
    
    async def get_trading_signals(self) -> List[TradingSignal]:
        """
        Получение торговых сигналов для выполнения
        
        Returns:
            Список торговых сигналов
        """
        try:
            signals_to_execute = []
            
            # Проверка сигналов
            for signal_name, signal in self.trading_signals.items():
                # Проверка времени сигнала (не старше 5 минут)
                if datetime.now() - signal.timestamp > timedelta(minutes=5):
                    continue
                
                # Проверка уверенности
                if signal.confidence < self.signal_threshold:
                    continue
                
                # Проверка возможности открытия позиции
                if await self._can_open_position(signal.symbol, signal.signal):
                    signals_to_execute.append(signal)
            
            logger.debug(f"Найдено {len(signals_to_execute)} сигналов для выполнения")
            return signals_to_execute
            
        except Exception as e:
            logger.error(f"Ошибка получения торговых сигналов: {e}")
            return []
    
    async def _can_open_position(self, symbol: str, signal: str) -> bool:
        """
        Проверка возможности открытия позиции
        
        Args:
            symbol: Тикер инструмента
            signal: Торговый сигнал
            
        Returns:
            True если можно открыть позицию
        """
        try:
            if not self.portfolio_manager:
                return False
            
            # Проверка максимального количества позиций
            current_positions = await self.portfolio_manager.get_positions()
            if len(current_positions) >= self.max_positions:
                return False
            
            # Проверка существующей позиции по символу
            if signal in ['BUY', 'SELL']:
                existing_position = await self.portfolio_manager.get_position(symbol)
                if existing_position:
                    # Если позиция уже есть, проверяем возможность увеличения
                    return await self._can_modify_position(symbol, signal)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки возможности открытия позиции: {e}")
            return False
    
    async def _can_modify_position(self, symbol: str, signal: str) -> bool:
        """
        Проверка возможности изменения позиции
        
        Args:
            symbol: Тикер инструмента
            signal: Торговый сигнал
            
        Returns:
            True если можно изменить позицию
        """
        try:
            if not self.portfolio_manager:
                return False
            
            position = await self.portfolio_manager.get_position(symbol)
            if not position:
                return True
            
            # Проверка времени последней сделки
            if symbol in self.last_trade_time:
                time_since_last_trade = datetime.now() - self.last_trade_time[symbol]
                if time_since_last_trade.total_seconds() < self.min_trade_interval:
                    logger.debug(f"Слишком рано для торговли {symbol}: прошло {time_since_last_trade.total_seconds()/60:.1f} мин")
                    return False
            
            # Проверка на противоположные сигналы
            if signal == 'SELL' and position.quantity > 0:
                # Продажа при наличии позиции - разрешено
                return True
            elif signal == 'BUY' and position.quantity < 0:
                # Покупка при короткой позиции - разрешено
                return True
            elif signal == 'BUY' and position.quantity > 0:
                # Покупка при длинной позиции - только если прошло достаточно времени
                return True
            elif signal == 'SELL' and position.quantity < 0:
                # Продажа при короткой позиции - только если прошло достаточно времени
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки возможности изменения позиции: {e}")
            return False
    
    async def execute_trades(self, signals: List[TradingSignal]):
        """
        Выполнение торговых операций
        
        Args:
            signals: Список торговых сигналов
        """
        try:
            logger.info(f"Выполнение {len(signals)} торговых операций")
            
            for signal in signals:
                try:
                    await self._execute_signal(signal)
                except Exception as e:
                    logger.error(f"Ошибка выполнения сигнала {signal.symbol}: {e}")
            
            logger.info("Выполнение торговых операций завершено")
            
        except Exception as e:
            logger.error(f"Ошибка выполнения торговых операций: {e}")
    
    async def _execute_signal(self, signal: TradingSignal):
        """
        Выполнение одного торгового сигнала
        
        Args:
            signal: Торговый сигнал
        """
        try:
            if signal.signal == 'HOLD':
                return
            
            # Расчет размера позиции
            position_size = await self._calculate_position_size(signal)
            if position_size <= 0:
                logger.debug(f"Размер позиции для {signal.symbol} равен 0, пропускаем")
                return
            
            # Создание ордера
            order = self._create_order(signal, position_size)
            if not order:
                return
            
            # Выполнение ордера
            await self._submit_order(order)
            
            logger.info(f"Выполнен сигнал {signal.signal} для {signal.symbol}: {order.quantity} штук")
            
        except Exception as e:
            logger.error(f"Ошибка выполнения сигнала {signal.symbol}: {e}")
    
    async def _calculate_position_size(self, signal: TradingSignal) -> float:
        """
        Расчет размера позиции
        
        Args:
            signal: Торговый сигнал
            
        Returns:
            Размер позиции
        """
        try:
            if not self.portfolio_manager:
                return 0.0
            
            # Получение текущего капитала
            portfolio_value = await self.portfolio_manager.get_portfolio_value()
            
            # Расчет размера позиции как процент от капитала
            position_value = portfolio_value * self.position_size
            
            # Получение текущей цены
            current_price = await self._get_current_price(signal.symbol)
            if current_price <= 0:
                return 0.0
            
            # Расчет количества акций
            quantity = position_value / current_price
            
            # Округление до целого количества акций
            quantity = int(quantity)
            
            # Минимальная проверка
            if quantity < 1:
                return 0.0
            
            return float(quantity)
            
        except Exception as e:
            logger.error(f"Ошибка расчета размера позиции: {e}")
            return 0.0
    
    async def _get_current_price(self, symbol: str) -> float:
        """
        Получение текущей цены инструмента
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            Текущая цена
        """
        try:
            if self.data_provider:
                realtime_data = await self.data_provider.get_latest_data(symbol)
                return realtime_data.get('realtime', {}).get('price', 0.0)
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка получения текущей цены для {symbol}: {e}")
            return 0.0
    
    def _create_order(self, signal: TradingSignal, quantity: float) -> Optional[Order]:
        """
        Создание ордера
        
        Args:
            signal: Торговый сигнал
            quantity: Количество
            
        Returns:
            Ордер или None
        """
        try:
            # Определение стороны ордера
            side = OrderSide.BUY if signal.signal == 'BUY' else OrderSide.SELL
            
            # Создание рыночного ордера
            order = Order(
                symbol=signal.symbol,
                side=side,
                quantity=quantity,
                order_type=OrderType.MARKET
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Ошибка создания ордера: {e}")
            return None
    
    async def _submit_order(self, order: Order):
        """
        Отправка ордера брокеру
        
        Args:
            order: Ордер для отправки
        """
        try:
            if self.broker_type == 'paper':
                await self._execute_paper_order(order)
            else:
                await self._execute_real_order(order)
            
            # Добавление в историю
            self.order_history.append(order)
            
        except Exception as e:
            logger.error(f"Ошибка отправки ордера {order.order_id}: {e}")
            order.status = OrderStatus.REJECTED
    
    async def _execute_paper_order(self, order: Order):
        """
        Выполнение бумажного ордера
        
        Args:
            order: Ордер для выполнения
        """
        try:
            # Получение текущей цены
            current_price = await self._get_current_price(order.symbol)
            if current_price <= 0:
                order.status = OrderStatus.REJECTED
                return
            
            # Симуляция выполнения ордера
            order.filled_price = current_price
            order.filled_quantity = order.quantity
            order.filled_at = datetime.now()
            order.status = OrderStatus.FILLED
            
            # Расчет комиссии (0.05% от суммы)
            order.commission = order.filled_quantity * order.filled_price * 0.0005
            
            # Обновление портфеля
            if self.portfolio_manager:
                await self._update_portfolio_from_order(order)
            
            # Обновление времени последней сделки
            self.last_trade_time[order.symbol] = datetime.now()
            
            logger.info(f"Бумажный ордер {order.order_id} выполнен: {order.filled_quantity} @ {order.filled_price}")
            
        except Exception as e:
            logger.error(f"Ошибка выполнения бумажного ордера: {e}")
            order.status = OrderStatus.REJECTED
    
    async def _execute_real_order(self, order: Order):
        """
        Выполнение реального ордера через брокера
        
        Args:
            order: Ордер для выполнения
        """
        try:
            # Здесь будет интеграция с реальным брокером
            logger.warning("Выполнение реальных ордеров не реализовано")
            order.status = OrderStatus.REJECTED
            
        except Exception as e:
            logger.error(f"Ошибка выполнения реального ордера: {e}")
            order.status = OrderStatus.REJECTED
    
    async def _update_portfolio_from_order(self, order: Order):
        """
        Обновление портфеля на основе выполненного ордера
        
        Args:
            order: Выполненный ордер
        """
        try:
            if not self.portfolio_manager:
                return
            
            # Создание транзакции
            transaction = {
                'symbol': order.symbol,
                'side': order.side.value,
                'quantity': order.filled_quantity,
                'price': order.filled_price,
                'commission': order.commission,
                'timestamp': order.filled_at
            }
            
            # Обновление портфеля
            await self.portfolio_manager.add_transaction(transaction)
            
        except Exception as e:
            logger.error(f"Ошибка обновления портфеля: {e}")
    
    async def get_active_orders(self) -> List[Order]:
        """
        Получение активных ордеров
        
        Returns:
            Список активных ордеров
        """
        return [order for order in self.active_orders.values() if order.status == OrderStatus.PENDING]
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Отмена ордера
        
        Args:
            order_id: ID ордера
            
        Returns:
            True если ордер отменен
        """
        try:
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                order.status = OrderStatus.CANCELLED
                del self.active_orders[order_id]
                logger.info(f"Ордер {order_id} отменен")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка отмены ордера {order_id}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса торгового движка
        
        Returns:
            Словарь со статусом
        """
        return {
            'broker_type': self.broker_type,
            'active_orders': len(self.active_orders),
            'total_orders': len(self.order_history),
            'trading_signals': len(self.trading_signals),
            'signal_threshold': self.signal_threshold,
            'max_positions': self.max_positions,
            'last_signal_check': self.last_signal_check.isoformat() if self.last_signal_check else None
        }

