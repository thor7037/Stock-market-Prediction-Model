"""Build 10-year training datasets for index direction models."""

from __future__ import annotations

from pathlib import Path

from ml.feature_utils import build_training_frame

OUTPUT_DIR = Path("historical_data")
SYMBOLS = {
    "^NSEI": "nifty",
    "^NSEBANK": "banknifty",
    "^BSESN": "sensex",
}


def build_dataset(symbol: str, filename: str) -> None:
    print(f"\nBuilding dataset for {symbol}...")

    df = build_training_frame(symbol, period="10y")
    if df.empty:
        raise ValueError(f"No usable OHLCV data for {symbol}")

    target_dist = df["Target"].value_counts(normalize=True).sort_index()
    print(f"\nTarget distribution for {symbol}:")
    print(target_dist.to_string())

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{filename}.csv"
    df.to_csv(output_path, index=False)

    print(f"\nSaved {len(df):,} rows to {output_path}")


if __name__ == "__main__":
    for symbol, filename in SYMBOLS.items():
        build_dataset(symbol, filename)
