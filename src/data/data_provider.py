"""
Провайдер данных для российского рынка
Поддерживает множественные источники данных
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance не установлен, YFinanceProvider недоступен")
import asyncio
from abc import ABC, abstractmethod
from .russian_data_provider import RussianDataProvider
from .enhanced_tbank_provider import EnhancedTBankProvider, MultiProviderDataProvider
from .news_data_provider import NewsDataProvider


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
        if not YFINANCE_AVAILABLE:
            raise ImportError("yfinance не установлен. Установите: pip install yfinance")
        
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
            if not YFINANCE_AVAILABLE:
                logger.warning("yfinance недоступен, используем российский провайдер")
                return await self.russian_provider.get_historical_data(symbol, period)
            
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
    Поддерживает множественные источники данных
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
        provider_type = config.get('provider', 'tbank').lower()
        
        # Инициализация провайдера в зависимости от типа
        if provider_type == 'tbank':
            # Используем T-Bank API как основной провайдер
            token = config.get('tbank_token')
            
            # Если токен не указан в конфигурации, загружаем из переменной окружения
            if not token:
                token = os.environ.get('TINKOFF_TOKEN')
                if not token:
                    logger.warning("T-Bank токен не найден в конфигурации и переменной окружения, используем fallback провайдеры")
                    self.provider = self._create_fallback_provider()
                else:
                    logger.info("T-Bank токен загружен из переменной окружения TINKOFF_TOKEN")
                    sandbox = config.get('tbank_sandbox', True)
                    self.provider = EnhancedTBankProvider(token, sandbox, self.symbols)
                    logger.info(f"Используется T-Bank провайдер данных для {len(self.symbols)} инструментов")
            else:
                sandbox = config.get('tbank_sandbox', True)
                # Поддержка автоматического определения счета
                account_id = config.get('tbank_account_id')
                if account_id is None:
                    logger.info("Account ID не указан, будет определен автоматически")
                self.provider = EnhancedTBankProvider(token, sandbox, self.symbols)
                logger.info(f"Используется T-Bank провайдер данных для {len(self.symbols)} инструментов")
        elif provider_type == 'multi':
            # Множественный провайдер
            self.provider = self._create_multi_provider()
            logger.info("Используется множественный провайдер данных")
        elif provider_type == 'russian':
            self.provider = RussianDataProvider(self.symbols)
            logger.info(f"Используется российский провайдер данных для {len(self.symbols)} инструментов")
        else:
            self.provider = YFinanceProvider(self.symbols)
            logger.info(f"Используется YFinance провайдер данных для {len(self.symbols)} инструментов")
        
        # Кэш данных
        self.market_data: Dict[str, pd.DataFrame] = {}
        self.realtime_data: Dict[str, Dict] = {}
        self.enhanced_data: Dict[str, Dict] = {}  # Расширенные данные со стаканом заявок
        self.news_data: Dict[str, Dict] = {}  # Новостные данные для анализа (короткий период)
        self.news_training_data: Dict[str, Dict] = {}  # Новостные данные для обучения (длинный период)
        self.last_update = None
        
        # Инициализация новостного провайдера
        news_config = config.get('news', {})
        if news_config.get('enabled', True):
            self.news_provider = NewsDataProvider(news_config)
            logger.info("Новостной провайдер инициализирован")
        else:
            self.news_provider = None
            logger.info("Новостной провайдер отключен")
        
        logger.info(f"Провайдер данных инициализирован для {len(self.symbols)} инструментов")
    
    def _create_fallback_provider(self):
        """Создание fallback провайдера"""
        return YFinanceProvider(self.symbols)
    
    def _create_multi_provider(self):
        """Создание множественного провайдера"""
        providers = []
        
        # T-Bank провайдер (если доступен токен)
        token = self.config.get('tbank_token')
        if token:
            sandbox = self.config.get('tbank_sandbox', True)
            providers.append(EnhancedTBankProvider(token, sandbox, self.symbols))
        
        # YFinance провайдер как резервный
        providers.append(YFinanceProvider(self.symbols))
        
        return MultiProviderDataProvider(providers, primary_provider="EnhancedTBankProvider")
    
    async def initialize(self):
        """
        Инициализация провайдера данных
        """
        logger.info("Инициализация провайдера данных")
        
        # Инициализация T-Bank провайдера, если используется
        if hasattr(self.provider, 'initialize'):
            await self.provider.initialize()
        
        # Загрузка исторических данных
        await self._load_historical_data()
        
        # Первоначальное обновление данных в реальном времени
        await self.update_market_data()
        
        # Загрузка новостных данных
        if self.news_provider:
            await self._load_news_data()
        
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
    
    async def _load_news_data(self):
        """
        Загрузка новостных данных
        """
        try:
            if not self.news_provider:
                logger.info("Новостной провайдер не инициализирован")
                return
            
            # Проверяем, нужно ли загружать новостные данные
            news_config = self.config.get('news', {})
            if not news_config.get('enabled', True):
                logger.info("Новостные данные отключены в конфигурации")
                return
            
            logger.info("Загрузка новостных данных")
            
            # Определяем период для новостей
            days_for_analysis = news_config.get('days_back', 14)  # Для анализа
            days_for_training = news_config.get('training_news_days', 180)  # Для обучения
            
            # Получение новостей для анализа (2 недели)
            analysis_news_data = await self.news_provider.get_all_symbols_news(self.symbols, days=days_for_analysis)
            
            # Получение новостей для обучения из хранилища с дополнением недостающих данных
            training_news_data = None
            if news_config.get('include_news_in_training', False):
                # Используем метод get_training_news, который загружает из хранилища и дополняет недостающие данные
                if hasattr(self.news_provider, 'get_training_news'):
                    training_news_data = await self.news_provider.get_training_news(self.symbols, days_for_training)
                else:
                    # Fallback на старый метод
                    training_news_data = await self.news_provider.get_all_symbols_news(self.symbols, days=days_for_training)
                
                if training_news_data:
                    self.news_training_data = training_news_data
                    logger.info(f"Загружены новостные данные для обучения: {days_for_training} дней")
                else:
                    logger.warning("Не удалось загрузить новостные данные для обучения")
            
            if analysis_news_data:
                self.news_data = analysis_news_data
                logger.info(f"Загружены новостные данные для анализа: {len(analysis_news_data)} символов (сводки за {days_for_analysis} дней)")
                
                # Логирование сводки новостей
                for symbol, news_summary in analysis_news_data.items():
                    logger.debug(f"Новости для {symbol}: {news_summary.get('total_news', 0)} новостей, "
                               f"тональность: {news_summary.get('avg_sentiment', 0):.3f}, "
                               f"тренд: {news_summary.get('recent_trend', 'neutral')}")
            else:
                logger.warning("Не удалось загрузить новостные данные")
            
            # Архивация устаревших данных
            await self._archive_old_news(days_for_training)
                
        except Exception as e:
            logger.error(f"Ошибка загрузки новостных данных: {e}")
    
    async def _archive_old_news(self, training_days: int):
        """
        Архивация новостей старше training_days
        
        Args:
            training_days: Количество дней для обучения (данные старше архивируются)
        """
        try:
            if not self.news_provider or not hasattr(self.news_provider, 'storage') or not self.news_provider.storage:
                return
            
            from datetime import date, timedelta
            cutoff_date = date.today() - timedelta(days=training_days)
            
            archived_count = self.news_provider.storage.archive_old_news(cutoff_date)
            if archived_count > 0:
                logger.info(f"Заархивировано {archived_count} устаревших новостей")
                
        except Exception as e:
            logger.warning(f"Ошибка архивации устаревших новостей: {e}")
    
    async def update_market_data(self):
        """
        Обновление рыночных данных
        """
        try:
            # Обновление данных в реальном времени
            self.realtime_data = await self.provider.get_realtime_data(self.symbols)
            
            # Получение расширенных данных (если поддерживается)
            if hasattr(self.provider, 'get_enhanced_market_data'):
                try:
                    self.enhanced_data = await self.provider.get_enhanced_market_data(self.symbols)
                    logger.debug(f"Получены расширенные данные для {len(self.enhanced_data)} инструментов")
                except Exception as e:
                    logger.warning(f"Ошибка получения расширенных данных: {e}")
            
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
            
            # Обновление новостных данных (если включено)
            if self.news_provider:
                try:
                    news_config = self.config.get('news', {})
                    if news_config.get('enabled', True):
                        # Обновляем новости для анализа (короткий период)
                        days_for_analysis = news_config.get('days_back', 14)
                        updated_news = await self.news_provider.get_all_symbols_news(self.symbols, days=days_for_analysis)
                        if updated_news:
                            self.news_data = updated_news
                            logger.debug(f"Обновлены новостные данные для анализа: {len(updated_news)} символов")
                except Exception as e:
                    logger.warning(f"Ошибка обновления новостных данных: {e}")
            
            self.last_update = datetime.now()
            logger.debug(f"Данные обновлены: {len(self.realtime_data)} инструментов")
            
        except Exception as e:
            logger.error(f"Ошибка обновления данных: {e}")
    
    async def update_news_data(self):
        """
        Обновление новостных данных
        """
        try:
            if not self.news_provider:
                logger.debug("Новостной провайдер не инициализирован")
                return
            
            # Обновление новостных данных
            news_data = await self.news_provider.get_all_symbols_news(self.symbols, days=14)
            
            if news_data:
                self.news_data = news_data
                logger.debug(f"Новостные данные обновлены для {len(news_data)} символов")
            else:
                logger.warning("Не удалось обновить новостные данные")
                
        except Exception as e:
            logger.error(f"Ошибка обновления новостных данных: {e}")
    
    async def get_current_price(self, symbol: str) -> float:
        """
        Получение текущей цены инструмента
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            Текущая цена или 0.0 если недоступна
        """
        try:
            # Попытка использовать прямой метод get_current_price() провайдера
            if hasattr(self.provider, 'get_current_price'):
                try:
                    price = await self.provider.get_current_price(symbol)
                    if price > 0:
                        logger.debug(f"Получена цена {symbol} через provider.get_current_price(): {price:.2f}")
                        return float(price)
                except Exception as e:
                    logger.debug(f"Ошибка при вызове provider.get_current_price() для {symbol}: {e}")
            
            # Если прямой метод недоступен, используем get_realtime_data()
            if hasattr(self.provider, 'get_realtime_data'):
                try:
                    realtime_data = await self.provider.get_realtime_data([symbol])
                    if symbol in realtime_data and 'price' in realtime_data[symbol]:
                        price = realtime_data[symbol]['price']
                        if price > 0:
                            logger.debug(f"Получена цена {symbol} через provider.get_realtime_data(): {price:.2f}")
                            return float(price)
                except Exception as e:
                    logger.debug(f"Ошибка при вызове provider.get_realtime_data() для {symbol}: {e}")
            
            # Если ничего не помогло, возвращаем 0.0
            logger.debug(f"Не удалось получить цену для {symbol} через провайдер")
            return 0.0
            
        except Exception as e:
            logger.error(f"Ошибка получения текущей цены для {symbol}: {e}")
            return 0.0
    
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
                'news': self.news_data.get(symbol, {}),
                'news_training': self.news_training_data.get(symbol, {}),
                'symbol': symbol
            }
        else:
            return {
                'historical': self.market_data,
                'realtime': self.realtime_data,
                'news': self.news_data,
                'news_training': self.news_training_data,
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
            'realtime_data_count': len(self.realtime_data),
            'enhanced_data_count': len(self.enhanced_data),
            'supports_orderbook': hasattr(self.provider, 'get_orderbook'),
            'supports_enhanced_data': hasattr(self.provider, 'get_enhanced_market_data')
        }
    
    async def get_orderbook_data(self, symbol: str) -> Dict:
        """
        Получение данных стакана заявок
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            Словарь с данными стакана заявок
        """
        if hasattr(self.provider, 'get_orderbook'):
            return await self.provider.get_orderbook(symbol)
        else:
            logger.warning(f"Провайдер {type(self.provider).__name__} не поддерживает стакан заявок")
            return {}
    
    async def get_enhanced_features(self, symbol: str) -> pd.DataFrame:
        """
        Получение расширенных признаков для нейросети
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            DataFrame с расширенными признаками
        """
        try:
            from ..neural_networks.enhanced_features import EnhancedFeatureExtractor
            
            # Получение базовых данных
            market_data = self.market_data.get(symbol, pd.DataFrame())
            if market_data.empty:
                logger.warning(f"Нет рыночных данных для {symbol}")
                return pd.DataFrame()
            
            # Получение расширенных данных
            enhanced_data = self.enhanced_data.get(symbol, {})
            orderbook_data = enhanced_data.get('orderbook', {})
            instrument_info = enhanced_data.get('instrument', {})
            
            # Извлечение признаков
            extractor = EnhancedFeatureExtractor()
            features = extractor.extract_all_features(
                market_data, 
                orderbook_data, 
                instrument_info
            )
            
            logger.debug(f"Извлечено {len(features.columns)} признаков для {symbol}")
            return features
            
        except Exception as e:
            logger.error(f"Ошибка извлечения расширенных признаков для {symbol}: {e}")
            return pd.DataFrame()
    
    def get_provider_info(self) -> Dict:
        """
        Получение информации о провайдере данных
        
        Returns:
            Словарь с информацией о провайдере
        """
        return {
            'provider_type': type(self.provider).__name__,
            'symbols_count': len(self.symbols),
            'market_data_count': len(self.market_data),
            'realtime_data_count': len(self.realtime_data),
            'enhanced_data_count': len(self.enhanced_data),
            'supports_orderbook': hasattr(self.provider, 'get_orderbook'),
            'supports_enhanced_data': hasattr(self.provider, 'get_enhanced_market_data'),
            'last_update': self.last_update.isoformat() if self.last_update else None
        }

