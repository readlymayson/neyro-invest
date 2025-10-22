"""
Панель портфеля с визуализацией активов
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
import time

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from loguru import logger


class PortfolioPanel:
    """
    Панель портфеля с визуализацией активов
    """
    
    def __init__(self, parent, main_window):
        """
        Инициализация панели портфеля
        
        Args:
            parent: Родительский виджет
            main_window: Главное окно приложения
        """
        self.parent = parent
        self.main_window = main_window
        
        # Данные портфеля
        self.portfolio_data = {}
        self.positions_data = []
        self.performance_data = []
        
        # Создание интерфейса
        self._create_widgets()
        
        # Запуск автообновления
        self._start_auto_update()
        
        logger.info("Панель портфеля инициализирована")
    
    def _create_widgets(self):
        """
        Создание виджетов панели
        """
        # Главный контейнер
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель - обзор портфеля
        self._create_overview_panel(main_frame)
        
        # Средняя панель - позиции и графики
        self._create_content_panel(main_frame)
        
        # Нижняя панель - детальная информация
        self._create_details_panel(main_frame)
    
    def _create_overview_panel(self, parent):
        """
        Создание панели обзора портфеля
        
        Args:
            parent: Родительский виджет
        """
        # Рамка обзора
        overview_frame = ttk.LabelFrame(parent, text="Обзор портфеля", padding=10)
        overview_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Основные метрики
        metrics_frame = ttk.Frame(overview_frame)
        metrics_frame.pack(fill=tk.X)
        
        # Конфигурация сетки
        for i in range(5):
            metrics_frame.columnconfigure(i, weight=1)
        
        # Создание карточек метрик
        self._create_portfolio_metric(metrics_frame, "Общая стоимость", "1,000,000 ₽", 0, 0, "blue")
        self._create_portfolio_metric(metrics_frame, "Денежные средства", "100,000 ₽", 0, 1, "green")
        self._create_portfolio_metric(metrics_frame, "Инвестировано", "900,000 ₽", 0, 2, "orange")
        self._create_portfolio_metric(metrics_frame, "Общий P&L", "+50,000 ₽", 0, 3, "green")
        self._create_portfolio_metric(metrics_frame, "P&L %", "+5.26%", 0, 4, "green")
        
        # Дополнительные метрики
        additional_frame = ttk.Frame(overview_frame)
        additional_frame.pack(fill=tk.X, pady=(10, 0))
        
        for i in range(5):
            additional_frame.columnconfigure(i, weight=1)
        
        self._create_portfolio_metric(additional_frame, "Дневной P&L", "+2,500 ₽", 0, 0, "green")
        self._create_portfolio_metric(additional_frame, "Позиций", "8", 0, 1, "blue")
        self._create_portfolio_metric(additional_frame, "Коэф. Шарпа", "1.25", 0, 2, "green")
        self._create_portfolio_metric(additional_frame, "Макс. просадка", "-3.2%", 0, 3, "red")
        self._create_portfolio_metric(additional_frame, "Волатильность", "15.8%", 0, 4, "orange")
    
    def _create_portfolio_metric(self, parent, title: str, value: str, row: int, col: int, color: str):
        """
        Создание карточки метрики портфеля
        
        Args:
            parent: Родительский виджет
            title: Заголовок метрики
            value: Значение метрики
            row: Строка в сетке
            col: Колонка в сетке
            color: Цвет значения
        """
        # Рамка карточки
        card_frame = ttk.Frame(parent, relief='raised', borderwidth=1)
        card_frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        # Заголовок
        title_label = ttk.Label(
            card_frame, 
            text=title, 
            font=('Arial', 9, 'bold'),
            foreground='gray'
        )
        title_label.pack(pady=(8, 2))
        
        # Значение
        value_label = ttk.Label(
            card_frame, 
            text=value, 
            font=('Arial', 12, 'bold'),
            foreground=color
        )
        value_label.pack(pady=(0, 8))
        
        # Сохранение ссылки для обновления
        setattr(self, f"portfolio_metric_{title.lower().replace(' ', '_').replace('.', '_')}", value_label)
    
    def _create_content_panel(self, parent):
        """
        Создание основной панели контента
        
        Args:
            parent: Родительский виджет
        """
        # Контейнер для контента
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Левая панель - позиции
        self._create_positions_panel(content_frame)
        
        # Правая панель - графики
        self._create_charts_panel(content_frame)
    
    def _create_positions_panel(self, parent):
        """
        Создание панели позиций
        
        Args:
            parent: Родительский виджет
        """
        # Левая панель
        positions_frame = ttk.LabelFrame(parent, text="Позиции портфеля", padding=10)
        positions_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Панель управления
        control_frame = ttk.Frame(positions_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            control_frame,
            text="🔄 Обновить",
            command=self._refresh_positions
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            control_frame,
            text="📊 Ребалансировка",
            command=self._show_rebalancing
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(
            control_frame,
            text="📈 Анализ",
            command=self._show_analysis
        ).pack(side=tk.RIGHT)
        
        # Таблица позиций
        columns = ("Символ", "Количество", "Ср. цена", "Тек. цена", "Стоимость", "P&L", "P&L %", "Вес %")
        self.positions_tree = ttk.Treeview(positions_frame, columns=columns, show='headings', height=12)
        
        # Настройка колонок
        column_widths = {"Символ": 60, "Количество": 80, "Ср. цена": 80, "Тек. цена": 80, 
                        "Стоимость": 100, "P&L": 80, "P&L %": 70, "Вес %": 60}
        
        for col in columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=column_widths.get(col, 80), anchor='center')
        
        # Скроллбары
        positions_v_scrollbar = ttk.Scrollbar(positions_frame, orient='vertical', command=self.positions_tree.yview)
        positions_h_scrollbar = ttk.Scrollbar(positions_frame, orient='horizontal', command=self.positions_tree.xview)
        self.positions_tree.configure(yscrollcommand=positions_v_scrollbar.set, xscrollcommand=positions_h_scrollbar.set)
        
        # Размещение
        self.positions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        positions_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        positions_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        # Контекстное меню для позиций
        self.positions_context_menu = tk.Menu(self.positions_tree, tearoff=0)
        self.positions_context_menu.add_command(label="Увеличить позицию", command=self._increase_position)
        self.positions_context_menu.add_command(label="Уменьшить позицию", command=self._decrease_position)
        self.positions_context_menu.add_command(label="Закрыть позицию", command=self._close_position)
        self.positions_context_menu.add_separator()
        self.positions_context_menu.add_command(label="Анализ позиции", command=self._analyze_position)
        self.positions_context_menu.add_command(label="История позиции", command=self._show_position_history)
        
        self.positions_tree.bind("<Button-3>", self._show_positions_context_menu)
        self.positions_tree.bind("<Double-1>", self._on_position_double_click)
    
    def _create_charts_panel(self, parent):
        """
        Создание панели графиков
        
        Args:
            parent: Родительский виджет
        """
        # Правая панель
        charts_frame = ttk.LabelFrame(parent, text="Визуализация портфеля", padding=10)
        charts_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Notebook для разных графиков
        self.charts_notebook = ttk.Notebook(charts_frame)
        self.charts_notebook.pack(fill=tk.BOTH, expand=True)
        
        # График распределения активов
        self._create_allocation_chart()
        
        # График производительности
        self._create_performance_chart()
        
        # График рисков
        self._create_risk_chart()
    
    def _create_allocation_chart(self):
        """
        Создание графика распределения активов
        """
        # Фрейм для графика распределения
        allocation_frame = ttk.Frame(self.charts_notebook)
        self.charts_notebook.add(allocation_frame, text="Распределение")
        
        # Создание matplotlib фигуры
        self.allocation_figure = Figure(figsize=(8, 6), dpi=100)
        self.allocation_ax = self.allocation_figure.add_subplot(111)
        
        # Создание canvas
        self.allocation_canvas = FigureCanvasTkAgg(self.allocation_figure, allocation_frame)
        self.allocation_canvas.draw()
        self.allocation_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Панель управления
        allocation_controls = ttk.Frame(allocation_frame)
        allocation_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            allocation_controls,
            text="Круговая диаграмма",
            command=lambda: self._update_allocation_chart("pie")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            allocation_controls,
            text="Столбчатая диаграмма",
            command=lambda: self._update_allocation_chart("bar")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            allocation_controls,
            text="Treemap",
            command=lambda: self._update_allocation_chart("treemap")
        ).pack(side=tk.LEFT, padx=2)
        
        # Инициальное отображение
        self._update_allocation_chart("pie")
    
    def _create_performance_chart(self):
        """
        Создание графика производительности
        """
        # Фрейм для графика производительности
        performance_frame = ttk.Frame(self.charts_notebook)
        self.charts_notebook.add(performance_frame, text="Производительность")
        
        # Создание matplotlib фигуры
        self.performance_figure = Figure(figsize=(8, 6), dpi=100)
        self.performance_ax = self.performance_figure.add_subplot(111)
        
        # Создание canvas
        self.performance_canvas = FigureCanvasTkAgg(self.performance_figure, performance_frame)
        self.performance_canvas.draw()
        self.performance_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Панель управления
        performance_controls = ttk.Frame(performance_frame)
        performance_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            performance_controls,
            text="1Д",
            command=lambda: self._update_performance_chart("1D")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            performance_controls,
            text="1Н",
            command=lambda: self._update_performance_chart("1W")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            performance_controls,
            text="1М",
            command=lambda: self._update_performance_chart("1M")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            performance_controls,
            text="Все",
            command=lambda: self._update_performance_chart("ALL")
        ).pack(side=tk.LEFT, padx=2)
        
        # Инициальное отображение
        self._update_performance_chart("1W")
    
    def _create_risk_chart(self):
        """
        Создание графика рисков
        """
        # Фрейм для графика рисков
        risk_frame = ttk.Frame(self.charts_notebook)
        self.charts_notebook.add(risk_frame, text="Анализ рисков")
        
        # Создание matplotlib фигуры
        self.risk_figure = Figure(figsize=(8, 6), dpi=100)
        self.risk_ax = self.risk_figure.add_subplot(111)
        
        # Создание canvas
        self.risk_canvas = FigureCanvasTkAgg(self.risk_figure, risk_frame)
        self.risk_canvas.draw()
        self.risk_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Панель управления
        risk_controls = ttk.Frame(risk_frame)
        risk_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            risk_controls,
            text="VaR",
            command=lambda: self._update_risk_chart("var")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            risk_controls,
            text="Корреляция",
            command=lambda: self._update_risk_chart("correlation")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            risk_controls,
            text="Волатильность",
            command=lambda: self._update_risk_chart("volatility")
        ).pack(side=tk.LEFT, padx=2)
        
        # Инициальное отображение
        self._update_risk_chart("var")
    
    def _create_details_panel(self, parent):
        """
        Создание панели детальной информации
        
        Args:
            parent: Родительский виджет
        """
        # Рамка деталей
        details_frame = ttk.LabelFrame(parent, text="Детальная информация", padding=10)
        details_frame.pack(fill=tk.X)
        
        # Notebook для разных таблиц
        self.details_notebook = ttk.Notebook(details_frame)
        self.details_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Таблица транзакций
        self._create_transactions_table()
        
        # Таблица дивидендов
        self._create_dividends_table()
        
        # Таблица метрик
        self._create_metrics_table()
    
    def _create_transactions_table(self):
        """
        Создание таблицы транзакций
        """
        # Фрейм для транзакций
        transactions_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(transactions_frame, text="Транзакции")
        
        # Панель фильтров
        filter_frame = ttk.Frame(transactions_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Период:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.transactions_period_var = tk.StringVar()
        period_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.transactions_period_var,
            values=["Сегодня", "Неделя", "Месяц", "Все"],
            state="readonly",
            width=10
        )
        period_combo.pack(side=tk.LEFT, padx=(0, 10))
        period_combo.set("Месяц")
        
        ttk.Label(filter_frame, text="Тип:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.transactions_type_var = tk.StringVar()
        type_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.transactions_type_var,
            values=["Все", "Покупка", "Продажа", "Дивиденды"],
            state="readonly",
            width=10
        )
        type_combo.pack(side=tk.LEFT, padx=(0, 10))
        type_combo.set("Все")
        
        ttk.Button(
            filter_frame,
            text="Применить",
            command=self._apply_transaction_filter
        ).pack(side=tk.LEFT)
        
        # Таблица транзакций
        columns = ("Дата", "Символ", "Тип", "Количество", "Цена", "Сумма", "Комиссия", "Баланс")
        self.transactions_tree = ttk.Treeview(transactions_frame, columns=columns, show='headings', height=8)
        
        # Настройка колонок
        for col in columns:
            self.transactions_tree.heading(col, text=col)
            self.transactions_tree.column(col, width=90, anchor='center')
        
        # Скроллбары
        trans_v_scrollbar = ttk.Scrollbar(transactions_frame, orient='vertical', command=self.transactions_tree.yview)
        trans_h_scrollbar = ttk.Scrollbar(transactions_frame, orient='horizontal', command=self.transactions_tree.xview)
        self.transactions_tree.configure(yscrollcommand=trans_v_scrollbar.set, xscrollcommand=trans_h_scrollbar.set)
        
        # Размещение
        self.transactions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        trans_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        trans_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
    
    def _create_dividends_table(self):
        """
        Создание таблицы дивидендов
        """
        # Фрейм для дивидендов
        dividends_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(dividends_frame, text="Дивиденды")
        
        # Таблица дивидендов
        columns = ("Дата", "Символ", "Тип", "Количество акций", "Дивиденд на акцию", "Общая сумма", "Налог")
        self.dividends_tree = ttk.Treeview(dividends_frame, columns=columns, show='headings', height=8)
        
        # Настройка колонок
        for col in columns:
            self.dividends_tree.heading(col, text=col)
            self.dividends_tree.column(col, width=100, anchor='center')
        
        # Скроллбары
        div_v_scrollbar = ttk.Scrollbar(dividends_frame, orient='vertical', command=self.dividends_tree.yview)
        div_h_scrollbar = ttk.Scrollbar(dividends_frame, orient='horizontal', command=self.dividends_tree.xview)
        self.dividends_tree.configure(yscrollcommand=div_v_scrollbar.set, xscrollcommand=div_h_scrollbar.set)
        
        # Размещение
        self.dividends_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        div_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        div_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=(10, 10), pady=(5, 0))
    
    def _create_metrics_table(self):
        """
        Создание таблицы метрик
        """
        # Фрейм для метрик
        metrics_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(metrics_frame, text="Метрики")
        
        # Таблица метрик
        columns = ("Метрика", "Значение", "Бенчмарк", "Статус", "Описание")
        self.metrics_tree = ttk.Treeview(metrics_frame, columns=columns, show='headings', height=8)
        
        # Настройка колонок
        column_widths = {"Метрика": 150, "Значение": 100, "Бенчмарк": 100, "Статус": 80, "Описание": 200}
        
        for col in columns:
            self.metrics_tree.heading(col, text=col)
            self.metrics_tree.column(col, width=column_widths.get(col, 100), anchor='center')
        
        # Скроллбары
        metrics_v_scrollbar = ttk.Scrollbar(metrics_frame, orient='vertical', command=self.metrics_tree.yview)
        metrics_h_scrollbar = ttk.Scrollbar(metrics_frame, orient='horizontal', command=self.metrics_tree.xview)
        self.metrics_tree.configure(yscrollcommand=metrics_v_scrollbar.set, xscrollcommand=metrics_h_scrollbar.set)
        
        # Размещение
        self.metrics_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        metrics_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        metrics_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=(10, 10), pady=(5, 0))
    
    def _start_auto_update(self):
        """
        Запуск автоматического обновления
        """
        def update_loop():
            while True:
                try:
                    # Обновление каждые 60 секунд
                    time.sleep(60)
                    
                    # Обновление данных в главном потоке
                    self.parent.after(0, self._auto_update)
                    
                except Exception as e:
                    logger.error(f"Ошибка в цикле автообновления портфеля: {e}")
        
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
            logger.error(f"Ошибка автообновления портфеля: {e}")
    
    def _update_allocation_chart(self, chart_type: str):
        """
        Обновление графика распределения активов
        
        Args:
            chart_type: Тип графика (pie, bar, treemap)
        """
        try:
            self.allocation_ax.clear()
            
            # Тестовые данные
            symbols = ['SBER', 'GAZP', 'LKOH', 'YNDX', 'MGNT', 'Денежные средства']
            values = [250000, 180000, 200000, 150000, 120000, 100000]
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
            
            if chart_type == "pie":
                wedges, texts, autotexts = self.allocation_ax.pie(
                    values, 
                    labels=symbols, 
                    colors=colors,
                    autopct='%1.1f%%',
                    startangle=90
                )
                
                # Улучшение внешнего вида
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                self.allocation_ax.set_title("Распределение активов в портфеле", fontsize=14, fontweight='bold')
                
            elif chart_type == "bar":
                bars = self.allocation_ax.bar(symbols, values, color=colors)
                
                # Добавление значений на столбцы
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    self.allocation_ax.text(bar.get_x() + bar.get_width()/2., height,
                                          f'{value:,.0f}₽',
                                          ha='center', va='bottom', fontweight='bold')
                
                self.allocation_ax.set_title("Стоимость активов в портфеле", fontsize=14, fontweight='bold')
                self.allocation_ax.set_ylabel("Стоимость (₽)")
                plt.setp(self.allocation_ax.xaxis.get_majorticklabels(), rotation=45)
            
            self.allocation_figure.tight_layout()
            self.allocation_canvas.draw()
            
        except Exception as e:
            logger.error(f"Ошибка обновления графика распределения: {e}")
    
    def _update_performance_chart(self, period: str):
        """
        Обновление графика производительности
        
        Args:
            period: Период отображения
        """
        try:
            self.allocation_ax.clear()
            
            # Генерация тестовых данных производительности
            if not self.performance_data:
                self._generate_performance_data()
            
            # Фильтрация данных по периоду
            filtered_data = self._filter_performance_data(period)
            
            if filtered_data:
                dates = [item['date'] for item in filtered_data]
                portfolio_values = [item['portfolio_value'] for item in filtered_data]
                benchmark_values = [item['benchmark_value'] for item in filtered_data]
                
                self.performance_ax.plot(dates, portfolio_values, linewidth=2, color='blue', label='Портфель')
                self.performance_ax.plot(dates, benchmark_values, linewidth=2, color='red', label='Бенчмарк', linestyle='--')
                
                # Заливка области между кривыми
                self.performance_ax.fill_between(dates, portfolio_values, benchmark_values, 
                                               where=np.array(portfolio_values) >= np.array(benchmark_values),
                                               color='green', alpha=0.3, interpolate=True, label='Превышение')
                self.performance_ax.fill_between(dates, portfolio_values, benchmark_values, 
                                               where=np.array(portfolio_values) < np.array(benchmark_values),
                                               color='red', alpha=0.3, interpolate=True, label='Отставание')
                
                self.performance_ax.set_title("Производительность портфеля", fontsize=14, fontweight='bold')
                self.performance_ax.set_xlabel("Дата")
                self.performance_ax.set_ylabel("Стоимость (₽)")
                self.performance_ax.legend()
                self.performance_ax.grid(True, alpha=0.3)
                
                plt.setp(self.performance_ax.xaxis.get_majorticklabels(), rotation=45)
            
            self.performance_figure.tight_layout()
            self.performance_canvas.draw()
            
        except Exception as e:
            logger.error(f"Ошибка обновления графика производительности: {e}")
    
    def _update_risk_chart(self, risk_type: str):
        """
        Обновление графика рисков
        
        Args:
            risk_type: Тип анализа рисков
        """
        try:
            self.risk_ax.clear()
            
            if risk_type == "var":
                # График Value at Risk
                symbols = ['SBER', 'GAZP', 'LKOH', 'YNDX', 'MGNT']
                var_95 = [12000, 8500, 15000, 18000, 9500]
                var_99 = [18000, 12500, 22000, 26000, 14000]
                
                x = np.arange(len(symbols))
                width = 0.35
                
                bars1 = self.risk_ax.bar(x - width/2, var_95, width, label='VaR 95%', color='orange', alpha=0.8)
                bars2 = self.risk_ax.bar(x + width/2, var_99, width, label='VaR 99%', color='red', alpha=0.8)
                
                self.risk_ax.set_title("Value at Risk по позициям", fontsize=14, fontweight='bold')
                self.risk_ax.set_ylabel("VaR (₽)")
                self.risk_ax.set_xticks(x)
                self.risk_ax.set_xticklabels(symbols)
                self.risk_ax.legend()
                self.risk_ax.grid(True, alpha=0.3)
                
            elif risk_type == "correlation":
                # Корреляционная матрица
                symbols = ['SBER', 'GAZP', 'LKOH', 'YNDX', 'MGNT']
                correlation_matrix = np.random.rand(5, 5)
                correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
                np.fill_diagonal(correlation_matrix, 1)
                
                im = self.risk_ax.imshow(correlation_matrix, cmap='RdYlBu', aspect='auto')
                self.risk_ax.set_xticks(range(len(symbols)))
                self.risk_ax.set_yticks(range(len(symbols)))
                self.risk_ax.set_xticklabels(symbols)
                self.risk_ax.set_yticklabels(symbols)
                self.risk_ax.set_title("Корреляционная матрица активов", fontsize=14, fontweight='bold')
                
                # Добавление значений корреляции
                for i in range(len(symbols)):
                    for j in range(len(symbols)):
                        text = self.risk_ax.text(j, i, f'{correlation_matrix[i, j]:.2f}',
                                               ha="center", va="center", color="black", fontweight='bold')
                
                plt.colorbar(im, ax=self.risk_ax)
                
            elif risk_type == "volatility":
                # График волатильности
                symbols = ['SBER', 'GAZP', 'LKOH', 'YNDX', 'MGNT']
                volatility = [15.2, 18.7, 22.1, 28.5, 16.8]
                colors = ['green' if v < 20 else 'orange' if v < 25 else 'red' for v in volatility]
                
                bars = self.risk_ax.bar(symbols, volatility, color=colors, alpha=0.8)
                
                # Добавление значений на столбцы
                for bar, vol in zip(bars, volatility):
                    height = bar.get_height()
                    self.risk_ax.text(bar.get_x() + bar.get_width()/2., height,
                                    f'{vol:.1f}%',
                                    ha='center', va='bottom', fontweight='bold')
                
                self.risk_ax.set_title("Волатильность активов (годовая)", fontsize=14, fontweight='bold')
                self.risk_ax.set_ylabel("Волатильность (%)")
                self.risk_ax.grid(True, alpha=0.3)
                
                # Добавление линий уровней риска
                self.risk_ax.axhline(y=20, color='orange', linestyle='--', alpha=0.7, label='Средний риск')
                self.risk_ax.axhline(y=25, color='red', linestyle='--', alpha=0.7, label='Высокий риск')
                self.risk_ax.legend()
            
            self.risk_figure.tight_layout()
            self.risk_canvas.draw()
            
        except Exception as e:
            logger.error(f"Ошибка обновления графика рисков: {e}")
    
    def _generate_performance_data(self):
        """
        Генерация тестовых данных производительности
        """
        try:
            from datetime import timedelta
            
            base_date = datetime.now() - timedelta(days=30)
            base_portfolio_value = 1000000
            base_benchmark_value = 1000000
            
            self.performance_data = []
            
            for i in range(30):
                date = base_date + timedelta(days=i)
                
                # Генерация случайных изменений
                portfolio_change = np.random.normal(0.001, 0.02)  # Среднее 0.1% в день, волатильность 2%
                benchmark_change = np.random.normal(0.0005, 0.015)  # Бенчмарк чуть хуже
                
                portfolio_value = base_portfolio_value * (1 + portfolio_change * (i + 1))
                benchmark_value = base_benchmark_value * (1 + benchmark_change * (i + 1))
                
                self.performance_data.append({
                    'date': date,
                    'portfolio_value': portfolio_value,
                    'benchmark_value': benchmark_value
                })
                
        except Exception as e:
            logger.error(f"Ошибка генерации данных производительности: {e}")
    
    def _filter_performance_data(self, period: str) -> List[Dict]:
        """
        Фильтрация данных производительности по периоду
        
        Args:
            period: Период фильтрации
            
        Returns:
            Отфильтрованные данные
        """
        try:
            if not self.performance_data or period == "ALL":
                return self.performance_data
            
            from datetime import timedelta
            now = datetime.now()
            
            if period == "1D":
                cutoff = now - timedelta(days=1)
            elif period == "1W":
                cutoff = now - timedelta(weeks=1)
            elif period == "1M":
                cutoff = now - timedelta(days=30)
            else:
                return self.performance_data
            
            return [item for item in self.performance_data if item['date'] >= cutoff]
            
        except Exception as e:
            logger.error(f"Ошибка фильтрации данных производительности: {e}")
            return self.performance_data
    
    def _refresh_positions(self):
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
                ("SBER", "100", "250.00", "255.00", "25,500", "+500", "+2.0%", "25.5%"),
                ("GAZP", "150", "180.00", "175.00", "26,250", "-750", "-2.8%", "26.3%"),
                ("LKOH", "10", "6500.00", "6600.00", "66,000", "+1,000", "+1.5%", "66.0%"),
                ("YNDX", "25", "3000.00", "3100.00", "77,500", "+2,500", "+3.3%", "77.5%"),
                ("MGNT", "50", "2400.00", "2350.00", "117,500", "-2,500", "-2.1%", "11.8%")
            ]
            
            for pos in test_positions:
                # Цветовое кодирование P&L
                pnl_percent = float(pos[6].replace('%', '').replace('+', ''))
                if pnl_percent > 0:
                    tags = ('positive',)
                elif pnl_percent < 0:
                    tags = ('negative',)
                else:
                    tags = ('neutral',)
                
                item_id = self.positions_tree.insert('', 'end', values=pos, tags=tags)
            
            # Настройка цветов
            self.positions_tree.tag_configure('positive', foreground='green')
            self.positions_tree.tag_configure('negative', foreground='red')
            self.positions_tree.tag_configure('neutral', foreground='gray')
            
            logger.debug("Таблица позиций обновлена")
            
        except Exception as e:
            logger.error(f"Ошибка обновления позиций: {e}")
    
    def _apply_transaction_filter(self):
        """
        Применение фильтра к транзакциям
        """
        try:
            # Очистка таблицы
            for item in self.transactions_tree.get_children():
                self.transactions_tree.delete(item)
            
            # Добавление отфильтрованных данных
            test_transactions = [
                ("2024-01-15", "SBER", "Покупка", "50", "250.00", "12,500", "6.25", "987,493.75"),
                ("2024-01-14", "GAZP", "Продажа", "25", "180.00", "4,500", "2.25", "999,997.75"),
                ("2024-01-13", "LKOH", "Покупка", "5", "6500.00", "32,500", "16.25", "995,499.75"),
                ("2024-01-12", "YNDX", "Покупка", "10", "3000.00", "30,000", "15.00", "1,028,015.00"),
                ("2024-01-11", "MGNT", "Покупка", "20", "2400.00", "48,000", "24.00", "1,058,039.00")
            ]
            
            for trans in test_transactions:
                self.transactions_tree.insert('', 'end', values=trans)
                
            logger.debug("Фильтр транзакций применен")
            
        except Exception as e:
            logger.error(f"Ошибка применения фильтра транзакций: {e}")
    
    def _show_positions_context_menu(self, event):
        """
        Показ контекстного меню для позиций
        
        Args:
            event: Событие клика
        """
        try:
            self.positions_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            logger.error(f"Ошибка показа контекстного меню позиций: {e}")
    
    def _on_position_double_click(self, event):
        """
        Обработка двойного клика по позиции
        
        Args:
            event: Событие клика
        """
        try:
            selection = self.positions_tree.selection()
            if selection:
                item = self.positions_tree.item(selection[0])
                values = item['values']
                self._show_position_details(values[0])  # Передаем символ
        except Exception as e:
            logger.error(f"Ошибка обработки двойного клика: {e}")
    
    def _show_position_details(self, symbol: str):
        """
        Показ детальной информации о позиции
        
        Args:
            symbol: Символ позиции
        """
        try:
            details = f"""
Детальная информация по позиции {symbol}:

Количество: 100 акций
Средняя цена покупки: 250.00 ₽
Текущая цена: 255.00 ₽
Рыночная стоимость: 25,500 ₽
Нереализованная прибыль: +500 ₽ (+2.0%)

Дата первой покупки: 2024-01-10
Количество сделок: 3
Общая комиссия: 15.75 ₽

Дивиденды получено: 150 ₽
Доходность с дивидендами: +2.6%
            """
            messagebox.showinfo(f"Позиция {symbol}", details)
        except Exception as e:
            logger.error(f"Ошибка показа деталей позиции: {e}")
    
    def _increase_position(self):
        """
        Увеличение позиции
        """
        selection = self.positions_tree.selection()
        if selection:
            item = self.positions_tree.item(selection[0])
            symbol = item['values'][0]
            messagebox.showinfo("Увеличение позиции", f"Функция увеличения позиции {symbol} в разработке")
    
    def _decrease_position(self):
        """
        Уменьшение позиции
        """
        selection = self.positions_tree.selection()
        if selection:
            item = self.positions_tree.item(selection[0])
            symbol = item['values'][0]
            messagebox.showinfo("Уменьшение позиции", f"Функция уменьшения позиции {symbol} в разработке")
    
    def _close_position(self):
        """
        Закрытие позиции
        """
        selection = self.positions_tree.selection()
        if selection:
            item = self.positions_tree.item(selection[0])
            symbol = item['values'][0]
            result = messagebox.askyesno("Закрытие позиции", f"Закрыть позицию по {symbol}?")
            if result:
                messagebox.showinfo("Информация", f"Позиция по {symbol} закрыта")
    
    def _analyze_position(self):
        """
        Анализ позиции
        """
        selection = self.positions_tree.selection()
        if selection:
            item = self.positions_tree.item(selection[0])
            symbol = item['values'][0]
            messagebox.showinfo("Анализ позиции", f"Функция анализа позиции {symbol} в разработке")
    
    def _show_position_history(self):
        """
        Показ истории позиции
        """
        selection = self.positions_tree.selection()
        if selection:
            item = self.positions_tree.item(selection[0])
            symbol = item['values'][0]
            messagebox.showinfo("История позиции", f"Функция истории позиции {symbol} в разработке")
    
    def _show_rebalancing(self):
        """
        Показ окна ребалансировки
        """
        messagebox.showinfo("Ребалансировка", "Функция ребалансировки портфеля в разработке")
    
    def _show_analysis(self):
        """
        Показ окна анализа портфеля
        """
        messagebox.showinfo("Анализ портфеля", "Функция анализа портфеля в разработке")
    
    def update_data(self, portfolio_data: Dict[str, Any]):
        """
        Обновление данных портфеля
        
        Args:
            portfolio_data: Данные портфеля
        """
        try:
            self.portfolio_data = portfolio_data
            
            # Обновление метрик
            if 'total_value' in portfolio_data:
                if hasattr(self, 'portfolio_metric_общая_стоимость'):
                    self.portfolio_metric_общая_стоимость.config(text=f"{portfolio_data['total_value']:,.0f} ₽")
            
            # Обновление таблиц
            self._refresh_positions()
            
        except Exception as e:
            logger.error(f"Ошибка обновления данных портфеля: {e}")
    
    def refresh_data(self):
        """
        Обновление всех данных панели
        """
        try:
            logger.debug("Обновление данных панели портфеля")
            
            # Обновление таблиц
            self._refresh_positions()
            self._apply_transaction_filter()
            
            # Обновление графиков
            self._update_allocation_chart("pie")
            self._update_performance_chart("1W")
            self._update_risk_chart("var")
            
        except Exception as e:
            logger.error(f"Ошибка обновления данных панели портфеля: {e}")
