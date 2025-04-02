import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import TradingStrategy.Constants as BaseConstants
import API.Upstox.Constants as UpstoxConstants


class UpstoxConstantsMapping:
    """
    This class is used to map Upstox constants to Base constants.
    """

    def __init__(self):
        pass

    @classmethod
    def transaction_type(
        cls, transaction_type: BaseConstants.BaseTransactionType
    ) -> UpstoxConstants.TransactionType:
        """
        Maps the transaction type from Base constants to Upstox constants.
        Args:
            transaction_type (BaseTransactionType): The transaction type from Base constants.
        Returns:
            TransactionType: The mapped transaction type from Upstox constants.
        """
        return getattr(UpstoxConstants.TransactionType, transaction_type.name)

    @classmethod
    def exchange(cls, exchange: BaseConstants.BaseExchange) -> UpstoxConstants.Exchange:
        """
        Maps the exchange from Base constants to Upstox constants.
        Args:
            exchange (BaseExchange): The exchange from Base constants.
        Returns:
            Exchange: The mapped exchange from Upstox constants.
        """
        return getattr(UpstoxConstants.Exchange, exchange.name)

    @classmethod
    def product_type(
        cls, product_type: BaseConstants.BaseProductType
    ) -> UpstoxConstants.ProductType:
        """
        Maps the product type from Base constants to Upstox constants.
        Args:
            product_type (BaseProductType): The product type from Base constants.
        Returns:
            ProductType: The mapped product type from Upstox constants.
        """
        return getattr(UpstoxConstants.ProductType, product_type.name)

    @classmethod
    def order_type(
        cls, order_type: BaseConstants.BaseOrderType
    ) -> UpstoxConstants.OrderType:
        """
        Maps the order type from Base constants to Upstox constants.
        Args:
            order_type (BaseOrderType): The order type from Base constants.
        Returns:
            OrderType: The mapped order type from Upstox constants.
        """
        return getattr(UpstoxConstants.OrderType, order_type.name)


if __name__ == "__main__":
    # Example usage for transaction type
    transaction_type = BaseConstants.BaseTransactionType.SELL
    mapped_transaction_type = UpstoxConstantsMapping.transaction_type(transaction_type)
    print(f"Mapped Transaction Type: {mapped_transaction_type}")

    # Example usage for exchange
    exchange = BaseConstants.BaseExchange.BSE
    mapped_exchange = UpstoxConstantsMapping.exchange(exchange)
    print(f"Mapped Exchange: {mapped_exchange}")

    # Example usage for product type
    product_type = BaseConstants.BaseProductType.INTRADAY
    mapped_product_type = UpstoxConstantsMapping.product_type(product_type)
    print(f"Mapped Product Type: {mapped_product_type}")

    # Example usage for order type
    order_type = BaseConstants.BaseOrderType.MARKET
    mapped_order_type = UpstoxConstantsMapping.order_type(order_type)
    print(f"Mapped Order Type: {mapped_order_type}")
