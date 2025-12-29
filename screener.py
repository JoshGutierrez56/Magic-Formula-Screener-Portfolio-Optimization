#!/usr/bin/env python3
"""
Magic Formula Stock Screener
============================
Implementation of Joel Greenblatt's Magic Formula investing strategy.

The Magic Formula ranks stocks by combining:
    1. Earnings Yield (EV/EBITDA) - "cheap" stocks
    2. Return on Capital (ROC) - "good" companies

Reference: "The Little Book That Beats the Market" by Joel Greenblatt

Usage:
    python screener.py                    # Run with defaults (25 stocks)
    python screener.py --top 30           # Select top 30 stocks
    python screener.py --top 50 --delay 0.3  # 50 stocks, slower fetching
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_CONFIG = {
    # Screening filters
    "min_market_cap": 2.0,      # Minimum market cap ($B)
    "max_pe": 100,              # Maximum P/E ratio
    "min_roc": 5.0,             # Minimum Return on Capital (%)
    "max_beta": 2.5,            # Maximum beta (filter volatile stocks)
    
    # Portfolio construction
    "top_n_stocks": 25,         # Number of stocks to select (Greenblatt: 20-30)
    "max_position_weight": 0.10, # Maximum weight per position
    
    # Data fetching
    "fetch_delay": 0.25,        # Delay between API calls (seconds)
    
    # Output
    "output_file": "magic_formula_output.xlsx",
}


# ============================================================================
# DATA LOADING
# ============================================================================

def load_universe(filepath: Optional[str] = None) -> list:
    """
    Load stock universe from CSV file or use built-in list.
    
    Args:
        filepath: Path to CSV file with 'Ticker' column
        
    Returns:
        List of ticker symbols
    """
    # Try to find ticker file
    search_paths = [
        Path(filepath) if filepath else None,
        Path("data/russell_3000.csv"),
        Path("../data/russell_3000.csv"),
        Path("russell_3000.csv"),
    ]
    
    for path in search_paths:
        if path and path.exists():
            df = pd.read_csv(path)
            tickers = df["Ticker"].dropna().tolist()
            print(f"✓ Loaded {len(tickers)} tickers from {path}")
            return tickers
    
    # Fallback to built-in large-cap universe
    print("⚠ No ticker file found, using built-in universe (~250 stocks)")
    return _get_builtin_universe()


def _get_builtin_universe() -> list:
    """Built-in stock universe (S&P 500 + mid-caps)."""
    return [
        # Mega Cap
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "BRK-B", "TSLA", "LLY", "AVGO",
        "JPM", "UNH", "V", "XOM", "MA", "COST", "HD", "PG", "JNJ", "NFLX",
        "WMT", "ABBV", "ORCL", "CRM", "BAC", "MRK", "CVX", "KO", "AMD", "PEP",
        # Large Cap
        "TMO", "CSCO", "ACN", "LIN", "MCD", "ABT", "ADBE", "WFC", "IBM", "GE",
        "QCOM", "CAT", "TXN", "INTU", "NOW", "ISRG", "AMGN", "VZ", "BKNG", "PFE",
        "SPGI", "DHR", "HON", "AXP", "RTX", "CMCSA", "T", "NEE", "LOW", "UNP",
        "PLD", "ETN", "SYK", "DE", "VRTX", "LMT", "BLK", "GS", "ADP", "SCHW",
        "BMY", "MDLZ", "CB", "GILD", "TJX", "ADI", "MMC", "REGN", "CI", "SBUX",
        "SO", "DUK", "COP", "EOG", "MO", "SLB", "MCK", "AMT", "ZTS", "FI",
        # Mid Cap Value
        "ICE", "PH", "CL", "GD", "NKE", "CME", "TGT", "USB", "NXPI", "MMM",
        "ALL", "TRV", "AFL", "PGR", "HIG", "MET", "PRU", "AIG", "WU", "BEN",
        "DVA", "HCA", "CNC", "HUM", "CVS", "CAH", "MCK", "BDX", "BSX", "MDT",
        "FAST", "ODFL", "CPRT", "FICO", "PWR", "EME", "FDX", "UPS", "CSX", "NSC",
        "MLM", "VMC", "FCX", "NEM", "NUE", "STLD", "CLF", "AA", "CF", "MOS",
        "DVN", "FANG", "OXY", "HAL", "BKR", "MPC", "VLO", "PSX", "OKE", "WMB",
        # Additional Value Stocks
        "CALM", "HCI", "RRR", "BYD", "CHTR", "LNG", "HRB", "APAM", "ACI", "KD",
        "BBWI", "TIGO", "WFRD", "HG", "KMB", "SLDE", "NATL", "PTCT", "PPC",
    ]


# ============================================================================
# DATA FETCHING
# ============================================================================

def fetch_stock_data(ticker: str) -> Optional[dict]:
    """
    Fetch fundamental data for a single stock.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary of stock data or None if fetch fails
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or not info.get("regularMarketPrice"):
            return None
        
        # Basic info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        mcap = (info.get("marketCap") or 0) / 1e9
        
        if price <= 0 or mcap < 0.5:
            return None
        
        sector = info.get("sector") or "Unknown"
        name = (info.get("shortName") or info.get("longName") or ticker)[:40]
        
        # Valuation metrics
        pe = info.get("trailingPE") or 0
        pe = pe if 0 < pe < 1000 else 999
        
        ev_ebitda = info.get("enterpriseToEbitda") or 0
        ev_ebitda = ev_ebitda if 0 < ev_ebitda < 100 else 20
        
        pb = info.get("priceToBook") or 1
        
        # Profitability metrics
        roe = (info.get("returnOnEquity") or 0) * 100
        roa = (info.get("returnOnAssets") or 0) * 100
        roe = max(min(roe, 150), -100)
        roa = max(min(roa, 50), -50)
        
        profit_margin = (info.get("profitMargins") or 0) * 100
        
        # ROC estimate (using ROE as proxy)
        roc = max(min(roe if roe > 0 else roa * 2, 100), 0)
        
        # Risk metrics
        beta = info.get("beta") or 1.0
        beta_raw = beta
        beta = max(min(beta, 4), -0.5)
        
        # Expected return from analyst targets
        target = info.get("targetMeanPrice") or info.get("targetMedianPrice") or 0
        if price > 0 and target > 0:
            exp_ret = max(min((target / price) - 1, 0.5), -0.5)
        else:
            exp_ret = 0.10
        
        # Volatility estimate from beta
        volatility = max(min(abs(beta_raw or 1) * 0.20, 1.5), 0.15)
        
        # Dividend yield
        div_yield = (info.get("dividendYield") or 0) * 100
        div_yield = max(min(div_yield, 20), 0)
        
        return {
            "Ticker": ticker,
            "Company": name,
            "Sector": sector,
            "Price": round(price, 2),
            "Mkt Cap ($B)": round(mcap, 1),
            "P/E": round(pe, 1),
            "EV/EBITDA": round(ev_ebitda, 1),
            "P/B": round(pb, 2),
            "ROE (%)": round(roe, 1),
            "ROA (%)": round(roa, 1),
            "ROC (%)": round(roc, 1),
            "Profit Margin (%)": round(profit_margin, 1),
            "Beta": round(beta, 2),
            "Beta_Raw": round(beta_raw if beta_raw else 1.0, 2),
            "Volatility": round(volatility, 3),
            "Target Price": round(target, 2),
            "Expected Return": round(exp_ret, 3),
            "Div Yield (%)": round(div_yield, 2),
        }
        
    except Exception:
        return None


def fetch_all_stocks(tickers: list, delay: float = 0.25) -> pd.DataFrame:
    """
    Fetch data for all stocks with rate limiting.
    
    Args:
        tickers: List of ticker symbols
        delay: Delay between API calls (seconds)
        
    Returns:
        DataFrame with stock data
    """
    print(f"\n📊 Fetching data for {len(tickers)} stocks...")
    print(f"   Estimated time: {len(tickers) * delay / 60:.1f} minutes")
    print("=" * 60)
    
    data = []
    failed = []
    start_time = time.time()
    
    for i, ticker in enumerate(tickers):
        # Progress update every 50 stocks
        if i % 50 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining = (len(tickers) - i) / rate / 60 if rate > 0 else 0
            print(f"  [{i:4}/{len(tickers)}] {len(data)} fetched, ~{remaining:.1f} min remaining")
        
        result = fetch_stock_data(ticker)
        if result:
            data.append(result)
        else:
            failed.append(ticker)
        
        time.sleep(delay)
    
    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"✓ Fetched {len(data)} stocks in {elapsed/60:.1f} minutes")
    print(f"✗ Failed: {len(failed)} stocks")
    
    return pd.DataFrame(data)


# ============================================================================
# MAGIC FORMULA RANKING
# ============================================================================

def apply_magic_formula(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Apply Magic Formula ranking to stocks.
    
    The Magic Formula combines:
        1. Earnings Yield (1/EV/EBITDA) - higher is better
        2. Return on Capital (ROC) - higher is better
    
    Args:
        df: DataFrame with stock data
        config: Configuration dictionary
        
    Returns:
        DataFrame filtered and ranked by Magic Formula
    """
    print("\n🔮 Applying Magic Formula ranking...")
    
    # Calculate Earnings Yield
    df["Earnings Yield"] = df["EV/EBITDA"].apply(lambda x: 1/x if x > 0 else 0)
    
    # Show high-beta stocks being filtered
    high_beta = df[df["Beta_Raw"] > config["max_beta"]]
    if len(high_beta) > 0:
        print(f"\n  Filtering {len(high_beta)} high-beta stocks (β > {config['max_beta']}):")
        for _, row in high_beta.head(5).iterrows():
            print(f"    {row['Ticker']:6} β={row['Beta_Raw']:.2f}")
        if len(high_beta) > 5:
            print(f"    ... and {len(high_beta) - 5} more")
    
    # Apply filters
    mask = (
        (df["Mkt Cap ($B)"] >= config["min_market_cap"]) &
        (df["P/E"] <= config["max_pe"]) &
        (df["P/E"] > 0) &
        (df["ROC (%)"] >= config["min_roc"]) &
        (df["Beta_Raw"] <= config["max_beta"])
    )
    
    df_filtered = df[mask].copy()
    print(f"\n  Stocks passing filters: {len(df_filtered)} / {len(df)}")
    
    if len(df_filtered) == 0:
        return df_filtered
    
    # Rank by Earnings Yield (higher = better = lower rank number)
    df_filtered["EY Rank"] = df_filtered["Earnings Yield"].rank(ascending=False, method="first")
    
    # Rank by ROC (higher = better = lower rank number)
    df_filtered["ROC Rank"] = df_filtered["ROC (%)"].rank(ascending=False, method="first")
    
    # Combined Magic Formula Score (lower = better)
    df_filtered["MF Score"] = df_filtered["EY Rank"] + df_filtered["ROC Rank"]
    df_filtered["MF Rank"] = df_filtered["MF Score"].rank(method="first")
    
    df_filtered = df_filtered.sort_values("MF Rank")
    
    # Display top 10
    print(f"\n  Top 10 Magic Formula Stocks:")
    print(f"  {'Rank':<5} {'Ticker':<7} {'EY':<9} {'ROC':<9} {'P/E':<7} {'Sector'}")
    print(f"  {'-'*55}")
    for _, row in df_filtered.head(10).iterrows():
        print(f"  {int(row['MF Rank']):<5} {row['Ticker']:<7} "
              f"{row['Earnings Yield']:.1%}{'':3} {row['ROC (%)']:.1f}%{'':4} "
              f"{row['P/E']:.1f}{'':3} {row['Sector'][:12]}")
    
    return df_filtered


# ============================================================================
# OUTPUT
# ============================================================================

def load_benchmark_weights(tickers: list) -> dict:
    """Load IWV (Russell 3000) benchmark weights if available."""
    search_paths = [
        Path("data/iwv_weights.csv"),
        Path("../data/iwv_weights.csv"),
        Path("iwv_weights.csv"),
    ]
    
    for path in search_paths:
        if path.exists():
            df = pd.read_csv(path)
            weights = dict(zip(df["Ticker"], df["Weight"]))
            return weights
    
    return {}


def export_results(
    df_all: pd.DataFrame,
    df_ranked: pd.DataFrame,
    config: dict,
    output_file: str
) -> None:
    """
    Export results to Excel workbook.
    
    Args:
        df_all: All fetched stock data
        df_ranked: Filtered and ranked stocks
        config: Configuration dictionary
        output_file: Output file path
    """
    print(f"\n📁 Exporting to {output_file}...")
    
    # Select top N stocks
    n = config["top_n_stocks"]
    df_selected = df_ranked.head(n).copy()
    
    # Cap extreme expected returns
    df_selected["Expected Return"] = df_selected["Expected Return"].clip(-0.5, 0.5)
    
    # Portfolio weights (equal weight)
    df_selected["Portfolio Weight"] = 1 / len(df_selected)
    
    # Benchmark weights
    bench_weights = load_benchmark_weights(df_selected["Ticker"].tolist())
    if bench_weights:
        df_selected["Bench Weight"] = df_selected["Ticker"].map(bench_weights).fillna(0)
        print(f"  ✓ Using IWV benchmark weights (sum: {df_selected['Bench Weight'].sum():.2%})")
    else:
        df_selected["Bench Weight"] = 1 / len(df_selected)
        print(f"  ⚠ No benchmark weights found, using equal weight")
    
    # Active weights
    df_selected["Active Weight"] = df_selected["Portfolio Weight"] - df_selected["Bench Weight"]
    
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # Sheet 1: All Data
        df_all.to_excel(writer, sheet_name="All Stocks", index=False)
        
        # Sheet 2: Ranked
        df_ranked.to_excel(writer, sheet_name="MF Ranked", index=False)
        
        # Sheet 3: Selected Portfolio
        cols = [
            "MF Rank", "Ticker", "Company", "Sector", "Price", "Mkt Cap ($B)",
            "P/E", "Earnings Yield", "ROC (%)", "MF Score", "Beta", "Volatility",
            "Expected Return", "Bench Weight", "Portfolio Weight", "Active Weight"
        ]
        df_selected[[c for c in cols if c in df_selected.columns]].to_excel(
            writer, sheet_name="Selected Stocks", index=False
        )
        
        # Sheet 4: Summary
        summary = pd.DataFrame({
            "Metric": [
                "Date Generated",
                "Stocks Screened",
                "Stocks Passing Filters",
                "Portfolio Size",
                "",
                "Avg Expected Return",
                "Avg Earnings Yield",
                "Avg ROC",
                "Avg Beta",
                "Avg P/E",
            ],
            "Value": [
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                len(df_all),
                len(df_ranked),
                len(df_selected),
                "",
                f"{df_selected['Expected Return'].mean():.1%}",
                f"{df_selected['Earnings Yield'].mean():.1%}",
                f"{df_selected['ROC (%)'].mean():.1f}%",
                f"{df_selected['Beta'].mean():.2f}",
                f"{df_selected['P/E'].mean():.1f}",
            ]
        })
        summary.to_excel(writer, sheet_name="Summary", index=False)
    
    print(f"✓ Exported to {output_file}")
    print(f"\n  Sheets:")
    print(f"    • All Stocks: {len(df_all)} rows")
    print(f"    • MF Ranked: {len(df_ranked)} rows")
    print(f"    • Selected Stocks: {len(df_selected)} rows")
    print(f"    • Summary")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Magic Formula Stock Screener",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python screener.py                  # Run with defaults
    python screener.py --top 30         # Select top 30 stocks
    python screener.py --universe data/sp500.csv  # Custom universe
        """
    )
    parser.add_argument("--top", type=int, default=25, help="Number of stocks to select (default: 25)")
    parser.add_argument("--delay", type=float, default=0.25, help="API delay in seconds (default: 0.25)")
    parser.add_argument("--universe", type=str, help="Path to ticker CSV file")
    parser.add_argument("--output", type=str, default="magic_formula_output.xlsx", help="Output file")
    parser.add_argument("--min-mcap", type=float, default=2.0, help="Min market cap in $B (default: 2)")
    parser.add_argument("--max-beta", type=float, default=2.5, help="Max beta (default: 2.5)")
    
    # Handle Jupyter environment
    if "ipykernel" in sys.modules:
        args = argparse.Namespace(
            top=25, delay=0.25, universe=None, 
            output="magic_formula_output.xlsx",
            min_mcap=2.0, max_beta=2.5
        )
        print("🔮 Running in Jupyter mode with defaults")
    else:
        args = parser.parse_args()
    
    # Build config
    config = DEFAULT_CONFIG.copy()
    config["top_n_stocks"] = args.top
    config["fetch_delay"] = args.delay
    config["output_file"] = args.output
    config["min_market_cap"] = args.min_mcap
    config["max_beta"] = args.max_beta
    
    # Header
    print("=" * 60)
    print("🔮 MAGIC FORMULA STOCK SCREENER")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Min Market Cap: ${config['min_market_cap']}B")
    print(f"  Max P/E: {config['max_pe']}")
    print(f"  Min ROC: {config['min_roc']}%")
    print(f"  Max Beta: {config['max_beta']}")
    print(f"  Select Top: {config['top_n_stocks']} stocks")
    
    # Load universe
    tickers = load_universe(args.universe)
    
    # Fetch data
    df_all = fetch_all_stocks(tickers, delay=config["fetch_delay"])
    
    if len(df_all) == 0:
        print("\n❌ No data fetched. Check your internet connection.")
        sys.exit(1)
    
    # Data quality check
    print(f"\n📋 Data Quality:")
    print(f"  ROC range: {df_all['ROC (%)'].min():.1f}% to {df_all['ROC (%)'].max():.1f}%")
    print(f"  P/E range: {df_all['P/E'].min():.1f} to {df_all['P/E'].max():.1f}")
    print(f"  Beta range: {df_all['Beta_Raw'].min():.2f} to {df_all['Beta_Raw'].max():.2f}")
    
    # Apply Magic Formula
    df_ranked = apply_magic_formula(df_all, config)
    
    if len(df_ranked) == 0:
        print("\n❌ No stocks passed filters.")
        sys.exit(1)
    
    # Export results
    export_results(df_all, df_ranked, config, config["output_file"])
    
    # Final summary
    df_selected = df_ranked.head(config["top_n_stocks"])
    print("\n" + "=" * 60)
    print(f"✅ COMPLETE!")
    print("=" * 60)
    print(f"\n📊 Portfolio Summary:")
    print(f"  Expected Return: {df_selected['Expected Return'].mean():.1%}")
    print(f"  Earnings Yield:  {df_selected['Earnings Yield'].mean():.1%}")
    print(f"  Avg ROC:         {df_selected['ROC (%)'].mean():.1f}%")
    print(f"  Avg Beta:        {df_selected['Beta'].mean():.2f}")


if __name__ == "__main__":
    main()
