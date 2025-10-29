"""
Извлечение портфельных признаков для нейросети
Включает данные о текущем портфеле, P&L, рисках и позициях
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class PortfolioFeatures:
    """Структура портфельных признаков"""
    # Общие метрики портфеля
    total_value: float
    cash_balance: float
    invested_value: float
    total_pnl: float
    total_pnl_percent: float
    realized_pnl: float
    unrealized_pnl: float
    
    # Рисковые метрики
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    var_95: float  # Value at Risk 95%
    
    # Концентрация портфеля
    position_count: int
    max_position_weight: float
    concentration_risk: float
    
    # Позиционные признаки
    winning_positions: int
    losing_positions: int
    avg_position_pnl: float
    avg_position_pnl_percent: float
    
    # Временные признаки портфеля
    days_since_last_trade: int
    portfolio_age_days: int
    recent_trades_count: int
    
    # Рыночные признаки относительно портфеля
    portfolio_beta: float
    correlation_with_market: float
    
    # Признаки по символам
    symbol_features: Dict[str, Dict[str, float]]


class PortfolioFeatureExtractor:
    """
    Извлекатель портфельных признаков для нейросети
    
    Включает:
    - Общие метрики портфеля (P&L, риски, концентрация)
    - Позиционные признаки (прибыльность, вес позиций)
    - Временные признаки (возраст портфеля, активность торгов)
    - Рыночные признаки (бета, корреляция)
    - Признаки по отдельным символам
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализация извлекателя портфельных признаков
        
        Args:
            config: Конфигурация извлечения признаков
        """
        self.config = config or {}
        self.lookback_days = self.config.get('lookback_days', 30)
        self.risk_free_rate = self.config.get('risk_free_rate', 0.05)  # 5% годовых
        self.var_confidence = self.config.get('var_confidence', 0.95)
        
        logger.info("Инициализирован извлекатель портфельных признаков")
    
    def extract_portfolio_features(
        self, 
        portfolio_manager,
        symbol: str = None
    ) -> PortfolioFeatures:
        """
        Извлечение портфельных признаков
        
        Args:
            portfolio_manager: Менеджер портфеля
            symbol: Конкретный символ для анализа (опционально)
            
        Returns:
            Структура портфельных признаков
        """
        try:
            # Получение базовых метрик портфеля
            portfolio_metrics = portfolio_manager.current_metrics
            if not portfolio_metrics:
                logger.warning("Метрики портфеля недоступны")
                return self._create_empty_features()
            
            # Извлечение общих метрик
            general_metrics = self._extract_general_metrics(portfolio_metrics)
            
            # Извлечение рисковых метрик
            risk_metrics = self._extract_risk_metrics(portfolio_manager)
            
            # Извлечение позиционных признаков
            position_features = self._extract_position_features(portfolio_manager)
            
            # Извлечение временных признаков
            temporal_features = self._extract_temporal_features(portfolio_manager)
            
            # Извлечение рыночных признаков
            market_features = self._extract_market_features(portfolio_manager, symbol)
            
            # Извлечение признаков по символам
            symbol_features = self._extract_symbol_features(portfolio_manager, symbol)
            
            # Объединение всех признаков
            features = PortfolioFeatures(
                **general_metrics,
                **risk_metrics,
                **position_features,
                **temporal_features,
                **market_features,
                symbol_features=symbol_features
            )
            
            logger.debug(f"Извлечено {len(vars(features))} портфельных признаков")
            return features
            
        except Exception as e:
            logger.error(f"Ошибка извлечения портфельных признаков: {e}")
            return self._create_empty_features()
    
    def _extract_general_metrics(self, portfolio_metrics) -> Dict[str, float]:
        """Извлечение общих метрик портфеля"""
        return {
            'total_value': portfolio_metrics.total_value,
            'cash_balance': portfolio_metrics.cash_balance,
            'invested_value': portfolio_metrics.invested_value,
            'total_pnl': portfolio_metrics.total_pnl,
            'total_pnl_percent': portfolio_metrics.total_pnl_percent,
            'realized_pnl': portfolio_metrics.realized_pnl,
            'unrealized_pnl': portfolio_metrics.unrealized_pnl
        }
    
    def _extract_risk_metrics(self, portfolio_manager) -> Dict[str, float]:
        """Извлечение рисковых метрик"""
        try:
            portfolio_metrics = portfolio_manager.current_metrics
            if not portfolio_metrics:
                return {
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'volatility': 0.0,
                    'var_95': 0.0
                }
            
            return {
                'sharpe_ratio': portfolio_metrics.sharpe_ratio,
                'max_drawdown': portfolio_metrics.max_drawdown,
                'volatility': portfolio_metrics.volatility,
                'var_95': self._calculate_var(portfolio_manager)
            }
        except Exception as e:
            logger.error(f"Ошибка извлечения рисковых метрик: {e}")
            return {
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'volatility': 0.0,
                'var_95': 0.0
            }
    
    def _extract_position_features(self, portfolio_manager) -> Dict[str, float]:
        """Извлечение позиционных признаков"""
        try:
            positions = portfolio_manager.positions
            if not positions:
                return {
                    'position_count': 0,
                    'max_position_weight': 0.0,
                    'concentration_risk': 0.0,
                    'winning_positions': 0,
                    'losing_positions': 0,
                    'avg_position_pnl': 0.0,
                    'avg_position_pnl_percent': 0.0
                }
            
            # Подсчет позиций
            position_count = len(positions)
            winning_positions = sum(1 for pos in positions.values() if pos.unrealized_pnl > 0)
            losing_positions = sum(1 for pos in positions.values() if pos.unrealized_pnl < 0)
            
            # Расчет весов позиций
            total_value = sum(pos.market_value for pos in positions.values())
            position_weights = [pos.market_value / total_value for pos in positions.values()] if total_value > 0 else []
            
            # Максимальный вес позиции
            max_position_weight = max(position_weights) if position_weights else 0.0
            
            # Индекс концентрации (сумма квадратов весов)
            concentration_risk = sum(w**2 for w in position_weights)
            
            # Средние P&L
            avg_position_pnl = np.mean([pos.unrealized_pnl for pos in positions.values()])
            avg_position_pnl_percent = np.mean([pos.unrealized_pnl_percent for pos in positions.values()])
            
            return {
                'position_count': position_count,
                'max_position_weight': max_position_weight,
                'concentration_risk': concentration_risk,
                'winning_positions': winning_positions,
                'losing_positions': losing_positions,
                'avg_position_pnl': avg_position_pnl,
                'avg_position_pnl_percent': avg_position_pnl_percent
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения позиционных признаков: {e}")
            return {
                'position_count': 0,
                'max_position_weight': 0.0,
                'concentration_risk': 0.0,
                'winning_positions': 0,
                'losing_positions': 0,
                'avg_position_pnl': 0.0,
                'avg_position_pnl_percent': 0.0
            }
    
    def _extract_temporal_features(self, portfolio_manager) -> Dict[str, int]:
        """Извлечение временных признаков"""
        try:
            from datetime import timezone
            
            # Получаем текущее время с timezone
            now = datetime.now(timezone.utc)
            
            # Возраст портфеля (дни с первой транзакции)
            transactions = portfolio_manager.transactions
            if transactions:
                first_transaction = min(t.timestamp for t in transactions)
                # Приводим к одинаковому типу datetime
                if first_transaction.tzinfo is None:
                    first_transaction = first_transaction.replace(tzinfo=timezone.utc)
                portfolio_age_days = (now - first_transaction).days
            else:
                portfolio_age_days = 0
            
            # Дни с последней транзакции
            if transactions:
                last_transaction = max(t.timestamp for t in transactions)
                # Приводим к одинаковому типу datetime
                if last_transaction.tzinfo is None:
                    last_transaction = last_transaction.replace(tzinfo=timezone.utc)
                days_since_last_trade = (now - last_transaction).days
            else:
                days_since_last_trade = 999  # Большое число если нет транзакций
            
            # Количество недавних транзакций
            recent_cutoff = now - timedelta(days=self.lookback_days)
            recent_trades_count = 0
            for t in transactions:
                # Приводим к одинаковому типу datetime
                t_timestamp = t.timestamp
                if t_timestamp.tzinfo is None:
                    t_timestamp = t_timestamp.replace(tzinfo=timezone.utc)
                if t_timestamp >= recent_cutoff:
                    recent_trades_count += 1
            
            return {
                'days_since_last_trade': days_since_last_trade,
                'portfolio_age_days': portfolio_age_days,
                'recent_trades_count': recent_trades_count
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения временных признаков: {e}")
            return {
                'days_since_last_trade': 999,
                'portfolio_age_days': 0,
                'recent_trades_count': 0
            }
    
    def _extract_market_features(self, portfolio_manager, symbol: str = None) -> Dict[str, float]:
        """Извлечение рыночных признаков"""
        try:
            # Здесь можно добавить расчет беты портфеля и корреляции с рынком
            # Пока возвращаем базовые значения
            return {
                'portfolio_beta': 1.0,  # По умолчанию бета = 1
                'correlation_with_market': 0.5  # Средняя корреляция
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения рыночных признаков: {e}")
            return {
                'portfolio_beta': 1.0,
                'correlation_with_market': 0.5
            }
    
    def _extract_symbol_features(self, portfolio_manager, symbol: str = None) -> Dict[str, Dict[str, float]]:
        """Извлечение признаков по символам"""
        try:
            symbol_features = {}
            positions = portfolio_manager.positions
            
            if symbol and symbol in positions:
                # Признаки для конкретного символа
                position = positions[symbol]
                symbol_features[symbol] = {
                    'position_weight': position.market_value / portfolio_manager.current_metrics.total_value if portfolio_manager.current_metrics.total_value > 0 else 0,
                    'position_pnl': position.unrealized_pnl,
                    'position_pnl_percent': position.unrealized_pnl_percent,
                    'position_duration_days': (datetime.now() - position.last_updated).days,
                    'position_size': abs(position.quantity),
                    'avg_price_vs_current': (position.current_price - position.average_price) / position.average_price if position.average_price > 0 else 0
                }
            else:
                # Признаки для всех символов
                for sym, pos in positions.items():
                    symbol_features[sym] = {
                        'position_weight': pos.market_value / portfolio_manager.current_metrics.total_value if portfolio_manager.current_metrics.total_value > 0 else 0,
                        'position_pnl': pos.unrealized_pnl,
                        'position_pnl_percent': pos.unrealized_pnl_percent,
                        'position_duration_days': (datetime.now() - pos.last_updated).days,
                        'position_size': abs(pos.quantity),
                        'avg_price_vs_current': (pos.current_price - pos.average_price) / pos.average_price if pos.average_price > 0 else 0
                    }
            
            return symbol_features
            
        except Exception as e:
            logger.error(f"Ошибка извлечения признаков по символам: {e}")
            return {}
    
    def _calculate_var(self, portfolio_manager) -> float:
        """Расчет Value at Risk"""
        try:
            # Упрощенный расчет VaR на основе волатильности портфеля
            portfolio_metrics = portfolio_manager.current_metrics
            if not portfolio_metrics:
                return 0.0
            
            # VaR = портфель * z-score * волатильность
            z_score = 1.645  # Для 95% доверительного интервала
            var = portfolio_metrics.total_value * z_score * (portfolio_metrics.volatility / 100)
            
            return var
            
        except Exception as e:
            logger.error(f"Ошибка расчета VaR: {e}")
            return 0.0
    
    def _create_empty_features(self) -> PortfolioFeatures:
        """Создание пустых признаков при ошибке"""
        return PortfolioFeatures(
            total_value=0.0,
            cash_balance=0.0,
            invested_value=0.0,
            total_pnl=0.0,
            total_pnl_percent=0.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            volatility=0.0,
            var_95=0.0,
            position_count=0,
            max_position_weight=0.0,
            concentration_risk=0.0,
            winning_positions=0,
            losing_positions=0,
            avg_position_pnl=0.0,
            avg_position_pnl_percent=0.0,
            days_since_last_trade=999,
            portfolio_age_days=0,
            recent_trades_count=0,
            portfolio_beta=1.0,
            correlation_with_market=0.5,
            symbol_features={}
        )
    
    def features_to_dataframe(self, features: PortfolioFeatures) -> pd.DataFrame:
        """
        Конвертация признаков в DataFrame для нейросети
        
        Args:
            features: Портфельные признаки
            
        Returns:
            DataFrame с признаками
        """
        try:
            # Создание словаря с признаками
            feature_dict = {}
            
            # Общие метрики
            feature_dict.update({
                'portfolio_total_value': features.total_value,
                'portfolio_cash_balance': features.cash_balance,
                'portfolio_invested_value': features.invested_value,
                'portfolio_total_pnl': features.total_pnl,
                'portfolio_total_pnl_percent': features.total_pnl_percent,
                'portfolio_realized_pnl': features.realized_pnl,
                'portfolio_unrealized_pnl': features.unrealized_pnl
            })
            
            # Рисковые метрики
            feature_dict.update({
                'portfolio_sharpe_ratio': features.sharpe_ratio,
                'portfolio_max_drawdown': features.max_drawdown,
                'portfolio_volatility': features.volatility,
                'portfolio_var_95': features.var_95
            })
            
            # Позиционные признаки
            feature_dict.update({
                'portfolio_position_count': features.position_count,
                'portfolio_max_position_weight': features.max_position_weight,
                'portfolio_concentration_risk': features.concentration_risk,
                'portfolio_winning_positions': features.winning_positions,
                'portfolio_losing_positions': features.losing_positions,
                'portfolio_avg_position_pnl': features.avg_position_pnl,
                'portfolio_avg_position_pnl_percent': features.avg_position_pnl_percent
            })
            
            # Временные признаки
            feature_dict.update({
                'portfolio_days_since_last_trade': features.days_since_last_trade,
                'portfolio_age_days': features.portfolio_age_days,
                'portfolio_recent_trades_count': features.recent_trades_count
            })
            
            # Рыночные признаки
            feature_dict.update({
                'portfolio_beta': features.portfolio_beta,
                'portfolio_correlation_with_market': features.correlation_with_market
            })
            
            # Признаки по символам (добавляем только для первого символа или усредненные)
            if features.symbol_features:
                # Берем первый символ или усредняем по всем
                symbol_data = list(features.symbol_features.values())[0] if features.symbol_features else {}
                feature_dict.update({
                    f'portfolio_{key}': value for key, value in symbol_data.items()
                })
            
            # Создание DataFrame
            df = pd.DataFrame([feature_dict])
            
            # Нормализация признаков
            df = self._normalize_portfolio_features(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Ошибка конвертации признаков в DataFrame: {e}")
            return pd.DataFrame()
    
    def _normalize_portfolio_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Нормализация портфельных признаков"""
        try:
            # Список признаков для нормализации
            normalize_columns = [
                'portfolio_total_value', 'portfolio_cash_balance', 'portfolio_invested_value',
                'portfolio_total_pnl', 'portfolio_realized_pnl', 'portfolio_unrealized_pnl',
                'portfolio_avg_position_pnl', 'portfolio_var_95'
            ]
            
            # Z-score нормализация для финансовых значений
            for col in normalize_columns:
                if col in df.columns:
                    # Простая нормализация (можно улучшить)
                    df[f'{col}_norm'] = (df[col] - df[col].mean()) / (df[col].std() + 1e-8)
            
            return df
            
        except Exception as e:
            logger.error(f"Ошибка нормализации портфельных признаков: {e}")
            return df
    
    def get_feature_names(self) -> List[str]:
        """Получение списка названий признаков"""
        return [
            'portfolio_total_value', 'portfolio_cash_balance', 'portfolio_invested_value',
            'portfolio_total_pnl', 'portfolio_total_pnl_percent', 'portfolio_realized_pnl',
            'portfolio_unrealized_pnl', 'portfolio_sharpe_ratio', 'portfolio_max_drawdown',
            'portfolio_volatility', 'portfolio_var_95', 'portfolio_position_count',
            'portfolio_max_position_weight', 'portfolio_concentration_risk',
            'portfolio_winning_positions', 'portfolio_losing_positions',
            'portfolio_avg_position_pnl', 'portfolio_avg_position_pnl_percent',
            'portfolio_days_since_last_trade', 'portfolio_age_days',
            'portfolio_recent_trades_count', 'portfolio_beta',
            'portfolio_correlation_with_market'
        ]
