import pandas as pd

# =====================================
# CLASSIFY MARKET REGIME
# =====================================

def classify_regime(df):

    # =================================
    # VOLATILITY
    # =================================

    volatility = (

        df["^NSEI_pct"]

        .rolling(10)

        .std()
    )

    # =================================
    # TREND
    # =================================

    short_ma = (

        df["^NSEI"]

        .rolling(20)

        .mean()
    )

    long_ma = (

        df["^NSEI"]

        .rolling(50)

        .mean()
    )

    # =================================
    # REGIME COLUMN
    # =================================

    regime = []

    # =================================
    # LOOP
    # =================================

    for i in range(len(df)):

        current_volatility = (
            volatility.iloc[i]
        )

        short_value = (
            short_ma.iloc[i]
        )

        long_value = (
            long_ma.iloc[i]
        )

        # =============================
        # UNKNOWN
        # =============================

        if pd.isna(
            current_volatility
        ):

            regime.append(
                "UNKNOWN"
            )

            continue

        # =============================
        # HIGH VOLATILITY
        # =============================

        if current_volatility > 1.5:

            regime.append(
                "HIGH_VOLATILITY"
            )

        # =============================
        # BULL TREND
        # =============================

        elif short_value > long_value:

            regime.append(
                "BULL"
            )

        # =============================
        # BEAR TREND
        # =============================

        elif short_value < long_value:

            regime.append(
                "BEAR"
            )

        # =============================
        # SIDEWAYS
        # =============================

        else:

            regime.append(
                "SIDEWAYS"
            )

    # =================================
    # SAVE REGIME
    # =================================

    df["MARKET_REGIME"] = regime

    return df