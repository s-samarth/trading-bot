from enum import StrEnum
from typing import Dict, ClassVar


class TradingSymbol(StrEnum):
    """Supported trading symbols."""
    IDEA = "IDEA"
    HDFCBANK = "HDFCBANK"

    @classmethod
    def all_symbols(cls) -> Dict[str, str]:
        """Returns a dictionary of all trading symbols."""
        return {symbol.name: symbol.value for symbol in cls}


class BaseExchange(StrEnum):
    """Supported exchanges."""
    NSE = "NSE"
    BSE = "BSE"

    _descriptions: ClassVar[Dict[str, str]] = {
        "NSE": "Represents equities traded on the National Stock Exchange.",
        "BSE": "Represents equities traded on the Bombay Stock Exchange.",
    }

    def description(self) -> str:
        """Returns the description of the exchange."""
        return self._descriptions.get(self.value, "Unknown Exchange")

    @classmethod
    def all_descriptions(cls) -> Dict[str, str]:
        """Returns a dictionary of all exchange descriptions."""
        return {exchange.value: exchange.description() for exchange in cls}


class BaseTransactionType(StrEnum):
    """Supported transaction types."""
    BUY = "BUY"
    SELL = "SELL"

    _descriptions: ClassVar[Dict[str, str]] = {
        "BUY": "Indicates a purchase of securities.",
        "SELL": "Indicates a sale of securities.",
    }

    def description(self) -> str:
        """Returns the description of the transaction type."""
        return self._descriptions.get(self.value, "Unknown Transaction Type")

    @classmethod
    def all_descriptions(cls) -> Dict[str, str]:
        """Returns a dictionary of all transaction type descriptions."""
        return {transaction.value: transaction.description() for transaction in cls}


class BaseProductType(StrEnum):
    """Supported product types."""
    INTRADAY = "INTRADAY"
    DELIVERY = "DELIVERY"
    COVERORDER = "COVERORDER"
    MARGINTRADINGFACILITY = "MARGINTRADINGFACILITY"

    _descriptions: ClassVar[Dict[str, str]] = {
        "INTRADAY": "Represents intraday trading.",
        "DELIVERY": "Represents delivery-based trading.",
        "COVERORDER": "Represents cover order trading.",
        "MARGINTRADINGFACILITY": "Represents margin trading facility.",
    }

    def description(self) -> str:
        """Returns the description of the product type."""
        return self._descriptions.get(self.value, "Unknown Product Type")

    @classmethod
    def all_descriptions(cls) -> Dict[str, str]:
        """Returns a dictionary of all product type descriptions."""
        return {product.value: product.description() for product in cls}


class BaseOrderType(StrEnum):
    """Supported order types."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOPLOSS = "STOPLOSS"
    STOPLOSS_MARKET = "STOPLOSS_MARKET"

    _descriptions: ClassVar[Dict[str, str]] = {
        "MARKET": "Market order at the current market price.",
        "LIMIT": "Limit order at a specified price.",
        "STOPLOSS": "Stop-loss order at a specified price.",
        "STOPLOSS_MARKET": "Stop-loss market order.",
    }

    def description(self) -> str:
        """Returns the description of the order type."""
        return self._descriptions.get(self.value, "Unknown Order Type")

    @classmethod
    def all_descriptions(cls) -> Dict[str, str]:
        """Returns a dictionary of all order type descriptions."""
        return {order.value: order.description() for order in cls}
