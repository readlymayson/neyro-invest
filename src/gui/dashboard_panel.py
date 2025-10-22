"""
Панель дашборда с графиками и метриками
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading
import time

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import numpy as np
from loguru import logger


class DashboardPanel:
    """
    Панель дашборда с графиками и метриками
    """
    
    def __init__(self, parent, main_window):
        """
        Инициализация панели дашборда
        
        Args:
            parent: Родительский виджет
            main_window: Главное окно приложения
        """
        self.parent = parent
        self.main_window = main_window
        
        # Данные для отображения
        self.portfolio_history = []
        self.price_data = {}
        self.system_metrics = {}
        
        # Создание интерфейса
        self._create_widgets()
        
        # Запуск автообновления
        self._start_auto_update()
        
        logger.info("Панель дашборда инициализирована")
    
    def _create_widgets(self):
        """
        Создание виджетов панели
        """
        # Главный контейнер
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель с метриками
        self._create_metrics_panel(main_frame)
        
        # Средняя панель с графиками
        self._create_charts_panel(main_frame)
        
        # Нижняя панель с таблицами
        self._create_tables_panel(main_frame)
    
    def _create_metrics_panel(self, parent):
        """
        Создание панели метрик
        
        Args:
            parent: Родительский виджет
        """
        # Рамка для метрик
        metrics_frame = ttk.LabelFrame(parent, text="Основные метрики", padding=10)
        metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Создание сетки для метрик
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill=tk.X)
        
        # Конфигурация сетки
        for i in range(4):
            metrics_grid.columnconfigure(i, weight=1)
        
        # Метрики портфеля
        self._create_metric_card(metrics_grid, "Общая стоимость", "0 ₽", 0, 0, "blue")
        self._create_metric_card(metrics_grid, "Прибыль/Убыток", "0 ₽ (0%)", 0, 1, "green")
        self._create_metric_card(metrics_grid, "Дневной P&L", "0 ₽ (0%)", 0, 2, "orange")
        self._create_metric_card(metrics_grid, "Количество позиций", "0", 0, 3, "purple")
        
        # Метрики системы
        self._create_metric_card(metrics_grid, "Статус системы", "Остановлена", 1, 0, "red")
        self._create_metric_card(metrics_grid, "Активных сигналов", "0", 1, 1, "blue")
        self._create_metric_card(metrics_grid, "Коэффициент Шарпа", "0.00", 1, 2, "green")
        self._create_metric_card(metrics_grid, "Максимальная просадка", "0%", 1, 3, "red")
    
    def _create_metric_card(self, parent, title: str, value: str, row: int, col: int, color: str):
        """
        Создание карточки метрики
        
        Args:
            parent: Родительский виджет
            title: Заголовок метрики
            value: Значение метрики
            row: Строка в сетке
            col: Колонка в сетке
            color: Цвет карточки
        """
        # Рамка карточки
        card_frame = ttk.Frame(parent, relief='raised', borderwidth=1)
        card_frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        # Заголовок
        title_label = ttk.Label(
            card_frame, 
            text=title, 
            font=('Arial', 10, 'bold'),
            foreground='gray'
        )
        title_label.pack(pady=(10, 5))
        
        # Значение
        value_label = ttk.Label(
            card_frame, 
            text=value, 
            font=('Arial', 14, 'bold'),
            foreground=color
        )
        value_label.pack(pady=(0, 10))
        
        # Сохранение ссылки на метку для обновления
        setattr(self, f"metric_{title.lower().replace(' ', '_').replace('/', '_')}", value_label)
    
    def _create_charts_panel(self, parent):
        """
        Создание панели графиков
        
        Args:
            parent: Родительский виджет
        """
        # Рамка для графиков
        charts_frame = ttk.LabelFrame(parent, text="Графики", padding=10)
        charts_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Notebook для разных графиков
        self.charts_notebook = ttk.Notebook(charts_frame)
        self.charts_notebook.pack(fill=tk.BOTH, expand=True)
        
        # График портфеля
        self._create_portfolio_chart()
        
        # График цен
        self._create_price_chart()
        
        # График сигналов
        self._create_signals_chart()
        
        # График рисков
        self._create_risk_chart()
    
    def _create_portfolio_chart(self):
        """
        Создание графика портфеля
        """
        # Фрейм для графика портфеля
        portfolio_frame = ttk.Frame(self.charts_notebook)
        self.charts_notebook.add(portfolio_frame, text="Портфель")
        
        # Создание matplotlib фигуры
        self.portfolio_figure = Figure(figsize=(12, 6), dpi=100)
        self.portfolio_ax = self.portfolio_figure.add_subplot(111)
        
        # Настройка графика
        self.portfolio_ax.set_title("Динамика стоимости портфеля", fontsize=14, fontweight='bold')
        self.portfolio_ax.set_xlabel("Время")
        self.portfolio_ax.set_ylabel("Стоимость (₽)")
        self.portfolio_ax.grid(True, alpha=0.3)
        
        # Создание canvas
        self.portfolio_canvas = FigureCanvasTkAgg(self.portfolio_figure, portfolio_frame)
        self.portfolio_canvas.draw()
        self.portfolio_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Панель управления графиком
        portfolio_controls = ttk.Frame(portfolio_frame)
        portfolio_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            portfolio_controls, 
            text="1Д", 
            command=lambda: self._update_portfolio_chart("1D")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            portfolio_controls, 
            text="1Н", 
            command=lambda: self._update_portfolio_chart("1W")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            portfolio_controls, 
            text="1М", 
            command=lambda: self._update_portfolio_chart("1M")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            portfolio_controls, 
            text="Все", 
            command=lambda: self._update_portfolio_chart("ALL")
        ).pack(side=tk.LEFT, padx=2)
    
    def _create_price_chart(self):
        """
        Создание графика цен
        """
        # Фрейм для графика цен
        price_frame = ttk.Frame(self.charts_notebook)
        self.charts_notebook.add(price_frame, text="Цены активов")
        
        # Создание matplotlib фигуры
        self.price_figure = Figure(figsize=(12, 6), dpi=100)
        self.price_ax = self.price_figure.add_subplot(111)
        
        # Настройка графика
        self.price_ax.set_title("Цены активов", fontsize=14, fontweight='bold')
        self.price_ax.set_xlabel("Время")
        self.price_ax.set_ylabel("Цена (₽)")
        self.price_ax.grid(True, alpha=0.3)
        
        # Создание canvas
        self.price_canvas = FigureCanvasTkAgg(self.price_figure, price_frame)
        self.price_canvas.draw()
        self.price_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Панель выбора активов
        price_controls = ttk.Frame(price_frame)
        price_controls.pack(fill=tk.X, pady=5)
        
        ttk.Label(price_controls, text="Активы:").pack(side=tk.LEFT, padx=5)
        
        self.symbols_var = tk.StringVar()
        symbols_combo = ttk.Combobox(
            price_controls, 
            textvariable=self.symbols_var,
            values=["SBER", "GAZP", "LKOH"],
            state="readonly"
        )
        symbols_combo.pack(side=tk.LEFT, padx=5)
        symbols_combo.bind('<<ComboboxSelected>>', self._on_symbol_selected)
        symbols_combo.set("SBER")
    
    def _create_signals_chart(self):
        """
        Создание графика сигналов
        """
        # Фрейм для графика сигналов
        signals_frame = ttk.Frame(self.charts_notebook)
        self.charts_notebook.add(signals_frame, text="Торговые сигналы")
        
        # Создание matplotlib фигуры
        self.signals_figure = Figure(figsize=(12, 6), dpi=100)
        self.signals_ax = self.signals_figure.add_subplot(111)
        
        # Настройка графика
        self.signals_ax.set_title("Торговые сигналы", fontsize=14, fontweight='bold')
        self.signals_ax.set_xlabel("Время")
        self.signals_ax.set_ylabel("Уверенность сигнала")
        self.signals_ax.grid(True, alpha=0.3)
        
        # Создание canvas
        self.signals_canvas = FigureCanvasTkAgg(self.signals_figure, signals_frame)
        self.signals_canvas.draw()
        self.signals_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_risk_chart(self):
        """
        Создание графика рисков
        """
        # Фрейм для графика рисков
        risk_frame = ttk.Frame(self.charts_notebook)
        self.charts_notebook.add(risk_frame, text="Анализ рисков")
        
        # Создание matplotlib фигуры
        self.risk_figure = Figure(figsize=(12, 6), dpi=100)
        self.risk_ax = self.risk_figure.add_subplot(111)
        
        # Настройка графика
        self.risk_ax.set_title("Анализ рисков портфеля", fontsize=14, fontweight='bold')
        self.risk_ax.set_xlabel("Время")
        self.risk_ax.set_ylabel("Риск (%)")
        self.risk_ax.grid(True, alpha=0.3)
        
        # Создание canvas
        self.risk_canvas = FigureCanvasTkAgg(self.risk_figure, risk_frame)
        self.risk_canvas.draw()
        self.risk_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_tables_panel(self, parent):
        """
        Создание панели таблиц
        
        Args:
            parent: Родительский виджет
        """
        # Рамка для таблиц
        tables_frame = ttk.LabelFrame(parent, text="Детальная информация", padding=10)
        tables_frame.pack(fill=tk.X)
        
        # Notebook для разных таблиц
        self.tables_notebook = ttk.Notebook(tables_frame)
        self.tables_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Таблица позиций
        self._create_positions_table()
        
        # Таблица сигналов
        self._create_signals_table()
        
        # Таблица метрик
        self._create_metrics_table()
    
    def _create_positions_table(self):
        """
        Создание таблицы позиций
        """
        # Фрейм для таблицы позиций
        positions_frame = ttk.Frame(self.tables_notebook)
        self.tables_notebook.add(positions_frame, text="Позиции")
        
        # Создание Treeview
        columns = ("Символ", "Количество", "Средняя цена", "Текущая цена", "P&L", "P&L %")
        self.positions_tree = ttk.Treeview(positions_frame, columns=columns, show='headings', height=6)
        
        # Настройка колонок
        for col in columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=100, anchor='center')
        
        # Скроллбар
        positions_scrollbar = ttk.Scrollbar(positions_frame, orient='vertical', command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=positions_scrollbar.set)
        
        # Размещение
        self.positions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        positions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_signals_table(self):
        """
        Создание таблицы сигналов
        """
        # Фрейм для таблицы сигналов
        signals_frame = ttk.Frame(self.tables_notebook)
        self.tables_notebook.add(signals_frame, text="Сигналы")
        
        # Создание Treeview
        columns = ("Время", "Символ", "Сигнал", "Уверенность", "Источник", "Статус")
        self.signals_tree = ttk.Treeview(signals_frame, columns=columns, show='headings', height=6)
        
        # Настройка колонок
        for col in columns:
            self.signals_tree.heading(col, text=col)
            self.signals_tree.column(col, width=100, anchor='center')
        
        # Скроллбар
        signals_scrollbar = ttk.Scrollbar(signals_frame, orient='vertical', command=self.signals_tree.yview)
        self.signals_tree.configure(yscrollcommand=signals_scrollbar.set)
        
        # Размещение
        self.signals_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        signals_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_metrics_table(self):
        """
        Создание таблицы метрик
        """
        # Фрейм для таблицы метрик
        metrics_frame = ttk.Frame(self.tables_notebook)
        self.tables_notebook.add(metrics_frame, text="Метрики")
        
        # Создание Treeview
        columns = ("Метрика", "Значение", "Изменение", "Статус")
        self.metrics_tree = ttk.Treeview(metrics_frame, columns=columns, show='headings', height=6)
        
        # Настройка колонок
        for col in columns:
            self.metrics_tree.heading(col, text=col)
            self.metrics_tree.column(col, width=150, anchor='center')
        
        # Скроллбар
        metrics_scrollbar = ttk.Scrollbar(metrics_frame, orient='vertical', command=self.metrics_tree.yview)
        self.metrics_tree.configure(yscrollcommand=metrics_scrollbar.set)
        
        # Размещение
        self.metrics_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        metrics_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _start_auto_update(self):
        """
        Запуск автоматического обновления
        """
        def update_loop():
            while True:
                try:
                    # Обновление каждые 30 секунд
                    time.sleep(30)
                    
                    # Обновление данных в главном потоке
                    self.parent.after(0, self._auto_update)
                    
                except Exception as e:
                    logger.error(f"Ошибка в цикле автообновления дашборда: {e}")
        
        # Запуск в отдельном потоке
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
    
    def _auto_update(self):
        """
        Автоматическое обновление данных
        """
        try:
            if self.main_window.is_system_running():
                self.refresh_data()
        except Exception as e:
            logger.error(f"Ошибка автообновления дашборда: {e}")
    
    def _update_portfolio_chart(self, period: str):
        """
        Обновление графика портфеля
        
        Args:
            period: Период отображения
        """
        try:
            self.portfolio_ax.clear()
            
            if not self.portfolio_history:
                # Генерация тестовых данных
                self._generate_test_portfolio_data()
            
            # Фильтрация данных по периоду
            filtered_data = self._filter_data_by_period(self.portfolio_history, period)
            
            if filtered_data:
                times = [item['timestamp'] for item in filtered_data]
                values = [item['total_value'] for item in filtered_data]
                
                self.portfolio_ax.plot(times, values, linewidth=2, color='blue', label='Стоимость портфеля')
                self.portfolio_ax.fill_between(times, values, alpha=0.3, color='blue')
                
                # Настройка осей
                self.portfolio_ax.set_title("Динамика стоимости портфеля", fontsize=14, fontweight='bold')
                self.portfolio_ax.set_xlabel("Время")
                self.portfolio_ax.set_ylabel("Стоимость (₽)")
                self.portfolio_ax.grid(True, alpha=0.3)
                self.portfolio_ax.legend()
                
                # Форматирование дат
                self.portfolio_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                self.portfolio_ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
                
                # Поворот меток дат
                plt.setp(self.portfolio_ax.xaxis.get_majorticklabels(), rotation=45)
            
            self.portfolio_figure.tight_layout()
            self.portfolio_canvas.draw()
            
        except Exception as e:
            logger.error(f"Ошибка обновления графика портфеля: {e}")
    
    def _generate_test_portfolio_data(self):
        """
        Генерация тестовых данных портфеля
        """
        try:
            base_time = datetime.now() - timedelta(hours=24)
            base_value = 1000000
            
            self.portfolio_history = []
            
            for i in range(144):  # 24 часа по 10 минут
                timestamp = base_time + timedelta(minutes=i*10)
                
                # Генерация случайного изменения
                change = np.random.normal(0, 5000)
                value = max(base_value + change * (i + 1) / 144, 500000)
                
                self.portfolio_history.append({
                    'timestamp': timestamp,
                    'total_value': value,
                    'cash_balance': value * 0.1,
                    'invested_value': value * 0.9,
                    'total_pnl': value - base_value,
                    'total_pnl_percent': ((value - base_value) / base_value) * 100
                })
                
        except Exception as e:
            logger.error(f"Ошибка генерации тестовых данных: {e}")
    
    def _filter_data_by_period(self, data: List[Dict], period: str) -> List[Dict]:
        """
        Фильтрация данных по периоду
        
        Args:
            data: Данные для фильтрации
            period: Период фильтрации
            
        Returns:
            Отфильтрованные данные
        """
        try:
            if not data or period == "ALL":
                return data
            
            now = datetime.now()
            
            if period == "1D":
                cutoff = now - timedelta(days=1)
            elif period == "1W":
                cutoff = now - timedelta(weeks=1)
            elif period == "1M":
                cutoff = now - timedelta(days=30)
            else:
                return data
            
            return [item for item in data if item['timestamp'] >= cutoff]
            
        except Exception as e:
            logger.error(f"Ошибка фильтрации данных: {e}")
            return data
    
    def _on_symbol_selected(self, event):
        """
        Обработка выбора символа
        
        Args:
            event: Событие выбора
        """
        try:
            symbol = self.symbols_var.get()
            self._update_price_chart(symbol)
        except Exception as e:
            logger.error(f"Ошибка обработки выбора символа: {e}")
    
    def _update_price_chart(self, symbol: str):
        """
        Обновление графика цен
        
        Args:
            symbol: Символ для отображения
        """
        try:
            self.price_ax.clear()
            
            # Генерация тестовых данных цен
            if symbol not in self.price_data:
                self._generate_test_price_data(symbol)
            
            data = self.price_data.get(symbol, [])
            
            if data:
                times = [item['timestamp'] for item in data]
                prices = [item['price'] for item in data]
                
                self.price_ax.plot(times, prices, linewidth=2, label=f'{symbol}')
                
                # Настройка графика
                self.price_ax.set_title(f"Цена {symbol}", fontsize=14, fontweight='bold')
                self.price_ax.set_xlabel("Время")
                self.price_ax.set_ylabel("Цена (₽)")
                self.price_ax.grid(True, alpha=0.3)
                self.price_ax.legend()
                
                # Форматирование дат
                self.price_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                self.price_ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                
                plt.setp(self.price_ax.xaxis.get_majorticklabels(), rotation=45)
            
            self.price_figure.tight_layout()
            self.price_canvas.draw()
            
        except Exception as e:
            logger.error(f"Ошибка обновления графика цен: {e}")
    
    def _generate_test_price_data(self, symbol: str):
        """
        Генерация тестовых данных цен
        
        Args:
            symbol: Символ для генерации данных
        """
        try:
            base_time = datetime.now() - timedelta(hours=24)
            
            # Базовые цены для разных символов
            base_prices = {"SBER": 250, "GAZP": 180, "LKOH": 6500}
            base_price = base_prices.get(symbol, 100)
            
            data = []
            current_price = base_price
            
            for i in range(144):  # 24 часа по 10 минут
                timestamp = base_time + timedelta(minutes=i*10)
                
                # Генерация случайного изменения цены
                change_percent = np.random.normal(0, 0.01)  # 1% волатильность
                current_price *= (1 + change_percent)
                current_price = max(current_price, base_price * 0.5)  # Минимум 50% от базовой цены
                
                data.append({
                    'timestamp': timestamp,
                    'price': current_price,
                    'volume': np.random.randint(1000, 10000)
                })
            
            self.price_data[symbol] = data
            
        except Exception as e:
            logger.error(f"Ошибка генерации данных цен для {symbol}: {e}")
    
    def update_system_status(self, status: Dict[str, Any]):
        """
        Обновление статуса системы
        
        Args:
            status: Статус системы
        """
        try:
            is_running = status.get('is_running', False)
            
            # Обновление метрики статуса системы
            if hasattr(self, 'metric_статус_системы'):
                status_text = "Работает" if is_running else "Остановлена"
                color = "green" if is_running else "red"
                self.metric_статус_системы.config(text=status_text, foreground=color)
            
            # Обновление других метрик из статуса
            if 'portfolio_manager' in status:
                portfolio_status = status['portfolio_manager']
                
                if hasattr(self, 'metric_общая_стоимость'):
                    total_value = portfolio_status.get('current_value', 0)
                    self.metric_общая_стоимость.config(text=f"{total_value:,.0f} ₽")
                
                if hasattr(self, 'metric_количество_позиций'):
                    positions_count = portfolio_status.get('positions_count', 0)
                    self.metric_количество_позиций.config(text=str(positions_count))
            
            if 'trading_engine' in status:
                trading_status = status['trading_engine']
                
                if hasattr(self, 'metric_активных_сигналов'):
                    signals_count = trading_status.get('trading_signals', 0)
                    self.metric_активных_сигналов.config(text=str(signals_count))
            
        except Exception as e:
            logger.error(f"Ошибка обновления статуса системы в дашборде: {e}")
    
    def refresh_data(self):
        """
        Обновление всех данных панели
        """
        try:
            logger.debug("Обновление данных дашборда")
            
            # Обновление графиков
            self._update_portfolio_chart("1D")
            
            current_symbol = self.symbols_var.get() or "SBER"
            self._update_price_chart(current_symbol)
            
            # Обновление таблиц
            self._update_positions_table()
            self._update_signals_table()
            self._update_metrics_table()
            
        except Exception as e:
            logger.error(f"Ошибка обновления данных дашборда: {e}")
    
    def _update_positions_table(self):
        """
        Обновление таблицы позиций
        """
        try:
            # Очистка таблицы
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
            
            # Получение данных о позициях
            investment_system = self.main_window.get_investment_system()
            if investment_system and investment_system.portfolio_manager:
                # Здесь должна быть логика получения реальных позиций
                pass
            
            # Добавление тестовых данных
            test_positions = [
                ("SBER", "100", "250.00", "255.00", "+500", "+2.0%"),
                ("GAZP", "50", "180.00", "175.00", "-250", "-1.4%"),
                ("LKOH", "10", "6500.00", "6600.00", "+1000", "+1.5%")
            ]
            
            for pos in test_positions:
                self.positions_tree.insert('', 'end', values=pos)
                
        except Exception as e:
            logger.error(f"Ошибка обновления таблицы позиций: {e}")
    
    def _update_signals_table(self):
        """
        Обновление таблицы сигналов
        """
        try:
            # Очистка таблицы
            for item in self.signals_tree.get_children():
                self.signals_tree.delete(item)
            
            # Добавление тестовых данных
            test_signals = [
                (datetime.now().strftime("%H:%M:%S"), "SBER", "BUY", "0.75", "LSTM", "Активен"),
                (datetime.now().strftime("%H:%M:%S"), "GAZP", "SELL", "0.68", "XGBoost", "Выполнен"),
                (datetime.now().strftime("%H:%M:%S"), "LKOH", "HOLD", "0.45", "DeepSeek", "Ожидание")
            ]
            
            for signal in test_signals:
                self.signals_tree.insert('', 'end', values=signal)
                
        except Exception as e:
            logger.error(f"Ошибка обновления таблицы сигналов: {e}")
    
    def _update_metrics_table(self):
        """
        Обновление таблицы метрик
        """
        try:
            # Очистка таблицы
            for item in self.metrics_tree.get_children():
                self.metrics_tree.delete(item)
            
            # Добавление тестовых данных
            test_metrics = [
                ("Коэффициент Шарпа", "1.25", "+0.05", "Хорошо"),
                ("Максимальная просадка", "5.2%", "-0.3%", "Норма"),
                ("Волатильность", "15.8%", "+1.2%", "Средняя"),
                ("Альфа", "0.08", "+0.02", "Отлично")
            ]
            
            for metric in test_metrics:
                self.metrics_tree.insert('', 'end', values=metric)
                
        except Exception as e:
            logger.error(f"Ошибка обновления таблицы метрик: {e}")
