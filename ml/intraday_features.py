import yfinance as yf

import pandas as pd

# =====================================
# FETCH INTRADAY FEATURES
# =====================================

def get_intraday_features():

    try:

        # =================================
        # DOWNLOAD 5 MIN DATA
        # =================================

        df = yf.download(

            "^NSEI",

            period="5d",

            interval="5m",

            progress=False,
        )

        # =================================
        # CHECK EMPTY
        # =================================

        if df.empty:

            print(
                "No intraday data found"
            )

            return None

        # =================================
        # REMOVE NULL VALUES
        # =================================

        df = df.dropna()

        # =================================
        # FIX SERIES
        # =================================

        close_prices = (
            df["Close"]
            .squeeze()
        )

        high_prices = (
            df["High"]
            .squeeze()
        )

        low_prices = (
            df["Low"]
            .squeeze()
        )

        volumes = (
            df["Volume"]
            .squeeze()
        )

        # =================================
        # CURRENT PRICE
        # =================================

        current_price = float(
            close_prices.iloc[-1]
        )

        previous_close = float(
            close_prices.iloc[-2]
        )

        # =================================
        # MOMENTUM
        # =================================

        momentum = (

            (
                current_price
                - previous_close
            )

            / previous_close

        ) * 100

        # =================================
        # VOLUME SPIKE
        # =================================

        avg_volume = float(

            volumes
            .tail(20)
            .mean()
        )

        latest_volume = float(
            volumes.iloc[-1]
        )

        # Safe default
        volume_spike = 1

        if avg_volume > 0:

            volume_spike = (

                latest_volume
                / avg_volume
            )

        # =================================
        # VWAP
        # =================================

        # Safe fallback
        vwap = current_price

        total_volume = (
            volumes.sum()
        )

        if total_volume > 0:

            vwap = (

                (
                    close_prices
                    * volumes
                ).sum()

                / total_volume
            )

        # =================================
        # DAY HIGH / LOW
        # =================================

        day_high = float(
            high_prices.max()
        )

        day_low = float(
            low_prices.min()
        )

        # =================================
        # BREAKOUT STRENGTH
        # =================================

        breakout_strength = 0

        range_value = (
            day_high - day_low
        )

        if range_value > 0:

            breakout_strength = (

                (
                    current_price
                    - day_low
                )

                / range_value
            )

        # =================================
        # RETURN FEATURES
        # =================================

        return {

            "intraday_momentum":
            round(
                momentum,
                2,
            ),

            "volume_spike":
            round(
                volume_spike,
                2,
            ),

            "vwap":
            round(
                float(vwap),
                2,
            ),

            "breakout_strength":
            round(
                breakout_strength,
                2,
            ),

            "day_high":
            round(
                day_high,
                2,
            ),

            "day_low":
            round(
                day_low,
                2,
            ),

            "current_price":
            round(
                current_price,
                2,
            ),
        }

    except Exception as error:

        print(
            "\nINTRADAY ERROR:\n"
        )

        print(error)

        return None

# =====================================
# TEST
# =====================================

if __name__ == "__main__":

    result = (
        get_intraday_features()
    )

    print(
        "\nINTRADAY FEATURES:\n"
    )

    print(result)