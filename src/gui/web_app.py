"""
Веб-приложение для системы Neyro-Invest
FastAPI + WebSocket для real-time обновлений
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import asyncio
from loguru import logger
import os

# Импорт компонентов системы
try:
    from ..trading.tbank_broker import TBankBroker
    from ..core.investment_system import InvestmentSystem
    from ..portfolio.portfolio_manager import PortfolioManager
    from ..neural_networks.network_manager import NetworkManager
    from ..trading.trading_engine import TradingEngine
    SYSTEM_AVAILABLE = True
    logger.info("Системные модули загружены успешно")
except ImportError as e:
    SYSTEM_AVAILABLE = False
    logger.warning(f"Системные модули не доступны, работаем в демо-режиме: {e}")

# Создание приложения FastAPI
app = FastAPI(
    title="Neyro-Invest Web GUI",
    description="Веб-интерфейс для нейросетевой торговой системы",
    version="2.0.0"
)

# CORS для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Менеджер WebSocket подключений
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket подключен. Всего подключений: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket отключен. Осталось подключений: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Отправка сообщения всем подключенным клиентам"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения: {e}")

manager = ConnectionManager()

# Модели данных
class SystemStatus(BaseModel):
    is_running: bool
    mode: str
    account_id: Optional[str] = None
    balance: float = 0.0
    last_update: str

class PortfolioData(BaseModel):
    total_value: float
    cash_balance: float
    invested_value: float
    total_pnl: float
    total_pnl_percent: float
    positions_count: int
    last_update: str

class TradingSignal(BaseModel):
    timestamp: str
    symbol: str
    signal: str  # BUY, SELL, HOLD
    confidence: float
    source: str
    executed: bool = False

class ConfigData(BaseModel):
    initial_capital: float
    broker: str
    sandbox: bool
    symbols: List[str]
    signal_threshold: float

# Глобальное состояние
app_state = {
    "system_running": False,
    "investment_system": None,
    "broker": None,
    "portfolio_manager": None,
    "network_manager": None,
    "trading_engine": None,
    "portfolio_data": None,
    "signals": [],
    "config": None,
    "system_task": None,  # Задача для запущенной системы
    "last_portfolio_update": None,
    "last_signals_update": None
}

# Статические файлы
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir.mkdir(parents=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ==================== ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница"""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse(content=get_default_html(), status_code=200)

@app.get("/api/health")
async def health_check():
    """Проверка здоровья API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_available": SYSTEM_AVAILABLE
    }

@app.get("/api/system/status")
async def get_system_status():
    """Получение статуса системы"""
    try:
        # Проверка реального состояния процесса
        import psutil
        system_process_running = False
        
        # Проверяем, запущен ли основной процесс инвестиционной системы
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('investment_system' in str(arg).lower() or 'run.py' in str(arg) for arg in cmdline):
                    system_process_running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Синхронизируем состояние
        if system_process_running and not app_state["system_running"]:
            app_state["system_running"] = True
            logger.info("Обнаружен запущенный процесс системы")
        
        if app_state["broker"]:
            status = app_state["broker"].get_status()
            return SystemStatus(
                is_running=app_state["system_running"],
                mode=status.get("mode", "unknown"),
                account_id=status.get("account_id"),
                balance=0.0,  # Будет обновлено через WebSocket
                last_update=datetime.now().isoformat()
            )
        
        # Возвращаем статус на основе состояния
        return SystemStatus(
            is_running=app_state["system_running"],
            mode="standalone" if app_state["system_running"] else "disconnected",
            last_update=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        # В случае ошибки возвращаем текущее состояние
        return SystemStatus(
            is_running=app_state["system_running"],
            mode="unknown",
            last_update=datetime.now().isoformat()
        )

@app.post("/api/system/start")
async def start_system(config_path: str = "config/main.yaml"):
    """Запуск торговой системы"""
    try:
        if app_state["system_running"]:
            return {"message": "Система уже запущена", "status": "already_running"}
        
        if not SYSTEM_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="Системные модули недоступны. Установите все зависимости."
            )
        
        logger.info("Запуск торговой системы...")
        
        # Создание экземпляра инвестиционной системы
        investment_system = InvestmentSystem(config_path)
        app_state["investment_system"] = investment_system
        
        # Получение компонентов системы для доступа к данным
        app_state["portfolio_manager"] = investment_system.portfolio_manager
        app_state["network_manager"] = investment_system.network_manager
        app_state["trading_engine"] = investment_system.trading_engine
        
        # Запуск системы в фоновой задаче
        app_state["system_task"] = asyncio.create_task(
            investment_system.start_trading()
        )
        
        app_state["system_running"] = True
        app_state["start_time"] = datetime.now()
        
        # Уведомление всех подключенных клиентов
        await manager.broadcast({
            "type": "system_status",
            "data": {
                "is_running": True, 
                "message": "Система запущена",
                "timestamp": datetime.now().isoformat()
            }
        })
        
        logger.info("✅ Торговая система успешно запущена")
        return {
            "message": "Система запущена успешно",
            "status": "started",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска системы: {e}")
        app_state["system_running"] = False
        app_state["investment_system"] = None
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/system/stop")
async def stop_system():
    """Остановка торговой системы"""
    try:
        if not app_state["system_running"]:
            return {"message": "Система уже остановлена", "status": "already_stopped"}
        
        logger.info("Остановка торговой системы...")
        
        # Остановка инвестиционной системы
        if app_state["investment_system"]:
            await app_state["investment_system"].stop_trading()
        
        # Отмена фоновой задачи
        if app_state["system_task"] and not app_state["system_task"].done():
            app_state["system_task"].cancel()
            try:
                await app_state["system_task"]
            except asyncio.CancelledError:
                logger.info("Задача системы отменена")
        
        # Очистка состояния
        app_state["system_running"] = False
        app_state["investment_system"] = None
        app_state["portfolio_manager"] = None
        app_state["network_manager"] = None
        app_state["trading_engine"] = None
        app_state["system_task"] = None
        
        # Уведомление клиентов
        await manager.broadcast({
            "type": "system_status",
            "data": {
                "is_running": False, 
                "message": "Система остановлена",
                "timestamp": datetime.now().isoformat()
            }
        })
        
        logger.info("✅ Торговая система успешно остановлена")
        return {
            "message": "Система остановлена успешно", 
            "status": "stopped",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка остановки системы: {e}")
        # Всё равно пытаемся очистить состояние
        app_state["system_running"] = False
        app_state["investment_system"] = None
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio")
async def get_portfolio():
    """Получение данных портфеля"""
    try:
        # Если система запущена, получаем реальные данные
        if app_state["portfolio_manager"]:
            try:
                portfolio_data = app_state["portfolio_manager"].get_portfolio_summary()
                app_state["last_portfolio_update"] = datetime.now()
                return portfolio_data
            except Exception as e:
                logger.warning(f"Ошибка получения данных из portfolio_manager: {e}")
        
        # Попытка загрузить из файла
        portfolio_file = Path("data/portfolio.json")
        if portfolio_file.exists():
            try:
                with open(portfolio_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data["last_update"] = datetime.now().isoformat()
                    return data
            except Exception as e:
                logger.warning(f"Ошибка чтения файла портфеля: {e}")
        
        # Возвращаем demo данные
        logger.info("Возвращаем demo данные портфеля")
        return {
            "total_value": 1000000,
            "cash_balance": 100000,
            "invested_value": 900000,
            "total_pnl": 0,
            "total_pnl_percent": 0,
            "positions_count": 0,
            "positions": [],
            "last_update": datetime.now().isoformat(),
            "mode": "demo"
        }
    except Exception as e:
        logger.error(f"Ошибка получения портфеля: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/signals")
async def get_signals(limit: int = 20):
    """Получение торговых сигналов"""
    try:
        # Если система запущена, получаем реальные сигналы
        if app_state["trading_engine"]:
            try:
                signals = await app_state["trading_engine"].get_recent_signals(limit)
                app_state["last_signals_update"] = datetime.now()
                app_state["signals"] = signals
                return signals
            except Exception as e:
                logger.warning(f"Ошибка получения сигналов из trading_engine: {e}")
        
        # Попытка загрузить из файла
        signals_file = Path("data/signals.json")
        if signals_file.exists():
            try:
                with open(signals_file, 'r', encoding='utf-8') as f:
                    signals = json.load(f)
                    return signals[-limit:] if len(signals) > limit else signals
            except Exception as e:
                logger.warning(f"Ошибка чтения файла сигналов: {e}")
        
        # Возвращаем сохраненные сигналы или пустой список
        if app_state["signals"]:
            return app_state["signals"][-limit:]
        
        logger.info("Сигналов пока нет")
        return []
    except Exception as e:
        logger.error(f"Ошибка получения сигналов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tbank/check")
async def check_tbank_connection(token: str, sandbox: bool = True):
    """Проверка подключения к T-Bank API"""
    try:
        if not SYSTEM_AVAILABLE:
            raise HTTPException(status_code=503, detail="Системные модули недоступны")
        
        broker = TBankBroker(token=token, sandbox=sandbox)
        await broker.initialize()
        
        balance = await broker.get_total_balance_rub()
        status = broker.get_status()
        
        app_state["broker"] = broker
        
        return {
            "success": True,
            "mode": "sandbox" if sandbox else "production",
            "account_id": status.get("account_id"),
            "balance": balance,
            "instruments": status.get("instruments_loaded", 0)
        }
    except Exception as e:
        logger.error(f"Ошибка проверки T-Bank: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/tbank/get-balance")
async def get_tbank_balance(token: str, sandbox: bool = True):
    """Получение баланса с T-Bank счета"""
    try:
        if not SYSTEM_AVAILABLE:
            raise HTTPException(status_code=503, detail="Системные модули недоступны")
        
        broker = TBankBroker(token=token, sandbox=sandbox)
        await broker.initialize()
        balance = await broker.get_total_balance_rub()
        
        return {
            "balance": balance,
            "currency": "RUB"
        }
    except Exception as e:
        logger.error(f"Ошибка получения баланса: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/config")
async def get_config():
    """Получение текущей конфигурации"""
    try:
        config_file = Path("config/main.yaml")
        if config_file.exists():
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config
        
        return {}
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
async def save_config(config: dict):
    """Сохранение конфигурации"""
    try:
        config_file = Path("config/main.yaml")
        import yaml
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        return {"message": "Конфигурация сохранена успешно"}
    except Exception as e:
        logger.error(f"Ошибка сохранения конфигурации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """Получение логов системы"""
    try:
        log_file = Path("logs/investment_system.log")
        if not log_file.exists():
            return {"logs": []}
        
        with open(log_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
            return {"logs": log_lines[-lines:]}
    except Exception as e:
        logger.error(f"Ошибка загрузки логов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/info")
async def get_system_info():
    """Получение детальной информации о системе"""
    try:
        info = {
            "is_running": app_state["system_running"],
            "has_investment_system": app_state["investment_system"] is not None,
            "has_portfolio_manager": app_state["portfolio_manager"] is not None,
            "has_network_manager": app_state["network_manager"] is not None,
            "has_trading_engine": app_state["trading_engine"] is not None,
            "system_available": SYSTEM_AVAILABLE,
            "last_portfolio_update": app_state["last_portfolio_update"].isoformat() if app_state["last_portfolio_update"] else None,
            "last_signals_update": app_state["last_signals_update"].isoformat() if app_state["last_signals_update"] else None,
            "start_time": app_state.get("start_time").isoformat() if app_state.get("start_time") else None,
            "active_websockets": len(manager.active_connections),
            "timestamp": datetime.now().isoformat()
        }
        
        if app_state["investment_system"]:
            info["system_running_internally"] = app_state["investment_system"].is_running
        
        return info
    except Exception as e:
        logger.error(f"Ошибка получения информации о системе: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/metrics")
async def get_system_metrics():
    """Получение метрик системы"""
    try:
        metrics = {
            "portfolio": {
                "total_value": 0,
                "total_pnl": 0,
                "positions_count": 0
            },
            "signals": {
                "total_count": len(app_state.get("signals", [])),
                "recent_count": 0
            },
            "system": {
                "uptime_seconds": 0,
                "is_running": app_state["system_running"]
            }
        }
        
        # Добавляем метрики портфеля
        if app_state["portfolio_manager"]:
            try:
                portfolio_data = app_state["portfolio_manager"].get_portfolio_summary()
                metrics["portfolio"]["total_value"] = portfolio_data.get("total_value", 0)
                metrics["portfolio"]["total_pnl"] = portfolio_data.get("total_pnl", 0)
                metrics["portfolio"]["positions_count"] = portfolio_data.get("positions_count", 0)
            except:
                pass
        
        # Добавляем uptime
        if app_state.get("start_time"):
            uptime = datetime.now() - app_state["start_time"]
            metrics["system"]["uptime_seconds"] = int(uptime.total_seconds())
            metrics["system"]["uptime"] = str(uptime)
        
        return metrics
    except Exception as e:
        logger.error(f"Ошибка получения метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time обновлений"""
    await manager.connect(websocket)
    try:
        while True:
            # Получение данных от клиента
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Обработка команд
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
            # Периодическая отправка обновлений
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Ошибка WebSocket: {e}")
        manager.disconnect(websocket)

# Фоновая задача для отправки обновлений
async def broadcast_updates():
    """Периодическая отправка обновлений клиентам"""
    while True:
        try:
            if app_state["system_running"] and len(manager.active_connections) > 0:
                # Отправка обновления портфеля
                try:
                    portfolio_data = await get_portfolio()
                    await manager.broadcast({
                        "type": "portfolio_update",
                        "data": portfolio_data
                    })
                except Exception as e:
                    logger.warning(f"Ошибка отправки портфеля: {e}")
                
                # Отправка новых сигналов
                try:
                    signals = await get_signals(limit=10)
                    if signals:
                        await manager.broadcast({
                            "type": "signals_update",
                            "data": signals
                        })
                except Exception as e:
                    logger.warning(f"Ошибка отправки сигналов: {e}")
                
                # Отправка статуса системы
                try:
                    if app_state["investment_system"]:
                        status_data = {
                            "is_running": app_state["system_running"],
                            "uptime": str(datetime.now() - app_state.get("start_time", datetime.now())),
                            "last_update": datetime.now().isoformat()
                        }
                        await manager.broadcast({
                            "type": "system_status",
                            "data": status_data
                        })
                except Exception as e:
                    logger.warning(f"Ошибка отправки статуса: {e}")
            
            await asyncio.sleep(5)  # Обновление каждые 5 секунд
        except Exception as e:
            logger.error(f"Ошибка фоновой рассылки: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Событие при запуске приложения"""
    logger.info("Запуск веб-приложения Neyro-Invest")
    
    # Создание необходимых директорий
    for dir_name in ["logs", "data", "config"]:
        Path(dir_name).mkdir(exist_ok=True)
    
    # Проверка запущенной системы при старте
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('investment_system' in str(arg).lower() or 'run.py' in str(arg) for arg in cmdline):
                    app_state["system_running"] = True
                    logger.info("Обнаружен запущенный процесс инвестиционной системы")
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        logger.warning(f"Не удалось проверить статус системы при запуске: {e}")
    
    # Запуск фоновой задачи
    asyncio.create_task(broadcast_updates())

@app.on_event("shutdown")
async def shutdown_event():
    """Событие при остановке приложения"""
    logger.info("Остановка веб-приложения")
    if app_state["system_running"]:
        app_state["system_running"] = False

def get_default_html() -> str:
    """HTML по умолчанию, если нет index.html"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Neyro-Invest - Web GUI</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 600px;
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
                font-size: 2.5em;
            }
            .status {
                display: inline-block;
                padding: 10px 20px;
                background: #4CAF50;
                color: white;
                border-radius: 25px;
                margin: 20px 0;
            }
            .info {
                color: #666;
                margin: 20px 0;
                line-height: 1.6;
            }
            .btn {
                display: inline-block;
                padding: 12px 30px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 25px;
                margin: 10px;
                transition: transform 0.2s;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Neyro-Invest</h1>
            <div class="status">✅ API Running</div>
            <p class="info">
                Веб-интерфейс для нейросетевой торговой системы<br>
                Версия 2.0.0
            </p>
            <p class="info">
                <strong>API Endpoints:</strong><br>
                <code>/api/health</code> - Health check<br>
                <code>/api/system/status</code> - System status<br>
                <code>/api/portfolio</code> - Portfolio data<br>
                <code>/api/signals</code> - Trading signals<br>
                <code>/docs</code> - API Documentation
            </p>
            <a href="/docs" class="btn">📚 API Docs</a>
            <a href="/api/health" class="btn">🏥 Health Check</a>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

