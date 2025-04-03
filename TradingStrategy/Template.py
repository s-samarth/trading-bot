import os
import sys
import json
import time
from decimal import Decimal
from typing import Optional, Tuple, List, Dict
from abc import ABC, abstractmethod


import numpy as np
from pydantic import BaseModel, Field


from config.Config import Config
from API.Upstox.TradeExecutor import OrderAPIv3 as UpstoxOrderAPI
from API.Upstox.TradeExecutor import PlaceOrderData as UpstoxPlaceOrderData
from API.Upstox.UpstoxLogin import Login as UpstoxLogin
from API.Upstox.Data import UserData, OrderData, MarketQuoteData, BrokerageData
from TradingStrategy.ApiConstantsMapping import UpstoxConstantsMapping
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
    ExectionFrequencyMode,
    ExecutionStatus,
    StrategyName,
    TradingMode,
    TradeAction,
)


class StrategyTemplate(ABC):
    """
    This is a template for creating a trading strategy.
    It includes methods for generating buy/sell signals,
    and executing the strategy. The strategy should be implemented
    by inheriting this class and overriding the abstract methods.

    Parameters:
    - strategy_input: BaseStrategyInput
        The input parameters for the trading strategy.
    - strategy_params: BaseStrategyParams
        The parameters for the trading strategy.
    - mode: TradingMode
        The mode of trading (BACKTEST/LIVE/SANDBOX).
    - broker: Broker
        The broker to be used for trading.
    """

    def __init__(
        self,
        strategy_input: BaseStrategyInput,
        strategy_params: BaseStrategyParams,
        mode: TradingMode = TradingMode.BACKTEST,
    ):

        self.strategy_name = self.__class__.__name__
        self.strategy_input = strategy_input
        self.strategy_params = strategy_params
        self.mode = mode
        self.broker = strategy_input.broker
        self.trade_status = TradeStatus.NOT_TRIGGERED

    @abstractmethod
    def get_buy_price(self) -> Decimal:
        """
        Calculate the buy price based on your strategy.
        This is an abstract method and should be implemented by the subclass.
        """
        pass

    @abstractmethod
    def get_buy_quantity(self, buy_price: Decimal) -> int:
        """
        Calculate the quantity to buy based on the allowed capital and strategy
        This is an abstract method and should be implemented by the subclass.
        """
        pass

    def execute(self) -> BaseStrategyOutput:
        """
        Execute the trading strategy.
        This method should be called to execute the strategy.
        """
        strategy_output = BaseStrategyOutput(
            trading_symbol=self.strategy_input.trading_symbol,
            exchange=self.strategy_input.exchange,
            trade_action=TradeAction.NO_ACTION,
            broker=self.broker,
        )
        if self.trade_status == TradeStatus.NOT_TRIGGERED:
            strategy_output = self.buy(strategy_output)

        elif self.trade_status == TradeStatus.HOLD:
            strategy_output = self.sell()

        else:
            raise ValueError(
                f"Cannot execute strategy for trade status: {self.trade_status}"
            )

        return strategy_output

    def buy(self, strategy_output: BaseStrategyOutput) -> BaseStrategyOutput:
        """
        Execute the buy order.
        This method should be called to execute the buy order.
        """
        ltp = self.strategy_input.ltp
        buy_signal = self.buy_signal(ltp)

        if buy_signal:
            # Buy signal generated
            buy_price = self.get_buy_price()
            quantity = self.get_buy_quantity(buy_price)
            trade_value = buy_price * quantity
            brokerage_charges = self.get_brokerage_charges(
                buy_price, quantity, transaction_type=BaseTransactionType.BUY
            )

            # Validate if the margin is sufficient for the trade
            if not self.validate_margin(trade_value, brokerage_charges):
                strategy_output.execution_status = ExecutionStatus.FAILURE
                strategy_output.information = "Insufficient margin for trade."
                return strategy_output

            # Place the order
            order_id = self.place_order(
                transaction_type=BaseTransactionType.BUY,
                price=buy_price,
                quantity=quantity,
            )
            strategy_output.trade_action = TradeAction.BUY
            strategy_output.quantity = quantity
            strategy_output.order_id = order_id
            strategy_output.information = "Buy order placed successfully."
            strategy_output.execution_status = ExecutionStatus.SUCCESS

        return strategy_output

    def sell(self, strategy_output: BaseStrategyOutput) -> BaseStrategyOutput:
        """
        Execute the sell order.
        This method should be called to execute the sell order.
        """
        strategy_output.trade_action = TradeAction.HOLD
        ltp = self.strategy_input.ltp
        # Check for sell signals

        sell_signal = self.sell_signal(ltp, self.get_buy_price())
        if sell_signal:
            # Sell signal generated
            sell_price = None
            quantity = None

            # Place the order
            order_id = self.place_order(
                transaction_type=BaseTransactionType.SELL,
                price=sell_price,
                quantity=quantity,
            )

            strategy_output.trade_action = TradeAction.SELL
            strategy_output.quantity = quantity
            strategy_output.order_id = order_id
            strategy_output.information = "Sell order placed successfully."
            strategy_output.execution_status = ExecutionStatus.SUCCESS

        return strategy_output

    def place_order(
        self, transaction_type: BaseTransactionType, price: Decimal, quantity: int
    ) -> str:
        """
        Place an order using the OrderAPI.
        This is a placeholder function and should be replaced with actual API call.
        """
        self.regenerate_access_token_if_expired()
        if self.broker == Broker.UPSTOX:
            access_token = (
                self.sandbox_access_token if self.is_sandbox else self.access_token
            )
            place_order_data = UpstoxPlaceOrderData(
                trading_symbol=self.strategy_input.trading_symbol,
                exchange=UpstoxConstantsMapping.exchange(self.strategy_input.exchange),
                transaction_type=UpstoxConstantsMapping.transaction_type(
                    transaction_type
                ),
                product_type=UpstoxConstantsMapping.product_type(
                    self.strategy_input.product_type
                ),
                order_type=UpstoxConstantsMapping.order_type(
                    self.strategy_input.order_type
                ),
                price=price,
                quantity=quantity,
            )
            order = UpstoxOrderAPI(
                access_token, sandbox_mode=self.is_sandbox
            ).place_order(
                place_order_data=place_order_data,
            )
            try:
                order_id = order["data"]["order_id"]
                return order_id
            except:
                return None

        else:
            raise NotImplementedError(
                "Order placement is not implemented for this broker."
            )

    def get_target_price(self, buy_price: Decimal) -> Decimal:
        """
        Calculate the target price based on the buy price.
        """
        target_price = buy_price * (1 + self.strategy_params.target_percent / 100)
        return target_price

    def get_stop_loss_price(self, buy_price: Decimal) -> Decimal:
        """
        Calculate the stop loss price based on the buy price.
        """
        stop_loss_price = buy_price * (1 - self.strategy_params.stop_loss_percent / 100)
        return stop_loss_price

    def buy_signal(self, ltp: Decimal) -> bool:
        """
        Generate a buy signal based on the last traded price (LTP).
        """
        buy_price = self.get_buy_price()
        tolerance = (self.strategy_params.tolerance_percent / 100) * buy_price
        if ltp < buy_price + tolerance:
            return True
        return False

    def sell_signal(self, ltp: Decimal, buy_price: Decimal) -> bool:
        """
        Generate a sell signal for Trigger Price or Stop Loss Price
        based on the last traded price (LTP) and buy price.
        """
        sell_price_target = self.get_target_price(buy_price)
        target_tolerance = (
            self.strategy_params.tolerance_percent / 100
        ) * sell_price_target
        if ltp > sell_price_target - target_tolerance:
            return True

        sell_price_stop_loss = self.get_stop_loss_price(buy_price)
        stop_loss_tolerance = (
            self.strategy_params.tolerance_percent / 100
        ) * sell_price_stop_loss
        if ltp < sell_price_stop_loss + stop_loss_tolerance:
            return True

        return False

    def get_brokerage_charges(
        self,
        price: Decimal,
        quantity: int,
        transaction_type: BaseTransactionType,
    ) -> Decimal:
        """
        Calculate the brokerage charges based on the buy price.
        This is a placeholder function and should be replaced with actual API call.
        """
        self.regenerate_access_token_if_expired()
        if self.broker == Broker.UPSTOX:
            brokerage_data = BrokerageData(self.access_token).get_brokerage(
                trading_symbol=self.strategy_input.trading_symbol,
                exchange=UpstoxConstantsMapping.exchange(self.strategy_input.exchange),
                transaction_type=UpstoxConstantsMapping.transaction_type(
                    transaction_type
                ),
                price=price,
                quantity=quantity,
            )
            if brokerage_data["status"] != "success":
                return Decimal(25.0)  # Default brokerage charges

            brokerage_charges = brokerage_data["data"]["charges"]["total"]
            return Decimal(brokerage_charges)
        else:
            raise NotImplementedError(
                "Brokerage charges calculation is not implemented for this broker."
            )

    def validate_margin(self, trade_value: Decimal, brokerage_charges: Decimal) -> bool:
        """
        Validate if the margin is sufficient for the trade.
        This is a placeholder function and should be replaced with actual API call.
        """
        self.regenerate_access_token_if_expired()
        if self.broker == Broker.UPSTOX:
            margin_data = UserData(self.access_token).get_fund_and_margin()
            if margin_data["status"] != "success":
                return False
            available_margin = margin_data["data"]["equity"]["available_margin"]
            if available_margin < trade_value + brokerage_charges:
                return False
            return True
        else:
            raise NotImplementedError(
                "Margin validation is not implemented for this broker."
            )


class StrategyTemplateV0(ABC):
    """
    This is a template for creating a trading strategy.
    It includes methods for executing the strategy,
    generating buy/sell signals, and managing orders.
    The strategy should be implemented by inheriting this class
    and overriding the abstract methods.

    Parameters:
    - strategy_input: BaseStrategyInput
        The input parameters for the trading strategy.
    - strategy_params: BaseStrategyParams
        The parameters for the trading strategy.
    - is_sandbox: bool
        If True, the strategy will run in sandbox mode.
    - broker: Broker
        The broker to be used for trading.
    - execution_frequency_mode: ExectionFrequencyMode
        The mode of execution frequency (CONSTANT or DYNAMIC).
        DYNAMIC execution is meant to save unnecessary API calls
        while being able to execute the strategy at a higher frequency
        when the LTP is close to the buy price or target price or stop loss price.
    - execution_frequency: Optional[Decimal]
        The frequency of execution in an hour.
        Default is 10 per hour.
        This argument is used only when the execution_frequency_mode is set to CONSTANT.
    - min_max_execution_frequency: Optional[Tuple[Decimal, Decimal]]
        The minimum and maximum execution frequency in an hour.
        Default is (1/24, 30).
        This argument is used only when the execution_frequency_mode is set to DYNAMIC.
    - logging_mode: str
        The mode of logging the strategy output.
        Default is "append", but can be set to "overwrite" to overwrite the previous logs.
    """

    def __init__(
        self,
        strategy_input: BaseStrategyInput,
        strategy_params: BaseStrategyParams,
        is_sandbox: bool = True,
        broker: Broker = Broker.UPSTOX,
        execution_frequency_mode: ExectionFrequencyMode = ExectionFrequencyMode.CONSTANT,
        execution_frequency: Optional[Decimal] = 10,
        min_max_execution_frequency: Optional[Tuple[Decimal, Decimal]] = (1 / 24, 30),
        logging_mode: str = "append",  # "append" or "overwrite"
    ):
        self.strategy_name = self.__class__.__name__
        self.strategy_input = strategy_input
        self.strategy_params = strategy_params
        self.is_sandbox = is_sandbox
        self.broker = broker
        self.access_token = None
        self.sandbox_access_token = None
        self.execution_frequency_mode = execution_frequency_mode
        self.execution_frequency = execution_frequency
        self.min_execution_frequency = min_max_execution_frequency[0]
        self.max_execution_frequency = min_max_execution_frequency[1]
        self.logging_mode = logging_mode
        self.trade_status = TradeStatus.NOT_TRIGGERED
        self.hold_quantity = 0
        self.buy_order_id = None
        self.sell_order_id = None
        self.order_failure_cooldown_time = (
            60 * 60 * 24
        )  # in seconds, this value is equal to one day

    @abstractmethod
    def get_buy_price(self) -> Decimal:
        """
        Calculate the buy price based on your strategy.
        This is an abstract method and should be implemented by the subclass.
        """
        pass

    @abstractmethod
    def get_buy_quantity(self, buy_price: Decimal) -> int:
        """
        Calculate the quantity to buy based on the allowed capital and strategy
        This is an abstract method and should be implemented by the subclass.
        """
        pass

    def run(self) -> None:
        """
        Run the trading strategy.
        This method should be called to start the strategy execution.
        """
        self.logs: List = self.get_logs()
        if self.execution_frequency_mode == ExectionFrequencyMode.CONSTANT:
            # Run the strategy at a constant frequency
            previous_strategy_output = None
            while True:
                strategy_output, _ = self.execute_strategy()

                if strategy_output.execution_status == ExecutionStatus.FAILURE:
                    # If the order failed, wait for the cooldown period
                    print(f"Order failed. Last Strategy Output: {strategy_output}")
                    time.sleep(self.order_failure_cooldown_time)

                self.log_strategy_output(previous_strategy_output, strategy_output)
                previous_strategy_output = strategy_output
                wait_time = self.rerun_wait_time(self.execution_frequency)
                time.sleep(wait_time)

        elif self.execution_frequency_mode == ExectionFrequencyMode.DYNAMIC:
            # Run the strategy at a dynamic frequency
            previous_strategy_output = None
            while True:
                strategy_output, price_data = self.execute_strategy()
                self.log_strategy_output(previous_strategy_output, strategy_output)
                previous_strategy_output = strategy_output
                self.execution_frequency = self.get_dynamic_execution_frequency(
                    price_data.ltp,
                    price_data.buy_price,
                    price_data.target_price,
                    price_data.stop_loss_price,
                    self.min_execution_frequency,
                    self.max_execution_frequency,
                )
                wait_time = self.rerun_wait_time(self.execution_frequency)
                time.sleep(wait_time)

        else:
            raise ValueError(
                "Invalid execution frequency mode. Use 'constant' or 'dynamic'."
            )

    def execute_strategy(self) -> Tuple[BaseStrategyOutput]:
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
        buy_price = self.get_buy_price()
        target_price = self.get_target_price(buy_price)
        stop_loss_price = self.get_stop_loss_price(buy_price)
        price_data = PriceData(
            ltp=ltp,
            buy_price=buy_price,
            target_price=target_price,
            stop_loss_price=stop_loss_price,
        )

        # Check if the stock is eligible for buying
        if self.trade_status == TradeStatus.NOT_TRIGGERED:
            strategy_output = self.buy(strategy_output, ltp)

        # Check if the stock is eligible for selling
        if self.trade_status == TradeStatus.HOLD:
            strategy_output = self.sell(strategy_output, ltp)

        return strategy_output, price_data

    def buy(
        self, strategy_output: BaseStrategyOutput, ltp: Decimal
    ) -> BaseStrategyOutput:
        """
        Execute the buy order.
        """
        # Check for buy signal
        buy_signal = self.buy_signal(ltp)

        if buy_signal:
            # Buy signal generated
            buy_price = buy_signal.price
            quantity = self.get_buy_quantity(buy_price)
            trade_value = buy_price * quantity
            brokerage_charges = self.get_brokerage_charges(
                buy_price, quantity, transaction_type=BaseTransactionType.BUY
            )

            # Validate if the margin is sufficient for the trade
            if not self.validate_margin(trade_value, brokerage_charges):
                strategy_output.information = "Insufficient margin for trade."
                return strategy_output

            # Place the order
            order_id = self.place_order(
                transaction_type=BaseTransactionType.BUY,
                price=buy_price,
                quantity=quantity,
            )
            # Check if the order was placed successfully
            if not order_id:
                strategy_output.information = (
                    "Order placement failed. No order ID returned."
                )
                strategy_output.execution_status = ExecutionStatus.FAILURE
                return strategy_output

            strategy_output.order_id = order_id
            # Validate the order

            if not self.validate_order(order_id):
                strategy_output.information = (
                    "Order validation failed. Order ID not found."
                )
                strategy_output.execution_status = ExecutionStatus.FAILURE
                return strategy_output
            self.buy_order_id = order_id
            self.hold_quantity = quantity
            self.trade_status = (
                TradeStatus.HOLD
            )  # self.trade_status is affected by the buy signal, it is not the actual status of the order
            strategy_output.information = "Buy order placed successfully."
            strategy_output.execution_status = ExecutionStatus.SUCCESS

            # Check Order Status
            strategy_output = self.buy_order_execution_status(strategy_output)

        else:
            # Check if there is a buy order already placed
            if self.buy_order_id:
                # Check Order Status
                strategy_output = self.buy_order_execution_status(strategy_output)
                return strategy_output

        return strategy_output

    def sell(
        self, strategy_output: BaseStrategyOutput, ltp: Decimal
    ) -> BaseStrategyOutput:
        """
        Execute the sell order.
        """
        # Check for sell signals
        sell_signal_trigger = self.sell_signal_trigger(ltp, self.get_buy_price())
        sell_signal_stop_loss = self.sell_signal_stop_loss(ltp, self.get_buy_price())
        sell_signal = (
            sell_signal_trigger if sell_signal_trigger else sell_signal_stop_loss
        )
        if sell_signal:
            # Sell signal generated
            sell_price = sell_signal.price
            trade_value = sell_price * self.hold_quantity
            brokerage_charges = self.get_brokerage_charges(
                sell_price,
                self.hold_quantity,
                transaction_type=BaseTransactionType.SELL,
            )

            # Validate if the margin is sufficient for the trade
            if not self.validate_margin(trade_value, brokerage_charges):
                strategy_output.information = "Insufficient margin for trade."
                return strategy_output

            # Place the order
            order_id = self.place_order(
                transaction_type=BaseTransactionType.SELL,
                price=sell_price,
                quantity=self.hold_quantity,
            )
            # Check if the order was placed successfully
            if not order_id:
                strategy_output.information = (
                    "Order placement failed. No order ID returned."
                )
                strategy_output.execution_status = ExecutionStatus.FAILURE
                return strategy_output

            strategy_output.order_id = order_id
            # Validate the order
            if not self.validate_order(order_id):
                strategy_output.information = (
                    "Order validation failed. Order ID not found."
                )
                strategy_output.execution_status = ExecutionStatus.FAILURE
                return strategy_output

            self.sell_order_id = order_id
            self.trade_status = sell_signal.trade_status
            strategy_output.information = "Sell order placed successfully."

            # Check Order Status
            strategy_output = self.sell_order_execution_status(strategy_output)

        else:
            # Check if there is a sell order already placed
            if self.sell_order_id:
                # Check Order Status
                strategy_output = self.sell_order_execution_status(strategy_output)

        return strategy_output

    def get_target_price(self, buy_price: Decimal) -> Decimal:
        """
        Calculate the target price based on the buy price.
        """
        target_price = buy_price * (1 + self.strategy_params.target_percent / 100)
        return target_price

    def get_stop_loss_price(self, buy_price: Decimal) -> Decimal:
        """
        Calculate the stop loss price based on the buy price.
        """
        stop_loss_price = buy_price * (1 - self.strategy_params.stop_loss_percent / 100)
        return stop_loss_price

    def buy_signal(self, ltp: Decimal) -> BaseStrategyTradeSignal:
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

    def sell_signal_trigger(
        self, ltp: Decimal, buy_price: Decimal
    ) -> BaseStrategyTradeSignal:
        """
        Generate a sell signal for Trigger Price based on the last traded price (LTP) and buy price.
        """
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

    def sell_signal_stop_loss(
        self, ltp: Decimal, buy_price: Decimal
    ) -> BaseStrategyTradeSignal:
        """
        Generate a sell signal for Stop Loss based on the last traded price (LTP) and buy price.
        """
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

    def broker_login(self) -> None:
        """
        Login to the broker API.
        """
        if self.broker == Broker.UPSTOX:
            try:
                self.access_token = UpstoxLogin().login()
                if self.is_sandbox:
                    self.sandbox_access_token = UpstoxLogin().login()
            except Exception as e:
                raise ValueError(f"Error logging into broker: {e}")
        else:
            raise NotImplementedError(
                "Broker login is not implemented for this broker."
            )

    def regenerate_access_token_if_expired(self) -> None:
        """
        Check if the access token is expired and regenerate it if necessary.
        """
        if not self.access_token:
            self.broker_login()
            return
        if self.broker == Broker.UPSTOX:
            try:
                self.user_data = UserData(self.access_token)
                self.user_data.get_profile()
            except:
                # If the access token is expired, regenerate it
                self.broker_login()
        else:
            raise NotImplementedError(
                "Access token expiry check is not implemented for this broker."
            )

    def get_ltp(self) -> Decimal:
        """
        Fetch the last traded price (LTP) of the stock.
        This is a placeholder function and should be replaced with actual API call.
        """
        self.regenerate_access_token_if_expired()
        if self.broker == Broker.UPSTOX:
            try:
                ltp_data = MarketQuoteData(self.access_token).get_ltp(
                    trading_symbol=self.strategy_input.trading_symbol,
                    exchange=UpstoxConstantsMapping.exchange(
                        self.strategy_input.exchange
                    ),
                )["data"]
                key = (
                    UpstoxConstantsMapping.exchange(self.strategy_input.exchange).value
                    + "_"
                    + UpstoxConstantsMapping.segment(self.strategy_input.segment)
                    + ":"
                    + self.strategy_input.trading_symbol.value
                )
                ltp = ltp_data[key]["last_price"]
                return Decimal(ltp)
            except Exception as e:
                raise ValueError(f"Error fetching LTP: {e}")

        else:
            raise NotImplementedError(
                "LTP fetching is not implemented for this broker."
            )

    def get_order_price(self, order_id: str) -> Decimal:
        """
        Fetch the order price for the stock.
        This is a placeholder function and should be replaced with actual API call.
        """
        self.regenerate_access_token_if_expired()
        if self.broker == Broker.UPSTOX:
            order_price = OrderData(self.access_token).get_order_details(order_id)[
                "data"
            ]["average_price"]
            return order_price

        else:
            raise NotImplementedError(
                "Order price fetching is not implemented for this broker."
            )

    def get_brokerage_charges(
        self,
        price: Decimal,
        quantity: int,
        transaction_type: BaseTransactionType,
    ) -> Decimal:
        """
        Calculate the brokerage charges based on the buy price.
        This is a placeholder function and should be replaced with actual API call.
        """
        self.regenerate_access_token_if_expired()
        if self.broker == Broker.UPSTOX:
            brokerage_data = BrokerageData(self.access_token).get_brokerage(
                trading_symbol=self.strategy_input.trading_symbol,
                exchange=UpstoxConstantsMapping.exchange(self.strategy_input.exchange),
                transaction_type=UpstoxConstantsMapping.transaction_type(
                    transaction_type
                ),
                price=price,
                quantity=quantity,
            )
            if brokerage_data["status"] != "success":
                return Decimal(25.0)  # Default brokerage charges

            brokerage_charges = brokerage_data["data"]["charges"]["total"]
            return Decimal(brokerage_charges)
        else:
            raise NotImplementedError(
                "Brokerage charges calculation is not implemented for this broker."
            )

    def validate_margin(self, trade_value: Decimal, brokerage_charges: Decimal) -> bool:
        """
        Validate if the margin is sufficient for the trade.
        This is a placeholder function and should be replaced with actual API call.
        """
        self.regenerate_access_token_if_expired()
        if self.broker == Broker.UPSTOX:
            margin_data = UserData(self.access_token).get_fund_and_margin()
            if margin_data["status"] != "success":
                return False
            available_margin = margin_data["data"]["equity"]["available_margin"]
            if available_margin < trade_value + brokerage_charges:
                return False
            return True
        else:
            raise NotImplementedError(
                "Margin validation is not implemented for this broker."
            )

    def place_order(
        self, transaction_type: BaseTransactionType, price: Decimal, quantity: int
    ) -> str:
        """
        Place an order using the OrderAPI.
        This is a placeholder function and should be replaced with actual API call.
        """
        self.regenerate_access_token_if_expired()
        if self.broker == Broker.UPSTOX:
            access_token = (
                self.sandbox_access_token if self.is_sandbox else self.access_token
            )
            place_order_data = UpstoxPlaceOrderData(
                trading_symbol=self.strategy_input.trading_symbol,
                exchange=UpstoxConstantsMapping.exchange(self.strategy_input.exchange),
                transaction_type=UpstoxConstantsMapping.transaction_type(
                    transaction_type
                ),
                product_type=UpstoxConstantsMapping.product_type(
                    self.strategy_input.product_type
                ),
                order_type=UpstoxConstantsMapping.order_type(
                    self.strategy_input.order_type
                ),
                price=price,
                quantity=quantity,
            )
            order = UpstoxOrderAPI(
                access_token, sandbox_mode=self.is_sandbox
            ).place_order(
                place_order_data=place_order_data,
            )
            try:
                order_id = order["data"]["order_id"]
                return order_id
            except:
                return None

        else:
            raise NotImplementedError(
                "Order placement is not implemented for this broker."
            )

    def validate_order(self, order_id: str) -> bool:
        """
        Validate the order status using the OrderAPI.
        This is a placeholder function and should be replaced with actual API call.
        """
        self.regenerate_access_token_if_expired()
        if self.broker == Broker.UPSTOX:
            order_data = OrderData(self.access_token).get_order_details(order_id)
            if order_data["status"] == "success":
                return True
            else:
                return False
        else:
            raise NotImplementedError(
                "Order validation is not implemented for this broker."
            )

    def get_order_status(self, order_id: str) -> BaseOrderStatus:
        """
        Get the order status using the OrderAPI.
        This is a placeholder function and should be replaced with actual API call.
        """
        self.regenerate_access_token_if_expired()
        if self.broker == Broker.UPSTOX:
            order_data = OrderData(self.access_token).get_order_details(order_id)
            order_status = order_data["status"]
            if order_status == UpstoxConstantsMapping.order_status(
                BaseOrderStatus.OPEN
            ):
                order_status = BaseOrderStatus.OPEN

            elif order_status == UpstoxConstantsMapping.order_status(
                BaseOrderStatus.COMPLETE
            ):
                order_status = BaseOrderStatus.COMPLETE

            elif order_status == UpstoxConstantsMapping.order_status(
                BaseOrderStatus.CANCELLED
            ):
                order_status = BaseOrderStatus.CANCELLED

            elif order_status == UpstoxConstantsMapping.order_status(
                BaseOrderStatus.REJECTED
            ):
                order_status = BaseOrderStatus.REJECTED

            return order_status
        else:
            raise NotImplementedError(
                "Order status fetching is not implemented for this broker."
            )

    def buy_order_execution_status(
        self, strategy_output: BaseStrategyOutput
    ) -> BaseStrategyOutput:
        """
        Retrieve the order status and update the strategy output.
        This method is called after placing a buy order.
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
            strategy_output.execution_status = ExecutionStatus.SUCCESS
        elif order_status == BaseOrderStatus.CANCELLED:
            self.trade_status = TradeStatus.NOT_TRIGGERED
            strategy_output.information = "Buy order was cancelled."
            strategy_output.execution_status = ExecutionStatus.FAILURE
        elif order_status == BaseOrderStatus.REJECTED:
            self.trade_status = TradeStatus.NOT_TRIGGERED
            strategy_output.information = "Buy order was rejected."
            strategy_output.execution_status = ExecutionStatus.FAILURE
        else:
            self.trade_status = TradeStatus.NOT_TRIGGERED
            strategy_output.information = "Buy order status is unknown."
            strategy_output.execution_status = ExecutionStatus.FAILURE
        return strategy_output

    def sell_order_execution_status(
        self, strategy_output: BaseStrategyOutput
    ) -> BaseStrategyOutput:
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
            strategy_output.execution_status = ExecutionStatus.SUCCESS
        elif order_status == BaseOrderStatus.CANCELLED:
            self.trade_status = TradeStatus.HOLD
            strategy_output.information = "Sell order was cancelled."
            strategy_output.execution_status = ExecutionStatus.FAILURE
        elif order_status == BaseOrderStatus.REJECTED:
            self.trade_status = TradeStatus.HOLD
            strategy_output.information = "Sell order was rejected."
            strategy_output.execution_status = ExecutionStatus.FAILURE
        else:
            self.trade_status = TradeStatus.HOLD
            strategy_output.information = "Sell order status is unknown."
            strategy_output.execution_status = ExecutionStatus.FAILURE
        return strategy_output

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

    def rerun_wait_time(self, frequency: Decimal) -> int:
        """
        Calculate the wait time before rerunning the strategy.
        """
        # Example logic to calculate wait time in seconds
        wait_time = 3600 / frequency  # Convert frequency to seconds
        # Round it to the nearest integer
        wait_time = int(wait_time)
        # Ensure wait time is at least 1 second
        if wait_time < 1:
            wait_time = 1
        return wait_time

    def get_dynamic_execution_frequency(
        self,
        ltp: Decimal,
        buy_price: Decimal,
        target_price: Decimal,
        stop_loss_price: Decimal,
        min_frequency: Decimal = 1 / 24,
        max_frequency: Decimal = 30,
    ) -> Decimal:
        """
        Get the dynamic execution frequency based on LTP and other factors.
        On a log scale, increasing the execution frequency from min_frequency
        to max_frequency based on the percentage closeness of LTP to the buy price
        or target price or stop loss price.
        """
        # Example logic to calculate dynamic execution frequency
        # This should be replaced with actual logic to calculate the frequency
        epsilon = 0.01
        penalization_exponent = (
            2  # We want to penalize the frequency if the LTP is too far from price
        )
        if self.trade_status == TradeStatus.NOT_TRIGGERED:
            ltp_buy_ratio = ltp / buy_price
            if ltp_buy_ratio <= 1:
                return max_frequency
            else:
                percentage_closeness = (ltp_buy_ratio - 1) * 100
                raw_frequency = (
                    1
                    / (np.log1p(percentage_closeness + epsilon))
                    ** penalization_exponent
                )
                max_raw_frequency = 1 / (
                    np.log1p(epsilon) ** penalization_exponent
                )  # With Epsilon=0.01, this comes out to be 100, mathematical approximation ln(1+x) ~ x if x is small
                # Normalize the frequency to the range [min_frequency, max_frequency]
                frequency = min_frequency + (max_frequency - min_frequency) * (
                    raw_frequency / max_raw_frequency
                )
                return frequency

        elif self.trade_status == TradeStatus.HOLD:
            ltp_target_ratio = ltp / target_price
            if ltp_target_ratio >= 1:
                return max_frequency
            else:
                percentage_closeness = (ltp_target_ratio - 1) * 100
                raw_frequency = (
                    1
                    / (np.log1p(percentage_closeness + epsilon))
                    ** penalization_exponent
                )
                max_raw_frequency = 1 / (np.log1p(epsilon) ** penalization_exponent)
                # Normalize the frequency to the range [min_frequency, max_frequency]
                target_frequency = min_frequency + (max_frequency - min_frequency) * (
                    raw_frequency / max_raw_frequency
                )

            ltp_stop_loss_ratio = ltp / stop_loss_price
            if ltp_stop_loss_ratio <= 1:
                return max_frequency
            else:
                percentage_closeness = (ltp_stop_loss_ratio - 1) * 100
                raw_frequency = (
                    1
                    / (np.log1p(percentage_closeness + epsilon))
                    ** penalization_exponent
                )
                max_raw_frequency = 1 / (np.log1p(epsilon) ** penalization_exponent)
                # Normalize the frequency to the range [min_frequency, max_frequency]
                stop_loss_frequency = min_frequency + (
                    max_frequency - min_frequency
                ) * (raw_frequency / max_raw_frequency)
                return max(target_frequency, stop_loss_frequency)
        else:
            # If the strategy is not triggered or hold, return the default frequency
            # Although this case should not happen as per the design
            # But we are keeping it for safety
            return (
                min_frequency + max_frequency
            ) / 2  # Default frequency if not triggered or hold

    def log_strategy_output(
        self,
        previous_strategy_output: BaseStrategyOutput = None,
        current_strategy_output: BaseStrategyOutput = None,
    ) -> None:
        """
        If the strategy output state_changes,
        Log the strategy output to a file.
        """
        results_dir = self.get_results_directory()
        filename = f"{self.strategy_input.trading_symbol}_{self.strategy_name}.json"
        file_path = os.path.join(results_dir, filename)
        if previous_strategy_output != current_strategy_output:
            results = current_strategy_output.model_dump()
            self.logs.append(results)
            with open(file_path, "w") as file:
                json.dump(self.logs, file, indent=4)

    def get_logs(self) -> str:
        """
        Get the log file
        """
        results_dir = self.get_results_directory()
        filename = f"{self.strategy_input.trading_symbol}_{self.strategy_name}.json"
        file_path = os.path.join(results_dir, filename)
        if self.logging_mode == "overwrite":
            return []
        if self.logging_mode == "append":
            if os.path.exists(file_path):
                with open(file_path, "r") as file:
                    logs = json.load(file)
                return logs
            else:
                return []

    def get_results_directory(self) -> str:
        """
        Get the directory where the logs will be stored.
        """
        root_dir = Config.root_dir
        results_dir = os.path.join(root_dir, "TradingResults")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        if self.is_sandbox:
            results_dir = os.path.join(results_dir, "Sandbox")
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
        else:
            results_dir = os.path.join(results_dir, "Real")
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)

        return results_dir


class PriceData(BaseModel):
    """
    This class is used to define the price data structure for a trading strategy.
    """

    ltp: Decimal = Field(..., description="Last traded price of the stock.")
    buy_price: Decimal = Field(..., description="Buy price of the stock.")
    target_price: Decimal = Field(
        ..., description="Target price for selling the stock."
    )
    stop_loss_price: Decimal = Field(..., description="Stop loss price for the stock.")
