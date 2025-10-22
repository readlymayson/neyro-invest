"""
Панель управления конфигурацией
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional
import yaml
import os
from pathlib import Path
from loguru import logger


class ConfigPanel:
    """
    Панель управления конфигурацией системы
    """
    
    def __init__(self, parent, main_window):
        """
        Инициализация панели конфигурации
        
        Args:
            parent: Родительский виджет
            main_window: Главное окно приложения
        """
        self.parent = parent
        self.main_window = main_window
        
        # Текущая конфигурация
        self.current_config = {}
        self.current_config_path = "config/main.yaml"
        self.config_modified = False
        
        # Создание интерфейса
        self._create_widgets()
        
        # Загрузка конфигурации
        self._load_config()
        
        logger.info("Панель конфигурации инициализирована")
    
    def _create_widgets(self):
        """
        Создание виджетов панели
        """
        # Главный контейнер
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель - управление файлами
        self._create_file_panel(main_frame)
        
        # Основная панель - настройки
        self._create_settings_panel(main_frame)
        
        # Нижняя панель - кнопки действий
        self._create_actions_panel(main_frame)
    
    def _create_file_panel(self, parent):
        """
        Создание панели управления файлами конфигурации
        
        Args:
            parent: Родительский виджет
        """
        # Рамка управления файлами
        file_frame = ttk.LabelFrame(parent, text="Управление конфигурацией", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Выбор файла конфигурации
        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(file_select_frame, text="Файл конфигурации:").pack(side=tk.LEFT)
        
        self.config_file_var = tk.StringVar(value=self.current_config_path)
        config_file_entry = ttk.Entry(
            file_select_frame,
            textvariable=self.config_file_var,
            state='readonly',
            width=50
        )
        config_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        ttk.Button(
            file_select_frame,
            text="Обзор...",
            command=self._browse_config_file
        ).pack(side=tk.RIGHT)
        
        # Кнопки управления файлами
        buttons_frame = ttk.Frame(file_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(
            buttons_frame,
            text="📂 Новый",
            command=self.new_config
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            buttons_frame,
            text="📁 Открыть",
            command=self.open_config
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            buttons_frame,
            text="💾 Сохранить",
            command=self.save_config
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            buttons_frame,
            text="💾 Сохранить как...",
            command=self._save_config_as
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            buttons_frame,
            text="🔄 Перезагрузить",
            command=self.reload_config
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Шаблоны конфигурации
        templates_frame = ttk.Frame(file_frame)
        templates_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(templates_frame, text="Шаблоны:").pack(side=tk.LEFT)
        
        ttk.Button(
            templates_frame,
            text="Консервативный",
            command=lambda: self._load_template("conservative_investing.yaml")
        ).pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Button(
            templates_frame,
            text="Агрессивный",
            command=lambda: self._load_template("aggressive_trading.yaml")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            templates_frame,
            text="По умолчанию",
            command=lambda: self._load_template("main.yaml")
        ).pack(side=tk.LEFT, padx=(0, 5))
    
    def _create_settings_panel(self, parent):
        """
        Создание панели настроек
        
        Args:
            parent: Родительский виджет
        """
        # Notebook для разных категорий настроек
        self.settings_notebook = ttk.Notebook(parent)
        self.settings_notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Вкладка данных
        self._create_data_settings()
        
        # Вкладка нейросетей
        self._create_neural_settings()
        
        # Вкладка торговли
        self._create_trading_settings()
        
        # Вкладка портфеля
        self._create_portfolio_settings()
        
        # Вкладка логирования
        self._create_logging_settings()
        
        # Вкладка уведомлений
        self._create_notifications_settings()
    
    def _create_data_settings(self):
        """
        Создание настроек данных
        """
        # Фрейм для настроек данных
        data_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(data_frame, text="Данные")
        
        # Прокручиваемый фрейм
        canvas = tk.Canvas(data_frame)
        scrollbar = ttk.Scrollbar(data_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Провайдер данных
        provider_frame = ttk.LabelFrame(scrollable_frame, text="Провайдер данных", padding=10)
        provider_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(provider_frame, text="Провайдер:").grid(row=0, column=0, sticky='w', pady=2)
        self.data_provider_var = tk.StringVar()
        provider_combo = ttk.Combobox(
            provider_frame,
            textvariable=self.data_provider_var,
            values=["yfinance", "tinkoff", "sber", "moex"],
            state="readonly"
        )
        provider_combo.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Символы для торговли
        symbols_frame = ttk.LabelFrame(scrollable_frame, text="Торговые инструменты", padding=10)
        symbols_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(symbols_frame, text="Символы:").grid(row=0, column=0, sticky='nw', pady=2)
        
        self.symbols_text = tk.Text(symbols_frame, height=4, width=40)
        self.symbols_text.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        symbols_scroll = ttk.Scrollbar(symbols_frame, orient='vertical', command=self.symbols_text.yview)
        symbols_scroll.grid(row=0, column=2, sticky='ns', pady=2)
        self.symbols_text.configure(yscrollcommand=symbols_scroll.set)
        
        # Интервалы обновления
        intervals_frame = ttk.LabelFrame(scrollable_frame, text="Интервалы обновления", padding=10)
        intervals_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(intervals_frame, text="Интервал обновления (сек):").grid(row=0, column=0, sticky='w', pady=2)
        self.update_interval_var = tk.IntVar()
        ttk.Spinbox(
            intervals_frame,
            from_=60,
            to=3600,
            textvariable=self.update_interval_var,
            width=10
        ).grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        
        ttk.Label(intervals_frame, text="История (дней):").grid(row=1, column=0, sticky='w', pady=2)
        self.history_days_var = tk.IntVar()
        ttk.Spinbox(
            intervals_frame,
            from_=30,
            to=1095,
            textvariable=self.history_days_var,
            width=10
        ).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        
        # Настройка сетки
        provider_frame.columnconfigure(1, weight=1)
        symbols_frame.columnconfigure(1, weight=1)
        intervals_frame.columnconfigure(1, weight=1)
        
        # Размещение canvas и scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_neural_settings(self):
        """
        Создание настроек нейросетей
        """
        # Фрейм для настроек нейросетей
        neural_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(neural_frame, text="Нейросети")
        
        # Прокручиваемый фрейм
        canvas = tk.Canvas(neural_frame)
        scrollbar = ttk.Scrollbar(neural_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Общие настройки
        general_frame = ttk.LabelFrame(scrollable_frame, text="Общие настройки", padding=10)
        general_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(general_frame, text="Интервал анализа (сек):").grid(row=0, column=0, sticky='w', pady=2)
        self.analysis_interval_var = tk.IntVar()
        ttk.Spinbox(
            general_frame,
            from_=300,
            to=7200,
            textvariable=self.analysis_interval_var,
            width=10
        ).grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        
        ttk.Label(general_frame, text="Метод ансамбля:").grid(row=1, column=0, sticky='w', pady=2)
        self.ensemble_method_var = tk.StringVar()
        ensemble_combo = ttk.Combobox(
            general_frame,
            textvariable=self.ensemble_method_var,
            values=["weighted_average", "majority_vote", "confidence_weighted"],
            state="readonly"
        )
        ensemble_combo.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Настройки LSTM
        lstm_frame = ttk.LabelFrame(scrollable_frame, text="LSTM модель", padding=10)
        lstm_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.lstm_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(
            lstm_frame,
            text="Включить LSTM",
            variable=self.lstm_enabled_var
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=2)
        
        ttk.Label(lstm_frame, text="Вес модели:").grid(row=1, column=0, sticky='w', pady=2)
        self.lstm_weight_var = tk.DoubleVar()
        ttk.Scale(
            lstm_frame,
            from_=0.0,
            to=1.0,
            variable=self.lstm_weight_var,
            orient=tk.HORIZONTAL
        ).grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ttk.Label(lstm_frame, text="Длина последовательности:").grid(row=2, column=0, sticky='w', pady=2)
        self.lstm_sequence_var = tk.IntVar()
        ttk.Spinbox(
            lstm_frame,
            from_=10,
            to=200,
            textvariable=self.lstm_sequence_var,
            width=10
        ).grid(row=2, column=1, sticky='w', padx=(10, 0), pady=2)
        
        # Настройки XGBoost
        xgb_frame = ttk.LabelFrame(scrollable_frame, text="XGBoost модель", padding=10)
        xgb_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.xgb_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(
            xgb_frame,
            text="Включить XGBoost",
            variable=self.xgb_enabled_var
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=2)
        
        ttk.Label(xgb_frame, text="Вес модели:").grid(row=1, column=0, sticky='w', pady=2)
        self.xgb_weight_var = tk.DoubleVar()
        ttk.Scale(
            xgb_frame,
            from_=0.0,
            to=1.0,
            variable=self.xgb_weight_var,
            orient=tk.HORIZONTAL
        ).grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ttk.Label(xgb_frame, text="Количество деревьев:").grid(row=2, column=0, sticky='w', pady=2)
        self.xgb_estimators_var = tk.IntVar()
        ttk.Spinbox(
            xgb_frame,
            from_=50,
            to=500,
            textvariable=self.xgb_estimators_var,
            width=10
        ).grid(row=2, column=1, sticky='w', padx=(10, 0), pady=2)
        
        # Настройки DeepSeek
        deepseek_frame = ttk.LabelFrame(scrollable_frame, text="DeepSeek модель", padding=10)
        deepseek_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.deepseek_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(
            deepseek_frame,
            text="Включить DeepSeek",
            variable=self.deepseek_enabled_var
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=2)
        
        ttk.Label(deepseek_frame, text="Вес модели:").grid(row=1, column=0, sticky='w', pady=2)
        self.deepseek_weight_var = tk.DoubleVar()
        ttk.Scale(
            deepseek_frame,
            from_=0.0,
            to=1.0,
            variable=self.deepseek_weight_var,
            orient=tk.HORIZONTAL
        ).grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ttk.Label(deepseek_frame, text="API ключ:").grid(row=2, column=0, sticky='w', pady=2)
        self.deepseek_api_key_var = tk.StringVar()
        ttk.Entry(
            deepseek_frame,
            textvariable=self.deepseek_api_key_var,
            show="*",
            width=30
        ).grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Настройка сетки
        general_frame.columnconfigure(1, weight=1)
        lstm_frame.columnconfigure(1, weight=1)
        xgb_frame.columnconfigure(1, weight=1)
        deepseek_frame.columnconfigure(1, weight=1)
        
        # Размещение canvas и scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_trading_settings(self):
        """
        Создание настроек торговли
        """
        # Фрейм для настроек торговли
        trading_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(trading_frame, text="Торговля")
        
        # Прокручиваемый фрейм
        canvas = tk.Canvas(trading_frame)
        scrollbar = ttk.Scrollbar(trading_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Основные настройки
        basic_frame = ttk.LabelFrame(scrollable_frame, text="Основные настройки", padding=10)
        basic_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(basic_frame, text="Брокер:").grid(row=0, column=0, sticky='w', pady=2)
        self.broker_var = tk.StringVar()
        broker_combo = ttk.Combobox(
            basic_frame,
            textvariable=self.broker_var,
            values=["paper", "tinkoff", "sber"],
            state="readonly"
        )
        broker_combo.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ttk.Label(basic_frame, text="Порог сигнала:").grid(row=1, column=0, sticky='w', pady=2)
        self.signal_threshold_var = tk.DoubleVar()
        ttk.Scale(
            basic_frame,
            from_=0.1,
            to=1.0,
            variable=self.signal_threshold_var,
            orient=tk.HORIZONTAL
        ).grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ttk.Label(basic_frame, text="Интервал проверки сигналов (сек):").grid(row=2, column=0, sticky='w', pady=2)
        self.signal_check_interval_var = tk.IntVar()
        ttk.Spinbox(
            basic_frame,
            from_=60,
            to=3600,
            textvariable=self.signal_check_interval_var,
            width=10
        ).grid(row=2, column=1, sticky='w', padx=(10, 0), pady=2)
        
        # Настройки позиций
        positions_frame = ttk.LabelFrame(scrollable_frame, text="Управление позициями", padding=10)
        positions_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(positions_frame, text="Максимум позиций:").grid(row=0, column=0, sticky='w', pady=2)
        self.max_positions_var = tk.IntVar()
        ttk.Spinbox(
            positions_frame,
            from_=1,
            to=50,
            textvariable=self.max_positions_var,
            width=10
        ).grid(row=0, column=1, sticky='w', padx=(10, 0), pady=2)
        
        ttk.Label(positions_frame, text="Размер позиции (% от капитала):").grid(row=1, column=0, sticky='w', pady=2)
        self.position_size_var = tk.DoubleVar()
        ttk.Scale(
            positions_frame,
            from_=0.01,
            to=0.5,
            variable=self.position_size_var,
            orient=tk.HORIZONTAL
        ).grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ttk.Label(positions_frame, text="Мин. интервал между сделками (сек):").grid(row=2, column=0, sticky='w', pady=2)
        self.min_trade_interval_var = tk.IntVar()
        ttk.Spinbox(
            positions_frame,
            from_=300,
            to=86400,
            textvariable=self.min_trade_interval_var,
            width=10
        ).grid(row=2, column=1, sticky='w', padx=(10, 0), pady=2)
        
        # Настройки брокера
        broker_settings_frame = ttk.LabelFrame(scrollable_frame, text="Настройки брокера T-Bank", padding=10)
        broker_settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(broker_settings_frame, text="T-Bank токен:").grid(row=0, column=0, sticky='w', pady=2)
        self.tinkoff_token_var = tk.StringVar()
        ttk.Entry(
            broker_settings_frame,
            textvariable=self.tinkoff_token_var,
            show="*",
            width=30
        ).grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ttk.Button(
            broker_settings_frame,
            text="ℹ️ Как получить",
            command=self._show_token_help
        ).grid(row=0, column=2, padx=(5, 0), pady=2)
        
        self.sandbox_mode_var = tk.BooleanVar()
        ttk.Checkbutton(
            broker_settings_frame,
            text="Режим песочницы (sandbox)",
            variable=self.sandbox_mode_var
        ).grid(row=1, column=0, columnspan=3, sticky='w', pady=2)
        
        # Информация о счете
        account_info_frame = ttk.Frame(broker_settings_frame)
        account_info_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(10, 0))
        
        ttk.Button(
            account_info_frame,
            text="📊 Проверить подключение",
            command=self._check_tbank_connection
        ).pack(side=tk.LEFT)
        
        ttk.Label(broker_settings_frame, text="Sber токен:").grid(row=3, column=0, sticky='w', pady=(10, 2))
        self.sber_token_var = tk.StringVar()
        ttk.Entry(
            broker_settings_frame,
            textvariable=self.sber_token_var,
            show="*",
            width=30,
            state='disabled'  # Пока не реализовано
        ).grid(row=3, column=1, sticky='ew', padx=(10, 0), pady=(10, 2))
        
        ttk.Label(
            broker_settings_frame,
            text="(в разработке)",
            foreground='gray',
            font=('Arial', 8, 'italic')
        ).grid(row=3, column=2, padx=(5, 0), pady=(10, 2))
        
        # Настройка сетки
        basic_frame.columnconfigure(1, weight=1)
        positions_frame.columnconfigure(1, weight=1)
        broker_settings_frame.columnconfigure(1, weight=1)
        
        # Размещение canvas и scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_portfolio_settings(self):
        """
        Создание настроек портфеля
        """
        # Фрейм для настроек портфеля
        portfolio_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(portfolio_frame, text="Портфель")
        
        # Основные настройки
        basic_frame = ttk.LabelFrame(portfolio_frame, text="Основные настройки", padding=10)
        basic_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(basic_frame, text="Начальный капитал (₽):").grid(row=0, column=0, sticky='w', pady=5)
        
        capital_container = ttk.Frame(basic_frame)
        capital_container.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        self.initial_capital_var = tk.IntVar()
        ttk.Spinbox(
            capital_container,
            from_=100000,
            to=100000000,
            textvariable=self.initial_capital_var,
            width=15,
            increment=100000
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            capital_container,
            text="💰 Получить со счета",
            command=self._get_balance_from_account
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(basic_frame, text="Интервал обновления (сек):").grid(row=1, column=0, sticky='w', pady=5)
        self.portfolio_update_interval_var = tk.IntVar()
        ttk.Spinbox(
            basic_frame,
            from_=60,
            to=3600,
            textvariable=self.portfolio_update_interval_var,
            width=15
        ).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Управление рисками
        risk_frame = ttk.LabelFrame(portfolio_frame, text="Управление рисками", padding=10)
        risk_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(risk_frame, text="Макс. риск на сделку (%):").grid(row=0, column=0, sticky='w', pady=5)
        self.max_risk_per_trade_var = tk.DoubleVar()
        ttk.Scale(
            risk_frame,
            from_=0.01,
            to=0.1,
            variable=self.max_risk_per_trade_var,
            orient=tk.HORIZONTAL
        ).grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        ttk.Label(risk_frame, text="Макс. риск портфеля (%):").grid(row=1, column=0, sticky='w', pady=5)
        self.max_portfolio_risk_var = tk.DoubleVar()
        ttk.Scale(
            risk_frame,
            from_=0.05,
            to=0.3,
            variable=self.max_portfolio_risk_var,
            orient=tk.HORIZONTAL
        ).grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        ttk.Label(risk_frame, text="Порог ребалансировки (%):").grid(row=2, column=0, sticky='w', pady=5)
        self.rebalance_threshold_var = tk.DoubleVar()
        ttk.Scale(
            risk_frame,
            from_=0.01,
            to=0.2,
            variable=self.rebalance_threshold_var,
            orient=tk.HORIZONTAL
        ).grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        # Настройка сетки
        basic_frame.columnconfigure(1, weight=1)
        risk_frame.columnconfigure(1, weight=1)
    
    def _create_logging_settings(self):
        """
        Создание настроек логирования
        """
        # Фрейм для настроек логирования
        logging_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(logging_frame, text="Логирование")
        
        # Основные настройки
        basic_frame = ttk.LabelFrame(logging_frame, text="Основные настройки", padding=10)
        basic_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(basic_frame, text="Уровень логирования:").grid(row=0, column=0, sticky='w', pady=5)
        self.log_level_var = tk.StringVar()
        log_level_combo = ttk.Combobox(
            basic_frame,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly"
        )
        log_level_combo.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        ttk.Label(basic_frame, text="Файл логов:").grid(row=1, column=0, sticky='w', pady=5)
        self.log_file_var = tk.StringVar()
        log_file_entry = ttk.Entry(
            basic_frame,
            textvariable=self.log_file_var,
            width=40
        )
        log_file_entry.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        ttk.Label(basic_frame, text="Максимальный размер:").grid(row=2, column=0, sticky='w', pady=5)
        self.log_max_size_var = tk.StringVar()
        ttk.Entry(
            basic_frame,
            textvariable=self.log_max_size_var,
            width=15
        ).grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        
        ttk.Label(basic_frame, text="Период хранения:").grid(row=3, column=0, sticky='w', pady=5)
        self.log_retention_var = tk.StringVar()
        ttk.Entry(
            basic_frame,
            textvariable=self.log_retention_var,
            width=15
        ).grid(row=3, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Настройка сетки
        basic_frame.columnconfigure(1, weight=1)
    
    def _create_notifications_settings(self):
        """
        Создание настроек уведомлений
        """
        # Фрейм для настроек уведомлений
        notifications_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(notifications_frame, text="Уведомления")
        
        # Общие настройки
        general_frame = ttk.LabelFrame(notifications_frame, text="Общие настройки", padding=10)
        general_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.notifications_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(
            general_frame,
            text="Включить уведомления",
            variable=self.notifications_enabled_var
        ).pack(anchor='w', pady=5)
        
        # Email уведомления
        email_frame = ttk.LabelFrame(notifications_frame, text="Email уведомления", padding=10)
        email_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(email_frame, text="SMTP сервер:").grid(row=0, column=0, sticky='w', pady=2)
        self.smtp_server_var = tk.StringVar()
        ttk.Entry(
            email_frame,
            textvariable=self.smtp_server_var,
            width=30
        ).grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ttk.Label(email_frame, text="SMTP порт:").grid(row=1, column=0, sticky='w', pady=2)
        self.smtp_port_var = tk.IntVar()
        ttk.Spinbox(
            email_frame,
            from_=25,
            to=587,
            textvariable=self.smtp_port_var,
            width=10
        ).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        
        ttk.Label(email_frame, text="Email отправителя:").grid(row=2, column=0, sticky='w', pady=2)
        self.email_username_var = tk.StringVar()
        ttk.Entry(
            email_frame,
            textvariable=self.email_username_var,
            width=30
        ).grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ttk.Label(email_frame, text="Пароль:").grid(row=3, column=0, sticky='w', pady=2)
        self.email_password_var = tk.StringVar()
        ttk.Entry(
            email_frame,
            textvariable=self.email_password_var,
            show="*",
            width=30
        ).grid(row=3, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ttk.Label(email_frame, text="Email получателя:").grid(row=4, column=0, sticky='w', pady=2)
        self.email_to_var = tk.StringVar()
        ttk.Entry(
            email_frame,
            textvariable=self.email_to_var,
            width=30
        ).grid(row=4, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Telegram уведомления
        telegram_frame = ttk.LabelFrame(notifications_frame, text="Telegram уведомления", padding=10)
        telegram_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(telegram_frame, text="Bot токен:").grid(row=0, column=0, sticky='w', pady=2)
        self.telegram_bot_token_var = tk.StringVar()
        ttk.Entry(
            telegram_frame,
            textvariable=self.telegram_bot_token_var,
            show="*",
            width=30
        ).grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ttk.Label(telegram_frame, text="Chat ID:").grid(row=1, column=0, sticky='w', pady=2)
        self.telegram_chat_id_var = tk.StringVar()
        ttk.Entry(
            telegram_frame,
            textvariable=self.telegram_chat_id_var,
            width=30
        ).grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Настройка сетки
        email_frame.columnconfigure(1, weight=1)
        telegram_frame.columnconfigure(1, weight=1)
    
    def _create_actions_panel(self, parent):
        """
        Создание панели действий
        
        Args:
            parent: Родительский виджет
        """
        # Рамка действий
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X)
        
        # Кнопки действий
        ttk.Button(
            actions_frame,
            text="✅ Применить",
            command=self._apply_config,
            style='Success.TButton'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            actions_frame,
            text="🔄 Сбросить",
            command=self._reset_config
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            actions_frame,
            text="✔ Проверить",
            command=self._validate_config
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Индикатор изменений
        self.changes_label = ttk.Label(
            actions_frame,
            text="",
            foreground='orange'
        )
        self.changes_label.pack(side=tk.RIGHT)
    
    def _browse_config_file(self):
        """
        Выбор файла конфигурации
        """
        try:
            filename = filedialog.askopenfilename(
                title="Выберите файл конфигурации",
                filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
                initialdir="config"
            )
            
            if filename:
                self.config_file_var.set(filename)
                self.current_config_path = filename
                self._load_config()
                
        except Exception as e:
            logger.error(f"Ошибка выбора файла конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось выбрать файл: {e}")
    
    def _load_template(self, template_name: str):
        """
        Загрузка шаблона конфигурации
        
        Args:
            template_name: Имя шаблона
        """
        try:
            template_path = f"config/{template_name}"
            if os.path.exists(template_path):
                self.current_config_path = template_path
                self.config_file_var.set(template_path)
                self._load_config()
                messagebox.showinfo("Информация", f"Шаблон {template_name} загружен")
            else:
                messagebox.showwarning("Предупреждение", f"Шаблон {template_name} не найден")
                
        except Exception as e:
            logger.error(f"Ошибка загрузки шаблона: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить шаблон: {e}")
    
    def _load_config(self):
        """
        Загрузка конфигурации из файла
        """
        try:
            if not os.path.exists(self.current_config_path):
                logger.warning(f"Файл конфигурации не найден: {self.current_config_path}")
                return
            
            with open(self.current_config_path, 'r', encoding='utf-8') as file:
                self.current_config = yaml.safe_load(file)
            
            # Заполнение полей интерфейса
            self._populate_fields()
            
            self.config_modified = False
            self._update_changes_indicator()
            
            logger.info(f"Конфигурация загружена из {self.current_config_path}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить конфигурацию: {e}")
    
    def _populate_fields(self):
        """
        Заполнение полей интерфейса данными из конфигурации
        """
        try:
            # Данные
            data_config = self.current_config.get('data', {})
            self.data_provider_var.set(data_config.get('provider', 'yfinance'))
            self.update_interval_var.set(data_config.get('update_interval', 300))
            self.history_days_var.set(data_config.get('history_days', 365))
            
            # Символы
            symbols = data_config.get('symbols', [])
            self.symbols_text.delete('1.0', tk.END)
            self.symbols_text.insert('1.0', '\n'.join(symbols))
            
            # Нейросети
            neural_config = self.current_config.get('neural_networks', {})
            self.analysis_interval_var.set(neural_config.get('analysis_interval', 1800))
            self.ensemble_method_var.set(neural_config.get('ensemble_method', 'weighted_average'))
            
            # Модели
            models = neural_config.get('models', [])
            for model in models:
                if model.get('type') == 'lstm':
                    self.lstm_enabled_var.set(model.get('enabled', True))
                    self.lstm_weight_var.set(model.get('weight', 0.3))
                    self.lstm_sequence_var.set(model.get('sequence_length', 60))
                elif model.get('type') == 'xgboost':
                    self.xgb_enabled_var.set(model.get('enabled', True))
                    self.xgb_weight_var.set(model.get('weight', 0.3))
                    self.xgb_estimators_var.set(model.get('n_estimators', 100))
                elif model.get('type') == 'deepseek':
                    self.deepseek_enabled_var.set(model.get('enabled', True))
                    self.deepseek_weight_var.set(model.get('weight', 0.4))
                    self.deepseek_api_key_var.set(model.get('api_key', ''))
            
            # Торговля
            trading_config = self.current_config.get('trading', {})
            self.broker_var.set(trading_config.get('broker', 'paper'))
            self.signal_threshold_var.set(trading_config.get('signal_threshold', 0.6))
            self.signal_check_interval_var.set(trading_config.get('signal_check_interval', 600))
            self.max_positions_var.set(trading_config.get('max_positions', 10))
            self.position_size_var.set(trading_config.get('position_size', 0.1))
            self.min_trade_interval_var.set(trading_config.get('min_trade_interval', 3600))
            
            # Настройки брокера
            broker_settings = trading_config.get('broker_settings', {})
            tinkoff_settings = broker_settings.get('tinkoff', {})
            sber_settings = broker_settings.get('sber', {})
            
            self.tinkoff_token_var.set(tinkoff_settings.get('token', ''))
            self.sber_token_var.set(sber_settings.get('token', ''))
            self.sandbox_mode_var.set(tinkoff_settings.get('sandbox', True))
            
            # Портфель
            portfolio_config = self.current_config.get('portfolio', {})
            self.initial_capital_var.set(portfolio_config.get('initial_capital', 1000000))
            self.portfolio_update_interval_var.set(portfolio_config.get('update_interval', 1800))
            self.max_risk_per_trade_var.set(portfolio_config.get('max_risk_per_trade', 0.02))
            self.max_portfolio_risk_var.set(portfolio_config.get('max_portfolio_risk', 0.1))
            self.rebalance_threshold_var.set(portfolio_config.get('rebalance_threshold', 0.05))
            
            # Логирование
            logging_config = self.current_config.get('logging', {})
            self.log_level_var.set(logging_config.get('level', 'INFO'))
            self.log_file_var.set(logging_config.get('file', 'logs/investment_system.log'))
            self.log_max_size_var.set(logging_config.get('max_size', '10 MB'))
            self.log_retention_var.set(logging_config.get('retention', '30 days'))
            
            # Уведомления
            notifications_config = self.current_config.get('notifications', {})
            self.notifications_enabled_var.set(notifications_config.get('enabled', False))
            
            email_config = notifications_config.get('email', {})
            self.smtp_server_var.set(email_config.get('smtp_server', ''))
            self.smtp_port_var.set(email_config.get('smtp_port', 587))
            self.email_username_var.set(email_config.get('username', ''))
            self.email_password_var.set(email_config.get('password', ''))
            self.email_to_var.set(email_config.get('to_email', ''))
            
            telegram_config = notifications_config.get('telegram', {})
            self.telegram_bot_token_var.set(telegram_config.get('bot_token', ''))
            self.telegram_chat_id_var.set(telegram_config.get('chat_id', ''))
            
        except Exception as e:
            logger.error(f"Ошибка заполнения полей: {e}")
    
    def _collect_config(self) -> Dict[str, Any]:
        """
        Сбор конфигурации из полей интерфейса
        
        Returns:
            Словарь конфигурации
        """
        try:
            config = {}
            
            # Данные
            symbols_text = self.symbols_text.get('1.0', tk.END).strip()
            symbols = [s.strip() for s in symbols_text.split('\n') if s.strip()]
            
            config['data'] = {
                'provider': self.data_provider_var.get(),
                'symbols': symbols,
                'update_interval': self.update_interval_var.get(),
                'history_days': self.history_days_var.get()
            }
            
            # Нейросети
            models = []
            
            if self.lstm_enabled_var.get():
                models.append({
                    'name': 'lstm_predictor',
                    'type': 'lstm',
                    'weight': self.lstm_weight_var.get(),
                    'enabled': True,
                    'sequence_length': self.lstm_sequence_var.get()
                })
            
            if self.xgb_enabled_var.get():
                models.append({
                    'name': 'xgboost_classifier',
                    'type': 'xgboost',
                    'weight': self.xgb_weight_var.get(),
                    'enabled': True,
                    'n_estimators': self.xgb_estimators_var.get()
                })
            
            if self.deepseek_enabled_var.get():
                models.append({
                    'name': 'deepseek_analyzer',
                    'type': 'deepseek',
                    'weight': self.deepseek_weight_var.get(),
                    'enabled': True,
                    'api_key': self.deepseek_api_key_var.get()
                })
            
            config['neural_networks'] = {
                'models': models,
                'analysis_interval': self.analysis_interval_var.get(),
                'ensemble_method': self.ensemble_method_var.get()
            }
            
            # Торговля
            config['trading'] = {
                'broker': self.broker_var.get(),
                'signal_threshold': self.signal_threshold_var.get(),
                'signal_check_interval': self.signal_check_interval_var.get(),
                'max_positions': self.max_positions_var.get(),
                'position_size': self.position_size_var.get(),
                'min_trade_interval': self.min_trade_interval_var.get(),
                'broker_settings': {
                    'tinkoff': {
                        'token': self.tinkoff_token_var.get(),
                        'sandbox': self.sandbox_mode_var.get()
                    },
                    'sber': {
                        'token': self.sber_token_var.get(),
                        'sandbox': self.sandbox_mode_var.get()
                    }
                }
            }
            
            # Портфель
            config['portfolio'] = {
                'initial_capital': self.initial_capital_var.get(),
                'max_risk_per_trade': self.max_risk_per_trade_var.get(),
                'max_portfolio_risk': self.max_portfolio_risk_var.get(),
                'update_interval': self.portfolio_update_interval_var.get(),
                'rebalance_threshold': self.rebalance_threshold_var.get()
            }
            
            # Логирование
            config['logging'] = {
                'level': self.log_level_var.get(),
                'file': self.log_file_var.get(),
                'max_size': self.log_max_size_var.get(),
                'retention': self.log_retention_var.get()
            }
            
            # Уведомления
            config['notifications'] = {
                'enabled': self.notifications_enabled_var.get(),
                'email': {
                    'smtp_server': self.smtp_server_var.get(),
                    'smtp_port': self.smtp_port_var.get(),
                    'username': self.email_username_var.get(),
                    'password': self.email_password_var.get(),
                    'to_email': self.email_to_var.get()
                },
                'telegram': {
                    'bot_token': self.telegram_bot_token_var.get(),
                    'chat_id': self.telegram_chat_id_var.get()
                }
            }
            
            return config
            
        except Exception as e:
            logger.error(f"Ошибка сбора конфигурации: {e}")
            raise
    
    def _apply_config(self):
        """
        Применение конфигурации
        """
        try:
            # Сбор конфигурации
            config = self._collect_config()
            
            # Валидация
            if not self._validate_config_data(config):
                return
            
            # Сохранение
            self.current_config = config
            self.save_config()
            
            # Уведомление об успехе
            messagebox.showinfo("Успех", "Конфигурация применена и сохранена")
            
            self.config_modified = False
            self._update_changes_indicator()
            
        except Exception as e:
            logger.error(f"Ошибка применения конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось применить конфигурацию: {e}")
    
    def _reset_config(self):
        """
        Сброс конфигурации к исходному состоянию
        """
        try:
            result = messagebox.askyesno(
                "Сброс конфигурации",
                "Вы уверены, что хотите сбросить все изменения?"
            )
            
            if result:
                self._load_config()
                messagebox.showinfo("Информация", "Конфигурация сброшена")
                
        except Exception as e:
            logger.error(f"Ошибка сброса конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сбросить конфигурацию: {e}")
    
    def _validate_config(self):
        """
        Валидация конфигурации
        """
        try:
            config = self._collect_config()
            
            if self._validate_config_data(config):
                messagebox.showinfo("Валидация", "Конфигурация корректна")
            
        except Exception as e:
            logger.error(f"Ошибка валидации конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Ошибка валидации: {e}")
    
    def _validate_config_data(self, config: Dict[str, Any]) -> bool:
        """
        Валидация данных конфигурации
        
        Args:
            config: Конфигурация для валидации
            
        Returns:
            True если конфигурация корректна
        """
        try:
            errors = []
            
            # Проверка данных
            data_config = config.get('data', {})
            if not data_config.get('symbols'):
                errors.append("Не указаны торговые символы")
            
            if data_config.get('update_interval', 0) < 60:
                errors.append("Интервал обновления должен быть не менее 60 секунд")
            
            # Проверка нейросетей
            neural_config = config.get('neural_networks', {})
            models = neural_config.get('models', [])
            
            if not models:
                errors.append("Не включена ни одна модель нейросети")
            
            total_weight = sum(model.get('weight', 0) for model in models)
            if abs(total_weight - 1.0) > 0.01:
                errors.append(f"Сумма весов моделей должна быть 1.0 (текущая: {total_weight:.2f})")
            
            # Проверка торговли
            trading_config = config.get('trading', {})
            if trading_config.get('signal_threshold', 0) < 0.1:
                errors.append("Порог сигнала должен быть не менее 0.1")
            
            # Проверка портфеля
            portfolio_config = config.get('portfolio', {})
            if portfolio_config.get('initial_capital', 0) < 100000:
                errors.append("Начальный капитал должен быть не менее 100,000 ₽")
            
            if errors:
                error_message = "Найдены ошибки в конфигурации:\n\n" + "\n".join(f"• {error}" for error in errors)
                messagebox.showerror("Ошибки валидации", error_message)
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка валидации данных конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Ошибка валидации: {e}")
            return False
    
    def _update_changes_indicator(self):
        """
        Обновление индикатора изменений
        """
        if self.config_modified:
            self.changes_label.config(text="● Есть несохраненные изменения", foreground='orange')
        else:
            self.changes_label.config(text="✓ Все изменения сохранены", foreground='green')
    
    def _save_config_as(self):
        """
        Сохранение конфигурации в новый файл
        """
        try:
            filename = filedialog.asksaveasfilename(
                title="Сохранить конфигурацию как",
                filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
                defaultextension=".yaml",
                initialdir="config"
            )
            
            if filename:
                self.current_config_path = filename
                self.config_file_var.set(filename)
                self.save_config()
                
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить конфигурацию: {e}")
    
    def new_config(self):
        """
        Создание новой конфигурации
        """
        try:
            if self.config_modified:
                result = messagebox.askyesnocancel(
                    "Несохраненные изменения",
                    "У вас есть несохраненные изменения. Сохранить их?"
                )
                
                if result is None:  # Cancel
                    return
                elif result:  # Yes
                    self.save_config()
            
            # Создание новой конфигурации
            self.current_config = {}
            self.current_config_path = "config/new_config.yaml"
            self.config_file_var.set(self.current_config_path)
            
            # Заполнение значениями по умолчанию
            self._set_default_values()
            
            self.config_modified = True
            self._update_changes_indicator()
            
            messagebox.showinfo("Информация", "Создана новая конфигурация")
            
        except Exception as e:
            logger.error(f"Ошибка создания новой конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось создать новую конфигурацию: {e}")
    
    def open_config(self):
        """
        Открытие конфигурации
        """
        try:
            if self.config_modified:
                result = messagebox.askyesnocancel(
                    "Несохраненные изменения",
                    "У вас есть несохраненные изменения. Сохранить их?"
                )
                
                if result is None:  # Cancel
                    return
                elif result:  # Yes
                    self.save_config()
            
            filename = filedialog.askopenfilename(
                title="Открыть конфигурацию",
                filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
                initialdir="config"
            )
            
            if filename:
                self.current_config_path = filename
                self.config_file_var.set(filename)
                self._load_config()
                
        except Exception as e:
            logger.error(f"Ошибка открытия конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось открыть конфигурацию: {e}")
    
    def save_config(self):
        """
        Сохранение конфигурации
        """
        try:
            # Сбор текущей конфигурации
            config = self._collect_config()
            
            # Создание директории если не существует
            config_dir = os.path.dirname(self.current_config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # Сохранение в файл
            with open(self.current_config_path, 'w', encoding='utf-8') as file:
                yaml.dump(config, file, default_flow_style=False, allow_unicode=True, indent=2)
            
            self.current_config = config
            self.config_modified = False
            self._update_changes_indicator()
            
            logger.info(f"Конфигурация сохранена в {self.current_config_path}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить конфигурацию: {e}")
    
    def reload_config(self):
        """
        Перезагрузка конфигурации
        """
        try:
            if self.config_modified:
                result = messagebox.askyesno(
                    "Перезагрузка конфигурации",
                    "У вас есть несохраненные изменения. Они будут потеряны. Продолжить?"
                )
                
                if not result:
                    return
            
            self._load_config()
            messagebox.showinfo("Информация", "Конфигурация перезагружена")
            
        except Exception as e:
            logger.error(f"Ошибка перезагрузки конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось перезагрузить конфигурацию: {e}")
    
    def _set_default_values(self):
        """
        Установка значений по умолчанию
        """
        try:
            # Данные
            self.data_provider_var.set("yfinance")
            self.update_interval_var.set(300)
            self.history_days_var.set(365)
            self.symbols_text.delete('1.0', tk.END)
            self.symbols_text.insert('1.0', "SBER\nGAZP\nLKOH")
            
            # Нейросети
            self.analysis_interval_var.set(1800)
            self.ensemble_method_var.set("weighted_average")
            self.lstm_enabled_var.set(True)
            self.lstm_weight_var.set(0.3)
            self.lstm_sequence_var.set(60)
            self.xgb_enabled_var.set(True)
            self.xgb_weight_var.set(0.3)
            self.xgb_estimators_var.set(100)
            self.deepseek_enabled_var.set(True)
            self.deepseek_weight_var.set(0.4)
            
            # Торговля
            self.broker_var.set("paper")
            self.signal_threshold_var.set(0.6)
            self.signal_check_interval_var.set(600)
            self.max_positions_var.set(10)
            self.position_size_var.set(0.1)
            self.min_trade_interval_var.set(3600)
            self.sandbox_mode_var.set(True)
            
            # Портфель
            self.initial_capital_var.set(1000000)
            self.portfolio_update_interval_var.set(1800)
            self.max_risk_per_trade_var.set(0.02)
            self.max_portfolio_risk_var.set(0.1)
            self.rebalance_threshold_var.set(0.05)
            
            # Логирование
            self.log_level_var.set("INFO")
            self.log_file_var.set("logs/investment_system.log")
            self.log_max_size_var.set("10 MB")
            self.log_retention_var.set("30 days")
            
            # Уведомления
            self.notifications_enabled_var.set(False)
            self.smtp_port_var.set(587)
            
        except Exception as e:
            logger.error(f"Ошибка установки значений по умолчанию: {e}")
    
    def get_current_config_path(self) -> str:
        """
        Получение пути к текущей конфигурации
        
        Returns:
            Путь к файлу конфигурации
        """
        return self.current_config_path
    
    def _get_balance_from_account(self):
        """
        Получение баланса со счета T-Bank
        """
        try:
            import asyncio
            import os
            from ..trading.tbank_broker import TBankBroker
            
            # Проверка наличия токена
            token = self.tinkoff_token_var.get()
            if not token:
                token = os.getenv('TINKOFF_TOKEN')
            
            if not token:
                messagebox.showwarning(
                    "Предупреждение",
                    "Не указан токен T-Bank.\n\n"
                    "Укажите токен в настройках брокера или в переменной окружения TINKOFF_TOKEN."
                )
                return
            
            # Получение настроек sandbox
            sandbox = self.sandbox_mode_var.get()
            
            # Показ индикатора загрузки
            loading_dialog = tk.Toplevel(self.parent)
            loading_dialog.title("Получение баланса")
            loading_dialog.geometry("300x100")
            loading_dialog.transient(self.parent)
            loading_dialog.grab_set()
            
            ttk.Label(
                loading_dialog,
                text="Подключение к T-Bank API...",
                font=('Arial', 10)
            ).pack(pady=20)
            
            progress = ttk.Progressbar(
                loading_dialog,
                mode='indeterminate'
            )
            progress.pack(fill=tk.X, padx=20)
            progress.start()
            
            # Функция для получения баланса в отдельном потоке
            def get_balance():
                try:
                    async def fetch_balance():
                        broker = TBankBroker(
                            token=token,
                            sandbox=sandbox
                        )
                        await broker.initialize()
                        balance = await broker.get_total_balance_rub()
                        return balance
                    
                    # Создание нового event loop для потока
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    balance = loop.run_until_complete(fetch_balance())
                    loop.close()
                    
                    # Обновление значения в главном потоке
                    self.parent.after(0, lambda: self._update_balance_value(balance, loading_dialog))
                    
                except Exception as e:
                    logger.error(f"Ошибка получения баланса: {e}")
                    self.parent.after(0, lambda: self._show_balance_error(str(e), loading_dialog))
            
            # Запуск в отдельном потоке
            import threading
            balance_thread = threading.Thread(target=get_balance, daemon=True)
            balance_thread.start()
            
        except Exception as e:
            logger.error(f"Ошибка инициализации получения баланса: {e}")
            messagebox.showerror("Ошибка", f"Не удалось получить баланс:\n{e}")
    
    def _update_balance_value(self, balance: float, dialog):
        """
        Обновление значения баланса
        
        Args:
            balance: Полученный баланс
            dialog: Диалоговое окно загрузки
        """
        try:
            dialog.destroy()
            
            if balance > 0:
                self.initial_capital_var.set(int(balance))
                self.config_modified = True
                self._update_changes_indicator()
                
                messagebox.showinfo(
                    "Баланс получен",
                    f"Баланс счета: {balance:,.2f} ₽\n\n"
                    f"Начальный капитал обновлен.\n"
                    f"Не забудьте сохранить конфигурацию."
                )
            else:
                messagebox.showwarning(
                    "Баланс нулевой",
                    "На счете нет доступных средств.\n\n"
                    "Для sandbox счетов используйте пополнение через API."
                )
                
        except Exception as e:
            logger.error(f"Ошибка обновления значения баланса: {e}")
    
    def _show_balance_error(self, error_msg: str, dialog):
        """
        Отображение ошибки получения баланса
        
        Args:
            error_msg: Сообщение об ошибке
            dialog: Диалоговое окно загрузки
        """
        try:
            dialog.destroy()
            messagebox.showerror(
                "Ошибка получения баланса",
                f"Не удалось получить баланс со счета:\n\n{error_msg}\n\n"
                f"Проверьте:\n"
                f"• Правильность токена\n"
                f"• Наличие интернет-соединения\n"
                f"• Настройки sandbox/production"
            )
        except Exception as e:
            logger.error(f"Ошибка отображения ошибки баланса: {e}")
    
    def _show_token_help(self):
        """
        Показ справки о получении токена T-Bank
        """
        help_text = """
Как получить токен T-Bank Invest API:

1. Откройте браузер и перейдите по ссылке:
   https://www.tbank.ru/invest/settings/api/

2. Войдите в свой аккаунт T-Bank Инвестиции

3. Перейдите в раздел "Настройки" → "API"

4. Нажмите кнопку "Выпустить токен"

5. Выберите тип токена:
   • Для торговли: "Полный доступ"
   • Для тестирования: "Только для чтения"

6. Скопируйте токен (показывается ОДИН раз!)

⚠️ Важно:
• Храните токен в безопасности
• Не передавайте токен третьим лицам
• Для тестирования используйте режим "Песочница"

📚 Документация:
docs/tbank/getting-started.md
        """
        messagebox.showinfo("Получение токена T-Bank", help_text)
    
    def _check_tbank_connection(self):
        """
        Проверка подключения к T-Bank API
        """
        try:
            import asyncio
            import os
            from ..trading.tbank_broker import TBankBroker
            
            # Проверка наличия токена
            token = self.tinkoff_token_var.get()
            if not token:
                token = os.getenv('TINKOFF_TOKEN')
            
            if not token:
                messagebox.showwarning(
                    "Предупреждение",
                    "Не указан токен T-Bank.\n\n"
                    "Укажите токен в настройках или в переменной окружения TINKOFF_TOKEN."
                )
                return
            
            # Получение настроек sandbox
            sandbox = self.sandbox_mode_var.get()
            
            # Показ индикатора загрузки
            loading_dialog = tk.Toplevel(self.parent)
            loading_dialog.title("Проверка подключения")
            loading_dialog.geometry("350x120")
            loading_dialog.transient(self.parent)
            loading_dialog.grab_set()
            
            ttk.Label(
                loading_dialog,
                text="Подключение к T-Bank API...",
                font=('Arial', 10)
            ).pack(pady=20)
            
            progress = ttk.Progressbar(
                loading_dialog,
                mode='indeterminate'
            )
            progress.pack(fill=tk.X, padx=20)
            progress.start()
            
            # Функция для проверки подключения в отдельном потоке
            def check_connection():
                try:
                    async def test_connection():
                        broker = TBankBroker(
                            token=token,
                            sandbox=sandbox
                        )
                        await broker.initialize()
                        
                        # Получение информации о счете
                        balance = await broker.get_total_balance_rub()
                        status = broker.get_status()
                        
                        return {
                            'success': True,
                            'balance': balance,
                            'account_id': status.get('account_id'),
                            'mode': status.get('mode'),
                            'instruments': status.get('instruments_loaded', 0)
                        }
                    
                    # Создание нового event loop для потока
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(test_connection())
                    loop.close()
                    
                    # Обновление результата в главном потоке
                    self.parent.after(0, lambda: self._show_connection_result(result, loading_dialog))
                    
                except Exception as e:
                    logger.error(f"Ошибка проверки подключения: {e}")
                    self.parent.after(0, lambda: self._show_connection_error(str(e), loading_dialog))
            
            # Запуск в отдельном потоке
            import threading
            check_thread = threading.Thread(target=check_connection, daemon=True)
            check_thread.start()
            
        except Exception as e:
            logger.error(f"Ошибка инициализации проверки подключения: {e}")
            messagebox.showerror("Ошибка", f"Не удалось проверить подключение:\n{e}")
    
    def _show_connection_result(self, result: dict, dialog):
        """
        Отображение результата проверки подключения
        
        Args:
            result: Результат проверки
            dialog: Диалоговое окно загрузки
        """
        try:
            dialog.destroy()
            
            if result.get('success'):
                mode_text = "Песочница (Sandbox)" if result.get('mode') == 'sandbox' else "Боевой режим (Production)"
                
                info_text = (
                    f"✅ Подключение успешно!\n\n"
                    f"Режим: {mode_text}\n"
                    f"Account ID: {result.get('account_id', 'N/A')}\n"
                    f"Баланс: {result.get('balance', 0):,.2f} ₽\n"
                    f"Доступно инструментов: {result.get('instruments', 0)}\n\n"
                    f"Вы можете использовать систему для торговли."
                )
                
                messagebox.showinfo("Подключение к T-Bank", info_text)
            else:
                messagebox.showerror("Ошибка подключения", "Не удалось подключиться к T-Bank API")
                
        except Exception as e:
            logger.error(f"Ошибка отображения результата подключения: {e}")
    
    def _show_connection_error(self, error_msg: str, dialog):
        """
        Отображение ошибки подключения
        
        Args:
            error_msg: Сообщение об ошибке
            dialog: Диалоговое окно загрузки
        """
        try:
            dialog.destroy()
            messagebox.showerror(
                "Ошибка подключения",
                f"Не удалось подключиться к T-Bank API:\n\n{error_msg}\n\n"
                f"Проверьте:\n"
                f"• Правильность токена\n"
                f"• Наличие интернет-соединения\n"
                f"• Настройки sandbox/production\n"
                f"• Установлена ли библиотека tinkoff-investments"
            )
        except Exception as e:
            logger.error(f"Ошибка отображения ошибки подключения: {e}")
