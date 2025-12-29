# Methodology

## The Magic Formula

The Magic Formula was developed by Joel Greenblatt and published in his 2005 book *"The Little Book That Beats the Market"*. The strategy systematically identifies stocks that are both **cheap** (high earnings yield) and **good** (high return on capital).

### Core Metrics

#### Earnings Yield (EY)

Measures how cheap a stock is relative to its earnings:

```
Earnings Yield = EBIT / Enterprise Value
```

Where:
- **EBIT** = Earnings Before Interest and Taxes
- **Enterprise Value** = Market Cap + Debt - Cash

In this implementation, we use `1 / EV/EBITDA` as a proxy.

#### Return on Capital (ROC)

Measures how efficiently a company uses its capital:

```
ROC = EBIT / (Net Working Capital + Net Fixed Assets)
```

We use **Return on Equity (ROE)** as a proxy, which is readily available from financial data providers.

### Ranking Process

1. Rank all stocks by Earnings Yield (1 = highest EY)
2. Rank all stocks by Return on Capital (1 = highest ROC)
3. Combined Score = EY Rank + ROC Rank
4. Select stocks with the lowest combined scores

---

## Portfolio Construction

### Grinold-Kahn Framework

The **Fundamental Law of Active Management** (Grinold & Kahn, 1999):

```
IR = IC × √BR × TC
```

Where:
- **IR** = Information Ratio (active return / tracking error)
- **IC** = Information Coefficient (correlation between forecasts and returns)
- **BR** = Breadth (number of independent bets)
- **TC** = Transfer Coefficient (implementation efficiency)

### Portfolio Volatility

For accurate risk measurement, we calculate portfolio volatility using the covariance matrix:

```
σ²_p = w'Σw
```

Where:
- **w** = vector of portfolio weights
- **Σ** = covariance matrix of returns
- **σ_p** = portfolio volatility (standard deviation)

This captures the actual correlations between stocks, rather than assuming a constant average correlation.

### Tracking Error

Tracking error measures how much the portfolio deviates from its benchmark:

```
TE = √(w_a'Σw_a)
```

Where:
- **w_a** = active weights (portfolio weight - benchmark weight)

### Information Ratio

The key performance metric for active managers:

```
IR = Active Return / Tracking Error
   = (R_p - R_b) / TE
```

---

## Data Sources

### Yahoo Finance

We use the `yfinance` library to fetch:
- Current prices
- Fundamental ratios (P/E, EV/EBITDA, ROE, etc.)
- Analyst price targets
- Beta
- Historical prices (for covariance calculation)

### Russell 3000 Universe

The screening universe is the Russell 3000 index, obtained from IWV (iShares Russell 3000 ETF) holdings.

### Benchmark Weights

IWV ETF weights are used as the market-cap weighted benchmark for:
- Tracking error calculation
- Active weight determination
- Information ratio computation

---

## Filtering Criteria

| Filter | Value | Rationale |
|--------|-------|-----------|
| Min Market Cap | $2B | Ensures liquidity, reduces data quality issues |
| Max P/E | 100 | Excludes speculative growth stocks |
| P/E > 0 | - | Excludes loss-making companies |
| Min ROC | 5% | Minimum profitability threshold |
| Max Beta | 2.5 | Excludes highly volatile/speculative stocks |

### Why Beta Filter?

Stocks with very high beta (>2.5) often include:
- Cryptocurrency-correlated companies (MSTR, COIN)
- Meme stocks with retail speculation
- Companies with unstable business models

These add volatility without improving expected returns.

---

## Optimization

### Objective Functions

1. **Maximize Sharpe Ratio**: (Return - Risk-Free Rate) / Volatility
2. **Maximize Information Ratio**: Active Return / Tracking Error
3. **Minimize Tracking Error**: Subject to return constraint

### Constraints

| Constraint | Value | Purpose |
|------------|-------|---------|
| Sum of weights | 100% | Fully invested |
| Min weight | 0% | No shorting |
| Max weight | 10% | Diversification |

### Excel Solver Setup

1. **Objective Cell**: Sharpe Ratio or IR
2. **Changing Cells**: Portfolio weight column
3. **Constraints**: As above

---

## References

1. Greenblatt, J. (2010). *The Little Book That Still Beats the Market*. Wiley.
2. Grinold, R. & Kahn, R. (1999). *Active Portfolio Management*. McGraw-Hill.
3. Asness, C., Frazzini, A., & Pedersen, L. (2019). Quality Minus Junk. *Review of Accounting Studies*.
