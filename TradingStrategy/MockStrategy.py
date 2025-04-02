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


CAPITAL = 1_00_000  # Total capital available for trading


class MockStrategyParams(BaseStrategyParams):
    """
    Parameters for the mock trading strategy.
    """

    all_time_high: Decimal = Field(
        default=1000.5, description="The all-time high price of the stock."
    )
    allowed_strategy_capital: Decimal = Field(
        default=CAPITAL * 0.05,
        description="The capital allowed for trading using this strategy.",
    )


class MockStrategy:
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
    The file name will be the Results.json
    """

    def __init__(
        self,
        strategy_input: BaseStrategyInput,
        strategy_params: MockStrategyParams,
        is_sandbox: bool = True,
        broker: Broker = Broker.UPSTOX,
    ):
        self.strategy_input = strategy_input
        self.strategy_params = strategy_params
        self.is_sandbox = is_sandbox
        self.broker = broker
        self.trade_status = TradeStatus.NOT_TRIGGERED
        self.hold_quantity = 0
        self.buy_order_id = None
        self.sell_order_id = None

    def execute_strategy(self): ...

    def strategy(self):
        """
        Execute the trading strategy.
        """
        strategy_output = BaseStrategyOutput(
            trading_symbol=self.strategy_input.trading_symbol,
            exchange=self.strategy_input.exchange,
            trade_status=self.trade_status,
            broker=self.broker,
        )
        ltp = self.get_ltp()
        # Check if the stock is eligible for trading
        if self.check_if_strategy_is_already_executed():
            strategy_output.information = (
                "Strategy already executed. Status type is HOLD."
            )
            return strategy_output

        # Check for buy signal
        buy_signal = self.buy_signal(ltp)
        if buy_signal:
            # Buy signal generated
            buy_price = buy_signal.price
            quantity = self.get_buy_quantity(buy_price)
            trade_value = buy_price * quantity
            brokerage_charges = self.get_brokerage_charges(trade_value)

            # Validate if the margin is sufficient for the trade
            if not self.validate_margin(trade_value, brokerage_charges):
                strategy_output.information = "Insufficient margin for trade."
                return strategy_output

            # Place the order
            order_id = self.place_order()
            # Check if the order was placed successfully
            if not order_id:
                strategy_output.information = (
                    "Order placement failed. No order ID returned."
                )
                return strategy_output

            strategy_output.order_id = order_id
            # Validate the order
            if not self.validate_order(order_id):
                strategy_output.information = (
                    "Order validation failed. Order ID not found."
                )
                return strategy_output
            self.buy_order_id = order_id
            self.trade_status = (
                TradeStatus.HOLD
            )  # self.trade_status is affected by the buy signal, it is not the actual status of the order
            strategy_output.information = "Buy order placed successfully."

        # Check Order Status
        strategy_output = self.buy_order_execution(strategy_output)

        if self.trade_status == TradeStatus.HOLD:
            # Check for sell signal
            sell_signal = self.sell_signal(ltp, buy_price)
            if sell_signal:
                # Sell signal generated
                sell_price = sell_signal.price
                trade_value = sell_price * self.hold_quantity
                brokerage_charges = self.get_brokerage_charges(trade_value)

                # Validate if the margin is sufficient for the trade
                if not self.validate_margin(trade_value, brokerage_charges):
                    strategy_output.information = "Insufficient margin for trade."
                    return strategy_output

                # Place the order
                order_id = self.place_order()
                # Check if the order was placed successfully
                if not order_id:
                    strategy_output.information = (
                        "Order placement failed. No order ID returned."
                    )
                    return strategy_output

                strategy_output.order_id = order_id
                # Validate the order
                if not self.validate_order(order_id):
                    strategy_output.information = (
                        "Order validation failed. Order ID not found."
                    )
                    return strategy_output

                self.sell_order_id = order_id
                self.trade_status = sell_signal.trade_status
                strategy_output.information = "Sell order placed successfully."

            # Check Order Status
            strategy_output = self.sell_order_execution(strategy_output)

        return strategy_output

    def log_strategy_output(
        self,
        previous_strategy_output: BaseStrategyOutput = None,
        current_strategy_output: BaseStrategyOutput = None,
    ):
        """
        If the strategy output state_changes,
        Log the strategy output to a file.
        """
        ...

    def buy_signal(self, ltp: Decimal):
        """
        Generate a buy signal based on the last traded price (LTP).
        """
        buy_price = self.get_buy_price()
        tolerance = (self.strategy_params.tolerance_percent / 100) * buy_price
        if ltp < buy_price + tolerance:
            signal = BaseStrategyTradeSignal(
                transaction_type=BaseTransactionType.BUY,
                price=buy_price,
                trade_status=TradeStatus.HOLD,
            )
            return signal
        return None

    def sell_signal(self, ltp: Decimal, buy_price: Decimal):
        """
        Generate a sell signal based on the last traded price (LTP) and buy price.
        """
        # Check for target price
        sell_price_target = self.get_target_price(buy_price)
        target_tolerance = (
            self.strategy_params.tolerance_percent / 100
        ) * sell_price_target
        if ltp > sell_price_target - target_tolerance:
            signal = BaseStrategyTradeSignal(
                transaction_type=BaseTransactionType.SELL,
                price=sell_price_target,
                trade_status=TradeStatus.PROFIT,
            )
            return signal

        # Check for stop loss
        sell_price_stop_loss = self.get_stop_loss_price(buy_price)
        stop_loss_tolerance = (
            self.strategy_params.tolerance_percent / 100
        ) * sell_price_stop_loss
        if ltp < sell_price_stop_loss + stop_loss_tolerance:
            signal = BaseStrategyTradeSignal(
                transaction_type=BaseTransactionType.SELL,
                price=sell_price_stop_loss,
                trade_status=TradeStatus.LOSS,
            )
            return signal

    def get_ltp(self):
        """
        Fetch the last traded price (LTP) of the stock.
        This is a placeholder function and should be replaced with actual API call.
        """
        ltp = 950.0  # Example LTP, replace with actual API call
        return ltp

    def get_order_price(self, order_id: str):
        """
        Fetch the order price for the stock.
        This is a placeholder function and should be replaced with actual API call.
        """
        order_price = 1000.0
        return order_price

    def get_buy_price(self):
        """
        Calculate the buy price based on the all-time high and the buy signal.
        """
        buy_price = self.strategy_params.all_time_high * 0.8
        return buy_price

    def get_target_price(self, buy_price: Decimal):
        """
        Calculate the target price based on the buy price.
        """
        target_price = buy_price * (1 + self.strategy_params.target_percent / 100)
        return target_price

    def get_stop_loss_price(self, buy_price: Decimal):
        """
        Calculate the stop loss price based on the buy price.
        """
        stop_loss_price = buy_price * (1 - self.strategy_params.stop_loss_percent / 100)
        return stop_loss_price

    def get_buy_quantity(self, buy_price: Decimal):
        """
        Calculate the quantity to buy based on the allowed capital.
        """
        quantity = int(self.strategy_params.allowed_strategy_capital / buy_price)
        return quantity

    def get_brokerage_charges(self, trade_value: Decimal):
        """
        Calculate the brokerage charges based on the buy price.
        This is a placeholder function and should be replaced with actual API call.
        """
        brokerage_charges = trade_value * 0.01
        return brokerage_charges

    def validate_margin(self, trade_value: Decimal, brokerage_charges: Decimal):
        """
        Validate if the margin is sufficient for the trade.
        This is a placeholder function and should be replaced with actual API call.
        """
        # Example margin validation logic
        margin_available = (
            10_000_00  # Example margin available, replace with actual API call
        )
        if trade_value + brokerage_charges > margin_available:
            return False
        return True

    def place_order(self):
        """
        Place an order using the OrderAPI.
        This is a placeholder function and should be replaced with actual API call.
        """
        order_id = "123456789"  # Example order ID, replace with actual API call
        return order_id

    def validate_order(self, order_id: str):
        """
        Validate the order status using the OrderAPI.
        This is a placeholder function and should be replaced with actual API call.
        """
        True  # Example order validation logic

    def get_order_status(self, order_id: str):
        """
        Get the order status using the OrderAPI.
        This is a placeholder function and should be replaced with actual API call.
        """
        order_status = BaseOrderStatus.OPEN
        return order_status

    def buy_order_execution(self, strategy_output: BaseStrategyOutput):
        """
        Execute the order
        """
        order_status = self.get_order_status(self.buy_order_id)
        strategy_output.order_status = order_status
        if order_status == BaseOrderStatus.OPEN:
            # Order is open, wait for execution
            strategy_output.information = "Buy order is open and waiting for execution."
        elif order_status == BaseOrderStatus.COMPLETE:
            strategy_output.transaction_type = BaseTransactionType.BUY
            strategy_output.transaction_price = self.get_order_price(self.buy_order_id)
            strategy_output.trade_status = self.trade_status
            strategy_output.information = "Buy order executed successfully."
        elif order_status == BaseOrderStatus.CANCELLED:
            self.trade_status = TradeStatus.NOT_TRIGGERED
            strategy_output.information = "Buy order was cancelled."
        elif order_status == BaseOrderStatus.REJECTED:
            self.trade_status = TradeStatus.NOT_TRIGGERED
            strategy_output.information = "Buy order was rejected."
        else:
            self.trade_status = TradeStatus.NOT_TRIGGERED
            strategy_output.information = "Buy order status is unknown."
        return strategy_output

    def sell_order_execution(self, strategy_output: BaseStrategyOutput):
        """
        Execute the order
        """
        order_status = self.get_order_status(self.sell_order_id)
        strategy_output.order_status = order_status
        if order_status == BaseOrderStatus.OPEN:
            # Order is open, wait for execution
            strategy_output.information = (
                "Sell order is open and waiting for execution."
            )
        elif order_status == BaseOrderStatus.COMPLETE:
            strategy_output.transaction_type = BaseTransactionType.SELL
            strategy_output.transaction_price = self.get_order_price(self.sell_order_id)
            strategy_output.trade_status = self.trade_status
            strategy_output.information = "Sell order executed successfully."
        elif order_status == BaseOrderStatus.CANCELLED:
            self.trade_status = TradeStatus.HOLD
            strategy_output.information = "Sell order was cancelled."
        elif order_status == BaseOrderStatus.REJECTED:
            self.trade_status = TradeStatus.HOLD
            strategy_output.information = "Sell order was rejected."
        else:
            self.trade_status = TradeStatus.HOLD
            strategy_output.information = "Sell order status is unknown."
        return strategy_output

    def check_if_strategy_is_already_executed(self):
        """
        Check if this strategy was already executed.
        for the given trading symbol.
        """
        # Example logic to check if the strategy was already executed
        # This should be replaced with actual logic to check the execution status
        if self.trade_status == TradeStatus.HOLD:
            return True
        return False

    def cooldown_strategy(self):
        """
        Cool down the strategy for a specified duration.
        This is a placeholder function and should be replaced with actual logic.
        """
        raise NotImplementedError("Cooldown strategy is not implemented yet.")

    def check_if_strategy_is_cooldown(self):
        """
        Check if the strategy is in cooldown mode.
        This is a placeholder function and should be replaced with actual logic.
        """
        raise NotImplementedError(
            "Check if strategy is in cooldown is not implemented yet."
        )


if __name__ == "__main__":
    # Example usage
    strategy_input = BaseStrategyInput(
        trading_symbol=TradingSymbol.HDFCBANK, exchange=BaseExchange.NSE
    )
