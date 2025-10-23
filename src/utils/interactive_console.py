"""
Интерактивная консоль для управления системой
Позволяет выполнять команды в реальном времени
"""

import asyncio
import sys
import os
from typing import Optional
from loguru import logger
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.command_manager import CommandManager, CommandType

class InteractiveConsole:
    """
    Интерактивная консоль для управления системой
    """
    
    def __init__(self):
        self.command_manager = CommandManager()
        self.running = False
        self.system = None
        self.portfolio = None
    
    def set_system_components(self, system=None, portfolio=None):
        """Установка компонентов системы"""
        self.system = system
        self.portfolio = portfolio
        self.command_manager.set_system_components(system, portfolio)
        logger.info("Компоненты системы установлены в InteractiveConsole")
    
    async def start(self):
        """Запуск интерактивной консоли"""
        self.running = True
        
        print("\n" + "="*70)
        print("🚀 NEYRO-INVEST INTERACTIVE CONSOLE")
        print("="*70)
        print("💡 Введите 'help' для просмотра доступных команд")
        print("💡 Введите 'exit' или 'quit' для выхода")
        print("="*70)
        
        while self.running:
            try:
                # Получение команды от пользователя
                command_line = await self._get_user_input()
                
                if not command_line:
                    continue
                
                # Обработка специальных команд
                if command_line.lower() in ['exit', 'quit', 'q']:
                    await self._cmd_exit()
                    break
                
                # Выполнение команды
                success = await self.command_manager.execute_command(command_line)
                
                if not success:
                    print("❌ Команда не выполнена")
                
                print()  # Пустая строка для разделения
                
            except KeyboardInterrupt:
                print("\n⚠️  Прерывание пользователем")
                await self._cmd_exit()
                break
            except Exception as e:
                logger.error(f"Ошибка в интерактивной консоли: {e}")
                print(f"❌ Ошибка: {e}")
    
    async def _get_user_input(self) -> str:
        """Получение ввода от пользователя"""
        try:
            # Используем asyncio для неблокирующего ввода
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(None, input, "neyro-invest> ")
            return user_input.strip()
        except EOFError:
            return "exit"
        except Exception as e:
            logger.error(f"Ошибка получения ввода: {e}")
            return ""
    
    async def _cmd_exit(self):
        """Выход из консоли"""
        print("\n👋 Выход из интерактивной консоли...")
        self.running = False
    
    def stop(self):
        """Остановка консоли"""
        self.running = False

async def start_interactive_console(system=None, broker=None, portfolio=None):
    """
    Запуск интерактивной консоли
    
    Args:
        system: Экземпляр системы
        broker: Экземпляр брокера
        portfolio: Экземпляр портфеля
    """
    console = InteractiveConsole()
    console.set_system_components(system, portfolio)
    await console.start()

if __name__ == "__main__":
    # Запуск консоли без системы (для тестирования)
    asyncio.run(start_interactive_console())
