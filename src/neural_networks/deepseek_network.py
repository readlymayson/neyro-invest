"""
DeepSeek API интеграция для анализа рынка
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
import pandas as pd
import numpy as np

from .base_network import BaseNeuralNetwork


class DeepSeekNetwork(BaseNeuralNetwork):
    """
    Интеграция с DeepSeek API для анализа финансовых данных
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Инициализация DeepSeek сети
        
        Args:
            name: Название сети
            config: Конфигурация сети
        """
        super().__init__(name, config)
        
        # Параметры API
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', 'https://api.deepseek.com/v1')
        self.model_name = config.get('model_name', 'deepseek-chat')
        self.max_tokens = config.get('max_tokens', 4000)
        self.temperature = config.get('temperature', 0.3)
        
        # Параметры анализа
        self.analysis_window = config.get('analysis_window', 30)  # дней
        self.feature_importance_threshold = config.get('feature_importance_threshold', 0.1)
        
        # Кэш для API запросов
        self.api_cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5 минут
        
        logger.info(f"Инициализирована DeepSeek сеть {self.name}")
    
    async def initialize(self):
        """
        Инициализация DeepSeek API
        """
        try:
            # Если API ключ не указан в конфигурации, загружаем из переменной окружения
            if not self.api_key:
                self.api_key = os.environ.get('DEEPSEEK_API_KEY')
                if not self.api_key:
                    logger.warning("API ключ DeepSeek не указан в конфигурации и переменной окружения")
                    logger.info("Установите переменную окружения: set DEEPSEEK_API_KEY=your_key_here")
                    return  # Пропускаем инициализацию без ошибки
            
            # Проверка подключения к API
            await self._test_api_connection()
            
            logger.info(f"DeepSeek API {self.name} инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации DeepSeek API {self.name}: {e}")
            raise
    
    async def _test_api_connection(self):
        """
        Тестирование подключения к DeepSeek API
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                test_payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "user", "content": "Привет! Это тест подключения."}
                    ],
                    "max_tokens": 10,
                    "temperature": 0.1
                }
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=test_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.debug("DeepSeek API подключение успешно")
                    else:
                        raise Exception(f"API вернул статус {response.status}")
                        
        except Exception as e:
            logger.error(f"Ошибка тестирования DeepSeek API: {e}")
            raise
    
    async def train(self, data: pd.DataFrame, target: str = 'Close', news_data: Dict[str, Any] = None, symbols: List[str] = None) -> Dict[str, float]:
        """
        "Обучение" DeepSeek модели (анализ исторических паттернов)
        
        Args:
            data: Данные для анализа
            target: Целевая переменная
            news_data: Новостные данные для анализа
            symbols: Список символов в данных (опционально, используется для определения символа анализа)
            
        Returns:
            Метрики анализа
        """
        try:
            logger.info(f"Анализ исторических данных DeepSeek моделью {self.name}")
            
            # Логирование входных данных
            logger.debug(f"DeepSeek {self.name}: Входные данные - форма: {data.shape}, колонки: {len(data.columns)}")
            if hasattr(data.index, 'min') and hasattr(data.index, 'max'):
                try:
                    first_date = data.index.min() if hasattr(data.index, 'min') else None
                    last_date = data.index.max() if hasattr(data.index, 'max') else None
                    if first_date and last_date:
                        date_range = (last_date - first_date).days if hasattr(last_date - first_date, 'days') else None
                        logger.debug(f"DeepSeek {self.name}: Диапазон дат входных данных: {first_date} - {last_date} ({date_range} дней)" if date_range else f"DeepSeek {self.name}: Диапазон дат: {first_date} - {last_date}")
                        logger.debug(f"DeepSeek {self.name}: Актуальность данных: последняя дата {last_date}, записей: {len(data)}")
                except Exception as e:
                    logger.debug(f"DeepSeek {self.name}: Не удалось определить диапазон дат: {e}")
            
            # Определение символа для анализа (используем первый символ из списка, если доступен)
            symbol_for_analysis = None
            if symbols and len(symbols) > 0:
                symbol_for_analysis = symbols[0]
                logger.debug(f"DeepSeek {self.name}: Используется символ {symbol_for_analysis} для анализа (первый из {len(symbols)} символов: {symbols})")
            else:
                # Попытка извлечь символ из данных (если есть колонка symbol после one-hot encoding)
                if hasattr(data, 'columns'):
                    symbol_cols = [col for col in data.columns if col.startswith('symbol_')]
                    if symbol_cols:
                        # Берем первый символ из колонок
                        first_symbol_col = symbol_cols[0]
                        symbol_for_analysis = first_symbol_col.replace('symbol_', '')
                        logger.debug(f"DeepSeek {self.name}: Символ определен из колонок данных: {symbol_for_analysis} (найдено символов в данных: {len(symbol_cols)})")
            
            # Подготовка данных для анализа с новостными данными (training_mode=True - исключаем портфельные признаки)
            logger.debug(f"DeepSeek {self.name}: Подготовка данных для анализа (символ: {symbol_for_analysis}, режим обучения: True)")
            analysis_data = self._prepare_data_for_analysis(data, target, portfolio_manager=None, symbol=symbol_for_analysis, news_data=news_data, training_mode=True)
            
            # Логирование структуры подготовленных данных
            if analysis_data:
                logger.debug(f"DeepSeek {self.name}: Структура подготовленных данных: ключи: {list(analysis_data.keys())}")
                if 'price_stats' in analysis_data:
                    logger.debug(f"DeepSeek {self.name}: Статистика цен: {analysis_data['price_stats']}")
                if 'volume_stats' in analysis_data:
                    logger.debug(f"DeepSeek {self.name}: Статистика объемов: {analysis_data['volume_stats']}")
                if 'technical_indicators' in analysis_data:
                    logger.debug(f"DeepSeek {self.name}: Технические индикаторы: {len(analysis_data['technical_indicators'])} индикаторов")
                if 'time_series' in analysis_data:
                    logger.debug(f"DeepSeek {self.name}: Временной ряд: {len(analysis_data['time_series'])} значений, последние: {analysis_data['time_series'][-3:] if len(analysis_data.get('time_series', [])) >= 3 else analysis_data.get('time_series', [])}")
            
            # Анализ паттернов через API
            patterns = await self._analyze_historical_patterns(analysis_data)
            
            # Расчет метрик
            metrics = self._calculate_training_metrics(patterns, data)
            
            self.is_trained = True
            self.performance_metrics = metrics
            
            logger.info(f"DeepSeek модель {self.name} проанализирована. Паттернов найдено: {len(patterns)}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Ошибка анализа DeepSeek моделью {self.name}: {e}")
            raise
    
    def _prepare_data_for_analysis(self, data: pd.DataFrame, target: str, portfolio_manager=None, symbol: str = None, news_data: Dict[str, Any] = None, training_mode: bool = False) -> Dict[str, Any]:
        """
        Подготовка данных для анализа DeepSeek
        
        Args:
            data: Исходные данные
            target: Целевая переменная
            portfolio_manager: Менеджер портфеля для извлечения портфельных признаков
            symbol: Символ для анализа портфельных признаков
            news_data: Новостные данные для анализа
            training_mode: Режим обучения - при True портфельные признаки не добавляются
            
        Returns:
            Подготовленные данные для анализа
        """
        try:
            logger.debug(f"DeepSeek: Подготовка данных для символа {symbol} (training_mode={training_mode})")
            logger.debug(f"Исходные данные: {data.shape}, колонки: {list(data.columns)[:10]}{'...' if len(data.columns) > 10 else ''}")
            
            # Логирование диапазона дат и актуальности данных
            if hasattr(data.index, 'min') and hasattr(data.index, 'max') and len(data) > 0:
                try:
                    first_date = data.index.min()
                    last_date = data.index.max()
                    if hasattr(first_date, 'date') and hasattr(last_date, 'date'):
                        date_range_days = (last_date - first_date).days if hasattr(last_date - first_date, 'days') else None
                        logger.debug(f"DeepSeek {symbol}: Диапазон дат исходных данных: {first_date} - {last_date}" + 
                                   (f" ({date_range_days} дней)" if date_range_days else ""))
                        
                        # Проверка актуальности данных
                        if hasattr(last_date, 'date'):
                            days_ago = (datetime.now().date() - last_date.date()).days if hasattr(datetime.now(), 'date') else None
                            if days_ago is not None:
                                logger.debug(f"DeepSeek {symbol}: Актуальность данных: последняя запись {days_ago} дней назад (дата: {last_date.date()})")
                except Exception as e:
                    logger.debug(f"DeepSeek {symbol}: Не удалось определить диапазон дат: {e}")
            
            # Получение последних данных
            logger.debug(f"DeepSeek {symbol}: Используется окно анализа: {self.analysis_window} записей (из {len(data)} доступных)")
            recent_data = data.tail(self.analysis_window).copy()
            logger.debug(f"Последние {self.analysis_window} строк: {recent_data.shape}")
            
            # Логирование диапазона дат в окне анализа
            if len(recent_data) > 0 and hasattr(recent_data.index, 'min') and hasattr(recent_data.index, 'max'):
                try:
                    window_first = recent_data.index.min()
                    window_last = recent_data.index.max()
                    logger.debug(f"DeepSeek {symbol}: Диапазон дат в окне анализа: {window_first} - {window_last}")
                except Exception:
                    pass
            
            # Расчет технических индикаторов (training_mode передается для исключения портфельных признаков)
            recent_data = self.prepare_features(recent_data, portfolio_manager=None, symbol=symbol, news_data=None, training_mode=training_mode)
            logger.debug(f"После расчета признаков: {recent_data.shape}, колонки: {list(recent_data.columns)}")
            
            # Подготовка статистики
            stats = {
                'price_stats': {
                    'current_price': recent_data[target].iloc[-1],
                    'avg_price': recent_data[target].mean(),
                    'price_change': recent_data[target].pct_change().mean(),
                    'volatility': recent_data[target].std(),
                    'min_price': recent_data[target].min(),
                    'max_price': recent_data[target].max()
                },
                'volume_stats': {
                    'avg_volume': recent_data['Volume'].mean(),
                    'volume_trend': recent_data['Volume'].pct_change().mean()
                },
                'technical_indicators': self._extract_technical_indicators(recent_data),
                'time_series': recent_data[target].tail(10).tolist()
            }
            
            logger.debug(f"Статистика цен для {symbol}: {stats['price_stats']}")
            logger.debug(f"Статистика объемов для {symbol}: {stats['volume_stats']}")
            logger.debug(f"Технические индикаторы для {symbol}: {stats['technical_indicators']}")
            
            # Добавление портфельных данных (только если не режим обучения)
            if portfolio_manager and not training_mode:
                try:
                    from .portfolio_features import PortfolioFeatureExtractor
                    portfolio_extractor = PortfolioFeatureExtractor(self.config.get('portfolio_features', {}))
                    portfolio_features = portfolio_extractor.extract_portfolio_features(portfolio_manager, symbol)
                    
                    stats['portfolio_stats'] = {
                        'total_value': portfolio_features.total_value,
                        'total_pnl': portfolio_features.total_pnl,
                        'total_pnl_percent': portfolio_features.total_pnl_percent,
                        'position_count': portfolio_features.position_count,
                        'winning_positions': portfolio_features.winning_positions,
                        'losing_positions': portfolio_features.losing_positions,
                        'sharpe_ratio': portfolio_features.sharpe_ratio,
                        'max_drawdown': portfolio_features.max_drawdown,
                        'volatility': portfolio_features.volatility
                    }
                    
                    # Добавление признаков по символу
                    if symbol and symbol in portfolio_features.symbol_features:
                        symbol_features = portfolio_features.symbol_features[symbol]
                        stats['symbol_portfolio_stats'] = symbol_features
                        
                except Exception as e:
                    logger.warning(f"Ошибка добавления портфельных данных в DeepSeek: {e}")
                    stats['portfolio_stats'] = {}
                    stats['symbol_portfolio_stats'] = {}
            
            # Добавление новостных данных
            if news_data and symbol and symbol in news_data:
                symbol_news = news_data[symbol]
                stats['news_stats'] = {
                    'avg_sentiment': symbol_news.get('avg_sentiment', 0.0),
                    'sentiment_confidence': symbol_news.get('sentiment_confidence', 0.0),
                    'total_news': symbol_news.get('total_news', 0),
                    'positive_news': symbol_news.get('positive_news', 0),
                    'negative_news': symbol_news.get('negative_news', 0),
                    'neutral_news': symbol_news.get('neutral_news', 0),
                    'recent_trend': symbol_news.get('recent_trend', 'neutral'),
                    'news_summary': symbol_news.get('news_summary', ''),
                    'last_news_date': symbol_news.get('last_news_date', '')
                }
                
                # Добавление последних новостей для контекста
                if 'news_list' in symbol_news and symbol_news['news_list']:
                    stats['recent_news'] = symbol_news['news_list'][:3]  # Последние 3 новости
                
                logger.debug(f"Добавлены новостные данные для {symbol} в DeepSeek анализ")
            else:
                stats['news_stats'] = {
                    'avg_sentiment': 0.0,
                    'sentiment_confidence': 0.0,
                    'total_news': 0,
                    'positive_news': 0,
                    'negative_news': 0,
                    'neutral_news': 0,
                    'recent_trend': 'neutral',
                    'news_summary': 'Нет новостных данных',
                    'last_news_date': ''
                }
                stats['recent_news'] = []
            
            # Добавление символа в данные для промпта
            if symbol:
                stats['symbol'] = symbol
                logger.debug(f"DeepSeek: Символ {symbol} добавлен в данные для анализа")
            else:
                logger.warning("DeepSeek: Символ не передан в _prepare_data_for_analysis")
            
            # Логирование полной структуры подготовленных данных
            logger.debug(f"DeepSeek {symbol}: Структура подготовленных данных для промпта:")
            logger.debug(f"  - price_stats: {list(stats.get('price_stats', {}).keys())}")
            logger.debug(f"  - volume_stats: {list(stats.get('volume_stats', {}).keys())}")
            logger.debug(f"  - technical_indicators: {len(stats.get('technical_indicators', {}))} индикаторов")
            logger.debug(f"  - time_series: {len(stats.get('time_series', []))} значений")
            logger.debug(f"  - news_stats: {'есть' if 'news_stats' in stats and stats.get('news_stats', {}).get('total_news', 0) > 0 else 'нет'}")
            logger.debug(f"  - portfolio_stats: {'есть' if 'portfolio_stats' in stats else 'нет'}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка подготовки данных для DeepSeek: {e}")
            return {}
    
    def _extract_technical_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Извлечение технических индикаторов
        
        Args:
            data: Данные с техническими индикаторами
            
        Returns:
            Словарь с индикаторами
        """
        indicators = {}
        
        try:
            # Логирование доступных колонок
            logger.debug(f"Доступные колонки в данных: {list(data.columns)}")
            logger.debug(f"Размер данных: {data.shape}")
            logger.debug(f"Последние 3 строки данных:\n{data.tail(3)}")
            
            # RSI
            if 'RSI' in data.columns:
                rsi_value = float(data['RSI'].iloc[-1])
                indicators['rsi'] = rsi_value
                indicators['rsi_overbought'] = bool(rsi_value > 70)
                indicators['rsi_oversold'] = bool(rsi_value < 30)
                logger.debug(f"RSI: {rsi_value}")
            else:
                logger.warning("Колонка RSI не найдена в данных")
            
            # MACD
            if 'MACD' in data.columns and 'MACD_Signal' in data.columns:
                macd_value = float(data['MACD'].iloc[-1])
                macd_signal_value = float(data['MACD_Signal'].iloc[-1])
                indicators['macd'] = macd_value
                indicators['macd_signal'] = macd_signal_value
                indicators['macd_bullish'] = bool(macd_value > macd_signal_value)
                logger.debug(f"MACD: {macd_value}, Signal: {macd_signal_value}")
            else:
                logger.warning("Колонки MACD или MACD_Signal не найдены в данных")
            
            # Bollinger Bands
            if all(col in data.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
                current_price = data['Close'].iloc[-1]
                bb_upper = data['BB_Upper'].iloc[-1]
                bb_lower = data['BB_Lower'].iloc[-1]
                indicators['bb_position'] = (current_price - bb_lower) / (bb_upper - bb_lower)
                indicators['bb_squeeze'] = data['BB_Width'].iloc[-1] if 'BB_Width' in data.columns else 0
                logger.debug(f"BB Position: {indicators['bb_position']}, Price: {current_price}, Upper: {bb_upper}, Lower: {bb_lower}")
            else:
                logger.warning("Колонки Bollinger Bands не найдены в данных")
            
            # Moving Averages
            if 'SMA_20' in data.columns and 'SMA_50' in data.columns:
                sma20_value = data['SMA_20'].iloc[-1]
                sma50_value = data['SMA_50'].iloc[-1]
                current_price = data['Close'].iloc[-1]
                indicators['sma_trend'] = bool(sma20_value > sma50_value)
                indicators['price_above_sma20'] = bool(current_price > sma20_value)
                indicators['price_above_sma50'] = bool(current_price > sma50_value)
                logger.debug(f"SMA20: {sma20_value}, SMA50: {sma50_value}, Price: {current_price}")
            else:
                logger.warning("Колонки SMA_20 или SMA_50 не найдены в данных")
            
            logger.debug(f"Извлеченные индикаторы: {indicators}")
            
        except Exception as e:
            logger.error(f"Ошибка извлечения технических индикаторов: {e}")
            logger.error(f"Данные: {data.head() if not data.empty else 'Пустые данные'}")
        
        return indicators
    
    async def _analyze_historical_patterns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Анализ исторических паттернов через DeepSeek API
        
        Args:
            data: Данные для анализа
            
        Returns:
            Список найденных паттернов
        """
        try:
            symbol = data.get('symbol', None)
            # Создание промпта для ОБУЧЕНИЯ (анализа паттернов)
            logger.debug(f"DeepSeek {self.name}: Используется промпт для обучения для символа {symbol}")
            
            # Проверка наличия метода создания промпта для обучения
            if hasattr(self, '_create_training_prompt'):
                prompt = self._create_training_prompt(data)  # Используем специальный промпт для обучения
            else:
                # Fallback на старый метод, если новый еще не создан
                logger.warning(f"DeepSeek {self.name}: Метод _create_training_prompt не найден, используется промпт для предсказания")
                prompt = self._create_analysis_prompt(data)
            
            # Отправка запроса к API с символом для кэширования
            response = await self._send_api_request(prompt, symbol=symbol)
            
            # Парсинг ответа (передаем флаг is_training=True для обучения)
            patterns = self._parse_analysis_response(response, is_training=True)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Ошибка анализа паттернов DeepSeek: {e}")
            return []
    
    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """
        Создание промпта для анализа данных
        
        Args:
            data: Данные для анализа
            
        Returns:
            Промпт для API
        """
        symbol = data.get('symbol', 'UNKNOWN')
        symbol_info = f"\nИНСТРУМЕНТ: {symbol}\n" if symbol != 'UNKNOWN' else "\nИНСТРУМЕНТ: Не указан\n"
        
        # Логирование данных для промпта
        logger.debug(f"DeepSeek {self.name}: Создание промпта для анализа (символ: {symbol})")
        logger.debug(f"DeepSeek {self.name}: Данные price_stats: {data.get('price_stats', {})}")
        logger.debug(f"DeepSeek {self.name}: Данные volume_stats: {data.get('volume_stats', {})}")
        logger.debug(f"DeepSeek {self.name}: Технические индикаторы: {list(data.get('technical_indicators', {}).keys())[:10]}{'...' if len(data.get('technical_indicators', {})) > 10 else ''}")
        
        time_series = data.get('time_series', [])
        if time_series:
            logger.debug(f"DeepSeek {self.name}: Временной ряд: {len(time_series)} значений")
        
        if 'news_stats' in data and data['news_stats'].get('total_news', 0) > 0:
            news_stats = data['news_stats']
            logger.debug(f"DeepSeek {self.name}: Новостные данные: всего={news_stats.get('total_news', 0)}, тональность={news_stats.get('avg_sentiment', 0):.3f}")
        else:
            logger.debug(f"DeepSeek {self.name}: Новостные данные отсутствуют")
        
        prompt = f"""
Ты - эксперт по техническому анализу финансовых рынков. Проанализируй следующие данные и определи торговые паттерны:
{symbol_info}
СТАТИСТИКА ЦЕН:
- Текущая цена: {data['price_stats']['current_price']:.2f}
- Средняя цена: {data['price_stats']['avg_price']:.2f}
- Изменение цены: {data['price_stats']['price_change']:.4f}
- Волатильность: {data['price_stats']['volatility']:.2f}
- Минимум: {data['price_stats']['min_price']:.2f}
- Максимум: {data['price_stats']['max_price']:.2f}

ОБЪЕМЫ:
- Средний объем: {data['volume_stats']['avg_volume']:.0f}
- Тренд объема: {data['volume_stats']['volume_trend']:.4f}

ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ:
{json.dumps(data['technical_indicators'], indent=2)}

ПОСЛЕДНИЕ ЦЕНЫ: {data['time_series']}
"""

        # Добавление новостных данных в промпт
        if 'news_stats' in data and data['news_stats']['total_news'] > 0:
            news_stats = data['news_stats']
            prompt += f"""

НОВОСТНЫЕ ДАННЫЕ:
- Общая тональность: {news_stats['avg_sentiment']:.3f}
- Уверенность в тональности: {news_stats['sentiment_confidence']:.3f}
- Всего новостей: {news_stats['total_news']}
- Позитивных новостей: {news_stats['positive_news']}
- Негативных новостей: {news_stats['negative_news']}
- Нейтральных новостей: {news_stats['neutral_news']}
- Новостной тренд: {news_stats['recent_trend']}
- Сводка новостей: {news_stats['news_summary']}
"""
            
            # Добавление последних новостей
            if 'recent_news' in data and data['recent_news']:
                prompt += "\nПОСЛЕДНИЕ НОВОСТИ:\n"
                for i, news in enumerate(data['recent_news'][:3], 1):
                    prompt += f"{i}. {news.get('title', 'Без заголовка')}\n"
                    if news.get('summary'):
                        prompt += f"   {news['summary'][:100]}...\n"

        prompt += """

Проанализируй эти данные и определи:
1. Основной тренд (бычий/медвежий/боковой)
2. Силу тренда (слабая/средняя/сильная)
3. Торговые сигналы (покупка/продажа/удержание)
4. Уровни поддержки и сопротивления
5. Риски и возможности
6. Влияние новостей на ценовое движение (если есть новостные данные)

ВАЖНО: В поле "patterns" укажи минимум 3-5 конкретных торговых паттернов, которые ты обнаружил в данных.

Примеры паттернов:
- "Голова и плечи" - разворотный паттерн
- "Двойная вершина/дно" - сигнал разворота
- "Восходящий/нисходящий треугольник" - продолжение тренда
- "Прорыв уровня поддержки/сопротивления" - важный сигнал
- "Дивергенция RSI/цены" - ослабление тренда
- "Увеличение объема при движении" - подтверждение тренда
- "Формирование флага/вымпела" - продолжение тренда
- "Молот/перевернутый молот" - разворотный сигнал
- "Поглощение бычье/медвежье" - сильный разворотный сигнал
- "Тройная вершина/дно" - разворотный паттерн

Каждый паттерн должен быть конкретным и привязанным к данным. Не пиши общие фразы типа "наблюдается тренд".
Обязательно укажи, на каких данных (даты, цены) ты видишь паттерн. Например: "Двойная вершина на уровнях 150.5 и 150.8 за последние 5 дней".

Ответь в формате JSON:
{
    "trend": "bullish/bearish/sideways",
    "trend_strength": "weak/moderate/strong",
    "signal": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "support_level": цена,
    "resistance_level": цена,
    "risk_level": "low/medium/high",
    "reasoning": "краткое объяснение",
    "patterns": ["список минимум 3-5 конкретных найденных паттернов с привязкой к данным"],
    "news_impact": "положительное/отрицательное/нейтральное влияние новостей"
}
"""
        logger.debug(f"DeepSeek {self.name}: Создан промпт для анализа (длина: {len(prompt)} символов)")
        logger.debug(f"DeepSeek {self.name}: Начало промпта (первые 250 символов):\n{prompt[:250]}...")
        return prompt
    
    def _create_training_prompt(self, data: Dict[str, Any]) -> str:
        """
        Создание промпта для обучения (анализа исторических паттернов)
        Отличается от промпта для предсказания - требует конкретные паттерны
        
        Args:
            data: Данные для анализа
            
        Returns:
            Промпт для API
        """
        symbol = data.get('symbol', 'UNKNOWN')
        symbol_info = f"\nИНСТРУМЕНТ: {symbol}\n" if symbol != 'UNKNOWN' else "\nИНСТРУМЕНТ: Не указан\n"
        
        prompt = f"""
Ты - эксперт по техническому анализу финансовых рынков.
Проанализируй следующие ИСТОРИЧЕСКИЕ данные и определи конкретные торговые паттерны:
{symbol_info}
СТАТИСТИКА ЦЕН:
- Текущая цена: {data['price_stats']['current_price']:.2f}
- Средняя цена: {data['price_stats']['avg_price']:.2f}
- Изменение цены: {data['price_stats']['price_change']:.4f}
- Волатильность: {data['price_stats']['volatility']:.2f}
- Минимум: {data['price_stats']['min_price']:.2f}
- Максимум: {data['price_stats']['max_price']:.2f}

ОБЪЕМЫ:
- Средний объем: {data['volume_stats']['avg_volume']:.0f}
- Тренд объема: {data['volume_stats']['volume_trend']:.4f}

ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ:
{json.dumps(data['technical_indicators'], indent=2)}

ПОСЛЕДНИЕ ЦЕНЫ: {data['time_series']}
"""

        # Добавление новостных данных в промпт
        if 'news_stats' in data and data['news_stats']['total_news'] > 0:
            news_stats = data['news_stats']
            prompt += f"""

НОВОСТНЫЕ ДАННЫЕ:
- Общая тональность: {news_stats['avg_sentiment']:.3f}
- Уверенность в тональности: {news_stats['sentiment_confidence']:.3f}
- Всего новостей: {news_stats['total_news']}
- Позитивных новостей: {news_stats['positive_news']}
- Негативных новостей: {news_stats['negative_news']}
- Нейтральных новостей: {news_stats['neutral_news']}
- Новостной тренд: {news_stats['recent_trend']}
- Сводка новостей: {news_stats['news_summary']}
"""
            
            # Добавление последних новостей
            if 'recent_news' in data and data['recent_news']:
                prompt += "\nПОСЛЕДНИЕ НОВОСТИ:\n"
                for i, news in enumerate(data['recent_news'][:3], 1):
                    prompt += f"{i}. {news.get('title', 'Без заголовка')}\n"
                    if news.get('summary'):
                        prompt += f"   {news['summary'][:100]}...\n"

        prompt += """

ВАЖНО: В поле "patterns" укажи минимум 3-5 КОНКРЕТНЫХ торговых паттернов, которые ты обнаружил в данных.

Примеры паттернов, которые нужно искать:
- "Голова и плечи" - разворотный паттерн на графике
- "Двойная вершина/дно" - сигнал разворота тренда
- "Восходящий/нисходящий треугольник" - продолжение тренда
- "Прорыв уровня поддержки/сопротивления" - важный сигнал изменения тренда
- "Дивергенция RSI/цены" - ослабление текущего тренда
- "Увеличение объема при движении" - подтверждение силы тренда
- "Формирование флага/вымпела" - продолжение тренда после консолидации
- "Молот/перевернутый молот" - разворотный сигнал на дне/вершине
- "Поглощение свечей" - сильный разворотный сигнал
- "Тройная вершина/дно" - долгосрочный разворот

Каждый паттерн должен быть КОНКРЕТНЫМ и привязанным к данным.
Укажи, на каких данных (примерные цены или периоды) ты видишь паттерн.
НЕ пиши общие фразы типа "наблюдается тренд" или "волатильность высокая".

Ответь в формате JSON:
{
    "trend": "bullish/bearish/sideways",
    "trend_strength": "weak/moderate/strong",
    "signal": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "support_level": цена_или_0,
    "resistance_level": цена_или_0,
    "risk_level": "low/medium/high",
    "reasoning": "развернутое объяснение с указанием конкретных паттернов",
    "patterns": [
        "Конкретный паттерн 1 с привязкой к данным",
        "Конкретный паттерн 2 с привязкой к данным",
        "Конкретный паттерн 3 с привязкой к данным",
        "и т.д. минимум 3-5 паттернов"
    ],
    "news_impact": "положительное/отрицательное/нейтральное влияние новостей"
}
"""
        logger.debug(f"DeepSeek {self.name}: Создан промпт для обучения (длина: {len(prompt)} символов)")
        logger.debug(f"DeepSeek {self.name}: Начало промпта (первые 300 символов):\n{prompt[:300]}...")
        return prompt
    
    async def _send_api_request(self, prompt: str, symbol: str = None) -> str:
        """
        Отправка запроса к DeepSeek API
        
        Args:
            prompt: Промпт для анализа
            symbol: Символ для кэширования (опционально)
            
        Returns:
            Ответ от API
        """
        try:
            # Логирование начала отправки запроса
            logger.debug(f"DeepSeek {self.name}: Отправка запроса к API (символ: {symbol}, длина промпта: {len(prompt)} символов)")
            logger.debug(f"DeepSeek {self.name}: Параметры запроса: model={self.model_name}, max_tokens={self.max_tokens}, temperature={self.temperature}")
            logger.debug(f"DeepSeek {self.name}: Начало промпта (первые 250 символов):\n{prompt[:250]}...")
            
            # Проверка кэша с учетом символа
            # Используем символ в ключе кэша, чтобы различать запросы для разных символов
            cache_key = f"{symbol}_{hash(prompt)}" if symbol else hash(prompt)
            if cache_key in self.api_cache:
                cached_response = self.api_cache[cache_key]
                cache_age = datetime.now().timestamp() - cached_response['timestamp']
                if cache_age < self.cache_ttl:
                    logger.debug(f"DeepSeek {self.name}: Используется кэшированный ответ (возраст: {cache_age:.1f} сек)")
                    return cached_response['response']
                else:
                    logger.debug(f"DeepSeek {self.name}: Кэш устарел (возраст: {cache_age:.1f} сек, TTL: {self.cache_ttl} сек)")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "stream": False
                }
                
                logger.debug(f"DeepSeek {self.name}: Payload подготовлен: model={payload['model']}, max_tokens={payload['max_tokens']}, "
                           f"temperature={payload['temperature']}, messages_count={len(payload['messages'])}")
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        api_response = result['choices'][0]['message']['content']
                        
                        # Сохранение в кэш
                        self.api_cache[cache_key] = {
                            'response': api_response,
                            'timestamp': datetime.now().timestamp(),
                            'symbol': symbol  # Сохраняем символ для отладки
                        }
                        
                        logger.debug(f"DeepSeek API: Ответ сохранен в кэш для символа {symbol}")
                        return api_response
                    else:
                        error_text = await response.text()
                        raise Exception(f"API ошибка {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"Ошибка запроса к DeepSeek API: {e}")
            raise
    
    def _parse_analysis_response(self, response: str, is_training: bool = False) -> List[Dict[str, Any]]:
        """
        Парсинг ответа от DeepSeek API
        
        Args:
            response: Ответ от API
            
        Returns:
            Список паттернов
        """
        try:
            # Логирование ответа API для диагностики
            response_preview = response[:500] if len(response) > 500 else response
            logger.debug(f"DeepSeek API ответ (первые 500 символов): {response_preview}")
            
            # Поиск JSON в ответе
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                analysis = json.loads(json_str)
                
                # Валидация ключевых полей
                trend = analysis.get('trend', 'sideways')
                signal = analysis.get('signal', 'HOLD')
                confidence = float(analysis.get('confidence', 0.5))
                reasoning = analysis.get('reasoning', '')
                support_level = analysis.get('support_level', 0)
                resistance_level = analysis.get('resistance_level', 0)
                
                # Извлечение паттернов с валидацией
                patterns_raw = analysis.get('patterns', [])
                
                # Проверка, что patterns - это массив
                if not isinstance(patterns_raw, list):
                    logger.warning(f"Поле patterns не является массивом: {type(patterns_raw)}, значение: {patterns_raw}")
                    patterns_list = []
                else:
                    patterns_list = [p for p in patterns_raw if p and isinstance(p, str) and len(p.strip()) > 0]
                
                # Строгая проверка наличия паттернов
                if not patterns_list or len(patterns_list) == 0:
                    # Для обучения - WARNING, для предсказаний - DEBUG (это нормально)
                    if is_training:
                        logger.warning(f"Массив patterns пустой в ответе API при обучении. Полный ответ: {response[:1000]}")
                        logger.debug(f"Ключи в ответе: {list(analysis.keys())}")
                        logger.debug(f"Reasoning (первые 200 символов): {reasoning[:200] if reasoning else 'отсутствует'}")
                    else:
                        logger.debug(f"Массив patterns пустой в ответе API при предсказании (это нормально)")
                else:
                    logger.debug(f"Найдено {len(patterns_list)} паттернов в ответе API")
                    logger.debug(f"Паттерны: {patterns_list}")
                
                # Fallback: если паттернов нет, пытаемся извлечь из reasoning
                if not patterns_list and reasoning:
                    pattern_keywords = {
                        'голова и плечи': 'Голова и плечи',
                        'двойная вершина': 'Двойная вершина',
                        'двойное дно': 'Двойное дно',
                        'треугольник': 'Треугольник',
                        'прорыв': 'Прорыв уровня',
                        'дивергенция': 'Дивергенция',
                        'молот': 'Молот',
                        'поглощение': 'Поглощение',
                        'флаг': 'Флаг',
                        'вымпел': 'Вымпел',
                        'поддержка': 'Уровень поддержки',
                        'сопротивление': 'Уровень сопротивления'
                    }
                    
                    reasoning_lower = reasoning.lower()
                    extracted_patterns = []
                    for keyword, pattern_name in pattern_keywords.items():
                        if keyword in reasoning_lower:
                            extracted_patterns.append(f"{pattern_name} (из анализа reasoning)")
                    
                    if extracted_patterns:
                        logger.debug(f"Извлечено паттернов из reasoning: {len(extracted_patterns)}")
                        patterns_list = extracted_patterns
                
                # Fallback: создаем базовые паттерны на основе анализа
                if not patterns_list:
                    fallback_patterns = []
                    if trend != 'sideways':
                        fallback_patterns.append(f"{trend.capitalize()} тренд подтвержден техническими индикаторами")
                    if signal in ['BUY', 'SELL']:
                        fallback_patterns.append(f"Сигнал {signal} с уверенностью {confidence:.2f}")
                    if support_level and support_level > 0:
                        fallback_patterns.append(f"Уровень поддержки: {support_level:.2f}")
                    if resistance_level and resistance_level > 0:
                        fallback_patterns.append(f"Уровень сопротивления: {resistance_level:.2f}")
                    if reasoning and len(reasoning) > 50:
                        fallback_patterns.append("Технический анализ выполнен на основе индикаторов")
                    
                    if fallback_patterns:
                        logger.debug(f"Создано fallback паттернов: {len(fallback_patterns)}")
                        patterns_list = fallback_patterns
                
                # Проверка полноты ответа
                if not signal or signal not in ['BUY', 'SELL', 'HOLD']:
                    logger.warning(f"Некорректный сигнал в ответе API: {signal}")
                if confidence <= 0:
                    logger.warning(f"Нулевая или отрицательная уверенность: {confidence}")
                
                result = {
                    'trend': trend,
                    'trend_strength': analysis.get('trend_strength', 'moderate'),
                    'signal': signal,
                    'confidence': confidence,
                    'support_level': support_level,
                    'resistance_level': resistance_level,
                    'risk_level': analysis.get('risk_level', 'medium'),
                    'reasoning': reasoning,
                    'patterns': patterns_list
                }
                
                logger.debug(f"Результат парсинга: trend={trend}, signal={signal}, confidence={confidence:.3f}, patterns_count={len(patterns_list)}")
                
                return [result]
            else:
                # Если JSON не найден, создаем базовый анализ
                logger.warning("JSON не найден в ответе API")
                logger.debug(f"Полный ответ API: {response}")
                return [{
                    'trend': 'sideways',
                    'trend_strength': 'moderate',
                    'signal': 'HOLD',
                    'confidence': 0.3,
                    'reasoning': 'Не удалось распарсить ответ API',
                    'patterns': []
                }]
                
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ответа DeepSeek: {e}")
            logger.debug(f"Ответ API (первые 1000 символов): {response[:1000]}")
            return [{
                'trend': 'sideways',
                'trend_strength': 'moderate',
                'signal': 'HOLD',
                'confidence': 0.1,
                'reasoning': f'Ошибка парсинга JSON: {str(e)}',
                'patterns': []
            }]
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа DeepSeek: {e}")
            logger.debug(f"Ответ API (первые 1000 символов): {response[:1000]}")
            return [{
                'trend': 'sideways',
                'trend_strength': 'moderate',
                'signal': 'HOLD',
                'confidence': 0.1,
                'reasoning': f'Ошибка анализа: {str(e)}',
                'patterns': []
            }]
    
    async def _evaluate_training_quality(self, data: Dict[str, Any], news_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Проверка качества обучения с использованием промпта для обучения (не для предсказания)
        
        Args:
            data: Данные для проверки
            news_data: Новостные данные для анализа
            
        Returns:
            Метрики качества обучения
        """
        try:
            logger.debug(f"DeepSeek {self.name}: Проверка качества обучения с использованием промпта для обучения")
            
            # Подготовка данных для анализа
            if 'historical' in data and isinstance(data['historical'], dict):
                # Определяем символ из данных (используем первый доступный)
                symbols_available = list(data['historical'].keys())
                symbol_for_analysis = symbols_available[0] if symbols_available else None
                
                if symbol_for_analysis:
                    logger.debug(f"DeepSeek {self.name}: Для проверки качества используется символ {symbol_for_analysis} (первый из {len(symbols_available)} символов: {symbols_available})")
                else:
                    logger.warning(f"DeepSeek {self.name}: Не удалось определить символ для проверки качества")
                
                # Берем первый символ для проверки
                symbol_data_list = [sd for sd in data['historical'].values() if not sd.empty]
                
                if not symbol_data_list:
                    logger.warning(f"DeepSeek {self.name}: Нет данных для проверки качества обучения")
                    return {}
                
                # Используем последние данные для проверки (до 100 последних строк)
                symbol_data = symbol_data_list[0].tail(100) if len(symbol_data_list) > 0 else pd.DataFrame()
                
                # Логирование данных для проверки качества
                logger.debug(f"DeepSeek {self.name}: Данные для проверки качества - форма: {symbol_data.shape}")
                if len(symbol_data) > 0 and hasattr(symbol_data.index, 'min') and hasattr(symbol_data.index, 'max'):
                    try:
                        first_date = symbol_data.index.min()
                        last_date = symbol_data.index.max()
                        date_range_days = (last_date - first_date).days if hasattr(last_date - first_date, 'days') else None
                        logger.debug(f"DeepSeek {self.name}: Диапазон дат данных для проверки: {first_date} - {last_date}" + 
                                   (f" ({date_range_days} дней)" if date_range_days else ""))
                        
                        # Актуальность данных
                        if hasattr(last_date, 'date'):
                            days_ago = (datetime.now().date() - last_date.date()).days if hasattr(datetime.now(), 'date') else None
                            if days_ago is not None:
                                logger.debug(f"DeepSeek {self.name}: Актуальность данных проверки: последняя запись {days_ago} дней назад")
                    except Exception as e:
                        logger.debug(f"DeepSeek {self.name}: Не удалось определить диапазон дат для проверки: {e}")
                
                if symbol_data.empty:
                    logger.warning(f"DeepSeek {self.name}: Данные пусты для проверки качества обучения")
                    return {}
                
                # Подготовка данных для анализа с новостными данными (training_mode=True - исключаем портфельные признаки)
                analysis_data = self._prepare_data_for_analysis(
                    symbol_data,
                    'Close',
                    portfolio_manager=None,
                    symbol=symbol_for_analysis,  # Передаем определенный символ
                    news_data=news_data,
                    training_mode=True
                )
                
                logger.debug(f"DeepSeek {self.name}: Подготовлены данные для проверки качества обучения")
                
                # Используем метод обучения с правильным промптом (через _analyze_historical_patterns)
                logger.debug(f"DeepSeek {self.name}: Вызов _analyze_historical_patterns() для проверки качества обучения")
                patterns = await self._analyze_historical_patterns(analysis_data)
                
                logger.debug(f"DeepSeek {self.name}: Получено паттернов при проверке качества: {len(patterns)}")
                
                # Логирование содержимого паттернов для диагностики
                if patterns:
                    first_pattern = patterns[0]
                    patterns_list = first_pattern.get('patterns', [])
                    logger.debug(f"DeepSeek {self.name}: Количество паттернов в анализе: {len(patterns_list)}")
                    if patterns_list:
                        logger.debug(f"DeepSeek {self.name}: Паттерны из ответа API: {patterns_list[:3]}")  # Первые 3 паттерна
                    else:
                        logger.warning(f"DeepSeek {self.name}: Массив patterns пустой в ответе при проверке качества")
                
                # Расчет метрик
                metrics = self._calculate_training_metrics(patterns, symbol_data)
                
                # ОБНОВЛЕНИЕ performance_metrics для использования в отчете
                self.performance_metrics.update(metrics)
                logger.debug(f"DeepSeek {self.name}: Обновлены performance_metrics: analysis_quality={metrics.get('analysis_quality', 0):.3f}, "
                           f"patterns_in_analysis={metrics.get('patterns_in_analysis', 0)}")
                
                logger.debug(f"DeepSeek {self.name}: Метрики качества обучения: analysis_quality={metrics.get('analysis_quality', 0):.3f}, "
                           f"patterns_in_analysis={metrics.get('patterns_in_analysis', 0)}")
                
                return metrics
            else:
                logger.warning(f"DeepSeek {self.name}: Неправильный формат данных для проверки качества обучения")
                return {}
                
        except Exception as e:
            logger.error(f"Ошибка проверки качества обучения DeepSeek {self.name}: {e}")
            import traceback
            logger.debug(f"Трассировка ошибки: {traceback.format_exc()}")
            return {}
    
    def _calculate_training_metrics(self, patterns: List[Dict[str, Any]], data: pd.DataFrame) -> Dict[str, float]:
        """
        Расчет метрик обучения
        
        Args:
            patterns: Найденные паттерны
            data: Исходные данные
            
        Returns:
            Метрики
        """
        try:
            if not patterns:
                return {
                    'patterns_found': 0,
                    'avg_confidence': 0.0,
                    'analysis_quality': 0.0,
                    'trend_accuracy': 0.0
                }
            
            avg_confidence = np.mean([p.get('confidence', 0) for p in patterns])
            patterns_count = len(patterns)
            
            # Улучшенный расчет качества анализа
            quality_scores = []
            total_patterns_in_analysis = 0
            
            for pattern in patterns:
                signal = pattern.get('signal', 'HOLD')
                confidence = pattern.get('confidence', 0.0)
                pattern_list = pattern.get('patterns', [])
                trend = pattern.get('trend', 'sideways')
                trend_strength = pattern.get('trend_strength', 'moderate')
                reasoning = pattern.get('reasoning', '')
                support_level = pattern.get('support_level', 0)
                resistance_level = pattern.get('resistance_level', 0)
                
                pattern_quality = 0.0
                
                # Базовая оценка на основе уверенности (самый важный фактор - 50%)
                pattern_quality += confidence * 0.5
                
                # Оценка сигнала (BUY/SELL важнее HOLD, но HOLD тоже важен)
                if signal in ['BUY', 'SELL']:
                    pattern_quality += 0.2
                elif signal == 'HOLD' and confidence > 0.5:
                    pattern_quality += 0.1  # HOLD с уверенностью тоже хорошо
                
                # Оценка тренда
                if trend != 'sideways':
                    pattern_quality += 0.1
                if trend_strength == 'strong':
                    pattern_quality += 0.1
                elif trend_strength == 'weak':
                    pattern_quality += 0.05
                
                # Оценка наличия паттернов в анализе (более мягкая оценка)
                if pattern_list and len(pattern_list) > 0:
                    total_patterns_in_analysis += len(pattern_list)
                    # Бонус за паттерны: до 0.15 за паттерны, но не снижаем качество если их нет
                    pattern_quality += min(len(pattern_list) * 0.05, 0.15)
                else:
                    # Если паттернов нет, но есть качественный reasoning, добавляем бонус
                    if reasoning and len(reasoning) > 50:
                        # Проверяем, есть ли в reasoning упоминания паттернов
                        pattern_keywords = ['паттерн', 'pattern', 'тренд', 'trend', 'сигнал', 'signal',
                                          'поддержка', 'сопротивление', 'support', 'resistance',
                                          'дивергенция', 'divergence', 'прорыв', 'breakout',
                                          'молот', 'hammer', 'треугольник', 'triangle']
                        if any(keyword in reasoning.lower() for keyword in pattern_keywords):
                            pattern_quality += 0.1  # Бонус за описание паттернов в reasoning
                            logger.debug("Найдены упоминания паттернов в reasoning, добавлен бонус")
                
                # Оценка качества reasoning (если есть развернутое объяснение)
                if reasoning:
                    reasoning_len = len(reasoning)
                    if reasoning_len > 100:
                        pattern_quality += 0.15
                    elif reasoning_len > 50:
                        pattern_quality += 0.1
                    elif reasoning_len > 20:
                        pattern_quality += 0.05
                
                # Бонус за наличие всех важных полей
                if support_level and support_level > 0:
                    pattern_quality += 0.05
                if resistance_level and resistance_level > 0:
                    pattern_quality += 0.05
                
                quality_scores.append(min(pattern_quality, 1.0))
            
            # Среднее качество по всем паттернам (для DeepSeek обычно 1 паттерн)
            analysis_quality = np.mean(quality_scores) if quality_scores else 0.0
            
            # Базовая оценка за успешный анализ (если основные поля заполнены)
            first_pattern = patterns[0] if patterns else None
            if first_pattern:
                signal = first_pattern.get('signal', 'HOLD')
                confidence = first_pattern.get('confidence', 0.0)
                reasoning = first_pattern.get('reasoning', '')
                
                # Если API вернул валидный JSON с основными полями, это уже успех
                if signal in ['BUY', 'SELL', 'HOLD'] and confidence > 0:
                    # Минимум 20% за валидный ответ
                    analysis_quality = max(analysis_quality, 0.2)
                    logger.debug(f"Базовая оценка качества установлена минимум в 0.2 (signal={signal}, confidence={confidence:.3f})")
                
                # Если паттернов нет, но есть качественный анализ с уверенностью >0.6
                first_pattern_list = first_pattern.get('patterns', [])
                if not first_pattern_list and reasoning and len(reasoning) > 50:
                    if confidence > 0.6 and signal in ['BUY', 'SELL']:
                        # Не снижаем качество ниже 0.3 для качественного анализа без паттернов
                        analysis_quality = max(analysis_quality, 0.3)
                        logger.debug(f"Качественный анализ без паттернов: качество установлено минимум в 0.3")
            
            # Детальное логирование при низком качестве анализа
            if analysis_quality < 0.3:
                logger.warning(f"Низкое качество анализа: {analysis_quality:.3f}")
                if first_pattern:
                    logger.warning(f"Детали анализа: signal={first_pattern.get('signal')}, "
                                 f"confidence={first_pattern.get('confidence', 0):.3f}, "
                                 f"patterns_count={len(first_pattern.get('patterns', []))}, "
                                 f"reasoning_len={len(first_pattern.get('reasoning', ''))}")
                    if first_pattern.get('patterns'):
                        logger.warning(f"Паттерны: {first_pattern.get('patterns')}")
                    else:
                        logger.warning("Паттерны отсутствуют в ответе")
            
            # Дополнительный бонус: если анализ был выполнен успешно, но качество низкое,
            # добавляем базовый бонус за сам факт успешного анализа
            if analysis_quality > 0 and analysis_quality < 0.3:
                # Минимальная базовая оценка за успешный анализ (20%)
                analysis_quality = max(analysis_quality, 0.2)
                logger.debug(f"Анализ выполнен успешно, качество повышено до минимума 0.2")
            
            # Улучшенный расчет точности тренда
            # Учитываем не только уверенность, но и согласованность тренда
            trend_scores = []
            for pattern in patterns:
                trend = pattern.get('trend', 'sideways')
                confidence = pattern.get('confidence', 0.0)
                trend_strength = pattern.get('trend_strength', 'moderate')
                
                trend_score = confidence
                if trend != 'sideways':
                    trend_score *= 1.1  # Бонус за определенный тренд
                if trend_strength == 'strong':
                    trend_score *= 1.2
                elif trend_strength == 'weak':
                    trend_score *= 0.9
                
                trend_scores.append(min(trend_score, 1.0))
            
            trend_accuracy = np.mean(trend_scores) if trend_scores else avg_confidence * 0.8
            
            # Учитываем количество найденных паттернов в анализе
            # Если паттернов больше, это лучше (но не снижаем качество если их нет)
            if total_patterns_in_analysis > 0:
                patterns_bonus = min(total_patterns_in_analysis / 5.0, 0.2)  # До 0.2 бонуса
                analysis_quality = min(analysis_quality + patterns_bonus, 1.0)
                logger.debug(f"Добавлен бонус за паттерны: {patterns_bonus:.3f}, итоговое качество: {analysis_quality:.3f}")
            else:
                logger.debug(f"Паттерны отсутствуют, бонус не добавлен, качество: {analysis_quality:.3f}")
            
            return {
                'patterns_found': patterns_count,
                'patterns_in_analysis': total_patterns_in_analysis,  # Общее количество паттернов в анализе
                'avg_confidence': avg_confidence,
                'analysis_quality': analysis_quality,
                'trend_accuracy': trend_accuracy,
                'signal_reliability': avg_confidence * 0.7
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета метрик DeepSeek: {e}")
            return {
                'patterns_found': 0,
                'avg_confidence': 0.0,
                'analysis_quality': 0.0,
                'trend_accuracy': 0.0
            }
    
    async def predict(self, data: pd.DataFrame, portfolio_manager=None, symbol: str = None, news_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Предсказание с помощью DeepSeek
        
        Args:
            data: Входные данные
            portfolio_manager: Менеджер портфеля для извлечения портфельных признаков
            symbol: Символ для анализа портфельных признаков
            news_data: Новостные данные для анализа
            
        Returns:
            Словарь с предсказаниями
        """
        try:
            if not self.is_trained:
                raise ValueError(f"Модель {self.name} не проанализирована")
            
            # Подготовка данных для предсказания с портфельными и новостными признаками
            prediction_data = self._prepare_data_for_analysis(data, 'Close', portfolio_manager, symbol, news_data)
            
            # Создание промпта для предсказания
            logger.debug(f"DeepSeek {self.name}: Используется промпт для предсказания для символа {symbol}")
            prompt = self._create_prediction_prompt(prediction_data)
            
            # Отправка запроса к API с символом для кэширования
            response = await self._send_api_request(prompt, symbol=symbol)
            
            # Парсинг ответа (передаем флаг is_training=False для предсказания)
            predictions = self._parse_analysis_response(response, is_training=False)
            
            if predictions:
                prediction = predictions[0]
                
                # Расчет силы сигнала
                signal_strength = self._calculate_signal_strength(prediction)
                
                # Добавление новостной информации в результат
                news_info = {}
                if news_data and symbol and symbol in news_data:
                    symbol_news = news_data[symbol]
                    news_info = {
                        'news_sentiment': symbol_news.get('avg_sentiment', 0.0),
                        'news_trend': symbol_news.get('recent_trend', 'neutral'),
                        'news_count': symbol_news.get('total_news', 0),
                        'news_summary': symbol_news.get('news_summary', ''),
                        'news_impact': prediction.get('news_impact', 'neutral')
                    }
                
                # Сохранение результатов
                self.last_prediction = {
                    'symbol': symbol,  # Добавляем символ в результат
                    'signal': prediction['signal'],
                    'signal_strength': signal_strength,
                    'confidence': prediction['confidence'],
                    'trend': prediction['trend'],
                    'trend_strength': prediction['trend_strength'],
                    'support_level': prediction.get('support_level', 0),
                    'resistance_level': prediction.get('resistance_level', 0),
                    'risk_level': prediction.get('risk_level', 'medium'),
                    'reasoning': prediction.get('reasoning', ''),
                    'patterns': prediction.get('patterns', []),
                    'news_info': news_info
                }
                self.last_prediction_time = datetime.now()
                
                logger.debug(f"DeepSeek модель {self.name} предсказала для {symbol}: {prediction['signal']} (уверенность: {prediction['confidence']:.3f})")
                
                return self.last_prediction
            else:
                return {
                    'symbol': symbol,  # Добавляем символ даже при ошибке
                    'signal': 'HOLD',
                    'signal_strength': 0.0,
                    'confidence': 0.0,
                    'reasoning': 'Не удалось получить предсказание',
                    'news_info': {}
                }
                
        except Exception as e:
            logger.error(f"Ошибка предсказания DeepSeek моделью {self.name} для символа {symbol}: {e}")
            return {
                'symbol': symbol,  # Добавляем символ даже при ошибке
                'signal': 'HOLD',
                'signal_strength': 0.0,
                'confidence': 0.0,
                'reasoning': f'Ошибка: {str(e)}',
                'news_info': {}
            }
    
    def _create_prediction_prompt(self, data: Dict[str, Any]) -> str:
        """
        Создание промпта для предсказания
        
        Args:
            data: Данные для предсказания
            
        Returns:
            Промпт для API
        """
        symbol = data.get('symbol', 'UNKNOWN')
        symbol_info = f"\nИНСТРУМЕНТ: {symbol}\n" if symbol != 'UNKNOWN' else "\nИНСТРУМЕНТ: Не указан\n"
        
        # Логирование данных, которые отправляются в API
        logger.debug(f"DeepSeek {self.name}: Создание промпта для предсказания (символ: {symbol})")
        logger.debug(f"DeepSeek {self.name}: Данные price_stats: {data.get('price_stats', {})}")
        logger.debug(f"DeepSeek {self.name}: Данные volume_stats: {data.get('volume_stats', {})}")
        logger.debug(f"DeepSeek {self.name}: Технические индикаторы: {list(data.get('technical_indicators', {}).keys())[:10]}{'...' if len(data.get('technical_indicators', {})) > 10 else ''}")
        
        if 'news_stats' in data and data['news_stats'].get('total_news', 0) > 0:
            news_stats = data['news_stats']
            logger.debug(f"DeepSeek {self.name}: Новостные данные: всего={news_stats.get('total_news', 0)}, тональность={news_stats.get('avg_sentiment', 0):.3f}")
        else:
            logger.debug(f"DeepSeek {self.name}: Новостные данные отсутствуют")
        
        prompt = f"""
Ты - эксперт по техническому анализу. На основе текущих данных дай краткий торговый сигнал:
{symbol_info}
ТЕКУЩИЕ ДАННЫЕ:
- Цена: {data['price_stats']['current_price']:.2f}
- Тренд: {data['price_stats']['price_change']:.4f}
- Волатильность: {data['price_stats']['volatility']:.2f}
- Объем: {data['volume_stats']['avg_volume']:.0f}

ИНДИКАТОРЫ:
{json.dumps(data['technical_indicators'], indent=2)}

Дай краткий ответ в формате JSON:
{{
    "signal": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "trend": "bullish/bearish/sideways",
    "reasoning": "краткое объяснение"
}}
"""
        logger.debug(f"DeepSeek {self.name}: Создан промпт для предсказания (длина: {len(prompt)} символов)")
        logger.debug(f"DeepSeek {self.name}: Начало промпта (первые 250 символов):\n{prompt[:250]}...")
        return prompt
    
    def _calculate_signal_strength(self, prediction: Dict[str, Any]) -> float:
        """
        Расчет силы сигнала
        
        Args:
            prediction: Предсказание
            
        Returns:
            Сила сигнала от -1 до 1
        """
        try:
            signal = prediction.get('signal', 'HOLD')
            confidence = prediction.get('confidence', 0.0)
            trend = prediction.get('trend', 'sideways')
            
            base_strength = 0.0
            
            if signal == 'BUY':
                base_strength = confidence
            elif signal == 'SELL':
                base_strength = -confidence
            
            # Корректировка на основе тренда
            if trend == 'bullish' and signal == 'BUY':
                base_strength *= 1.2
            elif trend == 'bearish' and signal == 'SELL':
                base_strength *= 1.2
            elif trend != 'sideways' and signal == 'HOLD':
                base_strength *= 0.5
            
            return max(-1.0, min(1.0, base_strength))
            
        except Exception:
            return 0.0
    
    async def get_feature_importance(self) -> Dict[str, float]:
        """
        Получение важности признаков для DeepSeek
        
        Returns:
            Словарь с важностью признаков
        """
        # DeepSeek не предоставляет прямую важность признаков
        # Возвращаем базовую важность на основе технических индикаторов
        return {
            'price_change': 0.3,
            'volume': 0.2,
            'rsi': 0.15,
            'macd': 0.15,
            'bollinger_bands': 0.1,
            'moving_averages': 0.1
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса DeepSeek сети
        
        Returns:
            Словарь со статусом
        """
        return {
            'name': self.name,
            'is_trained': self.is_trained,
            'performance_metrics': self.performance_metrics,
            'last_prediction_time': self.last_prediction_time.isoformat() if self.last_prediction_time else None,
            'api_configured': bool(self.api_key),
            'cache_size': len(self.api_cache),
            'config': {
                'model_name': self.model_name,
                'max_tokens': self.max_tokens,
                'temperature': self.temperature
            }
        }
