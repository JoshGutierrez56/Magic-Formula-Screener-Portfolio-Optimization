# 🔮 Magic Formula Portfolio Optimizer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![yfinance](https://img.shields.io/badge/data-Yahoo%20Finance-purple.svg)](https://github.com/ranaroussi/yfinance)

A quantitative stock screening and portfolio optimization system implementing **Joel Greenblatt's Magic Formula** investing strategy, enhanced with **Grinold-Kahn analytics** for institutional-grade portfolio construction.

<p align="center">
  <img src="docs/images/magic_formula_diagram.png" alt="Magic Formula Process" width="600">
</p>

## 📖 Overview

The **Magic Formula** ranks stocks by combining two factors:

1. **Earnings Yield** (EBIT/EV) — identifies cheap stocks
2. **Return on Capital** (EBIT/Net Working Capital + Net Fixed Assets) — identifies good companies

This implementation screens the **Russell 3000** universe, applies the Magic Formula ranking, and outputs an Excel workbook ready for portfolio optimization with Excel Solver.

### Key Features

- 📊 **Full Russell 3000 Screening** — 2,500+ stocks analyzed
- 🔢 **Covariance Matrix** — Actual correlations, not simplified assumptions  
- 📈 **Grinold-Kahn Analytics** — IC, Breadth, Transfer Coefficient tracking
- 📋 **Excel Solver Ready** — Optimize for Sharpe Ratio or Information Ratio
- ⚡ **Rate-Limit Handling** — Robust Yahoo Finance data fetching

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/magic-formula-portfolio.git
cd magic-formula-portfolio

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Run the screener (outputs magic_formula_output.xlsx)
python src/screener.py

# Calculate covariance matrix and update the workbook
python src/covariance.py
```

### Jupyter Notebook

```python
%run src/screener.py
%run src/covariance.py
```

## 📁 Project Structure

```
magic-formula-portfolio/
├── src/
│   ├── screener.py        # Main Magic Formula screener
│   └── covariance.py      # Covariance matrix calculator
├── data/
│   ├── russell_3000.csv   # Russell 3000 ticker universe
│   └── iwv_weights.csv    # IWV ETF benchmark weights
├── examples/
│   └── portfolio_optimizer.xlsx  # Example output with Solver setup
├── docs/
│   ├── methodology.md     # Detailed methodology
│   └── images/            # Documentation images
├── requirements.txt
├── LICENSE
└── README.md
```

## 📊 Output

The screener generates an Excel workbook with:

| Sheet | Description |
|-------|-------------|
| **All Stocks** | Raw data for all screened stocks |
| **MF Ranked** | Filtered stocks ranked by Magic Formula |
| **Selected Stocks** | Top 25 stocks for the portfolio |
| **Summary** | Portfolio statistics |

After running `covariance.py`:

| Sheet | Description |
|-------|-------------|
| **Covariance Matrix** | 25×25 annualized covariance matrix |
| **Correlation Matrix** | Pairwise correlations |

## 🎯 Portfolio Optimization

### Using Excel Solver

1. Open the output Excel file
2. Go to **Data → Solver**
3. Configure:
   - **Objective**: Maximize Sharpe Ratio (or minimize Tracking Error)
   - **By Changing**: Portfolio weights column
   - **Constraints**:
     - Sum of weights = 100%
     - Each weight ≥ 0% (no shorting)
     - Each weight ≤ 10% (concentration limit)

### Key Formulas

**Portfolio Volatility** (using covariance matrix):
```
σ_p = √(w'Σw)
Excel: =SQRT(SUMPRODUCT(weights, MMULT(cov_matrix, weights)))
```

**Tracking Error** (vs benchmark):
```
TE = √(w_active'Σw_active)
```

**Information Ratio**:
```
IR = (R_p - R_b) / TE
```

## ⚙️ Configuration

### Screener Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--top` | 25 | Number of stocks to select |
| `--min-mcap` | 2.0 | Minimum market cap ($B) |
| `--max-beta` | 2.5 | Maximum beta (filters volatile stocks) |
| `--delay` | 0.25 | API delay (seconds) |

### Example

```bash
# Select top 30 stocks, exclude high-beta
python src/screener.py --top 30 --max-beta 2.0

# Use custom universe
python src/screener.py --universe data/sp500.csv
```

## 📚 Methodology

### Magic Formula Ranking

1. **Calculate Earnings Yield** = EBITDA / Enterprise Value
2. **Calculate Return on Capital** = ROE (or ROA × 2 as proxy)
3. **Rank all stocks** by each metric (1 = best)
4. **Combined Score** = EY Rank + ROC Rank
5. **Select top N** stocks with lowest combined score

### Filtering Criteria

- Market Cap ≥ $2B (excludes micro-caps)
- P/E between 0 and 100 (excludes loss-makers and extreme valuations)
- ROC ≥ 5% (minimum profitability)
- Beta ≤ 2.5 (excludes highly volatile stocks)

### Why These Filters?

| Filter | Rationale |
|--------|-----------|
| Market Cap | Ensures liquidity, analyst coverage |
| P/E > 0 | Excludes unprofitable companies |
| P/E < 100 | Excludes speculative growth stocks |
| ROC ≥ 5% | Ensures minimum capital efficiency |
| Beta ≤ 2.5 | Filters crypto-correlated, meme stocks |

## 📈 Performance Considerations

### Expected Characteristics

Based on Greenblatt's research and backtests:

- **Expected Alpha**: 5-10% annually over market
- **Tracking Error**: 8-15% (concentrated portfolio)
- **Information Ratio**: 0.5-1.0
- **Turnover**: ~50% annually (rebalance every 6-12 months)

### Limitations

- **Data Quality**: Yahoo Finance data may have gaps
- **Transaction Costs**: Not included in optimization
- **Tax Efficiency**: Not considered
- **Capacity**: Strategy works best under $100M AUM

## 🔗 References

- Greenblatt, J. (2010). *The Little Book That Still Beats the Market*
- Grinold, R. & Kahn, R. (1999). *Active Portfolio Management*
- [Yahoo Finance API](https://github.com/ranaroussi/yfinance)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational purposes only. It is not financial advice. Past performance does not guarantee future results. Always do your own research before making investment decisions.

---

<p align="center">
  Made with 🔮 for quantitative investors
</p>
