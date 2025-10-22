"""
Пример бэктестинга торговых стратегий
"""

import asyncio
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Добавление корневой директории в путь
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.data.data_provider import DataProvider
from src.neural_networks.network_manager import NetworkManager
from src.trading.trading_engine import TradingEngine, TradingSignal
from src.portfolio.portfolio_manager import PortfolioManager
from src.utils.config_manager import ConfigManager
from loguru import logger


class BacktestEngine:
    """
    Движок для бэктестинга торговых стратегий
    """
    
    def __init__(self, config_path: str):
        """
        Инициализация движка бэктестинга
        
        Args:
            config_path: Путь к конфигурационному файлу
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Компоненты системы
        self.data_provider = None
        self.network_manager = None
        self.trading_engine = None
        self.portfolio_manager = None
        
        # Результаты бэктестинга
        self.backtest_results = []
        
    async def initialize(self):
        """
        Инициализация компонентов для бэктестинга
        """
        logger.info("Инициализация компонентов бэктестинга")
        
        # Инициализация провайдера данных
        self.data_provider = DataProvider(self.config['data'])
        await self.data_provider.initialize()
        
        # Инициализация менеджера нейросетей
        self.network_manager = NetworkManager(self.config['neural_networks'])
        await self.network_manager.initialize()
        
        # Инициализация торгового движка
        self.trading_engine = TradingEngine(self.config['trading'])
        await self.trading_engine.initialize()
        
        # Инициализация менеджера портфеля
        self.portfolio_manager = PortfolioManager(self.config['portfolio'])
        await self.portfolio_manager.initialize()
        
        # Установка компонентов в торговый движок
        self.trading_engine.set_components(self.data_provider, self.portfolio_manager)
        
        logger.info("Компоненты бэктестинга инициализированы")
    
    async def run_backtest(self, start_date: datetime, end_date: datetime, 
                          train_period_days: int = 365):
        """
        Запуск бэктестинга
        
        Args:
            start_date: Дата начала бэктестинга
            end_date: Дата окончания бэктестинга
            train_period_days: Период обучения моделей в днях
        """
        try:
            logger.info(f"Запуск бэктестинга с {start_date} по {end_date}")
            
            # Обучение моделей на исторических данных
            await self._train_models_for_backtest(start_date, train_period_days)
            
            # Выполнение бэктестинга
            current_date = start_date
            while current_date <= end_date:
                await self._run_backtest_day(current_date)
                current_date += timedelta(days=1)
            
            # Анализ результатов
            await self._analyze_backtest_results()
            
            logger.info("Бэктестинг завершен")
            
        except Exception as e:
            logger.error(f"Ошибка бэктестинга: {e}")
            raise
    
    async def _train_models_for_backtest(self, end_date: datetime, train_period_days: int):
        """
        Обучение моделей для бэктестинга
        
        Args:
            end_date: Дата окончания периода обучения
            train_period_days: Период обучения в днях
        """
        try:
            logger.info("Обучение моделей для бэктестинга")
            
            # Получение данных для обучения
            train_start = end_date - timedelta(days=train_period_days)
            
            # Здесь должна быть логика получения исторических данных за период обучения
            historical_data = await self.data_provider.get_latest_data()
            
            # Обучение моделей
            await self.network_manager.train_models(historical_data)
            
            logger.info("Модели обучены для бэктестинга")
            
        except Exception as e:
            logger.error(f"Ошибка обучения моделей для бэктестинга: {e}")
            raise
    
    async def _run_backtest_day(self, date: datetime):
        """
        Выполнение бэктестинга за один день
        
        Args:
            date: Дата для бэктестинга
        """
        try:
            # Получение данных за день
            daily_data = await self._get_daily_data(date)
            if not daily_data:
                return
            
            # Анализ нейросетями
            predictions = await self.network_manager.analyze(daily_data)
            
            # Обновление торговых сигналов
            await self.trading_engine.update_predictions(predictions)
            
            # Получение торговых сигналов
            signals = await self.trading_engine.get_trading_signals()
            
            # Выполнение торговых операций
            if signals:
                await self.trading_engine.execute_trades(signals)
            
            # Обновление портфеля
            await self.portfolio_manager.update_portfolio()
            
            # Сохранение результатов дня
            await self._save_daily_results(date, predictions, signals)
            
        except Exception as e:
            logger.error(f"Ошибка бэктестинга за день {date}: {e}")
    
    async def _get_daily_data(self, date: datetime):
        """
        Получение данных за конкретный день
        
        Args:
            date: Дата
            
        Returns:
            Данные за день
        """
        try:
            # Здесь должна быть логика получения данных за конкретный день
            # Для упрощения используем текущие данные
            return await self.data_provider.get_latest_data()
            
        except Exception as e:
            logger.error(f"Ошибка получения данных за день {date}: {e}")
            return None
    
    async def _save_daily_results(self, date: datetime, predictions: dict, signals: list):
        """
        Сохранение результатов дня
        
        Args:
            date: Дата
            predictions: Предсказания нейросетей
            signals: Торговые сигналы
        """
        try:
            portfolio_metrics = await self.portfolio_manager.get_portfolio_metrics()
            
            daily_result = {
                'date': date.isoformat(),
                'portfolio_value': portfolio_metrics.total_value if portfolio_metrics else 0,
                'cash_balance': portfolio_metrics.cash_balance if portfolio_metrics else 0,
                'total_pnl': portfolio_metrics.total_pnl if portfolio_metrics else 0,
                'total_pnl_percent': portfolio_metrics.total_pnl_percent if portfolio_metrics else 0,
                'signals_count': len(signals),
                'predictions': predictions.get('ensemble_prediction', {}),
                'positions_count': len(await self.portfolio_manager.get_positions())
            }
            
            self.backtest_results.append(daily_result)
            
        except Exception as e:
            logger.error(f"Ошибка сохранения результатов дня {date}: {e}")
    
    async def _analyze_backtest_results(self):
        """
        Анализ результатов бэктестинга
        """
        try:
            logger.info("Анализ результатов бэктестинга")
            
            if not self.backtest_results:
                logger.warning("Нет результатов бэктестинга для анализа")
                return
            
            # Создание DataFrame с результатами
            df = pd.DataFrame(self.backtest_results)
            
            # Расчет метрик
            initial_value = df['portfolio_value'].iloc[0]
            final_value = df['portfolio_value'].iloc[-1]
            total_return = (final_value - initial_value) / initial_value * 100
            
            max_value = df['portfolio_value'].max()
            min_value = df['portfolio_value'].min()
            max_drawdown = (max_value - min_value) / max_value * 100
            
            volatility = df['portfolio_value'].pct_change().std() * np.sqrt(252) * 100
            
            # Коэффициент Шарпа (предполагаем безрисковую ставку = 0)
            returns = df['portfolio_value'].pct_change().dropna()
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
            
            # Вывод результатов
            logger.info("=== РЕЗУЛЬТАТЫ БЭКТЕСТИНГА ===")
            logger.info(f"Начальная стоимость портфеля: {initial_value:,.2f} руб.")
            logger.info(f"Конечная стоимость портфеля: {final_value:,.2f} руб.")
            logger.info(f"Общая доходность: {total_return:.2f}%")
            logger.info(f"Максимальная просадка: {max_drawdown:.2f}%")
            logger.info(f"Волатильность: {volatility:.2f}%")
            logger.info(f"Коэффициент Шарпа: {sharpe_ratio:.2f}")
            logger.info(f"Количество торговых дней: {len(df)}")
            
            # Сохранение результатов в файл
            results_file = Path("backtest_results.csv")
            df.to_csv(results_file, index=False)
            logger.info(f"Результаты сохранены в {results_file}")
            
        except Exception as e:
            logger.error(f"Ошибка анализа результатов бэктестинга: {e}")


async def main():
    """
    Основная функция для запуска бэктестинга
    """
    try:
        # Создание движка бэктестинга
        backtest_engine = BacktestEngine("config/main.yaml")
        await backtest_engine.initialize()
        
        # Параметры бэктестинга
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        train_period_days = 365
        
        # Запуск бэктестинга
        await backtest_engine.run_backtest(start_date, end_date, train_period_days)
        
    except Exception as e:
        logger.error(f"Ошибка в основной программе бэктестинга: {e}")


if __name__ == "__main__":
    # Настройка логирования
    logger.add(
        "logs/backtesting.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    
    # Запуск бэктестинга
    asyncio.run(main())

