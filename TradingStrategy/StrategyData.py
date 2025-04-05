from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field

from TradingStrategy.Constants import (
    TradingSymbol,
    BaseExchange,
    BaseTransactionType,
    TradeResult,
    TradeStatus,
    BaseOrderStatus,
    Broker,
    BaseProductType,
    ExecutionStatus,
    BaseSegment,
    BaseOrderType,
    TradeAction,
    TradingMode,
)


class BrokerSecrets(BaseModel):
    """
    This class is used to define the secrets for the broker.
    """

    access_token: str = Field(..., description="The access token for the broker's API.")


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
    # access_token: Optional[str] = Field(
    #     None, description="The access token for the broker's API."
    # )


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
    trade_action: TradeAction = Field(
        ..., description="The action taken for the trade (BUY/SELL/HOLD/NO_ACTION)."
    )
    quantity: Optional[int] = Field(None, description="The quantity of stocks traded.")
    trade_charges: Optional[float] = Field(
        None, description="The charges incurred for executing the trade."
    )
    execution_status: Optional[ExecutionStatus] = Field(
        None, description="The status of the execution (SUCCESS/FAILURE/etc)."
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
    Inherit from this class to create specific strategy parameters.
    Example:
    target_percent: float = Field(
        ..., description="Target percentage for profit."
    )
    stop_loss_percent: float = Field(
        ..., description="Stop loss percentage for loss protection."
    )
    """

    # target_percent: float = Field(..., description="Target percentage for profit.")
    # stop_loss_percent: float = Field(
    #     ..., description="Stop loss percentage for loss protection."
    # )
    tolerance_percent: float = Field(
        default=0.1,
        description="Tolerance level at which to place orders. This is the percentage of the buy/sell price.",
    )


class BaseStrategyManagerState(BaseModel):
    """
    This class is used to define the state of the strategy manager.
    """

    strategy_name: str = Field(
        ..., description="The name of the strategy being managed."
    )
    ltp: float = Field(default=None, description="The last traded price of the stock.")
    timestamp: str = Field(
        None,
        description="Timestamp of the last update to the strategy manager.",
    )
    trade_status: TradeStatus = Field(
        default=TradeStatus.NOT_TRIGGERED,
        description="Status of the trade (NOT_TRIGGERED/HOLDING/EXIT/etc).",
    )
    trading_mode: TradingMode = Field(
        default=TradingMode.BACKTEST,
        description="Mode of trading (BACKTEST/LIVE/SIMULATION).",
    )
    holding_quantity: Optional[int] = Field(
        default=0, description="Quantity of stocks currently held."
    )
    buy_price_executed: Optional[float] = Field(
        None, description="Price at which the stock was bought."
    )
    sell_price_executed: Optional[float] = Field(
        None, description="Price at which the stock was sold."
    )
    stop_loss_at_buy_price: Optional[float] = Field(
        None, description="Stop loss price set at the time of buying."
    )
    target_price_at_buy_price: Optional[float] = Field(
        None, description="Target price set at the time of buying."
    )
    broker: Optional[Broker] = Field(
        default=None, description="The broker used for the trade."
    )
    cooldown_status: bool = Field(
        default=False, description="Indicates if the strategy is in cooldown."
    )
    cooldown_timestamp: Optional[str] = Field(
        None, description="Timestamp when the strategy entered cooldown."
    )
