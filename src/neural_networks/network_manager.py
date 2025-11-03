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
        self.last_evaluation = None
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
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
    
    async def train_models(self, data: Dict[str, Any], target: str = 'Close', news_data: Dict[str, Any] = None, 
                          data_provider=None, force_retrain: bool = False):
        """
        Обучение всех моделей
        
        Args:
            data: Данные для обучения
            target: Целевая переменная
            news_data: Новостные данные для обучения (если None, загружаются из хранилища)
            data_provider: Провайдер данных для загрузки новостей из хранилища
            force_retrain: Принудительное переобучение (если True, переобучает уже обученные модели)
        """
        # Получение параметра force_retrain из конфигурации, если не указан явно
        if not force_retrain:
            force_retrain = self.config.get('force_retrain', False)
        
        if force_retrain:
            logger.info("Режим принудительного переобучения включен")
        
        logger.info("Начало обучения всех моделей")
        
        # Если новостные данные не предоставлены, пытаемся загрузить из хранилища
        if news_data is None and data_provider is not None:
            try:
                news_config = data_provider.config.get('news', {})
                if news_config.get('enabled', True) and news_config.get('include_news_in_training', False):
                    training_days = news_config.get('training_news_days', 180)
                    if hasattr(data_provider, 'news_provider') and data_provider.news_provider:
                        logger.info(f"Загрузка новостных данных для обучения из хранилища ({training_days} дней)")
                        symbols = list(data.get('historical', {}).keys()) if 'historical' in data else []
                        if symbols:
                            news_data = await data_provider.news_provider.get_training_news(symbols, training_days)
                            logger.info(f"Загружены новостные данные для {len(news_data)} символов")
            except Exception as e:
                logger.warning(f"Не удалось загрузить новостные данные из хранилища: {e}")
        
        training_tasks = []
        
        for model_name, model in self.models.items():
            if model.is_trained and not force_retrain:
                logger.debug(f"Модель {model_name} уже обучена, пропускаем")
                continue
            elif force_retrain and model.is_trained:
                logger.info(f"Принудительное переобучение модели {model_name}")
                model.is_trained = False
            
            # Создание задачи обучения для каждой модели
            task = asyncio.create_task(self._train_single_model(model, data, target, news_data))
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
        
        # Проверка результатов обучения (если включено)
        if self.config.get('evaluate_after_training', True):
            try:
                await self.evaluate_training_results(data, target, news_data)
            except Exception as e:
                logger.error(f"Ошибка проверки результатов обучения: {e}")
    
    async def evaluate_training_results(self, data: Dict[str, Any], target: str = 'Close', news_data: Dict[str, Any] = None):
        """
        Проверка результатов обучения нейросетей на тестовых данных
        
        Args:
            data: Данные для обучения
            target: Целевая переменная
            news_data: Новостные данные
        """
        logger.info("Начало проверки результатов обучения")
        
        evaluation_results = {
            'timestamp': datetime.now().isoformat(),
            'models': {},
            'summary': {},
            'recommendations': []
        }
        
        trained_models = []
        all_test_predictions = {}
        
        # Проверка каждой модели
        for model_name, model in self.models.items():
            try:
                if not model.is_trained:
                    logger.warning(f"Модель {model_name} не обучена, пропускаем проверку")
                    evaluation_results['models'][model_name] = {
                        'status': 'not_trained',
                        'error': 'Модель не обучена'
                    }
                    continue
                
                trained_models.append(model_name)
                model_eval = await self._evaluate_single_model(model, data, target, news_data)
                evaluation_results['models'][model_name] = model_eval
                
                # Сохранение предсказаний для сравнения
                if 'test_predictions' in model_eval:
                    all_test_predictions[model_name] = model_eval['test_predictions']
                    
            except Exception as e:
                logger.error(f"Ошибка проверки модели {model_name}: {e}")
                evaluation_results['models'][model_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Сравнение моделей
        if len(trained_models) > 1:
            comparison = self._compare_models(evaluation_results['models'])
            evaluation_results['comparison'] = comparison
        
        # Генерация сводки
        summary = self._generate_summary(evaluation_results, trained_models)
        evaluation_results['summary'] = summary
        
        # Генерация рекомендаций
        recommendations = self._generate_recommendations(evaluation_results)
        evaluation_results['recommendations'] = recommendations
        
        # Сохранение результатов
        self.last_evaluation = evaluation_results
        
        # Вывод и сохранение отчета
        report_text = self._format_evaluation_report(evaluation_results)
        print("\n" + "="*80)
        print(report_text)
        print("="*80 + "\n")
        
        # Сохранение в файл
        await self._save_evaluation_report(report_text, evaluation_results)
        
        logger.info("Проверка результатов обучения завершена")
        
        return evaluation_results
    
    async def _evaluate_single_model(self, model: BaseNeuralNetwork, data: Dict[str, Any], target: str, news_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Проверка одной модели
        
        Args:
            model: Модель для проверки
            data: Данные
            target: Целевая переменная
            news_data: Новостные данные
            
        Returns:
            Результаты проверки модели
        """
        result = {
            'model_name': model.name,
            'model_type': type(model).__name__,
            'status': 'trained',
            'training_metrics': {},
            'test_metrics': {},
            'signal_distribution': {},
            'avg_confidence': 0.0,
            'news_data_used': bool(news_data),
            'feature_count': 0,
            'warnings': []
        }
        
        # Проверка метрик обучения
        # Для DeepSeek сначала получаем актуальные метрики через _evaluate_training_quality()
        training_quality_metrics = None
        if isinstance(model, DeepSeekNetwork):
            logger.debug(f"DeepSeek {model.name}: Получение актуальных метрик через _evaluate_training_quality()")
            try:
                training_quality_metrics = await model._evaluate_training_quality(data, news_data)
                if training_quality_metrics:
                    # Обновляем performance_metrics уже выполнено в _evaluate_training_quality()
                    result['training_metrics'] = model.performance_metrics.copy()
                    result['training_metrics'].update(training_quality_metrics)
                else:
                    # Если не удалось получить метрики, используем старые
                    if hasattr(model, 'performance_metrics') and model.performance_metrics:
                        result['training_metrics'] = model.performance_metrics.copy()
            except Exception as e:
                logger.error(f"Ошибка получения метрик DeepSeek {model.name}: {e}")
                # Fallback на старые метрики
                if hasattr(model, 'performance_metrics') and model.performance_metrics:
                    result['training_metrics'] = model.performance_metrics.copy()
        elif hasattr(model, 'performance_metrics') and model.performance_metrics:
            result['training_metrics'] = model.performance_metrics.copy()
        
        # Оценка качества метрик с использованием актуальных данных
        if result.get('training_metrics'):
            if isinstance(model, XGBoostNetwork):
                accuracy = result['training_metrics'].get('accuracy', 0.0)
                precision = result['training_metrics'].get('precision', 0.0)
                recall = result['training_metrics'].get('recall', 0.0)
                
                result['training_metrics']['quality'] = self._evaluate_metric_quality(accuracy, precision, recall)
                
                if accuracy < 0.3 or precision < 0.3 or recall < 0.3:
                    result['warnings'].append("Очень низкие метрики качества (< 0.3)")
                    
            elif isinstance(model, DeepSeekNetwork):
                # Используем актуальные метрики из training_quality_metrics или performance_metrics
                if training_quality_metrics:
                    # Используем актуальные метрики из проверки
                    patterns = training_quality_metrics.get('patterns_found', 0)
                    avg_conf = training_quality_metrics.get('avg_confidence', 0.0)
                    analysis_quality = training_quality_metrics.get('analysis_quality', 0.0)
                    trend_accuracy = training_quality_metrics.get('trend_accuracy', 0.0)
                    patterns_in_analysis = training_quality_metrics.get('patterns_in_analysis', 0)
                else:
                    # Fallback на старые метрики, если не удалось получить новые
                    patterns = result['training_metrics'].get('patterns_found', 0)
                    avg_conf = result['training_metrics'].get('avg_confidence', 0.0)
                    analysis_quality = result['training_metrics'].get('analysis_quality', 0.0)
                    trend_accuracy = result['training_metrics'].get('trend_accuracy', 0.0)
                    patterns_in_analysis = result['training_metrics'].get('patterns_in_analysis', 0)
                
                # Проверка предупреждений использует АКТУАЛЬНЫЕ метрики
                if avg_conf < 0.3:
                    result['warnings'].append("Очень низкая уверенность модели (< 0.3)")
                
                if analysis_quality < 0.3:
                    # Более детальная диагностика
                    if patterns_in_analysis == 0:
                        result['warnings'].append(
                            "Низкое качество анализа (< 0.3). API не вернул конкретные паттерны в анализе. "
                            "Проверьте промпт и ответ API."
                        )
                    else:
                        result['warnings'].append(
                            f"Низкое качество анализа (< 0.3). Найдено паттернов в анализе: {patterns_in_analysis}. "
                            "Возможно, нужно улучшить промпт для более детального анализа."
                        )
                else:
                    # Если качество хорошее, логируем успех
                    logger.debug(f"DeepSeek {model.name}: Качество анализа хорошее: {analysis_quality:.3f}, паттернов: {patterns_in_analysis}")
                
                result['training_metrics']['quality'] = self._evaluate_deepseek_quality(
                    patterns, avg_conf, analysis_quality, trend_accuracy
                )
        else:
            result['warnings'].append("Метрики обучения отсутствуют")
        
        # Проверка на тестовой выборке
        try:
            if 'historical' in data and isinstance(data['historical'], dict):
                # Для DeepSeek метрики уже получены выше, просто добавляем их в test_metrics
                if isinstance(model, DeepSeekNetwork):
                    if training_quality_metrics:
                        analysis_quality = training_quality_metrics.get('analysis_quality', 0.0)
                        patterns_in_analysis = training_quality_metrics.get('patterns_in_analysis', 0)
                        avg_confidence = training_quality_metrics.get('avg_confidence', 0.0)
                        
                        result['avg_confidence'] = avg_confidence
                        
                        # Добавляем информацию о паттернах
                        if patterns_in_analysis > 0:
                            logger.debug(f"DeepSeek {model.name}: При проверке найдено паттернов: {patterns_in_analysis}")
                        else:
                            logger.warning(f"DeepSeek {model.name}: При проверке не найдено паттернов в анализе")
                        
                        # Тестовые метрики для DeepSeek
                        result['test_metrics'] = {
                            'analysis_quality': analysis_quality,
                            'patterns_in_analysis': patterns_in_analysis,
                            'avg_confidence': avg_confidence
                        }
                
                else:
                    # Для других моделей (XGBoost и т.д.) используем стандартный метод predict()
                    # Объединение данных всех символов
                    combined_data = []
                    for symbol, symbol_data in data['historical'].items():
                        if not symbol_data.empty:
                            combined_data.append(symbol_data)
                    
                    if combined_data:
                        combined_df = pd.concat(combined_data, ignore_index=True)
                        
                        # Разделение на обучающую и тестовую выборки (20%)
                        test_size = int(len(combined_df) * 0.2)
                        if test_size > 0:
                            test_data = combined_df.tail(test_size)
                            
                            # Получение предсказаний на тестовой выборке
                            test_predictions = []
                            signals = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
                            confidences = []
                            
                            # Разбиваем тестовые данные на части для анализа
                            chunk_size = min(100, len(test_data))
                            for i in range(0, len(test_data), chunk_size):
                                chunk = test_data.iloc[i:i+chunk_size]
                                try:
                                    prediction = await model.predict(chunk, news_data=news_data)
                                    signal = prediction.get('signal', 'HOLD')
                                    confidence = prediction.get('confidence', 0.0)
                                    
                                    signals[signal] = signals.get(signal, 0) + 1
                                    confidences.append(confidence)
                                    test_predictions.append({
                                        'signal': signal,
                                        'confidence': confidence
                                    })
                                except Exception as e:
                                    logger.debug(f"Ошибка предсказания на тестовом чанке: {e}")
                                    continue
                            
                            result['test_predictions'] = test_predictions
                            result['signal_distribution'] = signals
                            result['avg_confidence'] = float(np.mean(confidences)) if confidences else 0.0
                            
                            # Расчет метрик на тестовой выборке (если доступны реальные значения)
                            # Для XGBoost можно сравнить с метриками обучения
                            if isinstance(model, XGBoostNetwork) and 'accuracy' in result['training_metrics']:
                                # Приблизительная оценка на основе распределения сигналов
                                total_signals = sum(signals.values())
                                if total_signals > 0:
                                    # Баланс сигналов (чем более равномерно, тем лучше, если нет перекоса)
                                    signal_balance = max(signals.values()) / total_signals
                                    if signal_balance > 0.8:
                                        result['warnings'].append(
                                            f"Сильный перекос в сторону одного сигнала: "
                                            f"{max(signals.items(), key=lambda x: x[1])[0]} составляет "
                                            f"{signal_balance*100:.1f}%"
                                        )
                                    
                                    result['test_metrics'] = {
                                        'signal_balance': float(signal_balance),
                                        'avg_confidence': result['avg_confidence'],
                                        'total_predictions': total_signals
                                    }
                        else:
                            result['warnings'].append("Тестовая выборка слишком мала для проверки")
        except Exception as e:
            logger.warning(f"Ошибка проверки на тестовой выборке для {model.name}: {e}")
            result['warnings'].append(f"Не удалось проверить на тестовой выборке: {str(e)}")
        
        # Проверка количества признаков
        if hasattr(model, 'feature_columns') and model.feature_columns:
            result['feature_count'] = len(model.feature_columns)
        elif hasattr(model, 'feature_importance') and model.feature_importance:
            result['feature_count'] = len(model.feature_importance)
        
        # Проверка использования новостных данных
        if hasattr(model, 'performance_metrics') and model.performance_metrics:
            news_used = model.performance_metrics.get('news_features_used', False)
            result['news_data_used'] = news_used or bool(news_data)
        
        return result
    
    def _evaluate_metric_quality(self, accuracy: float, precision: float, recall: float) -> str:
        """
        Оценка качества метрик
        
        Args:
            accuracy: Точность
            precision: Прецизионность
            recall: Полнота
            
        Returns:
            Оценка качества
        """
        avg_metric = (accuracy + precision + recall) / 3
        
        if avg_metric > 0.8:
            return "Отлично"
        elif avg_metric > 0.6:
            return "Хорошо"
        elif avg_metric > 0.4:
            return "Удовлетворительно"
        else:
            return "Плохо"
    
    def _evaluate_deepseek_quality(self, patterns: int, avg_conf: float, analysis_quality: float, trend_accuracy: float) -> str:
        """
        Оценка качества DeepSeek модели
        
        Args:
            patterns: Количество найденных паттернов
            avg_conf: Средняя уверенность
            analysis_quality: Качество анализа
            trend_accuracy: Точность тренда
            
        Returns:
            Оценка качества
        """
        # Улучшенная оценка качества для DeepSeek
        # DeepSeek может найти только 1 паттерн (один запрос к API), поэтому
        # не наказываем за малое количество паттернов, если анализ качественный
        
        # Оценка на основе уверенности (самый важный фактор)
        confidence_score = avg_conf
        
        # Оценка качества анализа (учитывает все факторы)
        quality_score = analysis_quality
        
        # Оценка точности тренда
        trend_score = trend_accuracy
        
        # Оценка количества паттернов (менее важна, т.к. DeepSeek возвращает один анализ)
        # Если паттернов больше 0, это уже хорошо (базовая оценка 0.5)
        if patterns > 0:
            patterns_score = 0.5 + min(patterns / 10.0, 0.5)  # От 0.5 до 1.0
        else:
            patterns_score = 0.0
        
        # Взвешенное среднее (больше веса на уверенность и качество анализа)
        avg_metric = (
            confidence_score * 0.35 +      # 35% - уверенность
            quality_score * 0.35 +          # 35% - качество анализа
            trend_score * 0.20 +            # 20% - точность тренда
            patterns_score * 0.10           # 10% - количество паттернов
        )
        
        if avg_metric > 0.8:
            return "Отлично"
        elif avg_metric > 0.6:
            return "Хорошо"
        elif avg_metric > 0.4:
            return "Удовлетворительно"
        else:
            return "Плохо"
    
    def _compare_models(self, models_eval: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Сравнение моделей
        
        Args:
            models_eval: Результаты проверки моделей
            
        Returns:
            Результаты сравнения
        """
        comparison = {
            'best_model': None,
            'best_score': 0.0,
            'model_scores': {},
            'consistency': 'unknown'
        }
        
        model_scores = {}
        
        for model_name, model_eval in models_eval.items():
            if model_eval.get('status') != 'trained':
                continue
            
            # Расчет общего скора модели
            score = 0.0
            training_metrics = model_eval.get('training_metrics', {})
            
            if 'accuracy' in training_metrics:
                # XGBoost модель
                accuracy = training_metrics.get('accuracy', 0.0)
                precision = training_metrics.get('precision', 0.0)
                recall = training_metrics.get('recall', 0.0)
                score = (accuracy + precision + recall) / 3
            elif 'avg_confidence' in training_metrics:
                # DeepSeek модель
                score = training_metrics.get('avg_confidence', 0.0)
            
            # Бонус за высокую уверенность
            avg_conf = model_eval.get('avg_confidence', 0.0)
            score = (score + avg_conf) / 2
            
            model_scores[model_name] = score
        
        if model_scores:
            best_model = max(model_scores.items(), key=lambda x: x[1])
            comparison['best_model'] = best_model[0]
            comparison['best_score'] = best_model[1]
            comparison['model_scores'] = model_scores
            
            # Проверка согласованности
            if len(model_scores) > 1:
                scores_list = list(model_scores.values())
                score_std = np.std(scores_list)
                if score_std < 0.1:
                    comparison['consistency'] = 'high'
                elif score_std < 0.2:
                    comparison['consistency'] = 'medium'
                else:
                    comparison['consistency'] = 'low'
                    comparison['warning'] = "Модели сильно расходятся в качестве"
        
        return comparison
    
    def _generate_summary(self, evaluation_results: Dict[str, Any], trained_models: List[str]) -> Dict[str, Any]:
        """
        Генерация сводки
        
        Args:
            evaluation_results: Результаты проверки
            trained_models: Список обученных моделей
            
        Returns:
            Сводка
        """
        summary = {
            'total_models': len(self.models),
            'trained_models': len(trained_models),
            'best_model': None,
            'average_quality': 'unknown'
        }
        
        if 'comparison' in evaluation_results:
            summary['best_model'] = evaluation_results['comparison'].get('best_model')
        
        # Подсчет среднего качества
        qualities = []
        for model_name, model_eval in evaluation_results['models'].items():
            if model_eval.get('status') == 'trained':
                training_metrics = model_eval.get('training_metrics', {})
                quality = training_metrics.get('quality', 'unknown')
                if quality != 'unknown':
                    qualities.append(quality)
        
        if qualities:
            quality_map = {'Отлично': 4, 'Хорошо': 3, 'Удовлетворительно': 2, 'Плохо': 1}
            avg_quality_num = np.mean([quality_map.get(q, 2) for q in qualities])
            if avg_quality_num >= 3.5:
                summary['average_quality'] = 'Отлично'
            elif avg_quality_num >= 2.5:
                summary['average_quality'] = 'Хорошо'
            elif avg_quality_num >= 1.5:
                summary['average_quality'] = 'Удовлетворительно'
            else:
                summary['average_quality'] = 'Плохо'
        
        return summary
    
    def _generate_recommendations(self, evaluation_results: Dict[str, Any]) -> List[str]:
        """
        Генерация рекомендаций по улучшению
        
        Args:
            evaluation_results: Результаты проверки
            
        Returns:
            Список рекомендаций
        """
        recommendations = []
        
        for model_name, model_eval in evaluation_results['models'].items():
            if model_eval.get('status') != 'trained':
                continue
            
            training_metrics = model_eval.get('training_metrics', {})
            quality = training_metrics.get('quality', 'unknown')
            
            # Низкие метрики
            if quality == 'Плохо':
                recommendations.append(
                    f"{model_name}: Метрики качества низкие. Рекомендуется увеличить объем данных "
                    f"или изменить параметры модели (например, уменьшить learning_rate или увеличить n_estimators)"
                )
            
            # Переобучение (если метрики обучения сильно выше тестовых)
            if 'test_metrics' in model_eval and 'training_metrics' in model_eval:
                train_acc = training_metrics.get('accuracy', 0.0)
                test_conf = model_eval.get('avg_confidence', 0.0)
                if train_acc > 0.9 and test_conf < 0.5:
                    recommendations.append(
                        f"{model_name}: Возможно переобучение. Метрики обучения высокие, "
                        f"но уверенность на тестовых данных низкая. Рекомендуется увеличить регуляризацию "
                        f"или добавить больше данных"
                    )
            
            # Перекос сигналов
            signal_dist = model_eval.get('signal_distribution', {})
            if signal_dist:
                total = sum(signal_dist.values())
                if total > 0:
                    max_signal_ratio = max(signal_dist.values()) / total
                    if max_signal_ratio > 0.8:
                        dominant_signal = max(signal_dist.items(), key=lambda x: x[1])[0]
                        recommendations.append(
                            f"{model_name}: Доминирует сигнал {dominant_signal} ({max_signal_ratio*100:.1f}%). "
                            f"Рекомендуется пересмотреть пороги классификации (buy_threshold/sell_threshold)"
                        )
        
        # Согласованность моделей
        if 'comparison' in evaluation_results:
            consistency = evaluation_results['comparison'].get('consistency', 'unknown')
            if consistency == 'low':
                recommendations.append(
                    "Модели сильно расходятся в предсказаниях. Рекомендуется проверить "
                    "входные данные и параметры моделей, возможно требуется больше данных для обучения"
                )
        
        if not recommendations:
            recommendations.append("Все модели показывают хорошие результаты. Продолжайте мониторинг качества.")
        
        return recommendations
    
    def _format_evaluation_report(self, evaluation_results: Dict[str, Any]) -> str:
        """
        Форматирование отчета о проверке
        
        Args:
            evaluation_results: Результаты проверки
            
        Returns:
            Текст отчета
        """
        timestamp = datetime.fromisoformat(evaluation_results['timestamp'])
        report_lines = [
            "="*80,
            "     === ОТЧЕТ О ПРОВЕРКЕ РЕЗУЛЬТАТОВ ОБУЧЕНИЯ ===",
            f"     Дата: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "="*80,
            ""
        ]
        
        # Проверка каждой модели
        for model_name, model_eval in evaluation_results['models'].items():
            if model_eval.get('status') != 'trained':
                report_lines.append(f"[{model_name}]")
                report_lines.append(f"  Статус: Не обучена ✗")
                report_lines.append("")
                continue
            
            report_lines.append(f"[{model_name}]")
            report_lines.append(f"  Статус: Обучена ✓")
            report_lines.append(f"  Тип: {model_eval.get('model_type', 'Unknown')}")
            
            # Метрики обучения
            training_metrics = model_eval.get('training_metrics', {})
            if training_metrics:
                report_lines.append("  Метрики на обучающей выборке:")
                
                if 'accuracy' in training_metrics:
                    # XGBoost
                    accuracy = training_metrics.get('accuracy', 0.0)
                    precision = training_metrics.get('precision', 0.0)
                    recall = training_metrics.get('recall', 0.0)
                    quality = training_metrics.get('quality', 'Unknown')
                    
                    report_lines.append(f"    - Accuracy: {accuracy:.3f} ({quality})")
                    report_lines.append(f"    - Precision: {precision:.3f} ({quality})")
                    report_lines.append(f"    - Recall: {recall:.3f} ({quality})")
                else:
                    # DeepSeek
                    patterns = training_metrics.get('patterns_found', 0)
                    avg_conf = training_metrics.get('avg_confidence', 0.0)
                    analysis_quality = training_metrics.get('analysis_quality', 0.0)
                    trend_accuracy = training_metrics.get('trend_accuracy', 0.0)
                    quality = training_metrics.get('quality', 'Unknown')
                    
                    report_lines.append(f"    - Паттернов найдено: {patterns}")
                    report_lines.append(f"    - Средняя уверенность: {avg_conf:.3f}")
                    report_lines.append(f"    - Качество анализа: {analysis_quality:.3f}")
                    report_lines.append(f"    - Точность тренда: {trend_accuracy:.3f}")
                    report_lines.append(f"    - Общая оценка: {quality}")
            
            # Метрики на тестовой выборке
            test_metrics = model_eval.get('test_metrics', {})
            if test_metrics:
                report_lines.append("  Метрики на тестовой выборке:")
                for key, value in test_metrics.items():
                    if isinstance(value, float):
                        report_lines.append(f"    - {key}: {value:.3f}")
                    else:
                        report_lines.append(f"    - {key}: {value}")
            
            # Распределение сигналов
            signal_dist = model_eval.get('signal_distribution', {})
            if signal_dist:
                total = sum(signal_dist.values())
                if total > 0:
                    report_lines.append("  Распределение сигналов:")
                    for signal, count in signal_dist.items():
                        percentage = (count / total) * 100
                        report_lines.append(f"    - {signal}: {percentage:.1f}%")
            
            # Средняя уверенность
            avg_conf = model_eval.get('avg_confidence', 0.0)
            report_lines.append(f"  Средняя уверенность: {avg_conf:.3f}")
            
            # Использование новостных данных
            news_used = model_eval.get('news_data_used', False)
            report_lines.append(f"  Использованы новостные данные: {'Да' if news_used else 'Нет'}")
            
            # Количество признаков
            feature_count = model_eval.get('feature_count', 0)
            if feature_count > 0:
                report_lines.append(f"  Количество признаков: {feature_count}")
            
            # Предупреждения
            warnings = model_eval.get('warnings', [])
            if warnings:
                report_lines.append("  Предупреждения:")
                for warning in warnings:
                    report_lines.append(f"    ⚠ {warning}")
            
            report_lines.append("")
        
        # Сводка
        summary = evaluation_results.get('summary', {})
        report_lines.append("="*80)
        report_lines.append("=== СВОДКА ===")
        report_lines.append(f"Всего моделей: {summary.get('total_models', 0)}")
        report_lines.append(f"Обучено успешно: {summary.get('trained_models', 0)}")
        
        best_model = summary.get('best_model')
        if best_model:
            comparison = evaluation_results.get('comparison', {})
            best_score = comparison.get('best_score', 0.0)
            report_lines.append(f"Лучшая модель: {best_model} (score: {best_score:.3f})")
        
        avg_quality = summary.get('average_quality', 'unknown')
        if avg_quality != 'unknown':
            report_lines.append(f"Среднее качество: {avg_quality}")
        
        # Рекомендации
        recommendations = evaluation_results.get('recommendations', [])
        if recommendations:
            report_lines.append("")
            report_lines.append("=== РЕКОМЕНДАЦИИ ===")
            for i, rec in enumerate(recommendations, 1):
                report_lines.append(f"{i}. {rec}")
        
        report_lines.append("="*80)
        
        return "\n".join(report_lines)
    
    async def _save_evaluation_report(self, report_text: str, evaluation_results: Dict[str, Any]):
        """
        Сохранение отчета в файл
        
        Args:
            report_text: Текст отчета
            evaluation_results: Результаты проверки
        """
        try:
            timestamp = datetime.fromisoformat(evaluation_results['timestamp'])
            filename = f"training_evaluation_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
            filepath = self.reports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            logger.info(f"Отчет о проверке сохранен в {filepath}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения отчета: {e}")
    
    async def _train_single_model(self, model: BaseNeuralNetwork, data: Dict[str, Any], target: str, news_data: Dict[str, Any] = None):
        """
        Обучение одной модели
        
        Args:
            model: Модель для обучения
            data: Данные для обучения
            target: Целевая переменная
            news_data: Новостные данные для обучения
        """
        try:
            # Подготовка данных для конкретной модели
            if 'historical' in data and isinstance(data['historical'], dict):
                # Подготовка данных каждого символа отдельно с нормализацией
                prepared_data_list = []
                symbols_list = []
                
                for symbol, symbol_data in data['historical'].items():
                    if symbol_data.empty:
                        continue
                    
                    # Подготовка признаков для символа (без финальной нормализации)
                    features = self._prepare_symbol_features(model, symbol_data, symbol, news_data)
                    
                    # Нормализация данных символа отдельно
                    features = self._normalize_symbol_features(features)
                    
                    # Добавление признака символа
                    features['symbol'] = symbol
                    
                    prepared_data_list.append(features)
                    symbols_list.append(symbol)
                
                if not prepared_data_list:
                    logger.warning(f"Нет данных для обучения модели {model.name}")
                    return
                
                # Объединение данных всех символов
                combined_df = pd.concat(prepared_data_list, ignore_index=True)
                
                # One-Hot Encoding для символа
                symbol_dummies = pd.get_dummies(combined_df['symbol'], prefix='symbol')
                combined_df = pd.concat([combined_df.drop('symbol', axis=1), symbol_dummies], axis=1)
                
                logger.info(f"Подготовлено данных для обучения модели {model.name}: {len(combined_df)} строк, {len(symbols_list)} символов: {symbols_list}")
                
                # Обучение модели с предобработанными данными
                # Параметр skip_normalization нужен только для XGBoost моделей
                # Параметр symbols передается для DeepSeek моделей
                if isinstance(model, XGBoostNetwork):
                    await model.train(combined_df, target, news_data, skip_normalization=True)
                elif isinstance(model, DeepSeekNetwork):
                    await model.train(combined_df, target, news_data, symbols=symbols_list)
                else:
                    await model.train(combined_df, target, news_data)
            else:
                logger.warning(f"Неправильный формат данных для модели {model.name}")
                
        except Exception as e:
            logger.error(f"Ошибка обучения модели {model.name}: {e}")
            raise
    
    def _prepare_symbol_features(self, model: BaseNeuralNetwork, symbol_data: pd.DataFrame, symbol: str, news_data: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Подготовка признаков для одного символа (без финальной нормализации)
        
        Args:
            model: Модель
            symbol_data: Данные символа
            symbol: Символ
            news_data: Новостные данные
            
        Returns:
            Подготовленные признаки без нормализации
        """
        features = symbol_data.copy()
        
        # Добавление технических индикаторов
        features = model._add_technical_indicators(features)
        
        # Добавление временных признаков
        features = model._add_time_features(features)
        
        # Добавление новостных признаков
        if news_data:
            features = model._add_news_features(features, news_data, symbol)
        
        return features
    
    def _normalize_symbol_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Нормализация признаков для одного символа
        
        Args:
            features: Признаки символа
            
        Returns:
            Нормализованные признаки
        """
        df = features.copy()
        
        # Нормализация ценовых данных
        price_columns = ['Open', 'High', 'Low', 'Close']
        for col in price_columns:
            if col in df.columns:
                rolling_mean = df[col].rolling(50).mean()
                rolling_std = df[col].rolling(50).std()
                # Избегаем деления на ноль
                rolling_std = rolling_std.replace(0, 1.0)  # Заменяем 0 на 1
                rolling_std = rolling_std.fillna(1.0)  # Заполняем NaN
                df[f'{col}_norm'] = (df[col] - rolling_mean) / rolling_std
                # Заполняем NaN в нормализованных данных
                df[f'{col}_norm'] = df[f'{col}_norm'].fillna(0.0)
        
        return df
    
    async def analyze(self, data: Dict[str, Any], portfolio_manager=None, news_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Анализ данных всеми моделями для всех символов
        
        Args:
            data: Входные данные
            portfolio_manager: Менеджер портфеля для извлечения портфельных признаков
            news_data: Новостные данные для анализа
            
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
                task = asyncio.create_task(self._analyze_single_model(model, data, portfolio_manager, news_data))
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
                
                # Добавление новостной информации в ансамблевое предсказание
                if news_data and symbol in news_data:
                    ensemble_predictions[symbol]['news_summary'] = news_data[symbol]
            
            # Сохранение результатов
            self.last_analysis = {
                'individual_predictions': predictions_by_model,
                'ensemble_predictions': ensemble_predictions,  # Теперь по символам
                'symbols_analyzed': list(all_symbols),
                'models_used': list(predictions_by_model.keys()),
                'analysis_time': datetime.now().isoformat(),
                'news_data_included': bool(news_data)
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
                'models_used': [],
                'news_data_included': False
            }
    
    async def _analyze_single_model(self, model: BaseNeuralNetwork, data: Dict[str, Any], portfolio_manager=None, news_data: Dict[str, Any] = None):
        """
        Анализ одной модели для всех символов
        
        Args:
            model: Модель для анализа
            data: Входные данные
            portfolio_manager: Менеджер портфеля для извлечения портфельных признаков
            news_data: Новостные данные для анализа
            
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
                            # Передача портфельных и новостных данных в модель
                            prediction = await model.predict(symbol_data, portfolio_manager=portfolio_manager, symbol=symbol, news_data=news_data)
                            prediction['symbol'] = symbol  # Добавляем информацию о символе
                            predictions_by_symbol[symbol] = prediction
                            logger.debug(f"Модель {model.name} проанализировала {symbol}: {prediction.get('signal', 'N/A')}")
                        except Exception as e:
                            logger.error(f"Ошибка анализа {symbol} моделью {model.name}: {e}")
                            predictions_by_symbol[symbol] = {
                                'error': str(e),
                                'confidence': 0.0,
                                'signal': 'HOLD',
                                'symbol': symbol,
                                'news_info': {}
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
