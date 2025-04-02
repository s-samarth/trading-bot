import os
import sys
import logging
import argparse
from typing import Dict, Optional
from dataclasses import dataclass
from decimal import Decimal
import time

from TradingStrategy.Constants import TradingSymbol, BaseExchange
from TradingStrategy.ApiConstantsMapping import UpstoxConstantsMapping as Mappings
from TradingStrategy.portfolio_manager import PortfolioManager, StockConfig
from API.Upstox.UpstoxLogin import Login, SandboxLogin
from API.Upstox.Data import MarketQuoteData
from API.Upstox.Constants import Segment
from API.Upstox.TradeExecutor import OrderAPI, OrderAPIv3, PlaceOrderData

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class APIVersion(str, Enum):
    """Supported API versions for order placement."""

    V2 = "v2"
    V3 = "v3"


def place_order(
    trade_details: TradingStrategyData,
    access_token: Optional[str] = None,
    api_version: APIVersion = APIVersion.V2,
) -> Optional[Dict[str, str]]:
    """
    Places an order based on the trade details.

    Args:
        trade_details: The trade details containing transaction type and other information
        access_token: Optional access token for the trading API
        api_version: API version to use for order placement

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
        if api_version == APIVersion.V3:
            order_api = OrderAPIv3(access_token=access_token)
            order_response = order_api.place_order(order_data=order_data)
            order_ids = {"order_id_v3": order_response["data"]["order_ids"][0]}
            logger.info(f"V3 order placed successfully: {order_ids}")
        else:
            order_api = OrderAPI(access_token=access_token)
            order_response = order_api.place_order(order_data=order_data)
            order_ids = {"order_id": order_response["data"]["order_id"]}
            logger.info(f"V2 order placed successfully: {order_ids}")

        return order_ids

    except Exception as e:
        logger.error(f"Error placing orders: {str(e)}")
        raise


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Portfolio Trading Demo")
    parser.add_argument(
        "--budget", type=float, required=True, help="Total budget for trading (in INR)"
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        choices=["IDEA", "HDFCBANK"],
        required=True,
        help="List of symbols to trade",
    )
    parser.add_argument(
        "--base-quantity",
        type=int,
        default=2,
        help="Base quantity to trade per symbol (default: 2)",
    )
    parser.add_argument(
        "--update-interval",
        type=int,
        default=60,
        help="Seconds between portfolio updates (default: 60)",
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Use sandbox environment for testing (default: True)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use live environment for trading (default: False)",
    )
    parser.add_argument(
        "--api-version",
        choices=["v2", "v3"],
        default="v2",
        help="API version to use (default: v2)",
    )

    args = parser.parse_args()

    # Handle sandbox/live environment selection
    if args.live:
        args.sandbox = False
    elif not args.sandbox and not args.live:
        args.sandbox = True  # Default to sandbox mode

    return args


def main():
    """Main function to demonstrate portfolio trading."""
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

        # Create stock configurations
        stock_configs = []
        for symbol in args.symbols:
            config = StockConfig(
                symbol=getattr(TradingSymbol, symbol),
                exchange=BaseExchange.NSE,
                base_quantity=args.base_quantity,
                min_quantity=1,
                max_quantity=args.base_quantity * 2,
                stop_loss_pct=0.02,  # 2% stop loss
                take_profit_pct=0.04,  # 4% take profit
                max_position_size=0.1,  # 10% of portfolio
                risk_per_trade=0.02,  # 2% risk per trade
            )
            stock_configs.append(config)

        # Initialize portfolio manager
        portfolio_manager = PortfolioManager(
            total_budget=Decimal(str(args.budget)),
            stock_configs=stock_configs,
            update_interval=args.update_interval,
        )

        # Initialize market data client
        market_quote = MarketQuoteData(access_token=access_token)

        logger.info("\nStarting portfolio trading...")
        logger.info("Press Ctrl+C to stop")

        while True:
            try:
                # Update prices for all stocks
                for symbol in args.symbols:
                    trading_symbol = getattr(TradingSymbol, symbol)
                    ltp_data = market_quote.get_ltp(
                        trading_symbol=trading_symbol, exchange=BaseExchange.NSE
                    )

                    key = f"{BaseExchange.NSE}_{Segment.EQUITY}:{trading_symbol}"
                    ltp = Decimal(str(ltp_data["data"][key]["last_price"]))
                    portfolio_manager.update_price(trading_symbol, ltp)

                # Analyze portfolio and get trading decisions
                trading_decisions = portfolio_manager.analyze_portfolio()

                # Execute trading decisions
                for decision in trading_decisions:
                    # Uncomment to actually place orders
                    # place_order(decision, access_token, APIVersion(args.api_version))
                    logger.info(
                        f"Order placement skipped (commented out) - would use {args.api_version} API"
                    )
                    logger.info(f"Trade decision: {decision}")

                # Get and log portfolio summary
                summary = portfolio_manager.get_portfolio_summary()
                logger.info("\nPortfolio Summary:")
                logger.info(f"Total Budget: ₹{summary['total_budget']:,.2f}")
                logger.info(f"Total Value: ₹{summary['total_value']:,.2f}")
                logger.info(f"Total P&L: ₹{summary['total_pnl']:,.2f}")
                logger.info(f"Available Budget: ₹{summary['available_budget']:,.2f}")
                logger.info("\nPositions:")
                for position in summary["positions"]:
                    logger.info(
                        f"{position['symbol']}: {position['quantity']} shares @ ₹{position['average_price']:,.2f}"
                    )
                    logger.info(f"  Current Price: ₹{position['current_price']:,.2f}")
                    logger.info(f"  P&L: ₹{position['unrealized_pnl']:,.2f}")
                    logger.info(f"  Stop Loss: ₹{position['stop_loss']:,.2f}")
                    logger.info(f"  Take Profit: ₹{position['take_profit']:,.2f}")

                # Wait for next update
                time.sleep(args.update_interval)

            except KeyboardInterrupt:
                logger.info("\nStopping portfolio trading...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(args.update_interval)  # Wait before retrying
                continue

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    main()
