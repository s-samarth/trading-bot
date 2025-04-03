import os
import sys
import time
import json
from typing import Optional, Tuple
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import numpy as np

from config.Config import Config
from TradeLedger import TradeLedger
from API.Upstox.UpstoxLogin import Login as UpstoxLogin
from API.Upstox.Data import MarketQuoteData as UpstoxMarketQuoteData
from TradingStrategy.Template import StrategyTemplate
from TradingStrategy.ExecutionValidator import ExecutionValidator
from TradingStrategy.StrategyData import (
    BaseStrategyOutput,
    BaseStrategyInput,
    BaseStrategyParams,
)
from TradingStrategy.ApiConstantsMapping import UpstoxConstantsMapping
from TradingStrategy.Constants import (
    TradingMode,
    ExecutionFrequencyMode,
    Broker,
    BaseExchange,
    TradingSymbol,
    BaseSegment,
    TradeStatus,
    TradeAction,
)


class StrategyManager:
    """Manages the execution of a trading strategy.
    This class is responsible for executing the trading strategy,
    validating the execution, and handling any errors that may occur.
    It also provides methods for logging the execution status and
    generating reports.

    Parameters
    - strategy: StrategyTemplate
        The trading strategy to be executed.
    - strategy_input: BaseStrategyInput
        The input data for the trading strategy.
    - strategy_params: BaseStrategyParams
        The parameters for the trading strategy.
    - trade_ledger_file: str
        The file path for the trade ledger.
    - mode: TradingMode
        The trading mode (BACKTEST, LIVE, SIMULATION).
    - execution_frequency_mode: ExecutionFrequencyMode
        The execution frequency mode (CONSTANT, DYNAMIC).
        DYNAMIC execution is meant to save unnecessary API calls
        while being able to execute the strategy at a higher frequency
        when the LTP is close to the target price or stop loss price.
    - execution_frequency: Optional[float]
        The frequency of execution in a hour.
        Default is 10 per hour.
        This is only used when execution_frequency_mode is set to CONSTANT.
    - min_max_execution_frequency: Optional[Tuple[float, float]]
        The minimum and maximum execution frequency in hours.
        Default is (1/24, 30).
        This is only used when execution_frequency_mode is set to DYNAMIC.
    - error_cooldown_time: int
        The cooldown time in minutes after an error occurs.
        Default is 60 minutes.
    - strategy_cooldown_time: int
        The cooldown time in days after the strategy is executed.
        Default is 30 days.
    """

    def __init__(
        self,
        strategy: StrategyTemplate,
        strategy_input: BaseStrategyInput,
        strategy_params: BaseStrategyParams,
        trade_ledger_file: str = "",
        mode: TradingMode = TradingMode.BACKTEST,
        execution_frequency_mode: ExecutionFrequencyMode = ExecutionFrequencyMode.CONSTANT,
        execution_frequency: Optional[float] = 10,
        min_max_execution_frequency: Optional[Tuple[float, float]] = (1 / 24, 30),
        error_cooldown_time: int = 60,
        strategy_cooldown_time: int = 30,  # in days
    ):
        self.strategy: StrategyTemplate = strategy(strategy_input, strategy_params)
        self.strategy_input: BaseStrategyInput = strategy_input
        self.strategy_params: BaseStrategyParams = strategy_params
        self.trade_ledger = TradeLedger(trade_ledger_file)
        self.mode = mode
        self.execution_frequency_mode = execution_frequency_mode
        if execution_frequency_mode == ExecutionFrequencyMode.CONSTANT:
            self.execution_frequency = execution_frequency
            self.min_max_execution_frequency = None
        elif execution_frequency_mode == ExecutionFrequencyMode.DYNAMIC:
            self.execution_frequency = None
            self.min_max_execution_frequency = min_max_execution_frequency

        if mode == TradingMode.LIVE:
            self.broker = strategy_input.broker

        self.error_cooldown_time = (
            error_cooldown_time * 60
        )  # Convert minutes to seconds

        self.strategy_cooldown_time = strategy_cooldown_time * 24 * 60 * 60

    def run(self):
        """
        Run the trading strategy.
        This method is responsible for executing the trading strategy,
        validating the execution, and handling any errors that may occur.
        """
        if self.mode == TradingMode.LIVE:
            self.run_live()
        elif self.mode == TradingMode.BACKTEST:
            self.run_backtest(max_iterations=100)
        elif self.mode == TradingMode.SIMULATION:
            self.run_simulation(max_iterations=100)
        else:
            raise ValueError(f"Invalid trading mode: {self.mode}")

    async def run_async(self):
        """
        Run the trading strategy asynchronously.
        This method is responsible for executing the trading strategy asynchronously,
        validating the execution, and handling any errors that may occur.
        """
        raise NotImplementedError("Asynchronous execution is not implemented yet.")

    def run_live(self):
        """
        Run the trading strategy in live mode.
        This method is responsible for executing the trading strategy,
        validating the execution, and handling any errors that may occur.
        """

        last_cooldown_time = self.get_last_cooldown_time()
        cooldown_time_remaining = self.strategy_cooldown_time_remaining(
            last_cooldown_time=last_cooldown_time
        )
        if cooldown_time_remaining:
            time.sleep(cooldown_time_remaining)

        # Fetch access token
        access_token = self.fetch_access_token()

        strategy_output: BaseStrategyOutput = (
            None  # Need to fetch the last strategy output from the log file
        )
        holding_quantity = (
            0  # Need to fetch the last holding quantity from the log file
        )
        while True:
            # Fetch LTP
            ltp = self.fetch_ltp(
                access_token=access_token,
                exchange=self.strategy_input.exchange,
                trading_symbol=self.strategy_input.trading_symbol,
                trading_segment=self.strategy_input.segment,
            )

            # Set LTP in strategy input
            self.strategy_input.ltp = ltp

            # Re initialize the strategy with the updated LTP and parameters
            self.strategy.strategy_params = self.get_strategy_params(ltp=ltp)
            self.strategy.strategy_input = self.strategy_input

            self.strategy.holding_quantity = holding_quantity

            if strategy_output is None:
                strategy_output = self.strategy.execute()
            else:
                if strategy_output.trade_action == TradeAction.NO_ACTION:
                    strategy_output = self.strategy.execute()
                elif (
                    strategy_output.trade_action == TradeAction.HOLD
                    or strategy_output.trade_action == TradeAction.BUY
                ):
                    self.strategy.trade_status = TradeStatus.HOLDING
                    strategy_output = self.strategy.execute()
                elif strategy_output.trade_action == TradeAction.SELL:
                    self.strategy.trade_status = TradeStatus.NOT_TRIGGERED
                    strategy_output = self.strategy.execute()
                else:
                    raise ValueError(
                        f"Invalid trade action: {strategy_output.trade_action}"
                    )

            # Validate the execution
            execution_validator = ExecutionValidator(
                strategy_output=strategy_output,
            )
            if not execution_validator.validate():
                print("Execution validation failed.")
                time.sleep(self.error_cooldown_time)
                continue

            # Change Holding quantity if needed
            if strategy_output.trade_action == TradeAction.BUY:
                holding_quantity += strategy_output.quantity
            elif strategy_output.trade_action == TradeAction.SELL:
                holding_quantity -= strategy_output.quantity

            # Log the strategy output, implement the logging logic
            self.log_strategy_output(strategy_output, ltp)

            # Check if the strategy needs to go into cooldown mode
            if self.cooldown_strategy():
                cooldown_days = self.strategy_cooldown_time // (24 * 60 * 60)
                print(
                    f"Strategy is now going into cooldown mode for {cooldown_days} days."
                )
                time.sleep(self.strategy_cooldown_time)
                continue

            # Re Run after the wait time
            if self.execution_frequency_mode == ExecutionFrequencyMode.CONSTANT:
                frequency = self.execution_frequency
            elif self.execution_frequency_mode == ExecutionFrequencyMode.DYNAMIC:
                frequency = self.get_dynamic_execution_frequency(
                    ltp=ltp,
                    min_frequency=self.min_max_execution_frequency[0],
                    max_frequency=self.min_max_execution_frequency[1],
                )
            else:
                raise ValueError(
                    f"Invalid execution frequency mode: {self.execution_frequency_mode}"
                )
            wait_time = self.rerun_wait_time(frequency=frequency)
            time.sleep(wait_time)

    def run_backtest(self, max_iterations: int = 10_000_000):
        """
        Run the trading strategy in backtest mode.
        This method is responsible for executing the trading strategy,
        validating the execution, and handling any errors that may occur.
        """

        # NEED TO IMPLEMENT A BETTER COOLDOWN STATE CHECK LOGIC HERE AS THIS IS A BACKTEST

        # Placeholder for backtest logic
        print("Running Backtest")
        strategy_output: BaseStrategyOutput = (
            None  # Need to fetch the last strategy output from the log file
        )
        ltp = 1
        iteration = 1
        holding_quantity = 0
        while (
            ltp is not None and iteration < max_iterations
        ):  # Make LTP None in the end of backtest, implement the logic in get_ltp function
            iteration += 1

            # Fetch LTP
            ltp = self.fetch_ltp(
                access_token=None,
                exchange=self.strategy_input.exchange,
                trading_symbol=self.strategy_input.trading_symbol,
                trading_segment=self.strategy_input.segment,
            )

            # Set LTP in strategy input
            self.strategy_input.ltp = ltp

            # Re initialize the strategy with the updated LTP and parameters
            self.strategy.strategy_params = self.get_strategy_params(ltp=ltp)
            self.strategy.strategy_input = self.strategy_input

            self.strategy.holding_quantity = holding_quantity

            if strategy_output is None:
                strategy_output = self.strategy.execute()
            else:
                if strategy_output.trade_action == TradeAction.NO_ACTION:
                    strategy_output = self.strategy.execute()
                elif (
                    strategy_output.trade_action == TradeAction.HOLD
                    or strategy_output.trade_action == TradeAction.BUY
                ):
                    self.strategy.trade_status = TradeStatus.HOLDING
                    strategy_output = self.strategy.execute()
                elif strategy_output.trade_action == TradeAction.SELL:
                    self.strategy.trade_status = TradeStatus.NOT_TRIGGERED
                    strategy_output = self.strategy.execute()
                else:
                    raise ValueError(
                        f"Invalid trade action: {strategy_output.trade_action}"
                    )

            # Validate the execution
            execution_validator = ExecutionValidator(
                strategy_output=strategy_output,
            )
            if not execution_validator.validate():
                print("Execution validation failed.")
                time.sleep(self.error_cooldown_time)
                continue

            if strategy_output.trade_action == TradeAction.BUY:
                holding_quantity += strategy_output.quantity
            elif strategy_output.trade_action == TradeAction.SELL:
                holding_quantity -= strategy_output.quantity

            # Log the strategy output, implement the logging logic
            self.log_strategy_output(strategy_output, ltp, holding_quantity)

            # NEED TO IMPLEMENT A BETTER COOLDOWN STATE CHECK LOGIC HERE AS THIS IS A BACKTEST

            # No need to wait for the next iteration in backtest mode

        return

    def run_simulation(self, max_iterations: int = 10_000_000):
        """
        Run the trading strategy in simulation mode.
        This method is responsible for executing the trading strategy,
        validating the execution, and handling any errors that may occur.
        """
        return self.run_backtest(max_iterations=max_iterations)

    def get_strategy_params(self, ltp: float) -> BaseStrategyParams:
        """
        Get the strategy parameters based on the last traded price (LTP).
        This method is responsible for retrieving the strategy parameters
        based on the LTP and handling any errors that may occur.
        Override this method in the derived class to customize the strategy parameters.
        """
        return self.strategy_params

    def fetch_access_token(self):
        """
        Fetch the access token for the broker using the login method.
        This method is responsible for fetching the access token
        and handling any errors that may occur.
        """
        login_status = False
        while not login_status:
            try:
                access_token = self.broker_login()
                login_status = True
            except:
                print(
                    f"Error logging into broker. Retrying after cooldown of {self.error_cooldown_time // 60} minutes."
                )
                time.sleep(self.error_cooldown_time)
        return access_token

    def broker_login(self):
        """
        Log in to the broker.
        This method is responsible for logging in to the broker
        and handling any errors that may occur.
        """
        if self.mode == TradingMode.LIVE:
            if self.broker == Broker.UPSTOX:
                try:
                    access_token = UpstoxLogin().login()
                except Exception as e:
                    raise ValueError(f"Error logging into broker: {e}")
            else:
                raise NotImplementedError(
                    "Broker login is not implemented for this broker."
                )
        else:
            access_token = None
        return access_token

    def fetch_ltp(
        self,
        access_token: str,
        exchange: BaseExchange,
        trading_symbol: TradingSymbol,
        trading_segment: BaseSegment,
    ):
        """
        Fetch the last traded price (LTP) of the stock.
        This method is responsible for fetching the LTP of the stock
        from the get_ltp method and handling any errors that may occur.
        """
        ltp_present = False
        while not ltp_present:
            try:
                ltp = self.get_ltp(
                    access_token=access_token,
                    exchange=exchange,
                    trading_symbol=trading_symbol,
                    trading_segment=trading_segment,
                )
                ltp_present = True
            except Exception as e:
                print(f"Error fetching LTP: {e}")
                print(
                    f"Retrying after cooldown of {self.error_cooldown_time // 60} minutes."
                )
                time.sleep(self.error_cooldown_time)

        return ltp

    def get_ltp(
        self,
        access_token: str,
        exchange: BaseExchange,
        trading_symbol: TradingSymbol,
        trading_segment: BaseSegment,
    ):
        """
        Get the last traded price (LTP) of the stock.
        This method is responsible for retrieving the LTP of the stock
        and handling any errors that may occur.
        """
        if self.mode == TradingMode.LIVE:
            if self.broker == Broker.UPSTOX:
                try:
                    ltp_data = UpstoxMarketQuoteData(access_token=access_token).get_ltp(
                        exchange=UpstoxConstantsMapping.exchange(exchange),
                        trading_symbol=trading_symbol,
                    )
                    key = UpstoxConstantsMapping.exchange(exchange)
                    +"_"
                    +UpstoxConstantsMapping.segment(trading_segment)
                    +":"
                    +trading_symbol
                    ltp = ltp_data[key]["last_price"]
                    return ltp
                except Exception as e:
                    raise ValueError(f"Error fetching LTP: {e}")
            else:
                raise NotImplementedError(
                    "LTP fetching is not implemented for this broker."
                )
        else:
            # For backtesting or simulation, return a mock LTP
            # Need to Write the logic for backtesting LTP Fetching
            fake_ltp = np.random.uniform(100, 2000)  # Replace with actual logic
            return fake_ltp

    def log_strategy_output(
        self, strategy_output: BaseStrategyOutput, ltp, holding_quantity
    ):
        """
        Log the strategy output.
        This method is responsible for logging the strategy output
        and handling any errors that may occur.
        Placeholder for actual implementation.
        Write a batched implementation to log the strategy output
        """
        # Write the file to root_directory/TradingResults/Backtest as json file
        log_file = os.path.join(Config.root_dir, "TradingResults/Backtest/Results.json")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        if not os.path.exists(log_file):
            with open(log_file, "w") as f:
                json.dump([], f)

        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            output_dict = {
                "timestamp": timestamp,
                "trading_symbol": strategy_output.trading_symbol,
                "exchange": strategy_output.exchange,
                "trade_action": strategy_output.trade_action,
                "holding_quantity": holding_quantity,
                "trade_charges": strategy_output.trade_charges,
                "ltp": ltp,
                "trade_action": strategy_output.trade_action,
                "quantity": strategy_output.quantity,
                "execution_status": strategy_output.execution_status,
                "order_id": strategy_output.order_id,
                "information": strategy_output.information,
            }
            logs.append(output_dict)
            with open(log_file, "w") as f:
                json.dump(logs, f, indent=4)

        except Exception as e:
            print(f"Error logging strategy output: {e}")
            raise ValueError(f"Error logging strategy output: {e}")

    def get_last_cooldown_time(self) -> datetime:
        """
        Get the last cooldown time.
        This method is responsible for retrieving the last cooldown time
        and handling any errors that may occur.
        Placeholder for actual implementation.
        """
        return None

    def strategy_cooldown_time_remaining(
        self, last_cooldown_time: datetime = None
    ) -> int:
        """
        Check if the strategy is in cooldown mode.
        This method is responsible for checking if the strategy is in cooldown mode.
        """
        if last_cooldown_time:
            current_time = datetime.now()
            time_difference = current_time - last_cooldown_time
            if time_difference.total_seconds() < self.strategy_cooldown_time:
                days_left = time_difference.days
                hours_left = (time_difference.seconds // 3600) % 24
                minutes_left = (time_difference.seconds // 60) % 60
                seconds_left = time_difference.seconds % 60
                print(
                    f"Strategy is in cooldown mode. "
                    + f"Time left: {days_left} days, {hours_left} hours, "
                    + f"{minutes_left} minutes, {seconds_left} seconds."
                )
                return time_difference.total_seconds()
            else:
                return None
        else:
            return None

    def cooldown_strategy(self) -> bool:
        """
        Cool down the strategy after an error.
        This method is responsible for cooling down the strategy
        after an error occurs and handling any errors that may occur.
        This is a placeholder for the actual implementation.
        """
        return False

    def rerun_wait_time(self, frequency: float) -> int:
        """
        Calculate the wait time before rerunning the strategy.
        This method is responsible for calculating the wait time
        before rerunning the strategy and handling any errors that may occur.
        """
        # Ensure frequency is not None or zero
        if frequency is None or frequency == 0:
            raise ValueError("Frequency cannot be None or zero.")
        # Calculate wait time in seconds
        wait_time = 3600 / frequency
        # Round it to the nearest integer
        wait_time = int(wait_time)
        # Ensure wait time is at least 1 second
        if wait_time < 1:
            wait_time = 1
        return wait_time

    def get_dynamic_execution_frequency(
        self,
        ltp: float,
        min_frequency: float = 1 / 24,
        max_frequency: float = 30,
    ) -> float:
        """
        Get the dynamic execution frequency based on LTP and other factors.
        On a log scale, increasing the execution frequency from min_frequency
        to max_frequency based on the percentage closeness of LTP to the buy price
        or target price or stop loss price.
        """
        # Set Harmonic mean of min and max frequency as default frequency
        default_frequency = self._get_harmonic_mean(min_frequency, max_frequency)
        if min_frequency is None or max_frequency is None:
            return default_frequency

        # Get the buy price, target price, and stop loss price
        buy_price = self.strategy.get_buy_price()
        try:
            target_price = self.strategy.get_target_price(buy_price)
        except:
            target_price = None
        try:
            stop_loss_price = self.strategy.get_stop_loss_price(buy_price)
        except:
            stop_loss_price = None

        # Example logic to calculate dynamic execution frequency
        # This should be replaced with actual logic to calculate the frequency

        if self.strategy.trade_status == TradeStatus.NOT_TRIGGERED:
            ltp_buy_ratio = ltp / buy_price
            if ltp_buy_ratio <= 1:
                return max_frequency
            else:
                percentage_closeness = (ltp_buy_ratio - 1) * 100
                frequency = self.calculate_frequency(
                    min_frequency,
                    max_frequency,
                    percentage_closeness,
                )
                return frequency

        elif self.strategy.trade_status == TradeStatus.HOLDING:
            if target_price is None:
                return default_frequency

            ltp_target_ratio = ltp / target_price
            if ltp_target_ratio >= 1:
                return max_frequency
            else:
                percentage_closeness = (ltp_target_ratio - 1) * 100
                target_frequency = self.calculate_frequency(
                    min_frequency, max_frequency, percentage_closeness
                )

            if stop_loss_price is None:
                return default_frequency

            ltp_stop_loss_ratio = ltp / stop_loss_price
            if ltp_stop_loss_ratio <= 1:
                return max_frequency
            else:
                percentage_closeness = (ltp_stop_loss_ratio - 1) * 100
                stop_loss_frequency = self.calculate_frequency(
                    min_frequency, max_frequency, percentage_closeness
                )
                return max(target_frequency, stop_loss_frequency)

        return default_frequency

    @staticmethod
    def _get_harmonic_mean(value1, value2):
        """
        Calculate the harmonic mean of two values.
        """
        if value1 + value2 == 0:
            return 0
        return (2 * value1 * value2) / (value1 + value2)

    @staticmethod
    def calculate_frequency(
        min_frequency: float,
        max_frequency: float,
        current_value: float,
        penalization_exponent: float = 2,
        epsilon: float = 0.01,
    ) -> float:
        """
        Calculate the frequency based on the current value and penalization exponent.
        Penalisation exponent is there because we want to penalise ltp for being too
        far from the buy/trigger/stoploss price.
        """
        if min_frequency is None or max_frequency is None:
            return self._get_harmonic_mean(min_frequency, max_frequency)
        raw_frequency = 1 / (np.log1p(current_value + epsilon)) ** penalization_exponent
        max_raw_frequency = 1 / (np.log1p(epsilon) ** penalization_exponent)
        # Normalize the frequency to the range [min_frequency, max_frequency]
        frequency = min_frequency + (max_frequency - min_frequency) * (
            raw_frequency / max_raw_frequency
        )


if __name__ == "__main__":
    from TradingStrategy.MockStrategy import MockStrategy, MockStrategyParams

    strategy_input = BaseStrategyInput(trading_symbol=TradingSymbol("HDFCBANK"))
    strategy_params = MockStrategyParams(
        target_percent=4,
        stop_loss_percent=2,
        all_time_high=1000.5,
        allowed_strategy_capital=5000,
    )

    strategy_manager = StrategyManager(
        strategy=MockStrategy,
        strategy_input=strategy_input,
        strategy_params=strategy_params,
        mode=TradingMode.BACKTEST,
        error_cooldown_time=1,
    )
    start_time = time.time()
    strategy_manager.run()
    end_time = time.time()
    print(f"Strategy Manager took {end_time - start_time} seconds")
