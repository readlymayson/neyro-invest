"""
Конфигурация логирования для системы Neyro-Invest
Обеспечивает правильную кодировку UTF-8 для всех логов
"""

import sys
from pathlib import Path
from loguru import logger

def setup_logging():
    """Настройка логирования с поддержкой UTF-8"""
    
    # Удаляем стандартные обработчики
    logger.remove()
    
    # Настройка для консоли с UTF-8
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # Настройка для файлов логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Основной лог файл
    logger.add(
        log_dir / "system.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    # Лог для торговли
    logger.add(
        log_dir / "trading.log",
        rotation="5 MB",
        retention="3 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        filter=lambda record: "trading" in record["name"].lower() or "broker" in record["name"].lower(),
        delay=True  # Файл создается только при первой записи, проходящей через фильтр
    )
    
    # Лог для нейросетей
    logger.add(
        log_dir / "neural_networks.log",
        rotation="5 MB",
        retention="3 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        filter=lambda record: "neural" in record["name"].lower() or "network" in record["name"].lower(),
        delay=True  # Файл создается только при первой записи, проходящей через фильтр
    )
    
    logger.info("Логирование настроено с поддержкой UTF-8")

def setup_web_logging():
    """Настройка логирования для веб-приложения"""
    
    # Удаляем стандартные обработчики
    logger.remove()
    
    # Настройка для консоли
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # Настройка для файла веб-логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "web_application.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    logger.info("Веб-логирование настроено с поддержкой UTF-8")
