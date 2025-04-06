import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import yfinance as yf

from config.Config import Config
from TradingStrategy.Constants import TradingSymbol, BaseExchange


def dump_stock_info(
    trading_symbol: TradingSymbol, exchange: BaseExchange = BaseExchange.NSE
):
    # Need to Fix Bugs here
    raise NotImplementedError("This method is not implemented yet.")
    """
    Dump stock information to a JSON file.
    This method retrieves stock information using yfinance and saves it to a JSON file.
    """
    if self.exchange == BaseExchange.NSE:
        stock_ticker_symbol = f"{trading_symbol}.NS"
    elif self.exchange == BaseExchange.BSE:
        stock_ticker_symbol = f"{trading_symbol}.BO"
    else:
        raise ValueError("Unsupported exchange. Supported exchanges are NSE and BSE.")
    stock_data = yf.Ticker(stock_ticker_symbol)
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "actions": stock_data.actions.to_dict(),
        "analyst_price_targets": stock_data.analyst_price_targets,
        "balance_sheet": stock_data.balance_sheet.to_dict(),
        "calendar": stock_data.calendar,
        "capital_gains": stock_data.capital_gains.to_dict(),
        "cash_flow": stock_data.cashflow.to_dict(),
        "dividends": stock_data.dividends.to_dict(),
        "earnings_dates": stock_data.earnings_dates.to_dict(),
        "earnings_estimate": stock_data.earnings_estimate.to_dict(),
        "earnings_history": stock_data.earnings_history.to_dict(),
        "eps_revisions": stock_data.eps_revisions.to_dict(),
        "eps_trend": stock_data.eps_trend.to_dict(),
        "financials": stock_data.financials.to_dict(),
        "growth_estimates": stock_data.growth_estimates.to_dict(),
        "history_metadata": stock_data.history_metadata,
        "income_stmt": stock_data.income_stmt.to_dict(),
        "info": stock_data.info,
        "insider_purchases": stock_data.insider_purchases.to_dict(),
        "insider_roster_holders": stock_data.insider_roster_holders.to_dict(),
        "insider_transactions": stock_data.insider_transactions.to_dict(),
        "institutional_holders": stock_data.institutional_holders.to_dict(),
        "isin": stock_data.isin,
        "major_holders": stock_data.major_holders.to_dict(),
        "mutualfund_holders": stock_data.mutualfund_holders.to_dict(),
        "news": stock_data.news,
        "options": stock_data.options,
        "quarterly_balance_sheet": stock_data.quarterly_balance_sheet.to_dict(),
        "quarterly_cash_flow": stock_data.quarterly_cashflow.to_dict(),
        "quarterly_financials": stock_data.quarterly_financials.to_dict(),
        "quarterly_income_stmt": stock_data.quarterly_income_stmt.to_dict(),
        "recommendations": stock_data.recommendations.to_dict(),
        "revenue_estimate": stock_data.revenue_estimate.to_dict(),
        "splits": stock_data.splits.to_dict(),
        "sustainability": stock_data.sustainability.to_dict(),
        "ttm_cash_flow": stock_data.ttm_cash_flow.to_dict(),
        "ttm_financials": stock_data.ttm_financials.to_dict(),
        "ttm_income_stmt": stock_data.ttm_income_stmt.to_dict(),
        "upgrades_downgrades": stock_data.upgrades_downgrades.to_dict(),
    }
    folder_path = os.path.join(Config.root_dir, "HistoricalData", trading_symbol)
    info_file_path = os.path.join(folder_path, "info.json")
    if not os.path.exists(info_file_path):
        with open(info_file_path, "w") as f:
            json.dump([data], f, indent=4)
    else:
        with open(info_file_path, "r") as f:
            data_logs = json.load(f)
        data_logs.extend([data])
        with open(info_file_path, "w") as f:
            json.dump(data_logs, f, indent=4)
