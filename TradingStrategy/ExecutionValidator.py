from TradingStrategy.StrategyData import BaseStrategyOutput


class ExecutionValidator:
    """
    This class is used to validate the execution of the trading strategy.
    It includes methods for checking if the strategy is actually Executed,
    without any errors.
    """

    def __init__(self, strategy_output: BaseStrategyOutput):
        """
        Initializes the ExecutionValidator with the strategy output.
        Args:
            strategy_output (BaseStrategyOutput): The output of the trading strategy.
        """
        self.strategy_output = strategy_output

    def validate(self):
        """
        Validates all the validation checks.
        This method should be called to perform all the validation checks
        on the trading strategy output.
        """
        return True

    def validate_execution(self):
        """
        Validate the execution of the trading strategy.
        This method should check if the strategy was executed without any errors.
        """
        pass

    def validate_access_token(self):
        """
        Validate the access token.
        This method should check if the access token is valid and not expired.
        If the token is invalid or expired, it should regenerate the access token.
        """
        pass

    def regenerate_access_token(self):
        """
        Regenerate the access token.
        This method should be implemented to regenerate the access token
        if it is invalid or expired.
        """
        pass

    def validate_order_id(self, order_id: str) -> bool:
        """
        Validate the order ID.
        Args:
            order_id (str): The order ID to validate.
        Returns:
            bool: True if the order ID is valid, False otherwise.
        """
        pass

    def validate_trade_action(self, trade_action: str) -> bool:
        """
        Validate the trade action.
        Args:
            trade_action (str): The trade action to validate.
        Returns:
            bool: True if the trade action is valid, False otherwise.
        """
        pass

    def validate_trade_quantity(self, quantity: int) -> bool:
        """
        Validate the trade quantity.
        Args:
            quantity (int): The trade quantity to validate.
        Returns:
            bool: True if the trade quantity is valid, False otherwise.
        """
        pass
