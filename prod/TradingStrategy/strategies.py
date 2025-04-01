from typing import List, Optional, Tuple, Dict
from decimal import Decimal
import logging
from dataclasses import dataclass

from TradingStrategy.Constants import TradingSymbol, BaseExchange, BaseTransactionType
from TradingStrategy.StrategyData import TradingStrategyData
from TradingStrategy.technical_analysis import (
    calculate_indicators,
    analyze_trend,
    generate_trading_signals,
    TechnicalIndicators
)

logger = logging.getLogger(__name__)

@dataclass
class PortfolioConfig:
    """Configuration for portfolio management."""
    total_budget: Decimal  # Total available capital
    max_position_size: float = 0.1  # Maximum position size as fraction of total budget (default: 10%)
    risk_per_trade: float = 0.02   # Maximum risk per trade as fraction of total budget (default: 2%)
    current_positions: Dict[str, Decimal] = None  # Current positions and their values

    def __post_init__(self):
        if self.current_positions is None:
            self.current_positions = {}

    def get_available_budget(self) -> Decimal:
        """Calculate available budget for new positions."""
        total_invested = sum(self.current_positions.values())
        return self.total_budget - total_invested

    def get_position_size(self, price: Decimal, stop_loss: Decimal) -> int:
        """
        Calculate position size based on risk management rules.
        
        Args:
            price: Current price of the asset
            stop_loss: Stop loss price
            
        Returns:
            int: Number of shares to trade
        """
        # Calculate maximum position value based on budget
        max_position_value = self.total_budget * Decimal(str(self.max_position_size))
        
        # Calculate maximum position value based on risk
        risk_amount = self.total_budget * Decimal(str(self.risk_per_trade))
        price_risk = abs(price - stop_loss)
        max_risk_based_value = risk_amount / price_risk
        
        # Use the smaller of the two limits
        max_value = min(max_position_value, max_risk_based_value)
        
        # Calculate number of shares
        shares = int(max_value / price)
        
        # Ensure at least 1 share
        return max(1, shares)

@dataclass
class VolumeConfig:
    """Configuration for volume control."""
    base_quantity: int  # Base quantity to trade
    max_quantity: int   # Maximum allowed quantity
    min_quantity: int   # Minimum allowed quantity
    volume_multiplier: float = 1.0  # Multiplier based on signal strength

@dataclass
class StrategyConfig:
    """Configuration for the trading strategy."""
    trading_symbol: TradingSymbol
    exchange: BaseExchange
    quantity: int
    position: Optional[str] = None
    price_history: List[float] = None
    min_price_history: int = 50  # Minimum number of price points needed for analysis
    # Simple strategy parameters
    buy_price: Optional[Decimal] = None
    sell_price: Optional[Decimal] = None
    strategy_type: str = "technical"  # "technical" or "simple"
    # Volume control
    volume_config: Optional[VolumeConfig] = None
    # Portfolio management
    portfolio_config: Optional[PortfolioConfig] = None

    def __post_init__(self):
        if self.price_history is None:
            self.price_history = []
        if self.volume_config is None:
            self.volume_config = VolumeConfig(
                base_quantity=self.quantity,
                max_quantity=self.quantity * 2,
                min_quantity=1
            )

    def to_strategy_data(self, ltp: Decimal) -> TradingStrategyData:
        """Convert config to TradingStrategyData."""
        return TradingStrategyData(
            trading_symbol=self.trading_symbol,
            exchange=self.exchange,
            ltp=ltp,
            buy_price=Decimal(str(ltp)),  # These will be set by the strategy
            sell_price=Decimal(str(ltp)),
            quantity=self.quantity
        )

def calculate_volume(
    base_quantity: int,
    signal_strength: float,
    volume_config: VolumeConfig,
    portfolio_config: Optional[PortfolioConfig] = None,
    price: Optional[Decimal] = None,
    stop_loss: Optional[Decimal] = None
) -> int:
    """
    Calculate the trading volume based on signal strength and configuration.
    
    Args:
        base_quantity: Base quantity to trade
        signal_strength: Strength of the trading signal (0.0 to 1.0)
        volume_config: Volume configuration parameters
        portfolio_config: Optional portfolio configuration for position sizing
        price: Current price of the asset
        stop_loss: Stop loss price
        
    Returns:
        int: Calculated trading volume
    """
    # Calculate volume based on signal strength
    volume = int(base_quantity * signal_strength * volume_config.volume_multiplier)
    
    # Apply portfolio-based position sizing if configured
    if portfolio_config and price and stop_loss:
        portfolio_based_volume = portfolio_config.get_position_size(price, stop_loss)
        volume = min(volume, portfolio_based_volume)
    
    # Ensure volume is within limits
    volume = max(volume_config.min_quantity, min(volume, volume_config.max_quantity))
    
    return volume

def simple_strategy(
    config: StrategyConfig,
    ltp: Decimal,
) -> TradingStrategyData:
    """
    A simple trading strategy that buys if price is below buy_price
    and sells if price is above sell_price.
    
    Args:
        config: Strategy configuration including buy/sell prices
        ltp: The last traded price of the stock
        
    Returns:
        TradingStrategyData: The trade details containing transaction type and other information
    """
    # Convert config to strategy data
    trade_details = config.to_strategy_data(ltp)
    
    # Validate prices
    if not config.buy_price or not config.sell_price:
        logger.error("Buy price and sell price must be set for simple strategy")
        return trade_details
    
    if config.buy_price >= config.sell_price:
        logger.error("Buy price must be less than sell price")
        return trade_details
    
    # Calculate signal strength based on price distance from thresholds
    price_range = config.sell_price - config.buy_price
    if ltp < config.buy_price:
        signal_strength = min(1.0, (config.buy_price - ltp) / price_range)
        trade_details.transaction_type = BaseTransactionType.BUY
        trade_details.buy_price = config.buy_price
        trade_details.sell_price = config.sell_price
        config.position = "LONG"
        logger.info(f"BUY signal triggered: LTP {ltp} < Buy Price {config.buy_price}")
    elif ltp > config.sell_price:
        signal_strength = min(1.0, (ltp - config.sell_price) / price_range)
        trade_details.transaction_type = BaseTransactionType.SELL
        trade_details.buy_price = config.buy_price
        trade_details.sell_price = config.sell_price
        config.position = "SHORT"
        logger.info(f"SELL signal triggered: LTP {ltp} > Sell Price {config.sell_price}")
    else:
        signal_strength = 0.0
        logger.info(f"No trade signal: LTP {ltp} within range [{config.buy_price}, {config.sell_price}]")
        return trade_details
    
    # Calculate volume based on signal strength and portfolio constraints
    trade_details.quantity = calculate_volume(
        config.volume_config.base_quantity,
        signal_strength,
        config.volume_config,
        config.portfolio_config,
        ltp,
        config.buy_price if trade_details.transaction_type == BaseTransactionType.BUY else config.sell_price
    )
    
    logger.info(f"Signal strength: {signal_strength:.2f}, Trading volume: {trade_details.quantity}")
    return trade_details

def technical_analysis_strategy(
    config: StrategyConfig,
    ltp: Decimal,
) -> TradingStrategyData:
    """
    A sophisticated trading strategy that uses multiple technical indicators
    to make trading decisions.
    
    The strategy combines:
    1. RSI (Relative Strength Index) for overbought/oversold conditions
    2. MACD (Moving Average Convergence Divergence) for trend following
    3. Bollinger Bands for volatility and price levels
    4. Moving Averages (SMA 20 and 50) for trend confirmation
    
    Args:
        config: Strategy configuration including price history
        ltp: The last traded price of the stock
        
    Returns:
        TradingStrategyData: The trade details containing transaction type and other information
    """
    # Convert config to strategy data
    trade_details = config.to_strategy_data(ltp)
    
    # Add current price to history
    config.price_history.append(float(ltp))
    
    # Keep only the last min_price_history points
    if len(config.price_history) > config.min_price_history:
        config.price_history = config.price_history[-config.min_price_history:]
    
    # If we don't have enough price history, return HOLD
    if len(config.price_history) < config.min_price_history:
        logger.info(f"Insufficient price history. Need {config.min_price_history} points, got {len(config.price_history)}")
        return trade_details
    
    # Calculate technical indicators
    indicators = calculate_indicators(config.price_history)
    
    # Analyze overall trend
    trend = analyze_trend(indicators)
    logger.info(f"Current trend analysis: {trend}")
    
    # Generate trading signals
    action, stop_loss, take_profit = generate_trading_signals(
        current_price=float(ltp),
        indicators=indicators,
        position=config.position
    )
    
    # Log the analysis
    logger.info(f"Technical Analysis Results:")
    logger.info(f"RSI: {indicators.rsi:.2f}")
    logger.info(f"MACD: {indicators.macd:.2f} | Signal: {indicators.macd_signal:.2f}")
    logger.info(f"SMA 20: {indicators.sma_20:.2f} | SMA 50: {indicators.sma_50:.2f}")
    logger.info(f"BB Upper: {indicators.bb_upper:.2f} | BB Lower: {indicators.bb_lower:.2f}")
    logger.info(f"Action: {action} | Stop Loss: {stop_loss:.2f} | Take Profit: {take_profit:.2f}")
    
    # Calculate signal strength based on multiple factors
    signal_strength = 0.0
    if action != "HOLD":
        # RSI contribution (0.3)
        rsi_strength = 0.0
        if action == "BUY" and indicators.rsi < 30:
            rsi_strength = (30 - indicators.rsi) / 30
        elif action == "SELL" and indicators.rsi > 70:
            rsi_strength = (indicators.rsi - 70) / 30
        signal_strength += rsi_strength * 0.3
        
        # MACD contribution (0.3)
        macd_strength = abs(indicators.macd_hist) / max(abs(indicators.macd), 1)
        signal_strength += macd_strength * 0.3
        
        # Bollinger Bands contribution (0.2)
        bb_strength = 0.0
        if action == "BUY" and float(ltp) < indicators.bb_lower:
            bb_strength = (indicators.bb_lower - float(ltp)) / (indicators.bb_middle - indicators.bb_lower)
        elif action == "SELL" and float(ltp) > indicators.bb_upper:
            bb_strength = (float(ltp) - indicators.bb_upper) / (indicators.bb_upper - indicators.bb_middle)
        signal_strength += bb_strength * 0.2
        
        # Moving Averages contribution (0.2)
        ma_strength = 0.0
        if action == "BUY" and float(ltp) > indicators.sma_20 > indicators.sma_50:
            ma_strength = (float(ltp) - indicators.sma_20) / (indicators.sma_20 - indicators.sma_50)
        elif action == "SELL" and float(ltp) < indicators.sma_20 < indicators.sma_50:
            ma_strength = (indicators.sma_20 - float(ltp)) / (indicators.sma_50 - indicators.sma_20)
        signal_strength += ma_strength * 0.2
    
    # Set the action and calculate volume
    if action == "BUY":
        trade_details.transaction_type = BaseTransactionType.BUY
        trade_details.buy_price = Decimal(str(ltp))
        trade_details.sell_price = Decimal(str(take_profit))
        config.position = "LONG"
    elif action == "SELL":
        trade_details.transaction_type = BaseTransactionType.SELL
        trade_details.buy_price = Decimal(str(stop_loss))
        trade_details.sell_price = Decimal(str(ltp))
        config.position = "SHORT"
    
    # Calculate volume based on signal strength and portfolio constraints
    trade_details.quantity = calculate_volume(
        config.volume_config.base_quantity,
        signal_strength,
        config.volume_config,
        config.portfolio_config,
        ltp,
        Decimal(str(stop_loss))
    )
    
    logger.info(f"Signal strength: {signal_strength:.2f}, Trading volume: {trade_details.quantity}")
    return trade_details

def run_strategy(
    config: StrategyConfig,
    ltp: Decimal,
) -> TradingStrategyData:
    """
    Run the selected trading strategy.
    
    Args:
        config: Strategy configuration
        ltp: The last traded price of the stock
        
    Returns:
        TradingStrategyData: The trade details containing transaction type and other information
    """
    if config.strategy_type == "simple":
        return simple_strategy(config, ltp)
    else:
        return technical_analysis_strategy(config, ltp) 