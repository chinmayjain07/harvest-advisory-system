import sys
print("Testing xgboost...")
import xgboost as xgb
print("XGBoost version:", xgb.__version__)

print("Testing lightgbm...")
import lightgbm as lgb
print("LightGBM version:", lgb.__version__)

print("Testing sklearn RandomForest...")
from sklearn.ensemble import RandomForestRegressor
print("RandomForest ready!")
