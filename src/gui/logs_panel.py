"""
Панель просмотра логов в реальном времени
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
import time
import os
import re
from pathlib import Path
from loguru import logger


class LogsPanel:
    """
    Панель просмотра логов в реальном времени
    """
    
    def __init__(self, parent, main_window):
        """
        Инициализация панели логов
        
        Args:
            parent: Родительский виджет
            main_window: Главное окно приложения
        """
        self.parent = parent
        self.main_window = main_window
        
        # Настройки логов
        self.log_files = [
            "logs/investment_system.log",
            "logs/neural_networks.log",
            "logs/trading.log"
        ]
        self.current_log_file = self.log_files[0] if self.log_files else None
        self.auto_scroll = True
        self.auto_refresh = True
        self.refresh_interval = 2  # секунды
        self.max_lines = 1000
        
        # Фильтры
        self.level_filter = "ALL"
        self.text_filter = ""
        self.date_filter = None
        
        # Данные логов
        self.log_entries = []
        self.filtered_entries = []
        
        # Создание интерфейса
        self._create_widgets()
        
        # Запуск мониторинга логов
        self._start_log_monitoring()
        
        logger.info("Панель логов инициализирована")
    
    def _create_widgets(self):
        """
        Создание виджетов панели
        """
        # Главный контейнер
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель - управление и фильтры
        self._create_control_panel(main_frame)
        
        # Основная панель - просмотр логов
        self._create_logs_panel(main_frame)
        
        # Нижняя панель - статистика
        self._create_stats_panel(main_frame)
    
    def _create_control_panel(self, parent):
        """
        Создание панели управления
        
        Args:
            parent: Родительский виджет
        """
        # Рамка управления
        control_frame = ttk.LabelFrame(parent, text="Управление логами", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Первая строка - выбор файла и основные кнопки
        row1 = ttk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row1, text="Файл логов:").pack(side=tk.LEFT)
        
        self.log_file_var = tk.StringVar(value=self.current_log_file or "")
        log_file_combo = ttk.Combobox(
            row1,
            textvariable=self.log_file_var,
            values=self.log_files,
            width=40
        )
        log_file_combo.pack(side=tk.LEFT, padx=(10, 10))
        log_file_combo.bind('<<ComboboxSelected>>', self._on_log_file_changed)
        
        ttk.Button(
            row1,
            text="📁 Обзор...",
            command=self._browse_log_file
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            row1,
            text="🔄 Обновить",
            command=self._refresh_logs
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            row1,
            text="🗑 Очистить",
            command=self._clear_logs
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            row1,
            text="💾 Экспорт",
            command=self._export_logs
        ).pack(side=tk.LEFT)
        
        # Вторая строка - фильтры
        row2 = ttk.Frame(control_frame)
        row2.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(row2, text="Уровень:").pack(side=tk.LEFT)
        
        self.level_filter_var = tk.StringVar(value="ALL")
        level_combo = ttk.Combobox(
            row2,
            textvariable=self.level_filter_var,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly",
            width=10
        )
        level_combo.pack(side=tk.LEFT, padx=(5, 15))
        level_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        ttk.Label(row2, text="Поиск:").pack(side=tk.LEFT)
        
        self.text_filter_var = tk.StringVar()
        search_entry = ttk.Entry(
            row2,
            textvariable=self.text_filter_var,
            width=30
        )
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        search_entry.bind('<KeyRelease>', self._on_search_changed)
        
        ttk.Button(
            row2,
            text="🔍 Найти",
            command=self._apply_filters
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            row2,
            text="❌ Сбросить",
            command=self._reset_filters
        ).pack(side=tk.LEFT)
        
        # Третья строка - настройки
        row3 = ttk.Frame(control_frame)
        row3.pack(fill=tk.X)
        
        self.auto_scroll_var = tk.BooleanVar(value=self.auto_scroll)
        ttk.Checkbutton(
            row3,
            text="Автопрокрутка",
            variable=self.auto_scroll_var,
            command=self._on_auto_scroll_changed
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        self.auto_refresh_var = tk.BooleanVar(value=self.auto_refresh)
        ttk.Checkbutton(
            row3,
            text="Автообновление",
            variable=self.auto_refresh_var,
            command=self._on_auto_refresh_changed
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(row3, text="Интервал (сек):").pack(side=tk.LEFT)
        
        self.refresh_interval_var = tk.IntVar(value=self.refresh_interval)
        interval_spinbox = ttk.Spinbox(
            row3,
            from_=1,
            to=60,
            textvariable=self.refresh_interval_var,
            width=5,
            command=self._on_interval_changed
        )
        interval_spinbox.pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Label(row3, text="Макс. строк:").pack(side=tk.LEFT)
        
        self.max_lines_var = tk.IntVar(value=self.max_lines)
        max_lines_spinbox = ttk.Spinbox(
            row3,
            from_=100,
            to=10000,
            textvariable=self.max_lines_var,
            width=6,
            increment=100,
            command=self._on_max_lines_changed
        )
        max_lines_spinbox.pack(side=tk.LEFT, padx=(5, 0))
    
    def _create_logs_panel(self, parent):
        """
        Создание панели просмотра логов
        
        Args:
            parent: Родительский виджет
        """
        # Рамка логов
        logs_frame = ttk.LabelFrame(parent, text="Логи системы", padding=10)
        logs_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Создание Treeview для логов
        columns = ("Время", "Уровень", "Модуль", "Сообщение")
        self.logs_tree = ttk.Treeview(logs_frame, columns=columns, show='headings', height=20)
        
        # Настройка колонок
        column_widths = {"Время": 150, "Уровень": 80, "Модуль": 200, "Сообщение": 600}
        
        for col in columns:
            self.logs_tree.heading(col, text=col, command=lambda c=col: self._sort_logs(c))
            self.logs_tree.column(col, width=column_widths.get(col, 100), anchor='w')
        
        # Настройка цветов для разных уровней логов
        self.logs_tree.tag_configure('DEBUG', foreground='gray')
        self.logs_tree.tag_configure('INFO', foreground='black')
        self.logs_tree.tag_configure('WARNING', foreground='orange')
        self.logs_tree.tag_configure('ERROR', foreground='red')
        self.logs_tree.tag_configure('CRITICAL', foreground='red', background='yellow')
        
        # Скроллбары
        logs_v_scrollbar = ttk.Scrollbar(logs_frame, orient='vertical', command=self.logs_tree.yview)
        logs_h_scrollbar = ttk.Scrollbar(logs_frame, orient='horizontal', command=self.logs_tree.xview)
        self.logs_tree.configure(yscrollcommand=logs_v_scrollbar.set, xscrollcommand=logs_h_scrollbar.set)
        
        # Размещение
        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        logs_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        logs_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        # Контекстное меню
        self.logs_context_menu = tk.Menu(self.logs_tree, tearoff=0)
        self.logs_context_menu.add_command(label="Копировать строку", command=self._copy_log_line)
        self.logs_context_menu.add_command(label="Копировать сообщение", command=self._copy_log_message)
        self.logs_context_menu.add_separator()
        self.logs_context_menu.add_command(label="Показать детали", command=self._show_log_details)
        self.logs_context_menu.add_command(label="Фильтр по модулю", command=self._filter_by_module)
        self.logs_context_menu.add_command(label="Фильтр по уровню", command=self._filter_by_level)
        
        self.logs_tree.bind("<Button-3>", self._show_logs_context_menu)
        self.logs_tree.bind("<Double-1>", self._on_log_double_click)
    
    def _create_stats_panel(self, parent):
        """
        Создание панели статистики
        
        Args:
            parent: Родительский виджет
        """
        # Рамка статистики
        stats_frame = ttk.LabelFrame(parent, text="Статистика логов", padding=10)
        stats_frame.pack(fill=tk.X)
        
        # Создание сетки для статистики
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)
        
        for i in range(6):
            stats_grid.columnconfigure(i, weight=1)
        
        # Счетчики по уровням
        self._create_stat_counter(stats_grid, "Всего", "0", 0, 0, "blue")
        self._create_stat_counter(stats_grid, "DEBUG", "0", 0, 1, "gray")
        self._create_stat_counter(stats_grid, "INFO", "0", 0, 2, "black")
        self._create_stat_counter(stats_grid, "WARNING", "0", 0, 3, "orange")
        self._create_stat_counter(stats_grid, "ERROR", "0", 0, 4, "red")
        self._create_stat_counter(stats_grid, "CRITICAL", "0", 0, 5, "red")
        
        # Дополнительная информация
        info_frame = ttk.Frame(stats_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.file_info_label = ttk.Label(
            info_frame,
            text="Файл не выбран",
            font=('Arial', 9)
        )
        self.file_info_label.pack(side=tk.LEFT)
        
        self.last_update_label = ttk.Label(
            info_frame,
            text="",
            font=('Arial', 9)
        )
        self.last_update_label.pack(side=tk.RIGHT)
    
    def _create_stat_counter(self, parent, title: str, value: str, row: int, col: int, color: str):
        """
        Создание счетчика статистики
        
        Args:
            parent: Родительский виджет
            title: Заголовок счетчика
            value: Значение счетчика
            row: Строка в сетке
            col: Колонка в сетке
            color: Цвет значения
        """
        # Рамка счетчика
        counter_frame = ttk.Frame(parent, relief='raised', borderwidth=1)
        counter_frame.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
        
        # Заголовок
        title_label = ttk.Label(
            counter_frame,
            text=title,
            font=('Arial', 9, 'bold'),
            foreground='gray'
        )
        title_label.pack(pady=(5, 2))
        
        # Значение
        value_label = ttk.Label(
            counter_frame,
            text=value,
            font=('Arial', 12, 'bold'),
            foreground=color
        )
        value_label.pack(pady=(0, 5))
        
        # Сохранение ссылки для обновления
        setattr(self, f"stat_{title.lower()}", value_label)
    
    def _start_log_monitoring(self):
        """
        Запуск мониторинга логов
        """
        def monitoring_loop():
            while True:
                try:
                    if self.auto_refresh and self.current_log_file:
                        # Обновление в главном потоке
                        self.parent.after(0, self._refresh_logs)
                    
                    time.sleep(self.refresh_interval)
                    
                except Exception as e:
                    logger.error(f"Ошибка в цикле мониторинга логов: {e}")
        
        # Запуск в отдельном потоке
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
    
    def _browse_log_file(self):
        """
        Выбор файла логов
        """
        try:
            filename = filedialog.askopenfilename(
                title="Выберите файл логов",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
                initialdir="logs"
            )
            
            if filename:
                self.current_log_file = filename
                self.log_file_var.set(filename)
                self._refresh_logs()
                
        except Exception as e:
            logger.error(f"Ошибка выбора файла логов: {e}")
            messagebox.showerror("Ошибка", f"Не удалось выбрать файл: {e}")
    
    def _on_log_file_changed(self, event):
        """
        Обработка изменения файла логов
        
        Args:
            event: Событие изменения
        """
        try:
            self.current_log_file = self.log_file_var.get()
            self._refresh_logs()
        except Exception as e:
            logger.error(f"Ошибка изменения файла логов: {e}")
    
    def _refresh_logs(self):
        """
        Обновление логов
        """
        try:
            if not self.current_log_file or not os.path.exists(self.current_log_file):
                self.file_info_label.config(text="Файл не найден")
                return
            
            # Чтение файла логов
            self._read_log_file()
            
            # Применение фильтров
            self._apply_filters()
            
            # Обновление статистики
            self._update_statistics()
            
            # Обновление информации о файле
            file_size = os.path.getsize(self.current_log_file)
            file_size_str = self._format_file_size(file_size)
            self.file_info_label.config(text=f"Файл: {os.path.basename(self.current_log_file)} ({file_size_str})")
            
            # Обновление времени
            self.last_update_label.config(text=f"Обновлено: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Ошибка обновления логов: {e}")
            self.file_info_label.config(text=f"Ошибка: {e}")
    
    def _read_log_file(self):
        """
        Чтение файла логов
        """
        try:
            self.log_entries = []
            
            with open(self.current_log_file, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                
                # Ограничение количества строк
                if len(lines) > self.max_lines:
                    lines = lines[-self.max_lines:]
                
                for line in lines:
                    entry = self._parse_log_line(line.strip())
                    if entry:
                        self.log_entries.append(entry)
                        
        except Exception as e:
            logger.error(f"Ошибка чтения файла логов: {e}")
            raise
    
    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Парсинг строки лога
        
        Args:
            line: Строка лога
            
        Returns:
            Словарь с данными лога или None
        """
        try:
            if not line.strip():
                return None
            
            # Попытка парсинга формата loguru
            # Формат: "2024-01-15 10:30:45.123 | INFO | module:function:line - message"
            pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3})?)\s*\|\s*(\w+)\s*\|\s*([^-]+?)\s*-\s*(.+)'
            match = re.match(pattern, line)
            
            if match:
                timestamp_str, level, module, message = match.groups()
                
                # Парсинг времени
                try:
                    if '.' in timestamp_str:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                    else:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    timestamp = datetime.now()
                
                return {
                    'timestamp': timestamp,
                    'level': level.upper(),
                    'module': module.strip(),
                    'message': message.strip(),
                    'raw_line': line
                }
            
            # Если не удалось распарсить, создаем простую запись
            return {
                'timestamp': datetime.now(),
                'level': 'INFO',
                'module': 'unknown',
                'message': line,
                'raw_line': line
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга строки лога: {e}")
            return None
    
    def _apply_filters(self):
        """
        Применение фильтров к логам
        """
        try:
            self.filtered_entries = []
            
            for entry in self.log_entries:
                # Фильтр по уровню
                if self.level_filter != "ALL" and entry['level'] != self.level_filter:
                    continue
                
                # Фильтр по тексту
                if self.text_filter:
                    search_text = self.text_filter.lower()
                    if (search_text not in entry['message'].lower() and 
                        search_text not in entry['module'].lower()):
                        continue
                
                self.filtered_entries.append(entry)
            
            # Обновление таблицы
            self._update_logs_table()
            
        except Exception as e:
            logger.error(f"Ошибка применения фильтров: {e}")
    
    def _update_logs_table(self):
        """
        Обновление таблицы логов
        """
        try:
            # Очистка таблицы
            for item in self.logs_tree.get_children():
                self.logs_tree.delete(item)
            
            # Добавление отфильтрованных записей
            for entry in self.filtered_entries:
                timestamp_str = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                values = (timestamp_str, entry['level'], entry['module'], entry['message'])
                
                # Определение тега для цветового кодирования
                tag = entry['level']
                
                self.logs_tree.insert('', 'end', values=values, tags=(tag,))
            
            # Автопрокрутка к концу
            if self.auto_scroll and self.filtered_entries:
                self.logs_tree.see(self.logs_tree.get_children()[-1])
                
        except Exception as e:
            logger.error(f"Ошибка обновления таблицы логов: {e}")
    
    def _update_statistics(self):
        """
        Обновление статистики логов
        """
        try:
            # Подсчет по уровням
            level_counts = {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0}
            
            for entry in self.log_entries:
                level = entry['level']
                if level in level_counts:
                    level_counts[level] += 1
            
            total = sum(level_counts.values())
            
            # Обновление счетчиков
            if hasattr(self, 'stat_всего'):
                self.stat_всего.config(text=str(total))
            
            for level, count in level_counts.items():
                stat_attr = f"stat_{level.lower()}"
                if hasattr(self, stat_attr):
                    getattr(self, stat_attr).config(text=str(count))
                    
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Форматирование размера файла
        
        Args:
            size_bytes: Размер в байтах
            
        Returns:
            Отформатированный размер
        """
        try:
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        except:
            return "Unknown"
    
    def _clear_logs(self):
        """
        Очистка отображаемых логов
        """
        try:
            result = messagebox.askyesno(
                "Очистка логов",
                "Очистить отображаемые логи?\n(Файл логов не будет изменен)"
            )
            
            if result:
                # Очистка таблицы
                for item in self.logs_tree.get_children():
                    self.logs_tree.delete(item)
                
                # Очистка данных
                self.log_entries = []
                self.filtered_entries = []
                
                # Обновление статистики
                self._update_statistics()
                
                messagebox.showinfo("Информация", "Логи очищены")
                
        except Exception as e:
            logger.error(f"Ошибка очистки логов: {e}")
            messagebox.showerror("Ошибка", f"Не удалось очистить логи: {e}")
    
    def _export_logs(self):
        """
        Экспорт логов
        """
        try:
            if not self.filtered_entries:
                messagebox.showwarning("Предупреждение", "Нет логов для экспорта")
                return
            
            filename = filedialog.asksaveasfilename(
                title="Экспорт логов",
                filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")],
                defaultextension=".txt"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as file:
                    if filename.endswith('.csv'):
                        # CSV формат
                        file.write("Время,Уровень,Модуль,Сообщение\n")
                        for entry in self.filtered_entries:
                            timestamp_str = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                            file.write(f'"{timestamp_str}","{entry["level"]}","{entry["module"]}","{entry["message"]}"\n')
                    else:
                        # Текстовый формат
                        for entry in self.filtered_entries:
                            file.write(entry['raw_line'] + '\n')
                
                messagebox.showinfo("Успех", f"Логи экспортированы в {filename}")
                
        except Exception as e:
            logger.error(f"Ошибка экспорта логов: {e}")
            messagebox.showerror("Ошибка", f"Не удалось экспортировать логи: {e}")
    
    def _on_filter_changed(self, event):
        """
        Обработка изменения фильтра уровня
        
        Args:
            event: Событие изменения
        """
        try:
            self.level_filter = self.level_filter_var.get()
            self._apply_filters()
        except Exception as e:
            logger.error(f"Ошибка изменения фильтра уровня: {e}")
    
    def _on_search_changed(self, event):
        """
        Обработка изменения поискового запроса
        
        Args:
            event: Событие изменения
        """
        try:
            self.text_filter = self.text_filter_var.get()
            # Применяем фильтр с небольшой задержкой для избежания частых обновлений
            self.parent.after(500, self._apply_filters)
        except Exception as e:
            logger.error(f"Ошибка изменения поискового фильтра: {e}")
    
    def _reset_filters(self):
        """
        Сброс всех фильтров
        """
        try:
            self.level_filter_var.set("ALL")
            self.text_filter_var.set("")
            self.level_filter = "ALL"
            self.text_filter = ""
            self._apply_filters()
        except Exception as e:
            logger.error(f"Ошибка сброса фильтров: {e}")
    
    def _on_auto_scroll_changed(self):
        """
        Обработка изменения автопрокрутки
        """
        self.auto_scroll = self.auto_scroll_var.get()
    
    def _on_auto_refresh_changed(self):
        """
        Обработка изменения автообновления
        """
        self.auto_refresh = self.auto_refresh_var.get()
    
    def _on_interval_changed(self):
        """
        Обработка изменения интервала обновления
        """
        self.refresh_interval = self.refresh_interval_var.get()
    
    def _on_max_lines_changed(self):
        """
        Обработка изменения максимального количества строк
        """
        self.max_lines = self.max_lines_var.get()
    
    def _sort_logs(self, column: str):
        """
        Сортировка логов по колонке
        
        Args:
            column: Колонка для сортировки
        """
        try:
            # Определение ключа сортировки
            if column == "Время":
                key_func = lambda entry: entry['timestamp']
            elif column == "Уровень":
                level_order = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}
                key_func = lambda entry: level_order.get(entry['level'], 5)
            elif column == "Модуль":
                key_func = lambda entry: entry['module']
            else:  # Сообщение
                key_func = lambda entry: entry['message']
            
            # Сортировка
            self.filtered_entries.sort(key=key_func)
            
            # Обновление таблицы
            self._update_logs_table()
            
        except Exception as e:
            logger.error(f"Ошибка сортировки логов: {e}")
    
    def _show_logs_context_menu(self, event):
        """
        Показ контекстного меню для логов
        
        Args:
            event: Событие клика
        """
        try:
            self.logs_context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            logger.error(f"Ошибка показа контекстного меню логов: {e}")
    
    def _on_log_double_click(self, event):
        """
        Обработка двойного клика по логу
        
        Args:
            event: Событие клика
        """
        try:
            selection = self.logs_tree.selection()
            if selection:
                self._show_log_details()
        except Exception as e:
            logger.error(f"Ошибка обработки двойного клика: {e}")
    
    def _copy_log_line(self):
        """
        Копирование строки лога
        """
        try:
            selection = self.logs_tree.selection()
            if selection:
                item = self.logs_tree.item(selection[0])
                values = item['values']
                line = f"{values[0]} | {values[1]} | {values[2]} - {values[3]}"
                
                self.parent.clipboard_clear()
                self.parent.clipboard_append(line)
                messagebox.showinfo("Информация", "Строка скопирована в буфер обмена")
        except Exception as e:
            logger.error(f"Ошибка копирования строки лога: {e}")
    
    def _copy_log_message(self):
        """
        Копирование сообщения лога
        """
        try:
            selection = self.logs_tree.selection()
            if selection:
                item = self.logs_tree.item(selection[0])
                message = item['values'][3]
                
                self.parent.clipboard_clear()
                self.parent.clipboard_append(message)
                messagebox.showinfo("Информация", "Сообщение скопировано в буфер обмена")
        except Exception as e:
            logger.error(f"Ошибка копирования сообщения лога: {e}")
    
    def _show_log_details(self):
        """
        Показ детальной информации о логе
        """
        try:
            selection = self.logs_tree.selection()
            if selection:
                item = self.logs_tree.item(selection[0])
                values = item['values']
                
                details = f"""
Детальная информация о записи лога:

Время: {values[0]}
Уровень: {values[1]}
Модуль: {values[2]}
Сообщение: {values[3]}

Полная строка:
{values[0]} | {values[1]} | {values[2]} - {values[3]}
                """
                
                messagebox.showinfo("Детали лога", details)
        except Exception as e:
            logger.error(f"Ошибка показа деталей лога: {e}")
    
    def _filter_by_module(self):
        """
        Фильтрация по модулю
        """
        try:
            selection = self.logs_tree.selection()
            if selection:
                item = self.logs_tree.item(selection[0])
                module = item['values'][2]
                
                self.text_filter_var.set(module)
                self.text_filter = module
                self._apply_filters()
        except Exception as e:
            logger.error(f"Ошибка фильтрации по модулю: {e}")
    
    def _filter_by_level(self):
        """
        Фильтрация по уровню
        """
        try:
            selection = self.logs_tree.selection()
            if selection:
                item = self.logs_tree.item(selection[0])
                level = item['values'][1]
                
                self.level_filter_var.set(level)
                self.level_filter = level
                self._apply_filters()
        except Exception as e:
            logger.error(f"Ошибка фильтрации по уровню: {e}")
    
    def add_log_message(self, log_data: Dict[str, Any]):
        """
        Добавление нового сообщения лога
        
        Args:
            log_data: Данные лога
        """
        try:
            # Добавление в список записей
            entry = {
                'timestamp': log_data.get('timestamp', datetime.now()),
                'level': log_data.get('level', 'INFO'),
                'module': log_data.get('module', 'unknown'),
                'message': log_data.get('message', ''),
                'raw_line': log_data.get('raw_line', '')
            }
            
            self.log_entries.append(entry)
            
            # Ограничение количества записей
            if len(self.log_entries) > self.max_lines:
                self.log_entries = self.log_entries[-self.max_lines:]
            
            # Применение фильтров и обновление
            self._apply_filters()
            self._update_statistics()
            
        except Exception as e:
            logger.error(f"Ошибка добавления сообщения лога: {e}")
