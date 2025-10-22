"""
Главное окно приложения
"""

import sys
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from loguru import logger
import threading
import queue

from ..core.investment_system import InvestmentSystem
from .dashboard_panel import DashboardPanel
from .trading_panel import TradingPanel
from .portfolio_panel import PortfolioPanel
from .config_panel import ConfigPanel
from .logs_panel import LogsPanel


class MainWindow:
    """
    Главное окно приложения
    """
    
    def __init__(self):
        """
        Инициализация главного окна
        """
        self.root = tk.Tk()
        self.root.title("Нейросетевая система инвестиций")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Система инвестиций
        self.investment_system: Optional[InvestmentSystem] = None
        self.system_running = False
        
        # Очередь для обновлений из асинхронных задач
        self.update_queue = queue.Queue()
        
        # Настройка стилей
        self._setup_styles()
        
        # Создание интерфейса
        self._create_menu()
        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()
        
        # Привязка событий
        self._bind_events()
        
        # Запуск обработчика обновлений
        self._start_update_handler()
        
        logger.info("Главное окно инициализировано")
    
    def _setup_styles(self):
        """
        Настройка стилей интерфейса
        """
        style = ttk.Style()
        
        # Настройка темы
        style.theme_use('clam')
        
        # Кастомные стили
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 10))
        
        # Стили для кнопок
        style.configure('Success.TButton', background='#28a745')
        style.configure('Danger.TButton', background='#dc3545')
        style.configure('Warning.TButton', background='#ffc107')
        
        # Стили для индикаторов
        style.configure('Running.TLabel', foreground='#28a745', font=('Arial', 10, 'bold'))
        style.configure('Stopped.TLabel', foreground='#dc3545', font=('Arial', 10, 'bold'))
        style.configure('Warning.TLabel', foreground='#ffc107', font=('Arial', 10, 'bold'))
    
    def _create_menu(self):
        """
        Создание главного меню
        """
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новая конфигурация", command=self._new_config)
        file_menu.add_command(label="Открыть конфигурацию", command=self._open_config)
        file_menu.add_command(label="Сохранить конфигурацию", command=self._save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт данных", command=self._export_data)
        file_menu.add_command(label="Импорт данных", command=self._import_data)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._on_closing)
        
        # Меню "Система"
        system_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Система", menu=system_menu)
        system_menu.add_command(label="Запустить систему", command=self._start_system)
        system_menu.add_command(label="Остановить систему", command=self._stop_system)
        system_menu.add_separator()
        system_menu.add_command(label="Статус системы", command=self._show_system_status)
        system_menu.add_command(label="Перезагрузить конфигурацию", command=self._reload_config)
        
        # Меню "Торговля"
        trading_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Торговля", menu=trading_menu)
        trading_menu.add_command(label="Экстренная остановка", command=self._emergency_stop)
        trading_menu.add_command(label="Закрыть все позиции", command=self._close_all_positions)
        trading_menu.add_separator()
        trading_menu.add_command(label="История сделок", command=self._show_trade_history)
        
        # Меню "Помощь"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Помощь", menu=help_menu)
        help_menu.add_command(label="Документация", command=self._show_documentation)
        help_menu.add_command(label="О программе", command=self._show_about)
    
    def _create_toolbar(self):
        """
        Создание панели инструментов
        """
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        # Кнопки управления системой
        self.start_button = ttk.Button(
            self.toolbar, 
            text="▶ Запустить", 
            command=self._start_system,
            style='Success.TButton'
        )
        self.start_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = ttk.Button(
            self.toolbar, 
            text="⏹ Остановить", 
            command=self._stop_system,
            style='Danger.TButton',
            state='disabled'
        )
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # Разделитель
        ttk.Separator(self.toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Кнопки быстрого доступа
        ttk.Button(
            self.toolbar, 
            text="📊 Обновить данные", 
            command=self._refresh_data
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            self.toolbar, 
            text="⚙ Настройки", 
            command=self._show_settings
        ).pack(side=tk.LEFT, padx=2)
        
        # Индикатор статуса системы
        self.status_indicator = ttk.Label(
            self.toolbar, 
            text="● Система остановлена",
            style='Stopped.TLabel'
        )
        self.status_indicator.pack(side=tk.RIGHT, padx=10)
    
    def _create_main_area(self):
        """
        Создание основной рабочей области
        """
        # Создание notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладка "Дашборд"
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="📊 Дашборд")
        self.dashboard_panel = DashboardPanel(self.dashboard_frame, self)
        
        # Вкладка "Торговля"
        self.trading_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.trading_frame, text="💹 Торговля")
        self.trading_panel = TradingPanel(self.trading_frame, self)
        
        # Вкладка "Портфель"
        self.portfolio_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.portfolio_frame, text="💼 Портфель")
        self.portfolio_panel = PortfolioPanel(self.portfolio_frame, self)
        
        # Вкладка "Конфигурация"
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="⚙ Конфигурация")
        self.config_panel = ConfigPanel(self.config_frame, self)
        
        # Вкладка "Логи"
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="📝 Логи")
        self.logs_panel = LogsPanel(self.logs_frame, self)
    
    def _create_status_bar(self):
        """
        Создание строки состояния
        """
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Статус системы
        self.status_label = ttk.Label(
            self.status_bar, 
            text="Готов к работе",
            style='Status.TLabel'
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Время последнего обновления
        self.last_update_label = ttk.Label(
            self.status_bar, 
            text="",
            style='Status.TLabel'
        )
        self.last_update_label.pack(side=tk.RIGHT, padx=5)
    
    def _bind_events(self):
        """
        Привязка событий
        """
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Привязка горячих клавиш
        self.root.bind('<Control-s>', lambda e: self._save_config())
        self.root.bind('<Control-o>', lambda e: self._open_config())
        self.root.bind('<F5>', lambda e: self._refresh_data())
        self.root.bind('<F1>', lambda e: self._show_documentation())
    
    def _start_update_handler(self):
        """
        Запуск обработчика обновлений интерфейса
        """
        def update_handler():
            try:
                while True:
                    try:
                        # Получение обновления из очереди
                        update_data = self.update_queue.get(timeout=0.1)
                        
                        # Обработка обновления в главном потоке
                        self.root.after(0, self._process_update, update_data)
                        
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"Ошибка в обработчике обновлений: {e}")
            except Exception as e:
                logger.error(f"Критическая ошибка в обработчике обновлений: {e}")
        
        # Запуск в отдельном потоке
        update_thread = threading.Thread(target=update_handler, daemon=True)
        update_thread.start()
        
        # Периодическое обновление интерфейса
        self._schedule_periodic_updates()
    
    def _schedule_periodic_updates(self):
        """
        Планирование периодических обновлений
        """
        # Обновление каждые 5 секунд
        self.root.after(5000, self._periodic_update)
    
    def _periodic_update(self):
        """
        Периодическое обновление интерфейса
        """
        try:
            # Обновление времени
            current_time = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.config(text=f"Обновлено: {current_time}")
            
            # Обновление статуса системы
            if self.investment_system and self.system_running:
                status = self.investment_system.get_system_status()
                self._update_system_status(status)
            
            # Планирование следующего обновления
            self._schedule_periodic_updates()
            
        except Exception as e:
            logger.error(f"Ошибка периодического обновления: {e}")
            self._schedule_periodic_updates()
    
    def _process_update(self, update_data: Dict[str, Any]):
        """
        Обработка обновления интерфейса
        
        Args:
            update_data: Данные для обновления
        """
        try:
            update_type = update_data.get('type')
            
            if update_type == 'system_status':
                self._update_system_status(update_data.get('data'))
            elif update_type == 'portfolio_update':
                self.portfolio_panel.update_data(update_data.get('data'))
            elif update_type == 'trading_signal':
                self.trading_panel.add_signal(update_data.get('data'))
            elif update_type == 'log_message':
                self.logs_panel.add_log_message(update_data.get('data'))
            elif update_type == 'error':
                self._show_error(update_data.get('message', 'Неизвестная ошибка'))
            
        except Exception as e:
            logger.error(f"Ошибка обработки обновления: {e}")
    
    def _update_system_status(self, status: Dict[str, Any]):
        """
        Обновление статуса системы
        
        Args:
            status: Статус системы
        """
        try:
            is_running = status.get('is_running', False)
            
            if is_running:
                self.status_indicator.config(
                    text="● Система работает",
                    style='Running.TLabel'
                )
                self.start_button.config(state='disabled')
                self.stop_button.config(state='normal')
                self.status_label.config(text="Система активна")
            else:
                self.status_indicator.config(
                    text="● Система остановлена",
                    style='Stopped.TLabel'
                )
                self.start_button.config(state='normal')
                self.stop_button.config(state='disabled')
                self.status_label.config(text="Система остановлена")
            
            # Обновление панелей
            self.dashboard_panel.update_system_status(status)
            
        except Exception as e:
            logger.error(f"Ошибка обновления статуса системы: {e}")
    
    def _start_system(self):
        """
        Запуск системы инвестиций
        """
        try:
            if self.system_running:
                messagebox.showwarning("Предупреждение", "Система уже запущена")
                return
            
            # Создание системы инвестиций
            config_path = self.config_panel.get_current_config_path()
            self.investment_system = InvestmentSystem(config_path)
            
            # Запуск в отдельном потоке
            def run_system():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.investment_system.start_trading())
                except Exception as e:
                    logger.error(f"Ошибка запуска системы: {e}")
                    self.update_queue.put({
                        'type': 'error',
                        'message': f"Ошибка запуска системы: {e}"
                    })
                finally:
                    self.system_running = False
            
            system_thread = threading.Thread(target=run_system, daemon=True)
            system_thread.start()
            
            self.system_running = True
            logger.info("Система инвестиций запущена")
            
        except Exception as e:
            logger.error(f"Ошибка запуска системы: {e}")
            messagebox.showerror("Ошибка", f"Не удалось запустить систему: {e}")
    
    def _stop_system(self):
        """
        Остановка системы инвестиций
        """
        try:
            if not self.system_running or not self.investment_system:
                messagebox.showwarning("Предупреждение", "Система не запущена")
                return
            
            # Остановка системы
            def stop_system():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.investment_system.stop_trading())
                except Exception as e:
                    logger.error(f"Ошибка остановки системы: {e}")
            
            stop_thread = threading.Thread(target=stop_system, daemon=True)
            stop_thread.start()
            
            self.system_running = False
            logger.info("Система инвестиций остановлена")
            
        except Exception as e:
            logger.error(f"Ошибка остановки системы: {e}")
            messagebox.showerror("Ошибка", f"Не удалось остановить систему: {e}")
    
    def _emergency_stop(self):
        """
        Экстренная остановка системы
        """
        result = messagebox.askyesno(
            "Экстренная остановка",
            "Вы уверены, что хотите экстренно остановить систему?\n"
            "Это может привести к потере данных."
        )
        
        if result:
            self.system_running = False
            if self.investment_system:
                # Принудительная остановка
                try:
                    # Здесь должна быть логика экстренной остановки
                    logger.warning("Выполнена экстренная остановка системы")
                except Exception as e:
                    logger.error(f"Ошибка экстренной остановки: {e}")
    
    def _show_error(self, message: str):
        """
        Показ ошибки пользователю
        
        Args:
            message: Сообщение об ошибке
        """
        messagebox.showerror("Ошибка", message)
    
    def _new_config(self):
        """Создание новой конфигурации"""
        self.config_panel.new_config()
    
    def _open_config(self):
        """Открытие конфигурации"""
        self.config_panel.open_config()
    
    def _save_config(self):
        """Сохранение конфигурации"""
        self.config_panel.save_config()
    
    def _export_data(self):
        """Экспорт данных"""
        messagebox.showinfo("Информация", "Функция экспорта данных в разработке")
    
    def _import_data(self):
        """Импорт данных"""
        messagebox.showinfo("Информация", "Функция импорта данных в разработке")
    
    def _show_system_status(self):
        """Показ статуса системы"""
        if self.investment_system:
            status = self.investment_system.get_system_status()
            # Здесь должно быть окно с подробным статусом
            messagebox.showinfo("Статус системы", f"Система работает: {status.get('is_running', False)}")
        else:
            messagebox.showinfo("Статус системы", "Система не инициализирована")
    
    def _reload_config(self):
        """Перезагрузка конфигурации"""
        self.config_panel.reload_config()
    
    def _close_all_positions(self):
        """Закрытие всех позиций"""
        result = messagebox.askyesno(
            "Закрытие позиций",
            "Вы уверены, что хотите закрыть все открытые позиции?"
        )
        
        if result:
            # Здесь должна быть логика закрытия позиций
            messagebox.showinfo("Информация", "Функция закрытия позиций в разработке")
    
    def _show_trade_history(self):
        """Показ истории сделок"""
        messagebox.showinfo("Информация", "Функция истории сделок в разработке")
    
    def _refresh_data(self):
        """Обновление данных"""
        try:
            # Обновление всех панелей
            self.dashboard_panel.refresh_data()
            self.trading_panel.refresh_data()
            self.portfolio_panel.refresh_data()
            
            self.status_label.config(text="Данные обновлены")
            logger.info("Данные интерфейса обновлены")
            
        except Exception as e:
            logger.error(f"Ошибка обновления данных: {e}")
            messagebox.showerror("Ошибка", f"Не удалось обновить данные: {e}")
    
    def _show_settings(self):
        """Показ настроек"""
        # Переключение на вкладку конфигурации
        self.notebook.select(self.config_frame)
    
    def _show_documentation(self):
        """Показ документации"""
        messagebox.showinfo("Документация", "Документация доступна в папке docs/")
    
    def _show_about(self):
        """Показ информации о программе"""
        about_text = """
Нейросетевая система инвестиций
Версия 1.0.0

Система автоматической торговли с использованием
нейронных сетей для анализа рынка и принятия
торговых решений.

© 2024 Все права защищены
        """
        messagebox.showinfo("О программе", about_text)
    
    def _on_closing(self):
        """
        Обработка закрытия приложения
        """
        if self.system_running:
            result = messagebox.askyesno(
                "Закрытие приложения",
                "Система инвестиций все еще работает.\n"
                "Остановить систему и закрыть приложение?"
            )
            
            if result:
                self._stop_system()
                # Даем время на остановку
                self.root.after(2000, self.root.destroy)
            return
        
        self.root.destroy()
    
    def run(self):
        """
        Запуск главного цикла приложения
        """
        try:
            logger.info("Запуск графического интерфейса")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Ошибка в главном цикле приложения: {e}")
        finally:
            logger.info("Графический интерфейс закрыт")
    
    def get_investment_system(self) -> Optional[InvestmentSystem]:
        """
        Получение системы инвестиций
        
        Returns:
            Система инвестиций или None
        """
        return self.investment_system
    
    def is_system_running(self) -> bool:
        """
        Проверка работы системы
        
        Returns:
            True если система работает
        """
        return self.system_running
    
    def add_update(self, update_data: Dict[str, Any]):
        """
        Добавление обновления в очередь
        
        Args:
            update_data: Данные для обновления
        """
        try:
            self.update_queue.put(update_data, timeout=1)
        except queue.Full:
            logger.warning("Очередь обновлений переполнена")
