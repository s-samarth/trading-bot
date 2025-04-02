from typing import List, Dict, Optional
from decimal import Decimal
import logging
from dataclasses import dataclass
from datetime import datetime

from TradingStrategy.Constants import TradingSymbol, BaseExchange
from TradingStrategy.StrategyData import TradingStrategyData
from TradingStrategy.strategies import (
    StrategyConfig,
    run_strategy,
    PortfolioConfig,
    VolumeConfig,
)
from TradingStrategy.technical_analysis import TechnicalIndicators

logger = logging.getLogger(__name__)


@dataclass
class StockPosition:
    """Represents a position in a stock."""

    symbol: TradingSymbol
    quantity: int
    average_price: Decimal
    current_price: Decimal
    position_type: str  # "LONG" or "SHORT"
    entry_time: datetime
    stop_loss: Decimal
    take_profit: Decimal
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")


@dataclass
class StockConfig:
    """Configuration for a stock in the portfolio."""

    symbol: TradingSymbol
    exchange: BaseExchange
    base_quantity: int
    min_quantity: int
    max_quantity: int
    stop_loss_pct: float = 0.02  # 2% stop loss
    take_profit_pct: float = 0.04  # 4% take profit
    max_position_size: float = 0.1  # 10% of portfolio
    risk_per_trade: float = 0.02  # 2% risk per trade


class PortfolioManager:
    """Manages a portfolio of stocks with automated trading decisions."""

    def __init__(
        self,
        total_budget: Decimal,
        stock_configs: List[StockConfig],
        update_interval: int = 60,  # seconds
    ):
        """
        Initialize the portfolio manager.

        Args:
            total_budget: Total available capital
            stock_configs: List of stock configurations
            update_interval: Time between portfolio updates in seconds
        """
        self.total_budget = total_budget
        self.stock_configs = {config.symbol: config for config in stock_configs}
        self.update_interval = update_interval

        # Initialize portfolio configuration
        self.portfolio_config = PortfolioConfig(
            total_budget=total_budget,
            max_position_size=0.1,  # Default 10% per position
            risk_per_trade=0.02,  # Default 2% risk per trade
            current_positions={},
        )

        # Initialize positions dictionary
        self.positions: Dict[TradingSymbol, StockPosition] = {}

        # Initialize price history for each stock
        self.price_history: Dict[TradingSymbol, List[float]] = {
            symbol: [] for symbol in self.stock_configs.keys()
        }

        logger.info(f"Initialized portfolio manager with budget: ₹{total_budget}")
        logger.info(
            f"Tracking {len(stock_configs)} stocks: {', '.join(str(s) for s in stock_configs)}"
        )

    def update_price(self, symbol: TradingSymbol, price: Decimal) -> None:
        """Update the current price and price history for a stock."""
        if symbol not in self.stock_configs:
            logger.warning(f"Received price update for unknown symbol: {symbol}")
            return

        # Update price history
        self.price_history[symbol].append(float(price))
        if len(self.price_history[symbol]) > 50:  # Keep last 50 price points
            self.price_history[symbol] = self.price_history[symbol][-50:]

        # Update position if exists
        if symbol in self.positions:
            position = self.positions[symbol]
            position.current_price = price
            position.unrealized_pnl = self._calculate_pnl(position)

    def _calculate_pnl(self, position: StockPosition) -> Decimal:
        """Calculate unrealized P&L for a position."""
        if position.position_type == "LONG":
            return (position.current_price - position.average_price) * position.quantity
        else:  # SHORT
            return (position.average_price - position.current_price) * position.quantity

    def _should_exit_position(self, position: StockPosition) -> bool:
        """Determine if a position should be exited based on stop loss or take profit."""
        if position.position_type == "LONG":
            # Exit if price hits stop loss or take profit
            return (
                position.current_price <= position.stop_loss
                or position.current_price >= position.take_profit
            )
        else:  # SHORT
            # Exit if price hits stop loss or take profit
            return (
                position.current_price >= position.stop_loss
                or position.current_price <= position.take_profit
            )

    def _create_strategy_config(self, symbol: TradingSymbol) -> StrategyConfig:
        """Create a strategy configuration for a stock."""
        stock_config = self.stock_configs[symbol]
        return StrategyConfig(
            trading_symbol=symbol,
            exchange=stock_config.exchange,
            quantity=stock_config.base_quantity,
            price_history=self.price_history[symbol],
            volume_config=VolumeConfig(
                base_quantity=stock_config.base_quantity,
                max_quantity=stock_config.max_quantity,
                min_quantity=stock_config.min_quantity,
            ),
            portfolio_config=self.portfolio_config,
        )

    def analyze_portfolio(self) -> List[TradingStrategyData]:
        """
        Analyze the entire portfolio and generate trading signals.

        Returns:
            List[TradingStrategyData]: List of trading decisions
        """
        trading_decisions = []

        # First, check existing positions for exits
        for symbol, position in list(self.positions.items()):
            if self._should_exit_position(position):
                # Create exit signal
                trade_details = TradingStrategyData(
                    trading_symbol=symbol,
                    exchange=self.stock_configs[symbol].exchange,
                    ltp=position.current_price,
                    quantity=position.quantity,
                    transaction_type=(
                        BaseTransactionType.SELL
                        if position.position_type == "LONG"
                        else BaseTransactionType.BUY
                    ),
                )
                trading_decisions.append(trade_details)

                # Update portfolio
                self.portfolio_config.current_positions.pop(symbol, None)
                self.positions.pop(symbol)
                logger.info(f"Exit signal generated for {symbol}: {trade_details}")

        # Then, analyze each stock for new entries
        for symbol, config in self.stock_configs.items():
            # Skip if we already have a position
            if symbol in self.positions:
                continue

            # Skip if we don't have enough price history
            if len(self.price_history[symbol]) < 50:
                continue

            # Create strategy config and analyze
            strategy_config = self._create_strategy_config(symbol)
            trade_details = technical_analysis_strategy(
                strategy_config, Decimal(str(self.price_history[symbol][-1]))
            )

            # If we have a valid trading signal
            if trade_details.transaction_type:
                # Calculate stop loss and take profit
                current_price = Decimal(str(self.price_history[symbol][-1]))
                stop_loss = current_price * Decimal(str(1 - config.stop_loss_pct))
                take_profit = current_price * Decimal(str(1 + config.take_profit_pct))

                # Create new position
                new_position = StockPosition(
                    symbol=symbol,
                    quantity=trade_details.quantity,
                    average_price=current_price,
                    current_price=current_price,
                    position_type=(
                        "LONG"
                        if trade_details.transaction_type == BaseTransactionType.BUY
                        else "SHORT"
                    ),
                    entry_time=datetime.now(),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                )

                # Update portfolio
                self.positions[symbol] = new_position
                self.portfolio_config.current_positions[symbol] = (
                    current_price * trade_details.quantity
                )

                trading_decisions.append(trade_details)
                logger.info(f"Entry signal generated for {symbol}: {trade_details}")

        return trading_decisions

    def get_portfolio_summary(self) -> Dict:
        """Get a summary of the current portfolio state."""
        total_value = self.total_budget
        total_pnl = Decimal("0")
        positions_summary = []

        for symbol, position in self.positions.items():
            position_value = position.current_price * position.quantity
            total_value += position_value
            total_pnl += position.unrealized_pnl

            positions_summary.append(
                {
                    "symbol": str(symbol),
                    "quantity": position.quantity,
                    "average_price": float(position.average_price),
                    "current_price": float(position.current_price),
                    "position_type": position.position_type,
                    "unrealized_pnl": float(position.unrealized_pnl),
                    "realized_pnl": float(position.realized_pnl),
                    "stop_loss": float(position.stop_loss),
                    "take_profit": float(position.take_profit),
                }
            )

        return {
            "total_budget": float(self.total_budget),
            "total_value": float(total_value),
            "total_pnl": float(total_pnl),
            "positions": positions_summary,
            "available_budget": float(self.portfolio_config.get_available_budget()),
        }
