"""
Пример бэктестинга торговых стратегий
"""

import asyncio
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns

# Добавление корневой директории в путь
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.data.data_provider import DataProvider
from src.neural_networks.network_manager import NetworkManager
from src.neural_networks.simple_signal_generator import SimpleSignalGenerator
from src.trading.trading_engine import TradingEngine, TradingSignal
from src.portfolio.portfolio_manager import PortfolioManager
from src.utils.config_manager import ConfigManager
from loguru import logger


class BacktestEngine:
    """
    Движок для бэктестинга торговых стратегий
    """
    
    def __init__(self, config_path: str = "config/backtest.yaml"):
        """
        Инициализация движка бэктестинга
        
        Args:
            config_path: Путь к конфигурационному файлу для бэктеста
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Компоненты системы
        self.data_provider = None
        self.network_manager = None
        self.simple_generator = None
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
        
        # Инициализация простого генератора сигналов
        simple_config = self.config['neural_networks']['models'][0]['config']
        self.simple_generator = SimpleSignalGenerator(simple_config)
        
        # Перезагрузка конфигурации для бэктеста
        from src.utils.config_manager import ConfigManager
        config_manager = ConfigManager('config/backtest.yaml')
        self.config = config_manager.get_config()
        
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
            
            # Создаем исторические данные для обучения
            training_data = {}
            symbols = self.config['data'].get('symbols', ['SBER', 'GAZP', 'LKOH'])
            
            for symbol in symbols:
                # Генерируем исторические данные для обучения
                base_price = 100.0  # Базовая цена
                prices = []
                
                for i in range(train_period_days):
                    # Генерируем цену с трендом и случайными колебаниями
                    trend = np.sin(i / 30) * 0.1  # Синусоидальный тренд
                    noise = np.random.normal(0, 0.02)  # Случайные колебания
                    price = base_price * (1 + trend + noise)
                    prices.append(price)
                
                training_data[symbol] = {
                    'prices': prices,
                    'volume': [np.random.randint(100000, 1000000) for _ in range(train_period_days)],
                    'symbol': symbol
                }
            
            # Обучение моделей
            await self.network_manager.train_models(training_data)
            
            logger.info("Модели обучены для бэктестинга")
            
        except Exception as e:
            logger.error(f"Ошибка обучения моделей для бэктестинга: {e}")
            # Продолжаем бэктест даже если обучение не удалось
            logger.warning("Продолжаем бэктест без обученных моделей")
    
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
            
            # Анализ нейросетями (с обработкой ошибок)
            predictions = {}
            try:
                predictions = await self.network_manager.analyze(daily_data, self.portfolio_manager)
                logger.debug(f"Нейросети вернули {len(predictions)} сигналов за {date}: {predictions}")
            except Exception as e:
                logger.warning(f"Ошибка анализа нейросетей за {date}: {e}")
            
            # Если нейросети не вернули сигналов, генерируем простые
            if not predictions or not predictions.get('ensemble_predictions') or len(predictions.get('ensemble_predictions', {})) == 0:
                logger.info(f"Нейросети не вернули сигналов за {date}, генерируем простые")
                predictions = await self._generate_simple_signals(daily_data)
                logger.info(f"Сгенерировано {len(predictions.get('ensemble_predictions', {}))} простых сигналов для {date}")
            else:
                logger.info(f"Используем сигналы от нейросетей: {predictions}")
            
            # Обновление торговых сигналов
            await self.trading_engine.update_predictions(predictions)
            
            # Получение торговых сигналов
            signals = await self.trading_engine.get_trading_signals()
            logger.debug(f"Получено {len(signals)} торговых сигналов за {date}")
            
            # Выполнение торговых операций
            if signals:
                await self.trading_engine.execute_trades(signals)
            
            # Обновление портфеля с историческими ценами
            # Извлекаем цены из daily_data для передачи в портфель
            historical_prices = {}
            for symbol, data in daily_data.items():
                if isinstance(data, dict) and 'price' in data:
                    historical_prices[symbol] = data['price']
            
            # Устанавливаем исторические цены в портфель
            self.portfolio_manager.set_backtest_prices(historical_prices)
            
            # Обновление портфеля
            await self.portfolio_manager.update_portfolio()
            
            # Сохранение результатов дня
            await self._save_daily_results(date, predictions, signals)
            
        except Exception as e:
            logger.error(f"Ошибка бэктестинга за день {date}: {e}")
    
    async def _generate_simple_signals(self, daily_data: dict) -> dict:
        """
        Генерация простых сигналов на основе случайности
        
        Args:
            daily_data: Данные за день
            
        Returns:
            Словарь с сигналами в правильном формате для trading_engine
        """
        return self.simple_generator.generate_signals(daily_data)
    
    async def _get_daily_data(self, date: datetime):
        """
        Получение данных за конкретный день
        
        Args:
            date: Дата
            
        Returns:
            Данные за день
        """
        try:
            # Для бэктестинга генерируем mock данные с историческими ценами
            symbols = self.config['data'].get('symbols', ['SBER', 'GAZP', 'LKOH', 'NVTK'])
            
            # Базовые цены для каждого символа (реалистичные значения)
            base_prices = {
                'SBER': 200.0,
                'GAZP': 150.0,
                'LKOH': 6000.0,
                'NVTK': 1500.0,
                'GMKN': 15000.0,
                'MGNT': 12000.0,
                'MOEX': 1500.0,
                'RTKM': 800.0,
                'AFLT': 50.0,
                'MTLR': 3000.0
            }
            
            # Создаем исторические данные с учетом даты
            historical_data = {}
            for symbol in symbols:
                base_price = base_prices.get(symbol, 100.0)
                
                # Добавляем тренд и случайные колебания на основе даты
                days_from_start = (date - datetime(2023, 1, 1)).days
                trend_factor = 1 + (days_from_start * 0.00005)  # Очень слабый тренд (0.005% в день)
                volatility = np.random.normal(0, 0.01)  # 1% волатильность (снижено с 2%)
                
                price = base_price * trend_factor * (1 + volatility)
                
                # Ограничиваем цену разумными пределами
                price = max(price, base_price * 0.5)  # Минимум 50% от базовой цены
                price = min(price, base_price * 2.0)  # Максимум 200% от базовой цены
                
                historical_data[symbol] = {
                    'price': round(price, 2),
                    'volume': np.random.randint(1000, 10000),
                    'change': round(volatility * 100, 2),
                    'timestamp': date.isoformat()
                }
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Ошибка генерации данных за {date}: {e}")
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
            positions = await self.portfolio_manager.get_positions()
            
            # Создание словаря позиций по символам
            positions_by_symbol = {}
            for position in positions:
                positions_by_symbol[position.symbol] = {
                    'quantity': position.quantity,
                    'average_price': position.average_price,
                    'current_price': position.current_price,
                    'unrealized_pnl': position.unrealized_pnl,
                    'market_value': position.market_value
                }
            
            daily_result = {
                'date': date.isoformat(),
                'portfolio_value': portfolio_metrics.total_value if portfolio_metrics else 0,
                'cash_balance': portfolio_metrics.cash_balance if portfolio_metrics else 0,
                'total_pnl': portfolio_metrics.total_pnl if portfolio_metrics else 0,
                'total_pnl_percent': portfolio_metrics.total_pnl_percent if portfolio_metrics else 0,
                'signals_count': len(signals),
                'predictions': predictions.get('ensemble_prediction', {}),
                'positions_count': len(positions),
                'positions_by_symbol': positions_by_symbol
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
            
            # Сохранение результатов в файл с уникальным именем в папке графиков
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            charts_dir = Path(f"backtest_charts_{timestamp}")
            charts_dir.mkdir(exist_ok=True)
            results_file = charts_dir / f"backtest_results_{timestamp}.csv"
            df.to_csv(results_file, index=False)
            logger.info(f"Результаты сохранены в {results_file}")
            
        except Exception as e:
            logger.error(f"Ошибка анализа результатов бэктестинга: {e}")
    
    async def _create_symbol_charts(self):
        """
        Создание графиков для каждого символа
        """
        try:
            logger.info("Создание графиков для символов")
            
            if not self.backtest_results:
                logger.warning("Нет результатов для создания графиков")
                return
            
            # Создание DataFrame с результатами
            df = pd.DataFrame(self.backtest_results)
            df['date'] = pd.to_datetime(df['date'])
            
            # Получение списка символов из конфигурации
            symbols = self.config.get('data', {}).get('symbols', [])
            
            if not symbols:
                logger.warning("Нет символов в конфигурации для создания графиков")
                return
            
            # Создание папки для графиков с временной меткой
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            charts_dir = Path(f"backtest_charts_{timestamp}")
            charts_dir.mkdir(exist_ok=True)
            
            # Настройка стиля графиков
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
            
            # Создание PDF файла для графиков с уникальным именем
            pdf_file = charts_dir / f"backtest_symbols_charts_{timestamp}.pdf"
            
            with PdfPages(pdf_file) as pdf:
                # График общей стоимости портфеля
                fig, ax = plt.subplots(figsize=(12, 8))
                ax.plot(df['date'], df['portfolio_value'], linewidth=2, label='Стоимость портфеля')
                ax.set_title('Общая стоимость портфеля', fontsize=16, fontweight='bold')
                ax.set_xlabel('Дата', fontsize=12)
                ax.set_ylabel('Стоимость (руб.)', fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                # Форматирование оси X
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
                plt.xticks(rotation=45)
                
                plt.tight_layout()
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()
                
                # Графики для каждого символа
                for symbol in symbols:
                    await self._create_symbol_chart(symbol, df, pdf, charts_dir, timestamp)
            
            logger.info(f"Графики сохранены в {pdf_file}")
            
        except Exception as e:
            logger.error(f"Ошибка создания графиков: {e}")
    
    async def _create_symbol_chart(self, symbol: str, df: pd.DataFrame, pdf: PdfPages, charts_dir: Path, timestamp: str):
        """
        Создание графика для конкретного символа
        """
        try:
            # Получение данных о позициях по символу
            symbol_data = []
            
            for result in self.backtest_results:
                date = pd.to_datetime(result['date'])
                
                # Получение позиции по символу на эту дату из сохраненных данных
                positions_by_symbol = result.get('positions_by_symbol', {})
                symbol_position = positions_by_symbol.get(symbol)
                
                if symbol_position and symbol_position['quantity'] > 0:
                    symbol_data.append({
                        'date': date,
                        'quantity': symbol_position['quantity'],
                        'avg_price': symbol_position['average_price'],
                        'current_price': symbol_position['current_price'],
                        'unrealized_pnl': symbol_position['unrealized_pnl'],
                        'market_value': symbol_position['market_value']
                    })
                else:
                    # Если позиции нет, добавляем нулевые значения
                    symbol_data.append({
                        'date': date,
                        'quantity': 0,
                        'avg_price': 0,
                        'current_price': 0,
                        'unrealized_pnl': 0,
                        'market_value': 0
                    })
            
            if not symbol_data:
                return
            
            symbol_df = pd.DataFrame(symbol_data)
            
            # Создание графика с двумя подграфиками
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # График 1: Цена символа и количество акций
            ax1_twin = ax1.twinx()
            
            # Цена символа
            ax1.plot(symbol_df['date'], symbol_df['current_price'], 
                    color='blue', linewidth=2, label=f'Цена {symbol}')
            ax1.set_ylabel('Цена (руб.)', color='blue', fontsize=12)
            ax1.tick_params(axis='y', labelcolor='blue')
            
            # Количество акций
            ax1_twin.bar(symbol_df['date'], symbol_df['quantity'], 
                        alpha=0.6, color='orange', label=f'Количество {symbol}')
            ax1_twin.set_ylabel('Количество акций', color='orange', fontsize=12)
            ax1_twin.tick_params(axis='y', labelcolor='orange')
            
            ax1.set_title(f'Символ {symbol}: Цена и позиция', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            
            # График 2: Прибыль/убыток
            ax2.plot(symbol_df['date'], symbol_df['unrealized_pnl'], 
                    color='green', linewidth=2, label='Нереализованная прибыль')
            ax2.plot(symbol_df['date'], symbol_df['market_value'], 
                    color='purple', linewidth=2, label='Рыночная стоимость позиции')
            
            ax2.set_title(f'Символ {symbol}: Прибыль/убыток', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Дата', fontsize=12)
            ax2.set_ylabel('Стоимость (руб.)', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            
            # Форматирование оси X для обоих графиков
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
                ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Сохранение в PDF
            pdf.savefig(fig, bbox_inches='tight')
            
            plt.close()
            
            logger.debug(f"Создан график для символа {symbol}")
            
        except Exception as e:
            logger.error(f"Ошибка создания графика для символа {symbol}: {e}")


async def main():
    """
    Основная функция для запуска бэктестинга
    """
    try:
        logger.info("Запуск бэктестинга с конфигурацией backtest.yaml")
        
        # Создание движка бэктестинга с новым конфигом
        backtest_engine = BacktestEngine("config/backtest.yaml")
        await backtest_engine.initialize()
        
        # Параметры бэктестинга из конфига
        backtest_config = backtest_engine.config.get('backtest', {})
        default_period = backtest_config.get('default_period', {})
        
        # Даты из конфига или по умолчанию
        if default_period.get('start_date') and default_period.get('end_date'):
            start_date = datetime.strptime(default_period['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(default_period['end_date'], '%Y-%m-%d')
        else:
            # По умолчанию - последний год
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
        
        train_period_days = default_period.get('train_period_days', 180)
        
        logger.info(f"Период бэктестинга: {start_date.date()} - {end_date.date()}")
        logger.info(f"Период обучения: {train_period_days} дней")
        
        # Запуск бэктестинга
        await backtest_engine.run_backtest(start_date, end_date, train_period_days)
        
        # Создание графиков для символов
        await backtest_engine._create_symbol_charts()
        
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

