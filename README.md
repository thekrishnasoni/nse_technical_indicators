# NSE Technical Indicators Calculator

A command-line Python tool to calculate standard technical analysis indicators from historical stock price data and generate actionable buy/sell trading signals.

It is written in pure Python using `pandas` and `numpy`, avoiding compilation and dependency issues associated with C-based libraries like `ta-lib`.

## Features

- **Standard Indicators**:
  - Simple Moving Average (SMA)
  - Exponential Moving Average (EMA)
  - Relative Strength Index (RSI)
  - Moving Average Convergence Divergence (MACD, Signal Line, Histogram)
  - Bollinger Bands (Upper, Middle/SMA 20, Lower)
- **Signal Generation**: Computes momentum, trend crossover, and volatility breakthrough buy/sell signals per data point.
- **Action Signal**: Consolidates multiple indicators into a unified action recommendation (`STRONG BUY`, `BUY`, `NEUTRAL`, `SELL`, `STRONG SELL`).
- **Terminal Dashboard**: Prints a clean text dashboard summarizing the latest price, indicators, and actions.
- **Customizable Windows**: Allows overriding periods and parameters directly via command-line arguments.

## Requirements

- Python 3.6 or higher
- `pandas`
- `numpy`

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/thekrishnasoni/nse_technical_indicators.git
cd nse_technical_indicators
pip install -r requirements.txt
```

## Usage

### Run Calculator

Calculate all indicators for an input historical CSV file:
```bash
python calculator.py --input TCS_historical.csv
```

### Save Output with Custom Parameters

Customize moving average periods and set a custom output file:
```bash
python calculator.py --input TCS_historical.csv --sma 10,20,50,100 --ema 5,12 --rsi-period 14 --output tcs_indicators.csv
```

## Options

- `-i`, `--input`: Input historical CSV file path (from Historical Stock Data Fetcher).
- `-o`, `--output`: Output CSV file path (defaults to `{INPUT}_indicators.csv`).
- `--rsi-period`: RSI window period (default: `14`).
- `--macd-fast`: MACD fast EMA period (default: `12`).
- `--macd-slow`: MACD slow EMA period (default: `26`).
- `--macd-signal`: MACD signal period (default: `9`).
- `--bb-period`: Bollinger Bands window period (default: `20`).
- `--bb-std`: Bollinger Bands standard deviation multiplier (default: `2.0`).
- `--sma`: Comma-separated SMA periods to calculate (default: `20,50,200`).
- `--ema`: Comma-separated EMA periods to calculate (default: `9,21`).

## License

This project is licensed under the MIT License.
