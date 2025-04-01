import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
import sqlite3
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TradeRecord:
    """Represents a completed trade."""
    id: int
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: Decimal
    exit_price: Decimal
    quantity: int
    position_type: str
    pnl: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    strategy: str
    reason: str

@dataclass
class PortfolioSnapshot:
    """Represents a portfolio state at a point in time."""
    id: int
    timestamp: datetime
    total_value: Decimal
    cash_balance: Decimal
    total_pnl: Decimal
    positions: Dict[str, Dict]

class Database:
    """Manages database operations for the trading system."""
    
    def __init__(self, db_path: str = "trading.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self) -> None:
        """Create necessary database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    entry_time TIMESTAMP NOT NULL,
                    exit_time TIMESTAMP NOT NULL,
                    entry_price DECIMAL NOT NULL,
                    exit_price DECIMAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    position_type TEXT NOT NULL,
                    pnl DECIMAL NOT NULL,
                    stop_loss DECIMAL NOT NULL,
                    take_profit DECIMAL NOT NULL,
                    strategy TEXT NOT NULL,
                    reason TEXT NOT NULL
                )
            """)
            
            # Create portfolio snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    total_value DECIMAL NOT NULL,
                    cash_balance DECIMAL NOT NULL,
                    total_pnl DECIMAL NOT NULL,
                    positions TEXT NOT NULL
                )
            """)
            
            # Create system metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    cpu_usage REAL NOT NULL,
                    memory_usage REAL NOT NULL,
                    api_latency REAL NOT NULL,
                    error_count INTEGER NOT NULL,
                    active_positions INTEGER NOT NULL
                )
            """)
            
            # Create risk metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    daily_pnl DECIMAL NOT NULL,
                    drawdown DECIMAL NOT NULL,
                    max_drawdown DECIMAL NOT NULL,
                    volatility REAL NOT NULL,
                    sharpe_ratio REAL NOT NULL
                )
            """)
            
            conn.commit()
    
    def record_trade(self, trade: TradeRecord) -> None:
        """Record a completed trade in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trades (
                    symbol, entry_time, exit_time, entry_price, exit_price,
                    quantity, position_type, pnl, stop_loss, take_profit,
                    strategy, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.symbol,
                trade.entry_time,
                trade.exit_time,
                float(trade.entry_price),
                float(trade.exit_price),
                trade.quantity,
                trade.position_type,
                float(trade.pnl),
                float(trade.stop_loss),
                float(trade.take_profit),
                trade.strategy,
                trade.reason
            ))
            conn.commit()
    
    def record_portfolio_snapshot(self, snapshot: PortfolioSnapshot) -> None:
        """Record a portfolio snapshot in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO portfolio_snapshots (
                    timestamp, total_value, cash_balance, total_pnl, positions
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                snapshot.timestamp,
                float(snapshot.total_value),
                float(snapshot.cash_balance),
                float(snapshot.total_pnl),
                str(snapshot.positions)  # Convert dict to string for storage
            ))
            conn.commit()
    
    def record_system_metrics(
        self,
        cpu_usage: float,
        memory_usage: float,
        api_latency: float,
        error_count: int,
        active_positions: int
    ) -> None:
        """Record system performance metrics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_metrics (
                    timestamp, cpu_usage, memory_usage, api_latency,
                    error_count, active_positions
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                cpu_usage,
                memory_usage,
                api_latency,
                error_count,
                active_positions
            ))
            conn.commit()
    
    def record_risk_metrics(
        self,
        daily_pnl: Decimal,
        drawdown: Decimal,
        max_drawdown: Decimal,
        volatility: float,
        sharpe_ratio: float
    ) -> None:
        """Record risk management metrics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO risk_metrics (
                    timestamp, daily_pnl, drawdown, max_drawdown,
                    volatility, sharpe_ratio
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                float(daily_pnl),
                float(drawdown),
                float(max_drawdown),
                volatility,
                sharpe_ratio
            ))
            conn.commit()
    
    def get_trade_history(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[TradeRecord]:
        """Retrieve trade history with optional filters."""
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if start_time:
            query += " AND entry_time >= ?"
            params.append(start_time)
        if end_time:
            query += " AND exit_time <= ?"
            params.append(end_time)
        
        query += " ORDER BY entry_time DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                TradeRecord(
                    id=row[0],
                    symbol=row[1],
                    entry_time=datetime.fromisoformat(row[2]),
                    exit_time=datetime.fromisoformat(row[3]),
                    entry_price=Decimal(str(row[4])),
                    exit_price=Decimal(str(row[5])),
                    quantity=row[6],
                    position_type=row[7],
                    pnl=Decimal(str(row[8])),
                    stop_loss=Decimal(str(row[9])),
                    take_profit=Decimal(str(row[10])),
                    strategy=row[11],
                    reason=row[12]
                )
                for row in rows
            ]
    
    def get_portfolio_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[PortfolioSnapshot]:
        """Retrieve portfolio history with optional time filters."""
        query = "SELECT * FROM portfolio_snapshots WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                PortfolioSnapshot(
                    id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    total_value=Decimal(str(row[2])),
                    cash_balance=Decimal(str(row[3])),
                    total_pnl=Decimal(str(row[4])),
                    positions=eval(row[5])  # Convert string back to dict
                )
                for row in rows
            ]
    
    def get_risk_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Retrieve risk metrics with optional time filters."""
        query = "SELECT * FROM risk_metrics WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row[0],
                    "timestamp": datetime.fromisoformat(row[1]),
                    "daily_pnl": Decimal(str(row[2])),
                    "drawdown": Decimal(str(row[3])),
                    "max_drawdown": Decimal(str(row[4])),
                    "volatility": row[5],
                    "sharpe_ratio": row[6]
                }
                for row in rows
            ] 