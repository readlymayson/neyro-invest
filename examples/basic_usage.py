"""
Пример базового использования системы нейросетевых инвестиций
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавление корневой директории в путь
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.core.investment_system import InvestmentSystem
from loguru import logger


async def main():
    """
    Основная функция для запуска системы инвестиций
    """
    try:
        logger.info("Запуск системы нейросетевых инвестиций")
        
        # Инициализация системы
        system = InvestmentSystem("config/main.yaml")
        
        # Запуск торговой системы
        await system.start_trading()
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Ошибка в основной программе: {e}")
    finally:
        logger.info("Система остановлена")


if __name__ == "__main__":
    # Настройка логирования
    logger.add(
        "logs/basic_usage.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    
    # Запуск системы
    asyncio.run(main())

