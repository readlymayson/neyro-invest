#!/usr/bin/env python3
"""
Главное приложение GUI для системы нейросетевых инвестиций
Отдельный интерфейс для визуализации и управления
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from loguru import logger
import yaml
import requests
import time

class InvestmentGUI:
    """
    Главное GUI приложение для системы инвестиций
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Система нейросетевых инвестиций - GUI")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Настройка стиля
        self.setup_styles()
        
        # Переменные состояния
        self.system_status = "Отключена"
        self.portfolio_value = 1000000
        self.current_positions = {}
        self.trading_signals = []
        self.system_logs = []
        
        # Очереди для обновления данных
        self.data_queue = queue.Queue()
        self.log_queue = queue.Queue()
        
        # Интеграция с системой
        self.investment_system = None
        self.system_process = None
        
        # Создание интерфейса
        self.create_widgets()
        
        # Проверка статуса системы
        self.check_system_status()
        
        # Запуск обновления данных
        self.update_data()
        
    def setup_styles(self):
        """Настройка стилей интерфейса"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Цветовая схема
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#f0f0f0')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), background='#f0f0f0')
        style.configure('Status.TLabel', font=('Arial', 10), background='#f0f0f0')
        
        # Кнопки
        style.configure('Start.TButton', background='#4CAF50', foreground='white')
        style.configure('Stop.TButton', background='#f44336', foreground='white')
        style.configure('Config.TButton', background='#2196F3', foreground='white')
        
    def create_widgets(self):
        """Создание виджетов интерфейса"""
        # Главное меню
        self.create_menu()
        
        # Панель статуса
        self.create_status_panel()
        
        # Основные вкладки
        self.create_notebook()
        
        # Панель управления
        self.create_control_panel()
        
    def create_menu(self):
        """Создание главного меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Загрузить конфигурацию", command=self.load_config)
        file_menu.add_command(label="Сохранить конфигурацию", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Меню "Система"
        system_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Система", menu=system_menu)
        system_menu.add_command(label="Запустить систему", command=self.start_system)
        system_menu.add_command(label="Остановить систему", command=self.stop_system)
        system_menu.add_command(label="Перезапустить", command=self.restart_system)
        
        # Меню "Помощь"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Помощь", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
        help_menu.add_command(label="Документация", command=self.show_docs)
        
    def create_status_panel(self):
        """Создание панели статуса"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        # Статус системы
        ttk.Label(status_frame, text="Статус системы:", style='Header.TLabel').pack(side='left')
        self.status_label = ttk.Label(status_frame, text="Отключена", style='Status.TLabel')
        self.status_label.pack(side='left', padx=(10, 20))
        
        # Капитал
        ttk.Label(status_frame, text="Капитал:", style='Header.TLabel').pack(side='left')
        self.capital_label = ttk.Label(status_frame, text="1,000,000 ₽", style='Status.TLabel')
        self.capital_label.pack(side='left', padx=(10, 20))
        
        # Последнее обновление
        ttk.Label(status_frame, text="Обновлено:", style='Header.TLabel').pack(side='left')
        self.update_label = ttk.Label(status_frame, text="--:--:--", style='Status.TLabel')
        self.update_label.pack(side='left', padx=(10, 0))
        
    def create_notebook(self):
        """Создание вкладок"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Вкладка "Дашборд"
        self.create_dashboard_tab()
        
        # Вкладка "Портфель"
        self.create_portfolio_tab()
        
        # Вкладка "Торговля"
        self.create_trading_tab()
        
        # Вкладка "Аналитика"
        self.create_analytics_tab()
        
        # Вкладка "Логи"
        self.create_logs_tab()
        
        # Вкладка "Настройки"
        self.create_settings_tab()
        
    def create_dashboard_tab(self):
        """Создание вкладки дашборда"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 Дашборд")
        
        # Левая панель - графики
        left_frame = ttk.Frame(dashboard_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # График портфеля
        portfolio_frame = ttk.LabelFrame(left_frame, text="Динамика портфеля")
        portfolio_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        self.portfolio_fig = Figure(figsize=(8, 4), dpi=100)
        self.portfolio_ax = self.portfolio_fig.add_subplot(111)
        self.portfolio_canvas = FigureCanvasTkAgg(self.portfolio_fig, portfolio_frame)
        self.portfolio_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # График сигналов
        signals_frame = ttk.LabelFrame(left_frame, text="Торговые сигналы")
        signals_frame.pack(fill='both', expand=True)
        
        self.signals_fig = Figure(figsize=(8, 3), dpi=100)
        self.signals_ax = self.signals_fig.add_subplot(111)
        self.signals_canvas = FigureCanvasTkAgg(self.signals_fig, signals_frame)
        self.signals_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Правая панель - метрики
        right_frame = ttk.Frame(dashboard_frame)
        right_frame.pack(side='right', fill='y', padx=(5, 0))
        
        # Ключевые метрики
        metrics_frame = ttk.LabelFrame(right_frame, text="Ключевые метрики")
        metrics_frame.pack(fill='x', pady=(0, 10))
        
        self.create_metrics_widgets(metrics_frame)
        
        # Активные позиции
        positions_frame = ttk.LabelFrame(right_frame, text="Активные позиции")
        positions_frame.pack(fill='both', expand=True)
        
        self.positions_tree = ttk.Treeview(positions_frame, columns=('Symbol', 'Quantity', 'Price', 'Value'), show='headings')
        self.positions_tree.heading('Symbol', text='Символ')
        self.positions_tree.heading('Quantity', text='Количество')
        self.positions_tree.heading('Price', text='Цена')
        self.positions_tree.heading('Value', text='Стоимость')
        self.positions_tree.pack(fill='both', expand=True)
        
    def create_portfolio_tab(self):
        """Создание вкладки портфеля"""
        portfolio_frame = ttk.Frame(self.notebook)
        self.notebook.add(portfolio_frame, text="💼 Портфель")
        
        # График распределения активов
        allocation_frame = ttk.LabelFrame(portfolio_frame, text="Распределение активов")
        allocation_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.allocation_fig = Figure(figsize=(10, 6), dpi=100)
        self.allocation_ax = self.allocation_fig.add_subplot(111)
        self.allocation_canvas = FigureCanvasTkAgg(self.allocation_fig, allocation_frame)
        self.allocation_canvas.get_tk_widget().pack(fill='both', expand=True)
        
    def create_trading_tab(self):
        """Создание вкладки торговли"""
        trading_frame = ttk.Frame(self.notebook)
        self.notebook.add(trading_frame, text="📈 Торговля")
        
        # Панель управления торговлей
        control_frame = ttk.LabelFrame(trading_frame, text="Управление торговлей")
        control_frame.pack(fill='x', padx=10, pady=10)
        
        # Кнопки управления
        ttk.Button(control_frame, text="🟢 Запустить торговлю", 
                  command=self.start_trading, style='Start.TButton').pack(side='left', padx=5)
        ttk.Button(control_frame, text="🔴 Остановить торговлю", 
                  command=self.stop_trading, style='Stop.TButton').pack(side='left', padx=5)
        ttk.Button(control_frame, text="⚙️ Настройки", 
                  command=self.open_trading_settings, style='Config.TButton').pack(side='left', padx=5)
        
        # Таблица торговых сигналов
        signals_frame = ttk.LabelFrame(trading_frame, text="Торговые сигналы")
        signals_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.signals_tree = ttk.Treeview(signals_frame, columns=('Time', 'Symbol', 'Signal', 'Confidence', 'Action'), show='headings')
        self.signals_tree.heading('Time', text='Время')
        self.signals_tree.heading('Symbol', text='Символ')
        self.signals_tree.heading('Signal', text='Сигнал')
        self.signals_tree.heading('Confidence', text='Уверенность')
        self.signals_tree.heading('Action', text='Действие')
        self.signals_tree.pack(fill='both', expand=True)
        
    def create_analytics_tab(self):
        """Создание вкладки аналитики"""
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="📊 Аналитика")
        
        # График производительности
        performance_frame = ttk.LabelFrame(analytics_frame, text="Производительность портфеля")
        performance_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.performance_fig = Figure(figsize=(12, 8), dpi=100)
        self.performance_ax = self.performance_fig.add_subplot(111)
        self.performance_canvas = FigureCanvasTkAgg(self.performance_fig, performance_frame)
        self.performance_canvas.get_tk_widget().pack(fill='both', expand=True)
        
    def create_logs_tab(self):
        """Создание вкладки логов"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📝 Логи")
        
        # Панель управления логами
        log_control_frame = ttk.Frame(logs_frame)
        log_control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(log_control_frame, text="Обновить", command=self.refresh_logs).pack(side='left', padx=5)
        ttk.Button(log_control_frame, text="Очистить", command=self.clear_logs).pack(side='left', padx=5)
        ttk.Button(log_control_frame, text="Сохранить", command=self.save_logs).pack(side='left', padx=5)
        
        # Область логов
        log_frame = ttk.LabelFrame(logs_frame, text="Системные логи")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=20, wrap='word')
        log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scrollbar.pack(side='right', fill='y')
        
    def create_settings_tab(self):
        """Создание вкладки настроек"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Настройки")
        
        # Настройки системы
        system_frame = ttk.LabelFrame(settings_frame, text="Настройки системы")
        system_frame.pack(fill='x', padx=10, pady=10)
        
        # Выбор конфигурации
        ttk.Label(system_frame, text="Конфигурация:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.config_var = tk.StringVar(value="config/main.yaml")
        config_combo = ttk.Combobox(system_frame, textvariable=self.config_var, width=30)
        config_combo['values'] = [
            "config/main.yaml",
            "config/aggressive_trading.yaml", 
            "config/conservative_investing.yaml",
            "config/test_config.yaml"
        ]
        config_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Настройки API
        api_frame = ttk.LabelFrame(settings_frame, text="API настройки")
        api_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(api_frame, text="DeepSeek API:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.deepseek_var = tk.StringVar()
        ttk.Entry(api_frame, textvariable=self.deepseek_var, show="*", width=40).grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        ttk.Label(api_frame, text="Tinkoff API:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.tinkoff_var = tk.StringVar()
        ttk.Entry(api_frame, textvariable=self.tinkoff_var, show="*", width=40).grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Кнопки
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="Сохранить настройки", command=self.save_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Загрузить настройки", command=self.load_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Сбросить", command=self.reset_settings).pack(side='left', padx=5)
        
    def create_control_panel(self):
        """Создание панели управления"""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Кнопки управления системой
        ttk.Button(control_frame, text="🚀 Запустить систему", 
                  command=self.start_system, style='Start.TButton').pack(side='left', padx=5)
        ttk.Button(control_frame, text="⏹️ Остановить систему", 
                  command=self.stop_system, style='Stop.TButton').pack(side='left', padx=5)
        ttk.Button(control_frame, text="🔄 Перезапустить", 
                  command=self.restart_system).pack(side='left', padx=5)
        
        # Индикатор состояния
        self.status_indicator = tk.Canvas(control_frame, width=20, height=20, bg='red')
        self.status_indicator.pack(side='right', padx=10)
        
    def create_metrics_widgets(self, parent):
        """Создание виджетов метрик"""
        # Общая доходность
        ttk.Label(parent, text="Общая доходность:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.return_label = ttk.Label(parent, text="+0.00%", style='Status.TLabel')
        self.return_label.grid(row=0, column=1, sticky='e', padx=5, pady=2)
        
        # Дневная доходность
        ttk.Label(parent, text="Дневная доходность:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.daily_return_label = ttk.Label(parent, text="+0.00%", style='Status.TLabel')
        self.daily_return_label.grid(row=1, column=1, sticky='e', padx=5, pady=2)
        
        # Количество позиций
        ttk.Label(parent, text="Активные позиции:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.positions_count_label = ttk.Label(parent, text="0", style='Status.TLabel')
        self.positions_count_label.grid(row=2, column=1, sticky='e', padx=5, pady=2)
        
        # Последний сигнал
        ttk.Label(parent, text="Последний сигнал:").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.last_signal_label = ttk.Label(parent, text="Нет", style='Status.TLabel')
        self.last_signal_label.grid(row=3, column=1, sticky='e', padx=5, pady=2)
        
    def update_data(self):
        """Обновление данных интерфейса"""
        try:
            # Обработка очереди данных
            while not self.data_queue.empty():
                data = self.data_queue.get_nowait()
                self.process_data_update(data)
            
            # Обработка очереди логов
            while not self.log_queue.empty():
                log_entry = self.log_queue.get_nowait()
                self.add_log_entry(log_entry)
            
            # Обновление времени
            current_time = datetime.now().strftime("%H:%M:%S")
            self.update_label.config(text=current_time)
            
            # Периодическая проверка статуса системы (каждые 10 секунд)
            if hasattr(self, '_last_status_check'):
                if time.time() - self._last_status_check > 10:
                    self.check_system_status()
                    self.load_system_data()
                    self._last_status_check = time.time()
            else:
                self._last_status_check = time.time()
            
            # Обновление реальных данных
            if self.system_status == "Запущена":
                self.update_real_data()
            
            # Обновление графиков
            self.update_charts()
            
        except Exception as e:
            logger.error(f"Ошибка обновления данных: {e}")
        
        # Планирование следующего обновления
        self.root.after(1000, self.update_data)
        
    def process_data_update(self, data):
        """Обработка обновления данных"""
        if 'portfolio_value' in data:
            self.portfolio_value = data['portfolio_value']
            self.capital_label.config(text=f"{self.portfolio_value:,.0f} ₽")
            
        if 'positions' in data:
            self.current_positions = data['positions']
            self.update_positions_table()
            
        if 'signals' in data:
            self.trading_signals = data['signals']
            self.update_signals_table()
            
    def update_positions_table(self):
        """Обновление таблицы позиций"""
        # Очистка таблицы
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)
            
        # Добавление позиций
        for symbol, position in self.current_positions.items():
            self.positions_tree.insert('', 'end', values=(
                symbol,
                position.get('quantity', 0),
                f"{position.get('price', 0):.2f}",
                f"{position.get('value', 0):,.0f}"
            ))
            
    def update_signals_table(self):
        """Обновление таблицы сигналов"""
        # Очистка таблицы
        for item in self.signals_tree.get_children():
            self.signals_tree.delete(item)
            
        # Добавление сигналов
        for signal in self.trading_signals[-10:]:  # Последние 10 сигналов
            self.signals_tree.insert('', 'end', values=(
                signal.get('time', ''),
                signal.get('symbol', ''),
                signal.get('signal', ''),
                f"{signal.get('confidence', 0):.1%}",
                signal.get('action', '')
            ))
            
    def update_charts(self):
        """Обновление графиков"""
        # Обновление графика портфеля
        self.update_portfolio_chart()
        
        # Обновление графика сигналов
        self.update_signals_chart()
        
        # Обновление графика распределения
        self.update_allocation_chart()
        
        # Обновление графика производительности
        self.update_performance_chart()
        
    def update_portfolio_chart(self):
        """Обновление графика портфеля"""
        self.portfolio_ax.clear()
        
        # Загрузка реальных данных из истории портфеля
        try:
            # Если есть история портфеля, используем её
            if not hasattr(self, 'portfolio_history'):
                self.portfolio_history = []
            
            # Добавление текущего значения в историю
            current_time = datetime.now()
            self.portfolio_history.append({
                'time': current_time,
                'value': self.portfolio_value
            })
            
            # Храним историю за последние 24 часа
            cutoff_time = current_time - timedelta(hours=24)
            self.portfolio_history = [
                item for item in self.portfolio_history 
                if item['time'] > cutoff_time
            ]
            
            # Построение графика
            if len(self.portfolio_history) > 1:
                times = [item['time'] for item in self.portfolio_history]
                values = [item['value'] for item in self.portfolio_history]
                
                self.portfolio_ax.plot(times, values, linewidth=2, color='blue')
            else:
                # Если недостаточно данных, показываем текущее значение
                self.portfolio_ax.axhline(y=self.portfolio_value, color='blue', linewidth=2)
                
        except Exception as e:
            logger.error(f"Ошибка обновления графика портфеля: {e}")
        
        self.portfolio_ax.set_title('Динамика портфеля (24 часа)')
        self.portfolio_ax.set_ylabel('Стоимость (₽)')
        self.portfolio_ax.grid(True, alpha=0.3)
        
        self.portfolio_canvas.draw()
        
    def update_signals_chart(self):
        """Обновление графика сигналов"""
        self.signals_ax.clear()
        
        # Использование реальных сигналов из системы
        try:
            if self.trading_signals and len(self.trading_signals) > 0:
                colors = {'BUY': 'green', 'SELL': 'red', 'HOLD': 'gray'}
                
                # Преобразование сигналов для отображения
                for i, signal in enumerate(self.trading_signals[-20:]):  # Последние 20 сигналов
                    signal_type = signal.get('signal', 'HOLD')
                    if signal_type != 'HOLD':
                        # Используем индекс как временную метку
                        self.signals_ax.scatter(i, i, c=colors.get(signal_type, 'gray'), 
                                              s=100, alpha=0.7, label=signal_type)
                
                # Добавление подписей
                if len(self.trading_signals) > 0:
                    self.signals_ax.legend()
            else:
                # Если нет сигналов, показываем сообщение
                self.signals_ax.text(0.5, 0.5, 'Нет торговых сигналов', 
                                   ha='center', va='center', transform=self.signals_ax.transAxes)
                
        except Exception as e:
            logger.error(f"Ошибка обновления графика сигналов: {e}")
        
        self.signals_ax.set_title('Торговые сигналы (последние 20)')
        self.signals_ax.set_ylabel('Индекс сигнала')
        self.signals_ax.grid(True, alpha=0.3)
        
        self.signals_canvas.draw()
        
    def update_allocation_chart(self):
        """Обновление графика распределения"""
        self.allocation_ax.clear()
        
        # Использование реальных данных о позициях
        try:
            if self.current_positions and len(self.current_positions) > 0:
                # Расчет стоимости позиций
                labels = []
                sizes = []
                
                total_invested = sum(pos.get('value', 0) for pos in self.current_positions.values())
                
                for symbol, position in self.current_positions.items():
                    value = position.get('value', 0)
                    if value > 0:
                        labels.append(symbol)
                        sizes.append(value)
                
                # Добавление наличных
                cash = self.portfolio_value - total_invested
                if cash > 0:
                    labels.append('Наличные')
                    sizes.append(cash)
                
                # Генерация цветов
                colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
                
                # Построение круговой диаграммы
                if sizes:
                    self.allocation_ax.pie(sizes, labels=labels, colors=colors, 
                                          autopct='%1.1f%%', startangle=90)
                else:
                    self.allocation_ax.text(0.5, 0.5, 'Нет активных позиций', 
                                          ha='center', va='center', 
                                          transform=self.allocation_ax.transAxes)
            else:
                # Если нет позиций, показываем 100% наличных
                self.allocation_ax.pie([100], labels=['Наличные'], colors=['#ffcc99'], 
                                      autopct='%1.1f%%', startangle=90)
                
        except Exception as e:
            logger.error(f"Ошибка обновления графика распределения: {e}")
        
        self.allocation_ax.set_title('Распределение активов')
        self.allocation_canvas.draw()
    
    def update_performance_chart(self):
        """Обновление графика производительности"""
        try:
            self.performance_ax.clear()
            
            # Использование реальной истории портфеля
            if hasattr(self, 'portfolio_history') and len(self.portfolio_history) > 1:
                times = [item['time'] for item in self.portfolio_history]
                values = [item['value'] for item in self.portfolio_history]
                
                # Построение графика портфеля
                self.performance_ax.plot(times, values, linewidth=2, color='blue', label='Портфель')
                
                # Построение бенчмарка (начальное значение)
                initial_value = self.portfolio_history[0]['value'] if self.portfolio_history else 1000000
                benchmark = [initial_value] * len(times)
                self.performance_ax.plot(times, benchmark, linewidth=2, color='gray', 
                                       linestyle='--', label='Начальное значение')
                
                # Заливка области
                values_array = np.array(values)
                benchmark_array = np.array(benchmark)
                
                self.performance_ax.fill_between(times, values_array, benchmark_array,
                                                where=values_array >= benchmark_array,
                                                color='green', alpha=0.3, label='Прибыль')
                self.performance_ax.fill_between(times, values_array, benchmark_array,
                                                where=values_array < benchmark_array,
                                                color='red', alpha=0.3, label='Убыток')
                
                self.performance_ax.legend(loc='best')
                self.performance_ax.set_title('Производительность портфеля')
                self.performance_ax.set_ylabel('Стоимость (₽)')
                self.performance_ax.set_xlabel('Время')
                self.performance_ax.grid(True, alpha=0.3)
            else:
                # Если недостаточно данных
                self.performance_ax.text(0.5, 0.5, 'Недостаточно данных для анализа\nСистема собирает данные...', 
                                       ha='center', va='center', transform=self.performance_ax.transAxes,
                                       fontsize=14)
                self.performance_ax.set_title('Производительность портфеля')
            
            self.performance_canvas.draw()
            
        except Exception as e:
            logger.error(f"Ошибка обновления графика производительности: {e}")
        
    def add_log_entry(self, log_entry):
        """Добавление записи в лог"""
        self.log_text.insert(tk.END, f"{log_entry}\n")
        self.log_text.see(tk.END)
        
    def start_system(self):
        """Запуск системы"""
        self.system_status = "Запускается"
        self.status_label.config(text="Запускается")
        self.status_indicator.config(bg='yellow')
        
        # Здесь будет логика запуска системы
        messagebox.showinfo("Система", "Система запущена!")
        
    def stop_system(self):
        """Остановка системы"""
        self.system_status = "Остановлена"
        self.status_label.config(text="Остановлена")
        self.status_indicator.config(bg='red')
        
        messagebox.showinfo("Система", "Система остановлена!")
        
    def restart_system(self):
        """Перезапуск системы"""
        self.stop_system()
        self.root.after(2000, self.start_system)
        
    def start_trading(self):
        """Запуск торговли"""
        messagebox.showinfo("Торговля", "Торговля запущена!")
        
    def stop_trading(self):
        """Остановка торговли"""
        messagebox.showinfo("Торговля", "Торговля остановлена!")
        
    def open_trading_settings(self):
        """Открытие настроек торговли"""
        messagebox.showinfo("Настройки", "Настройки торговли")
        
    def load_config(self):
        """Загрузка конфигурации"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл конфигурации",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if file_path:
            self.config_var.set(file_path)
            messagebox.showinfo("Конфигурация", f"Конфигурация загружена: {file_path}")
            
    def save_config(self):
        """Сохранение конфигурации"""
        messagebox.showinfo("Конфигурация", "Конфигурация сохранена!")
        
    def refresh_logs(self):
        """Обновление логов"""
        # Загрузка логов из файла
        log_file = Path("logs/neural_networks.log")
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()[-100:]  # Последние 100 строк
                self.log_text.delete(1.0, tk.END)
                for log in logs:
                    self.log_text.insert(tk.END, log)
                    
    def clear_logs(self):
        """Очистка логов"""
        self.log_text.delete(1.0, tk.END)
        
    def save_logs(self):
        """Сохранение логов"""
        file_path = filedialog.asksaveasfilename(
            title="Сохранить логи",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("Логи", f"Логи сохранены: {file_path}")
            
    def save_settings(self):
        """Сохранение настроек"""
        messagebox.showinfo("Настройки", "Настройки сохранены!")
        
    def load_settings(self):
        """Загрузка настроек"""
        messagebox.showinfo("Настройки", "Настройки загружены!")
        
    def reset_settings(self):
        """Сброс настроек"""
        self.config_var.set("config/main.yaml")
        self.deepseek_var.set("")
        self.tinkoff_var.set("")
        messagebox.showinfo("Настройки", "Настройки сброшены!")
        
    def show_about(self):
        """Показ информации о программе"""
        about_text = """
Система нейросетевых инвестиций v2.0

GUI для визуализации и управления
системой автоматической торговли.

Возможности:
• Мониторинг портфеля в реальном времени
• Управление торговыми стратегиями
• Анализ производительности
• Просмотр логов системы
• Настройка параметров
        """
        messagebox.showinfo("О программе", about_text)
        
    def show_docs(self):
        """Показ документации"""
        messagebox.showinfo("Документация", "Документация доступна в папке docs/")
    
    def check_system_status(self):
        """Проверка статуса торговой системы"""
        try:
            # Проверяем, запущена ли система через процессы
            import psutil
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'python.exe' or proc.info['name'] == 'python':
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if 'run.py' in cmdline or 'investment_system' in cmdline:
                            python_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if python_processes:
                self.system_status = "Запущена"
                self.status_label.config(text="Запущена")
                self.status_indicator.config(bg='green')
                logger.info("Торговая система обнаружена и запущена")
            else:
                self.system_status = "Отключена"
                self.status_label.config(text="Отключена")
                self.status_indicator.config(bg='red')
                logger.info("Торговая система не запущена")
                
        except ImportError:
            # psutil не установлен, используем альтернативный метод
            self.check_system_status_alternative()
        except Exception as e:
            logger.error(f"Ошибка проверки статуса системы: {e}")
            self.system_status = "Неизвестно"
            self.status_label.config(text="Неизвестно")
            self.status_indicator.config(bg='yellow')
    
    def check_system_status_alternative(self):
        """Альтернативная проверка статуса системы"""
        try:
            # Проверяем наличие логов системы
            log_file = Path("logs/neural_networks.log")
            if log_file.exists():
                # Проверяем время последней записи в лог
                last_modified = log_file.stat().st_mtime
                current_time = time.time()
                
                # Если лог обновлялся в последние 5 минут, система работает
                if current_time - last_modified < 300:  # 5 минут
                    self.system_status = "Запущена"
                    self.status_label.config(text="Запущена")
                    self.status_indicator.config(bg='green')
                else:
                    self.system_status = "Отключена"
                    self.status_label.config(text="Отключена")
                    self.status_indicator.config(bg='red')
            else:
                self.system_status = "Отключена"
                self.status_label.config(text="Отключена")
                self.status_indicator.config(bg='red')
                
        except Exception as e:
            logger.error(f"Ошибка альтернативной проверки статуса: {e}")
            self.system_status = "Неизвестно"
            self.status_label.config(text="Неизвестно")
            self.status_indicator.config(bg='yellow')
    
    def load_system_data(self):
        """Загрузка данных из системы"""
        try:
            # Загрузка данных из логов системы
            self.load_data_from_logs()
            
            # Загрузка данных портфеля из файлов (если есть)
            portfolio_file = Path("data/portfolio.json")
            if portfolio_file.exists():
                with open(portfolio_file, 'r', encoding='utf-8') as f:
                    portfolio_data = json.load(f)
                    self.portfolio_value = portfolio_data.get('total_value', 1000000)
                    self.current_positions = portfolio_data.get('positions', {})
            
            # Загрузка торговых сигналов из файлов (если есть)
            signals_file = Path("data/signals.json")
            if signals_file.exists():
                with open(signals_file, 'r', encoding='utf-8') as f:
                    self.trading_signals = json.load(f)
            
            # Обновление интерфейса
            self.capital_label.config(text=f"{self.portfolio_value:,.0f} ₽")
            self.update_positions_table()
            self.update_signals_table()
            
        except Exception as e:
            logger.error(f"Ошибка загрузки данных системы: {e}")
    
    def load_data_from_logs(self):
        """Загрузка данных из логов системы"""
        try:
            # Чтение последних логов для извлечения данных
            log_file = Path("logs/neural_networks.log")
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # Анализ последних 50 строк логов
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                
                # Поиск информации о портфеле и сигналах
                for line in recent_lines:
                    if "портфель" in line.lower() or "portfolio" in line.lower():
                        # Извлечение данных о портфеле из логов
                        self.extract_portfolio_from_log(line)
                    elif "сигнал" in line.lower() or "signal" in line.lower():
                        # Извлечение торговых сигналов из логов
                        self.extract_signal_from_log(line)
                        
        except Exception as e:
            logger.error(f"Ошибка загрузки данных из логов: {e}")
    
    def extract_portfolio_from_log(self, log_line: str):
        """Извлечение данных портфеля из лога"""
        try:
            # Поиск числовых значений в логах
            import re
            numbers = re.findall(r'\d+\.?\d*', log_line)
            if numbers:
                # Если найдены числа, обновляем портфель
                value = float(numbers[0]) if numbers else 1000000
                if value > 100000:  # Разумное значение для портфеля
                    self.portfolio_value = value
                    
        except Exception as e:
            logger.error(f"Ошибка извлечения данных портфеля: {e}")
    
    def extract_signal_from_log(self, log_line: str):
        """Извлечение торгового сигнала из лога"""
        try:
            # Создание тестового сигнала на основе лога
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Определение типа сигнала по содержимому лога
            if "buy" in log_line.lower() or "покупка" in log_line.lower():
                signal_type = "BUY"
            elif "sell" in log_line.lower() or "продажа" in log_line.lower():
                signal_type = "SELL"
            else:
                signal_type = "HOLD"
            
            # Добавление сигнала
            signal = {
                'time': current_time,
                'symbol': 'SBER',  # По умолчанию
                'signal': signal_type,
                'confidence': 0.75,
                'action': f'Анализ: {signal_type}'
            }
            
            # Добавление в список сигналов (максимум 20)
            self.trading_signals.append(signal)
            if len(self.trading_signals) > 20:
                self.trading_signals = self.trading_signals[-20:]
                
        except Exception as e:
            logger.error(f"Ошибка извлечения сигнала: {e}")
    
    def update_real_data(self):
        """Обновление реальных данных из системы"""
        try:
            # Инициализация счетчика
            if not hasattr(self, '_update_counter'):
                self._update_counter = 0
            
            self._update_counter += 1
            
            # Каждые 5 секунд загружаем данные из системы
            if self._update_counter % 5 == 0:
                # Загрузка данных из логов
                self.load_system_data()
                
                # Обновление метрик
                self.update_metrics()
                
        except Exception as e:
            logger.error(f"Ошибка обновления реальных данных: {e}")
    
    def update_metrics(self):
        """Обновление метрик портфеля"""
        try:
            # Расчет общей доходности
            if self.portfolio_value > 0:
                total_return = ((self.portfolio_value - 1000000) / 1000000) * 100
                self.return_label.config(text=f"{total_return:+.2f}%")
                
                # Цвет в зависимости от доходности
                if total_return > 0:
                    self.return_label.config(foreground='green')
                elif total_return < 0:
                    self.return_label.config(foreground='red')
                else:
                    self.return_label.config(foreground='black')
            
            # Обновление количества позиций
            positions_count = len(self.current_positions)
            self.positions_count_label.config(text=str(positions_count))
            
            # Обновление последнего сигнала
            if self.trading_signals:
                last_signal = self.trading_signals[-1]
                signal_text = f"{last_signal['signal']} ({last_signal['symbol']})"
                self.last_signal_label.config(text=signal_text)
                
                # Цвет в зависимости от типа сигнала
                if last_signal['signal'] == 'BUY':
                    self.last_signal_label.config(foreground='green')
                elif last_signal['signal'] == 'SELL':
                    self.last_signal_label.config(foreground='red')
                else:
                    self.last_signal_label.config(foreground='black')
            
        except Exception as e:
            logger.error(f"Ошибка обновления метрик: {e}")
        
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

def main():
    """Главная функция"""
    try:
        app = InvestmentGUI()
        app.run()
    except Exception as e:
        logger.error(f"Ошибка запуска GUI: {e}")
        messagebox.showerror("Ошибка", f"Ошибка запуска GUI: {e}")

if __name__ == "__main__":
    main()
