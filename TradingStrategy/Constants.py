from enum import StrEnum


class Broker(StrEnum):
    ZERODHA = "ZERODHA"
    UPSTOX = "UPSTOX"
    ANGELONE = "ANGELONE"

    def description(self) -> str:
        descriptions = {
            "ZERODHA": "Represents Zerodha broker.",
            "UPSTOX": "Represents Upstox broker.",
            "ANGELONE": "Represents Angel One broker.",
        }
        return descriptions.get(self.value, "Unknown Broker")

    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all broker descriptions.
        """
        return {broker.value: broker.description() for broker in cls}


class TradingSymbol(StrEnum):
    IDEA = "IDEA"
    HDFCBANK = "HDFCBANK"

    def description(self) -> str:
        descriptions = {
            "IDEA": "Represents the trading symbol for Idea Cellular.",
            "HDFCBANK": "Represents the trading symbol for HDFC Bank.",
        }
        return descriptions.get(self.value, "Unknown Trading Symbol")

    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all trading symbol descriptions.
        """
        return {symbol.value: symbol.description() for symbol in cls}


class TradeStatus(StrEnum):
    PROFIT = "PROFIT"
    LOSS = "LOSS"
    HOLD = "HOLD"
    NOT_TRIGGERED = "NOT_TRIGGERED"

    def description(self) -> str:
        descriptions = {
            "PROFIT": "Indicates a profitable trade.",
            "LOSS": "Indicates a loss-making trade.",
            "HOLD": "Indicates a trade that is currently held.",
            "NOT_TRIGGERED": "Indicates a trade that has not been triggered.",
        }
        return descriptions.get(self.value, "Unknown Trade Status")

    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all trade status descriptions.
        """
        return {status.value: status.description() for status in cls}


class BaseExchange(StrEnum):
    NSE = "NSE"
    BSE = "BSE"

    def description(self) -> str:
        self.descriptions = {
            "NSE": "Represents equities traded on the National Stock Exchange.",
            "BSE": "Represents equities traded on the Bombay Stock Exchange.",
        }
        return self.descriptions.get(self.value, "Unknown Exchange")

    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all exchange descriptions.
        """
        return {exchange.value: exchange.description() for exchange in cls}


class BaseTransactionType(StrEnum):
    BUY = "BUY"
    SELL = "SELL"

    def description(self) -> str:
        descriptions = {
            "BUY": "Indicates a purchase of securities.",
            "SELL": "Indicates a sale of securities.",
        }
        return descriptions.get(self.value, "Unknown Transaction Type")

    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all transaction type descriptions.
        """
        return {transaction.value: transaction.description() for transaction in cls}


class BaseProductType(StrEnum):
    INTRADAY = "INTRADAY"
    DELIVERY = "DELIVERY"
    COVERORDER = "COVERORDER"
    MARGINTRADINGFACILITY = "MARGINTRADINGFACILITY"

    def description(self) -> str:
        descriptions = {
            "INTRADAY": "Represents intraday trading.",
            "DELIVERY": "Represents delivery-based trading.",
            "COVERORDER": "Represents cover order trading.",
            "MARGINTRADINGFACILITY": "Represents margin trading facility.",
        }
        return descriptions.get(self.value, "Unknown Product Type")

    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all product type descriptions.
        """
        return {product.value: product.description() for product in cls}


class BaseOrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOPLOSS = "STOPLOSS"
    STOPLOSS_MARKET = "STOPLOSS_MARKET"

    def description(self) -> str:
        descriptions = {
            "MARKET": "Market order at the current market price.",
            "LIMIT": "Limit order at a specified price.",
            "STOPLOSS": "Stop-loss order at a specified price.",
            "STOPLOSS_MARKET": "Stop-loss market order.",
        }
        return descriptions.get(self.value, "Unknown Order Type")

    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all order type descriptions.
        """
        return {order.value: order.description() for order in cls}


class BaseOrderStatus(StrEnum):
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    OPEN_PENDING = "OPEN_PENDING"
    VALIDATION_PENDING = "VALIDATION_PENDING"
    # Add more statuses as needed

    def description(self) -> str:
        descriptions = {
            "OPEN": "Order is open and active.",
            "COMPLETE": "Order has been executed.",
            "CANCELLED": "Order has been cancelled.",
            "REJECTED": "Order has been rejected.",
            "OPEN_PENDING": "Order is pending to be opened.",
            "VALIDATION_PENDING": "Order is pending validation.",
        }
        return descriptions.get(self.value, "Unknown Order Status")

    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all order status descriptions.
        """
        return {status.value: status.description() for status in cls}
