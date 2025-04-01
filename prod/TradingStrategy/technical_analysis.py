import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
from decimal import Decimal
from dataclasses import dataclass

@dataclass
class TechnicalIndicators:
    """Technical indicators for trading analysis."""
    rsi: float
    macd: float
    macd_signal: float
    macd_hist: float
    sma_20: float
    sma_50: float
    ema_9: float
    bb_upper: float
    bb_middle: float
    bb_lower: float

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate Relative Strength Index (RSI)."""
    if len(prices) < period + 1:
        return 50.0  # Default neutral value if not enough data
    
    # Calculate price changes
    deltas = np.diff(prices)
    
    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Calculate average gains and losses
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi)

def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
    """Calculate MACD (Moving Average Convergence Divergence)."""
    if len(prices) < slow + signal:
        return 0.0, 0.0, 0.0
    
    # Calculate EMAs
    ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean()
    ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean()
    
    # Calculate MACD line
    macd_line = ema_fast - ema_slow
    
    # Calculate signal line
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    return float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), float(histogram.iloc[-1])

def calculate_sma(prices: List[float], period: int) -> float:
    """Calculate Simple Moving Average (SMA)."""
    if len(prices) < period:
        return float(np.mean(prices))  # Return mean of available data if not enough points
    
    return float(np.mean(prices[-period:]))

def calculate_ema(prices: List[float], period: int) -> float:
    """Calculate Exponential Moving Average (EMA)."""
    if len(prices) < period:
        return float(np.mean(prices))  # Return mean of available data if not enough points
    
    return float(pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1])

def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
    """Calculate Bollinger Bands."""
    if len(prices) < period:
        sma = float(np.mean(prices))
        std = float(np.std(prices))
        return sma + (std_dev * std), sma, sma - (std_dev * std)
    
    sma = calculate_sma(prices, period)
    std = float(np.std(prices[-period:]))
    
    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)
    
    return upper_band, sma, lower_band

def calculate_indicators(prices: List[float]) -> TechnicalIndicators:
    """Calculate all technical indicators."""
    return TechnicalIndicators(
        rsi=calculate_rsi(prices),
        macd=calculate_macd(prices)[0],
        macd_signal=calculate_macd(prices)[1],
        macd_hist=calculate_macd(prices)[2],
        sma_20=calculate_sma(prices, 20),
        sma_50=calculate_sma(prices, 50),
        ema_9=calculate_ema(prices, 9),
        bb_upper=calculate_bollinger_bands(prices)[0],
        bb_middle=calculate_bollinger_bands(prices)[1],
        bb_lower=calculate_bollinger_bands(prices)[2]
    )

def analyze_trend(indicators: TechnicalIndicators) -> str:
    """Analyze the overall trend based on technical indicators."""
    trend_signals = []
    
    # Moving average trend
    if indicators.sma_20 > indicators.sma_50:
        trend_signals.append("UPTREND")
    elif indicators.sma_20 < indicators.sma_50:
        trend_signals.append("DOWNTREND")
    
    # MACD trend
    if indicators.macd > indicators.macd_signal:
        trend_signals.append("MACD_BULLISH")
    elif indicators.macd < indicators.macd_signal:
        trend_signals.append("MACD_BEARISH")
    
    # RSI trend
    if indicators.rsi > 70:
        trend_signals.append("RSI_OVERBOUGHT")
    elif indicators.rsi < 30:
        trend_signals.append("RSI_OVERSOLD")
    
    # Bollinger Bands trend
    if indicators.bb_upper > indicators.bb_middle > indicators.bb_lower:
        trend_signals.append("BB_EXPANDING")
    elif indicators.bb_upper < indicators.bb_middle < indicators.bb_lower:
        trend_signals.append("BB_CONTRACTING")
    
    return " | ".join(trend_signals)

def generate_trading_signals(
    current_price: float,
    indicators: TechnicalIndicators,
    position: Optional[str] = None
) -> Tuple[str, float, float]:
    """
    Generate trading signals based on technical analysis.
    
    Args:
        current_price: Current price of the asset
        indicators: Technical indicators
        position: Current position ("LONG", "SHORT", or None)
    
    Returns:
        Tuple[str, float, float]: (Action, Stop Loss, Take Profit)
    """
    # Initialize default values
    action = "HOLD"
    stop_loss = current_price * 0.98  # 2% below current price
    take_profit = current_price * 1.04  # 4% above current price
    
    # RSI conditions
    if indicators.rsi < 30 and position != "LONG":
        action = "BUY"
        stop_loss = current_price * 0.97  # 3% below entry
        take_profit = current_price * 1.06  # 6% above entry
    elif indicators.rsi > 70 and position != "SHORT":
        action = "SELL"
        stop_loss = current_price * 1.03  # 3% above entry
        take_profit = current_price * 0.94  # 6% below entry
    
    # MACD conditions
    if indicators.macd > indicators.macd_signal and indicators.macd_hist > 0:
        if position != "LONG":
            action = "BUY"
            stop_loss = current_price * 0.97
            take_profit = current_price * 1.06
    elif indicators.macd < indicators.macd_signal and indicators.macd_hist < 0:
        if position != "SHORT":
            action = "SELL"
            stop_loss = current_price * 1.03
            take_profit = current_price * 0.94
    
    # Bollinger Bands conditions
    if current_price < indicators.bb_lower and position != "LONG":
        action = "BUY"
        stop_loss = current_price * 0.97
        take_profit = indicators.bb_middle
    elif current_price > indicators.bb_upper and position != "SHORT":
        action = "SELL"
        stop_loss = current_price * 1.03
        take_profit = indicators.bb_middle
    
    # Moving average conditions
    if current_price > indicators.sma_20 > indicators.sma_50 and position != "LONG":
        action = "BUY"
        stop_loss = indicators.sma_50
        take_profit = current_price * 1.06
    elif current_price < indicators.sma_20 < indicators.sma_50 and position != "SHORT":
        action = "SELL"
        stop_loss = indicators.sma_50
        take_profit = current_price * 0.94
    
    return action, stop_loss, take_profit 