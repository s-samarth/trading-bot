import random
from abc import ABC, abstractmethod


from API.Upstox.TradeExecutor import OrderAPIv3 as UpstoxOrderAPI
from API.Upstox.TradeExecutor import PlaceOrderData as UpstoxPlaceOrderData
from API.Upstox.Data import UserData, BrokerageData
from TradingStrategy.ApiConstantsMapping import UpstoxConstantsMapping
from TradingStrategy.StrategyData import (
    BaseStrategyInput,
    BaseStrategyParams,
    BaseStrategyOutput,
)
from TradingStrategy.Constants import (
    TradeResult,
    TradeStatus,
    BaseTransactionType,
    Broker,
    BaseOrderType,
    ExecutionStatus,
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
        self.trade_status = (
            TradeStatus.NOT_TRIGGERED
        )  # To be changed only by the Strategy Manager
        self.quantity = None  # To be changed only by the Strategy Validator in case of only partial buy
        self.holding_quantity = 0  # To be changed only by the strategy manager

    @abstractmethod
    def get_buy_price(self) -> float:
        """
        Calculate the buy price based on your strategy.
        This is an abstract method and should be implemented by the subclass.
        """
        pass

    @abstractmethod
    def get_buy_quantity(self, buy_price: float) -> int:
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

        elif self.trade_status == TradeStatus.HOLDING:
            strategy_output = self.sell(strategy_output)

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
            order_id = self.place_limit_order(
                transaction_type=BaseTransactionType.BUY,
                price=buy_price,
                quantity=quantity,
            )
            strategy_output.trade_action = TradeAction.BUY
            strategy_output.quantity = quantity
            strategy_output.trade_charges = brokerage_charges
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
        buy_price = self.get_buy_price()
        quantity = self.quantity if self.quantity else self.get_buy_quantity(buy_price)
        strategy_output.quantity = (
            quantity  # Set the quantity in the output even while holding
        )
        if quantity > self.holding_quantity:
            return strategy_output

        sell_signal = self.sell_signal(ltp, buy_price)
        if sell_signal:
            # Sell signal generated
            if sell_signal == TradeResult.PROFIT:
                sell_price = self.get_target_price(buy_price)
            else:
                sell_price = self.get_stop_loss_price(buy_price)

            # Place the order
            order_id = self.place_limit_order(
                transaction_type=BaseTransactionType.SELL,
                price=sell_price,
                quantity=quantity,
            )

            # Get Brokerage Charges
            brokerage_charges = self.get_brokerage_charges(
                buy_price, quantity, transaction_type=BaseTransactionType.BUY
            )

            strategy_output.trade_action = TradeAction.SELL
            strategy_output.quantity = quantity
            strategy_output.trade_charges = brokerage_charges
            strategy_output.order_id = order_id
            strategy_output.information = f"Sell order placed successfully."
            strategy_output.execution_status = ExecutionStatus.SUCCESS

        return strategy_output

    def place_limit_order(
        self, transaction_type: BaseTransactionType, price: float, quantity: int
    ) -> str:
        """
        Place a LIMIT order using the OrderAPI.
        This is a placeholder function and should be replaced with actual API call.
        """
        if self.mode == TradingMode.BACKTEST or self.mode == TradingMode.SIMULATION:
            # Backtest or Simulation mode, no order placement Generate random order ID
            order_id = str(random.randint(100000, 999999))
            return order_id

        elif self.mode == TradingMode.LIVE:
            # Live mode, place order using the API
            if self.broker is None:
                raise ValueError("Broker is not set for live trading.")

            if self.broker == Broker.UPSTOX:
                access_token = self.strategy_input.access_token
                place_order_data = UpstoxPlaceOrderData(
                    trading_symbol=self.strategy_input.trading_symbol,
                    exchange=UpstoxConstantsMapping.exchange(
                        self.strategy_input.exchange
                    ),
                    transaction_type=UpstoxConstantsMapping.transaction_type(
                        transaction_type
                    ),
                    product_type=UpstoxConstantsMapping.product_type(
                        self.strategy_input.product_type
                    ),
                    order_type=UpstoxConstantsMapping.order_type(BaseOrderType.LIMIT),
                    price=price,
                    quantity=quantity,
                )
                order = UpstoxOrderAPI(access_token, sandbox_mode=False).place_order(
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
        else:
            raise NotImplementedError(
                "Order placement is not implemented for this mode."
            )

    def get_target_price(self, buy_price: float) -> float:
        """
        Calculate the target price based on the buy price.
        """
        target_price = buy_price * (1 + self.strategy_params.target_percent / 100)
        return target_price

    def get_stop_loss_price(self, buy_price: float) -> float:
        """
        Calculate the stop loss price based on the buy price.
        """
        stop_loss_price = buy_price * (1 - self.strategy_params.stop_loss_percent / 100)
        return stop_loss_price

    def buy_signal(self, ltp: float) -> bool:
        """
        Generate a buy signal based on the last traded price (LTP).
        """
        buy_price = self.get_buy_price()
        tolerance = (self.strategy_params.tolerance_percent / 100) * buy_price
        if ltp < buy_price + tolerance:
            return True
        return False

    def sell_signal(self, ltp: float, buy_price: float) -> TradeResult:
        """
        Generate a sell signal for Trigger Price or Stop Loss Price
        based on the last traded price (LTP) and buy price.
        """
        sell_price_target = float(self.get_target_price(buy_price))
        target_tolerance = (
            self.strategy_params.tolerance_percent / 100
        ) * sell_price_target
        if ltp > sell_price_target - target_tolerance:
            return TradeResult.PROFIT

        sell_price_stop_loss = self.get_stop_loss_price(buy_price)
        stop_loss_tolerance = (
            self.strategy_params.tolerance_percent / 100
        ) * sell_price_stop_loss
        if ltp < sell_price_stop_loss + stop_loss_tolerance:
            return TradeResult.LOSS

        return None

    def get_brokerage_charges(
        self,
        price: float,
        quantity: int,
        transaction_type: BaseTransactionType,
    ) -> float:
        """
        Calculate the brokerage charges based on the buy price.
        This is a placeholder function and should be replaced with actual API call.
        """
        default_brokerage = 25
        if self.mode == TradingMode.BACKTEST or TradingMode.SIMULATION:
            return default_brokerage

        elif self.mode == TradingMode.LIVE:
            if self.broker is None:
                raise ValueError("Broker is not set for live trading.")

            if self.broker == Broker.UPSTOX:
                brokerage_data = BrokerageData(
                    self.strategy_input.access_token
                ).get_brokerage(
                    trading_symbol=self.strategy_input.trading_symbol,
                    exchange=UpstoxConstantsMapping.exchange(
                        self.strategy_input.exchange
                    ),
                    transaction_type=UpstoxConstantsMapping.transaction_type(
                        transaction_type
                    ),
                    price=price,
                    quantity=quantity,
                )
                try:
                    brokerage_charges = brokerage_data["data"]["charges"]["total"]
                    return brokerage_charges
                except:
                    return default_brokerage
            else:
                raise NotImplementedError(
                    "Brokerage charges calculation is not implemented for this broker."
                )

        else:
            raise NotImplementedError(
                "Brokerage charges calculation is not implemented for this mode."
            )

    def validate_margin(self, trade_value: float, brokerage_charges: float) -> bool:
        """
        Validate if the margin is sufficient for the trade.
        This is a placeholder function and should be replaced with actual API call.
        """
        if self.mode == TradingMode.BACKTEST or TradingMode.SIMULATION:
            # Need to make this functionality for these modes too
            return True

        elif self.mode == TradingMode.LIVE:

            if self.broker == Broker.UPSTOX:
                margin_data = UserData(
                    self.strategy_input.access_token
                ).get_fund_and_margin()
                if margin_data["status"] != "success":
                    return False

                try:
                    available_margin = margin_data["data"]["equity"]["available_margin"]
                except:
                    return False

                if available_margin < trade_value + brokerage_charges:
                    return False
                return True
            else:
                raise NotImplementedError(
                    "Margin validation is not implemented for this broker."
                )

        else:
            raise NotImplementedError(
                "Margin validation is not implemented for this mode."
            )
