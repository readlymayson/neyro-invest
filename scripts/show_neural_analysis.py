# -*- coding: utf-8 -*-
"""
Скрипт для отображения всей доступной информации по анализу нейросетей
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import pickle

# Добавление корневой директории в путь
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.neural_networks.network_manager import NetworkManager
from src.utils.config_manager import ConfigManager
from src.data.data_provider import DataProvider
from loguru import logger
import pandas as pd
import numpy as np


class NeuralAnalysisReporter:
    """Класс для отображения информации об анализе нейросетей"""
    
    def __init__(self, config_path: str = "config/main.yaml"):
        """
        Инициализация репортера
        
        Args:
            config_path: Путь к конфигурационному файлу
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        self.network_manager = NetworkManager(self.config['neural_networks'])
        self.data_provider = DataProvider(self.config['data'])
        self.models_dir = Path("models")
        self.data_dir = Path("data")
        
    async def initialize(self):
        """Инициализация менеджера нейросетей и провайдера данных"""
        try:
            await self.data_provider.initialize()
            await self.network_manager.initialize()
            logger.info("Менеджер нейросетей и провайдер данных инициализированы")
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
    
    def print_header(self, title: str, width: int = 80):
        """Печать заголовка"""
        print("\n" + "=" * width)
        print(f"  {title}")
        print("=" * width)
    
    def print_section(self, title: str, width: int = 80):
        """Печать заголовка секции"""
        print("\n" + "-" * width)
        print(f"  {title}")
        print("-" * width)
    
    def format_dict(self, data: Dict[str, Any], indent: int = 2) -> str:
        """Форматирование словаря для вывода"""
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{' ' * indent}{key}:")
                lines.append(self.format_dict(value, indent + 2))
            elif isinstance(value, float):
                lines.append(f"{' ' * indent}{key}: {value:.4f}")
            elif isinstance(value, list):
                lines.append(f"{' ' * indent}{key}: {len(value)} элементов")
                if len(value) <= 5:
                    for item in value:
                        lines.append(f"{' ' * (indent + 2)}- {item}")
            else:
                lines.append(f"{' ' * indent}{key}: {value}")
        return "\n".join(lines)
    
    def show_configuration(self):
        """Отображение конфигурации нейросетей"""
        self.print_header("КОНФИГУРАЦИЯ НЕЙРОСЕТЕЙ")
        
        nn_config = self.config.get('neural_networks', {})
        
        # Информация о моделях
        print("\n📊 Модели:")
        models = nn_config.get('models', [])
        for i, model_config in enumerate(models, 1):
            print(f"\n  {i}. {model_config.get('name', 'Unknown')}")
            print(f"     Тип: {model_config.get('type', 'Unknown')}")
            print(f"     Включена: {model_config.get('enabled', True)}")
            
            # Параметры модели
            config_params = model_config.get('config', {})
            if config_params:
                print(f"     Параметры:")
                for param, value in config_params.items():
                    if param != 'api_key':  # Не показываем API ключи
                        if isinstance(value, float):
                            print(f"       - {param}: {value:.4f}")
                        else:
                            print(f"       - {param}: {value}")
        
        # Информация об ансамбле
        self.print_section("Ансамбль моделей")
        ensemble = nn_config.get('ensemble', {})
        print(f"  Метод: {ensemble.get('method', 'weighted_average')}")
        print(f"  Порог уверенности: {ensemble.get('confidence_threshold', 0.7)}")
        
        weights = ensemble.get('weights', {})
        if weights:
            print("  Веса моделей:")
            for model_name, weight in weights.items():
                print(f"    - {model_name}: {weight}")
        
        # Интервалы анализа
        self.print_section("Интервалы анализа")
        print(f"  Интервал анализа: {nn_config.get('analysis_interval', 180)} сек")
        print(f"  Интервал проверки сигналов: {nn_config.get('signal_check_interval', 180)} сек")
    
    def show_models_status(self):
        """Отображение статуса моделей"""
        self.print_header("СТАТУС МОДЕЛЕЙ")
        
        status = self.network_manager.get_status()
        
        print(f"\nВсего моделей: {status.get('total_models', 0)}")
        print(f"Обученных моделей: {status.get('trained_models', 0)}")
        print(f"Метод ансамбля: {status.get('ensemble_method', 'N/A')}")
        
        last_analysis = status.get('last_analysis_time')
        if last_analysis:
            print(f"Последний анализ: {last_analysis}")
        else:
            print("Последний анализ: не выполнялся")
        
        # Детальный статус каждой модели
        models_status = status.get('models_status', {})
        for model_name, model_status in models_status.items():
            self.print_section(f"Модель: {model_name}")
            print(f"  Обучена: {'✅ Да' if model_status.get('is_trained') else '❌ Нет'}")
            
            # Метрики производительности
            metrics = model_status.get('performance_metrics', {})
            if metrics:
                print("  Метрики производительности:")
                for metric, value in metrics.items():
                    if isinstance(value, float):
                        print(f"    - {metric}: {value:.4f}")
                    else:
                        print(f"    - {metric}: {value}")
            else:
                print("  Метрики производительности: недоступны")
            
            # Время последнего предсказания
            last_pred_time = model_status.get('last_prediction_time')
            if last_pred_time:
                print(f"  Последнее предсказание: {last_pred_time}")
            else:
                print("  Последнее предсказание: не выполнялось")
    
    def show_last_analysis(self):
        """Отображение последнего анализа"""
        self.print_header("ПОСЛЕДНИЙ АНАЛИЗ")
        
        last_analysis = self.network_manager.last_analysis
        
        if not last_analysis:
            print("\n❌ Анализ еще не выполнялся")
            return
        
        # Общая информация
        print(f"\nВремя анализа: {last_analysis.get('analysis_time', 'N/A')}")
        print(f"Проанализировано символов: {len(last_analysis.get('symbols_analyzed', []))}")
        print(f"Использовано моделей: {len(last_analysis.get('models_used', []))}")
        news_included = '✅ Да' if last_analysis.get('news_data_included') else '❌ Нет'
        print(f"Новостные данные включены: {news_included}")
        
        # Индивидуальные предсказания по моделям
        self.print_section("Индивидуальные предсказания по моделям")
        individual = last_analysis.get('individual_predictions', {})
        
        for model_name, predictions in individual.items():
            print(f"\n  Модель: {model_name}")
            print(f"    Проанализировано символов: {len(predictions)}")
            
            # Показываем первые несколько предсказаний
            for symbol, prediction in list(predictions.items())[:5]:
                signal = prediction.get('signal', 'N/A')
                confidence = prediction.get('confidence', 0.0)
                print(f"    {symbol}: {signal} (уверенность: {confidence:.4f})")
            
            if len(predictions) > 5:
                print(f"    ... и еще {len(predictions) - 5} символов")
        
        # Ансамблевые предсказания
        self.print_section("Ансамблевые предсказания")
        ensemble_preds = last_analysis.get('ensemble_predictions', {})
        
        if ensemble_preds:
            # Группировка по сигналам
            signals_count = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
            for symbol, pred in ensemble_preds.items():
                signal = pred.get('signal', 'HOLD')
                if signal in signals_count:
                    signals_count[signal] += 1
            
            print(f"\n  Распределение сигналов:")
            print(f"    BUY: {signals_count['BUY']}")
            print(f"    SELL: {signals_count['SELL']}")
            print(f"    HOLD: {signals_count['HOLD']}")
            
            # Показываем детали по первым символам
            print(f"\n  Детали по символам (первые 10):")
            for i, (symbol, pred) in enumerate(list(ensemble_preds.items())[:10], 1):
                signal = pred.get('signal', 'N/A')
                confidence = pred.get('confidence', 0.0)
                trend = pred.get('trend', 'N/A')
                method = pred.get('method', 'N/A')
                
                print(f"\n    {i}. {symbol}")
                print(f"       Сигнал: {signal}")
                print(f"       Уверенность: {confidence:.4f}")
                print(f"       Тренд: {trend}")
                print(f"       Метод: {method}")
                
                # Новостная информация
                news_summary = pred.get('news_summary')
                if news_summary:
                    print(f"       Новости: включены")
                
                # Распределение сигналов моделей
                signal_dist = pred.get('signal_distribution', {})
                if signal_dist:
                    print(f"       Распределение: {signal_dist}")
            
            if len(ensemble_preds) > 10:
                print(f"\n    ... и еще {len(ensemble_preds) - 10} символов")
        else:
            print("\n  Ансамблевые предсказания отсутствуют")
    
    async def show_feature_importance(self):
        """Отображение важности признаков"""
        self.print_header("ВАЖНОСТЬ ПРИЗНАКОВ")
        
        for model_name, model in self.network_manager.models.items():
            self.print_section(f"Модель: {model_name}")
            
            try:
                # Попытка получить важность признаков
                feature_importance = None
                
                # Прямой доступ к атрибуту (для XGBoost)
                if hasattr(model, 'feature_importance') and model.feature_importance:
                    feature_importance = model.feature_importance
                # Асинхронный метод (если доступен)
                elif hasattr(model, 'get_feature_importance'):
                    try:
                        feature_importance = await model.get_feature_importance()
                    except:
                        pass
                
                if feature_importance:
                    # Сортировка по важности
                    sorted_features = sorted(
                        feature_importance.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                    
                    print(f"\n  Топ-15 важных признаков:")
                    for i, (feature, importance) in enumerate(sorted_features[:15], 1):
                        print(f"    {i:2d}. {feature}: {importance:.6f}")
                    
                    if len(sorted_features) > 15:
                        print(f"\n    ... и еще {len(sorted_features) - 15} признаков")
                else:
                    print("  Важность признаков недоступна (модель не обучена)")
            except Exception as e:
                print(f"  Ошибка получения важности признаков: {e}")
    
    def show_saved_models(self):
        """Отображение информации о сохраненных моделях"""
        self.print_header("СОХРАНЕННЫЕ МОДЕЛИ")
        
        if not self.models_dir.exists():
            print("\n❌ Директория models не найдена")
            return
        
        model_files = list(self.models_dir.glob("*.pkl"))
        
        if not model_files:
            print("\n❌ Сохраненные модели не найдены")
            return
        
        print(f"\nНайдено файлов моделей: {len(model_files)}")
        
        for model_file in model_files:
            self.print_section(f"Файл: {model_file.name}")
            
            try:
                # Попытка получить информацию о файле
                file_size = model_file.stat().st_size
                file_time = datetime.fromtimestamp(model_file.stat().st_mtime)
                
                print(f"  Размер: {file_size / 1024:.2f} KB")
                print(f"  Дата изменения: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Попытка загрузить и получить информацию о модели
                try:
                    with open(model_file, 'rb') as f:
                        model_data = pickle.load(f)
                    
                    if hasattr(model_data, 'is_trained'):
                        print(f"  Обучена: {'✅ Да' if model_data.is_trained else '❌ Нет'}")
                    
                    if hasattr(model_data, 'performance_metrics'):
                        metrics = model_data.performance_metrics
                        if metrics:
                            print("  Метрики:")
                            for metric, value in list(metrics.items())[:3]:
                                if isinstance(value, float):
                                    print(f"    - {metric}: {value:.4f}")
                                else:
                                    print(f"    - {metric}: {value}")
                    
                    if hasattr(model_data, 'name'):
                        print(f"  Имя модели: {model_data.name}")
                        
                except Exception as e:
                    print(f"  ⚠️  Не удалось прочитать модель: {e}")
                    
            except Exception as e:
                print(f"  ⚠️  Ошибка получения информации о файле: {e}")
    
    def show_saved_signals(self):
        """Отображение сохраненных сигналов"""
        self.print_header("СОХРАНЕННЫЕ СИГНАЛЫ")
        
        signals_file = self.data_dir / "signals.json"
        
        if not signals_file.exists():
            print("\n❌ Файл signals.json не найден")
            return
        
        try:
            with open(signals_file, 'r', encoding='utf-8') as f:
                signals = json.load(f)
            
            if not signals:
                print("\n❌ Сигналы отсутствуют")
                return
            
            print(f"\nВсего сигналов: {len(signals)}")
            
            # Группировка по символам
            symbols_count = {}
            signals_by_symbol = {}
            for signal in signals:
                symbol = signal.get('symbol', 'Unknown')
                symbols_count[symbol] = symbols_count.get(symbol, 0) + 1
                if symbol not in signals_by_symbol:
                    signals_by_symbol[symbol] = []
                signals_by_symbol[symbol].append(signal)
            
            print(f"Уникальных символов: {len(symbols_count)}")
            
            # Группировка по сигналам
            signal_types = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
            for signal in signals:
                sig_type = signal.get('signal', 'HOLD')
                if sig_type in signal_types:
                    signal_types[sig_type] += 1
            
            print(f"\nРаспределение сигналов:")
            print(f"  BUY: {signal_types['BUY']}")
            print(f"  SELL: {signal_types['SELL']}")
            print(f"  HOLD: {signal_types['HOLD']}")
            
            # Группировка по источникам
            sources_count = {}
            for signal in signals:
                source = signal.get('source', 'Unknown')
                sources_count[source] = sources_count.get(source, 0) + 1
            
            print(f"\nПо источникам:")
            for source, count in sources_count.items():
                print(f"  {source}: {count}")
            
            # Последние сигналы
            self.print_section("Последние сигналы (первые 10)")
            for i, signal in enumerate(signals[:10], 1):
                print(f"\n  {i}. {signal.get('symbol', 'N/A')}")
                print(f"     Сигнал: {signal.get('signal', 'N/A')}")
                print(f"     Уверенность: {signal.get('confidence', 0.0):.4f}")
                print(f"     Время: {signal.get('time', 'N/A')}")
                print(f"     Источник: {signal.get('source', 'N/A')}")
                reasoning = signal.get('reasoning', '')
                if reasoning:
                    print(f"     Обоснование: {reasoning[:100]}...")
            
            if len(signals) > 10:
                print(f"\n  ... и еще {len(signals) - 10} сигналов")
                
        except Exception as e:
            print(f"\n❌ Ошибка чтения файла signals.json: {e}")
    
    async def show_analysis_data(self):
        """Отображение структуры данных для анализа"""
        self.print_header("ДАННЫЕ ДЛЯ АНАЛИЗА (СОЗДАНИЕ СИГНАЛОВ)")
        
        try:
            # Получение последних данных
            market_data = await self.data_provider.get_latest_data()
            
            # Структура данных для анализа
            self.print_section("Структура входных данных")
            print("  Данные передаются в формате:")
            print("    data = {")
            print("      'historical': {symbol: pd.DataFrame},  # Исторические данные по символам")
            print("      'realtime': {symbol: dict},           # Данные в реальном времени")
            print("      'news': {symbol: dict},               # Новостные данные")
            print("      'last_update': datetime               # Время последнего обновления")
            print("    }")
            
            # Исторические данные
            historical = market_data.get('historical', {})
            if isinstance(historical, dict):
                print(f"\n  Исторические данные: {len(historical)} символов")
                
                # Показываем пример для первого символа
                if historical:
                    first_symbol = list(historical.keys())[0]
                    symbol_data = historical[first_symbol]
                    
                    if isinstance(symbol_data, pd.DataFrame) and not symbol_data.empty:
                        self.print_section(f"Пример данных для {first_symbol}")
                        print(f"  Размер данных: {len(symbol_data)} строк × {len(symbol_data.columns)} столбцов")
                        if len(symbol_data) > 0:
                            print(f"  Период: {symbol_data.index[0]} - {symbol_data.index[-1]}")
                        
                        print("\n  Столбцы базовых данных:")
                        base_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                        for col in base_columns:
                            if col in symbol_data.columns:
                                values = symbol_data[col]
                                print(f"    - {col}:")
                                print(f"      Минимум: {values.min():.2f}")
                                print(f"      Максимум: {values.max():.2f}")
                                print(f"      Среднее: {values.mean():.2f}")
                                print(f"      Последнее значение: {values.iloc[-1]:.2f}")
                        
                        print("\n  Последние 5 строк данных:")
                        print(symbol_data.tail(5).to_string())
                        
                        # Информация о признаках, которые будут созданы
                        self.print_section("Признаки, создаваемые при анализе")
                        print("  Технические индикаторы:")
                        print("    - SMA_5, SMA_10, SMA_20, SMA_50 (скользящие средние)")
                        print("    - EMA_5, EMA_10, EMA_20, EMA_50 (экспоненциальные средние)")
                        print("    - RSI (индекс относительной силы)")
                        print("    - MACD, MACD_Signal (индикатор схождения-расхождения)")
                        print("    - BB_Upper, BB_Middle, BB_Lower, BB_Width (полосы Боллинджера)")
                        print("    - Volatility (волатильность)")
                        print("    - Volume_SMA, Volume_Ratio (объемные индикаторы)")
                        print("    - Price_Change, Price_Change_5, Price_Change_10 (изменения цен)")
                        print("    - Open_norm, High_norm, Low_norm, Close_norm (нормализованные цены)")
                        print("    - Hour, DayOfWeek, Month, Quarter (временные признаки)")
                        
                        print("\n  Всего признаков создается: ~30+")
            
            # Новостные данные
            news_data = market_data.get('news', {})
            if news_data:
                self.print_section("Новостные данные")
                print(f"  Новости загружены для {len(news_data)} символов")
                
                # Пример новостных данных
                if news_data:
                    first_symbol = list(news_data.keys())[0]
                    symbol_news = news_data[first_symbol]
                    
                    print(f"\n  Пример новостных данных для {first_symbol}:")
                    if isinstance(symbol_news, dict):
                        print(f"    - Всего новостей: {symbol_news.get('total_news', 0)}")
                        print(f"    - Положительных: {symbol_news.get('positive_news', 0)}")
                        print(f"    - Отрицательных: {symbol_news.get('negative_news', 0)}")
                        print(f"    - Нейтральных: {symbol_news.get('neutral_news', 0)}")
                        print(f"    - Средняя тональность: {symbol_news.get('avg_sentiment', 0.0):.4f}")
                        print(f"    - Уверенность тональности: {symbol_news.get('sentiment_confidence', 0.0):.4f}")
                        print(f"    - Тренд: {symbol_news.get('recent_trend', 'neutral')}")
            
            # Данные в реальном времени
            realtime = market_data.get('realtime', {})
            if realtime:
                self.print_section("Данные в реальном времени")
                print(f"  Данные для {len(realtime)} символов")
                
                if realtime:
                    first_symbol = list(realtime.keys())[0]
                    symbol_realtime = realtime[first_symbol]
                    
                    print(f"\n  Пример данных для {first_symbol}:")
                    if isinstance(symbol_realtime, dict):
                        for key, value in symbol_realtime.items():
                            if isinstance(value, float):
                                print(f"    - {key}: {value:.2f}")
                            else:
                                print(f"    - {key}: {value}")
            
            # Информация о передаче данных в модели
            self.print_section("Передача данных в модели")
            print("  При анализе данные передаются в каждый символ отдельно:")
            print("    for symbol, symbol_data in data['historical'].items():")
            print("      prediction = await model.predict(")
            print("        symbol_data,                    # DataFrame с историческими данными")
            print("        portfolio_manager=...,          # Менеджер портфеля (опционально)")
            print("        symbol=symbol,                  # Символ для анализа")
            print("        news_data=news_data[symbol]    # Новостные данные для символа")
            print("      )")
            
        except Exception as e:
            print(f"\n❌ Ошибка получения данных для анализа: {e}")
            import traceback
            traceback.print_exc()
    
    async def show_training_data(self):
        """Отображение структуры данных для обучения"""
        self.print_header("ДАННЫЕ ДЛЯ ОБУЧЕНИЯ")
        
        try:
            # Получение исторических данных для обучения
            historical_data = await self.data_provider.get_latest_data()
            
            self.print_section("Структура входных данных для обучения")
            print("  Данные передаются в формате:")
            print("    data = pd.DataFrame  # Объединенные данные всех символов")
            print("    target = 'Close'      # Целевая переменная")
            print("    news_data = {symbol: dict}  # Новостные данные (опционально)")
            
            # Получение примера данных для обучения
            historical = historical_data.get('historical', {})
            if isinstance(historical, dict) and historical:
                # Объединение данных всех символов (как при обучении)
                combined_data = []
                for symbol, symbol_data in historical.items():
                    if isinstance(symbol_data, pd.DataFrame) and not symbol_data.empty:
                        symbol_data_copy = symbol_data.copy()
                        symbol_data_copy['Symbol'] = symbol  # Добавляем метку символа
                        combined_data.append(symbol_data_copy)
                
                if combined_data:
                    combined_df = pd.concat(combined_data, ignore_index=True)
                    
                    self.print_section("Пример объединенных данных для обучения")
                    print(f"  Общий размер: {len(combined_df)} строк × {len(combined_df.columns)} столбцов")
                    print(f"  Символов в данных: {combined_df['Symbol'].nunique() if 'Symbol' in combined_df.columns else 'N/A'}")
                    
                    if 'Symbol' in combined_df.columns:
                        print("\n  Распределение по символам:")
                        symbol_counts = combined_df['Symbol'].value_counts()
                        for symbol, count in symbol_counts.head(10).items():
                            print(f"    - {symbol}: {count} строк")
                        if len(symbol_counts) > 10:
                            print(f"    ... и еще {len(symbol_counts) - 10} символов")
                    
                    # Столбцы базовых данных
                    base_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                    available_columns = [col for col in base_columns if col in combined_df.columns]
                    
                    if available_columns:
                        print("\n  Статистика по базовым данным:")
                        for col in available_columns:
                            values = combined_df[col]
                            print(f"    {col}:")
                            print(f"      Минимум: {values.min():.2f}")
                            print(f"      Максимум: {values.max():.2f}")
                            print(f"      Среднее: {values.mean():.2f}")
                            print(f"      Медиана: {values.median():.2f}")
                            print(f"      Стандартное отклонение: {values.std():.2f}")
                            print(f"      Пропусков: {values.isna().sum()}")
                    
                    # Информация о подготовке признаков
                    self.print_section("Подготовка признаков при обучении")
                    print("  Процесс подготовки:")
                    print("    1. Добавление технических индикаторов (~20 признаков)")
                    print("    2. Добавление временных признаков (4 признака)")
                    print("    3. Добавление портфельных признаков (если доступны)")
                    print("    4. Добавление новостных признаков (если доступны)")
                    print("    5. Нормализация данных")
                    
                    print("\n  Итоговое количество признаков: ~30-50 в зависимости от конфигурации")
                    
                    # Информация о создании целевых меток
                    self.print_section("Создание целевых меток")
                    print("  Для XGBoost модели:")
                    print("    - Рассчитывается будущее изменение цены:")
                    print("      future_return = price[t+1] / price[t] - 1")
                    print("    - Создаются метки классов:")
                    print("      0 = SELL  (future_return <= -0.05, падение >5%)")
                    print("      1 = HOLD  (-0.05 < future_return < 0.05)")
                    print("      2 = BUY   (future_return >= 0.05, рост >5%)")
                    
                    print("\n  Пример распределения меток (на основе порогов):")
                    print("    SELL: при падении цены на 5% и более")
                    print("    HOLD: при изменении цены от -5% до +5%")
                    print("    BUY:  при росте цены на 5% и более")
                    
                    # Пример данных после подготовки признаков
                    if len(combined_df) > 0:
                        self.print_section("Пример первых строк данных для обучения")
                        print(combined_df.head(3).to_string())
            
            # Новостные данные для обучения
            news_data = historical_data.get('news', {})
            if news_data:
                self.print_section("Новостные данные для обучения")
                print(f"  Новости доступны для {len(news_data)} символов")
                
                news_config = self.config.get('data', {}).get('news', {})
                if news_config.get('include_news_in_training', False):
                    training_days = news_config.get('training_news_days', 180)
                    print(f"  Используются новости за последние {training_days} дней")
                else:
                    print("  Новостные данные в обучении отключены")
            
            # Информация о процессе обучения
            self.print_section("Процесс обучения")
            print("  1. Загрузка исторических данных (обычно 1 год)")
            print("  2. Объединение данных всех символов")
            print("  3. Подготовка признаков (технические индикаторы, новости и т.д.)")
            print("  4. Создание целевых меток")
            print("  5. Разделение на обучающую (80%) и тестовую (20%) выборки")
            print("  6. Обучение модели на обучающей выборке")
            print("  7. Оценка на тестовой выборке")
            print("  8. Сохранение метрик производительности")
            
        except Exception as e:
            print(f"\n❌ Ошибка получения данных для обучения: {e}")
            import traceback
            traceback.print_exc()
    
    def show_summary(self):
        """Отображение краткой сводки"""
        self.print_header("КРАТКАЯ СВОДКА", width=60)
        
        status = self.network_manager.get_status()
        
        print(f"\nМоделей всего: {status.get('total_models', 0)}")
        print(f"Моделей обучено: {status.get('trained_models', 0)}")
        
        last_analysis = self.network_manager.last_analysis
        if last_analysis:
            print(f"Последний анализ: {last_analysis.get('analysis_time', 'N/A')}")
            print(f"Символов проанализировано: {len(last_analysis.get('symbols_analyzed', []))}")
        else:
            print("Последний анализ: не выполнялся")
        
        # Информация о файлах
        model_files = list(self.models_dir.glob("*.pkl")) if self.models_dir.exists() else []
        print(f"Сохраненных моделей: {len(model_files)}")
        
        signals_file = self.data_dir / "signals.json"
        if signals_file.exists():
            try:
                with open(signals_file, 'r', encoding='utf-8') as f:
                    signals = json.load(f)
                print(f"Сохраненных сигналов: {len(signals)}")
            except:
                print("Сохраненных сигналов: недоступно")
        else:
            print("Сохраненных сигналов: 0")
    
    async def run_single_analysis(self):
        """Выполнение разового анализа и вывод результатов"""
        self.print_header("РАЗОВЫЙ АНАЛИЗ")
        
        try:
            print("\n🔄 Загрузка данных...")
            # Получение последних данных
            market_data = await self.data_provider.get_latest_data()
            
            # Получение новостных данных
            news_data = market_data.get('news', {})
            
            print(f"✅ Данные загружены:")
            historical = market_data.get('historical', {})
            if isinstance(historical, dict):
                print(f"   - Исторические данные: {len(historical)} символов")
            print(f"   - Новостные данные: {len(news_data)} символов")
            
            print("\n🔄 Выполнение анализа нейросетями...")
            
            # Инициализация портфельного менеджера (если нужен)
            from src.portfolio.portfolio_manager import PortfolioManager
            portfolio_manager = None
            try:
                portfolio_config = self.config.get('portfolio', {})
                portfolio_manager = PortfolioManager(portfolio_config)
                await portfolio_manager.initialize()
            except Exception as e:
                logger.debug(f"Портфельный менеджер недоступен: {e}")
            
            # Выполнение анализа
            analysis_results = await self.network_manager.analyze(
                market_data,
                portfolio_manager=portfolio_manager,
                news_data=news_data
            )
            
            print("✅ Анализ завершен!\n")
            
            # Вывод результатов
            self.print_header("РЕЗУЛЬТАТЫ АНАЛИЗА")
            
            # Общая информация
            self.print_section("Общая информация")
            print(f"  Время анализа: {analysis_results.get('analysis_time', 'N/A')}")
            print(f"  Проанализировано символов: {len(analysis_results.get('symbols_analyzed', []))}")
            print(f"  Использовано моделей: {len(analysis_results.get('models_used', []))}")
            news_included = '✅ Да' if analysis_results.get('news_data_included') else '❌ Нет'
            print(f"  Новостные данные включены: {news_included}")
            
            # Индивидуальные предсказания по моделям
            self.print_section("Предсказания по моделям")
            individual = analysis_results.get('individual_predictions', {})
            
            for model_name, predictions in individual.items():
                print(f"\n  📊 Модель: {model_name}")
                print(f"     Проанализировано символов: {len(predictions)}")
                
                # Показываем первые несколько предсказаний
                for symbol, prediction in list(predictions.items())[:5]:
                    signal = prediction.get('signal', 'N/A')
                    confidence = prediction.get('confidence', 0.0)
                    print(f"     {symbol}: {signal} (уверенность: {confidence:.4f})")
                
                if len(predictions) > 5:
                    print(f"     ... и еще {len(predictions) - 5} символов")
            
            # Ансамблевые предсказания
            self.print_section("Ансамблевые предсказания")
            ensemble_preds = analysis_results.get('ensemble_predictions', {})
            
            if ensemble_preds:
                # Группировка по сигналам
                signals_count = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
                for symbol, pred in ensemble_preds.items():
                    signal = pred.get('signal', 'HOLD')
                    if signal in signals_count:
                        signals_count[signal] += 1
                
                print(f"\n  📈 Распределение сигналов:")
                print(f"     BUY:  {signals_count['BUY']}")
                print(f"     SELL: {signals_count['SELL']}")
                print(f"     HOLD: {signals_count['HOLD']}")
                
                # Детали по всем символам
                print(f"\n  📋 Детали по символам:")
                for i, (symbol, pred) in enumerate(ensemble_preds.items(), 1):
                    signal = pred.get('signal', 'N/A')
                    confidence = pred.get('confidence', 0.0)
                    trend = pred.get('trend', 'N/A')
                    method = pred.get('method', 'N/A')
                    
                    # Эмодзи для сигналов
                    signal_emoji = {
                        'BUY': '🟢',
                        'SELL': '🔴',
                        'HOLD': '🟡'
                    }.get(signal, '⚪')
                    
                    print(f"\n     {i}. {symbol} {signal_emoji}")
                    print(f"        Сигнал: {signal}")
                    print(f"        Уверенность: {confidence:.4f}")
                    print(f"        Тренд: {trend}")
                    print(f"        Метод: {method}")
                    
                    # Распределение сигналов моделей
                    signal_dist = pred.get('signal_distribution', {})
                    if signal_dist:
                        print(f"        Распределение: BUY={signal_dist.get('BUY', 0):.2f}, "
                              f"SELL={signal_dist.get('SELL', 0):.2f}, "
                              f"HOLD={signal_dist.get('HOLD', 0):.2f}")
                    
                    # Новостная информация
                    news_summary = pred.get('news_summary')
                    if news_summary:
                        print(f"        📰 Новости: включены")
                        if isinstance(news_summary, dict):
                            sentiment = news_summary.get('avg_sentiment', 0.0)
                            print(f"           Тональность: {sentiment:.4f}")
            
            # Рекомендации
            self.print_section("Рекомендации")
            # Получаем порог уверенности из конфигурации
            nn_config = self.config.get('neural_networks', {})
            ensemble_config = nn_config.get('ensemble', {})
            confidence_threshold = ensemble_config.get('confidence_threshold', 0.7)
            
            buy_signals = [(s, p) for s, p in ensemble_preds.items() 
                          if p.get('signal') == 'BUY' and p.get('confidence', 0) >= confidence_threshold]
            sell_signals = [(s, p) for s, p in ensemble_preds.items() 
                           if p.get('signal') == 'SELL' and p.get('confidence', 0) >= confidence_threshold]
            
            print(f"\n  Порог уверенности для рекомендаций: {confidence_threshold}")
            
            if buy_signals:
                print("\n  🟢 Рекомендуется к покупке (высокая уверенность):")
                for symbol, pred in buy_signals:
                    confidence = pred.get('confidence', 0.0)
                    print(f"     - {symbol}: уверенность {confidence:.4f}")
            
            if sell_signals:
                print("\n  🔴 Рекомендуется к продаже (высокая уверенность):")
                for symbol, pred in sell_signals:
                    confidence = pred.get('confidence', 0.0)
                    print(f"     - {symbol}: уверенность {confidence:.4f}")
            
            if not buy_signals and not sell_signals:
                print(f"\n  ⚠️  Нет сигналов с высокой уверенностью (>={confidence_threshold})")
                print("     Рекомендуется удержание позиций")
            
            print("\n" + "=" * 80)
            print("  АНАЛИЗ ЗАВЕРШЕН")
            print("=" * 80 + "\n")
            
        except Exception as e:
            print(f"\n❌ Ошибка выполнения анализа: {e}")
            import traceback
            traceback.print_exc()
    
    async def generate_report(self):
        """Генерация полного отчета"""
        try:
            await self.initialize()
            
            # Краткая сводка
            self.show_summary()
            
            # Конфигурация
            self.show_configuration()
            
            # Статус моделей
            self.show_models_status()
            
            # Последний анализ
            self.show_last_analysis()
            
            # Важность признаков
            await self.show_feature_importance()
            
            # Сохраненные модели
            self.show_saved_models()
            
            # Сохраненные сигналы
            self.show_saved_signals()
            
            # Данные для анализа
            await self.show_analysis_data()
            
            # Данные для обучения
            await self.show_training_data()
            
            print("\n" + "=" * 80)
            print("  ОТЧЕТ ЗАВЕРШЕН")
            print("=" * 80 + "\n")
            
        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Отображение информации об анализе нейросетей')
    parser.add_argument(
        '--config',
        type=str,
        default='config/main.yaml',
        help='Путь к конфигурационному файлу'
    )
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Выполнить разовый анализ и показать результаты'
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Показать только отчет без анализа'
    )
    
    args = parser.parse_args()
    
    reporter = NeuralAnalysisReporter(args.config)
    
    if args.analyze:
        # Выполнить разовый анализ
        await reporter.initialize()
        await reporter.run_single_analysis()
    elif args.report_only:
        # Только отчет без анализа
        await reporter.generate_report()
    else:
        # По умолчанию: отчет + разовый анализ
        await reporter.initialize()
        await reporter.run_single_analysis()
        print("\n" + "=" * 80)
        print("  ПОКАЗАТЬ ПОЛНЫЙ ОТЧЕТ? (да/нет)")
        print("=" * 80)
        try:
            response = input("\nВведите 'да' для полного отчета или Enter для выхода: ").strip().lower()
            if response in ['да', 'yes', 'y', 'д']:
                await reporter.generate_report()
        except (KeyboardInterrupt, EOFError):
            print("\n\nВыход...")


if __name__ == "__main__":
    asyncio.run(main())

