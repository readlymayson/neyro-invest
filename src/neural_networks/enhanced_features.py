"""
Расширенные признаки для нейросети с использованием стакана заявок
и других рыночных данных от T-Bank API
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger
from datetime import datetime


class EnhancedFeatureExtractor:
    """
    Извлекатель расширенных признаков для нейросети
    
    Включает:
    - Стандартные технические индикаторы
    - Признаки стакана заявок
    - Объемные индикаторы
    - Временные признаки
    - Микроструктурные признаки
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализация извлекателя признаков
        
        Args:
            config: Конфигурация извлечения признаков
        """
        self.config = config or {}
        self.orderbook_depth = self.config.get('orderbook_depth', 10)
        self.volume_periods = self.config.get('volume_periods', [5, 10, 20])
        self.price_periods = self.config.get('price_periods', [5, 10, 20, 50])
        
        logger.info("Инициализирован извлекатель расширенных признаков")
    
    def extract_all_features(
        self, 
        market_data: pd.DataFrame, 
        orderbook_data: Dict = None,
        instrument_info: Dict = None
    ) -> pd.DataFrame:
        """
        Извлечение всех признаков для нейросети
        
        Args:
            market_data: OHLCV данные
            orderbook_data: Данные стакана заявок
            instrument_info: Информация об инструменте
            
        Returns:
            DataFrame с признаками
        """
        try:
            features = market_data.copy()
            
            # 1. Стандартные технические индикаторы
            features = self._add_technical_indicators(features)
            
            # 2. Объемные индикаторы
            features = self._add_volume_indicators(features)
            
            # 3. Временные признаки
            features = self._add_time_features(features)
            
            # 4. Признаки стакана заявок (если доступны)
            if orderbook_data:
                features = self._add_orderbook_features(features, orderbook_data)
            
            # 5. Инструментальные признаки
            if instrument_info:
                features = self._add_instrument_features(features, instrument_info)
            
            # 6. Нормализация признаков
            features = self._normalize_features(features)
            
            logger.debug(f"Извлечено {len(features.columns)} признаков")
            return features
            
        except Exception as e:
            logger.error(f"Ошибка извлечения признаков: {e}")
            return market_data
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Добавление технических индикаторов"""
        df = data.copy()
        
        # Скользящие средние
        for window in self.price_periods:
            df[f'SMA_{window}'] = df['Close'].rolling(window=window).mean()
            df[f'EMA_{window}'] = df['Close'].ewm(span=window).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['Close'].ewm(span=12).mean()
        ema_26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema_12 - ema_26
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        # Stochastic Oscillator
        low_14 = df['Low'].rolling(window=14).min()
        high_14 = df['High'].rolling(window=14).max()
        df['Stoch_K'] = 100 * (df['Close'] - low_14) / (high_14 - low_14)
        df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
        
        # Williams %R
        df['Williams_R'] = -100 * (high_14 - df['Close']) / (high_14 - low_14)
        
        # Commodity Channel Index (CCI)
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        sma_tp = typical_price.rolling(window=20).mean()
        mad = typical_price.rolling(window=20).apply(lambda x: np.mean(np.abs(x - x.mean())))
        df['CCI'] = (typical_price - sma_tp) / (0.015 * mad)
        
        # Average True Range (ATR)
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        df['ATR'] = true_range.rolling(window=14).mean()
        
        # Волатильность
        df['Volatility'] = df['Close'].rolling(window=20).std()
        df['Volatility_ratio'] = df['Volatility'] / df['Close']
        
        # Ценовые изменения
        for period in [1, 5, 10, 20]:
            df[f'Price_Change_{period}'] = df['Close'].pct_change(period)
            df[f'Price_Change_{period}_abs'] = df['Close'].diff(period)
        
        return df
    
    def _add_volume_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Добавление объемных индикаторов"""
        df = data.copy()
        
        # Объемные скользящие средние
        for window in self.volume_periods:
            df[f'Volume_SMA_{window}'] = df['Volume'].rolling(window=window).mean()
            df[f'Volume_EMA_{window}'] = df['Volume'].ewm(span=window).mean()
        
        # Отношения объемов
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']
        df['Volume_Change'] = df['Volume'].pct_change()
        df['Volume_Change_5'] = df['Volume'].pct_change(5)
        
        # On-Balance Volume (OBV)
        df['OBV'] = (df['Volume'] * np.sign(df['Close'].diff())).cumsum()
        
        # Volume Price Trend (VPT)
        df['VPT'] = (df['Volume'] * (df['Close'] / df['Close'].shift() - 1)).cumsum()
        
        # Accumulation/Distribution Line
        clv = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'])
        clv = clv.fillna(0)  # Заполняем NaN нулями
        df['ADL'] = (clv * df['Volume']).cumsum()
        
        # Money Flow Index (MFI)
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        money_flow = typical_price * df['Volume']
        positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(window=14).sum()
        negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(window=14).sum()
        df['MFI'] = 100 - (100 / (1 + positive_flow / negative_flow))
        
        # Ease of Movement
        distance = ((df['High'] + df['Low']) / 2) - ((df['High'].shift() + df['Low'].shift()) / 2)
        box_height = df['Volume'] / (df['High'] - df['Low'])
        df['EOM'] = distance / box_height
        df['EOM_SMA'] = df['EOM'].rolling(window=14).mean()
        
        return df
    
    def _add_time_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Добавление временных признаков"""
        df = data.copy()
        
        if hasattr(df.index, 'hour'):
            # Временные признаки
            df['Hour'] = df.index.hour
            df['DayOfWeek'] = df.index.dayofweek
            df['DayOfMonth'] = df.index.day
            df['Month'] = df.index.month
            df['Quarter'] = df.index.quarter
            df['Year'] = df.index.year
            
            # Циклические признаки
            df['Hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 24)
            df['Hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 24)
            df['DayOfWeek_sin'] = np.sin(2 * np.pi * df['DayOfWeek'] / 7)
            df['DayOfWeek_cos'] = np.cos(2 * np.pi * df['DayOfWeek'] / 7)
            df['Month_sin'] = np.sin(2 * np.pi * df['Month'] / 12)
            df['Month_cos'] = np.cos(2 * np.pi * df['Month'] / 12)
            
            # Торговые сессии
            df['Is_Market_Open'] = ((df['Hour'] >= 10) & (df['Hour'] < 18)).astype(int)
            df['Is_Morning'] = ((df['Hour'] >= 10) & (df['Hour'] < 12)).astype(int)
            df['Is_Afternoon'] = ((df['Hour'] >= 12) & (df['Hour'] < 15)).astype(int)
            df['Is_Evening'] = ((df['Hour'] >= 15) & (df['Hour'] < 18)).astype(int)
        
        return df
    
    def _add_orderbook_features(self, data: pd.DataFrame, orderbook_data: Dict) -> pd.DataFrame:
        """Добавление признаков стакана заявок"""
        df = data.copy()
        
        try:
            # Базовые метрики стакана
            if 'spread' in orderbook_data:
                df['Spread'] = orderbook_data['spread']
                df['Spread_Percent'] = orderbook_data.get('spread_percent', 0)
            
            if 'mid_price' in orderbook_data:
                df['Mid_Price'] = orderbook_data['mid_price']
                df['Price_vs_Mid'] = (df['Close'] - orderbook_data['mid_price']) / orderbook_data['mid_price']
            
            # Объемы в стакане
            if 'total_bid_volume' in orderbook_data:
                df['Total_Bid_Volume'] = orderbook_data['total_bid_volume']
                df['Total_Ask_Volume'] = orderbook_data.get('total_ask_volume', 0)
                df['Volume_Imbalance'] = orderbook_data.get('volume_imbalance', 0)
                df['Bid_Ask_Ratio'] = df['Total_Bid_Volume'] / (df['Total_Ask_Volume'] + 1e-8)
            
            # Глубина стакана
            if 'bids' in orderbook_data and 'asks' in orderbook_data:
                bids = orderbook_data['bids']
                asks = orderbook_data['asks']
                
                if bids and asks:
                    # Количество уровней
                    df['Bid_Levels'] = len(bids)
                    df['Ask_Levels'] = len(asks)
                    
                    # Средние цены в стакане
                    if bids:
                        bid_prices = [bid['price'] for bid in bids]
                        df['Avg_Bid_Price'] = np.mean(bid_prices)
                        df['Bid_Price_Std'] = np.std(bid_prices)
                    
                    if asks:
                        ask_prices = [ask['price'] for ask in asks]
                        df['Avg_Ask_Price'] = np.mean(ask_prices)
                        df['Ask_Price_Std'] = np.std(ask_prices)
                    
                    # Концентрация объема
                    if bids:
                        bid_volumes = [bid['quantity'] for bid in bids]
                        total_bid_vol = sum(bid_volumes)
                        if total_bid_vol > 0:
                            df['Bid_Volume_Concentration'] = max(bid_volumes) / total_bid_vol
                    
                    if asks:
                        ask_volumes = [ask['quantity'] for ask in asks]
                        total_ask_vol = sum(ask_volumes)
                        if total_ask_vol > 0:
                            df['Ask_Volume_Concentration'] = max(ask_volumes) / total_ask_vol
                    
                    # Глубина по ценам
                    if len(bids) > 1 and len(asks) > 1:
                        bid_range = bid_prices[0] - bid_prices[-1]
                        ask_range = ask_prices[-1] - ask_prices[0]
                        df['Bid_Price_Range'] = bid_range
                        df['Ask_Price_Range'] = ask_range
                        df['Total_Price_Range'] = bid_range + ask_range
            
            logger.debug("Добавлены признаки стакана заявок")
            
        except Exception as e:
            logger.warning(f"Ошибка добавления признаков стакана: {e}")
        
        return df
    
    def _add_instrument_features(self, data: pd.DataFrame, instrument_info: Dict) -> pd.DataFrame:
        """Добавление инструментальных признаков"""
        df = data.copy()
        
        try:
            # Тип инструмента
            instrument_type = instrument_info.get('type', 'unknown')
            type_mapping = {'share': 1, 'bond': 2, 'etf': 3, 'unknown': 0}
            df['Instrument_Type'] = type_mapping.get(instrument_type, 0)
            
            # Валюта
            currency = instrument_info.get('currency', 'RUB')
            currency_mapping = {'RUB': 1, 'USD': 2, 'EUR': 3, 'CNY': 4}
            df['Currency'] = currency_mapping.get(currency, 1)
            
            # Статус торгов
            trading_status = instrument_info.get('trading_status', 'UNKNOWN')
            status_mapping = {
                'SECURITY_TRADING_STATUS_NORMAL_TRADING': 1,
                'SECURITY_TRADING_STATUS_NOT_AVAILABLE_FOR_TRADING': 0,
                'SECURITY_TRADING_STATUS_CLOSING_AUCTION': 2,
                'SECURITY_TRADING_STATUS_OPENING_AUCTION': 3
            }
            df['Trading_Status'] = status_mapping.get(trading_status, 0)
            
            logger.debug("Добавлены инструментальные признаки")
            
        except Exception as e:
            logger.warning(f"Ошибка добавления инструментальных признаков: {e}")
        
        return df
    
    def _normalize_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Нормализация признаков"""
        df = data.copy()
        
        # Список колонок для нормализации
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        # Исключаем колонки, которые уже нормализованы или являются категориальными
        exclude_columns = [
            'Hour', 'DayOfWeek', 'DayOfMonth', 'Month', 'Quarter', 'Year',
            'Is_Market_Open', 'Is_Morning', 'Is_Afternoon', 'Is_Evening',
            'Instrument_Type', 'Currency', 'Trading_Status',
            'Hour_sin', 'Hour_cos', 'DayOfWeek_sin', 'DayOfWeek_cos',
            'Month_sin', 'Month_cos'
        ]
        
        normalize_columns = [col for col in numeric_columns if col not in exclude_columns]
        
        # Z-score нормализация
        for col in normalize_columns:
            if col in df.columns:
                # Используем скользящее окно для нормализации
                window = min(50, len(df))
                if window > 1:
                    rolling_mean = df[col].rolling(window=window, min_periods=1).mean()
                    rolling_std = df[col].rolling(window=window, min_periods=1).std()
                    df[f'{col}_norm'] = (df[col] - rolling_mean) / (rolling_std + 1e-8)
        
        return df
    
    def get_feature_importance_categories(self) -> Dict[str, List[str]]:
        """Получение категорий признаков для анализа важности"""
        return {
            'price_indicators': [
                'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50',
                'EMA_5', 'EMA_10', 'EMA_20', 'EMA_50',
                'RSI', 'MACD', 'MACD_Signal', 'MACD_Histogram'
            ],
            'volatility_indicators': [
                'BB_Upper', 'BB_Lower', 'BB_Width', 'BB_Position',
                'ATR', 'Volatility', 'Volatility_ratio'
            ],
            'volume_indicators': [
                'Volume_Ratio', 'Volume_Change', 'Volume_Change_5',
                'OBV', 'VPT', 'ADL', 'MFI', 'EOM', 'EOM_SMA'
            ],
            'orderbook_indicators': [
                'Spread', 'Spread_Percent', 'Mid_Price', 'Price_vs_Mid',
                'Total_Bid_Volume', 'Total_Ask_Volume', 'Volume_Imbalance',
                'Bid_Ask_Ratio', 'Bid_Levels', 'Ask_Levels'
            ],
            'time_indicators': [
                'Hour', 'DayOfWeek', 'Month', 'Quarter',
                'Is_Market_Open', 'Is_Morning', 'Is_Afternoon', 'Is_Evening'
            ],
            'instrument_indicators': [
                'Instrument_Type', 'Currency', 'Trading_Status'
            ]
        }
    
    def get_feature_count(self) -> int:
        """Получение общего количества признаков"""
        categories = self.get_feature_importance_categories()
        return sum(len(features) for features in categories.values())
