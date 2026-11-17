"""
Investment Strategy Comparative Analysis
Compare All Weather, Permanent Portfolio, Berkshire Hathaway (BRK.B), and SPY.

Install dependencies: python -m pip install yfinance pandas numpy matplotlib
Run the program:     python strategy_comparison.py

Backtesting assumptions:
1. All four strategies start on the same date with $10,000 in initial capital.
2. Yahoo Finance prices adjusted for dividends and stock splits are used to approximate total returns.
3. All Weather and Permanent Portfolio are rebalanced to target weights after the last trading day of each year.
4. BRK.B and SPY are buy-and-hold strategies; taxes, slippage, and rebalancing costs are excluded.
5. The Sharpe ratio assumes a 0% risk-free rate for a simplified comparison.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf


# ========= 1. Basic Settings =========
START_DATE = "2010-01-01"  # All strategies begin on the first date with data available for every asset
INITIAL_CAPITAL = 10_000    # Each strategy starts with $10,000
TRADING_DAYS = 252         # Approximate number of U.S. stock market trading days per year
OUTPUT_DIR = Path("output_strategy")

# Use publicly traded ETFs to construct simplified strategy proxies.
# These allocations do not represent Bridgewater's actual holdings.
STRATEGIES = {
    "All Weather": {
        "SPY": 0.30,   # U.S. equities
        "TLT": 0.40,   # Long-term U.S. Treasury bonds
        "IEF": 0.15,   # Intermediate-term U.S. Treasury bonds
        "GLD": 0.075,  # Gold
        "DBC": 0.075,  # Commodities
    },
    "Permanent Portfolio": {
        "SPY": 0.25,   # Equities
        "TLT": 0.25,   # Long-term Treasury bonds
        "GLD": 0.25,   # Gold
        "BIL": 0.25,   # Short-term Treasury bills (cash proxy)
    },
    "BRK.B": {"BRK-B": 1.00},  # yfinance uses BRK-B instead of BRK.B
    "SPY": {"SPY": 1.00},      # S&P 500 ETF benchmark
}


def download_prices():
    """Download daily adjusted closing prices and align all assets by trading date."""
    # Collect every unique ticker used in the strategies to avoid duplicate downloads.
    tickers = sorted({ticker for allocation in STRATEGIES.values()
                      for ticker in allocation})
    print("Downloading:", ", ".join(tickers))

    raw = yf.download(
        tickers=tickers,
        start=START_DATE,
        auto_adjust=True,  # Adjust closing prices for stock splits and dividends
        progress=False,
        threads=False,
    )
    if raw.empty:
        raise RuntimeError("没有下载到行情数据，请检查网络后重试。")

    # With multiple tickers, yfinance generally returns MultiIndex columns:
    # one level for the price field and another for the ticker symbol.
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"].copy()
    else:
        raise RuntimeError("下载数据格式异常：预期多个 Ticker 的价格表。")

    # Check that price data was downloaded for every required ticker.
    missing = [ticker for ticker in tickers if ticker not in prices.columns]
    if missing:
        raise RuntimeError(f"以下资产缺少价格数据：{missing}")

    prices = prices[tickers].sort_index()
    prices = prices.dropna(how="any")  # Keep only dates with valid prices for every asset
    prices = prices.loc[(prices > 0).all(axis=1)]

    if len(prices) < TRADING_DAYS:
        raise RuntimeError("共同有效交易日太少，无法进行可靠的长期比较。")

    # Save adjusted prices so the underlying data can be reviewed and reproduced.
    prices.to_csv(OUTPUT_DIR / "adjusted_prices.csv")
    return prices


def backtest(prices, allocation):
    """Simulate buy-and-hold investing with rebalancing at the end of each year."""
    # Map target portfolio weights to the full list of price columns.
    # Assets not included in the strategy receive a weight of zero.
    target_weights = pd.Series(0.0, index=prices.columns)
    for ticker, weight in allocation.items():
        target_weights[ticker] = weight
    if not np.isclose(target_weights.sum(), 1.0):
        raise ValueError("每个策略的目标权重必须合计为 100%。")

    # pct_change() calculates today's price divided by yesterday's price, minus one.
    daily_returns = prices.pct_change(fill_method=None).iloc[1:]

    current_weights = target_weights.copy()
    account_value = INITIAL_CAPITAL
    values = [account_value]  # Start at $10,000 before the first daily return is applied

    for i, (date, asset_returns) in enumerate(daily_returns.iterrows()):
        # Daily portfolio return = current portfolio weights × daily asset returns.
        portfolio_return = float((current_weights * asset_returns).sum())
        account_value *= 1.0 + portfolio_return
        values.append(account_value)

        # Asset price movements cause portfolio weights to drift over time.
        # Buy-and-hold is therefore different from maintaining fixed daily weights.
        current_weights = (current_weights * (1.0 + asset_returns)
                           / (1.0 + portfolio_return))

        # Restore target weights after the last trading day's close each year.
        # The rebalanced weights apply to the following trading session.
        # Rebalancing has no effect on the 100% SPY and 100% BRK.B portfolios.
        if (i + 1 < len(daily_returns)
                and date.year != daily_returns.index[i + 1].year):
            current_weights = target_weights.copy()

    return pd.Series(values, index=prices.index, dtype=float)


def calculate_metrics(values):
    """Calculate total return, CAGR, volatility, Sharpe ratio, and maximum drawdown."""
    daily = values.pct_change(fill_method=None).dropna()
    years = (values.index[-1] - values.index[0]).days / 365.25
    total_return = values.iloc[-1] / values.iloc[0] - 1.0
    cagr = (values.iloc[-1] / values.iloc[0]) ** (1.0 / years) - 1.0

    annual_volatility = daily.std(ddof=1) * np.sqrt(TRADING_DAYS)
    # For simplicity, assume a 0% risk-free rate in the Sharpe ratio calculation.
    # Use annualized average returns rather than CAGR for this calculation.
    sharpe = (daily.mean() / daily.std(ddof=1) * np.sqrt(TRADING_DAYS)
              if daily.std(ddof=1) > 0 else np.nan)
    max_drawdown = (values / values.cummax() - 1.0).min()

    return {
        "Total Return": total_return,
        "CAGR": cagr,
        "Annual Volatility": annual_volatility,
        "Sharpe (Rf=0)": sharpe,
        "Max Drawdown": max_drawdown,
    }


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    prices = download_prices()
    print(f"Common data: {prices.index[0].date()} to "
          f"{prices.index[-1].date()} ({len(prices)} trading days)")

    # Backtest each strategy to produce a daily portfolio value series.
    results = pd.DataFrame(index=prices.index)
    metrics = {}
    for name, allocation in STRATEGIES.items():
        results[name] = backtest(prices, allocation)
        metrics[name] = calculate_metrics(results[name])

    # Save the performance metrics and daily portfolio values.
    report = pd.DataFrame(metrics).T
    report.to_csv(OUTPUT_DIR / "strategy_metrics.csv")
    results.to_csv(OUTPUT_DIR / "daily_portfolio_values.csv")

    # Format returns, volatility, and drawdown as percentages for terminal output.
    displayed = report.copy()
    for col in ["Total Return", "CAGR", "Annual Volatility", "Max Drawdown"]:
        displayed[col] = displayed[col].map(lambda x: f"{x:.2%}")
    displayed["Sharpe (Rf=0)"] = displayed["Sharpe (Rf=0)"].map(
        lambda x: f"{x:.2f}")
    print("\n=== INVESTMENT STRATEGY COMPARISON ===")
    print(displayed.to_string())

    # Plot the growth of a $10,000 initial investment for all four strategies.
    plt.figure(figsize=(12, 6))
    for name in results.columns:
        plt.plot(results.index, results[name], label=name, linewidth=1.7)
    plt.title("Investment Strategy Comparison — Growth of $10,000")
    plt.ylabel("Portfolio Value (USD)")
    plt.xlabel("Date")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    chart_path = OUTPUT_DIR / "strategy_comparison.png"
    plt.savefig(chart_path, dpi=180)
    plt.close()

    print(f"\nSaved: {OUTPUT_DIR / 'strategy_metrics.csv'}")
    print(f"Saved: {OUTPUT_DIR / 'daily_portfolio_values.csv'}")
    print(f"Saved: {chart_path}")
    print("Note: hypothetical ETF proxies; dividends adjusted; annual rebalancing;")
    print("      no fees, taxes or trading costs; Sharpe assumes Rf=0.")


# Run main() only when this file is executed directly.
# Importing this module for testing will not automatically download data.
if __name__ == "__main__":
    main()
