"""
Базовый класс для нейросетей
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from loguru import logger
from datetime import datetime


class BaseNeuralNetwork(ABC):
    """
    Базовый класс для всех нейросетей в системе
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Инициализация нейросети
        
        Args:
            name: Название нейросети
            config: Конфигурация нейросети
        """
        self.name = name
        self.config = config
        self.is_trained = False
        self.performance_metrics: Dict[str, float] = {}
        self.last_prediction = None
        self.last_prediction_time = None
        
        logger.info(f"Инициализирована нейросеть {self.name}")
    
    @abstractmethod
    async def initialize(self):
        """
        Инициализация модели
        """
        pass
    
    @abstractmethod
    async def train(self, data: pd.DataFrame, target: str = 'Close') -> Dict[str, float]:
        """
        Обучение модели
        
        Args:
            data: Данные для обучения
            target: Целевая переменная
            
        Returns:
            Метрики обучения
        """
        pass
    
    @abstractmethod
    async def predict(self, data: pd.DataFrame, portfolio_manager=None, symbol: str = None) -> Dict[str, Any]:
        """
        Предсказание на основе данных
        
        Args:
            data: Входные данные
            portfolio_manager: Менеджер портфеля для извлечения портфельных признаков
            symbol: Символ для анализа портфельных признаков
            
        Returns:
            Словарь с предсказаниями
        """
        pass
    
    @abstractmethod
    async def get_feature_importance(self) -> Dict[str, float]:
        """
        Получение важности признаков
        
        Returns:
            Словарь с важностью признаков
        """
        pass
    
    def prepare_features(self, data: pd.DataFrame, portfolio_manager=None, symbol: str = None) -> pd.DataFrame:
        """
        Подготовка признаков для модели
        
        Args:
            data: Исходные данные
            portfolio_manager: Менеджер портфеля для извлечения портфельных признаков
            symbol: Символ для анализа портфельных признаков
            
        Returns:
            Подготовленные признаки
        """
        features = data.copy()
        
        # Добавление технических индикаторов
        features = self._add_technical_indicators(features)
        
        # Добавление временных признаков
        features = self._add_time_features(features)
        
        # Добавление портфельных признаков
        if portfolio_manager:
            features = self._add_portfolio_features(features, portfolio_manager, symbol)
        
        # Нормализация данных
        features = self._normalize_features(features)
        
        return features
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Добавление технических индикаторов
        
        Args:
            data: Исходные данные
            
        Returns:
            Данные с техническими индикаторами
        """
        df = data.copy()
        
        # Скользящие средние
        for window in [5, 10, 20, 50]:
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
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        
        # Волатильность
        df['Volatility'] = df['Close'].rolling(window=20).std()
        
        # Объемные индикаторы
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # Ценовые изменения
        df['Price_Change'] = df['Close'].pct_change()
        df['Price_Change_5'] = df['Close'].pct_change(5)
        df['Price_Change_10'] = df['Close'].pct_change(10)
        
        return df
    
    def _add_time_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Добавление временных признаков
        
        Args:
            data: Исходные данные
            
        Returns:
            Данные с временными признаками
        """
        df = data.copy()
        
        if hasattr(df.index, 'hour'):
            df['Hour'] = df.index.hour
            df['DayOfWeek'] = df.index.dayofweek
            df['Month'] = df.index.month
            df['Quarter'] = df.index.quarter
        
        return df
    
    def _normalize_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Нормализация признаков
        
        Args:
            data: Исходные данные
            
        Returns:
            Нормализованные данные
        """
        df = data.copy()
        
        # Нормализация ценовых данных
        price_columns = ['Open', 'High', 'Low', 'Close']
        for col in price_columns:
            if col in df.columns:
                df[f'{col}_norm'] = (df[col] - df[col].rolling(50).mean()) / df[col].rolling(50).std()
        
        return df
    
    def _add_portfolio_features(self, data: pd.DataFrame, portfolio_manager, symbol: str = None) -> pd.DataFrame:
        """Добавление портфельных признаков"""
        df = data.copy()
        
        try:
            from .portfolio_features import PortfolioFeatureExtractor
            
            # Создание извлекателя портфельных признаков
            portfolio_extractor = PortfolioFeatureExtractor(self.config.get('portfolio_features', {}))
            
            # Извлечение портфельных признаков
            portfolio_features = portfolio_extractor.extract_portfolio_features(portfolio_manager, symbol)
            
            # Конвертация в DataFrame
            portfolio_df = portfolio_extractor.features_to_dataframe(portfolio_features)
            
            # Добавление портфельных признаков к основным данным
            if not portfolio_df.empty:
                for col in portfolio_df.columns:
                    df[col] = portfolio_df[col].iloc[0] if len(portfolio_df) > 0 else 0.0
            
            logger.debug("Добавлены портфельные признаки в базовую модель")
            
        except Exception as e:
            logger.warning(f"Ошибка добавления портфельных признаков в базовую модель: {e}")
        
        return df
    
    def create_sequences(self, data: pd.DataFrame, sequence_length: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """
        Создание последовательностей для обучения
        
        Args:
            data: Данные
            sequence_length: Длина последовательности
            
        Returns:
            Кортеж (X, y) - входные данные и целевые значения
        """
        # Выбор признаков
        feature_columns = [col for col in data.columns if col not in ['Open', 'High', 'Low', 'Close', 'Volume']]
        
        if not feature_columns:
            feature_columns = ['Close']
        
        # Подготовка данных
        values = data[feature_columns].values
        
        X, y = [], []
        for i in range(sequence_length, len(values)):
            X.append(values[i-sequence_length:i])
            y.append(values[i, 0])  # Предсказываем Close цену
        
        return np.array(X), np.array(y)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса нейросети
        
        Returns:
            Словарь со статусом
        """
        return {
            'name': self.name,
            'is_trained': self.is_trained,
            'performance_metrics': self.performance_metrics,
            'last_prediction_time': self.last_prediction_time.isoformat() if self.last_prediction_time else None,
            'config': self.config
        }
    
    def save_model(self, path: str):
        """
        Сохранение модели
        
        Args:
            path: Путь для сохранения
        """
        # Реализация зависит от конкретной модели
        logger.info(f"Сохранение модели {self.name} в {path}")
    
    def load_model(self, path: str):
        """
        Загрузка модели
        
        Args:
            path: Путь к модели
        """
        # Реализация зависит от конкретной модели
        logger.info(f"Загрузка модели {self.name} из {path}")

