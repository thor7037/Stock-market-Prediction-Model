"""Feature engineering for ML pipeline."""

from ml.feature_utils import enrich_nifty_features


def build_features(ohlcv):
    return enrich_nifty_features(ohlcv)
