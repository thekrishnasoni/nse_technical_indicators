#!/usr/bin/env python3
"""
NSE Technical Indicators Calculator

This utility calculates standard technical indicators (SMA, EMA, RSI, MACD,
Bollinger Bands) from historical stock price data CSV files and outputs
the results to a new CSV file. It also provides buy/sell signal analysis
and a terminal dashboard summary.
"""

import argparse
import os
import sys
from typing import Optional, List, Tuple
import numpy as np
import pandas as pd

# Technical Indicators Calculation Functions


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculates Simple Moving Average (SMA)."""
    return series.rolling(window=period).mean()


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculates Exponential Moving Average (EMA)."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing (EMA with alpha = 1/period)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()

    # Prevent division by zero
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)  # Default neutral RSI for division by zero


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculates MACD, MACD Signal, and MACD Histogram."""
    fast_ema = calculate_ema(series, fast)
    slow_ema = calculate_ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculates Upper, Middle (SMA), and Lower Bollinger Bands."""
    middle_band = calculate_sma(series, period)
    std_dev = series.rolling(window=period).std()
    upper_band = middle_band + (num_std * std_dev)
    lower_band = middle_band - (num_std * std_dev)
    return upper_band, middle_band, lower_band


def generate_trading_signals(df: pd.DataFrame, rsi_col: str, macd_col: str, macd_sig_col: str, bb_upper_col: str, bb_lower_col: str) -> pd.DataFrame:
    """
    Generates basic trading signals based on RSI, MACD, and Bollinger Bands.
    """
    close = df["Close Price"]
    rsi = df[rsi_col]
    macd = df[macd_col]
    macd_sig = df[macd_sig_col]
    bb_upper = df[bb_upper_col]
    bb_lower = df[bb_lower_col]

    # RSI Signals (Overbought > 70, Oversold < 30)
    rsi_signal = np.where(rsi > 70, "SELL (Overbought)", np.where(rsi < 30, "BUY (Oversold)", "NEUTRAL"))

    # MACD Crossover Signals (MACD crosses Signal)
    macd_diff = macd - macd_sig
    macd_diff_prev = macd_diff.shift(1)
    macd_signal = np.where((macd_diff > 0) & (macd_diff_prev <= 0), "BUY (Bullish Cross)",
                           np.where((macd_diff < 0) & (macd_diff_prev >= 0), "SELL (Bearish Cross)", "NEUTRAL"))

    # Bollinger Bands Breakthrough Signals
    bb_signal = np.where(close > bb_upper, "SELL (Above BB Upper)",
                         np.where(close < bb_lower, "BUY (Below BB Lower)", "NEUTRAL"))

    # Consolidated Signal
    buy_signals = 0
    sell_signals = 0
    for sig in [rsi_signal, macd_signal, bb_signal]:
        buy_signals += np.where(np.char.startswith(sig.astype(str), "BUY"), 1, 0)
        sell_signals += np.where(np.char.startswith(sig.astype(str), "SELL"), 1, 0)

    consolidated_signal = np.where(buy_signals >= 2, "STRONG BUY",
                                   np.where(buy_signals == 1, "BUY",
                                            np.where(sell_signals >= 2, "STRONG SELL",
                                                     np.where(sell_signals == 1, "SELL", "NEUTRAL"))))

    df["RSI_Signal"] = rsi_signal
    df["MACD_Signal"] = macd_signal
    df["BB_Signal"] = bb_signal
    df["Action_Signal"] = consolidated_signal
    return df


def display_dashboard(df: pd.DataFrame, symbol: str) -> None:
    """Displays a clean summary of latest indicators and signals."""
    if df.empty:
        return

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    print("=" * 80)
    print(f"  NSE Technical Indicators Dashboard | Symbol: {symbol.upper()}")
    print("=" * 80)
    print(f"  Latest Close: Rs. {latest.get('Close Price', 0.0):,.2f}  |  Date: {latest.get('Date')}")
    print("  " + "-" * 74)

    # Trend Indicators
    print("  TREND & MOMENTUM:")
    for col in df.columns:
        if col.startswith("SMA_") or col.startswith("EMA_"):
            print(f"    - {col:<12}: Rs. {latest[col]:<12,.2f}  (Previous: Rs. {prev[col]:,.2f})")

    # Oscillators
    print("\n  OSCILLATORS:")
    if "RSI_14" in df.columns:
        rsi_val = latest["RSI_14"]
        rsi_state = "Neutral"
        if rsi_val > 70:
            rsi_state = "Overbought"
        elif rsi_val < 30:
            rsi_state = "Oversold"
        print(f"    - RSI (14)    : {rsi_val:<12.2f}  ({rsi_state})")

    if "MACD_12_26" in df.columns:
        print(f"    - MACD Line   : {latest['MACD_12_26']:<12.4f}  |  Signal: {latest['MACD_Signal_9']:.4f}")
        print(f"    - Histogram   : {latest['MACD_Hist_9']:.4f}")

    # Volatility Bands
    print("\n  VOLATILITY BANDS (Bollinger Bands 20, 2):")
    if "BB_Middle_20" in df.columns:
        print(f"    - Upper Band  : Rs. {latest['BB_Upper_20']:<12,.2f}  |  Middle (SMA 20): Rs. {latest['BB_Middle_20']:,.2f}")
        print(f"    - Lower Band  : Rs. {latest['BB_Lower_20']:,.2f}")

    # Trading Signals Summary
    print("\n  TRADING SIGNALS SUMMARY:")
    print(f"    - RSI Signal  : {latest.get('RSI_Signal', 'NEUTRAL')}")
    print(f"    - MACD Signal : {latest.get('MACD_Signal', 'NEUTRAL')}")
    print(f"    - BB Signal   : {latest.get('BB_Signal', 'NEUTRAL')}")
    print(f"    - ACTION      : \033[1m{latest.get('Action_Signal', 'NEUTRAL')}\033[0m")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Calculate technical indicators from stock price CSV data.")
    parser.add_argument("-i", "--input", required=True, help="Input historical CSV file path")
    parser.add_argument("-o", "--output", help="Output CSV file path (defaults to {input}_indicators.csv)")
    parser.add_argument("--rsi-period", type=int, default=14, help="RSI period (default: 14)")
    parser.add_argument("--macd-fast", type=int, default=12, help="MACD Fast EMA period (default: 12)")
    parser.add_argument("--macd-slow", type=int, default=26, help="MACD Slow EMA period (default: 26)")
    parser.add_argument("--macd-signal", type=int, default=9, help="MACD Signal period (default: 9)")
    parser.add_argument("--bb-period", type=int, default=20, help="Bollinger Bands period (default: 20)")
    parser.add_argument("--bb-std", type=float, default=2.0, help="Bollinger Bands standard deviation multiplier (default: 2.0)")
    parser.add_argument("--sma", default="20,50,200", help="Comma-separated SMA periods (default: 20,50,200)")
    parser.add_argument("--ema", default="9,21", help="Comma-separated EMA periods (default: 9,21)")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        print(f"Error loading CSV file: {e}", file=sys.stderr)
        sys.exit(1)

    # Basic validations on CSV structure
    required_cols = ["Date", "Close Price"]
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Required column '{col}' is missing from the input CSV.", file=sys.stderr)
            sys.exit(1)

    # Parse and sort dates ascending
    df["Parsed_Date"] = pd.to_datetime(df["Date"], format="%d-%b-%Y", errors="coerce")
    df = df.dropna(subset=["Parsed_Date"]).sort_values("Parsed_Date").reset_index(drop=True)
    df = df.drop(columns=["Parsed_Date"])

    # Ensure Close Price is numeric
    df["Close Price"] = pd.to_numeric(df["Close Price"].astype(str).str.replace(",", ""), errors="coerce")
    df = df.dropna(subset=["Close Price"])

    if len(df) < 5:
        print("Error: Input file has too few rows to calculate indicators.", file=sys.stderr)
        sys.exit(1)

    # Determine symbol from CSV (if Symbol column exists)
    symbol = df["Symbol"].iloc[0] if "Symbol" in df.columns else "Stock"

    # 1. Calculate SMAs
    sma_periods = [int(p.strip()) for p in args.sma.split(",") if p.strip().isdigit()]
    for period in sma_periods:
        df[f"SMA_{period}"] = calculate_sma(df["Close Price"], period)

    # 2. Calculate EMAs
    ema_periods = [int(p.strip()) for p in args.ema.split(",") if p.strip().isdigit()]
    for period in ema_periods:
        df[f"EMA_{period}"] = calculate_ema(df["Close Price"], period)

    # 3. Calculate RSI
    rsi_col = f"RSI_{args.rsi_period}"
    df[rsi_col] = calculate_rsi(df["Close Price"], args.rsi_period)

    # 4. Calculate MACD
    macd_col = f"MACD_{args.macd_fast}_{args.macd_slow}"
    macd_sig_col = f"MACD_Signal_{args.macd_signal}"
    macd_hist_col = f"MACD_Hist_{args.macd_signal}"
    df[macd_col], df[macd_sig_col], df[macd_hist_col] = calculate_macd(df["Close Price"], args.macd_fast, args.macd_slow, args.macd_signal)

    # 5. Calculate Bollinger Bands
    bb_upper_col = f"BB_Upper_{args.bb_period}"
    bb_middle_col = f"BB_Middle_{args.bb_period}"
    bb_lower_col = f"BB_Lower_{args.bb_period}"
    df[bb_upper_col], df[bb_middle_col], df[bb_lower_col] = calculate_bollinger_bands(df["Close Price"], args.bb_period, args.bb_std)

    # 6. Generate Trading Signals
    df = generate_trading_signals(df, rsi_col, macd_col, macd_sig_col, bb_upper_col, bb_lower_col)

    # Set output path
    output_path = args.output if args.output else args.input.replace(".csv", "_indicators.csv")
    if output_path == args.input:
        output_path = args.input.replace(".csv", "_indicators_calc.csv")

    try:
        # Save output
        df.to_csv(output_path, index=False)
        print(f"Calculated all indicators successfully.")
        print(f"Saved results with indicators to: {output_path}\n")
        display_dashboard(df, symbol)
    except OSError as e:
        print(f"Error saving indicators output file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
