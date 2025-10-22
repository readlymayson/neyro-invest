"""
Брокер для торговли через T-Bank (Tinkoff) Invest API
Поддерживает работу в sandbox и production режимах
Документация: https://developer.tbank.ru/invest/intro/developer/sandbox
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal
from loguru import logger
import asyncio

try:
    from tinkoff.invest import Client, AsyncClient, OrderDirection, OrderType
    from tinkoff.invest.schemas import (
        PostOrderResponse, 
        OrderState,
        MoneyValue,
        OperationState,
        OperationType
    )
    from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX
    TINKOFF_AVAILABLE = True
except ImportError:
    TINKOFF_AVAILABLE = False
    logger.warning("Библиотека tinkoff-investments не установлена. T-Bank брокер недоступен.")


class TBankBroker:
    """
    Брокер для торговли через T-Bank Invest API
    
    Особенности песочницы:
    - Виртуальные счета (создаются и удаляются по требованию)
    - Не начисляются дивиденды и купоны
    - Упрощенный алгоритм исполнения ордеров
    - Комиссия 0.05% от объема сделки
    - Маржинальная торговля с плечом 2
    """
    
    def __init__(self, token: str, sandbox: bool = True, account_id: Optional[str] = None):
        """
        Инициализация брокера T-Bank
        
        Args:
            token: API токен T-Bank Invest
            sandbox: Использовать песочницу (True) или prod (False)
            account_id: ID счета (для sandbox будет создан автоматически если не указан)
        """
        if not TINKOFF_AVAILABLE:
            raise ImportError(
                "Для работы с T-Bank API необходимо установить библиотеку: "
                "pip install tinkoff-investments"
            )
        
        self.token = token
        self.sandbox = sandbox
        self.target = INVEST_GRPC_API_SANDBOX if sandbox else INVEST_GRPC_API
        self.account_id = account_id
        
        # Кэш данных
        self.instruments_cache: Dict[str, str] = {}  # ticker -> figi
        self.positions: Dict[str, Dict] = {}
        self.orders: Dict[str, Dict] = {}
        self.client = None  # Сохраняем клиент для использования в веб-GUI
        
        mode = "SANDBOX" if sandbox else "PRODUCTION"
        logger.info(f"Инициализирован T-Bank брокер в режиме {mode}")
    
    def get_client(self):
        """Получение клиента для использования в веб-GUI"""
        return AsyncClient(self.token, target=self.target)
    
    async def initialize(self):
        """
        Инициализация брокера
        """
        logger.info("Инициализация T-Bank брокера")
        
        try:
            async with AsyncClient(self.token, target=self.target) as client:
                # Загрузка списка инструментов
                response = await client.instruments.shares()
                for share in response.instruments:
                    # В sandbox проверяем дополнительно trading_status
                    if self.sandbox:
                        # Для sandbox проверяем, что инструмент доступен для торговли
                        if share.api_trade_available_flag and share.trading_status.name == 'SECURITY_TRADING_STATUS_NORMAL_TRADING':
                            self.instruments_cache[share.ticker] = share.figi
                    else:
                        # Для production достаточно флага api_trade_available_flag
                        if share.api_trade_available_flag:
                            self.instruments_cache[share.ticker] = share.figi
                
                logger.info(f"Загружено {len(self.instruments_cache)} торгуемых инструментов")
                
                # Вывод примеров доступных тикеров для отладки
                if self.instruments_cache:
                    sample_tickers = list(self.instruments_cache.keys())[:10]
                    logger.debug(f"Примеры доступных тикеров: {', '.join(sample_tickers)}")
                
                # Для sandbox: создание/получение счета
                if self.sandbox:
                    await self._setup_sandbox_account(client)
                else:
                    # Для prod: получение списка счетов
                    accounts = await client.users.get_accounts()
                    if accounts.accounts:
                        if not self.account_id:
                            self.account_id = accounts.accounts[0].id
                        logger.info(f"Используется счет: {self.account_id}")
                    else:
                        raise ValueError("Не найдено ни одного счета")
                
                # Загрузка текущих позиций
                await self.update_positions()
                
        except Exception as e:
            logger.error(f"Ошибка инициализации T-Bank брокера: {e}")
            raise
    
    async def _setup_sandbox_account(self, client):
        """
        Настройка счета в песочнице
        
        Args:
            client: Клиент T-Bank API
        """
        if not self.account_id:
            try:
                # Сначала проверяем существующие sandbox аккаунты
                accounts_response = await client.sandbox.get_sandbox_accounts()
                if accounts_response.accounts:
                    # Используем первый доступный аккаунт
                    self.account_id = accounts_response.accounts[0].id
                    logger.info(f"Используется существующий sandbox счет: {self.account_id}")
                else:
                    # Создание нового счета в песочнице
                    response = await client.sandbox.open_sandbox_account()
                    self.account_id = response.account_id
                    logger.info(f"Создан новый sandbox счет: {self.account_id}")
                    
                    # Пополнение счета (по умолчанию 1 млн рублей)
                    await client.sandbox.sandbox_pay_in(
                        account_id=self.account_id,
                        amount=self._money_value(1_000_000, "rub")
                    )
                    logger.info("Счет пополнен на 1,000,000 RUB")
            except Exception as e:
                if "Sandbox accounts limit reached" in str(e):
                    logger.warning("Достигнут лимит sandbox аккаунтов, попытка использовать существующий...")
                    # Попробуем получить существующие аккаунты еще раз
                    try:
                        accounts_response = await client.sandbox.get_sandbox_accounts()
                        if accounts_response.accounts:
                            self.account_id = accounts_response.accounts[0].id
                            logger.info(f"Используется существующий sandbox счет: {self.account_id}")
                        else:
                            raise e
                    except Exception as e2:
                        logger.error(f"Не удалось получить существующие sandbox аккаунты: {e2}")
                        raise e
                else:
                    raise e
        else:
            logger.info(f"Используется существующий sandbox счет: {self.account_id}")
    
    async def update_positions(self):
        """
        Обновление текущих позиций
        """
        try:
            async with AsyncClient(self.token, target=self.target) as client:
                if self.sandbox:
                    response = await client.sandbox.get_sandbox_positions(
                        account_id=self.account_id
                    )
                else:
                    response = await client.operations.get_positions(
                        account_id=self.account_id
                    )
                
                self.positions = {}
                for position in response.securities:
                    # Находим тикер по FIGI
                    ticker = self._figi_to_ticker(position.figi)
                    if ticker:
                        self.positions[ticker] = {
                            'figi': position.figi,
                            'quantity': self._quotation_to_float(position.balance),
                            'blocked': self._quotation_to_float(position.blocked) if hasattr(position, 'blocked') else 0,
                            'average_price': self._money_value_to_float(position.average_position_price) if hasattr(position, 'average_position_price') else 0,
                        }
                
                logger.debug(f"Обновлены позиции: {len(self.positions)} инструментов")
                
        except Exception as e:
            logger.error(f"Ошибка обновления позиций: {e}")
    
    async def place_order(
        self,
        ticker: str,
        quantity: int,
        direction: str,
        order_type: str = "market",
        price: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Размещение ордера
        
        Args:
            ticker: Тикер инструмента
            quantity: Количество лотов
            direction: Направление ("buy" или "sell")
            order_type: Тип ордера ("market" или "limit")
            price: Цена для limit ордера
            
        Returns:
            Информация о размещенном ордере
        """
        try:
            figi = self.instruments_cache.get(ticker)
            if not figi:
                logger.warning(
                    f"Инструмент {ticker} недоступен для торговли в {'sandbox' if self.sandbox else 'production'}. "
                    f"Доступно {len(self.instruments_cache)} инструментов."
                )
                return None
            
            # Конвертация параметров
            order_direction = (
                OrderDirection.ORDER_DIRECTION_BUY 
                if direction.lower() == "buy" 
                else OrderDirection.ORDER_DIRECTION_SELL
            )
            
            order_type_enum = (
                OrderType.ORDER_TYPE_MARKET 
                if order_type.lower() == "market" 
                else OrderType.ORDER_TYPE_LIMIT
            )
            
            async with AsyncClient(self.token, target=self.target) as client:
                # Размещение ордера
                if self.sandbox:
                    response = await client.sandbox.post_sandbox_order(
                        figi=figi,
                        quantity=quantity,
                        account_id=self.account_id,
                        direction=order_direction,
                        order_type=order_type_enum,
                        price=self._quotation(price) if price else None
                    )
                else:
                    response = await client.orders.post_order(
                        figi=figi,
                        quantity=quantity,
                        account_id=self.account_id,
                        direction=order_direction,
                        order_type=order_type_enum,
                        price=self._quotation(price) if price else None
                    )
                
                order_info = {
                    'order_id': response.order_id,
                    'ticker': ticker,
                    'figi': figi,
                    'direction': direction,
                    'quantity': quantity,
                    'order_type': order_type,
                    'price': price,
                    'status': 'placed',
                    'timestamp': datetime.now().isoformat(),
                    'execution_price': self._money_value_to_float(response.executed_order_price) if hasattr(response, 'executed_order_price') else None,
                    'total_commission': self._money_value_to_float(response.total_order_amount) if hasattr(response, 'total_order_amount') else None,
                }
                
                self.orders[response.order_id] = order_info
                
                logger.info(
                    f"Ордер размещен: {direction.upper()} {quantity} лотов {ticker} "
                    f"(order_id: {response.order_id})"
                )
                
                return order_info
                
        except Exception as e:
            logger.error(f"Ошибка размещения ордера для {ticker}: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Отмена ордера
        
        Args:
            order_id: ID ордера
            
        Returns:
            True если ордер отменен успешно
        """
        try:
            async with AsyncClient(self.token, target=self.target) as client:
                if self.sandbox:
                    await client.sandbox.cancel_sandbox_order(
                        account_id=self.account_id,
                        order_id=order_id
                    )
                else:
                    await client.orders.cancel_order(
                        account_id=self.account_id,
                        order_id=order_id
                    )
                
                if order_id in self.orders:
                    self.orders[order_id]['status'] = 'cancelled'
                
                logger.info(f"Ордер {order_id} отменен")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка отмены ордера {order_id}: {e}")
            return False
    
    async def get_order_state(self, order_id: str) -> Optional[Dict]:
        """
        Получение состояния ордера
        
        Args:
            order_id: ID ордера
            
        Returns:
            Информация о состоянии ордера
        """
        try:
            async with AsyncClient(self.token, target=self.target) as client:
                if self.sandbox:
                    response = await client.sandbox.get_sandbox_order_state(
                        account_id=self.account_id,
                        order_id=order_id
                    )
                else:
                    response = await client.orders.get_order_state(
                        account_id=self.account_id,
                        order_id=order_id
                    )
                
                return {
                    'order_id': response.order_id,
                    'execution_status': str(response.execution_report_status),
                    'lots_requested': response.lots_requested,
                    'lots_executed': response.lots_executed,
                    'initial_price': self._money_value_to_float(response.initial_order_price) if hasattr(response, 'initial_order_price') else None,
                    'executed_price': self._money_value_to_float(response.executed_order_price) if hasattr(response, 'executed_order_price') else None,
                    'total_commission': self._money_value_to_float(response.total_order_amount) if hasattr(response, 'total_order_amount') else None,
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения состояния ордера {order_id}: {e}")
            return None
    
    async def get_portfolio(self) -> Dict:
        """
        Получение информации о портфеле
        
        Returns:
            Информация о портфеле
        """
        try:
            async with AsyncClient(self.token, target=self.target) as client:
                if self.sandbox:
                    response = await client.sandbox.get_sandbox_portfolio(
                        account_id=self.account_id
                    )
                else:
                    response = await client.operations.get_portfolio(
                        account_id=self.account_id
                    )
                
                portfolio = {
                    'total_amount': self._money_value_to_float(response.total_amount_shares) if hasattr(response, 'total_amount_shares') else 0,
                    'expected_yield': self._quotation_to_float(response.expected_yield) if hasattr(response, 'expected_yield') else 0,
                    'positions': []
                }
                
                for position in response.positions:
                    ticker = self._figi_to_ticker(position.figi)
                    portfolio['positions'].append({
                        'ticker': ticker,
                        'figi': position.figi,
                        'quantity': self._quotation_to_float(position.quantity),
                        'average_price': self._money_value_to_float(position.average_position_price) if hasattr(position, 'average_position_price') else 0,
                        'current_price': self._money_value_to_float(position.current_price) if hasattr(position, 'current_price') else 0,
                        'expected_yield': self._quotation_to_float(position.expected_yield) if hasattr(position, 'expected_yield') else 0,
                    })
                
                return portfolio
                
        except Exception as e:
            logger.error(f"Ошибка получения портфеля: {e}")
            return {'total_amount': 0, 'expected_yield': 0, 'positions': []}
    
    async def get_account_balance(self) -> Dict[str, float]:
        """
        Получение баланса счета (денежные средства по валютам)
        
        Returns:
            Словарь с балансами по валютам: {'rub': amount, 'usd': amount, ...}
        """
        try:
            async with AsyncClient(self.token, target=self.target) as client:
                if self.sandbox:
                    response = await client.sandbox.get_sandbox_positions(
                        account_id=self.account_id
                    )
                else:
                    response = await client.operations.get_positions(
                        account_id=self.account_id
                    )
                
                balances = {}
                
                # Получение денежных средств
                if hasattr(response, 'money') and response.money:
                    for money in response.money:
                        currency = money.currency.lower()
                        amount = self._money_value_to_float(money)
                        balances[currency] = amount
                
                logger.debug(f"Получены балансы счета: {balances}")
                return balances
                
        except Exception as e:
            logger.error(f"Ошибка получения баланса счета: {e}")
            return {}
    
    async def get_total_balance_rub(self) -> float:
        """
        Получение общего баланса в рублях (доступные средства)
        
        Returns:
            Сумма доступных средств в рублях
        """
        try:
            balances = await self.get_account_balance()
            rub_balance = balances.get('rub', 0.0)
            
            logger.info(f"Доступные средства на счете: {rub_balance:,.2f} ₽")
            return rub_balance
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса в рублях: {e}")
            return 0.0
    
    async def get_operations(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Получение списка операций
        
        Args:
            from_date: Начальная дата
            to_date: Конечная дата
            
        Returns:
            Список операций
        """
        try:
            if not from_date:
                from_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if not to_date:
                to_date = datetime.now()
            
            async with AsyncClient(self.token, target=self.target) as client:
                if self.sandbox:
                    response = await client.sandbox.get_sandbox_operations(
                        account_id=self.account_id,
                        from_=from_date,
                        to=to_date
                    )
                else:
                    response = await client.operations.get_operations(
                        account_id=self.account_id,
                        from_=from_date,
                        to=to_date
                    )
                
                operations = []
                for op in response.operations:
                    operations.append({
                        'id': op.id,
                        'type': str(op.operation_type),
                        'date': op.date.isoformat() if op.date else None,
                        'state': str(op.state),
                        'figi': op.figi if hasattr(op, 'figi') else None,
                        'quantity': op.quantity if hasattr(op, 'quantity') else 0,
                        'price': self._money_value_to_float(op.price) if hasattr(op, 'price') else 0,
                        'payment': self._money_value_to_float(op.payment) if hasattr(op, 'payment') else 0,
                    })
                
                return operations
                
        except Exception as e:
            logger.error(f"Ошибка получения операций: {e}")
            return []
    
    async def close_sandbox_account(self):
        """
        Закрытие счета в песочнице
        """
        if not self.sandbox:
            logger.warning("Метод доступен только для sandbox")
            return
        
        try:
            async with AsyncClient(self.token, target=self.target) as client:
                await client.sandbox.close_sandbox_account(
                    account_id=self.account_id
                )
                logger.info(f"Sandbox счет {self.account_id} закрыт")
                self.account_id = None
                
        except Exception as e:
            logger.error(f"Ошибка закрытия sandbox счета: {e}")
    
    def _ticker_to_figi(self, ticker: str) -> Optional[str]:
        """Конвертация тикера в FIGI"""
        return self.instruments_cache.get(ticker)
    
    def _figi_to_ticker(self, figi: str) -> Optional[str]:
        """Конвертация FIGI в тикер"""
        for ticker, f in self.instruments_cache.items():
            if f == figi:
                return ticker
        return None
    
    def _quotation_to_float(self, quotation) -> float:
        """Конвертация Quotation в float"""
        if quotation is None:
            return 0.0
        # Если уже число - вернуть как есть
        if isinstance(quotation, (int, float)):
            return float(quotation)
        # Если Quotation объект
        if hasattr(quotation, 'units') and hasattr(quotation, 'nano'):
            return quotation.units + quotation.nano / 1_000_000_000
        return 0.0
    
    def _quotation(self, value: float):
        """Конвертация float в Quotation"""
        from tinkoff.invest import Quotation
        units = int(value)
        nano = int((value - units) * 1_000_000_000)
        return Quotation(units=units, nano=nano)
    
    def _money_value(self, value: float, currency: str = "rub"):
        """Создание MoneyValue"""
        from tinkoff.invest import MoneyValue
        units = int(value)
        nano = int((value - units) * 1_000_000_000)
        return MoneyValue(currency=currency, units=units, nano=nano)
    
    def _money_value_to_float(self, money_value) -> float:
        """Конвертация MoneyValue в float"""
        if money_value is None:
            return 0.0
        # Если уже число - вернуть как есть
        if isinstance(money_value, (int, float)):
            return float(money_value)
        # Если MoneyValue объект
        if hasattr(money_value, 'units') and hasattr(money_value, 'nano'):
            return money_value.units + money_value.nano / 1_000_000_000
        return 0.0
    
    def get_available_tickers(self) -> List[str]:
        """
        Получение списка доступных для торговли тикеров
        
        Returns:
            Список тикеров
        """
        return list(self.instruments_cache.keys())
    
    def is_ticker_available(self, ticker: str) -> bool:
        """
        Проверка доступности тикера для торговли
        
        Args:
            ticker: Тикер инструмента
            
        Returns:
            True если тикер доступен для торговли
        """
        return ticker in self.instruments_cache
    
    def get_status(self) -> Dict:
        """
        Получение статуса брокера
        
        Returns:
            Словарь со статусом
        """
        return {
            'broker': 'T-Bank Invest API',
            'mode': 'sandbox' if self.sandbox else 'production',
            'account_id': self.account_id,
            'instruments_loaded': len(self.instruments_cache),
            'current_positions': len(self.positions),
            'active_orders': len([o for o in self.orders.values() if o.get('status') == 'placed']),
        }


