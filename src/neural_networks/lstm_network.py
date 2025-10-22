"""
LSTM нейросеть для предсказания цен
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from typing import Dict, List, Tuple, Any
from loguru import logger
from datetime import datetime

from .base_network import BaseNeuralNetwork


class LSTMNetwork(BaseNeuralNetwork):
    """
    LSTM нейросеть для предсказания цен акций
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Инициализация LSTM сети
        
        Args:
            name: Название сети
            config: Конфигурация сети
        """
        super().__init__(name, config)
        
        # Параметры модели
        self.sequence_length = config.get('sequence_length', 60)
        self.lstm_units = config.get('lstm_units', [50, 50])
        self.dropout_rate = config.get('dropout_rate', 0.2)
        self.learning_rate = config.get('learning_rate', 0.001)
        self.batch_size = config.get('batch_size', 32)
        self.epochs = config.get('epochs', 100)
        
        # Модель
        self.model = None
        self.scaler = None
        self.feature_columns = []
        
        logger.info(f"Инициализирована LSTM сеть {self.name}")
    
    async def initialize(self):
        """
        Инициализация LSTM модели
        """
        try:
            # Создание модели
            self.model = self._build_model()
            
            # Компиляция модели
            self.model.compile(
                optimizer=Adam(learning_rate=self.learning_rate),
                loss='mse',
                metrics=['mae', 'mape']
            )
            
            logger.info(f"LSTM модель {self.name} инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации LSTM модели {self.name}: {e}")
            raise
    
    def _build_model(self) -> Sequential:
        """
        Построение архитектуры LSTM модели
        
        Returns:
            Скомпилированная модель
        """
        model = Sequential()
        
        # Первый LSTM слой
        model.add(LSTM(
            units=self.lstm_units[0],
            return_sequences=True,
            input_shape=(self.sequence_length, len(self.feature_columns))
        ))
        model.add(Dropout(self.dropout_rate))
        
        # Дополнительные LSTM слои
        for units in self.lstm_units[1:]:
            model.add(LSTM(units=units, return_sequences=True))
            model.add(Dropout(self.dropout_rate))
        
        # Последний LSTM слой
        model.add(LSTM(units=self.lstm_units[-1], return_sequences=False))
        model.add(Dropout(self.dropout_rate))
        
        # Полносвязные слои
        model.add(Dense(units=25, activation='relu'))
        model.add(Dropout(self.dropout_rate))
        model.add(Dense(units=1, activation='linear'))
        
        return model
    
    async def train(self, data: pd.DataFrame, target: str = 'Close') -> Dict[str, float]:
        """
        Обучение LSTM модели
        
        Args:
            data: Данные для обучения
            target: Целевая переменная
            
        Returns:
            Метрики обучения
        """
        try:
            logger.info(f"Начало обучения LSTM модели {self.name}")
            
            # Подготовка данных
            features = self.prepare_features(data)
            
            # Определение признаков
            self.feature_columns = [col for col in features.columns if col != target]
            
            # Создание последовательностей
            X, y = self.create_sequences(features, self.sequence_length)
            
            if len(X) == 0:
                raise ValueError("Недостаточно данных для создания последовательностей")
            
            # Разделение на обучающую и валидационную выборки
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Callbacks
            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-7
                )
            ]
            
            # Обучение модели
            history = self.model.fit(
                X_train, y_train,
                batch_size=self.batch_size,
                epochs=self.epochs,
                validation_data=(X_val, y_val),
                callbacks=callbacks,
                verbose=0
            )
            
            # Сохранение метрик
            self.performance_metrics = {
                'train_loss': float(history.history['loss'][-1]),
                'val_loss': float(history.history['val_loss'][-1]),
                'train_mae': float(history.history['mae'][-1]),
                'val_mae': float(history.history['val_mae'][-1]),
                'epochs_trained': len(history.history['loss'])
            }
            
            self.is_trained = True
            
            logger.info(f"LSTM модель {self.name} обучена. Валидационная потеря: {self.performance_metrics['val_loss']:.4f}")
            
            return self.performance_metrics
            
        except Exception as e:
            logger.error(f"Ошибка обучения LSTM модели {self.name}: {e}")
            raise
    
    async def predict(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Предсказание с помощью LSTM модели
        
        Args:
            data: Входные данные
            
        Returns:
            Словарь с предсказаниями
        """
        try:
            if not self.is_trained or self.model is None:
                raise ValueError(f"Модель {self.name} не обучена")
            
            # Подготовка данных
            features = self.prepare_features(data)
            
            # Использование сохраненных признаков
            if self.feature_columns:
                features = features[self.feature_columns]
            else:
                features = features.select_dtypes(include=[np.number])
            
            # Создание последовательности для предсказания
            if len(features) < self.sequence_length:
                raise ValueError(f"Недостаточно данных для предсказания. Нужно минимум {self.sequence_length} записей")
            
            # Последняя последовательность
            last_sequence = features.tail(self.sequence_length).values
            X_pred = last_sequence.reshape(1, self.sequence_length, -1)
            
            # Предсказание
            prediction = self.model.predict(X_pred, verbose=0)[0][0]
            
            # Дополнительные предсказания на несколько шагов вперед
            multi_step_predictions = []
            current_sequence = last_sequence.copy()
            
            for step in range(1, 6):  # Предсказания на 5 шагов вперед
                pred = self.model.predict(current_sequence.reshape(1, self.sequence_length, -1), verbose=0)[0][0]
                multi_step_predictions.append(pred)
                
                # Обновление последовательности
                current_sequence = np.roll(current_sequence, -1, axis=0)
                current_sequence[-1, 0] = pred  # Предполагаем, что первый признак - это цена
            
            # Сохранение результатов
            self.last_prediction = {
                'next_price': float(prediction),
                'multi_step_predictions': [float(p) for p in multi_step_predictions],
                'confidence': self._calculate_confidence(prediction, multi_step_predictions)
            }
            self.last_prediction_time = datetime.now()
            
            logger.debug(f"LSTM модель {self.name} выполнила предсказание: {prediction:.4f}")
            
            return self.last_prediction
            
        except Exception as e:
            logger.error(f"Ошибка предсказания LSTM модели {self.name}: {e}")
            return {
                'next_price': 0.0,
                'multi_step_predictions': [0.0] * 5,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _calculate_confidence(self, prediction: float, multi_step_predictions: List[float]) -> float:
        """
        Расчет уверенности в предсказании
        
        Args:
            prediction: Основное предсказание
            multi_step_predictions: Предсказания на несколько шагов
            
        Returns:
            Уверенность от 0 до 1
        """
        try:
            # Простая метрика уверенности на основе стабильности предсказаний
            if len(multi_step_predictions) < 2:
                return 0.5
            
            # Расчет стандартного отклонения предсказаний
            std_dev = np.std(multi_step_predictions)
            
            # Нормализация к диапазону [0, 1]
            confidence = max(0, 1 - std_dev / abs(prediction) if prediction != 0 else 0.5)
            
            return min(1.0, confidence)
            
        except Exception:
            return 0.5
    
    async def get_feature_importance(self) -> Dict[str, float]:
        """
        Получение важности признаков для LSTM
        
        Returns:
            Словарь с важностью признаков
        """
        # LSTM не предоставляет прямую важность признаков
        # Возвращаем равномерное распределение
        if not self.feature_columns:
            return {}
        
        importance = 1.0 / len(self.feature_columns)
        return {feature: importance for feature in self.feature_columns}
    
    def save_model(self, path: str):
        """
        Сохранение LSTM модели
        
        Args:
            path: Путь для сохранения
        """
        try:
            if self.model is not None:
                self.model.save(f"{path}/{self.name}_lstm.h5")
                logger.info(f"LSTM модель {self.name} сохранена в {path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения LSTM модели {self.name}: {e}")
    
    def load_model(self, path: str):
        """
        Загрузка LSTM модели
        
        Args:
            path: Путь к модели
        """
        try:
            self.model = tf.keras.models.load_model(f"{path}/{self.name}_lstm.h5")
            self.is_trained = True
            logger.info(f"LSTM модель {self.name} загружена из {path}")
        except Exception as e:
            logger.error(f"Ошибка загрузки LSTM модели {self.name}: {e}")

