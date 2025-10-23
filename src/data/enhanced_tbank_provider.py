"""
Расширенный провайдер данных через T-Bank Invest API
Включает стакан заявок, расширенные рыночные данные и множественные источники
"""

from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import asyncio
from datetime import datetime, timedelta
from loguru import logger
import os
from abc import ABC, abstractmethod

try:
    from tinkoff.invest import Client, AsyncClient, CandleInterval, HistoricCandle
    from tinkoff.invest.schemas import Share, GetLastPricesResponse, OrderBook
    from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX
    TINKOFF_AVAILABLE = True
except ImportError:
    TINKOFF_AVAILABLE = False
    logger.warning("T-Bank API недоступен. Установите: pip install tinkoff-investments")


class BaseDataProvider(ABC):
    """Базовый класс для провайдеров данных"""
    
    @abstractmethod
    async def get_historical_data(self, symbol: str, period: str) -> pd.DataFrame:
        """Получение исторических данных"""
        pass
    
    @abstractmethod
    async def get_realtime_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Получение данных в реальном времени"""
        pass
    
    @abstractmethod
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Dict:
        """Получение стакана заявок"""
        pass


class EnhancedTBankProvider(BaseDataProvider):
    """
    Расширенный провайдер данных через T-Bank Invest API
    
    Возможности:
    - Исторические свечи с различными интервалами
    - Стакан заявок (order book) с глубиной
    - Данные в реальном времени
    - Информация об инструментах
    - Расширенные рыночные данные
    """
    
    def __init__(self, token: str, sandbox: bool = True, symbols: List[str] = None):
        """
        Инициализация провайдера
        
        Args:
            token: API токен T-Bank
            sandbox: Использовать песочницу
            symbols: Список отслеживаемых символов
        """
        if not TINKOFF_AVAILABLE:
            raise ImportError(
                "Для работы с T-Bank API необходимо установить библиотеку: "
                "pip install tinkoff-investments"
            )
        
        self.token = token
        self.sandbox = sandbox
        self.target = INVEST_GRPC_API_SANDBOX if sandbox else INVEST_GRPC_API
        self.symbols = symbols or []
        
        # Кэш данных
        self.instruments_cache: Dict[str, Dict] = {}  # ticker -> {figi, name, currency}
        self.orderbook_cache: Dict[str, Dict] = {}   # ticker -> orderbook data
        self.last_prices_cache: Dict[str, float] = {} # ticker -> last price
        
        # Интервалы для свечей
        self.candle_intervals = {
            '1m': CandleInterval.CANDLE_INTERVAL_1_MIN,
            '5m': CandleInterval.CANDLE_INTERVAL_5_MIN,
            '15m': CandleInterval.CANDLE_INTERVAL_15_MIN,
            '1h': CandleInterval.CANDLE_INTERVAL_HOUR,
            '1d': CandleInterval.CANDLE_INTERVAL_DAY
        }
        
        logger.info(f"Инициализирован расширенный T-Bank провайдер (sandbox={sandbox})")
        
        # Инициализация будет выполнена при первом вызове
        self._initialized = False
    
    async def initialize(self):
        """Инициализация провайдера"""
        if self._initialized:
            return
            
        try:
            async with AsyncClient(self.token, target=self.target) as client:
                # Загрузка списка инструментов
                await self._load_instruments(client)
                logger.info(f"Загружено {len(self.instruments_cache)} инструментов")
                self._initialized = True
                
        except Exception as e:
            logger.error(f"Ошибка инициализации T-Bank провайдера: {e}")
            raise
    
    async def _load_instruments(self, client):
        """Загрузка списка доступных инструментов"""
        try:
            # Получение акций
            shares_response = await client.instruments.shares()
            for share in shares_response.instruments:
                if share.api_trade_available_flag:
                    self.instruments_cache[share.ticker] = {
                        'figi': share.figi,
                        'name': share.name,
                        'currency': share.currency,
                        'trading_status': share.trading_status.name,
                        'type': 'share'
                    }
            
            # Получение облигаций
            bonds_response = await client.instruments.bonds()
            for bond in bonds_response.instruments:
                if bond.api_trade_available_flag:
                    self.instruments_cache[bond.ticker] = {
                        'figi': bond.figi,
                        'name': bond.name,
                        'currency': bond.currency,
                        'trading_status': bond.trading_status.name,
                        'type': 'bond'
                    }
            
            # Получение ETF
            etfs_response = await client.instruments.etfs()
            for etf in etfs_response.instruments:
                if etf.api_trade_available_flag:
                    self.instruments_cache[etf.ticker] = {
                        'figi': etf.figi,
                        'name': etf.name,
                        'currency': etf.currency,
                        'trading_status': etf.trading_status.name,
                        'type': 'etf'
                    }
                    
        except Exception as e:
            logger.error(f"Ошибка загрузки инструментов: {e}")
            raise
    
    def _ticker_to_figi(self, ticker: str) -> Optional[str]:
        """Получение FIGI по тикеру"""
        if not self._initialized:
            logger.warning("Провайдер не инициализирован, FIGI не найден")
            return None
        return self.instruments_cache.get(ticker, {}).get('figi')
    
    def _quotation_to_float(self, quotation) -> float:
        """Конвертация Quotation в float"""
        if quotation is None:
            return 0.0
        return float(quotation.units) + float(quotation.nano) / 1_000_000_000
    
    async def get_historical_data(
        self, 
        symbol: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Получение исторических данных
        
        Args:
            symbol: Тикер инструмента
            period: Период данных (1d, 1w, 1m, 3m, 6m, 1y, 2y, 5y)
            interval: Интервал свечей (1m, 5m, 15m, 1h, 1d)
            
        Returns:
            DataFrame с историческими данными
        """
        try:
            figi = self._ticker_to_figi(symbol)
            if not figi:
                logger.warning(f"FIGI не найден для тикера {symbol}")
                return pd.DataFrame()
            
            # Определение периода
            period_map = {
                '1d': 1, '1w': 7, '1m': 30, '3m': 90, 
                '6m': 180, '1y': 365, '2y': 730, '5y': 1825
            }
            days = period_map.get(period, 365)
            
            # Определение интервала
            candle_interval = self.candle_intervals.get(interval, CandleInterval.CANDLE_INTERVAL_DAY)
            
            # Расчет дат
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            async with AsyncClient(self.token, target=self.target) as client:
                candles = []
                async for candle in client.get_all_candles(
                    figi=figi,
                    from_=from_date,
                    to=to_date,
                    interval=candle_interval,
                ):
                    candles.append(candle)
                
                if not candles:
                    logger.warning(f"Нет данных для {symbol}")
                    return pd.DataFrame()
                
                # Конвертация в DataFrame
                data = []
                for candle in candles:
                    data.append({
                        'Open': self._quotation_to_float(candle.open),
                        'High': self._quotation_to_float(candle.high),
                        'Low': self._quotation_to_float(candle.low),
                        'Close': self._quotation_to_float(candle.close),
                        'Volume': candle.volume,
                        'Time': candle.time
                    })
                
                df = pd.DataFrame(data)
                df.set_index('Time', inplace=True)
                df.sort_index(inplace=True)
                
                logger.debug(f"Получены исторические данные для {symbol}: {len(df)} записей")
                return df
                
        except Exception as e:
            logger.error(f"Ошибка получения исторических данных для {symbol}: {e}")
            return pd.DataFrame()
    
    async def get_realtime_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Получение данных в реальном времени
        
        Args:
            symbols: Список тикеров
            
        Returns:
            Словарь с данными по тикерам
        """
        result = {}
        
        try:
            # Получение FIGI для всех символов
            figi_list = []
            symbol_to_figi = {}
            
            for symbol in symbols:
                figi = self._ticker_to_figi(symbol)
                if figi:
                    figi_list.append(figi)
                    symbol_to_figi[figi] = symbol
            
            if not figi_list:
                logger.warning("Нет доступных FIGI для получения данных")
                return result
            
            async with AsyncClient(self.token, target=self.target) as client:
                # Получение последних цен
                last_prices_response = await client.market_data.get_last_prices(figi=figi_list)
                
                for price_data in last_prices_response.last_prices:
                    symbol = symbol_to_figi.get(price_data.figi)
                    if symbol:
                        result[symbol] = {
                            'price': self._quotation_to_float(price_data.price),
                            'timestamp': price_data.time.isoformat(),
                            'figi': price_data.figi
                        }
                        
                        # Обновление кэша
                        self.last_prices_cache[symbol] = self._quotation_to_float(price_data.price)
                
                logger.debug(f"Получены данные в реальном времени для {len(result)} инструментов")
                
        except Exception as e:
            logger.error(f"Ошибка получения данных в реальном времени: {e}")
        
        return result
    
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Dict:
        """
        Получение стакана заявок
        
        Args:
            symbol: Тикер инструмента
            depth: Глубина стакана
            
        Returns:
            Словарь со стаканом заявок
        """
        try:
            figi = self._ticker_to_figi(symbol)
            if not figi:
                logger.warning(f"FIGI не найден для тикера {symbol}")
                return {}
            
            async with AsyncClient(self.token, target=self.target) as client:
                response = await client.market_data.get_order_book(
                    figi=figi,
                    depth=depth
                )
                
                orderbook = {
                    'symbol': symbol,
                    'figi': figi,
                    'depth': depth,
                    'timestamp': datetime.now().isoformat(),  # Используем текущее время
                    'bids': [
                        {
                            'price': self._quotation_to_float(bid.price),
                            'quantity': bid.quantity
                        }
                        for bid in response.bids
                    ],
                    'asks': [
                        {
                            'price': self._quotation_to_float(ask.price),
                            'quantity': ask.quantity
                        }
                        for ask in response.asks
                    ],
                    'last_price': self._quotation_to_float(response.last_price) if response.last_price else 0.0,
                }
                
                # Расчет дополнительных метрик
                if orderbook['bids'] and orderbook['asks']:
                    best_bid = orderbook['bids'][0]['price']
                    best_ask = orderbook['asks'][0]['price']
                    orderbook['spread'] = best_ask - best_bid
                    orderbook['spread_percent'] = (orderbook['spread'] / best_ask) * 100
                    orderbook['mid_price'] = (best_bid + best_ask) / 2
                    
                    # Объемы в стакане
                    orderbook['total_bid_volume'] = sum(bid['quantity'] for bid in orderbook['bids'])
                    orderbook['total_ask_volume'] = sum(ask['quantity'] for ask in orderbook['asks'])
                    orderbook['volume_imbalance'] = orderbook['total_bid_volume'] - orderbook['total_ask_volume']
                
                # Обновление кэша
                self.orderbook_cache[symbol] = orderbook
                
                logger.debug(f"Получен стакан заявок для {symbol}: {len(orderbook['bids'])} bids, {len(orderbook['asks'])} asks")
                return orderbook
                
        except Exception as e:
            logger.error(f"Ошибка получения стакана для {symbol}: {e}")
            return {}
    
    async def get_enhanced_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Получение расширенных рыночных данных
        
        Включает:
        - Базовые цены и объемы
        - Стакан заявок
        - Спреды и метрики ликвидности
        - Информацию об инструментах
        
        Args:
            symbols: Список тикеров
            
        Returns:
            Словарь с расширенными данными
        """
        result = {}
        
        try:
            # Получение базовых данных
            realtime_data = await self.get_realtime_data(symbols)
            
            for symbol in symbols:
                if symbol not in realtime_data:
                    continue
                
                # Получение стакана заявок
                orderbook = await self.get_orderbook(symbol, depth=10)
                
                # Информация об инструменте
                instrument_info = self.instruments_cache.get(symbol, {})
                
                # Объединение всех данных
                result[symbol] = {
                    # Базовые данные
                    'price': realtime_data[symbol]['price'],
                    'timestamp': realtime_data[symbol]['timestamp'],
                    'figi': realtime_data[symbol]['figi'],
                    
                    # Стакан заявок
                    'orderbook': orderbook,
                    
                    # Информация об инструменте
                    'instrument': {
                        'name': instrument_info.get('name', ''),
                        'currency': instrument_info.get('currency', ''),
                        'type': instrument_info.get('type', ''),
                        'trading_status': instrument_info.get('trading_status', '')
                    },
                    
                    # Дополнительные метрики
                    'metrics': {
                        'spread': orderbook.get('spread', 0),
                        'spread_percent': orderbook.get('spread_percent', 0),
                        'mid_price': orderbook.get('mid_price', 0),
                        'volume_imbalance': orderbook.get('volume_imbalance', 0),
                        'total_bid_volume': orderbook.get('total_bid_volume', 0),
                        'total_ask_volume': orderbook.get('total_ask_volume', 0)
                    }
                }
                
            logger.debug(f"Получены расширенные данные для {len(result)} инструментов")
            
        except Exception as e:
            logger.error(f"Ошибка получения расширенных данных: {e}")
        
        return result
    
    async def get_available_instruments(self) -> Dict[str, Dict]:
        """Получение списка доступных инструментов"""
        return self.instruments_cache.copy()
    
    async def get_instrument_info(self, symbol: str) -> Dict:
        """Получение информации об инструменте"""
        return self.instruments_cache.get(symbol, {})
    
    def get_cached_orderbook(self, symbol: str) -> Optional[Dict]:
        """Получение кэшированного стакана заявок"""
        return self.orderbook_cache.get(symbol)
    
    def get_cached_price(self, symbol: str) -> Optional[float]:
        """Получение кэшированной цены"""
        return self.last_prices_cache.get(symbol)


class MultiProviderDataProvider(BaseDataProvider):
    """
    Провайдер данных с поддержкой множественных источников
    
    Может использовать несколько провайдеров одновременно:
    - T-Bank API (основной)
    - YFinance (резервный)
    - Другие источники
    """
    
    def __init__(self, providers: List[BaseDataProvider], primary_provider: str = "tbank"):
        """
        Инициализация множественного провайдера
        
        Args:
            providers: Список провайдеров данных
            primary_provider: Основной провайдер
        """
        self.providers = {provider.__class__.__name__: provider for provider in providers}
        self.primary_provider = primary_provider
        self.fallback_providers = [name for name in self.providers.keys() if name != primary_provider]
        
        logger.info(f"Инициализирован множественный провайдер: {list(self.providers.keys())}")
    
    async def get_historical_data(self, symbol: str, period: str) -> pd.DataFrame:
        """Получение исторических данных с fallback"""
        for provider_name in [self.primary_provider] + self.fallback_providers:
            try:
                provider = self.providers[provider_name]
                data = await provider.get_historical_data(symbol, period)
                if not data.empty:
                    logger.debug(f"Данные получены от {provider_name}")
                    return data
            except Exception as e:
                logger.warning(f"Ошибка получения данных от {provider_name}: {e}")
                continue
        
        logger.error(f"Не удалось получить данные для {symbol} ни от одного провайдера")
        return pd.DataFrame()
    
    async def get_realtime_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Получение данных в реальном времени с fallback"""
        for provider_name in [self.primary_provider] + self.fallback_providers:
            try:
                provider = self.providers[provider_name]
                data = await provider.get_realtime_data(symbols)
                if data:
                    logger.debug(f"Данные получены от {provider_name}")
                    return data
            except Exception as e:
                logger.warning(f"Ошибка получения данных от {provider_name}: {e}")
                continue
        
        logger.error(f"Не удалось получить данные ни от одного провайдера")
        return {}
    
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Dict:
        """Получение стакана заявок (только от T-Bank)"""
        tbank_provider = self.providers.get('EnhancedTBankProvider')
        if tbank_provider:
            return await tbank_provider.get_orderbook(symbol, depth)
        else:
            logger.warning("T-Bank провайдер недоступен для получения стакана заявок")
            return {}
