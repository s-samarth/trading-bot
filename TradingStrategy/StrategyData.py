from typing import Optional, Any
from decimal import Decimal
from pydantic import BaseModel, Field

from TradingStrategy.Constants import (
    TradingSymbol,
    BaseExchange,
    BaseTransactionType,
    TradeStatus,
    BaseOrderStatus,
    Broker,
    BaseProductType,
    ExecutionStatus,
    BaseSegment,
    BaseOrderType,
    TradeAction,
)


class BaseStrategyInput(BaseModel):
    """
    This class is used to define the base data structure for a trading strategy.
    """

    trading_symbol: TradingSymbol = Field(
        ..., description="The trading symbol for the stock."
    )
    ltp: Decimal = Field(..., description="The last traded price of the stock.")
    exchange: BaseExchange = Field(
        default=BaseExchange.NSE, description="The exchange where the stock is traded."
    )
    product_type: BaseProductType = Field(
        default=BaseProductType.DELIVERY,
        description="The type of product (INTRADAY/DELIVERY/etc).",
    )
    segment: BaseSegment = Field(
        default=BaseSegment.EQUITY,
        description="The segment of the market (EQUITY/COMMODITY/etc).",
    )
    order_type: BaseOrderType = Field(
        default=BaseOrderType.LIMIT, description="The type of order (MARKET/LIMIT/etc)."
    )
    broker: Broker = Field(
        default=Broker.UPSTOX, description="The broker used for the trade."
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
    trade_action: TradeAction = Field(
        ..., description="The action taken for the trade (BUY/SELL/HOLD/NO_ACTION)."
    )
    quantity: Optional[int] = Field(..., description="The quantity of stocks traded.")
    broker: Broker = Field(..., description="The broker used for the trade.")
    execution_status: Optional[ExecutionStatus] = Field(
        None, description="The status of the execution (SUCCESS/FAILURE/etc)."
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
