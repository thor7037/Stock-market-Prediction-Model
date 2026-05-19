import pandas as pd

from sklearn.model_selection import (
    train_test_split
)

from sklearn.metrics import (

    mean_absolute_error,

    mean_squared_error,

    r2_score,
)

from xgboost import (
    XGBRegressor
)

import numpy as np

import joblib

# =====================================
# LOAD DATASET
# =====================================

print(
    "\nLoading dataset..."
)

df = pd.read_csv(
    "historical_data/dataset.csv"
)

# =====================================
# DROP UNUSED COLUMNS
# =====================================

drop_columns = [

    "Date",

    "Target",

    "Direction",
]

for column in drop_columns:

    if column in df.columns:

        df = df.drop(
            columns=[column]
        )

# =====================================
# FEATURES & TARGET
# =====================================

X = df.drop(
    columns=["NEXT_DAY_RETURN"]
)

y = df["NEXT_DAY_RETURN"]

# =====================================
# TRAIN TEST SPLIT
# =====================================

X_train, X_test, y_train, y_test = (

    train_test_split(

        X,

        y,

        test_size=0.2,

        random_state=42,

        shuffle=False,
    )
)

# =====================================
# MODEL
# =====================================

model = XGBRegressor(

    n_estimators=1200,

    max_depth=8,

    learning_rate=0.01,

    subsample=0.9,

    colsample_bytree=0.9,

    random_state=42,
)

# =====================================
# TRAIN
# =====================================

print(
    "\nTraining regression model..."
)

model.fit(

    X_train,

    y_train
)

# =====================================
# PREDICT
# =====================================

predictions = model.predict(
    X_test
)

# =====================================
# METRICS
# =====================================

mae = mean_absolute_error(

    y_test,

    predictions
)

rmse = np.sqrt(

    mean_squared_error(

        y_test,

        predictions
    )
)

r2 = r2_score(

    y_test,

    predictions
)

print(
    f"\nMAE: {round(mae, 4)}"
)

print(
    f"RMSE: {round(rmse, 4)}"
)

print(
    f"R2 Score: {round(r2, 4)}"
)

# =====================================
# FEATURE IMPORTANCE
# =====================================

importance_df = pd.DataFrame({

    "Feature": X.columns,

    "Importance":
    model.feature_importances_,
})

importance_df = (

    importance_df

    .sort_values(

        by="Importance",

        ascending=False
    )
)

print(
    "\nTop Features:\n"
)

print(
    importance_df.head(20)
)

# =====================================
# SAVE MODEL
# =====================================

joblib.dump(

    model,

    "ml/nifty_regression_model.pkl"
)

print(
    "\nRegression model saved!"
)