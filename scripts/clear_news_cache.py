# -*- coding: utf-8 -*-
"""
Скрипт для сброса кеша новостей символов
"""

import sys
import os
from pathlib import Path

# Добавление корневой директории в путь
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from loguru import logger
from src.utils.config_manager import ConfigManager
from src.data.news_data_provider import NewsDataProvider


async def clear_news_cache():
    """
    Сброс кеша новостей для всех символов
    """
    try:
        logger.info("🔄 Начало сброса кеша новостей")
        
        # Загрузка конфигурации
        config_manager = ConfigManager("config/main.yaml")
        config = config_manager.get_config()
        
        # Инициализация провайдера новостей
        news_config = config.get('data', {}).get('news', {})
        if not news_config.get('enabled', False):
            logger.warning("Новостные данные отключены в конфигурации")
            return
        
        news_provider = NewsDataProvider(news_config)
        
        # Очистка кеша в основном провайдере
        cache_size_before = len(news_provider.cache)
        news_provider.cache.clear()
        logger.info(f"✅ Очищен кеш основного провайдера: удалено {cache_size_before} записей")
        
        # Очистка кеша в каждом провайдере
        total_cleared = cache_size_before
        for provider in news_provider.providers:
            if hasattr(provider, 'cache'):
                provider_cache_size = len(provider.cache)
                provider.cache.clear()
                total_cleared += provider_cache_size
                logger.info(f"✅ Очищен кеш провайдера {type(provider).__name__}: удалено {provider_cache_size} записей")
        
        logger.info(f"✅ Кеш новостей успешно сброшен. Всего удалено записей: {total_cleared}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при сбросе кеша новостей: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(clear_news_cache())

