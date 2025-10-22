"""
Основной класс системы нейросетевых инвестиций
"""

from typing import Dict, List, Optional
from loguru import logger
import asyncio
from datetime import datetime

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
        
        # Инициализация менеджера портфеля
        await self.portfolio_manager.initialize()
        
        # Установка связей между компонентами
        self.trading_engine.set_components(self.data_provider, self.portfolio_manager)
        
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
                # Получение последних данных
                market_data = await self.data_provider.get_latest_data()
                
                # Анализ нейросетями
                predictions = await self.network_manager.analyze(market_data)
                
                # Передача предсказаний в торговый движок
                await self.trading_engine.update_predictions(predictions)
                
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

