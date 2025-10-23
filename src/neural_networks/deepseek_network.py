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
    
    async def train(self, data: pd.DataFrame, target: str = 'Close') -> Dict[str, float]:
        """
        "Обучение" DeepSeek модели (анализ исторических паттернов)
        
        Args:
            data: Данные для анализа
            target: Целевая переменная
            
        Returns:
            Метрики анализа
        """
        try:
            logger.info(f"Анализ исторических данных DeepSeek моделью {self.name}")
            
            # Подготовка данных для анализа
            analysis_data = self._prepare_data_for_analysis(data, target)
            
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
    
    def _prepare_data_for_analysis(self, data: pd.DataFrame, target: str) -> Dict[str, Any]:
        """
        Подготовка данных для анализа DeepSeek
        
        Args:
            data: Исходные данные
            target: Целевая переменная
            
        Returns:
            Подготовленные данные для анализа
        """
        try:
            # Получение последних данных
            recent_data = data.tail(self.analysis_window).copy()
            
            # Расчет технических индикаторов
            recent_data = self.prepare_features(recent_data)
            
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
            # RSI
            if 'RSI' in data.columns:
                indicators['rsi'] = float(data['RSI'].iloc[-1])
                indicators['rsi_overbought'] = bool(data['RSI'].iloc[-1] > 70)
                indicators['rsi_oversold'] = bool(data['RSI'].iloc[-1] < 30)
            
            # MACD
            if 'MACD' in data.columns and 'MACD_Signal' in data.columns:
                indicators['macd'] = float(data['MACD'].iloc[-1])
                indicators['macd_signal'] = float(data['MACD_Signal'].iloc[-1])
                indicators['macd_bullish'] = bool(data['MACD'].iloc[-1] > data['MACD_Signal'].iloc[-1])
            
            # Bollinger Bands
            if all(col in data.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
                current_price = data['Close'].iloc[-1]
                indicators['bb_position'] = (current_price - data['BB_Lower'].iloc[-1]) / (data['BB_Upper'].iloc[-1] - data['BB_Lower'].iloc[-1])
                indicators['bb_squeeze'] = data['BB_Width'].iloc[-1] if 'BB_Width' in data.columns else 0
            
            # Moving Averages
            if 'SMA_20' in data.columns and 'SMA_50' in data.columns:
                indicators['sma_trend'] = bool(data['SMA_20'].iloc[-1] > data['SMA_50'].iloc[-1])
                indicators['price_above_sma20'] = bool(data['Close'].iloc[-1] > data['SMA_20'].iloc[-1])
                indicators['price_above_sma50'] = bool(data['Close'].iloc[-1] > data['SMA_50'].iloc[-1])
            
        except Exception as e:
            logger.error(f"Ошибка извлечения технических индикаторов: {e}")
        
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
            # Создание промпта для анализа
            prompt = self._create_analysis_prompt(data)
            
            # Отправка запроса к API
            response = await self._send_api_request(prompt)
            
            # Парсинг ответа
            patterns = self._parse_analysis_response(response)
            
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
        prompt = f"""
Ты - эксперт по техническому анализу финансовых рынков. Проанализируй следующие данные и определи торговые паттерны:

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

Проанализируй эти данные и определи:
1. Основной тренд (бычий/медвежий/боковой)
2. Силу тренда (слабая/средняя/сильная)
3. Торговые сигналы (покупка/продажа/удержание)
4. Уровни поддержки и сопротивления
5. Риски и возможности

Ответь в формате JSON:
{{
    "trend": "bullish/bearish/sideways",
    "trend_strength": "weak/moderate/strong",
    "signal": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "support_level": цена,
    "resistance_level": цена,
    "risk_level": "low/medium/high",
    "reasoning": "краткое объяснение",
    "patterns": ["список найденных паттернов"]
}}
"""
        return prompt
    
    async def _send_api_request(self, prompt: str) -> str:
        """
        Отправка запроса к DeepSeek API
        
        Args:
            prompt: Промпт для анализа
            
        Returns:
            Ответ от API
        """
        try:
            # Проверка кэша
            cache_key = hash(prompt)
            if cache_key in self.api_cache:
                cached_response = self.api_cache[cache_key]
                if datetime.now().timestamp() - cached_response['timestamp'] < self.cache_ttl:
                    return cached_response['response']
            
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
                            'timestamp': datetime.now().timestamp()
                        }
                        
                        return api_response
                    else:
                        error_text = await response.text()
                        raise Exception(f"API ошибка {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"Ошибка запроса к DeepSeek API: {e}")
            raise
    
    def _parse_analysis_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Парсинг ответа от DeepSeek API
        
        Args:
            response: Ответ от API
            
        Returns:
            Список паттернов
        """
        try:
            # Поиск JSON в ответе
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                analysis = json.loads(json_str)
                
                return [{
                    'trend': analysis.get('trend', 'sideways'),
                    'trend_strength': analysis.get('trend_strength', 'moderate'),
                    'signal': analysis.get('signal', 'HOLD'),
                    'confidence': float(analysis.get('confidence', 0.5)),
                    'support_level': analysis.get('support_level', 0),
                    'resistance_level': analysis.get('resistance_level', 0),
                    'risk_level': analysis.get('risk_level', 'medium'),
                    'reasoning': analysis.get('reasoning', ''),
                    'patterns': analysis.get('patterns', [])
                }]
            else:
                # Если JSON не найден, создаем базовый анализ
                return [{
                    'trend': 'sideways',
                    'trend_strength': 'moderate',
                    'signal': 'HOLD',
                    'confidence': 0.3,
                    'reasoning': 'Не удалось распарсить ответ API'
                }]
                
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа DeepSeek: {e}")
            return [{
                'trend': 'sideways',
                'trend_strength': 'moderate',
                'signal': 'HOLD',
                'confidence': 0.1,
                'reasoning': f'Ошибка анализа: {str(e)}'
            }]
    
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
                    'analysis_quality': 0.0
                }
            
            avg_confidence = np.mean([p.get('confidence', 0) for p in patterns])
            patterns_count = len(patterns)
            
            # Расчет качества анализа
            quality_score = 0.0
            for pattern in patterns:
                if pattern.get('signal') in ['BUY', 'SELL']:
                    quality_score += 0.3
                if pattern.get('confidence', 0) > 0.7:
                    quality_score += 0.2
                if pattern.get('patterns'):
                    quality_score += 0.1
            
            analysis_quality = min(quality_score, 1.0)
            
            return {
                'patterns_found': patterns_count,
                'avg_confidence': avg_confidence,
                'analysis_quality': analysis_quality,
                'trend_accuracy': avg_confidence * 0.8,  # Примерная оценка
                'signal_reliability': avg_confidence * 0.7
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета метрик DeepSeek: {e}")
            return {
                'patterns_found': 0,
                'avg_confidence': 0.0,
                'analysis_quality': 0.0
            }
    
    async def predict(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Предсказание с помощью DeepSeek
        
        Args:
            data: Входные данные
            
        Returns:
            Словарь с предсказаниями
        """
        try:
            if not self.is_trained:
                raise ValueError(f"Модель {self.name} не проанализирована")
            
            # Подготовка данных для предсказания
            prediction_data = self._prepare_data_for_analysis(data, 'Close')
            
            # Создание промпта для предсказания
            prompt = self._create_prediction_prompt(prediction_data)
            
            # Отправка запроса к API
            response = await self._send_api_request(prompt)
            
            # Парсинг ответа
            predictions = self._parse_analysis_response(response)
            
            if predictions:
                prediction = predictions[0]
                
                # Расчет силы сигнала
                signal_strength = self._calculate_signal_strength(prediction)
                
                # Сохранение результатов
                self.last_prediction = {
                    'signal': prediction['signal'],
                    'signal_strength': signal_strength,
                    'confidence': prediction['confidence'],
                    'trend': prediction['trend'],
                    'trend_strength': prediction['trend_strength'],
                    'support_level': prediction.get('support_level', 0),
                    'resistance_level': prediction.get('resistance_level', 0),
                    'risk_level': prediction.get('risk_level', 'medium'),
                    'reasoning': prediction.get('reasoning', ''),
                    'patterns': prediction.get('patterns', [])
                }
                self.last_prediction_time = datetime.now()
                
                logger.debug(f"DeepSeek модель {self.name} предсказала: {prediction['signal']} (уверенность: {prediction['confidence']:.3f})")
                
                return self.last_prediction
            else:
                return {
                    'signal': 'HOLD',
                    'signal_strength': 0.0,
                    'confidence': 0.0,
                    'reasoning': 'Не удалось получить предсказание'
                }
                
        except Exception as e:
            logger.error(f"Ошибка предсказания DeepSeek моделью {self.name}: {e}")
            return {
                'signal': 'HOLD',
                'signal_strength': 0.0,
                'confidence': 0.0,
                'reasoning': f'Ошибка: {str(e)}'
            }
    
    def _create_prediction_prompt(self, data: Dict[str, Any]) -> str:
        """
        Создание промпта для предсказания
        
        Args:
            data: Данные для предсказания
            
        Returns:
            Промпт для API
        """
        prompt = f"""
Ты - эксперт по техническому анализу. На основе текущих данных дай краткий торговый сигнал:

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
