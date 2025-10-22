// Vue.js приложение для Neyro-Invest

const { createApp } = Vue;

createApp({
    data() {
        return {
            // Текущая вкладка
            currentTab: 'dashboard',
            
            // Вкладки навигации
            tabs: [
                { id: 'dashboard', name: 'Дашборд', icon: '📊' },
                { id: 'trading', name: 'Торговля', icon: '⚡' },
                { id: 'portfolio', name: 'Портфель', icon: '💼' },
                { id: 'config', name: 'Настройки', icon: '⚙️' },
                { id: 'logs', name: 'Логи', icon: '📝' }
            ],
            
            // Состояние системы
            systemRunning: false,
            lastUpdate: new Date().toISOString(),
            
            // Данные портфеля
            portfolio: {
                total_value: 1000000,
                cash_balance: 100000,
                invested_value: 900000,
                total_pnl: 0,
                total_pnl_percent: 0,
                positions_count: 0,
                positions: [],
                last_update: new Date().toISOString()
            },
            
            // Торговые сигналы
            signals: [],
            
            // Конфигурация
            config: {
                tbank_token: '',
                sandbox: true,
                initial_capital: 1000000,
                signal_threshold: 0.7,
                symbols_text: 'SBER, GAZP, LKOH, YNDX, GMKN'
            },
            
            // Логи
            logs: [],
            autoRefreshLogs: false,
            
            // Статус подключения
            connectionStatus: null,
            
            // Модальное окно
            showTokenModal: false,
            
            // WebSocket
            ws: null,
            reconnectInterval: null
        };
    },
    
    mounted() {
        console.log('🚀 Neyro-Invest Web GUI загружен');
        
        // Загрузка данных
        this.loadSystemStatus();
        this.loadPortfolio();
        this.loadSignals();
        this.loadConfig();
        this.loadTbankToken();
        
        // Подключение WebSocket
        this.connectWebSocket();
        
        // Инициализация графиков
        this.$nextTick(() => {
            this.initCharts();
        });
        
        // Автообновление
        setInterval(() => {
            this.lastUpdate = new Date().toISOString();
            this.loadSystemStatus(); // Проверка статуса системы
            if (this.autoRefreshLogs) {
                this.loadLogs();
            }
        }, 5000);
    },
    
    beforeUnmount() {
        if (this.ws) {
            this.ws.close();
        }
        if (this.reconnectInterval) {
            clearInterval(this.reconnectInterval);
        }
    },
    
    methods: {
        // Переключение вкладок
        switchTab(tabId) {
            console.log('🔄 Переключение на вкладку:', tabId);
            this.currentTab = tabId;
        },
        
        // Форматирование валюты
        formatCurrency(value) {
            if (value === null || value === undefined || isNaN(value) || value === 'не число') {
                return '0 ₽';
            }
            return new Intl.NumberFormat('ru-RU', {
                style: 'currency',
                currency: 'RUB',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(Number(value));
        },
        
        // Форматирование времени
        formatTime(timestamp) {
            if (!timestamp) return '-';
            const date = new Date(timestamp);
            return date.toLocaleString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        },
        
        // Получение текста режима данных
        getModeText(mode) {
            const modes = {
                'real': 'T-Bank API',
                'system': 'Торговая система',
                'file': 'Сохраненные данные',
                'demo': 'Демо данные'
            };
            return modes[mode] || 'Неизвестно';
        },
        
        // Получение CSS класса для режима
        getModeClass(mode) {
            const classes = {
                'real': 'positive',
                'system': 'positive',
                'file': 'warning',
                'demo': 'negative'
            };
            return classes[mode] || '';
        },
        
        // WebSocket подключение
        connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            try {
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onopen = () => {
                    console.log('✅ WebSocket подключен');
                    if (this.reconnectInterval) {
                        clearInterval(this.reconnectInterval);
                        this.reconnectInterval = null;
                    }
                };
                
                this.ws.onmessage = (event) => {
                    const message = JSON.parse(event.data);
                    this.handleWebSocketMessage(message);
                };
                
                this.ws.onerror = (error) => {
                    console.error('❌ WebSocket ошибка:', error);
                };
                
                this.ws.onclose = () => {
                    console.log('🔌 WebSocket отключен');
                    // Переподключение через 5 секунд
                    if (!this.reconnectInterval) {
                        this.reconnectInterval = setInterval(() => {
                            console.log('🔄 Попытка переподключения...');
                            this.connectWebSocket();
                        }, 5000);
                    }
                };
            } catch (error) {
                console.error('Ошибка создания WebSocket:', error);
            }
        },
        
        // Обработка сообщений WebSocket
        handleWebSocketMessage(message) {
            console.log('📨 WebSocket сообщение:', message);
            
            switch (message.type) {
                case 'portfolio_update':
                    this.portfolio = { ...this.portfolio, ...message.data };
                    console.log('📊 Портфель обновлен через WebSocket');
                    this.$nextTick(() => {
                        this.updateCharts();
                    });
                    break;
                    
                case 'system_status':
                    const wasRunning = this.systemRunning;
                    this.systemRunning = message.data.is_running;
                    if (wasRunning !== this.systemRunning) {
                        console.log('🔄 Статус системы изменен:', this.systemRunning ? 'Запущена' : 'Остановлена');
                    }
                    break;
                    
                case 'signals_update':
                    if (message.data && message.data.length > 0) {
                        this.signals = message.data;
                        console.log('📡 Сигналы обновлены через WebSocket:', message.data.length);
                    }
                    break;
                    
                case 'new_signal':
                    this.signals.unshift(message.data);
                    if (this.signals.length > 50) {
                        this.signals = this.signals.slice(0, 50);
                    }
                    console.log('🆕 Новый сигнал:', message.data);
                    break;
                    
                case 'pong':
                    // Ответ на ping
                    break;
                    
                default:
                    console.log('❓ Неизвестный тип сообщения:', message.type);
            }
        },
        
        // Загрузка статуса системы
        async loadSystemStatus() {
            try {
                const response = await fetch('/api/system/status');
                if (response.ok) {
                    const data = await response.json();
                    this.systemRunning = data.is_running;
                    console.log('✅ Статус системы:', data.is_running ? 'Запущена' : 'Остановлена');
                }
            } catch (error) {
                console.error('❌ Ошибка загрузки статуса:', error);
            }
        },
        
        // Загрузка портфеля
        async loadPortfolio() {
            try {
                const response = await fetch('/api/portfolio');
                if (response.ok) {
                    const data = await response.json();
                    
                    // Очистка некорректных данных
                    const cleanData = {
                        total_value: Number(data.total_value) || 0,
                        cash_balance: Number(data.cash_balance) || 0,
                        invested_value: Number(data.invested_value) || 0,
                        total_pnl: Number(data.total_pnl) || 0,
                        total_pnl_percent: Number(data.total_pnl_percent) || 0,
                        positions_count: Number(data.positions_count) || 0,
                        positions: Array.isArray(data.positions) ? data.positions.map(pos => ({
                            ...pos,
                            quantity: Number(pos.quantity) || 0,
                            avg_price: Number(pos.avg_price) || 0,
                            current_price: Number(pos.current_price) || 0,
                            value: Number(pos.value) || 0,
                            pnl: Number(pos.pnl) || 0,
                            pnl_percent: Number(pos.pnl_percent) || 0,
                            weight_percent: Number(pos.weight_percent) || 0
                        })) : [],
                        last_update: data.last_update || new Date().toISOString()
                    };
                    
                    this.portfolio = { ...this.portfolio, ...cleanData };
                    console.log('✅ Портфель загружен:', cleanData);
                    
                    // Обновление графиков при изменении данных
                    this.$nextTick(() => {
                        this.updateCharts();
                    });
                }
            } catch (error) {
                console.error('❌ Ошибка загрузки портфеля:', error);
            }
        },
        
        // Загрузка сигналов
        async loadSignals() {
            try {
                const response = await fetch('/api/signals?limit=20');
                if (response.ok) {
                    this.signals = await response.json();
                    console.log('✅ Сигналы загружены:', this.signals.length);
                }
            } catch (error) {
                console.error('❌ Ошибка загрузки сигналов:', error);
            }
        },
        
        // Загрузка конфигурации
        async loadConfig() {
            try {
                const response = await fetch('/api/config');
                if (response.ok) {
                    const data = await response.json();
                    if (data.portfolio) {
                        this.config.initial_capital = data.portfolio.initial_capital || 1000000;
                    }
                    if (data.signals) {
                        this.config.signal_threshold = data.signals.threshold || 0.7;
                    }
                    if (data.tinkoff) {
                        this.config.sandbox = data.tinkoff.sandbox !== false;
                    }
                    console.log('✅ Конфигурация загружена');
                }
            } catch (error) {
                console.error('❌ Ошибка загрузки конфигурации:', error);
            }
        },
        
        // Загрузка токена T-Bank
        async loadTbankToken() {
            try {
                const response = await fetch('/api/tbank-token');
                if (response.ok) {
                    const data = await response.json();
                    if (data.token) {
                        this.config.tbank_token = data.token;
                        console.log(`✅ T-Bank токен загружен из ${data.source}`);
                    }
                }
            } catch (error) {
                console.error('❌ Ошибка загрузки токена T-Bank:', error);
            }
        },
        
        // Сохранение конфигурации
        async saveConfig() {
            try {
                const configData = {
                    portfolio: {
                        initial_capital: this.config.initial_capital
                    },
                    signals: {
                        threshold: this.config.signal_threshold
                    },
                    tinkoff: {
                        sandbox: this.config.sandbox
                    }
                };
                
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(configData)
                });
                
                if (response.ok) {
                    alert('✅ Конфигурация сохранена успешно!');
                } else {
                    alert('❌ Ошибка сохранения конфигурации');
                }
            } catch (error) {
                console.error('❌ Ошибка сохранения конфигурации:', error);
                alert('❌ Ошибка сохранения конфигурации: ' + error.message);
            }
        },
        
        // Загрузка логов
        async loadLogs() {
            try {
                const response = await fetch('/api/logs?lines=100');
                if (response.ok) {
                    const data = await response.json();
                    this.logs = data.logs || [];
                }
            } catch (error) {
                console.error('❌ Ошибка загрузки логов:', error);
            }
        },
        
        // Очистка экрана логов
        clearLogsDisplay() {
            this.logs = [];
        },
        
        // Запуск системы
        async startSystem() {
            try {
                const response = await fetch('/api/system/start', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.systemRunning = true;
                    alert('✅ ' + data.message);
                } else {
                    alert('❌ Ошибка запуска системы');
                }
            } catch (error) {
                console.error('❌ Ошибка запуска системы:', error);
                alert('❌ Ошибка запуска системы: ' + error.message);
            }
        },
        
        // Остановка системы
        async stopSystem() {
            try {
                const response = await fetch('/api/system/stop', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.systemRunning = false;
                    alert('✅ ' + data.message);
                } else {
                    alert('❌ Ошибка остановки системы');
                }
            } catch (error) {
                console.error('❌ Ошибка остановки системы:', error);
                alert('❌ Ошибка остановки системы: ' + error.message);
            }
        },
        
        // Проверка подключения T-Bank
        async checkTbankConnection() {
            if (!this.config.tbank_token) {
                alert('⚠️ Введите токен T-Bank');
                return;
            }
            
            this.connectionStatus = null;
            
            try {
                const response = await fetch('/api/tbank/check', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        token: this.config.tbank_token,
                        sandbox: this.config.sandbox
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.connectionStatus = {
                        success: true,
                        ...data
                    };
                } else {
                    const error = await response.json();
                    this.connectionStatus = {
                        success: false,
                        error: error.detail || 'Неизвестная ошибка'
                    };
                }
            } catch (error) {
                console.error('❌ Ошибка проверки подключения:', error);
                this.connectionStatus = {
                    success: false,
                    error: error.message
                };
            }
        },
        
        // Получение баланса
        async getTbankBalance() {
            if (!this.config.tbank_token) {
                alert('⚠️ Введите токен T-Bank');
                return;
            }
            
            try {
                const response = await fetch('/api/tbank/get-balance', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        token: this.config.tbank_token,
                        sandbox: this.config.sandbox
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.config.initial_capital = Math.floor(data.balance);
                    alert(`✅ Баланс получен: ${this.formatCurrency(data.balance)}`);
                } else {
                    const error = await response.json();
                    alert('❌ Ошибка получения баланса: ' + error.detail);
                }
            } catch (error) {
                console.error('❌ Ошибка получения баланса:', error);
                alert('❌ Ошибка получения баланса: ' + error.message);
            }
        },
        
        // Показать справку по токену
        showTokenHelp() {
            this.showTokenModal = true;
        },
        
        // Инициализация графиков
        initCharts() {
            this.initPortfolioChart();
            this.initAssetsChart();
        },
        
        // Обновление графиков
        updateCharts() {
            // Пересоздание графиков с новыми данными
            const portfolioCanvas = document.getElementById('portfolioChart');
            const assetsCanvas = document.getElementById('assetsChart');
            
            if (portfolioCanvas && assetsCanvas) {
                // Уничтожение старых графиков если они существуют
                Chart.getChart('portfolioChart')?.destroy();
                Chart.getChart('assetsChart')?.destroy();
                
                // Создание новых графиков
                this.initPortfolioChart();
                this.initAssetsChart();
            }
        },
        
        // График портфеля
        initPortfolioChart() {
            const canvas = document.getElementById('portfolioChart');
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            
            // Демо-данные для графика
            const labels = [];
            const data = [];
            const now = new Date();
            
            for (let i = 30; i >= 0; i--) {
                const date = new Date(now);
                date.setDate(date.getDate() - i);
                labels.push(date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' }));
                
                // Случайные данные для демонстрации
                const baseValue = 1000000;
                const variation = Math.sin(i / 5) * 50000 + Math.random() * 30000;
                data.push(baseValue + variation);
            }
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Стоимость портфеля',
                        data: data,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    return this.formatCurrency(context.parsed.y);
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                callback: (value) => {
                                    return ((value || 0) / 1000).toFixed(0) + 'K';
                                }
                            }
                        }
                    }
                }
            });
        },
        
        // График распределения активов
        initAssetsChart() {
            const canvas = document.getElementById('assetsChart');
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Денежные средства', 'Акции', 'Облигации'],
                    datasets: [{
                        data: [
                            this.portfolio.cash_balance,
                            this.portfolio.invested_value * 0.7,
                            this.portfolio.invested_value * 0.3
                        ],
                        backgroundColor: [
                            '#4CAF50',
                            '#667eea',
                            '#764ba2'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const label = context.label || '';
                                    const value = this.formatCurrency(context.parsed);
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percent = (((context.parsed || 0) / (total || 1)) * 100).toFixed(1);
                                    return `${label}: ${value} (${percent}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }
}).mount('#app');

