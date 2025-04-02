import os
import sys
import json
from decimal import Decimal

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from pydantic import Field

from TradingStrategy.StrategyData import (
    BaseStrategyInput,
    BaseStrategyParams,
    BaseStrategyTradeSignal,
    BaseStrategyOutput,
)
from TradingStrategy.Constants import (
    TradingSymbol,
    BaseExchange,
    TradeStatus,
    BaseTransactionType,
    Broker,
    BaseOrderStatus,
)
from API.Upstox.TradeExecutor import OrderAPIv3 as OrderAPI
from TradingStrategy.Template import StrategyTemplate


class MockStrategyParams(BaseStrategyParams):
    """
    Parameters for the mock trading strategy.
    """

    all_time_high: Decimal = Field(
        default=1000.5, description="The all-time high price of the stock."
    )
    allowed_strategy_capital: Decimal = Field(
        default=1_00_000 * 0.05,
        description="The capital allowed for trading using this strategy.",
    )


class MockStrategy(StrategyTemplate):
    """
    A mock trading strategy for demonstration purposes.
    Strategy: If LTP of the stock is less 80% of the all time high, buy the stock.
    Once Bought, the target price of selling is 4% above the buy price.
    The stop loss is set at 2% below the buy price.
    The quantity is of the stock would be fixed to max 5% of the total alloted capital.
    For Buy we place a limit order at the buy price when LTP is less than the buy price or
    only 0.1% above the buy price.
    For Sell we place a limit order at the sell price when LTP is greater than the sell price or
    only 0.1% below the sell price in case of trigger price being hit.
    Once the order is placed, we will not place any more orders.
    We will log the results of the strategy in a file in root directory/TradingResults
    in the folder either Real or Sandbox depending on the mode of trading.
    The results will be logged only when we finally sell the stock.
    Incase of 2 Consecutive losses, we will stop the strategy for some time(variable)
    and then start again.
    The file name will be the Results_TradingSymbol.json
    """

    def __init__(
        self,
        strategy_input: BaseStrategyInput,
        strategy_params: MockStrategyParams,
        is_sandbox: bool = True,
        broker: Broker = Broker.UPSTOX,
    ):
        super().__init__(strategy_input, strategy_params, is_sandbox, broker)

    def strategy_name(self) -> str:
        """
        Returns the name of the strategy.
        """
        return "MockStrategy"

    def get_buy_price(self):
        """
        Returns the buy price for the strategy.
        """
        return self.strategy_params.all_time_high * Decimal("0.8")

    def get_buy_quantity(self, buy_price):
        """
        Returns the quantity to buy for the strategy.
        """
        return int(self.strategy_params.allowed_strategy_capital / (buy_price))


if __name__ == "__main__":
    # Example usage of the MockStrategy class
    strategy_input = BaseStrategyInput(trading_symbol=TradingSymbol("HDFCBANK"))
    strategy_params = MockStrategyParams(
        target_percent=Decimal("0.04"),
        stop_loss_percent=Decimal("0.02"),
        all_time_high=Decimal("1000.5"),
        allowed_strategy_capital=Decimal("5000.0"),
    )
    strategy = MockStrategy(
        strategy_input=strategy_input,
        strategy_params=strategy_params,
        is_sandbox=True,
        broker=Broker.UPSTOX,
    )
    print(f"Strategy Name: {strategy.strategy_name()}")
    print(f"Buy Price: {strategy.get_buy_price()}")
    print(f"Buy Quantity: {strategy.get_buy_quantity(strategy.get_buy_price())}")
