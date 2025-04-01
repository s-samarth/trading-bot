import os
import sys
import logging
import argparse
from typing import Dict, Optional
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from TradingStrategy.Constants import TradingSymbol, BaseExchange, BaseTransactionType
from TradingStrategy.StrategyData import TradingStrategyData
from TradingStrategy.ApiConstantsMapping import UpstoxConstantsMapping as Mappings
from API.Upstox.UpstoxLogin import Login, SandboxLogin
from API.Upstox.Data import MarketQuoteData
from API.Upstox.Constants import Segment
from API.Upstox.TradeExecutor import OrderAPI, OrderAPIv3, PlaceOrderData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIVersion(str, Enum):
    """Supported API versions for order placement."""
    V2 = "v2"
    V3 = "v3"

@dataclass
class TradingConfig:
    """Configuration for trading parameters."""
    trading_symbol: TradingSymbol
    buy_price: Decimal
    sell_price: Decimal
    quantity: int
    exchange: BaseExchange = BaseExchange.NSE
    segment: Segment = Segment.EQUITY
    api_version: APIVersion = APIVersion.V2
    use_sandbox: bool = True

    def to_strategy_data(self, ltp: Decimal) -> TradingStrategyData:
        """Convert config to TradingStrategyData."""
        return TradingStrategyData(
            trading_symbol=self.trading_symbol,
            exchange=self.exchange,
            ltp=ltp,
            buy_price=self.buy_price,
            sell_price=self.sell_price,
            quantity=self.quantity
        )

def simple_trading_strategy(
    config: TradingConfig,
    ltp: Decimal,
) -> TradingStrategyData:
    """
    A simple trading strategy which buys if LTP is less than buy price and sells if LTP is greater than sell price.
    
    Args:
        config: Trading configuration parameters
        ltp: The last traded price of the stock
        
    Returns:
        TradingStrategyData: The trade details containing transaction type and other information
    """
    # Convert config to strategy data
    trade_details = config.to_strategy_data(ltp)

    # Determine transaction type based on LTP
    if ltp < config.buy_price:
        trade_details.transaction_type = BaseTransactionType.BUY
        logger.info(f"BUY signal triggered: LTP {ltp} < Buy Price {config.buy_price}")
    elif ltp > config.sell_price:
        trade_details.transaction_type = BaseTransactionType.SELL
        logger.info(f"SELL signal triggered: LTP {ltp} > Sell Price {config.sell_price}")
    else:
        logger.info(f"No trade signal: LTP {ltp} within range [{config.buy_price}, {config.sell_price}]")

    return trade_details

async def place_order(
    trade_details: TradingStrategyData,
    config: TradingConfig,
    access_token: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """
    Places an order based on the trade details.
    
    Args:
        trade_details: The trade details containing transaction type and other information
        config: Trading configuration including API version preference
        access_token: Optional access token for the trading API
        
    Returns:
        Optional[Dict[str, str]]: Dictionary containing order IDs if order was placed, None otherwise
    """
    if not trade_details.transaction_type:
        logger.info("No trade action taken - no transaction type specified")
        return None

    try:
        order_data = PlaceOrderData(
            trading_symbol=trade_details.trading_symbol,
            transaction_type=trade_details.transaction_type,
            quantity=trade_details.quantity,
            exchange=Mappings.exchange(trade_details.exchange),
        )

        # Place order based on API version preference
        if config.api_version == APIVersion.V3:
            order_api = OrderAPIv3(access_token=access_token)
            order_response = await order_api.place_order(order_data=order_data)
            order_ids = {"order_id_v3": order_response["data"]["order_ids"][0]}
            logger.info(f"V3 order placed successfully: {order_ids}")
        else:
            order_api = OrderAPI(access_token=access_token)
            order_response = await order_api.place_order(order_data=order_data)
            order_ids = {"order_id": order_response["data"]["order_id"]}
            logger.info(f"V2 order placed successfully: {order_ids}")
        
        return order_ids
        
    except Exception as e:
        logger.error(f"Error placing orders: {str(e)}")
        raise

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Trading Strategy Demo')
    parser.add_argument(
        '--sandbox',
        action='store_true',
        help='Use sandbox environment for testing (default: True)'
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Use live environment for trading (default: False)'
    )
    parser.add_argument(
        '--api-version',
        choices=['v2', 'v3'],
        default='v2',
        help='API version to use (default: v2)'
    )
    parser.add_argument(
        '--symbol',
        choices=['IDEA', 'HDFCBANK'],
        default='IDEA',
        help='Trading symbol to use (default: IDEA)'
    )
    parser.add_argument(
        '--buy-price',
        type=float,
        required=True,
        help='Buy price threshold'
    )
    parser.add_argument(
        '--sell-price',
        type=float,
        required=True,
        help='Sell price threshold'
    )
    parser.add_argument(
        '--quantity',
        type=int,
        default=2,
        help='Number of shares to trade (default: 2)'
    )
    
    args = parser.parse_args()
    
    # Handle sandbox/live environment selection
    if args.live:
        args.sandbox = False
    elif not args.sandbox and not args.live:
        args.sandbox = True  # Default to sandbox mode
    
    return args

async def main():
    """Main function to demonstrate the trading strategy."""
    try:
        # Parse command line arguments
        args = parse_args()
        logger.info(f"Running with configuration: {args}")

        # Login to appropriate environment
        if args.sandbox:
            access_token = SandboxLogin().login()
            logger.info("Logged in successfully to sandbox environment")
        else:
            access_token = Login().login()
            logger.info("Logged in successfully to live environment")

        # Fetch LTP of selected symbol
        trading_symbol = getattr(TradingSymbol, args.symbol)
        market_quote = MarketQuoteData(access_token=access_token)
        ltp_data = market_quote.get_ltp(trading_symbol=trading_symbol, exchange=BaseExchange.NSE)
        
        key = f"{BaseExchange.NSE}_{Segment.EQUITY}:{trading_symbol}"
        ltp = Decimal(str(ltp_data["data"][key]["last_price"]))
        logger.info(f"Current LTP of {trading_symbol}: {ltp}")

        # Create trading configuration
        config = TradingConfig(
            trading_symbol=trading_symbol,
            buy_price=Decimal(str(args.buy_price)),
            sell_price=Decimal(str(args.sell_price)),
            quantity=args.quantity,
            api_version=APIVersion(args.api_version),
            use_sandbox=args.sandbox
        )

        # Run strategy
        logger.info(f"\nRunning strategy with API version {config.api_version}")
        trade_details = simple_trading_strategy(config, ltp)
        logger.info(f"Trade details: {trade_details}")
        
        if trade_details.transaction_type:
            # Uncomment to actually place orders
            # await place_order(trade_details, config, access_token)
            logger.info(f"Order placement skipped (commented out) - would use {config.api_version} API")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
