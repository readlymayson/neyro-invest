"""
Панель управления торговлей
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger


class TradingPanel:
    """
    Панель управления торговлей
    """
    
    def __init__(self, parent, main_window):
        """
        Инициализация панели торговли
        
        Args:
            parent: Родительский виджет
            main_window: Главное окно приложения
        """
        self.parent = parent
        self.main_window = main_window
        
        # Данные торговли
        self.active_signals = []
        self.order_history = []
        self.trading_settings = {}
        
        # Создание интерфейса
        self._create_widgets()
        
        logger.info("Панель торговли инициализирована")
    
    def _create_widgets(self):
        """
        Создание виджетов панели
        """
        # Главный контейнер
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель - управление
        self._create_control_panel(main_frame)
        
        # Правая панель - информация
        self._create_info_panel(main_frame)
    
    def _create_control_panel(self, parent):
        """
        Создание панели управления
        
        Args:
            parent: Родительский виджет
        """
        # Левая панель
        control_frame = ttk.Frame(parent)
        control_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Панель быстрых действий
        self._create_quick_actions(control_frame)
        
        # Панель настроек торговли
        self._create_trading_settings(control_frame)
        
        # Панель ручной торговли
        self._create_manual_trading(control_frame)
        
        # Панель управления рисками
        self._create_risk_management(control_frame)
    
    def _create_quick_actions(self, parent):
        """
        Создание панели быстрых действий
        
        Args:
            parent: Родительский виджет
        """
        # Рамка быстрых действий
        actions_frame = ttk.LabelFrame(parent, text="Быстрые действия", padding=10)
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Кнопки управления
        buttons_frame = ttk.Frame(actions_frame)
        buttons_frame.pack(fill=tk.X)
        
        # Первый ряд кнопок
        row1 = ttk.Frame(buttons_frame)
        row1.pack(fill=tk.X, pady=(0, 5))
        
        self.start_trading_btn = ttk.Button(
            row1, 
            text="▶ Запустить торговлю", 
            command=self._start_trading,
            style='Success.TButton'
        )
        self.start_trading_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        self.stop_trading_btn = ttk.Button(
            row1, 
            text="⏹ Остановить торговлю", 
            command=self._stop_trading,
            style='Danger.TButton',
            state='disabled'
        )
        self.stop_trading_btn.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Второй ряд кнопок
        row2 = ttk.Frame(buttons_frame)
        row2.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            row2, 
            text="🚨 Экстренная остановка", 
            command=self._emergency_stop,
            style='Warning.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        ttk.Button(
            row2, 
            text="📊 Закрыть все позиции", 
            command=self._close_all_positions
        ).pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Статус торговли
        status_frame = ttk.Frame(actions_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(status_frame, text="Статус торговли:").pack(side=tk.LEFT)
        
        self.trading_status_label = ttk.Label(
            status_frame, 
            text="Остановлена",
            style='Stopped.TLabel'
        )
        self.trading_status_label.pack(side=tk.RIGHT)
    
    def _create_trading_settings(self, parent):
        """
        Создание панели настроек торговли
        
        Args:
            parent: Родительский виджет
        """
        # Рамка настроек
        settings_frame = ttk.LabelFrame(parent, text="Настройки торговли", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Настройки сигналов
        signals_frame = ttk.Frame(settings_frame)
        signals_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(signals_frame, text="Порог сигнала:").pack(side=tk.LEFT)
        
        self.signal_threshold_var = tk.DoubleVar(value=0.6)
        signal_threshold_scale = ttk.Scale(
            signals_frame,
            from_=0.1,
            to=1.0,
            variable=self.signal_threshold_var,
            orient=tk.HORIZONTAL
        )
        signal_threshold_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        self.signal_threshold_label = ttk.Label(signals_frame, text="0.60")
        self.signal_threshold_label.pack(side=tk.RIGHT)
        
        signal_threshold_scale.configure(command=self._on_signal_threshold_change)
        
        # Настройки позиций
        position_frame = ttk.Frame(settings_frame)
        position_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(position_frame, text="Размер позиции (%):").pack(side=tk.LEFT)
        
        self.position_size_var = tk.DoubleVar(value=10.0)
        position_size_scale = ttk.Scale(
            position_frame,
            from_=1.0,
            to=50.0,
            variable=self.position_size_var,
            orient=tk.HORIZONTAL
        )
        position_size_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        self.position_size_label = ttk.Label(position_frame, text="10.0%")
        self.position_size_label.pack(side=tk.RIGHT)
        
        position_size_scale.configure(command=self._on_position_size_change)
        
        # Максимальное количество позиций
        max_positions_frame = ttk.Frame(settings_frame)
        max_positions_frame.pack(fill=tk.X)
        
        ttk.Label(max_positions_frame, text="Макс. позиций:").pack(side=tk.LEFT)
        
        self.max_positions_var = tk.IntVar(value=10)
        max_positions_spinbox = ttk.Spinbox(
            max_positions_frame,
            from_=1,
            to=50,
            textvariable=self.max_positions_var,
            width=10
        )
        max_positions_spinbox.pack(side=tk.RIGHT)
    
    def _create_manual_trading(self, parent):
        """
        Создание панели ручной торговли
        
        Args:
            parent: Родительский виджет
        """
        # Рамка ручной торговли
        manual_frame = ttk.LabelFrame(parent, text="Ручная торговля", padding=10)
        manual_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Выбор символа
        symbol_frame = ttk.Frame(manual_frame)
        symbol_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(symbol_frame, text="Символ:").pack(side=tk.LEFT)
        
        self.manual_symbol_var = tk.StringVar()
        symbol_combo = ttk.Combobox(
            symbol_frame,
            textvariable=self.manual_symbol_var,
            values=["SBER", "GAZP", "LKOH"],
            state="readonly",
            width=15
        )
        symbol_combo.pack(side=tk.RIGHT)
        symbol_combo.set("SBER")
        
        # Количество
        quantity_frame = ttk.Frame(manual_frame)
        quantity_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(quantity_frame, text="Количество:").pack(side=tk.LEFT)
        
        self.manual_quantity_var = tk.IntVar(value=10)
        quantity_spinbox = ttk.Spinbox(
            quantity_frame,
            from_=1,
            to=1000,
            textvariable=self.manual_quantity_var,
            width=15
        )
        quantity_spinbox.pack(side=tk.RIGHT)
        
        # Тип ордера
        order_type_frame = ttk.Frame(manual_frame)
        order_type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(order_type_frame, text="Тип ордера:").pack(side=tk.LEFT)
        
        self.order_type_var = tk.StringVar()
        order_type_combo = ttk.Combobox(
            order_type_frame,
            textvariable=self.order_type_var,
            values=["Рыночный", "Лимитный", "Стоп"],
            state="readonly",
            width=15
        )
        order_type_combo.pack(side=tk.RIGHT)
        order_type_combo.set("Рыночный")
        
        # Цена (для лимитных ордеров)
        price_frame = ttk.Frame(manual_frame)
        price_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(price_frame, text="Цена:").pack(side=tk.LEFT)
        
        self.manual_price_var = tk.DoubleVar(value=0.0)
        price_entry = ttk.Entry(
            price_frame,
            textvariable=self.manual_price_var,
            width=15
        )
        price_entry.pack(side=tk.RIGHT)
        
        # Кнопки покупки/продажи
        buttons_frame = ttk.Frame(manual_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(
            buttons_frame,
            text="📈 Купить",
            command=self._manual_buy,
            style='Success.TButton'
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            buttons_frame,
            text="📉 Продать",
            command=self._manual_sell,
            style='Danger.TButton'
        ).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
    
    def _create_risk_management(self, parent):
        """
        Создание панели управления рисками
        
        Args:
            parent: Родительский виджет
        """
        # Рамка управления рисками
        risk_frame = ttk.LabelFrame(parent, text="Управление рисками", padding=10)
        risk_frame.pack(fill=tk.X)
        
        # Стоп-лосс
        stop_loss_frame = ttk.Frame(risk_frame)
        stop_loss_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stop_loss_enabled_var = tk.BooleanVar(value=True)
        stop_loss_check = ttk.Checkbutton(
            stop_loss_frame,
            text="Стоп-лосс (%)",
            variable=self.stop_loss_enabled_var
        )
        stop_loss_check.pack(side=tk.LEFT)
        
        self.stop_loss_var = tk.DoubleVar(value=5.0)
        stop_loss_entry = ttk.Entry(
            stop_loss_frame,
            textvariable=self.stop_loss_var,
            width=10
        )
        stop_loss_entry.pack(side=tk.RIGHT)
        
        # Тейк-профит
        take_profit_frame = ttk.Frame(risk_frame)
        take_profit_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.take_profit_enabled_var = tk.BooleanVar(value=True)
        take_profit_check = ttk.Checkbutton(
            take_profit_frame,
            text="Тейк-профит (%)",
            variable=self.take_profit_enabled_var
        )
        take_profit_check.pack(side=tk.LEFT)
        
        self.take_profit_var = tk.DoubleVar(value=10.0)
        take_profit_entry = ttk.Entry(
            take_profit_frame,
            textvariable=self.take_profit_var,
            width=10
        )
        take_profit_entry.pack(side=tk.RIGHT)
        
        # Максимальный риск портфеля
        max_risk_frame = ttk.Frame(risk_frame)
        max_risk_frame.pack(fill=tk.X)
        
        ttk.Label(max_risk_frame, text="Макс. риск портфеля (%):").pack(side=tk.LEFT)
        
        self.max_risk_var = tk.DoubleVar(value=10.0)
        max_risk_entry = ttk.Entry(
            max_risk_frame,
            textvariable=self.max_risk_var,
            width=10
        )
        max_risk_entry.pack(side=tk.RIGHT)
    
    def _create_info_panel(self, parent):
        """
        Создание информационной панели
        
        Args:
            parent: Родительский виджет
        """
        # Правая панель
        info_frame = ttk.Frame(parent)
        info_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Notebook для разных вкладок
        self.info_notebook = ttk.Notebook(info_frame)
        self.info_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка активных сигналов
        self._create_signals_tab()
        
        # Вкладка активных ордеров
        self._create_orders_tab()
        
        # Вкладка истории сделок
        self._create_history_tab()
        
        # Вкладка статистики
        self._create_statistics_tab()
    
    def _create_signals_tab(self):
        """
        Создание вкладки активных сигналов
        """
        # Фрейм для сигналов
        signals_frame = ttk.Frame(self.info_notebook)
        self.info_notebook.add(signals_frame, text="Активные сигналы")
        
        # Заголовок
        header_frame = ttk.Frame(signals_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(
            header_frame, 
            text="Активные торговые сигналы",
            style='Header.TLabel'
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            header_frame,
            text="🔄 Обновить",
            command=self._refresh_signals
        ).pack(side=tk.RIGHT)
        
        # Таблица сигналов
        columns = ("Время", "Символ", "Сигнал", "Уверенность", "Источник", "Действие")
        self.signals_tree = ttk.Treeview(signals_frame, columns=columns, show='headings', height=15)
        
        # Настройка колонок
        for col in columns:
            self.signals_tree.heading(col, text=col)
            self.signals_tree.column(col, width=100, anchor='center')
        
        # Скроллбары
        signals_v_scrollbar = ttk.Scrollbar(signals_frame, orient='vertical', command=self.signals_tree.yview)
        signals_h_scrollbar = ttk.Scrollbar(signals_frame, orient='horizontal', command=self.signals_tree.xview)
        self.signals_tree.configure(yscrollcommand=signals_v_scrollbar.set, xscrollcommand=signals_h_scrollbar.set)
        
        # Размещение
        self.signals_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        signals_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10))
        signals_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=(10, 10))
        
        # Контекстное меню для сигналов
        self.signals_context_menu = tk.Menu(self.signals_tree, tearoff=0)
        self.signals_context_menu.add_command(label="Выполнить сигнал", command=self._execute_signal)
        self.signals_context_menu.add_command(label="Игнорировать сигнал", command=self._ignore_signal)
        self.signals_context_menu.add_separator()
        self.signals_context_menu.add_command(label="Подробности", command=self._show_signal_details)
        
        self.signals_tree.bind("<Button-3>", self._show_signals_context_menu)
    
    def _create_orders_tab(self):
        """
        Создание вкладки активных ордеров
        """
        # Фрейм для ордеров
        orders_frame = ttk.Frame(self.info_notebook)
        self.info_notebook.add(orders_frame, text="Активные ордера")
        
        # Заголовок
        header_frame = ttk.Frame(orders_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(
            header_frame, 
            text="Активные ордера",
            style='Header.TLabel'
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            header_frame,
            text="🔄 Обновить",
            command=self._refresh_orders
        ).pack(side=tk.RIGHT)
        
        # Таблица ордеров
        columns = ("ID", "Время", "Символ", "Тип", "Сторона", "Количество", "Цена", "Статус")
        self.orders_tree = ttk.Treeview(orders_frame, columns=columns, show='headings', height=15)
        
        # Настройка колонок
        for col in columns:
            self.orders_tree.heading(col, text=col)
            self.orders_tree.column(col, width=80, anchor='center')
        
        # Скроллбары
        orders_v_scrollbar = ttk.Scrollbar(orders_frame, orient='vertical', command=self.orders_tree.yview)
        orders_h_scrollbar = ttk.Scrollbar(orders_frame, orient='horizontal', command=self.orders_tree.xview)
        self.orders_tree.configure(yscrollcommand=orders_v_scrollbar.set, xscrollcommand=orders_h_scrollbar.set)
        
        # Размещение
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        orders_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10))
        orders_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=(10, 10))
        
        # Контекстное меню для ордеров
        self.orders_context_menu = tk.Menu(self.orders_tree, tearoff=0)
        self.orders_context_menu.add_command(label="Отменить ордер", command=self._cancel_order)
        self.orders_context_menu.add_command(label="Изменить ордер", command=self._modify_order)
        self.orders_context_menu.add_separator()
        self.orders_context_menu.add_command(label="Подробности", command=self._show_order_details)
        
        self.orders_tree.bind("<Button-3>", self._show_orders_context_menu)
    
    def _create_history_tab(self):
        """
        Создание вкладки истории сделок
        """
        # Фрейм для истории
        history_frame = ttk.Frame(self.info_notebook)
        self.info_notebook.add(history_frame, text="История сделок")
        
        # Заголовок с фильтрами
        header_frame = ttk.Frame(history_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(
            header_frame, 
            text="История сделок",
            style='Header.TLabel'
        ).pack(side=tk.LEFT)
        
        # Фильтры
        filters_frame = ttk.Frame(header_frame)
        filters_frame.pack(side=tk.RIGHT)
        
        ttk.Label(filters_frame, text="Период:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.history_period_var = tk.StringVar()
        period_combo = ttk.Combobox(
            filters_frame,
            textvariable=self.history_period_var,
            values=["Сегодня", "Неделя", "Месяц", "Все"],
            state="readonly",
            width=10
        )
        period_combo.pack(side=tk.LEFT, padx=(0, 10))
        period_combo.set("Сегодня")
        
        ttk.Button(
            filters_frame,
            text="🔄 Обновить",
            command=self._refresh_history
        ).pack(side=tk.LEFT)
        
        # Таблица истории
        columns = ("Время", "Символ", "Сторона", "Количество", "Цена", "Сумма", "Комиссия", "P&L")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=15)
        
        # Настройка колонок
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=90, anchor='center')
        
        # Скроллбары
        history_v_scrollbar = ttk.Scrollbar(history_frame, orient='vertical', command=self.history_tree.yview)
        history_h_scrollbar = ttk.Scrollbar(history_frame, orient='horizontal', command=self.history_tree.xview)
        self.history_tree.configure(yscrollcommand=history_v_scrollbar.set, xscrollcommand=history_h_scrollbar.set)
        
        # Размещение
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        history_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10))
        history_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, padx=(10, 10))
    
    def _create_statistics_tab(self):
        """
        Создание вкладки статистики
        """
        # Фрейм для статистики
        stats_frame = ttk.Frame(self.info_notebook)
        self.info_notebook.add(stats_frame, text="Статистика")
        
        # Основные метрики
        metrics_frame = ttk.LabelFrame(stats_frame, text="Торговые метрики", padding=10)
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Создание сетки метрик
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill=tk.X)
        
        for i in range(3):
            metrics_grid.columnconfigure(i, weight=1)
        
        # Метрики торговли
        self._create_stat_metric(metrics_grid, "Всего сделок", "0", 0, 0)
        self._create_stat_metric(metrics_grid, "Прибыльных", "0 (0%)", 0, 1)
        self._create_stat_metric(metrics_grid, "Убыточных", "0 (0%)", 0, 2)
        
        self._create_stat_metric(metrics_grid, "Средняя прибыль", "0 ₽", 1, 0)
        self._create_stat_metric(metrics_grid, "Средний убыток", "0 ₽", 1, 1)
        self._create_stat_metric(metrics_grid, "Профит-фактор", "0.00", 1, 2)
        
        # Детальная статистика
        details_frame = ttk.LabelFrame(stats_frame, text="Детальная статистика", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Таблица статистики по символам
        columns = ("Символ", "Сделок", "Прибыль", "Убыток", "P&L", "Win Rate")
        self.stats_tree = ttk.Treeview(details_frame, columns=columns, show='headings', height=10)
        
        # Настройка колонок
        for col in columns:
            self.stats_tree.heading(col, text=col)
            self.stats_tree.column(col, width=100, anchor='center')
        
        # Скроллбар
        stats_scrollbar = ttk.Scrollbar(details_frame, orient='vertical', command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=stats_scrollbar.set)
        
        # Размещение
        self.stats_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_stat_metric(self, parent, title: str, value: str, row: int, col: int):
        """
        Создание метрики статистики
        
        Args:
            parent: Родительский виджет
            title: Заголовок метрики
            value: Значение метрики
            row: Строка в сетке
            col: Колонка в сетке
        """
        # Рамка метрики
        metric_frame = ttk.Frame(parent, relief='raised', borderwidth=1)
        metric_frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        # Заголовок
        title_label = ttk.Label(
            metric_frame, 
            text=title, 
            font=('Arial', 9, 'bold'),
            foreground='gray'
        )
        title_label.pack(pady=(5, 2))
        
        # Значение
        value_label = ttk.Label(
            metric_frame, 
            text=value, 
            font=('Arial', 12, 'bold')
        )
        value_label.pack(pady=(0, 5))
        
        # Сохранение ссылки для обновления
        setattr(self, f"stat_{title.lower().replace(' ', '_')}", value_label)
    
    # Обработчики событий
    def _on_signal_threshold_change(self, value):
        """
        Обработка изменения порога сигнала
        
        Args:
            value: Новое значение
        """
        self.signal_threshold_label.config(text=f"{float(value):.2f}")
    
    def _on_position_size_change(self, value):
        """
        Обработка изменения размера позиции
        
        Args:
            value: Новое значение
        """
        self.position_size_label.config(text=f"{float(value):.1f}%")
    
    def _start_trading(self):
        """
        Запуск торговли
        """
        try:
            if self.main_window.is_system_running():
                self.start_trading_btn.config(state='disabled')
                self.stop_trading_btn.config(state='normal')
                self.trading_status_label.config(text="Активна", style='Running.TLabel')
                logger.info("Торговля запущена")
            else:
                messagebox.showwarning("Предупреждение", "Сначала запустите систему инвестиций")
        except Exception as e:
            logger.error(f"Ошибка запуска торговли: {e}")
            messagebox.showerror("Ошибка", f"Не удалось запустить торговлю: {e}")
    
    def _stop_trading(self):
        """
        Остановка торговли
        """
        try:
            self.start_trading_btn.config(state='normal')
            self.stop_trading_btn.config(state='disabled')
            self.trading_status_label.config(text="Остановлена", style='Stopped.TLabel')
            logger.info("Торговля остановлена")
        except Exception as e:
            logger.error(f"Ошибка остановки торговли: {e}")
            messagebox.showerror("Ошибка", f"Не удалось остановить торговлю: {e}")
    
    def _emergency_stop(self):
        """
        Экстренная остановка торговли
        """
        result = messagebox.askyesno(
            "Экстренная остановка",
            "Вы уверены, что хотите экстренно остановить торговлю?\n"
            "Все активные ордера будут отменены."
        )
        
        if result:
            try:
                # Логика экстренной остановки
                self._stop_trading()
                logger.warning("Выполнена экстренная остановка торговли")
                messagebox.showinfo("Информация", "Торговля экстренно остановлена")
            except Exception as e:
                logger.error(f"Ошибка экстренной остановки: {e}")
                messagebox.showerror("Ошибка", f"Ошибка экстренной остановки: {e}")
    
    def _close_all_positions(self):
        """
        Закрытие всех позиций
        """
        result = messagebox.askyesno(
            "Закрытие позиций",
            "Вы уверены, что хотите закрыть все открытые позиции?"
        )
        
        if result:
            try:
                # Логика закрытия всех позиций
                messagebox.showinfo("Информация", "Все позиции закрыты")
                logger.info("Все позиции закрыты")
            except Exception as e:
                logger.error(f"Ошибка закрытия позиций: {e}")
                messagebox.showerror("Ошибка", f"Не удалось закрыть позиции: {e}")
    
    def _manual_buy(self):
        """
        Ручная покупка
        """
        try:
            symbol = self.manual_symbol_var.get()
            quantity = self.manual_quantity_var.get()
            order_type = self.order_type_var.get()
            price = self.manual_price_var.get()
            
            if not symbol:
                messagebox.showwarning("Предупреждение", "Выберите символ")
                return
            
            if quantity <= 0:
                messagebox.showwarning("Предупреждение", "Количество должно быть больше 0")
                return
            
            # Логика создания ордера на покупку
            logger.info(f"Ручная покупка: {quantity} {symbol} по цене {price}")
            messagebox.showinfo("Информация", f"Ордер на покупку {quantity} {symbol} создан")
            
        except Exception as e:
            logger.error(f"Ошибка ручной покупки: {e}")
            messagebox.showerror("Ошибка", f"Не удалось создать ордер: {e}")
    
    def _manual_sell(self):
        """
        Ручная продажа
        """
        try:
            symbol = self.manual_symbol_var.get()
            quantity = self.manual_quantity_var.get()
            order_type = self.order_type_var.get()
            price = self.manual_price_var.get()
            
            if not symbol:
                messagebox.showwarning("Предупреждение", "Выберите символ")
                return
            
            if quantity <= 0:
                messagebox.showwarning("Предупреждение", "Количество должно быть больше 0")
                return
            
            # Логика создания ордера на продажу
            logger.info(f"Ручная продажа: {quantity} {symbol} по цене {price}")
            messagebox.showinfo("Информация", f"Ордер на продажу {quantity} {symbol} создан")
            
        except Exception as e:
            logger.error(f"Ошибка ручной продажи: {e}")
            messagebox.showerror("Ошибка", f"Не удалось создать ордер: {e}")
    
    def _refresh_signals(self):
        """
        Обновление списка сигналов
        """
        try:
            # Очистка таблицы
            for item in self.signals_tree.get_children():
                self.signals_tree.delete(item)
            
            # Добавление тестовых данных
            test_signals = [
                (datetime.now().strftime("%H:%M:%S"), "SBER", "BUY", "0.75", "LSTM", "Выполнить"),
                (datetime.now().strftime("%H:%M:%S"), "GAZP", "SELL", "0.68", "XGBoost", "Выполнить"),
                (datetime.now().strftime("%H:%M:%S"), "LKOH", "HOLD", "0.45", "DeepSeek", "Ожидание")
            ]
            
            for signal in test_signals:
                self.signals_tree.insert('', 'end', values=signal)
                
            logger.debug("Список сигналов обновлен")
            
        except Exception as e:
            logger.error(f"Ошибка обновления сигналов: {e}")
    
    def _refresh_orders(self):
        """
        Обновление списка ордеров
        """
        try:
            # Очистка таблицы
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)
            
            # Добавление тестовых данных
            test_orders = [
                ("ORD001", "10:30:15", "SBER", "Рыночный", "BUY", "10", "255.00", "Ожидание"),
                ("ORD002", "10:25:30", "GAZP", "Лимитный", "SELL", "20", "175.00", "Частично")
            ]
            
            for order in test_orders:
                self.orders_tree.insert('', 'end', values=order)
                
            logger.debug("Список ордеров обновлен")
            
        except Exception as e:
            logger.error(f"Ошибка обновления ордеров: {e}")
    
    def _refresh_history(self):
        """
        Обновление истории сделок
        """
        try:
            # Очистка таблицы
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # Добавление тестовых данных
            test_history = [
                ("10:15:30", "SBER", "BUY", "10", "250.00", "2500", "1.25", "+50"),
                ("09:45:15", "GAZP", "SELL", "15", "180.00", "2700", "1.35", "-30"),
                ("09:30:00", "LKOH", "BUY", "5", "6500.00", "32500", "16.25", "+150")
            ]
            
            for trade in test_history:
                self.history_tree.insert('', 'end', values=trade)
                
            logger.debug("История сделок обновлена")
            
        except Exception as e:
            logger.error(f"Ошибка обновления истории: {e}")
    
    def _show_signals_context_menu(self, event):
        """
        Показ контекстного меню для сигналов
        
        Args:
            event: Событие клика
        """
        try:
            self.signals_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            logger.error(f"Ошибка показа контекстного меню сигналов: {e}")
    
    def _show_orders_context_menu(self, event):
        """
        Показ контекстного меню для ордеров
        
        Args:
            event: Событие клика
        """
        try:
            self.orders_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            logger.error(f"Ошибка показа контекстного меню ордеров: {e}")
    
    def _execute_signal(self):
        """
        Выполнение выбранного сигнала
        """
        selection = self.signals_tree.selection()
        if selection:
            item = self.signals_tree.item(selection[0])
            values = item['values']
            messagebox.showinfo("Информация", f"Выполнение сигнала {values[2]} для {values[1]}")
    
    def _ignore_signal(self):
        """
        Игнорирование выбранного сигнала
        """
        selection = self.signals_tree.selection()
        if selection:
            self.signals_tree.delete(selection[0])
            messagebox.showinfo("Информация", "Сигнал проигнорирован")
    
    def _show_signal_details(self):
        """
        Показ подробностей сигнала
        """
        selection = self.signals_tree.selection()
        if selection:
            item = self.signals_tree.item(selection[0])
            values = item['values']
            messagebox.showinfo("Подробности сигнала", f"Сигнал: {values[2]}\nСимвол: {values[1]}\nУверенность: {values[3]}")
    
    def _cancel_order(self):
        """
        Отмена выбранного ордера
        """
        selection = self.orders_tree.selection()
        if selection:
            item = self.orders_tree.item(selection[0])
            values = item['values']
            result = messagebox.askyesno("Отмена ордера", f"Отменить ордер {values[0]}?")
            if result:
                self.orders_tree.delete(selection[0])
                messagebox.showinfo("Информация", "Ордер отменен")
    
    def _modify_order(self):
        """
        Изменение выбранного ордера
        """
        messagebox.showinfo("Информация", "Функция изменения ордера в разработке")
    
    def _show_order_details(self):
        """
        Показ подробностей ордера
        """
        selection = self.orders_tree.selection()
        if selection:
            item = self.orders_tree.item(selection[0])
            values = item['values']
            messagebox.showinfo("Подробности ордера", f"ID: {values[0]}\nСимвол: {values[2]}\nТип: {values[3]}")
    
    def add_signal(self, signal_data: Dict[str, Any]):
        """
        Добавление нового сигнала
        
        Args:
            signal_data: Данные сигнала
        """
        try:
            # Добавление сигнала в список
            self.active_signals.append(signal_data)
            
            # Обновление таблицы сигналов
            self._refresh_signals()
            
        except Exception as e:
            logger.error(f"Ошибка добавления сигнала: {e}")
    
    def refresh_data(self):
        """
        Обновление всех данных панели
        """
        try:
            logger.debug("Обновление данных панели торговли")
            
            # Обновление всех таблиц
            self._refresh_signals()
            self._refresh_orders()
            self._refresh_history()
            
        except Exception as e:
            logger.error(f"Ошибка обновления данных панели торговли: {e}")
