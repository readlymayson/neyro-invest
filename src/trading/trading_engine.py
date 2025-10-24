"""
Торговый движок для выполнения торговых операций
"""

import asyncio
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from enum import Enum
import pandas as pd

from ..data.data_provider import DataProvider
from ..portfolio.portfolio_manager import PortfolioManager

try:
    from .tbank_broker import TBankBroker
    TBANK_AVAILABLE = True
except ImportError:
    TBANK_AVAILABLE = False
    logger.warning("T-Bank брокер недоступен")


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
        
        # Список символов для торговли (будет установлен при инициализации)
        self.symbols = []
        
        # Ограничения размера позиций
        position_limits = config.get('position_limits', {})
        self.max_position_size = position_limits.get('max_position_size', 0.1)  # Максимум 10% на позицию
        self.max_total_exposure = position_limits.get('max_total_exposure', 0.8)  # Максимум 80% в инвестициях
        self.min_position_size = position_limits.get('min_position_size', 0.01)  # Минимум 1% на позицию
        self.position_size_check = position_limits.get('position_size_check', True)  # Включить проверки
        
        # Настройки разрешения конфликтующих сигналов
        signal_resolution = config.get('signal_resolution', {})
        self.signal_resolution_method = signal_resolution.get('method', 'hybrid')
        self.signal_weights = signal_resolution.get('signal_weights', {'SELL': 1.5, 'BUY': 1.0, 'HOLD': 0.5})
        self.min_confidence_threshold = signal_resolution.get('min_confidence_threshold', 0.6)
        self.enable_deduplication = signal_resolution.get('enable_deduplication', True)
        self.enable_ensemble_voting = signal_resolution.get('enable_ensemble_voting', True)
        
        # Раздельные задержки по типам сигналов
        signal_cooldowns = config.get('signal_cooldowns', {})
        self.buy_cooldown = signal_cooldowns.get('buy_cooldown', 1800)    # 30 минут для покупок
        self.sell_cooldown = signal_cooldowns.get('sell_cooldown', 3600)   # 1 час для продаж
        self.hold_cooldown = signal_cooldowns.get('hold_cooldown', 900)     # 15 минут для удержания
        
        # Защита от частых продаж
        sell_protection = config.get('sell_signal_protection', {})
        self.sell_protection_enabled = sell_protection.get('enabled', True)
        self.min_confidence_increase = sell_protection.get('min_confidence_increase', 0.1)
        self.max_sells_per_hour = sell_protection.get('max_sells_per_hour', 2)
        self.panic_sell_threshold = sell_protection.get('panic_sell_threshold', 0.9)
        self.filter_cooldown_signals = sell_protection.get('filter_cooldown_signals', True)
        
        # Торговые данные
        self.active_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.trading_signals: Dict[str, TradingSignal] = {}
        self.last_signal_check = None
        
        # Защита от частых перепродаж
        self.last_trade_time: Dict[str, datetime] = {}  # Последняя сделка по символу
        self.sell_history: Dict[str, List[datetime]] = {}  # История продаж по символу
        self.last_sell_confidence: Dict[str, float] = {}   # Последняя уверенность продажи
        
        # Компоненты системы
        self.data_provider: Optional[DataProvider] = None
        self.portfolio_manager: Optional[PortfolioManager] = None
        
        # T-Bank брокер
        self.tbank_broker: Optional['TBankBroker'] = None
        self.broker_settings = config.get('broker_settings', {})
        
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
    
    def set_symbols(self, symbols: List[str]):
        """
        Установка списка символов для торговли
        
        Args:
            symbols: Список символов инструментов
        """
        self.symbols = symbols.copy()
        logger.debug(f"Установлено {len(self.symbols)} символов для торговли: {self.symbols}")
    
    async def _initialize_broker(self):
        """
        Инициализация брокера
        """
        if self.broker_type == 'paper':
            logger.info("Используется бумажный торговый брокер")
        elif self.broker_type == 'tinkoff' or self.broker_type == 'tbank':
            if not TBANK_AVAILABLE:
                logger.error("T-Bank брокер недоступен. Установите библиотеку: pip install tinkoff-investments")
                return
            
            logger.info("Инициализация подключения к T-Bank (Tinkoff) API")
            
            # Получение настроек брокера
            tbank_settings = self.broker_settings.get('tbank', {})
            token = tbank_settings.get('token', '')
            sandbox = tbank_settings.get('sandbox', True)
            account_id = tbank_settings.get('account_id', None)
            
            # Если токен не найден в настройках, загружаем из переменной окружения
            if not token:
                token = os.environ.get('TINKOFF_TOKEN')
                if not token:
                    logger.error("T-Bank токен не указан в конфигурации и переменной окружения")
                    return
                else:
                    logger.info("T-Bank токен загружен из переменной окружения TINKOFF_TOKEN")
            
            # Создание брокера
            self.tbank_broker = TBankBroker(
                token=token,
                sandbox=sandbox,
                account_id=account_id
            )
            
            # Инициализация брокера
            await self.tbank_broker.initialize()
            
            mode = "SANDBOX" if sandbox else "PRODUCTION"
            logger.info(f"T-Bank брокер инициализирован в режиме {mode}")
            
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
        Обновление предсказаний от нейросетей для всех символов
        
        Args:
            predictions: Предсказания от нейросетей по всем символам
        """
        try:
            # НЕ очищаем старые сигналы - сохраняем историю для кулдауна
            # self.trading_signals.clear()  # Убрано для сохранения кулдауна
            
            # Очищаем только устаревшие сигналы (старше 5 минут)
            current_time = datetime.now()
            expired_signals = []
            for key, signal in self.trading_signals.items():
                if current_time - signal.timestamp > timedelta(minutes=5):
                    expired_signals.append(key)
            
            for key in expired_signals:
                del self.trading_signals[key]
            
            if expired_signals:
                logger.debug(f"Очищено {len(expired_signals)} устаревших сигналов")
            
            # Обработка предсказаний каждой модели для каждого символа
            if 'individual_predictions' in predictions:
                for model_name, symbols_predictions in predictions['individual_predictions'].items():
                    # symbols_predictions - это словарь {symbol: prediction}
                    for symbol, prediction in symbols_predictions.items():
                        if 'error' in prediction:
                            continue
                        
                        # Создание торгового сигнала
                        signal = self._create_trading_signal(prediction, model_name)
                        if signal:
                            # Фильтрация сигналов на кулдауне перед сохранением
                            if self.filter_cooldown_signals and not await self._can_execute_signal_by_type(signal):
                                logger.debug(f"🚫 {signal.symbol}: Сигнал {signal.signal} отфильтрован на кулдауне при создании")
                                continue
                            
                            # Ключ с именем модели и символом
                            key = f"{model_name}_{symbol}"
                            self.trading_signals[key] = signal
            
            # Обработка ансамблевых предсказаний (теперь по символам)
            if 'ensemble_predictions' in predictions:
                for symbol, ensemble_pred in predictions['ensemble_predictions'].items():
                    ensemble_signal = self._create_trading_signal(
                        ensemble_pred, 
                        'ensemble'
                    )
                    if ensemble_signal:
                        # Фильтрация сигналов на кулдауне перед сохранением
                        if self.filter_cooldown_signals and not await self._can_execute_signal_by_type(ensemble_signal):
                            logger.debug(f"🚫 {ensemble_signal.symbol}: Ансамблевый сигнал {ensemble_signal.signal} отфильтрован на кулдауне при создании")
                            continue
                        
                        key = f"ensemble_{symbol}"
                        self.trading_signals[key] = ensemble_signal
            
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
            
            # Определение символа из предсказания
            symbol = prediction.get('symbol', 'UNKNOWN')
            if symbol == 'UNKNOWN':
                logger.warning(f"Предсказание без символа: {prediction}")
                return None
            
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
                
                # Фильтрация сигналов на кулдауне перед анализом
                if self.filter_cooldown_signals and not await self._can_execute_signal_by_type(signal):
                    logger.debug(f"🚫 {signal.symbol}: Сигнал {signal.signal} отфильтрован на кулдауне")
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
                if signal == 'BUY':
                    return True
                else:
                    return False
            
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
            elif signal == 'SELL' and position.quantity <= 0:
                # Продажа при короткой позиции - только если прошло достаточно времени
                return False
            elif signal == 'HOLD' and position.quantity <= 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки возможности изменения позиции: {e}")
            return False
    
    async def _can_execute_signal_by_type(self, signal: TradingSignal) -> bool:
        """
        Проверка возможности выполнения сигнала с учетом типа и задержек
        
        Args:
            signal: Торговый сигнал
            
        Returns:
            True если сигнал можно выполнить
        """
        try:
            symbol = signal.symbol
            signal_type = signal.signal
            current_time = datetime.now()
            
            # Определяем задержку в зависимости от типа сигнала
            if signal_type == 'BUY':
                cooldown = self.buy_cooldown
            elif signal_type == 'SELL':
                cooldown = self.sell_cooldown
            elif signal_type == 'HOLD':
                cooldown = self.hold_cooldown
            else:
                cooldown = self.min_trade_interval
            
            # Проверка времени последней сделки
            if self.portfolio_manager and symbol in self.portfolio_manager.last_trade_time:
                time_since_last_trade = current_time - self.portfolio_manager.last_trade_time[symbol]
                if time_since_last_trade.total_seconds() < cooldown:
                    logger.debug(f"⏸️ {symbol}: {signal_type} заблокирован - прошло {time_since_last_trade.total_seconds()/60:.1f} мин (нужно {cooldown/60:.1f} мин)")
                    return False
            
            # Дополнительные проверки для продаж
            if signal_type == 'SELL' and self.sell_protection_enabled:
                return await self._can_execute_sell_signal(signal)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки возможности выполнения сигнала: {e}")
            return False
    
    async def _can_execute_sell_signal(self, signal: TradingSignal) -> bool:
        """
        Проверка возможности выполнения сигнала продажи с дополнительными ограничениями
        
        Args:
            signal: Торговый сигнал продажи
            
        Returns:
            True если продажу можно выполнить
        """
        try:
            symbol = signal.symbol
            current_time = datetime.now()
            
            # Проверка времени последней продажи
            if self.portfolio_manager and symbol in self.portfolio_manager.last_trade_time:
                time_since_last_sell = current_time - self.portfolio_manager.last_trade_time[symbol]
                if time_since_last_sell.total_seconds() < self.sell_cooldown:
                    logger.info(f"⏸️ {symbol}: Продажа заблокирована - прошло {time_since_last_sell.total_seconds()/60:.1f} мин")
                    return False
            
            # Проверка количества продаж в час
            if self.portfolio_manager and symbol in self.portfolio_manager.sell_history:
                recent_sells = [
                    sell_time for sell_time in self.portfolio_manager.sell_history[symbol]
                    if (current_time - sell_time).total_seconds() < 3600
                ]
                if len(recent_sells) >= self.max_sells_per_hour:
                    logger.warning(f"⚠️ {symbol}: Превышен лимит продаж в час ({self.max_sells_per_hour})")
                    return False
            
            # Проверка увеличения уверенности (кроме панических продаж)
            if signal.confidence < self.panic_sell_threshold and self.portfolio_manager and symbol in self.portfolio_manager.last_sell_confidence:
                confidence_increase = signal.confidence - self.portfolio_manager.last_sell_confidence[symbol]
                if confidence_increase < self.min_confidence_increase:
                    logger.info(f"⏸️ {symbol}: Продажа заблокирована - недостаточное увеличение уверенности ({confidence_increase:.3f})")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки возможности продажи: {e}")
            return False
    
    def _get_signal_cooldown(self, signal_type: str) -> int:
        """
        Получение задержки для типа сигнала
        
        Args:
            signal_type: Тип сигнала (BUY/SELL/HOLD)
            
        Returns:
            Задержка в секундах
        """
        if signal_type == 'BUY':
            return self.buy_cooldown
        elif signal_type == 'SELL':
            return self.sell_cooldown
        elif signal_type == 'HOLD':
            return self.hold_cooldown
        else:
            return self.min_trade_interval
    
    async def execute_trades(self, signals: List[TradingSignal]):
        """
        Выполнение торговых операций с гибридным разрешением конфликтов
        
        Args:
            signals: Список торговых сигналов
        """
        try:
            logger.info(f"🔄 Обработка {len(signals)} торговых сигналов")
            
            # Гибридное разрешение конфликтующих сигналов
            resolved_signals = self.resolve_signals_hybrid(signals)
            logger.info(f"📊 После разрешения конфликтов: {len(resolved_signals)} сигналов")
            
            executed_count = 0
            rejected_count = 0
            
            for signal in resolved_signals:
                try:
                    # Проверка возможности выполнения сигнала с учетом задержек
                    if not await self._can_execute_signal_by_type(signal):
                        logger.debug(f"⏸️ {signal.symbol}: Сигнал {signal.signal} заблокирован задержкой")
                        rejected_count += 1
                        continue
                    
                    # Сохраняем состояние до выполнения
                    initial_log_level = logger.level("INFO")
                    
                    await self._execute_signal(signal)
                    
                    # Подсчитываем результат (это приблизительная оценка)
                    if signal.signal != 'HOLD':
                        # Проверяем, был ли сигнал выполнен, анализируя последние логи
                        # В реальной реализации можно добавить флаг успешного выполнения
                        pass
                        
                except Exception as e:
                    logger.error(f"❌ {signal.symbol}: Критическая ошибка: {e}")
                    rejected_count += 1
            
            logger.info(f"📊 Статистика выполнения сигналов:")
            logger.info(f"   📈 Всего сигналов: {len(signals)}")
            logger.info(f"   🔄 После разрешения конфликтов: {len(resolved_signals)}")
            logger.info(f"   ⏸️  HOLD сигналов: {len([s for s in resolved_signals if s.signal == 'HOLD'])}")
            logger.info(f"   🔄 Активных сигналов: {len([s for s in resolved_signals if s.signal != 'HOLD'])}")
            logger.info(f"   ⚠️  Проверьте логи выше для детальной информации о каждом сигнале")
            
        except Exception as e:
            logger.error(f"Ошибка выполнения торговых операций: {e}")
    
    def resolve_signals_hybrid(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Гибридный подход к разрешению сигналов
        
        Args:
            signals: Список торговых сигналов
            
        Returns:
            Список разрешенных сигналов
        """
        try:
            if not signals:
                return []
            
            logger.debug(f"Начало разрешения {len(signals)} сигналов методом {self.signal_resolution_method}")
            
            # 1. Дедупликация - убираем повторяющиеся сигналы
            if self.enable_deduplication:
                deduplicated = self._deduplicate_signals(signals)
                logger.debug(f"После дедупликации: {len(deduplicated)} сигналов")
            else:
                deduplicated = signals
            
            # 2. Группировка по символам
            symbols_signals = self._group_by_symbol(deduplicated)
            logger.debug(f"Группировка по символам: {len(symbols_signals)} символов")
            
            # 3. Разрешение конфликтов для каждого символа
            resolved_signals = []
            for symbol, symbol_signals in symbols_signals.items():
                if len(symbol_signals) == 1:
                    resolved_signals.append(symbol_signals[0])
                else:
                    # Ансамблевое голосование с учетом приоритетов
                    resolved_signal = self._ensemble_voting_with_priority(symbol_signals)
                    resolved_signals.append(resolved_signal)
                    logger.debug(f"Разрешен конфликт для {symbol}: {resolved_signal.signal} (уверенность: {resolved_signal.confidence:.3f})")
            
            logger.info(f"✅ Разрешение сигналов завершено: {len(signals)} → {len(resolved_signals)}")
            return resolved_signals
            
        except Exception as e:
            logger.error(f"Ошибка разрешения сигналов: {e}")
            return signals  # Возвращаем исходные сигналы в случае ошибки
    
    def _deduplicate_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Удаление дублирующих сигналов
        
        Args:
            signals: Список сигналов
            
        Returns:
            Список уникальных сигналов
        """
        try:
            # Группируем по символу и типу сигнала
            signal_groups = {}
            for signal in signals:
                key = (signal.symbol, signal.signal)
                if key not in signal_groups:
                    signal_groups[key] = []
                signal_groups[key].append(signal)
            
            deduplicated = []
            for (symbol, signal_type), group_signals in signal_groups.items():
                if len(group_signals) == 1:
                    deduplicated.append(group_signals[0])
                else:
                    # Выбираем сигнал с наивысшей уверенностью
                    best_signal = max(group_signals, key=lambda s: s.confidence)
                    deduplicated.append(best_signal)
                    logger.debug(f"Дедупликация {symbol}: выбрано {signal_type} с уверенностью {best_signal.confidence:.3f}")
            
            return deduplicated
            
        except Exception as e:
            logger.error(f"Ошибка дедупликации сигналов: {e}")
            return signals
    
    def _group_by_symbol(self, signals: List[TradingSignal]) -> Dict[str, List[TradingSignal]]:
        """
        Группировка сигналов по символам
        
        Args:
            signals: Список сигналов
            
        Returns:
            Словарь {symbol: [signals]}
        """
        symbols_signals = {}
        for signal in signals:
            if signal.symbol not in symbols_signals:
                symbols_signals[signal.symbol] = []
            symbols_signals[signal.symbol].append(signal)
        
        return symbols_signals
    
    def _ensemble_voting_with_priority(self, signals: List[TradingSignal]) -> TradingSignal:
        """
        Ансамблевое голосование с учетом приоритетов и уверенности
        
        Args:
            signals: Список сигналов для одного символа
            
        Returns:
            Результирующий сигнал
        """
        try:
            if not signals:
                return None
            
            if len(signals) == 1:
                return signals[0]
            
            # Подсчет взвешенных голосов
            weighted_votes = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
            
            for signal in signals:
                weight = self.signal_weights.get(signal.signal, 1.0) * signal.confidence
                weighted_votes[signal.signal] += weight
                logger.debug(f"Голос {signal.signal}: вес {self.signal_weights.get(signal.signal, 1.0)} * уверенность {signal.confidence:.3f} = {weight:.3f}")
            
            # Выбор победителя
            winner_signal = max(weighted_votes.keys(), key=lambda k: weighted_votes[k])
            
            # Создание результирующего сигнала
            winner_signals = [s for s in signals if s.signal == winner_signal]
            best_confidence = max(s.confidence for s in winner_signals)
            
            logger.debug(f"Победитель: {winner_signal} с суммарным весом {weighted_votes[winner_signal]:.3f}")
            
            return TradingSignal(
                symbol=signals[0].symbol,
                signal=winner_signal,
                confidence=best_confidence,
                source='ensemble_resolved',
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Ошибка ансамблевого голосования: {e}")
            # Возвращаем сигнал с наивысшей уверенностью
            return max(signals, key=lambda s: s.confidence)
    
    async def _execute_signal(self, signal: TradingSignal):
        """
        Выполнение одного торгового сигнала
        
        Args:
            signal: Торговый сигнал
        """
        try:
            if signal.signal == 'HOLD':
                logger.debug(f"Сигнал {signal.symbol}: HOLD - пропускаем")
                return
            
            logger.info(f"Обработка сигнала {signal.signal} для {signal.symbol}")
            
            # Устанавливаем кулдаун для инструмента при обработке сигнала
            if self.portfolio_manager:
                await self.portfolio_manager.set_cooldown_for_symbol(signal.symbol, signal.signal)
            
            # Проверка доступности инструмента в брокере
            if self.broker_type in ['tinkoff', 'tbank'] and self.tbank_broker:
                if not self.tbank_broker.is_ticker_available(signal.symbol):
                    logger.info(f"⏸️ {signal.symbol}: Инструмент недоступен для торговли в T-Bank")
                    return
            
            # Проверка на запрет коротких продаж (маржинальной торговли)
            if signal.signal == 'SELL':
                if not await self._can_sell(signal.symbol):
                    logger.info(f"⏸️ {signal.symbol}: Невозможно продать - нет позиции")
                    return
            
            # Расчет размера позиции
            position_size = await self._calculate_position_size(signal)
            if position_size <= 0:
                logger.warning(f"❌ {signal.symbol}: Размер позиции равен 0 - недостаточно средств или акций")
                return
            
            # Создание ордера
            order = self._create_order(signal, position_size)
            if not order:
                logger.warning(f"❌ {signal.symbol}: Не удалось создать ордер")
                return
            
            # Выполнение ордера
            result = await self._submit_order(order)
            logger.debug(f"🔍 {signal.symbol}: Результат _submit_order: {result}, статус ордера: {order.status}")
            
            if result:
                logger.info(f"✅ {signal.symbol}: Сигнал {signal.signal} выполнен - {order.quantity} штук")
                
                # Сохранение уверенности последней продажи для защиты от частых продаж
                if signal.signal == 'SELL' and self.portfolio_manager:
                    await self.portfolio_manager.set_last_sell_confidence(signal.symbol, signal.confidence)
            else:
                logger.warning(f"❌ {signal.symbol}: Ордер не выполнен - ошибка брокера")
            
        except Exception as e:
            logger.error(f"❌ {signal.symbol}: Ошибка выполнения сигнала: {e}")
    
    async def _calculate_position_size(self, signal: TradingSignal) -> float:
        """
        Расчет размера позиции с учетом ограничений
        
        Args:
            signal: Торговый сигнал
            
        Returns:
            Размер позиции
        """
        try:
            if not self.portfolio_manager:
                return 0.0
            
            # Для продажи - проверяем доступное количество
            if signal.signal == 'SELL':
                positions = self.portfolio_manager.positions
                if signal.symbol not in positions:
                    logger.info(f"⏸️ {signal.symbol}: Нет позиции для продажи")
                    return 0.0
                
                # Возвращаем количество акций в позиции (или его часть)
                available_quantity = positions[signal.symbol].quantity
                if available_quantity <= 0:
                    logger.info(f"⏸️ {signal.symbol}: Недостаточно акций для продажи: {available_quantity}")
                    return 0.0
                
                # Продаем всю позицию или часть (в зависимости от конфигурации)
                sell_quantity = int(available_quantity * self.position_size)
                if sell_quantity < 1:
                    sell_quantity = int(available_quantity)  # Продаем все если меньше 1
                
                logger.info(f"✅ {signal.symbol}: Размер позиции для продажи: {sell_quantity} лотов из {available_quantity}")
                return float(sell_quantity)
            
            # Для покупки - расчет с учетом ограничений
            if not self.position_size_check:
                # Если проверки отключены, используем старую логику
                return await self._calculate_position_size_legacy(signal)
            
            # Получение текущего капитала и позиций
            portfolio_value = await self.portfolio_manager.get_portfolio_value()
            positions = self.portfolio_manager.positions
            
            # Проверка максимального общего воздействия
            current_invested_value = sum(pos.market_value for pos in positions.values())
            max_allowed_investment = portfolio_value * self.max_total_exposure
            
            if current_invested_value >= max_allowed_investment:
                logger.warning(f"❌ {signal.symbol}: Превышен лимит общего воздействия: {current_invested_value:.2f} ₽ >= {max_allowed_investment:.2f} ₽")
                return 0.0
            
            # Получение текущей цены
            current_price = await self._get_current_price(signal.symbol)
            if current_price <= 0:
                logger.warning(f"❌ {signal.symbol}: Не удалось получить текущую цену")
                return 0.0
            
            # Расчет максимально допустимого размера позиции
            max_position_value = portfolio_value * self.max_position_size
            min_position_value = portfolio_value * self.min_position_size
            
            # Проверка существующей позиции по символу
            existing_position_value = 0.0
            if signal.symbol in positions:
                existing_position_value = positions[signal.symbol].market_value
            
            # Расчет доступного размера для новой позиции
            available_for_position = min(
                max_position_value - existing_position_value,  # Не превышать лимит на позицию
                max_allowed_investment - current_invested_value  # Не превышать общий лимит
            )
            
            # Проверка минимального размера
            if available_for_position < min_position_value:
                logger.warning(f"❌ {signal.symbol}: Недостаточно средств для минимальной позиции: {available_for_position:.2f} ₽ < {min_position_value:.2f} ₽")
                return 0.0
            
            # Расчет количества акций
            quantity = available_for_position / current_price
            quantity = int(quantity)
            
            # Минимальная проверка
            if quantity < 1:
                logger.warning(f"❌ {signal.symbol}: Недостаточно средств для покупки (нужно минимум {current_price:.2f} ₽)")
                return 0.0
            
            position_value = quantity * current_price
            logger.info(f"✅ {signal.symbol}: Размер позиции для покупки: {quantity} лотов на {position_value:.2f} ₽ (лимит: {max_position_value:.2f} ₽)")
            return float(quantity)
            
        except Exception as e:
            logger.error(f"Ошибка расчета размера позиции: {e}")
            return 0.0
    
    async def _calculate_position_size_legacy(self, signal: TradingSignal) -> float:
        """
        Старый метод расчета размера позиции (без ограничений)
        """
        try:
            # Получение текущего капитала
            portfolio_value = await self.portfolio_manager.get_portfolio_value()
            
            # Расчет размера позиции как процент от капитала
            position_value = portfolio_value * self.position_size
            
            # Получение текущей цены
            current_price = await self._get_current_price(signal.symbol)
            if current_price <= 0:
                logger.warning(f"❌ {signal.symbol}: Не удалось получить текущую цену")
                return 0.0
            
            # Расчет количества акций
            quantity = position_value / current_price
            
            # Округление до целого количества акций
            quantity = int(quantity)
            
            # Минимальная проверка
            if quantity < 1:
                logger.warning(f"❌ {signal.symbol}: Недостаточно средств для покупки (нужно минимум {current_price:.2f} ₽)")
                return 0.0
            
            logger.info(f"✅ {signal.symbol}: Размер позиции для покупки: {quantity} лотов на {position_value:.2f} ₽")
            return float(quantity)
            
        except Exception as e:
            logger.error(f"Ошибка расчета размера позиции (legacy): {e}")
            return 0.0
    
    async def _can_sell(self, symbol: str) -> bool:
        """
        Проверка возможности продажи инструмента (есть ли позиция)
        Запрет коротких продаж (маржинальной торговли)
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            True если можно продавать (есть позиция), False иначе
        """
        try:
            if not self.portfolio_manager:
                return False
            
            # Получаем текущие позиции
            positions = self.portfolio_manager.positions
            
            # Проверяем наличие позиции по символу
            if symbol not in positions:
                logger.debug(f"Позиция {symbol} не найдена в портфеле, продажа запрещена")
                return False
            
            # Проверяем что количество положительное (не short позиция)
            position = positions[symbol]
            if position.quantity <= 0:
                logger.debug(f"Позиция {symbol} имеет нулевое или отрицательное количество: {position.quantity}, продажа запрещена")
                return False
            
            logger.debug(f"Позиция {symbol} доступна для продажи: {position.quantity} акций")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки возможности продажи {symbol}: {e}")
            return False
    
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
    
    async def _submit_order(self, order: Order) -> bool:
        """
        Отправка ордера брокеру
        
        Args:
            order: Ордер для отправки
            
        Returns:
            True если ордер успешно отправлен, False иначе
        """
        try:
            if self.broker_type == 'paper':
                await self._execute_paper_order(order)
            else:
                await self._execute_real_order(order)
            
            # Добавление в историю
            self.order_history.append(order)
            
            # Возвращаем True если ордер выполнен успешно
            return order.status == OrderStatus.FILLED
            
        except Exception as e:
            logger.error(f"Ошибка отправки ордера {order.order_id}: {e}")
            order.status = OrderStatus.REJECTED
            return False
    
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
            if self.broker_type in ['tinkoff', 'tbank'] and self.tbank_broker:
                await self._execute_tbank_order(order)
            else:
                logger.warning(f"Выполнение реальных ордеров для брокера {self.broker_type} не реализовано")
                order.status = OrderStatus.REJECTED
            
        except Exception as e:
            logger.error(f"Ошибка выполнения реального ордера: {e}")
            order.status = OrderStatus.REJECTED
    
    async def _execute_tbank_order(self, order: Order):
        """
        Выполнение ордера через T-Bank API
        
        Args:
            order: Ордер для выполнения
        """
        try:
            if not self.tbank_broker:
                logger.error("T-Bank брокер не инициализирован")
                order.status = OrderStatus.REJECTED
                return
            
            # Конвертация количества в целое (лоты)
            lots = int(order.quantity)
            if lots < 1:
                logger.warning(f"Количество лотов меньше 1: {order.quantity}")
                order.status = OrderStatus.REJECTED
                return
            
            # Размещение ордера в лотах
            order_info = await self.tbank_broker.place_order_lots(
                ticker=order.symbol,
                lots=lots,
                direction=order.side.value,
                order_type=order.order_type.value,
                price=order.price
            )
            
            if order_info:
                # Обновление информации об ордере
                order.filled_price = order_info.get('execution_price', order.price)
                order.filled_quantity = order.quantity
                order.filled_at = datetime.now()
                order.status = OrderStatus.FILLED
                order.commission = order_info.get('total_commission', 0)
                
                # Обновление портфеля
                if self.portfolio_manager:
                    await self._update_portfolio_from_order(order)
                
                logger.info(
                    f"T-Bank ордер {order_info.get('order_id')} выполнен: "
                    f"{order.filled_quantity} @ {order.filled_price}"
                )
            else:
                logger.error(f"Не удалось разместить ордер через T-Bank")
                order.status = OrderStatus.REJECTED
            
        except Exception as e:
            logger.error(f"Ошибка выполнения T-Bank ордера: {e}")
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

