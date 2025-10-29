"""
XGBoost модель для классификации торговых сигналов
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score
from typing import Dict, List, Tuple, Any
from loguru import logger
from datetime import datetime

from .base_network import BaseNeuralNetwork


class XGBoostNetwork(BaseNeuralNetwork):
    """
    XGBoost модель для классификации торговых сигналов
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Инициализация XGBoost модели
        
        Args:
            name: Название модели
            config: Конфигурация модели
        """
        super().__init__(name, config)
        
        # Параметры модели
        self.n_estimators = config.get('n_estimators', 100)
        self.max_depth = config.get('max_depth', 6)
        self.learning_rate = config.get('learning_rate', 0.1)
        self.subsample = config.get('subsample', 0.8)
        self.colsample_bytree = config.get('colsample_bytree', 0.8)
        self.random_state = config.get('random_state', 42)
        
        # Пороги для классификации
        self.buy_threshold = config.get('buy_threshold', 0.05)
        self.sell_threshold = config.get('sell_threshold', -0.05)
        
        # Модель
        self.model = None
        self.feature_columns = []
        self.feature_importance = {}
        
        logger.info(f"Инициализирована XGBoost модель {self.name}")
    
    async def initialize(self):
        """
        Инициализация XGBoost модели
        """
        try:
            # Создание модели
            self.model = xgb.XGBClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                subsample=self.subsample,
                colsample_bytree=self.colsample_bytree,
                random_state=self.random_state,
                eval_metric='mlogloss'  # Изменено на mlogloss для многоклассовой классификации
            )
            
            logger.info(f"XGBoost модель {self.name} инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации XGBoost модели {self.name}: {e}")
            raise
    
    def _create_target_labels(self, data: pd.DataFrame, target: str = 'Close') -> pd.Series:
        """
        Создание меток для классификации
        
        Args:
            data: Данные
            target: Целевая переменная
            
        Returns:
            Серия с метками классов
        """
        # Расчет будущих изменений цены
        future_returns = data[target].shift(-1) / data[target] - 1
        
        # Создание меток: 0 - продажа, 1 - удержание, 2 - покупка
        labels = pd.Series(index=data.index, dtype=int)
        
        labels[future_returns >= self.buy_threshold] = 2  # Покупка
        labels[future_returns <= self.sell_threshold] = 0  # Продажа
        labels[(future_returns > self.sell_threshold) & (future_returns < self.buy_threshold)] = 1  # Удержание
        
        return labels
    
    async def train(self, data: pd.DataFrame, target: str = 'Close', news_data: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Обучение XGBoost модели
        
        Args:
            data: Данные для обучения
            target: Целевая переменная
            news_data: Новостные данные для обучения
            
        Returns:
            Метрики обучения
        """
        try:
            logger.info(f"Начало обучения XGBoost модели {self.name}")
            
            # Подготовка данных с новостными признаками
            features = self.prepare_features(data, news_data=news_data)
            
            # Определение признаков
            self.feature_columns = [col for col in features.columns if col != target]
            
            # Создание целевых меток
            labels = self._create_target_labels(features, target)
            
            # Удаление NaN значений
            valid_indices = ~(labels.isna() | features[self.feature_columns].isna().any(axis=1))
            X = features[self.feature_columns][valid_indices]
            y = labels[valid_indices]
            
            if len(X) == 0:
                raise ValueError("Недостаточно данных для обучения")
            
            # Проверка на достаточность данных
            if len(X) < 10:
                raise ValueError(f"Недостаточно данных для обучения: {len(X)} образцов")
            
            # Проверка размеров данных
            logger.debug(f"Размеры данных: X={X.shape}, y={y.shape}")
            logger.debug(f"Уникальные значения y: {y.unique()}")
            logger.debug(f"Распределение классов: {y.value_counts().to_dict()}")
            
            # Разделение на обучающую и тестовую выборки
            # Проверяем, можно ли использовать stratify
            if len(y.unique()) > 1 and all(y.value_counts() >= 2):
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=self.random_state, stratify=y
                )
            else:
                # Если недостаточно данных для stratify, используем обычное разделение
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=self.random_state
                )
            
            # Проверка размеров после разделения
            logger.debug(f"Размеры после разделения: X_train={X_train.shape}, y_train={y_train.shape}, X_test={X_test.shape}, y_test={y_test.shape}")
            
            # Убеждаемся, что все данные числовые
            X_train = X_train.astype(float)
            X_test = X_test.astype(float)
            y_train = y_train.astype(int)
            y_test = y_test.astype(int)
            
            # Обучение модели
            self.model.fit(X_train, y_train)
            
            # Предсказания на тестовой выборке
            y_pred = self.model.predict(X_test)
            
            # Расчет метрик
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted')
            recall = recall_score(y_test, y_pred, average='weighted')
            
            # Сохранение метрик
            self.performance_metrics = {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'n_estimators_used': self.model.best_iteration if hasattr(self.model, 'best_iteration') else self.n_estimators,
                'news_features_used': bool(news_data)
            }
            
            # Сохранение важности признаков
            self.feature_importance = dict(zip(self.feature_columns, self.model.feature_importances_))
            
            self.is_trained = True
            
            logger.info(f"XGBoost модель {self.name} обучена. Точность: {accuracy:.4f}")
            
            return self.performance_metrics
            
        except Exception as e:
            logger.error(f"Ошибка обучения XGBoost модели {self.name}: {e}")
            raise
    
    async def predict(self, data: pd.DataFrame, portfolio_manager=None, symbol: str = None, news_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Предсказание с помощью XGBoost модели
        
        Args:
            data: Входные данные
            portfolio_manager: Менеджер портфеля для извлечения портфельных признаков
            symbol: Символ для анализа портфельных признаков
            news_data: Новостные данные для анализа
            
        Returns:
            Словарь с предсказаниями
        """
        try:
            if not self.is_trained or self.model is None:
                raise ValueError(f"Модель {self.name} не обучена")
            
            # Подготовка данных с портфельными и новостными признаками
            features = self.prepare_features(data, portfolio_manager, symbol, news_data)
            
            # Использование сохраненных признаков
            if self.feature_columns:
                features = features[self.feature_columns]
            else:
                features = features.select_dtypes(include=[np.number])
            
            # Получение последней записи
            last_features = features.tail(1)
            
            # Предсказание класса
            class_prediction = self.model.predict(last_features)[0]
            
            # Предсказание вероятностей
            probabilities = self.model.predict_proba(last_features)[0]
            
            # Интерпретация результатов
            class_names = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
            signal = class_names.get(class_prediction, 'HOLD')
            
            # Расчет уверенности
            confidence = float(max(probabilities))
            
            # Дополнительная информация
            signal_strength = self._calculate_signal_strength(probabilities, class_prediction)
            
            # Добавление новостной информации в результат
            news_info = {}
            if news_data and symbol and symbol in news_data:
                symbol_news = news_data[symbol]
                news_info = {
                    'news_sentiment': symbol_news.get('avg_sentiment', 0.0),
                    'news_trend': symbol_news.get('recent_trend', 'neutral'),
                    'news_count': symbol_news.get('total_news', 0),
                    'news_summary': symbol_news.get('news_summary', '')
                }
            
            # Генерация reasoning на основе анализа
            reasoning = self._generate_reasoning(signal, confidence, probabilities, news_info, symbol)
            
            # Сохранение результатов
            self.last_prediction = {
                'signal': signal,
                'signal_strength': signal_strength,
                'confidence': confidence,
                'probabilities': {
                    'SELL': float(probabilities[0]),
                    'HOLD': float(probabilities[1]),
                    'BUY': float(probabilities[2])
                },
                'class_prediction': int(class_prediction),
                'news_info': news_info,
                'reasoning': reasoning
            }
            self.last_prediction_time = datetime.now()
            
            logger.debug(f"XGBoost модель {self.name} предсказала: {signal} (уверенность: {confidence:.4f})")
            
            return self.last_prediction
            
        except Exception as e:
            logger.error(f"Ошибка предсказания XGBoost модели {self.name}: {e}")
            return {
                'signal': 'HOLD',
                'signal_strength': 0.0,
                'confidence': 0.0,
                'probabilities': {'SELL': 0.33, 'HOLD': 0.34, 'BUY': 0.33},
                'class_prediction': 1,
                'news_info': {},
                'error': str(e)
            }
    
    def _calculate_signal_strength(self, probabilities: np.ndarray, class_prediction: int) -> float:
        """
        Расчет силы сигнала
        
        Args:
            probabilities: Вероятности классов
            class_prediction: Предсказанный класс
            
        Returns:
            Сила сигнала от -1 до 1
        """
        try:
            if class_prediction == 0:  # SELL
                return -probabilities[0]  # Отрицательная сила для продажи
            elif class_prediction == 2:  # BUY
                return probabilities[2]  # Положительная сила для покупки
            else:  # HOLD
                return 0.0  # Нейтральная сила для удержания
                
        except Exception:
            return 0.0
    
    def _generate_reasoning(self, signal: str, confidence: float, probabilities: np.ndarray, 
                           news_info: Dict[str, Any], symbol: str) -> str:
        """
        Генерация краткой сводки причины решения
        
        Args:
            signal: Торговый сигнал
            confidence: Уверенность в сигнале
            probabilities: Вероятности классов
            news_info: Новостная информация
            symbol: Тикер инструмента
            
        Returns:
            Краткая сводка причины решения
        """
        try:
            reasoning_parts = []
            
            # Основная причина на основе сигнала
            if signal == 'BUY':
                reasoning_parts.append(f"Рекомендация покупки {symbol}")
            elif signal == 'SELL':
                reasoning_parts.append(f"Рекомендация продажи {symbol}")
            else:
                reasoning_parts.append(f"Рекомендация удержания позиции по {symbol}")
            
            # Уверенность
            if confidence > 0.8:
                reasoning_parts.append("высокая уверенность")
            elif confidence > 0.6:
                reasoning_parts.append("средняя уверенность")
            else:
                reasoning_parts.append("низкая уверенность")
            
            # Анализ вероятностей
            buy_prob = probabilities[2]
            sell_prob = probabilities[0]
            hold_prob = probabilities[1]
            
            if buy_prob > 0.5:
                reasoning_parts.append(f"вероятность роста {buy_prob:.1%}")
            elif sell_prob > 0.5:
                reasoning_parts.append(f"вероятность падения {sell_prob:.1%}")
            else:
                reasoning_parts.append(f"неопределенность (удержание {hold_prob:.1%})")
            
            # Новостной фон
            if news_info and news_info.get('news_count', 0) > 0:
                news_sentiment = news_info.get('news_sentiment', 0)
                if news_sentiment > 0.1:
                    reasoning_parts.append("позитивные новости")
                elif news_sentiment < -0.1:
                    reasoning_parts.append("негативные новости")
                else:
                    reasoning_parts.append("нейтральные новости")
            
            return ". ".join(reasoning_parts) + "."
            
        except Exception as e:
            logger.error(f"Ошибка генерации reasoning: {e}")
            return f"Сигнал {signal} для {symbol} с уверенностью {confidence:.2f}"
    
    async def get_feature_importance(self) -> Dict[str, float]:
        """
        Получение важности признаков
        
        Returns:
            Словарь с важностью признаков
        """
        return self.feature_importance.copy()
    
    def save_model(self, path: str):
        """
        Сохранение XGBoost модели
        
        Args:
            path: Путь для сохранения
        """
        try:
            if self.model is not None:
                self.model.save_model(f"{path}/{self.name}_xgboost.json")
                logger.info(f"XGBoost модель {self.name} сохранена в {path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения XGBoost модели {self.name}: {e}")
    
    def load_model(self, path: str):
        """
        Загрузка XGBoost модели
        
        Args:
            path: Путь к модели
        """
        try:
            self.model = xgb.XGBClassifier()
            self.model.load_model(f"{path}/{self.name}_xgboost.json")
            self.is_trained = True
            logger.info(f"XGBoost модель {self.name} загружена из {path}")
        except Exception as e:
            logger.error(f"Ошибка загрузки XGBoost модели {self.name}: {e}")
