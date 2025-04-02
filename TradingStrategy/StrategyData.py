from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from TradingStrategy.Constants import TradingSymbol, BaseExchange, BaseTransactionType



class TradingStrategyData(BaseModel):
    """
    This class is used to define the data structure for a trading strategy.
    """

    trading_symbol: TradingSymbol = Field(
        ..., description="The trading symbol for the stock."
    )
    exchange: BaseExchange = Field(
        default=BaseExchange.NSE, description="The exchange where the stock is traded."
    )
    ltp: Decimal = Field(..., description="The last traded price of the stock.")
    buy_price: Decimal = Field(..., description="The price at which to buy the stock.")
    sell_price: Decimal = Field(
        ..., description="The price at which to sell the stock."
    )
    quantity: int = Field(..., description="The number of shares to trade.")
    transaction_type: Optional[BaseTransactionType] = Field(
        default=None, description="The type of transaction (BUY/SELL)."
    )

    @field_validator("ltp", "buy_price", "sell_price")
    @classmethod
    def validate_prices(cls, v):
        if v <= 0:
            raise ValueError("Prices must be positive numbers")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be a positive number")
        return v

    @field_validator("sell_price")
    @classmethod
    def validate_sell_price(cls, v, info):
        if "buy_price" in info.data and v <= info.data["buy_price"]:
            raise ValueError("Sell price must be greater than buy price")
        return v
