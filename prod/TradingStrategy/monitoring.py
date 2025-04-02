import os
import logging
import psutil
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from TradingStrategy.database import Database

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    """Configuration for alert thresholds."""

    cpu_threshold: float = 80.0  # CPU usage percentage
    memory_threshold: float = 80.0  # Memory usage percentage
    api_latency_threshold: float = 1000.0  # API latency in milliseconds
    error_rate_threshold: int = 10  # Number of errors per minute
    daily_loss_threshold: float = 0.05  # 5% daily loss limit
    drawdown_threshold: float = 0.15  # 15% maximum drawdown
    volatility_threshold: float = 0.02  # 2% volatility threshold


@dataclass
class EmailConfig:
    """Configuration for email alerts."""

    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    recipient_email: str


class MonitoringSystem:
    """Monitors system health and performance, sends alerts when thresholds are exceeded."""

    def __init__(
        self,
        database: Database,
        alert_config: Optional[AlertConfig] = None,
        email_config: Optional[EmailConfig] = None,
    ):
        """Initialize monitoring system."""
        self.database = database
        self.alert_config = alert_config or AlertConfig()
        self.email_config = email_config
        self.error_count = 0
        self.last_error_reset = time.time()
        self.peak_portfolio_value = Decimal("0")
        self.daily_start_value = Decimal("0")
        self.daily_start_time = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def check_system_health(self) -> List[str]:
        """Check system health metrics and return any alerts."""
        alerts = []

        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > self.alert_config.cpu_threshold:
            alerts.append(f"High CPU usage: {cpu_percent:.1f}%")

        # Check memory usage
        memory = psutil.virtual_memory()
        if memory.percent > self.alert_config.memory_threshold:
            alerts.append(f"High memory usage: {memory.percent:.1f}%")

        # Check error rate
        current_time = time.time()
        if current_time - self.last_error_reset >= 60:  # Reset error count every minute
            if self.error_count > self.alert_config.error_rate_threshold:
                alerts.append(f"High error rate: {self.error_count} errors per minute")
            self.error_count = 0
            self.last_error_reset = current_time

        return alerts

    def check_portfolio_health(self) -> List[str]:
        """Check portfolio health metrics and return any alerts."""
        alerts = []

        # Get latest portfolio snapshot
        snapshots = self.database.get_portfolio_history(
            start_time=self.daily_start_time, end_time=datetime.now()
        )
        if not snapshots:
            return alerts

        latest = snapshots[0]

        # Check daily loss
        if self.daily_start_value > 0:
            daily_return = (
                latest.total_value - self.daily_start_value
            ) / self.daily_start_value
            if daily_return < -self.alert_config.daily_loss_threshold:
                alerts.append(f"Daily loss threshold exceeded: {daily_return:.2%}")

        # Check drawdown
        if latest.total_value > self.peak_portfolio_value:
            self.peak_portfolio_value = latest.total_value
        else:
            drawdown = (
                self.peak_portfolio_value - latest.total_value
            ) / self.peak_portfolio_value
            if drawdown > self.alert_config.drawdown_threshold:
                alerts.append(f"Maximum drawdown exceeded: {drawdown:.2%}")

        # Check daily reset
        if datetime.now().date() > self.daily_start_time.date():
            self.daily_start_value = latest.total_value
            self.daily_start_time = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        return alerts

    def check_risk_metrics(self) -> List[str]:
        """Check risk metrics and return any alerts."""
        alerts = []

        # Get latest risk metrics
        metrics = self.database.get_risk_metrics(
            start_time=self.daily_start_time, end_time=datetime.now()
        )
        if not metrics:
            return alerts

        latest = metrics[0]

        # Check volatility
        if latest["volatility"] > self.alert_config.volatility_threshold:
            alerts.append(f"High volatility: {latest['volatility']:.2%}")

        return alerts

    def record_error(self) -> None:
        """Record an error occurrence."""
        self.error_count += 1

    def send_alert(self, alerts: List[str]) -> None:
        """Send alerts via email if configured."""
        if not alerts or not self.email_config:
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_config.sender_email
            msg["To"] = self.email_config.recipient_email
            msg["Subject"] = "Trading System Alert"

            body = "The following alerts were triggered:\n\n"
            for alert in alerts:
                body += f"- {alert}\n"

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(
                self.email_config.smtp_server, self.email_config.smtp_port
            ) as server:
                server.starttls()
                server.login(
                    self.email_config.sender_email, self.email_config.sender_password
                )
                server.send_message(msg)

            logger.info("Alert email sent successfully")

        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")

    def update_metrics(self) -> None:
        """Update system and portfolio metrics."""
        # Record system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        self.database.record_system_metrics(
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            api_latency=0.0,  # This should be measured in the API client
            error_count=self.error_count,
            active_positions=0,  # This should be tracked in the portfolio manager
        )

        # Check for alerts
        alerts = []
        alerts.extend(self.check_system_health())
        alerts.extend(self.check_portfolio_health())
        alerts.extend(self.check_risk_metrics())

        if alerts:
            logger.warning(f"Alerts triggered: {alerts}")
            self.send_alert(alerts)
