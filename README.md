# Investment Strategy Comparative Analysis

**Python backtesting of All Weather, Permanent Portfolio, Berkshire Hathaway, and the S&P 500**

A compact investment research project comparing long-run growth, volatility, drawdowns, and risk-adjusted returns across two diversified asset-allocation strategies and two equity buy-and-hold investments.

![Investment Strategy Comparison](output_strategy/strategy_comparison.png)

## Research questions

1. How much long-term compound growth is sacrificed in exchange for diversification?
2. Do defensive, multi-asset portfolios exhibit lower historical volatility and maximum drawdown than equities?
3. How does Berkshire Hathaway Class B stock compare with an S&P 500 ETF over the same period?

## Strategies and assumptions

| Strategy | Investment allocation | Rebalancing |
| --- | --- | --- |
| **All Weather (simplified proxy)** | 30% SPY, 40% TLT, 15% IEF, 7.5% GLD, 7.5% DBC | Annually |
| **Permanent Portfolio (ETF proxy)** | 25% SPY, 25% TLT, 25% GLD, 25% BIL | Annually |
| **Berkshire Hathaway** | 100% BRK.B (Yahoo Finance ticker `BRK-B`) | Buy and hold |
| **S&P 500** | 100% SPY | Buy and hold |

These are **illustrative ETF implementations**, not the reported live results of Bridgewater or any other investment manager. The classic Permanent Portfolio allocation is represented here with ETFs rather than directly holding the underlying assets.

All strategies start with **$10,000**, from the first common trading date available after **January 1, 2010**. Returns are based on **adjusted closing prices** from Yahoo Finance via `yfinance`, a proxy for reinvested distributions and corporate actions. Asset weights drift within each year; diversified portfolios rebalance to target weights at each calendar year-end, with the new weights effective on the next trading day. Trading costs, slippage, and taxes are excluded. Sharpe ratios assume a **0% risk-free rate**.

## Historical results

*Results copied from the user's completed 2026-11-17 run; future runs can differ as prices and date coverage change.*

| Strategy | Total return | CAGR | Annual volatility | Sharpe (Rf = 0) | Max drawdown |
| --- | ---: | ---: | ---: | ---: | ---: |
| All Weather | 194.74% | 6.62% | 7.88% | 0.85 | -23.03% |
| Permanent Portfolio | 197.84% | 6.68% | **7.08%** | **0.95** | **-17.00%** |
| Berkshire Hathaway (BRK.B) | **786.08%** | **13.81%** | 19.21% | 0.77 | -29.57% |
| S&P 500 (SPY) | 768.14% | 13.67% | 17.06% | 0.84 | -33.72% |

The unrounded values are in [`output_strategy/strategy_metrics.csv`](output_strategy/strategy_metrics.csv). The saved image is from the same user-shared historical run.

### Findings

- **Long-term growth:** Berkshire Hathaway narrowly exceeded SPY on CAGR (13.81% versus 13.67%), but had higher annualized volatility (19.21% versus 17.06%) and a lower zero-risk-free Sharpe ratio.
- **Capital preservation:** The Permanent Portfolio proxy had the lowest volatility and smallest maximum drawdown among the four strategies in this sample. Its 6.68% CAGR was substantially below the equity-only alternatives.
- **Risk-adjusted returns:** The Permanent Portfolio proxy had the highest Sharpe ratio (0.95) **under the simplified 0% risk-free-rate assumption**, not necessarily under a time-varying Treasury-bill benchmark.
- **Sensitivity to macroeconomic conditions:** Even diversified portfolios can lose value when both stocks and long-duration bonds decline, such as during rate shocks.

**Interpretation:** This historical comparison illustrates the trade-off between compound growth and diversification. It does not establish that any strategy will outperform in the future, nor does it measure Berkshire's manager-specific alpha.

## Reproduce the project

Requires Python 3.10+ and internet access to download prices.

```bash
# From the project directory
python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
python -m pip install -r requirements.txt
python strategy_comparison.py
```

Windows PowerShell users can activate with `.venv\Scripts\Activate.ps1` instead.

The script prints a performance table and creates these files inside `output_strategy/`:

| File | Purpose |
| --- | --- |
| `strategy_comparison.png` | Growth of $10,000 for four strategies |
| `strategy_metrics.csv` | Total return, CAGR, volatility, Sharpe ratio, max drawdown |
| `daily_portfolio_values.csv` | Daily simulated values (generated when run; not included in GitHub package) |
| `adjusted_prices.csv` | Downloaded adjusted prices (generated when run; not included in GitHub package) |

To change the backtest's beginning, edit `START_DATE` in `strategy_comparison.py`; to change the ETF allocations, edit `STRATEGIES`. A later start date may be required if any asset lacks historical prices.

## Methodology

1. **Data collection:** Download adjusted closing prices using `yfinance`, then restrict all assets to common available trading dates.
2. **Portfolio simulation:** Apply each asset's daily return to its current portfolio weight. Between annual rebalances, weights drift naturally with asset price changes.
3. **Performance analytics:** Compute compounded growth, CAGR, annualized daily-return volatility, a simplified Sharpe ratio, and peak-to-trough maximum drawdown.
4. **Visualization:** Plot all strategy values on a common $10,000 initial-investment scale.

Key definitions:

- `CAGR = (Ending Value / Beginning Value)^(1 / Years) - 1`
- `Annualized Volatility = Std Dev(Daily Returns) × sqrt(252)`
- `Sharpe (Rf=0) = Mean(Daily Returns) / Std Dev(Daily Returns) × sqrt(252)`
- `Maximum Drawdown = min(Portfolio Value / Running Peak - 1)`

## Limitations

- **Data quality and timing:** Yahoo Finance data and adjusted price history may be revised, incomplete, or unavailable. Re-running at a later date can change figures.
- **Illustrative portfolio proxies:** The All Weather allocation is a simplified published-style ETF proxy, not Bridgewater's proprietary implementation. A single fixed allocation cannot capture every form of risk-parity or tactical management.
- **Backtest assumptions:** Assumes frictionless year-end rebalancing at the closing mark; excludes transaction costs, taxes, liquidity, and bid-ask spread.
- **Metric choice:** Sharpe uses an assumed 0% risk-free rate. A more rigorous analysis would use an appropriate time-varying Treasury yield, assess inflation-adjusted returns, and test sensitivity to rebalancing frequency.
- **Scope:** This is a descriptive historical comparison, not a prediction or a causal test of whether diversification creates alpha. BRK.B is a stock investment, not a diversified ETF strategy.

## Technology

Python · pandas · NumPy · Matplotlib · yfinance

**Educational investment research project. Not financial advice.**
