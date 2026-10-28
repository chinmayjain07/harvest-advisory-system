import os
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.linear_model import RidgeCV
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
import shap

from feature_engineering import build_crop_feature_matrix, get_feature_columns

def compute_metrics(y_true, y_pred, y_naive=None):
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    mape = float(mean_absolute_percentage_error(y_true, y_pred) * 100)
    me = float(np.mean(y_pred - y_true))
    
    rrmse = None
    if y_naive is not None:
        rmse_naive = float(np.sqrt(mean_squared_error(y_true, y_naive)))
        rrmse = float(rmse / rmse_naive) if rmse_naive > 0 else 1.0
        
    return {
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "mape_pct": round(mape, 2),
        "me": round(me, 2),
        "rrmse_vs_naive": round(rrmse, 4) if rrmse is not None else None
    }

# Test run for Potato at horizon 7
df = build_crop_feature_matrix("Potato", "Pune")
features = get_feature_columns()
target_col = "target_h7"
naive_col = "naive_h7"

valid_df = df.dropna(subset=features + [target_col, naive_col]).reset_index(drop=True)
split_date = valid_df['arrival_date'].max() - pd.DateOffset(months=12)

train_df = valid_df[valid_df['arrival_date'] < split_date]
test_df = valid_df[valid_df['arrival_date'] >= split_date]

print(f"Train samples: {len(train_df)} | Test samples: {len(test_df)}")

X_train, y_train = train_df[features], train_df[target_col]
X_test, y_test = test_df[features], test_df[target_col]
y_test_naive = test_df[naive_col]

# Naive
naive_metrics = compute_metrics(y_test, y_test_naive)
print("Naive Baseline:", naive_metrics)

# Random Forest
rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)
print("Random Forest:", compute_metrics(y_test, y_pred_rf, y_test_naive))

# XGBoost
xgb = XGBRegressor(n_estimators=120, max_depth=5, learning_rate=0.05, random_state=42, n_jobs=-1)
xgb.fit(X_train, y_train)
y_pred_xgb = xgb.predict(X_test)
print("XGBoost:", compute_metrics(y_test, y_pred_xgb, y_test_naive))

# LightGBM
lgb = LGBMRegressor(n_estimators=120, max_depth=5, learning_rate=0.05, random_state=42, n_jobs=-1, verbose=-1)
lgb.fit(X_train, y_train)
y_pred_lgb = lgb.predict(X_test)
print("LightGBM:", compute_metrics(y_test, y_pred_lgb, y_test_naive))
