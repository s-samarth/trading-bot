from TradingStrategy.StrategyData import BaseStrategyOutput

from TradingStrategy.Constants import ExecutionStatus


class ExecutionValidator:
    """
    This class is used to validate the execution of the trading strategy.
    It includes methods for checking if the strategy is actually Executed,
    without any errors.
    """

    def __init__(self):
        pass

    def validate_execution(self, strategy_output: BaseStrategyOutput) -> bool:
        """
        Validate the execution of the trading strategy.
        Args:
            strategy_output (BaseStrategyOutput): The output of the trading strategy.
        Returns:
            bool: True if the execution is valid, False otherwise.
        """
        # Check if the execution status is SUCCESS
        if strategy_output.execution_status == ExecutionStatus.SUCCESS:
            return True
        else:
            return False
