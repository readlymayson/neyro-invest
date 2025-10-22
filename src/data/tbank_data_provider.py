"""
Провайдер данных через T-Bank (Tinkoff) Invest API
Поддерживает работу в sandbox и production режимах
"""

from typing import Dict, List, Optional
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from loguru import logger
import os

try:
    from tinkoff.invest import Client, AsyncClient, CandleInterval, HistoricCandle
    from tinkoff.invest.schemas import Share, GetLastPricesResponse
    from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX
    TINKOFF_AVAILABLE = True
except ImportError:
    TINKOFF_AVAILABLE = False
    logger.warning("Библиотека tinkoff-investments не установлена. T-Bank провайдер недоступен.")


class TBankDataProvider:
    """
    Провайдер данных через T-Bank Invest API
    Документация: https://developer.tbank.ru/invest/intro/developer/sandbox
    """
    
    def __init__(self, token: str, sandbox: bool = True):
        """
        Инициализация провайдера T-Bank
        
        Args:
            token: API токен T-Bank Invest
            sandbox: Использовать песочницу (True) или prod (False)
        """
        if not TINKOFF_AVAILABLE:
            raise ImportError(
                "Для работы с T-Bank API необходимо установить библиотеку: "
                "pip install tinkoff-investments"
            )
        
        self.token = token
        self.sandbox = sandbox
        self.target = INVEST_GRPC_API_SANDBOX if sandbox else INVEST_GRPC_API
        
        # Кэш данных
        self.instruments_cache: Dict[str, str] = {}  # ticker -> figi
        self.last_prices_cache: Dict[str, float] = {}
        self.cache_timestamp: Optional[datetime] = None
        
        mode = "SANDBOX" if sandbox else "PRODUCTION"
        logger.info(f"Инициализирован T-Bank провайдер данных в режиме {mode}")
    
    async def initialize(self):
        """
        Инициализация провайдера - загрузка списка инструментов
        """
        logger.info("Инициализация T-Bank провайдера")
        
        try:
            async with AsyncClient(self.token, target=self.target) as client:
                # Загрузка списка акций
                response = await client.instruments.shares()
                
                for share in response.instruments:
                    # Сохраняем только торгуемые инструменты
                    if share.api_trade_available_flag:
                        self.instruments_cache[share.ticker] = share.figi
                
                logger.info(f"Загружено {len(self.instruments_cache)} инструментов")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации T-Bank провайдера: {e}")
            raise
    
    def _ticker_to_figi(self, ticker: str) -> Optional[str]:
        """
        Конвертация тикера в FIGI
        
        Args:
            ticker: Тикер инструмента
            
        Returns:
            FIGI инструмента или None
        """
        return self.instruments_cache.get(ticker)
    
    async def get_historical_data(
        self, 
        ticker: str, 
        period: str = "1y",
        interval: str = "day"
    ) -> pd.DataFrame:
        """
        Получение исторических данных
        
        Args:
            ticker: Тикер инструмента (например, "SBER")
            period: Период данных (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y)
            interval: Интервал свечей (1min, 5min, 15min, hour, day)
            
        Returns:
            DataFrame с историческими данными (OHLCV)
        """
        try:
            figi = self._ticker_to_figi(ticker)
            if not figi:
                logger.warning(f"FIGI не найден для тикера {ticker}")
                return pd.DataFrame()
            
            # Конвертация периода в даты
            to_date = datetime.now()
            period_map = {
                "1d": timedelta(days=1),
                "5d": timedelta(days=5),
                "1mo": timedelta(days=30),
                "3mo": timedelta(days=90),
                "6mo": timedelta(days=180),
                "1y": timedelta(days=365),
                "2y": timedelta(days=730),
            }
            from_date = to_date - period_map.get(period, timedelta(days=365))
            
            # Конвертация интервала
            interval_map = {
                "1min": CandleInterval.CANDLE_INTERVAL_1_MIN,
                "5min": CandleInterval.CANDLE_INTERVAL_5_MIN,
                "15min": CandleInterval.CANDLE_INTERVAL_15_MIN,
                "hour": CandleInterval.CANDLE_INTERVAL_HOUR,
                "day": CandleInterval.CANDLE_INTERVAL_DAY,
            }
            candle_interval = interval_map.get(interval, CandleInterval.CANDLE_INTERVAL_DAY)
            
            async with AsyncClient(self.token, target=self.target) as client:
                candles = []
                async for candle in client.get_all_candles(
                    figi=figi,
                    from_=from_date,
                    to=to_date,
                    interval=candle_interval,
                ):
                    candles.append(candle)
                
                # Конвертация в DataFrame
                if not candles:
                    logger.warning(f"Нет данных для {ticker}")
                    return pd.DataFrame()
                
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
                
                logger.debug(f"Получены исторические данные для {ticker}: {len(df)} записей")
                return df
                
        except Exception as e:
            logger.error(f"Ошибка получения исторических данных для {ticker}: {e}")
            return pd.DataFrame()
    
    async def get_current_price(self, ticker: str) -> float:
        """
        Получение текущей цены инструмента
        
        Args:
            ticker: Тикер инструмента
            
        Returns:
            Текущая цена
        """
        try:
            figi = self._ticker_to_figi(ticker)
            if not figi:
                logger.warning(f"FIGI не найден для тикера {ticker}")
                return 0.0
            
            async with AsyncClient(self.token, target=self.target) as client:
                # Получение последней цены
                response = await client.market_data.get_last_prices(figi=[figi])
                
                if response.last_prices:
                    price = self._quotation_to_float(response.last_prices[0].price)
                    self.last_prices_cache[ticker] = price
                    return price
                
                return 0.0
                
        except Exception as e:
            logger.error(f"Ошибка получения текущей цены для {ticker}: {e}")
            return 0.0
    
    async def get_realtime_data(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Получение данных в реальном времени для нескольких инструментов
        
        Args:
            tickers: Список тикеров
            
        Returns:
            Словарь с данными по каждому тикеру
        """
        result = {}
        
        try:
            # Конвертация тикеров в FIGI
            figis = []
            ticker_to_figi = {}
            for ticker in tickers:
                figi = self._ticker_to_figi(ticker)
                if figi:
                    figis.append(figi)
                    ticker_to_figi[figi] = ticker
            
            if not figis:
                logger.warning("Не найдено FIGI для запрошенных тикеров")
                return result
            
            async with AsyncClient(self.token, target=self.target) as client:
                # Получение последних цен
                response = await client.market_data.get_last_prices(figi=figis)
                
                for last_price in response.last_prices:
                    ticker = ticker_to_figi.get(last_price.figi)
                    if ticker:
                        price = self._quotation_to_float(last_price.price)
                        
                        # Получение дополнительной информации (дневные изменения)
                        # В продакшене можно использовать стримы для real-time данных
                        result[ticker] = {
                            'price': price,
                            'figi': last_price.figi,
                            'timestamp': last_price.time.isoformat() if last_price.time else datetime.now().isoformat(),
                            'change': 0.0,  # Требует дополнительного запроса
                            'change_percent': 0.0,
                            'volume': 0,
                        }
                        
                        self.last_prices_cache[ticker] = price
                
                self.cache_timestamp = datetime.now()
                logger.debug(f"Обновлены цены для {len(result)} инструментов")
                
        except Exception as e:
            logger.error(f"Ошибка получения данных в реальном времени: {e}")
        
        return result
    
    async def get_orderbook(self, ticker: str, depth: int = 10) -> Dict:
        """
        Получение стакана заявок
        
        Args:
            ticker: Тикер инструмента
            depth: Глубина стакана
            
        Returns:
            Словарь со стаканом заявок
        """
        try:
            figi = self._ticker_to_figi(ticker)
            if not figi:
                logger.warning(f"FIGI не найден для тикера {ticker}")
                return {}
            
            async with AsyncClient(self.token, target=self.target) as client:
                response = await client.market_data.get_order_book(
                    figi=figi,
                    depth=depth
                )
                
                return {
                    'figi': figi,
                    'depth': depth,
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
                
        except Exception as e:
            logger.error(f"Ошибка получения стакана для {ticker}: {e}")
            return {}
    
    def _quotation_to_float(self, quotation) -> float:
        """
        Конвертация Quotation в float
        
        Args:
            quotation: Объект Quotation из T-Bank API
            
        Returns:
            Число с плавающей точкой
        """
        if quotation is None:
            return 0.0
        return quotation.units + quotation.nano / 1_000_000_000
    
    async def search_instrument(self, query: str) -> List[Dict]:
        """
        Поиск инструментов по запросу
        
        Args:
            query: Поисковый запрос (тикер или название)
            
        Returns:
            Список найденных инструментов
        """
        try:
            async with AsyncClient(self.token, target=self.target) as client:
                response = await client.instruments.find_instrument(query=query)
                
                instruments = []
                for instrument in response.instruments:
                    instruments.append({
                        'ticker': instrument.ticker,
                        'figi': instrument.figi,
                        'name': instrument.name,
                        'type': instrument.instrument_type,
                        'currency': instrument.currency,
                    })
                
                return instruments
                
        except Exception as e:
            logger.error(f"Ошибка поиска инструментов по запросу '{query}': {e}")
            return []
    
    def get_status(self) -> Dict:
        """
        Получение статуса провайдера
        
        Returns:
            Словарь со статусом
        """
        return {
            'provider': 'T-Bank Invest API',
            'mode': 'sandbox' if self.sandbox else 'production',
            'instruments_loaded': len(self.instruments_cache),
            'cached_prices': len(self.last_prices_cache),
            'last_update': self.cache_timestamp.isoformat() if self.cache_timestamp else None,
        }


