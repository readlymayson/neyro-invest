"""
Сервис для работы с T-Bank API
Централизованное управление подключением и получением данных
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from loguru import logger

try:
    from tinkoff.invest import AsyncClient
    from ..trading.tbank_broker import TBankBroker
    TINKOFF_AVAILABLE = True
except ImportError as e:
    TINKOFF_AVAILABLE = False
    logger.warning(f"Tinkoff Invest API недоступен: {e}")


class TBankService:
    """Сервис для работы с T-Bank API"""
    
    def __init__(self):
        self.broker: Optional[TBankBroker] = None
        self.is_connected = False
        self.last_update = None
        
    async def connect(self, token: str, sandbox: bool = True) -> Dict[str, Any]:
        """
        Подключение к T-Bank API
        
        Args:
            token: Токен T-Bank
            sandbox: Режим песочницы
            
        Returns:
            Результат подключения
        """
        try:
            if not TINKOFF_AVAILABLE:
                return {
                    "success": False,
                    "error": "Tinkoff Invest API недоступен"
                }
            
            # Создаем брокера
            self.broker = TBankBroker(token=token, sandbox=sandbox)
            await self.broker.initialize()
            
            # Получаем статус
            status = self.broker.get_status()
            balance = await self.broker.get_total_balance_rub()
            
            self.is_connected = True
            self.last_update = datetime.now()
            
            logger.info(f"T-Bank подключен: {status.get('account_id')}")
            
            return {
                "success": True,
                "mode": "sandbox" if sandbox else "production",
                "account_id": status.get("account_id"),
                "balance": balance,
                "instruments": status.get("instruments_loaded", 0)
            }
            
        except Exception as e:
            logger.error(f"Ошибка подключения к T-Bank: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_portfolio_data(self) -> Dict[str, Any]:
        """
        Получение данных портфеля
        
        Returns:
            Данные портфеля
        """
        if not self.is_connected or not self.broker:
            return {
                "error": "Не подключен к T-Bank",
                "mode": "disconnected"
            }
        
        try:
            # Получаем баланс
            balance = await self.broker.get_total_balance_rub()
            
            # Получаем портфель
            portfolio = await self.broker.get_portfolio()
            
            # Обрабатываем данные
            total_value = balance
            invested_value = 0
            total_pnl = 0
            positions_list = []
            
            # Обрабатываем позиции из портфеля
            for position in portfolio.get('positions', []):
                ticker = position.get('ticker', '')
                quantity = position.get('quantity', 0)
                
                # Пропускаем позиции без тикера или с нулевым количеством
                if not ticker or quantity <= 0:
                    continue
                    
                value = position.get('value', 0)
                pnl = position.get('pnl', 0)
                
                invested_value += value
                total_pnl += pnl
                
                positions_list.append({
                    "symbol": ticker,
                    "name": ticker,
                    "quantity": quantity,
                    "avg_price": position.get('avg_price', 0),
                    "current_price": position.get('current_price', 0),
                    "value": value,
                    "pnl": pnl,
                    "pnl_percent": position.get('pnl_percent', 0),
                    "weight_percent": (value / (balance + invested_value) * 100) if (balance + invested_value) > 0 else 0
                })
            
            total_value = balance + invested_value
            total_pnl_percent = (total_pnl / invested_value * 100) if invested_value > 0 else 0
            
            self.last_update = datetime.now()
            
            return {
                "total_value": total_value,
                "cash_balance": balance,
                "invested_value": invested_value,
                "total_pnl": total_pnl,
                "total_pnl_percent": total_pnl_percent,
                "positions_count": len(positions_list),
                "positions": positions_list,
                "last_update": self.last_update.isoformat(),
                "mode": "real"
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения данных портфеля: {e}")
            return {
                "error": str(e),
                "mode": "error"
            }
    
    async def get_balance(self) -> Dict[str, Any]:
        """
        Получение баланса
        
        Returns:
            Данные баланса
        """
        if not self.is_connected or not self.broker:
            return {
                "error": "Не подключен к T-Bank"
            }
        
        try:
            balance = await self.broker.get_total_balance_rub()
            return {
                "balance": balance,
                "currency": "RUB"
            }
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return {
                "error": str(e)
            }
    
    def disconnect(self):
        """Отключение от T-Bank"""
        self.broker = None
        self.is_connected = False
        self.last_update = None
        logger.info("Отключен от T-Bank")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса подключения
        
        Returns:
            Статус сервиса
        """
        return {
            "connected": self.is_connected,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "broker_status": self.broker.get_status() if self.broker else None
        }


# Глобальный экземпляр сервиса
tbank_service = TBankService()


async def get_tbank_token_from_env() -> Optional[str]:
    """
    Получение токена T-Bank из переменных окружения
    
    Returns:
        Токен или None
    """
    # Проверяем переменные окружения
    token = os.getenv("TINKOFF_TOKEN")
    if token:
        return token
    
    # Проверяем .env файл
    env_file = Path(".env")
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith("TINKOFF_TOKEN="):
                        token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if token:
                            return token
        except Exception as e:
            logger.warning(f"Ошибка чтения .env файла: {e}")
    
    return None


async def auto_connect_tbank() -> bool:
    """
    Автоматическое подключение к T-Bank при запуске
    
    Returns:
        True если подключение успешно
    """
    try:
        token = await get_tbank_token_from_env()
        if not token:
            logger.info("T-Bank токен не найден, пропускаем автоматическое подключение")
            return False
        
        logger.info("Найден T-Bank токен, подключаемся...")
        result = await tbank_service.connect(token, sandbox=True)
        
        if result.get("success"):
            logger.info("T-Bank автоматически подключен")
            return True
        else:
            logger.warning(f"Не удалось автоматически подключиться к T-Bank: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.warning(f"Ошибка автоматического подключения к T-Bank: {e}")
        return False
