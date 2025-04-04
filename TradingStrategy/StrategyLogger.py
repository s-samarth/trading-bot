import asyncio
import threading
import json
import os
from datetime import datetime

import aiofiles

from config.Config import Config
from TradingStrategy.StrategyData import BaseStrategyOutput


# Module is filled with bugs and errors, and is not working as intended.
# Needs to be fixed and refactored.
class AsyncStrategyLogger:
    def __init__(self, root_dir=Config.root_dir, batch_size=10, flush_interval=5):
        self.log_file = os.path.join(root_dir, "TradingResults/Backtest/Results.json")
        self.batch_size = batch_size  # ✅ Controls when to flush logs
        self.flush_interval = flush_interval  # ✅ Auto flush interval (seconds)
        self.log_buffer = []
        self.lock = asyncio.Lock()  # ✅ Prevent race conditions in async

        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        # 🚀 New: Add stop signal + task handle
        self.stop_event = asyncio.Event()
        # Start auto-flush task
        self.auto_flush_task = asyncio.create_task(self._auto_flush_async())

    async def log_strategy_output_async(
        self, strategy_output: BaseStrategyOutput, ltp, holding_quantity
    ):
        """
        Logs the strategy output asynchronously using batching.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        output_dict = {
            "timestamp": timestamp,
            "trading_symbol": strategy_output.trading_symbol,
            "exchange": strategy_output.exchange,
            "trade_action": strategy_output.trade_action,
            "holding_quantity": holding_quantity,
            "trade_charges": strategy_output.trade_charges,
            "ltp": ltp,
            "quantity": strategy_output.quantity,
            "execution_status": strategy_output.execution_status,
            "order_id": strategy_output.order_id,
            "information": strategy_output.information,
        }

        async with self.lock:
            self.log_buffer.append(output_dict)

            # ✅ Flush when batch is full
            if len(self.log_buffer) >= self.batch_size:
                await self._flush_logs_async()

    async def _flush_logs_async(self):
        """
        Flushes the log buffer to the file asynchronously.
        """
        if not self.log_buffer:
            return

        async with self.lock:
            try:
                # Load existing logs
                if os.path.exists(self.log_file):
                    async with aiofiles.open(self.log_file, "r") as f:
                        content = await f.read()
                        logs = json.loads(content) if content else []
                else:
                    logs = []

                # Append new logs
                logs.extend(self.log_buffer)
                self.log_buffer.clear()  # ✅ Clear buffer after writing

                # Write back to file
                async with aiofiles.open(self.log_file, "w") as f:
                    await f.write(json.dumps(logs, indent=4))

            except Exception as e:
                print(f"Error logging strategy output: {e}")

    async def _auto_flush_async(self):
        try:
            while not self.stop_event.is_set():
                await asyncio.sleep(self.flush_interval)
                await self._flush_logs_async()
        except asyncio.CancelledError:
            pass  # Handle graceful exit if needed

    async def stop_logger_async(self):
        """
        Gracefully stop the logger: stop flushing, flush remaining logs, release resources.
        """
        self.stop_event.set()
        await self.auto_flush_task  # Wait for flush task to end
        await self._flush_logs_async()
        print("Logger stopped and all resources released.")


class SyncStrategyLogger:
    def __init__(self, root_dir=Config.root_dir, batch_size=10, flush_interval=5):
        self.logger = AsyncStrategyLogger(root_dir, batch_size, flush_interval)

        # Create a new event loop for async operations
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_event_loop, daemon=True)
        self.thread.start()

        # Event to track if the loop is running
        self.loop_running = True

        # Start auto-flush task in the background
        self.auto_flush_task = asyncio.run_coroutine_threadsafe(
            self.logger._auto_flush_async(), self.loop
        )

    def _start_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def log_strategy_output(self, strategy_output, ltp, holding_quantity):
        """
        Runs the async log function inside the background event loop.
        """
        if not self.loop_running:
            raise RuntimeError("Cannot log: Event loop is not running.")

        future = asyncio.run_coroutine_threadsafe(
            self.logger.log_strategy_output_async(
                strategy_output, ltp, holding_quantity
            ),
            self.loop,
        )
        return future.result()

    def stop_logger(self):
        """
        Stops the logger, flushes logs, cancels tasks, and shuts down the event loop.
        """
        if not self.loop_running:
            return  # Already stopped

        try:
            # ✅ Cancel the auto-flush task
            if self.auto_flush_task:
                self.auto_flush_task.cancel()

            # ✅ Flush any remaining logs before stopping
            asyncio.run_coroutine_threadsafe(
                self.logger._flush_logs_async(), self.loop
            ).result()

            # ✅ Call async stop method in AsyncStrategyLogger
            asyncio.run_coroutine_threadsafe(
                self.logger.stop_logger_async(), self.loop
            ).result()

            # ✅ Stop the event loop safely
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.loop_running = False  # Mark loop as stopped
            self.thread.join()  # Wait for thread to exit

        except Exception as e:
            print(f"Error stopping logger: {e}")

        print("Logger stopped gracefully.")
