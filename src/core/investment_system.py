"""
Основной класс системы нейросетевых инвестиций
"""

from typing import Dict, List, Optional
from loguru import logger
import asyncio
from datetime import datetime
import json
from pathlib import Path

from ..data.data_provider import DataProvider
from ..neural_networks.network_manager import NetworkManager
from ..trading.trading_engine import TradingEngine
from ..portfolio.portfolio_manager import PortfolioManager
from ..utils.config_manager import ConfigManager


class InvestmentSystem:
    """
    Основная система нейросетевых инвестиций
    """
    
    def __init__(self, config_path: str = "config/main.yaml"):
        """
        Инициализация системы инвестиций
        
        Args:
            config_path: Путь к конфигурационному файлу
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Инициализация компонентов
        self.data_provider = DataProvider(self.config['data'])
        self.network_manager = NetworkManager(self.config['neural_networks'])
        self.trading_engine = TradingEngine(self.config['trading'])
        self.portfolio_manager = PortfolioManager(self.config['portfolio'])
        
        self.is_running = False
        self.tasks: List[asyncio.Task] = []
        
        logger.info("Система инвестиций инициализирована")
    
    async def initialize_components(self):
        """
        Инициализация компонентов системы (для интерактивного режима)
        """
        logger.info("Инициализация компонентов для интерактивного режима")
        await self._initialize_components()
        logger.info("Компоненты готовы для интерактивного режима")
    
    async def start_trading(self):
        """
        Запуск торговой системы
        """
        if self.is_running:
            logger.warning("Торговая система уже запущена")
            return
        
        self.is_running = True
        logger.info("Запуск торговой системы")
        
        try:
            # Инициализация компонентов
            await self._initialize_components()
            
            # Запуск основных задач
            await self._start_main_tasks()
            
            # Ожидание завершения
            await asyncio.gather(*self.tasks)
            
        except Exception as e:
            logger.error(f"Ошибка в торговой системе: {e}")
            await self.stop_trading()
    
    async def stop_trading(self):
        """
        Остановка торговой системы
        """
        if not self.is_running:
            return
        
        logger.info("Остановка торговой системы")
        self.is_running = False
        
        # Отмена всех задач
        for task in self.tasks:
            task.cancel()
        
        # Ожидание завершения задач
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("Торговая система остановлена")
    
    async def _initialize_components(self):
        """
        Инициализация всех компонентов системы
        """
        logger.info("Инициализация компонентов системы")
        
        # Инициализация провайдера данных
        await self.data_provider.initialize()
        
        # Инициализация нейросетей
        await self.network_manager.initialize()
        
        # Инициализация торгового движка
        await self.trading_engine.initialize()
        
        # Установка списка символов в торговый движок
        symbols = self.config['data'].get('symbols', [])
        self.trading_engine.set_symbols(symbols)
        
        # Инициализация менеджера портфеля
        await self.portfolio_manager.initialize()
        
        # Установка связей между компонентами
        self.trading_engine.set_components(self.data_provider, self.portfolio_manager)
        self.portfolio_manager.set_data_provider(self.data_provider)
        
        # Установка T-Bank брокера в PortfolioManager для синхронизации
        if hasattr(self.trading_engine, 'tbank_broker') and self.trading_engine.tbank_broker:
            self.portfolio_manager.set_tbank_broker(self.trading_engine.tbank_broker)
            # Синхронизация с T-Bank при инициализации
            await self.portfolio_manager.sync_with_tbank()
        
        logger.info("Все компоненты инициализированы")
    
    async def _start_main_tasks(self):
        """
        Запуск основных задач системы
        """
        # Задача обновления данных
        self.tasks.append(
            asyncio.create_task(self._data_update_loop())
        )
        
        # Задача анализа нейросетями
        self.tasks.append(
            asyncio.create_task(self._analysis_loop())
        )
        
        # Задача торговли
        self.tasks.append(
            asyncio.create_task(self._trading_loop())
        )
        
        # Задача управления портфелем
        self.tasks.append(
            asyncio.create_task(self._portfolio_loop())
        )
        
        # Задача экспорта данных для GUI
        self.tasks.append(
            asyncio.create_task(self._export_loop())
        )
        
        logger.info("Основные задачи запущены")
    
    async def _data_update_loop(self):
        """
        Цикл обновления данных
        """
        while self.is_running:
            try:
                await self.data_provider.update_market_data()
                await asyncio.sleep(self.config['data']['update_interval'])
            except Exception as e:
                logger.error(f"Ошибка обновления данных: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
    
    async def _analysis_loop(self):
        """
        Цикл анализа нейросетями
        """
        while self.is_running:
            try:
                logger.info("🔄 Начало цикла анализа нейросетями")
                
                # Получение последних данных
                market_data = await self.data_provider.get_latest_data()
                
                # Получение новостных данных
                news_data = market_data.get('news', {})
                logger.info(f"📰 Получены новостные данные для {len(news_data)} символов")
                
                # Анализ нейросетями с портфельными и новостными данными
                predictions = await self.network_manager.analyze(market_data, self.portfolio_manager, news_data)
                
                # Передача предсказаний в торговый движок
                await self.trading_engine.update_predictions(predictions)
                
                # Экспорт сигналов после обновления предсказаний
                await self._export_signals_data()
                
                logger.info(f"✅ Цикл анализа завершен, следующий через {self.config['neural_networks']['analysis_interval']} сек")
                await asyncio.sleep(self.config['neural_networks']['analysis_interval'])
            except Exception as e:
                logger.error(f"Ошибка анализа: {e}")
                await asyncio.sleep(60)
    
    async def _trading_loop(self):
        """
        Цикл торговли
        """
        while self.is_running:
            try:
                # Получение торговых сигналов
                signals = await self.trading_engine.get_trading_signals()
                
                # Выполнение торговых операций
                if signals:
                    await self.trading_engine.execute_trades(signals)
                
                await asyncio.sleep(self.config['trading']['signal_check_interval'])
            except Exception as e:
                logger.error(f"Ошибка торговли: {e}")
                await asyncio.sleep(60)
    
    async def _portfolio_loop(self):
        """
        Цикл управления портфелем
        """
        while self.is_running:
            try:
                # Обновление состояния портфеля
                await self.portfolio_manager.update_portfolio()
                
                # Проверка рисков
                await self.portfolio_manager.check_risks()
                
                await asyncio.sleep(self.config['portfolio']['update_interval'])
            except Exception as e:
                logger.error(f"Ошибка управления портфелем: {e}")
                await asyncio.sleep(60)
    
    async def _export_loop(self):
        """
        Цикл экспорта данных для GUI
        """
        while self.is_running:
            try:
                # Экспорт данных портфеля
                await self._export_portfolio_data()
                
                # Экспорт торговых сигналов
                await self._export_signals_data()
                
                # Экспорт каждые 10 секунд
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Ошибка экспорта данных: {e}")
                await asyncio.sleep(30)
    
    async def _export_portfolio_data(self):
        """Экспорт данных портфеля в JSON"""
        try:
            # Создание директории data если её нет
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            # Получение данных портфеля
            portfolio_data = {
                'total_value': self.portfolio_manager.cash_balance + sum(
                    pos.market_value for pos in self.portfolio_manager.positions.values()
                ),
                'cash_balance': self.portfolio_manager.cash_balance,
                'positions': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Добавление позиций
            for symbol, position in self.portfolio_manager.positions.items():
                portfolio_data['positions'][symbol] = {
                    'quantity': position.quantity,
                    'price': position.current_price,
                    'value': position.market_value,
                    'pnl': position.unrealized_pnl,
                    'pnl_percent': position.unrealized_pnl_percent
                }
            
            # Сохранение в файл
            portfolio_file = data_dir / "portfolio.json"
            with open(portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(portfolio_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Данные портфеля экспортированы: {portfolio_data['total_value']:.2f}")
            
        except Exception as e:
            logger.error(f"Ошибка экспорта данных портфеля: {e}")
    
    async def _export_signals_data(self):
        """Экспорт торговых сигналов в JSON"""
        try:
            # Создание директории data если её нет
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            # Получение ВСЕХ торговых сигналов (не только для выполнения)
            all_signals = self.trading_engine.trading_signals
            logger.info(f"📊 Экспорт сигналов: найдено {len(all_signals)} сигналов")
            
            signals_data = []
            if all_signals:
                for signal in all_signals.values():
                    signals_data.append({
                        'time': signal.timestamp.strftime("%H:%M:%S"),
                        'symbol': signal.symbol,
                        'signal': signal.signal,
                        'confidence': float(signal.confidence),  # Конвертация в обычный float
                        'action': f"Сигнал: {signal.signal}",
                        'price': float(signal.price) if signal.price else 0.0,
                        'strength': float(signal.strength),
                        'source': signal.source,
                        'reasoning': signal.reasoning
                    })
                    logger.debug(f"📊 Экспорт сигнала: {signal.symbol} {signal.signal} ({signal.timestamp.strftime('%H:%M:%S')})")
            
            # Загрузка существующих сигналов
            signals_file = data_dir / "signals.json"
            existing_signals = []
            if signals_file.exists():
                try:
                    with open(signals_file, 'r', encoding='utf-8') as f:
                        existing_signals = json.load(f)
                        # Добавляем поле reasoning к старым сигналам, если его нет
                        for signal in existing_signals:
                            if 'reasoning' not in signal:
                                signal['reasoning'] = ""
                except:
                    existing_signals = []
            
            # Добавление новых сигналов
            existing_signals.extend(signals_data)
            
            # Храним только последние 50 сигналов
            existing_signals = existing_signals[-50:]
            
            # Сохранение в файл
            with open(signals_file, 'w', encoding='utf-8') as f:
                json.dump(existing_signals, f, ensure_ascii=False, indent=2)
            
            if signals_data:
                logger.info(f"✅ Экспортировано {len(signals_data)} новых сигналов в signals.json")
            else:
                logger.debug("ℹ️ Нет новых сигналов для экспорта")
            
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта торговых сигналов: {e}")
    
    def get_system_status(self) -> Dict:
        """
        Получение статуса системы
        
        Returns:
            Словарь со статусом всех компонентов
        """
        return {
            'is_running': self.is_running,
            'data_provider': self.data_provider.get_status(),
            'network_manager': self.network_manager.get_status(),
            'trading_engine': self.trading_engine.get_status(),
            'portfolio_manager': self.portfolio_manager.get_status(),
            'timestamp': datetime.now().isoformat()
        }

