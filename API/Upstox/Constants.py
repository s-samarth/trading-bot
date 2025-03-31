from enum import StrEnum

class Exchange(StrEnum):
    NSE = "NSE" 
    BSE = "BSE"
    NFO = "NFO"
    BFO = "BFO"
    CDS = "CDS"
    BCD = "BCD"
    NSCOM = "NSCOM"
    MCX = "MCX"

    def description(self) -> str:
        self.descriptions = {
            "NSE": "Represents equities traded on the National Stock Exchange.",
            "BSE": "Represents equities traded on the Bombay Stock Exchange.",
            "NFO": "Futures and options segment of the National Stock Exchange.",
            "BFO": "Futures and options segment of the Bombay Stock Exchange.",
            "CDS": "Currency derivatives segment for forex futures and options.",
            "BCD": "Commodity derivatives trading on the Bombay Stock Exchange.",
            "NSCOM": "Commodity derivatives trading on National Stock Exchange.",
            "MCX": "Commodity futures trading on the Multi Commodity Exchange."
        }
        return self.descriptions.get(self.value, "Unknown Exchange")
    
    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all exchange descriptions.
        """
        return {exchange.value: exchange.description() for exchange in cls}
    

class TransactionType(StrEnum):
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
    

class ProductType(StrEnum):
    INTRADAY = "I"
    DELIVERY = "D"
    COVERORDER = "CO"
    MARGINTRADINGFACILITY = "MTF"

    def description(self) -> str:
        descriptions = {
            "I": "Intraday trading where positions are squared off within the same trading day.",
            "D": "Delivery trading where securities are bought or sold for delivery.",
            "CO": "Intraday trading order that combines a market or limit order with a compulsory stop-loss order",
            "MTF": "Allows investors to buy stocks by paying only a fraction of the total transaction value, with the broker funding the remaining amount"
        }
        return descriptions.get(self.value, "Unknown Product Type")
    
    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all product type descriptions.
        """
        return {product.value: product.description() for product in cls}
    

class Segment(StrEnum):
    EQUITY = "EQ"
    FUTUREOPTION = "FO"
    COMMODITY = "COM"
    CURRENCYDERIVATIVE = "CD"

    def description(self) -> str:
        descriptions = {
            "EQUITY": "Equity segment for trading stocks.",
            "FUTUREOPTION": "Futures and options segment for derivatives trading.",
            "COMMODITY": "Commodity segment for trading commodities.",
            "CURRENCYDERIVATIVE": "Currency derivatives segment for forex trading."
        }
        return descriptions.get(self.value, "Unknown Segment")
    
    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all segment descriptions.
        """
        return {segment.value: segment.description() for segment in cls}


class EquitySecurityType(StrEnum):
    SME = "SME"
    RELIST = "RELIST"
    PCA = "PCA"
    IPO = "IPO"
    NORMAL = "NORMAL"

    def description(self) -> str:
        descriptions = {
            "SME": "Equity that caters to small and medium-sized enterprises for market access.",
            "RELIST": "Equity that has been reintroduced to trading on the market after a period of absence.",
            "PCA": "Equity subject to regulatory oversight due to financial or operational concerns.",
            "IPO": "Equity initially offered to the public by a company entering the market.",
            "NORMAL": "Equity that operates under standard market conditions without special classifications."
        }
        return descriptions.get(self.value, "Unknown Security Type")
    
    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all security type descriptions.
        """
        return {security.value: security.description() for security in cls}


class MarketStatus(StrEnum):
    NORMAL_OPEN = "NORMAL_OPEN"
    NORMAL_CLOSE = "NORMAL_CLOSE"
    PRE_OPEN_START = "PRE_OPEN_START"
    PRE_OPEN_END = "PRE_OPEN_END"
    CLOSING_START = "CLOSING_START"
    CLOSING_END = "CLOSING_END"

    def description(self) -> str:
        descriptions = {
            "NORMAL_OPEN": "Indicates the start of a normal trading session.",
            "NORMAL_CLOSE": "Marks the end of a normal trading session.",
            "PRE_OPEN_START": "Marks the beginning of the pre-market session.",
            "PRE_OPEN_END": "Indicates the end of the pre-market session.",
            "CLOSING_START": "Marks the start of the closing phase.",
            "CLOSING_END": "Indicates the end of the closing phase."
        }
        return descriptions.get(self.value, "Unknown Market Status")
    
    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all market status descriptions.
        """
        return {status.value: status.description() for status in cls}
    

class OrderStatus(StrEnum):
    VALIDATION_PENDING = "validation pending"
    MODIFY_PENDING = "modify pending"
    TRIGGER_PENDING = "trigger pending"
    PUT_ORDER_REQ_RECEIVED = "put order req received"
    MODIFY_AFTER_MARKET_ORDER_REQ_RECEIVED = "modify after market order req received"
    CANCELLED_AFTER_MARKET_ORDER = "cancelled after market order"
    OPEN = "open"
    COMPLETE = "complete"
    MODIFY_VALIDATION_PENDING = "modify validation pending"
    AFTER_MARKET_ORDER_REQ_RECEIVED = "after market order req received"
    MODIFIED = "modified"
    NOT_CANCELLED = "not cancelled"
    CANCEL_PENDING = "cancel pending"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    OPEN_PENDING = "open pending"
    NOT_MODIFIED = "not modified"

    def description(self) -> str:
        descriptions = {
            "validation pending": "The order has been received and is awaiting validation.",
            "modify pending": "A request to modify the order has been initiated and is pending.",
            "trigger pending": "The order is awaiting a trigger to move it to the market.",
            "put order req received": "The request to place a new order has been received.",
            "modify after market order req received": "A modification request for an after-market order has been received.",
            "cancelled after market order": "The after-market order has been cancelled.",
            "open": "The order is active and open in the market.",
            "complete": "The order has been fully executed.",
            "modify validation pending": "A modification request has been received and is pending validation.",
            "after market order req received": "A new after-market order request has been received.",
            "modified": "The order has been successfully modified.",
            "not cancelled": "The request for cancellation was not processed; the order remains active.",
            "cancel pending": "The order is in the process of cancellation but the cancellation is not yet confirmed.",
            "rejected": "The order was not accepted and has been rejected by the exchange.",
            "cancelled": "The order has been successfully cancelled.",
            "open pending": "The order has been received and is pending opening.",
            "not modified": "The request for modification was not processed; the order remains in its original state."
        }
        return descriptions.get(self.value, "Unknown Order Status")

    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all order status descriptions.
        """
        return {status.value: status.description() for status in cls}


class HistoricalDataInterval(StrEnum):
    ONE_MINUTE = "1minute"
    THRITY_MINUTES = "30minute"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    def description(self) -> str:
        descriptions = {
            "1minute": "Data interval of one minute.",
            "30minutes": "Data interval of thirty minutes.",
            "day": "Daily data interval.",
            "week": "Weekly data interval.",
            "month": "Monthly data interval."
        }
        return descriptions.get(self.value, "Unknown Interval")
    
    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all historical data interval descriptions.
        """
        return {interval.value: interval.description() for interval in cls}


class Validity(StrEnum):
    DAY = "DAY"
    IOC = "IOC"
    
    def description(self) -> str:
        descriptions = {
            "DAY": "Order is valid for the entire trading day.",
            "IOC": "Immediate or Cancel; order is executed immediately or cancelled."
        }
        return descriptions.get(self.value, "Unknown Validity")
    
    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all validity descriptions.
        """
        return {validity.value: validity.description() for validity in cls}


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOPLOSS = "SL"
    STOPLOSS_MARKET = "SL-M"

    def description(self) -> str:
        descriptions = {
            "MARKET": "Order executed at the current market price.",
            "LIMIT": "Order executed at a specified price or better.",
            "SL": "Stop-loss order to limit potential losses.",
            "SL-M": "Stop-loss market order; triggers a market order when the stop price is reached."
        }
        return descriptions.get(self.value, "Unknown Order Type")
    
    @classmethod
    def all_descriptions(cls):
        """
        Returns a dictionary of all order type descriptions.
        """
        return {order_type.value: order_type.description() for order_type in cls}
    

if __name__ == "__main__":
    print(f"Exchange Descriptions: {Exchange.all_descriptions()}\n")
    print(f"Transaction Type Descriptions: {TransactionType.all_descriptions()}\n")
    print(f"Product Type Descriptions: {ProductType.all_descriptions()}\n")
    print(f"Segment Descriptions: {Segment.all_descriptions()}\n")
    print(f"Equity Security Type Descriptions: {EquitySecurityType.all_descriptions()}\n")
    print(f"Market Status Descriptions: {MarketStatus.all_descriptions()}\n")
    print(f"Order Status Descriptions: {OrderStatus.all_descriptions()}\n")
    print(f"Historical Data Interval Descriptions: {HistoricalDataInterval.all_descriptions()}\n")

