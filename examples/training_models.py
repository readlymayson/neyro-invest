"""
Пример обучения нейросетей на исторических данных
"""

import asyncio
import sys
import os
from pathlib import Path
import pandas as pd

# Добавление корневой директории в путь
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.data.data_provider import DataProvider
from src.neural_networks.network_manager import NetworkManager
from src.utils.config_manager import ConfigManager
from loguru import logger


async def train_models():
    """
    Обучение нейросетей на исторических данных
    """
    try:
        logger.info("Начало обучения нейросетей")
        
        # Загрузка конфигурации
        config_manager = ConfigManager("config/main.yaml")
        config = config_manager.get_config()
        
        # Инициализация провайдера данных
        data_provider = DataProvider(config['data'])
        await data_provider.initialize()
        
        # Получение исторических данных
        logger.info("Загрузка исторических данных")
        historical_data = await data_provider.get_latest_data()
        
        # Инициализация менеджера нейросетей
        network_manager = NetworkManager(config['neural_networks'])
        await network_manager.initialize()
        
        # Обучение моделей
        logger.info("Обучение нейросетей")
        await network_manager.train_models(historical_data)
        
        # Тестирование моделей
        logger.info("Тестирование обученных моделей")
        test_results = await network_manager.analyze(historical_data)
        
        logger.info("Результаты тестирования:")
        logger.info(f"Ансамблевое предсказание: {test_results.get('ensemble_prediction', {})}")
        
        # Сохранение моделей
        logger.info("Сохранение обученных моделей")
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        for model_name, model in network_manager.models.items():
            if model.is_trained:
                model.save_model(str(models_dir))
                logger.info(f"Модель {model_name} сохранена")
        
        logger.info("Обучение нейросетей завершено успешно")
        
    except Exception as e:
        logger.error(f"Ошибка обучения нейросетей: {e}")
        raise


async def test_single_model():
    """
    Тестирование одной модели
    """
    try:
        logger.info("Тестирование отдельной модели")
        
        # Загрузка конфигурации
        config_manager = ConfigManager("config/main.yaml")
        config = config_manager.get_config()
        
        # Инициализация провайдера данных
        data_provider = DataProvider(config['data'])
        await data_provider.initialize()
        
        # Получение данных для тестирования
        historical_data = await data_provider.get_latest_data()
        
        # Тестирование LSTM модели
        from src.neural_networks.lstm_network import LSTMNetwork
        
        lstm_config = {
            'sequence_length': 60,
            'lstm_units': [50, 50],
            'dropout_rate': 0.2,
            'learning_rate': 0.001,
            'batch_size': 32,
            'epochs': 50
        }
        
        lstm_model = LSTMNetwork("test_lstm", lstm_config)
        await lstm_model.initialize()
        
        # Обучение модели
        if historical_data.get('historical'):
            for symbol, data in historical_data['historical'].items():
                if not data.empty:
                    logger.info(f"Обучение модели на данных {symbol}")
                    metrics = await lstm_model.train(data)
                    logger.info(f"Метрики обучения: {metrics}")
                    
                    # Тестирование предсказания
                    prediction = await lstm_model.predict(data.tail(100))
                    logger.info(f"Предсказание: {prediction}")
                    break
        
        logger.info("Тестирование модели завершено")
        
    except Exception as e:
        logger.error(f"Ошибка тестирования модели: {e}")
        raise


if __name__ == "__main__":
    # Настройка логирования
    logger.add(
        "logs/training.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    
    # Выбор режима
    import argparse
    
    parser = argparse.ArgumentParser(description="Обучение нейросетей")
    parser.add_argument("--mode", choices=["train", "test"], default="train", 
                       help="Режим работы: train - обучение всех моделей, test - тестирование одной модели")
    
    args = parser.parse_args()
    
    if args.mode == "train":
        asyncio.run(train_models())
    else:
        asyncio.run(test_single_model())

