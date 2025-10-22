"""
Провайдер данных для российских акций
Использует альтернативные источники данных
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
import requests
import json


class RussianDataProvider:
    """
    Провайдер данных для российских акций
    """
    
    def __init__(self, symbols: List[str]):
        """
        Инициализация провайдера
        
        Args:
            symbols: Список символов для отслеживания
        """
        self.symbols = symbols
        self.data_cache = {}
        
        # Моковые данные для тестирования (реалистичные цены российских акций)
        self.mock_data = {
            'SBER': {
                'name': 'Сбербанк',
                'current_price': 250.0,
                'currency': 'RUB'
            },
            'GAZP': {
                'name': 'Газпром',
                'current_price': 180.0,
                'currency': 'RUB'
            },
            'LKOH': {
                'name': 'Лукойл',
                'current_price': 7500.0,
                'currency': 'RUB'
            },
            'NVTK': {
                'name': 'Новатэк',
                'current_price': 1200.0,
                'currency': 'RUB'
            },
            'ROSN': {
                'name': 'Роснефть',
                'current_price': 550.0,
                'currency': 'RUB'
            },
            'GMKN': {
                'name': 'ГМК Норникель',
                'current_price': 15000.0,
                'currency': 'RUB'
            },
            'YNDX': {
                'name': 'Яндекс',
                'current_price': 3500.0,
                'currency': 'RUB'
            },
            'MGNT': {
                'name': 'Магнит',
                'current_price': 6000.0,
                'currency': 'RUB'
            },
            'TATN': {
                'name': 'Татнефть',
                'current_price': 650.0,
                'currency': 'RUB'
            },
            'SNGS': {
                'name': 'Сургутнефтегаз',
                'current_price': 35.0,
                'currency': 'RUB'
            }
        }
        
        logger.info(f"Инициализирован провайдер российских данных для {len(symbols)} инструментов")
    
    async def get_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """
        Получение исторических данных (моковые данные)
        
        Args:
            symbol: Тикер инструмента
            period: Период данных
            
        Returns:
            DataFrame с историческими данными
        """
        try:
            if symbol not in self.mock_data:
                logger.warning(f"Символ {symbol} не найден в моковых данных")
                return pd.DataFrame()
            
            # Генерируем моковые исторические данные
            days = 365 if period == "1y" else 365  # Всегда генерируем год данных для обучения
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Генерируем реалистичные данные
            base_price = self.mock_data[symbol]['current_price']
            np.random.seed(hash(symbol) % 2**32)  # Для воспроизводимости
            
            # Создаем более реалистичное случайное блуждание цен
            returns = np.random.normal(0, 0.03, len(dates))  # 3% волатильность
            prices = [base_price]
            
            # Добавляем тренды и циклы для более реалистичных данных
            trend = np.linspace(0, 0.1, len(dates))  # Небольшой восходящий тренд
            cycle = 0.05 * np.sin(2 * np.pi * np.arange(len(dates)) / 30)  # Месячный цикл
            
            for i in range(1, len(dates)):
                # Комбинируем случайное блуждание, тренд и цикл
                total_return = returns[i] + trend[i] + cycle[i]
                new_price = prices[-1] * (1 + total_return)
                # Ограничиваем разумными пределами
                new_price = max(new_price, base_price * 0.3)  # Минимум 30%
                new_price = min(new_price, base_price * 3.0)  # Максимум 300%
                prices.append(new_price)
            
            # Создаем DataFrame
            data = pd.DataFrame({
                'Open': [p * (1 + np.random.normal(0, 0.01)) for p in prices],
                'High': [p * (1 + abs(np.random.normal(0, 0.02))) for p in prices],
                'Low': [p * (1 - abs(np.random.normal(0, 0.02))) for p in prices],
                'Close': prices,
                'Volume': [np.random.randint(1000000, 10000000) for _ in range(len(dates))]
            }, index=dates)
            
            # Убеждаемся, что High >= Low
            data['High'] = np.maximum(data['High'], data['Low'])
            data['High'] = np.maximum(data['High'], data['Close'])
            data['Low'] = np.minimum(data['Low'], data['Close'])
            
            logger.info(f"Сгенерированы моковые данные для {symbol}: {len(data)} дней")
            return data
            
        except Exception as e:
            logger.error(f"Ошибка генерации данных для {symbol}: {e}")
            return pd.DataFrame()
    
    async def get_current_price(self, symbol: str) -> float:
        """
        Получение текущей цены
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            Текущая цена
        """
        try:
            if symbol in self.mock_data:
                # Добавляем небольшое случайное изменение
                base_price = self.mock_data[symbol]['current_price']
                change = np.random.normal(0, 0.01)  # 1% волатильность
                return base_price * (1 + change)
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка получения цены для {symbol}: {e}")
            return 0.0
    
    async def get_market_data(self) -> Dict[str, Dict]:
        """
        Получение рыночных данных для всех символов
        
        Returns:
            Словарь с данными по всем символам
        """
        result = {}
        
        for symbol in self.symbols:
            try:
                current_price = await self.get_current_price(symbol)
                
                result[symbol] = {
                    'price': current_price,
                    'volume': np.random.randint(1000000, 10000000),
                    'change': np.random.normal(0, 0.02) * current_price,
                    'change_percent': np.random.normal(0, 2),
                    'market_cap': current_price * np.random.randint(1000000, 100000000),
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Ошибка получения данных для {symbol}: {e}")
                result[symbol] = {
                    'price': 0,
                    'volume': 0,
                    'change': 0,
                    'change_percent': 0,
                    'market_cap': 0,
                    'timestamp': datetime.now().isoformat()
                }
        
        return result
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """
        Получение информации о символе
        
        Args:
            symbol: Тикер инструмента
            
        Returns:
            Словарь с информацией
        """
        return self.mock_data.get(symbol, {
            'name': f'Неизвестная компания {symbol}',
            'current_price': 100.0,
            'currency': 'RUB'
        })
