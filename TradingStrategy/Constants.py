from enum import StrEnum

class TradingSymbol(StrEnum):
    IDEA = "IDEA"
    HDFCBANK = "HDFCBANK"


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
            "SELL": "Indicates a sale of securities."
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
            "MARGINTRADINGFACILITY": "Represents margin trading facility."
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
            "STOPLOSS_MARKET": "Stop-loss market order."
        }
        return descriptions.get(self.value, "Unknown Order Type")
    
    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all order type descriptions.
        """
        return {order.value: order.description() for order in cls}