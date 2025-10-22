"""
Провайдер данных для российского рынка
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import asyncio
from abc import ABC, abstractmethod
from .russian_data_provider import RussianDataProvider


class MarketDataProvider(ABC):
    """
    Абстрактный класс провайдера данных рынка
    """
    
    @abstractmethod
    async def get_historical_data(self, symbol: str, period: str) -> pd.DataFrame:
        """
        Получение исторических данных
        
        Args:
            symbol: Тикер инструмента
            period: Период данных
            
        Returns:
            DataFrame с историческими данными
        """
        pass
    
    @abstractmethod
    async def get_current_price(self, symbol: str) -> float:
        """
        Получение текущей цены
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            Текущая цена
        """
        pass
    
    @abstractmethod
    async def get_realtime_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Получение данных в реальном времени
        
        Args:
            symbols: Список тикеров
            
        Returns:
            Словарь с данными по тикерам
        """
        pass


class YFinanceProvider(MarketDataProvider):
    """
    Провайдер данных через Yahoo Finance
    """
    
    def __init__(self, symbols: List[str]):
        """
        Инициализация провайдера
        
        Args:
            symbols: Список тикеров для отслеживания
        """
        self.symbols = symbols
        self.last_update = None
        self.cache: Dict[str, pd.DataFrame] = {}
        
        # Российские тикеры для Yahoo Finance
        self.russian_symbols = {
            'SBER': 'SBER.ME',
            'GAZP': 'GAZP.ME', 
            'LKOH': 'LKOH.ME',
            'NVTK': 'NVTK.ME',
            'ROSN': 'ROSN.ME',
            'NLMK': 'NLMK.ME',
            'MAGN': 'MAGN.ME',
            'YNDX': 'YNDX.ME'
        }
        
        # Российский провайдер для моковых данных
        self.russian_provider = RussianDataProvider(symbols)
        
        logger.info(f"Инициализирован провайдер YFinance для {len(symbols)} инструментов")
    
    async def get_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """
        Получение исторических данных
        
        Args:
            symbol: Тикер инструмента
            period: Период данных (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            DataFrame с историческими данными
        """
        try:
            # Конвертация российского тикера
            yf_symbol = self._convert_symbol(symbol)
            
            ticker = yf.Ticker(yf_symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                logger.warning(f"Нет данных для символа {symbol} через YFinance, используем российский провайдер")
                # Используем российский провайдер как fallback
                return await self.russian_provider.get_historical_data(symbol, period)
            
            # Очистка данных
            data = self._clean_data(data)
            
            # Кэширование
            self.cache[symbol] = data
            
            logger.debug(f"Получены исторические данные для {symbol}: {len(data)} записей")
            return data
            
        except Exception as e:
            logger.error(f"Ошибка получения исторических данных для {symbol}: {e}")
            return pd.DataFrame()
    
    async def get_current_price(self, symbol: str) -> float:
        """
        Получение текущей цены
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            Текущая цена
        """
        try:
            yf_symbol = self._convert_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            
            info = ticker.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            if current_price == 0:
                # Попытка получить из последних данных
                data = await self.get_historical_data(symbol, "1d")
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                else:
                    # Используем российский провайдер
                    logger.warning(f"Нет данных для {symbol} через YFinance, используем российский провайдер")
                    return await self.russian_provider.get_current_price(symbol)
            
            return float(current_price)
            
        except Exception as e:
            logger.error(f"Ошибка получения текущей цены для {symbol}: {e}")
            return 0.0
    
    async def get_realtime_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Получение данных в реальном времени
        
        Args:
            symbols: Список тикеров
            
        Returns:
            Словарь с данными по тикерам
        """
        result = {}
        
        for symbol in symbols:
            try:
                yf_symbol = self._convert_symbol(symbol)
                ticker = yf.Ticker(yf_symbol)
                info = ticker.info
                
                result[symbol] = {
                    'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                    'volume': info.get('volume', 0),
                    'change': info.get('regularMarketChange', 0),
                    'change_percent': info.get('regularMarketChangePercent', 0),
                    'market_cap': info.get('marketCap', 0),
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Ошибка получения данных в реальном времени для {symbol}: {e}")
                result[symbol] = {
                    'price': 0,
                    'volume': 0,
                    'change': 0,
                    'change_percent': 0,
                    'market_cap': 0,
                    'timestamp': datetime.now().isoformat()
                }
        
        return result
    
    def _convert_symbol(self, symbol: str) -> str:
        """
        Конвертация тикера в формат Yahoo Finance
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            Тикер в формате Yahoo Finance
        """
        # Если это российский тикер, добавляем .ME
        if symbol in self.russian_symbols:
            return self.russian_symbols[symbol]
        
        # Если это американский тикер, возвращаем как есть
        return symbol
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Очистка данных от пропусков и выбросов
        
        Args:
            data: Исходные данные
            
        Returns:
            Очищенные данные
        """
        # Удаление строк с NaN
        data = data.dropna()
        
        # Удаление выбросов (цены больше 3 стандартных отклонений)
        for column in ['Open', 'High', 'Low', 'Close']:
            if column in data.columns:
                mean = data[column].mean()
                std = data[column].std()
                data = data[abs(data[column] - mean) <= 3 * std]
        
        return data


class DataProvider:
    """
    Основной провайдер данных системы
    """
    
    def __init__(self, config: Dict):
        """
        Инициализация провайдера данных
        
        Args:
            config: Конфигурация провайдера данных
        """
        self.config = config
        self.symbols = config.get('symbols', [])
        self.update_interval = config.get('update_interval', 60)
        self.history_days = config.get('history_days', 365)
        provider_type = config.get('provider', 'yfinance').lower()
        
        # Инициализация провайдера в зависимости от типа
        if provider_type == 'russian':
            self.provider = RussianDataProvider(self.symbols)
            logger.info(f"Используется российский провайдер данных для {len(self.symbols)} инструментов")
        else:
            self.provider = YFinanceProvider(self.symbols)
            logger.info(f"Используется YFinance провайдер данных для {len(self.symbols)} инструментов")
        
        # Кэш данных
        self.market_data: Dict[str, pd.DataFrame] = {}
        self.realtime_data: Dict[str, Dict] = {}
        self.last_update = None
        
        logger.info(f"Провайдер данных инициализирован для {len(self.symbols)} инструментов")
    
    async def initialize(self):
        """
        Инициализация провайдера данных
        """
        logger.info("Инициализация провайдера данных")
        
        # Загрузка исторических данных
        await self._load_historical_data()
        
        # Первоначальное обновление данных в реальном времени
        await self.update_market_data()
        
        logger.info("Провайдер данных инициализирован")
    
    async def _load_historical_data(self):
        """
        Загрузка исторических данных
        """
        logger.info("Загрузка исторических данных")
        
        for symbol in self.symbols:
            try:
                data = await self.provider.get_historical_data(
                    symbol, 
                    period=f"{self.history_days}d"
                )
                
                if not data.empty:
                    self.market_data[symbol] = data
                    logger.debug(f"Загружены исторические данные для {symbol}: {len(data)} записей")
                else:
                    logger.warning(f"Не удалось загрузить исторические данные для {symbol}")
                    
            except Exception as e:
                logger.error(f"Ошибка загрузки исторических данных для {symbol}: {e}")
        
        logger.info(f"Загружены исторические данные для {len(self.market_data)} инструментов")
    
    async def update_market_data(self):
        """
        Обновление рыночных данных
        """
        try:
            # Обновление данных в реальном времени
            self.realtime_data = await self.provider.get_realtime_data(self.symbols)
            
            # Обновление последней записи в исторических данных
            for symbol in self.symbols:
                if symbol in self.market_data:
                    current_price = self.realtime_data.get(symbol, {}).get('price', 0)
                    if current_price > 0:
                        # Добавление новой записи
                        new_row = pd.DataFrame({
                            'Open': [current_price],
                            'High': [current_price],
                            'Low': [current_price],
                            'Close': [current_price],
                            'Volume': [self.realtime_data.get(symbol, {}).get('volume', 0)]
                        }, index=[datetime.now()])
                        
                        self.market_data[symbol] = pd.concat([self.market_data[symbol], new_row])
                        
                        # Ограничение размера данных
                        if len(self.market_data[symbol]) > 1000:
                            self.market_data[symbol] = self.market_data[symbol].tail(1000)
            
            self.last_update = datetime.now()
            logger.debug(f"Данные обновлены: {len(self.realtime_data)} инструментов")
            
        except Exception as e:
            logger.error(f"Ошибка обновления данных: {e}")
    
    async def get_latest_data(self, symbol: Optional[str] = None) -> Dict:
        """
        Получение последних данных
        
        Args:
            symbol: Тикер инструмента (если None, то для всех)
            
        Returns:
            Словарь с последними данными
        """
        if symbol:
            return {
                'historical': self.market_data.get(symbol, pd.DataFrame()),
                'realtime': self.realtime_data.get(symbol, {}),
                'symbol': symbol
            }
        else:
            return {
                'historical': self.market_data,
                'realtime': self.realtime_data,
                'last_update': self.last_update
            }
    
    def get_technical_indicators(self, symbol: str) -> Dict:
        """
        Расчет технических индикаторов
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            Словарь с техническими индикаторами
        """
        if symbol not in self.market_data:
            return {}
        
        data = self.market_data[symbol].copy()
        
        try:
            # Простые скользящие средние
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            
            # Экспоненциальные скользящие средние
            data['EMA_12'] = data['Close'].ewm(span=12).mean()
            data['EMA_26'] = data['Close'].ewm(span=26).mean()
            
            # MACD
            data['MACD'] = data['EMA_12'] - data['EMA_26']
            data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
            
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            data['BB_Middle'] = data['Close'].rolling(window=20).mean()
            bb_std = data['Close'].rolling(window=20).std()
            data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
            data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)
            
            # Возврат последних значений
            last_row = data.iloc[-1]
            return {
                'sma_20': last_row['SMA_20'],
                'sma_50': last_row['SMA_50'],
                'ema_12': last_row['EMA_12'],
                'ema_26': last_row['EMA_26'],
                'macd': last_row['MACD'],
                'macd_signal': last_row['MACD_Signal'],
                'rsi': last_row['RSI'],
                'bb_upper': last_row['BB_Upper'],
                'bb_middle': last_row['BB_Middle'],
                'bb_lower': last_row['BB_Lower']
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета технических индикаторов для {symbol}: {e}")
            return {}
    
    def get_status(self) -> Dict:
        """
        Получение статуса провайдера данных
        
        Returns:
            Словарь со статусом
        """
        return {
            'symbols_count': len(self.symbols),
            'data_loaded': len(self.market_data),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'realtime_data_count': len(self.realtime_data)
        }

