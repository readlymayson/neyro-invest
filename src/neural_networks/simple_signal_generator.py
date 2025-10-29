# -*- coding: utf-8 -*-
"""
Простой генератор сигналов для бэктестинга
"""

import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger


class SimpleSignalGenerator:
    """
    Простой генератор торговых сигналов для бэктестинга
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация генератора сигналов
        
        Args:
            config: Конфигурация генератора
        """
        self.config = config
        self.signal_probability = config.get('signal_probability', 0.4)
        self.buy_probability = config.get('buy_probability', 0.6)
        self.confidence_range = config.get('confidence_range', [0.7, 0.95])
        self.min_confidence = config.get('min_confidence', 0.6)
        
        logger.info(f"Инициализирован простой генератор сигналов:")
        logger.info(f"  - Вероятность сигнала: {self.signal_probability}")
        logger.info(f"  - Вероятность покупки: {self.buy_probability}")
        logger.info(f"  - Диапазон уверенности: {self.confidence_range}")
    
    def generate_signals(self, daily_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерация торговых сигналов
        
        Args:
            daily_data: Данные за день
            
        Returns:
            Словарь с сигналами в формате для trading_engine
        """
        signals = {}
        
        for symbol, data in daily_data.items():
            if isinstance(data, dict) and 'price' in data:
                # Простая логика: случайный сигнал
                signal_prob = np.random.random()
                
                if signal_prob > (1 - self.signal_probability):  # Генерируем сигнал
                    signal_type = np.random.choice(
                        ['BUY', 'SELL'], 
                        p=[self.buy_probability, 1 - self.buy_probability]
                    )
                    confidence = np.random.uniform(
                        self.confidence_range[0], 
                        self.confidence_range[1]
                    )
                    
                    # Проверяем минимальную уверенность
                    if confidence >= self.min_confidence:
                        # Генерация reasoning для простого генератора
                        reasoning = self._generate_simple_reasoning(signal_type, confidence, symbol)
                        
                        signals[symbol] = {
                            'symbol': symbol,
                            'signal': signal_type,
                            'confidence': confidence,
                            'price': data['price'],
                            'timestamp': data.get('timestamp', datetime.now().isoformat()),
                            'source': 'simple_generator',
                            'reasoning': reasoning
                        }
                        logger.debug(f"Сгенерирован сигнал {signal_type} для {symbol} с уверенностью {confidence:.2f}")
        
        # Возвращаем в формате, который ожидает trading_engine
        return {
            'individual_predictions': {
                'simple_generator': signals
            },
            'ensemble_predictions': signals,
            'symbols_analyzed': list(signals.keys()),
            'models_used': ['simple_generator'],
            'analysis_time': datetime.now().isoformat()
        }
    
    def _generate_simple_reasoning(self, signal_type: str, confidence: float, symbol: str) -> str:
        """
        Генерация простого reasoning для случайного генератора
        
        Args:
            signal_type: Тип сигнала
            confidence: Уверенность
            symbol: Тикер инструмента
            
        Returns:
            Краткая сводка причины решения
        """
        try:
            reasoning_parts = []
            
            # Основная причина
            if signal_type == 'BUY':
                reasoning_parts.append(f"Случайная рекомендация покупки {symbol}")
            elif signal_type == 'SELL':
                reasoning_parts.append(f"Случайная рекомендация продажи {symbol}")
            
            # Уверенность
            if confidence > 0.8:
                reasoning_parts.append("высокая случайная уверенность")
            elif confidence > 0.6:
                reasoning_parts.append("средняя случайная уверенность")
            else:
                reasoning_parts.append("низкая случайная уверенность")
            
            # Дополнительная информация
            reasoning_parts.append("основано на случайной генерации для тестирования")
            
            return ". ".join(reasoning_parts) + "."
            
        except Exception as e:
            logger.error(f"Ошибка генерации простого reasoning: {e}")
            return f"Случайный сигнал {signal_type} для {symbol} с уверенностью {confidence:.2f}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики генератора
        
        Returns:
            Статистика работы генератора
        """
        return {
            'signal_probability': self.signal_probability,
            'buy_probability': self.buy_probability,
            'confidence_range': self.confidence_range,
            'min_confidence': self.min_confidence,
            'generator_type': 'simple_random'
        }
