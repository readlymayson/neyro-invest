"""
Менеджер нейросетей для координации работы множества моделей
"""

import asyncio
import os
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger
from datetime import datetime
import numpy as np
import pandas as pd

from .base_network import BaseNeuralNetwork
from .xgboost_network import XGBoostNetwork
from .deepseek_network import DeepSeekNetwork


class NetworkManager:
    """
    Менеджер для координации работы множества нейросетей
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация менеджера нейросетей
        
        Args:
            config: Конфигурация нейросетей
        """
        self.config = config
        self.models: Dict[str, BaseNeuralNetwork] = {}
        self.ensemble_method = config.get('ensemble_method', 'weighted_average')
        self.last_analysis = None
        self.last_analysis_time = None
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Инициализация моделей
        self._initialize_models()
        
        logger.info(f"Менеджер нейросетей инициализирован с {len(self.models)} моделями")
    
    def _initialize_models(self):
        """
        Инициализация всех моделей из конфигурации
        """
        model_configs = self.config.get('models', [])
        
        for model_config in model_configs:
            if not model_config.get('enabled', True):
                continue
            
            model_name = model_config['name']
            model_type = model_config['type']
            
            try:
                if model_type == 'xgboost':
                    model = XGBoostNetwork(model_name, model_config)
                elif model_type == 'deepseek':
                    model = DeepSeekNetwork(model_name, model_config)
                else:
                    logger.warning(f"Неизвестный тип модели: {model_type}")
                    continue
                
                self.models[model_name] = model
                logger.info(f"Модель {model_name} ({model_type}) добавлена")
                
            except Exception as e:
                logger.error(f"Ошибка инициализации модели {model_name}: {e}")
    
    async def initialize(self):
        """
        Инициализация всех моделей
        """
        logger.info("Инициализация всех нейросетей")
        
        for model_name, model in self.models.items():
            try:
                await model.initialize()
                logger.debug(f"Модель {model_name} инициализирована")
            except Exception as e:
                logger.error(f"Ошибка инициализации модели {model_name}: {e}")
        
        # Попытка загрузки сохраненных моделей
        await self.load_models()
        
        logger.info("Все нейросети инициализированы")
    
    async def train_models(self, data: Dict[str, Any], target: str = 'Close'):
        """
        Обучение всех моделей
        
        Args:
            data: Данные для обучения
            target: Целевая переменная
        """
        logger.info("Начало обучения всех моделей")
        
        training_tasks = []
        
        for model_name, model in self.models.items():
            if model.is_trained:
                logger.debug(f"Модель {model_name} уже обучена, пропускаем")
                continue
            
            # Создание задачи обучения для каждой модели
            task = asyncio.create_task(self._train_single_model(model, data, target))
            training_tasks.append(task)
        
        if training_tasks:
            # Параллельное обучение моделей
            results = await asyncio.gather(*training_tasks, return_exceptions=True)
            
            # Обработка результатов
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Ошибка обучения модели: {result}")
                else:
                    logger.info(f"Модель обучена успешно")
        
        logger.info("Обучение всех моделей завершено")
        
        # Сохранение обученных моделей
        await self.save_models()
    
    async def _train_single_model(self, model: BaseNeuralNetwork, data: Dict[str, Any], target: str):
        """
        Обучение одной модели
        
        Args:
            model: Модель для обучения
            data: Данные для обучения
            target: Целевая переменная
        """
        try:
            # Подготовка данных для конкретной модели
            if 'historical' in data and isinstance(data['historical'], dict):
                # Объединение данных всех символов
                combined_data = []
                for symbol, symbol_data in data['historical'].items():
                    if not symbol_data.empty:
                        combined_data.append(symbol_data)
                
                if combined_data:
                    combined_df = pd.concat(combined_data, ignore_index=True)
                    await model.train(combined_df, target)
                else:
                    logger.warning(f"Нет данных для обучения модели {model.name}")
            else:
                logger.warning(f"Неправильный формат данных для модели {model.name}")
                
        except Exception as e:
            logger.error(f"Ошибка обучения модели {model.name}: {e}")
            raise
    
    async def analyze(self, data: Dict[str, Any], portfolio_manager=None) -> Dict[str, Any]:
        """
        Анализ данных всеми моделями для всех символов
        
        Args:
            data: Входные данные
            portfolio_manager: Менеджер портфеля для извлечения портфельных признаков
            
        Returns:
            Результаты анализа от всех моделей по каждому символу
        """
        try:
            logger.debug("Начало анализа данных нейросетями")
            
            # Анализ каждой моделью
            predictions_by_model = {}
            analysis_tasks = []
            
            for model_name, model in self.models.items():
                if not model.is_trained:
                    logger.warning(f"Модель {model_name} не обучена, пропускаем")
                    continue
                
                # Создание задачи анализа для каждой модели
                task = asyncio.create_task(self._analyze_single_model(model, data, portfolio_manager))
                analysis_tasks.append((model_name, task))
            
            # Параллельный анализ всеми моделями
            for model_name, task in analysis_tasks:
                try:
                    prediction = await task  # Теперь это словарь {symbol: prediction}
                    predictions_by_model[model_name] = prediction
                except Exception as e:
                    logger.error(f"Ошибка анализа модели {model_name}: {e}")
                    predictions_by_model[model_name] = {}
            
            # Получаем список всех символов
            all_symbols = set()
            for model_predictions in predictions_by_model.values():
                all_symbols.update(model_predictions.keys())
            
            # Ансамблевое предсказание для каждого символа
            ensemble_predictions = {}
            for symbol in all_symbols:
                # Собираем предсказания всех моделей для этого символа
                symbol_predictions = {}
                for model_name, model_data in predictions_by_model.items():
                    if symbol in model_data:
                        symbol_predictions[model_name] = model_data[symbol]
                
                # Создаем ансамбль для символа
                ensemble_predictions[symbol] = self._create_ensemble_prediction(symbol_predictions)
                ensemble_predictions[symbol]['symbol'] = symbol
            
            # Сохранение результатов
            self.last_analysis = {
                'individual_predictions': predictions_by_model,
                'ensemble_predictions': ensemble_predictions,  # Теперь по символам
                'symbols_analyzed': list(all_symbols),
                'models_used': list(predictions_by_model.keys()),
                'analysis_time': datetime.now().isoformat()
            }
            self.last_analysis_time = datetime.now()
            
            logger.debug(f"Анализ завершен. Проанализировано символов: {len(all_symbols)}, использовано моделей: {len(predictions_by_model)}")
            
            return self.last_analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа данных: {e}")
            return {
                'error': str(e),
                'ensemble_predictions': {},
                'individual_predictions': {},
                'symbols_analyzed': [],
                'models_used': []
            }
    
    async def _analyze_single_model(self, model: BaseNeuralNetwork, data: Dict[str, Any], portfolio_manager=None):
        """
        Анализ одной модели для всех символов
        
        Args:
            model: Модель для анализа
            data: Входные данные
            portfolio_manager: Менеджер портфеля для извлечения портфельных признаков
            
        Returns:
            Словарь с результатами анализа по каждому символу
        """
        try:
            # Подготовка данных для модели
            if 'historical' in data and isinstance(data['historical'], dict):
                predictions_by_symbol = {}
                
                # Анализируем каждый символ отдельно
                for symbol, symbol_data in data['historical'].items():
                    if not symbol_data.empty:
                        try:
                            # Передача портфельных данных в модель
                            prediction = await model.predict(symbol_data, portfolio_manager=portfolio_manager, symbol=symbol)
                            prediction['symbol'] = symbol  # Добавляем информацию о символе
                            predictions_by_symbol[symbol] = prediction
                            logger.debug(f"Модель {model.name} проанализировала {symbol}: {prediction.get('signal', 'N/A')}")
                        except Exception as e:
                            logger.error(f"Ошибка анализа {symbol} моделью {model.name}: {e}")
                            predictions_by_symbol[symbol] = {
                                'error': str(e),
                                'confidence': 0.0,
                                'signal': 'HOLD',
                                'symbol': symbol
                            }
                
                if not predictions_by_symbol:
                    raise ValueError(f"Нет данных для анализа в модели {model.name}")
                
                return predictions_by_symbol
            else:
                raise ValueError(f"Неправильный формат данных для модели {model.name}")
                
        except Exception as e:
            logger.error(f"Ошибка анализа модели {model.name}: {e}")
            raise
    
    def _create_ensemble_prediction(self, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создание ансамблевого предсказания
        
        Args:
            predictions: Предсказания от всех моделей
            
        Returns:
            Ансамблевое предсказание
        """
        try:
            if not predictions:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'method': 'no_predictions'
                }
            
            # Получение весов моделей
            model_weights = {}
            for model_config in self.config.get('models', []):
                model_weights[model_config['name']] = model_config.get('weight', 1.0)
            
            if self.ensemble_method == 'weighted_average':
                return self._weighted_average_ensemble(predictions, model_weights)
            elif self.ensemble_method == 'majority_vote':
                return self._majority_vote_ensemble(predictions, model_weights)
            elif self.ensemble_method == 'confidence_weighted':
                return self._confidence_weighted_ensemble(predictions, model_weights)
            else:
                logger.warning(f"Неизвестный метод ансамбля: {self.ensemble_method}")
                return self._weighted_average_ensemble(predictions, model_weights)
                
        except Exception as e:
            logger.error(f"Ошибка создания ансамблевого предсказания: {e}")
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'method': 'error',
                'error': str(e)
            }
    
    def _weighted_average_ensemble(self, predictions: Dict[str, Any], weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Взвешенное среднее ансамблевое предсказание
        
        Args:
            predictions: Предсказания от моделей
            weights: Веса моделей
            
        Returns:
            Взвешенное среднее предсказание
        """
        try:
            total_weight = 0
            weighted_price = 0
            weighted_confidence = 0
            signal_votes = {'BUY': 0, 'HOLD': 0, 'SELL': 0}
            
            for model_name, prediction in predictions.items():
                if 'error' in prediction:
                    continue
                
                weight = weights.get(model_name, 1.0)
                total_weight += weight
                
                # Обработка предсказаний цен
                if 'next_price' in prediction:
                    weighted_price += prediction['next_price'] * weight
                
                # Обработка торговых сигналов (XGBoost)
                if 'signal' in prediction:
                    signal = prediction['signal']
                    if signal in signal_votes:
                        signal_votes[signal] += weight
                
                # Обработка уверенности
                if 'confidence' in prediction:
                    weighted_confidence += prediction['confidence'] * weight
            
            if total_weight == 0:
                return {'signal': 'HOLD', 'confidence': 0.0}
            
            # Определение итогового сигнала
            final_signal = max(signal_votes, key=signal_votes.get)
            
            # Определение тренда на основе сигналов
            trend = 'sideways'  # По умолчанию
            if final_signal == 'BUY':
                trend = 'bullish'
            elif final_signal == 'SELL':
                trend = 'bearish'
            
            # Попытка получить тренд от DeepSeek модели
            for model_name, prediction in predictions.items():
                if 'trend' in prediction and prediction['trend'] != 'unknown':
                    trend = prediction['trend']
                    break
            
            return {
                'signal': final_signal,
                'trend': trend,
                'next_price': weighted_price / total_weight if weighted_price > 0 else None,
                'confidence': weighted_confidence / total_weight,
                'method': 'weighted_average',
                'signal_distribution': signal_votes
            }
            
        except Exception as e:
            logger.error(f"Ошибка взвешенного среднего: {e}")
            return {'signal': 'HOLD', 'confidence': 0.0}
    
    def _majority_vote_ensemble(self, predictions: Dict[str, Any], weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Ансамблевое предсказание по большинству голосов
        
        Args:
            predictions: Предсказания от моделей
            weights: Веса моделей
            
        Returns:
            Предсказание по большинству голосов
        """
        signal_votes = {'BUY': 0, 'HOLD': 0, 'SELL': 0}
        confidences = []
        
        for model_name, prediction in predictions.items():
            if 'error' in prediction:
                continue
            
            weight = weights.get(model_name, 1.0)
            
            if 'signal' in prediction:
                signal = prediction['signal']
                if signal in signal_votes:
                    signal_votes[signal] += weight
            
            if 'confidence' in prediction:
                confidences.append(prediction['confidence'])
        
        final_signal = max(signal_votes, key=signal_votes.get)
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        # Определение тренда на основе сигналов
        trend = 'sideways'  # По умолчанию
        if final_signal == 'BUY':
            trend = 'bullish'
        elif final_signal == 'SELL':
            trend = 'bearish'
        
        # Попытка получить тренд от DeepSeek модели
        for model_name, prediction in predictions.items():
            if 'trend' in prediction and prediction['trend'] != 'unknown':
                trend = prediction['trend']
                break
        
        return {
            'signal': final_signal,
            'trend': trend,
            'confidence': avg_confidence,
            'method': 'majority_vote',
            'signal_distribution': signal_votes
        }
    
    def _confidence_weighted_ensemble(self, predictions: Dict[str, Any], weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Ансамблевое предсказание с учетом уверенности моделей
        
        Args:
            predictions: Предсказания от моделей
            weights: Веса моделей
            
        Returns:
            Предсказание с учетом уверенности
        """
        signal_confidence = {'BUY': [], 'HOLD': [], 'SELL': []}
        
        for model_name, prediction in predictions.items():
            if 'error' in prediction:
                continue
            
            weight = weights.get(model_name, 1.0)
            confidence = prediction.get('confidence', 0.0)
            
            if 'signal' in prediction:
                signal = prediction['signal']
                if signal in signal_confidence:
                    signal_confidence[signal].append(confidence * weight)
        
        # Выбор сигнала с наибольшей средней уверенностью
        signal_avg_confidence = {}
        for signal, confidences in signal_confidence.items():
            if confidences:
                signal_avg_confidence[signal] = np.mean(confidences)
            else:
                signal_avg_confidence[signal] = 0.0
        
        final_signal = max(signal_avg_confidence, key=signal_avg_confidence.get)
        final_confidence = signal_avg_confidence[final_signal]
        
        # Определение тренда на основе сигналов
        trend = 'sideways'  # По умолчанию
        if final_signal == 'BUY':
            trend = 'bullish'
        elif final_signal == 'SELL':
            trend = 'bearish'
        
        # Попытка получить тренд от DeepSeek модели
        for model_name, prediction in predictions.items():
            if 'trend' in prediction and prediction['trend'] != 'unknown':
                trend = prediction['trend']
                break
        
        return {
            'signal': final_signal,
            'trend': trend,
            'confidence': final_confidence,
            'method': 'confidence_weighted',
            'signal_confidence': signal_avg_confidence
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса менеджера нейросетей
        
        Returns:
            Словарь со статусом
        """
        model_status = {}
        for model_name, model in self.models.items():
            model_status[model_name] = model.get_status()
        
        return {
            'total_models': len(self.models),
            'trained_models': sum(1 for model in self.models.values() if model.is_trained),
            'models_status': model_status,
            'ensemble_method': self.ensemble_method,
            'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None
        }
    
    async def save_models(self):
        """
        Сохранение всех обученных моделей
        """
        try:
            for model_name, model in self.models.items():
                if model.is_trained:
                    model_path = self.models_dir / f"{model_name}.pkl"
                    with open(model_path, 'wb') as f:
                        pickle.dump(model, f)
                    logger.info(f"Модель {model_name} сохранена в {model_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения моделей: {e}")
    
    async def load_models(self):
        """
        Загрузка сохраненных моделей
        """
        try:
            loaded_count = 0
            for model_name, model in self.models.items():
                model_path = self.models_dir / f"{model_name}.pkl"
                if model_path.exists():
                    try:
                        with open(model_path, 'rb') as f:
                            saved_model = pickle.load(f)
                        # Копируем состояние обученной модели
                        model.is_trained = saved_model.is_trained
                        model.performance_metrics = saved_model.performance_metrics
                        model.last_prediction = saved_model.last_prediction
                        model.last_prediction_time = saved_model.last_prediction_time
                        
                        # Для XGBoost копируем модель
                        if hasattr(model, 'model') and hasattr(saved_model, 'model'):
                            model.model = saved_model.model
                            model.feature_columns = saved_model.feature_columns
                            model.feature_importance = saved_model.feature_importance
                        
                        loaded_count += 1
                        logger.info(f"Модель {model_name} загружена из {model_path}")
                    except Exception as e:
                        logger.error(f"Ошибка загрузки модели {model_name}: {e}")
            
            if loaded_count > 0:
                logger.info(f"Загружено {loaded_count} обученных моделей")
            else:
                logger.info("Обученные модели не найдены")
                
        except Exception as e:
            logger.error(f"Ошибка загрузки моделей: {e}")
