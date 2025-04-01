import os
import sys
import logging
import signal
import time
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
import argparse
from dataclasses import dataclass
import json

from TradingStrategy.database import Database, TradeRecord, PortfolioSnapshot
from TradingStrategy.monitoring import MonitoringSystem, AlertConfig, EmailConfig
from TradingStrategy.portfolio_manager import PortfolioManager, StockConfig
from TradingStrategy.strategies import StrategyConfig, run_strategy
from TradingStrategy.Constants import TradingSymbol, BaseExchange
from TradingStrategy.ApiConstantsMapping import UpstoxConstantsMapping as Mappings
from API.Upstox.UpstoxLogin import Login, SandboxLogin
from API.Upstox.Data import MarketQuoteData
from API.Upstox.Constants import Segment
from API.Upstox.TradeExecutor import OrderAPI, OrderAPIv3, PlaceOrderData
from .client import Client, APIVersion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TradingConfig:
    """Configuration for the trading system."""
    budget: Decimal
    symbols: List[str]
    base_quantity: int
    update_interval: int
    is_sandbox: bool
    strategy_type: str
    buy_price: Optional[Decimal] = None
    sell_price: Optional[Decimal] = None
    email_config: Optional[EmailConfig] = None

class TradingSystem:
    """Main trading system that coordinates all components."""
    
    def __init__(self, config: TradingConfig):
        """Initialize the trading system."""
        self.config = config
        self.database = Database()
        self.monitoring = MonitoringSystem(
            database=self.database,
            email_config=config.email_config
        )
        
        # Initialize market data client
        self.market_client = MarketDataClient()
        
        # Initialize trading client
        self.trading_client = Client(
            api_version=APIVersion.V2,
            is_sandbox=config.is_sandbox
        )
        
        # Initialize portfolio manager
        stock_configs = [
            StockConfig(
                symbol=symbol,
                base_quantity=config.base_quantity,
                stop_loss_pct=Decimal('0.02'),
                take_profit_pct=Decimal('0.04')
            )
            for symbol in config.symbols
        ]
        
        self.portfolio_manager = PortfolioManager(
            total_budget=config.budget,
            stock_configs=stock_configs
        )
        
        # Initialize strategy config
        self.strategy_config = StrategyConfig(
            strategy_type=config.strategy_type,
            buy_price=config.buy_price,
            sell_price=config.sell_price
        )
        
        # Signal handlers
        self.running = True
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum: int, frame: Optional[object] = None) -> None:
        """Handle shutdown signals gracefully."""
        logger.info("Shutdown signal received. Cleaning up...")
        self.running = False
    
    def _place_order(self, trade: Dict) -> None:
        """Place an order through the trading client."""
        try:
            # Place order
            order = self.trading_client.place_order(
                symbol=trade["symbol"],
                quantity=trade["quantity"],
                side=trade["side"],
                order_type="MARKET"
            )
            
            logger.info(f"Order placed successfully: {order}")
            
            # Record trade in database
            trade_record = TradeRecord(
                id=0,  # Will be set by database
                symbol=trade["symbol"],
                entry_time=datetime.now(),
                exit_time=datetime.now(),  # Will be updated when position is closed
                entry_price=Decimal(str(trade["price"])),
                exit_price=Decimal('0'),  # Will be updated when position is closed
                quantity=trade["quantity"],
                position_type=trade["side"],
                pnl=Decimal('0'),  # Will be updated when position is closed
                stop_loss=Decimal(str(trade["stop_loss"])),
                take_profit=Decimal(str(trade["take_profit"])),
                strategy=self.config.strategy_type,
                reason=trade["reason"]
            )
            self.database.record_trade(trade_record)
            
        except Exception as e:
            logger.error(f"Failed to place order: {str(e)}")
            self.monitoring.record_error()
    
    def _update_portfolio(self) -> None:
        """Update portfolio state and record metrics."""
        try:
            # Get current prices
            prices = self.market_client.get_prices(self.config.symbols)
            
            # Update portfolio
            self.portfolio_manager.update_prices(prices)
            
            # Record portfolio snapshot
            snapshot = PortfolioSnapshot(
                id=0,  # Will be set by database
                timestamp=datetime.now(),
                total_value=self.portfolio_manager.get_total_value(),
                cash_balance=self.portfolio_manager.get_available_budget(),
                total_pnl=self.portfolio_manager.get_total_pnl(),
                positions=self.portfolio_manager.get_positions()
            )
            self.database.record_portfolio_snapshot(snapshot)
            
            # Record risk metrics
            self.database.record_risk_metrics(
                daily_pnl=self.portfolio_manager.get_daily_pnl(),
                drawdown=self.portfolio_manager.get_current_drawdown(),
                max_drawdown=self.portfolio_manager.get_max_drawdown(),
                volatility=self.portfolio_manager.get_portfolio_volatility(),
                sharpe_ratio=self.portfolio_manager.get_sharpe_ratio()
            )
            
        except Exception as e:
            logger.error(f"Failed to update portfolio: {str(e)}")
            self.monitoring.record_error()
    
    def _analyze_portfolio(self) -> None:
        """Analyze portfolio and execute trades."""
        try:
            # Get trading signals
            signals = self.portfolio_manager.analyze_portfolio()
            
            # Execute trades
            for signal in signals:
                if signal["action"] == "BUY":
                    self._place_order({
                        "symbol": signal["symbol"],
                        "quantity": signal["quantity"],
                        "side": "BUY",
                        "price": signal["price"],
                        "stop_loss": signal["stop_loss"],
                        "take_profit": signal["take_profit"],
                        "reason": signal["reason"]
                    })
                elif signal["action"] == "SELL":
                    self._place_order({
                        "symbol": signal["symbol"],
                        "quantity": signal["quantity"],
                        "side": "SELL",
                        "price": signal["price"],
                        "stop_loss": signal["stop_loss"],
                        "take_profit": signal["take_profit"],
                        "reason": signal["reason"]
                    })
            
        except Exception as e:
            logger.error(f"Failed to analyze portfolio: {str(e)}")
            self.monitoring.record_error()
    
    def run(self) -> None:
        """Main trading loop."""
        logger.info("Starting trading system...")
        
        while self.running:
            try:
                # Update monitoring metrics
                self.monitoring.update_metrics()
                
                # Update portfolio state
                self._update_portfolio()
                
                # Analyze portfolio and execute trades
                self._analyze_portfolio()
                
                # Sleep for update interval
                time.sleep(self.config.update_interval)
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                self.monitoring.record_error()
                time.sleep(5)  # Wait before retrying
        
        logger.info("Trading system stopped.")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Trading System")
    parser.add_argument("--budget", type=float, required=True, help="Total trading budget")
    parser.add_argument("--symbols", nargs="+", required=True, help="Trading symbols")
    parser.add_argument("--base-quantity", type=int, required=True, help="Base quantity per trade")
    parser.add_argument("--update-interval", type=int, default=60, help="Update interval in seconds")
    parser.add_argument("--strategy", choices=["technical", "simple"], required=True, help="Trading strategy")
    parser.add_argument("--buy-price", type=float, help="Buy price for simple strategy")
    parser.add_argument("--sell-price", type=float, help="Sell price for simple strategy")
    parser.add_argument("--live", action="store_true", help="Run in live mode")
    parser.add_argument("--email-config", type=str, help="Path to email configuration file")
    
    return parser.parse_args()

def load_email_config(config_path: str) -> Optional[EmailConfig]:
    """Load email configuration from file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return EmailConfig(
                smtp_server=config["smtp_server"],
                smtp_port=config["smtp_port"],
                sender_email=config["sender_email"],
                sender_password=config["sender_password"],
                recipient_email=config["recipient_email"]
            )
    except Exception as e:
        logger.error(f"Failed to load email config: {str(e)}")
        return None

def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    # Load email configuration if provided
    email_config = None
    if args.email_config:
        email_config = load_email_config(args.email_config)
    
    # Create trading configuration
    config = TradingConfig(
        budget=Decimal(str(args.budget)),
        symbols=args.symbols,
        base_quantity=args.base_quantity,
        update_interval=args.update_interval,
        is_sandbox=not args.live,
        strategy_type=args.strategy,
        buy_price=Decimal(str(args.buy_price)) if args.buy_price else None,
        sell_price=Decimal(str(args.sell_price)) if args.sell_price else None,
        email_config=email_config
    )
    
    # Create and run trading system
    system = TradingSystem(config)
    system.run()

if __name__ == "__main__":
    main() 