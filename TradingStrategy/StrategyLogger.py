import os
import json
import asyncio
import threading
from typing import Optional
from datetime import datetime

import aiofiles

from config.Config import Config
from TradingStrategy.StrategyData import (
    BaseStrategyInput,
    BaseStrategyOutput,
    BaseStrategyParams,
    BaseStrategyManagerState,
)
from TradingStrategy.Constants import (
    TradingSymbol,
    TradingMode,
)


class StrategyLogger:
    def __init__(
        self,
        strategy_name: str,
        trading_symbol: TradingSymbol,
        trading_mode: TradingMode,
        reset_logger: bool = False,
        log_file_path: Optional[str] = None,
        verbose: bool = False,
    ):
        self.logs = []
        self.strategy_name = strategy_name
        self.trading_symbol = trading_symbol
        self.trading_mode = trading_mode
        self.reset_logger = reset_logger
        self.verbose = verbose
        if log_file_path is None:
            filename = (
                "TradingResults/"
                + trading_mode
                + "/"
                + strategy_name
                + "/Results_"
                + trading_symbol
                + ".json"
            )
            self.log_file_path = os.path.join(Config.root_dir, filename)
        else:
            self.log_file_path = log_file_path

        self.output_id = 0

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)

        # Create the log file if it doesn't exist or reset_logger is True
        if not os.path.exists(self.log_file_path) or reset_logger:
            with open(self.log_file_path, "w") as f:
                json.dump([], f, indent=4)
        else:
            # If the file exists and reset_logger is False, read the existing logs
            with open(self.log_file_path, "r") as f:
                self.logs = json.load(f)
                self.output_id = self.logs[-1]["output_id"] + 1

    def log_strategy_output(
        self,
        strategy_name: str,
        strategy_input: BaseStrategyInput,
        strategy_output: BaseStrategyOutput,
        strategy_params: BaseStrategyParams,
        strategy_manager_state: BaseStrategyManagerState,
        batch_size: int = 10,
    ):
        """
        Logs the strategy output to a JSON file.
        """
        try:
            self.output_id += 1
            if self.verbose:
                log_entry = self._get_log_entry(
                    strategy_name,
                    strategy_input,
                    strategy_output,
                    strategy_params,
                    strategy_manager_state,
                )
            else:
                if (
                    strategy_output.trade_action == "BUY"
                    or strategy_output.trade_action == "SELL"
                ):
                    log_entry = self._get_log_entry(
                        strategy_name,
                        strategy_input,
                        strategy_output,
                        strategy_params,
                        strategy_manager_state,
                    )
                else:
                    log_entry = None
            if log_entry:
                self.logs.append(log_entry)

                if len(self.logs) >= batch_size:
                    # Write the logs to the file in batches
                    with open(self.log_file_path, "r") as f:
                        existing_logs = json.load(f)

                    existing_logs.extend(self.logs)
                    with open(self.log_file_path, "w") as f:
                        json.dump(existing_logs, f, indent=4)

                    # Clear the logs after writing
                    self.logs.clear()

        except Exception as e:
            print(f"Error logging the Strategy Results: {e}")
            raise ValueError(f"Error logging the Strategy Results: {e}")

    def end_logging(self):
        """
        Flushes any remaining logs to the file.
        """
        try:
            if self.logs:
                with open(self.log_file_path, "r") as f:
                    existing_logs = json.load(f)

                existing_logs.extend(self.logs)
                with open(self.log_file_path, "w") as f:
                    json.dump(existing_logs, f, indent=4)

                # Clear the logs after writing
                self.logs.clear()

        except Exception as e:
            print(f"Error ending logging: {e}")
            raise ValueError(f"Error ending logging: {e}")

    def _get_log_entry(
        self,
        strategy_name: str,
        strategy_input: BaseStrategyInput,
        strategy_output: BaseStrategyOutput,
        strategy_params: BaseStrategyParams,
        strategy_manager_state: BaseStrategyManagerState,
    ):
        """
        Gets a log entry for the strategy
        """
        timpestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = {
            "timestamp": timpestamp,
            "output_id": self.output_id,
            "strategy_name": strategy_name,
            "trading_symbol": strategy_input.trading_symbol,
            "exchange": strategy_input.exchange,
            "product_type": strategy_input.product_type,
            "segment": strategy_input.segment,
            "order_type": strategy_input.order_type,
            "ltp": strategy_manager_state.ltp,
            "trade_action": strategy_output.trade_action,
            "quantity": strategy_manager_state.holding_quantity,
            "trade_charges": strategy_output.trade_charges,
            "execution_status": strategy_output.execution_status,
            "order_id": strategy_output.order_id,
            "trading_mode": strategy_manager_state.trading_mode,
            "buy_price_executed": strategy_manager_state.buy_price_executed,
            "target_price_at_buy_time": strategy_manager_state.target_price_at_buy_time,
            "stop_loss_price_at_buy_time": strategy_manager_state.stop_loss_price_at_buy_time,
            "sell_price_executed": strategy_manager_state.sell_price_executed,
            "strategy_params": strategy_params.model_dump(),
            "broker": strategy_manager_state.broker,
            "cooldown_status": strategy_manager_state.cooldown_status,
            "cooldown_timestamp": strategy_manager_state.cooldown_timestamp,
            "information": strategy_output.information,
        }
        return log_entry
