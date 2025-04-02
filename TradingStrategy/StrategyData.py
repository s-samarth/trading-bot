from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field

from TradingStrategy.Constants import (
    TradingSymbol,
    BaseExchange,
    BaseTransactionType,
    TradeStatus,
    BaseOrderStatus,
    Broker,
)


class BaseStrategyInput(BaseModel):
    """
    This class is used to define the base data structure for a trading strategy.
    """

    trading_symbol: TradingSymbol = Field(
        ..., description="The trading symbol for the stock."
    )
    exchange: BaseExchange = Field(
        default=BaseExchange.NSE, description="The exchange where the stock is traded."
    )


class BaseStrategyOutput(BaseModel):
    """
    This class is used to define the output data structure for a trading strategy.
    """

    trading_symbol: TradingSymbol = Field(
        ..., description="The trading symbol for the stock."
    )
    exchange: BaseExchange = Field(
        default=BaseExchange.NSE, description="The exchange where the stock is traded."
    )
    trade_status: TradeStatus = Field(
        ..., description="The status of the trade (PROFIT/LOSS/HOLD/NOT_TRIGGERED)."
    )
    broker: Broker = Field(..., description="The broker used for the trade.")
    order_status: Optional[BaseOrderStatus] = Field(
        ..., description="The status of the order (OPEN/CLOSED/etc)."
    )
    transaction_type: Optional[BaseTransactionType] = Field(
        ..., description="The type of transaction (BUY/SELL)."
    )
    transaction_price: Optional[Decimal] = Field(
        ..., description="The price at which the transaction was executed."
    )
    order_id: Optional[str] = Field(
        None, description="The ID of the order placed for the trade."
    )
    information: Optional[str] = Field(
        None, description="Additional information about the trade."
    )


class BaseStrategyParams(BaseModel):
    """
    This class is used to define the configuration for a trading strategy.
    """

    target_percent: Decimal = Field(..., description="Target percentage for profit.")
    stop_loss_percent: Decimal = Field(
        ..., description="Stop loss percentage for loss protection."
    )
    tolerance_percent: Decimal = Field(
        default=0.1,
        description="Tolerance level at which to place orders. This is the percentage of the buy/sell price.",
    )


class BaseStrategyTradeSignal(BaseModel):
    """
    This class is used to define the trading signal for a strategy.
    """

    transaction_type: BaseTransactionType = Field(
        ..., description="The type of transaction (BUY/SELL)."
    )
    price: Decimal = Field(..., description="The price at which to execute the trade.")
    trade_status: TradeStatus = Field(
        ..., description="The status of the trade (PROFIT/LOSS/HOLD/NOT_TRIGGERED)."
    )
