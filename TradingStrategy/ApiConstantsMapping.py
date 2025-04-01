import os
import sys
from typing import Type, TypeVar, ClassVar

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import TradingStrategy.Constants as BaseConstants
import API.Upstox.Constants as UpstoxConstants

T = TypeVar('T')

class UpstoxConstantsMapping:
    """
    Maps base trading constants to Upstox-specific constants.
    Provides type-safe mapping between base and Upstox constants.
    """

    _mapping_cache: ClassVar[dict] = {}

    @classmethod
    def _get_cached_mapping(cls, base_enum: Type[T], upstox_enum: Type[T], name: str) -> T:
        """
        Get cached mapping or create new one.
        
        Args:
            base_enum: Base enum class
            upstox_enum: Upstox enum class
            name: Name of the enum value
            
        Returns:
            Mapped Upstox enum value
            
        Raises:
            AttributeError: If mapping doesn't exist
        """
        cache_key = f"{base_enum.__name__}_{name}"
        if cache_key not in cls._mapping_cache:
            try:
                cls._mapping_cache[cache_key] = getattr(upstox_enum, name)
            except AttributeError:
                raise AttributeError(f"No mapping found for {name} in {upstox_enum.__name__}")
        return cls._mapping_cache[cache_key]

    @classmethod
    def transaction_type(
        cls, transaction_type: BaseConstants.BaseTransactionType
    ) -> UpstoxConstants.TransactionType:
        """
        Maps the transaction type from Base constants to Upstox constants.
        
        Args:
            transaction_type: The transaction type from Base constants
            
        Returns:
            The mapped transaction type from Upstox constants
            
        Raises:
            AttributeError: If mapping doesn't exist
        """
        return cls._get_cached_mapping(
            BaseConstants.BaseTransactionType,
            UpstoxConstants.TransactionType,
            transaction_type.name
        )

    @classmethod
    def exchange(
        cls, exchange: BaseConstants.BaseExchange
    ) -> UpstoxConstants.Exchange:
        """
        Maps the exchange from Base constants to Upstox constants.
        
        Args:
            exchange: The exchange from Base constants
            
        Returns:
            The mapped exchange from Upstox constants
            
        Raises:
            AttributeError: If mapping doesn't exist
        """
        return cls._get_cached_mapping(
            BaseConstants.BaseExchange,
            UpstoxConstants.Exchange,
            exchange.name
        )

    @classmethod
    def product_type(
        cls, product_type: BaseConstants.BaseProductType
    ) -> UpstoxConstants.ProductType:
        """
        Maps the product type from Base constants to Upstox constants.
        
        Args:
            product_type: The product type from Base constants
            
        Returns:
            The mapped product type from Upstox constants
            
        Raises:
            AttributeError: If mapping doesn't exist
        """
        return cls._get_cached_mapping(
            BaseConstants.BaseProductType,
            UpstoxConstants.ProductType,
            product_type.name
        )

    @classmethod
    def order_type(
        cls, order_type: BaseConstants.BaseOrderType
    ) -> UpstoxConstants.OrderType:
        """
        Maps the order type from Base constants to Upstox constants.
        
        Args:
            order_type: The order type from Base constants
            
        Returns:
            The mapped order type from Upstox constants
            
        Raises:
            AttributeError: If mapping doesn't exist
        """
        return cls._get_cached_mapping(
            BaseConstants.BaseOrderType,
            UpstoxConstants.OrderType,
            order_type.name
        )


def test_mappings() -> None:
    """Test all constant mappings."""
    try:
        # Test transaction type mapping
        transaction_type = BaseConstants.BaseTransactionType.SELL
        mapped_transaction_type = UpstoxConstantsMapping.transaction_type(transaction_type)
        print(f"✅ Transaction Type Mapping: {transaction_type} -> {mapped_transaction_type}")

        # Test exchange mapping
        exchange = BaseConstants.BaseExchange.BSE
        mapped_exchange = UpstoxConstantsMapping.exchange(exchange)
        print(f"✅ Exchange Mapping: {exchange} -> {mapped_exchange}")

        # Test product type mapping
        product_type = BaseConstants.BaseProductType.INTRADAY
        mapped_product_type = UpstoxConstantsMapping.product_type(product_type)
        print(f"✅ Product Type Mapping: {product_type} -> {mapped_product_type}")

        # Test order type mapping
        order_type = BaseConstants.BaseOrderType.MARKET
        mapped_order_type = UpstoxConstantsMapping.order_type(order_type)
        print(f"✅ Order Type Mapping: {order_type} -> {mapped_order_type}")

        print("\n✅ All mappings tested successfully!")
    except Exception as e:
        print(f"❌ Error testing mappings: {str(e)}")
        raise


if __name__ == "__main__":
    test_mappings()
