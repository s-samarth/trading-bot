from typing import Optional

from pydantic import BaseModel, Field

from TradingStrategy.Constants import TradingSymbol, BaseExchange, BaseTransactionType


class TradingStrategyData(BaseModel):
    """
    This class is used to define the data structure for a trading strategy.
    """

    trading_symbol: TradingSymbol = Field(
        ..., description="The trading symbol for the stock."
    )
    exchange: str = Field(
        default=BaseExchange.NSE, description="The exchange where the stock is traded."
    )
    ltp: float = Field(..., description="The last traded price of the stock.")
    buy_price: float = Field(..., description="The price at which to buy the stock.")
    sell_price: float = Field(..., description="The price at which to sell the stock.")
    quantity: int = Field(..., description="The number of shares to trade.")
    transaction_type: Optional[BaseTransactionType] = Field(
        ..., description="The type of transaction (BUY/SELL)."
    )  # Optional
