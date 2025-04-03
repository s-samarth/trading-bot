import os
import sys
import json
from pprint import pprint

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from pydantic import Field

from TradingStrategy.StrategyData import BaseStrategyInput, BaseStrategyParams
from TradingStrategy.Constants import TradingSymbol, TradeStatus
from TradingStrategy.Template import StrategyTemplate


class MockStrategyParams(BaseStrategyParams):
    """
    Parameters for the mock trading strategy.
    """

    all_time_high: float = Field(
        default=1000.5, description="The all-time high price of the stock."
    )
    allowed_strategy_capital: float = Field(
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
        self, strategy_input: BaseStrategyInput, strategy_params: MockStrategyParams
    ):
        super().__init__(strategy_input, strategy_params)

    def get_buy_price(self):
        """
        Returns the buy price for the strategy.
        """
        return self.strategy_params.all_time_high * 0.8

    def get_buy_quantity(self, buy_price):
        """
        Returns the quantity to buy for the strategy.
        """
        return int(self.strategy_params.allowed_strategy_capital / (buy_price))


if __name__ == "__main__":
    # Example usage of the MockStrategy class
    strategy_input = BaseStrategyInput(
        trading_symbol=TradingSymbol("HDFCBANK"), ltp=801
    )
    strategy_params = MockStrategyParams(
        target_percent=4,
        stop_loss_percent=2,
        all_time_high=1000.5,
        allowed_strategy_capital=5000,
    )
    strategy = MockStrategy(
        strategy_input=strategy_input,
        strategy_params=strategy_params,
    )
    print(f"Strategy Name: {strategy.strategy_name}")
    print(f"Strategy Input: {strategy.strategy_input}")
    print(f"Strategy Params: {strategy.strategy_params}")

    print(f"Buy Price: {strategy.get_buy_price()}")
    print(f"Buy Quantity: {strategy.get_buy_quantity(strategy.get_buy_price())}")

    # Do Nothing Example
    strategy_input = BaseStrategyInput(
        trading_symbol=TradingSymbol("HDFCBANK"), ltp=1000
    )

    strategy = MockStrategy(
        strategy_input=strategy_input,
        strategy_params=strategy_params,
    )
    strategy_output = strategy.execute()
    print("Do Nothing Example\n")
    pprint(f"Strategy Output: {strategy_output.model_dump()}\n")
    print("================================================\n")

    # Buy Example
    strategy_input = BaseStrategyInput(
        trading_symbol=TradingSymbol("HDFCBANK"), ltp=801
    )
    strategy = MockStrategy(
        strategy_input=strategy_input,
        strategy_params=strategy_params,
    )
    strategy_output = strategy.execute()
    print("Buy Example\n")
    pprint(f"Strategy Output: {strategy_output.model_dump()}\n")
    print("================================================\n")

    # Hold Example 1
    strategy_input = BaseStrategyInput(
        trading_symbol=TradingSymbol("HDFCBANK"), ltp=805
    )
    strategy = MockStrategy(
        strategy_input=strategy_input,
        strategy_params=strategy_params,
    )
    strategy.trade_status = TradeStatus.HOLDING
    strategy_output = strategy.execute()
    print("Hold Example 1\n")
    pprint(f"Strategy Output: {strategy_output.model_dump()}\n")
    print("================================================\n")

    # Hold Example 2
    strategy_input = BaseStrategyInput(
        trading_symbol=TradingSymbol("HDFCBANK"), ltp=786
    )
    strategy = MockStrategy(
        strategy_input=strategy_input,
        strategy_params=strategy_params,
    )
    strategy.trade_status = TradeStatus.HOLDING
    strategy_output = strategy.execute()
    print("Hold Example 2\n")
    pprint(f"Strategy Output: {strategy_output.model_dump()}\n")
    print("================================================\n")

    # Sell Example 1
    strategy_input = BaseStrategyInput(
        trading_symbol=TradingSymbol("HDFCBANK"), ltp=832
    )
    strategy = MockStrategy(
        strategy_input=strategy_input,
        strategy_params=strategy_params,
    )
    strategy.trade_status = TradeStatus.HOLDING
    strategy_output = strategy.execute()
    print("Sell Example 1\n")
    pprint(f"Strategy Output: {strategy_output.model_dump()}\n")
    print("================================================\n")

    # Sell Example 2
    strategy_input = BaseStrategyInput(
        trading_symbol=TradingSymbol("HDFCBANK"), ltp=785
    )
    strategy = MockStrategy(
        strategy_input=strategy_input,
        strategy_params=strategy_params,
    )
    strategy.trade_status = TradeStatus.HOLDING
    strategy_output = strategy.execute()
    print("Sell Example 2\n")
    pprint(f"Strategy Output: {strategy_output.model_dump()}\n")
    print("================================================\n")
