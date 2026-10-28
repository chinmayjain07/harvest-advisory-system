import os
import sys
import json
import time
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple

from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.linear_model import RidgeCV
import xgboost as xgb
from lightgbm import LGBMRegressor

from feature_engineering import build_crop_feature_matrix, get_feature_columns

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")

def calculate_metrics(y_true: pd.Series, y_pred: np.ndarray, y_naive: pd.Series) -> Dict[str, float]:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    mape = float(mean_absolute_percentage_error(y_true, y_pred) * 100)
    me = float(np.mean(y_pred - y_true))
    
    rmse_naive = float(np.sqrt(mean_squared_error(y_true, y_naive)))
    rrmse = float(rmse / rmse_naive) if rmse_naive > 0 else 1.0
    
    return {
        "RMSE": round(rmse, 2),
        "MAE": round(mae, 2),
        "MAPE (%)": round(mape, 2),
        "ME": round(me, 2),
        "RRMSE (vs Naive)": round(rrmse, 4)
    }

def train_and_evaluate_all():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    crops = ["Potato", "Tomato", "Onion"]
    horizons = [7, 14, 30]
    all_results = []
    shap_summaries = {}

    print("===========================================================================")
    print("      PHASE 2: ENSEMBLE REGRESSION TRAINING & BENCHMARKING PIPELINE       ")
    print("===========================================================================")

    for crop in crops:
        print(f"\n>>>>>>>>>>>>>>> Processing Crop: {crop.upper()} <<<<<<<<<<<<<<<")
        df_full = build_crop_feature_matrix(crop, "Pune")
        features = get_feature_columns()

        for h in horizons:
            target_col = f"target_h{h}"
            naive_col = f"naive_h{h}"

            # Prepare dataset
            df_valid = df_full.dropna(subset=features + [target_col, naive_col]).reset_index(drop=True)
            
            # Split chronologically: last 12 months as the test set
            split_date = df_valid['arrival_date'].max() - pd.DateOffset(months=12)
            train_df = df_valid[df_valid['arrival_date'] < split_date].copy()
            test_df = df_valid[df_valid['arrival_date'] >= split_date].copy()

            X_train = train_df[features]
            y_train = train_df[target_col]
            X_test = test_df[features]
            y_test = test_df[target_col]
            y_test_naive = test_df[naive_col]

            print(f"\n--- Horizon h={h} days | Train: {len(train_df):,} rows (< {split_date.date()}) | Test: {len(test_df):,} rows (>= {split_date.date()}) ---")

            # 1. Naive Baseline ("Tomorrow = today")
            y_pred_naive = y_test_naive.values
            naive_metrics = calculate_metrics(y_test, y_pred_naive, y_test_naive)
            all_results.append({
                "Crop": crop,
                "Horizon": f"{h}d",
                "Model": "Naive Baseline",
                **naive_metrics
            })
            print(f"  [Naive Baseline]   MAPE: {naive_metrics['MAPE (%)']}% | RMSE: {naive_metrics['RMSE']} | RRMSE: 1.000")

            # 2. Random Forest Regressor
            rf = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_leaf=3,
                random_state=42,
                n_jobs=4
            )
            rf.fit(X_train, y_train)
            y_pred_rf = rf.predict(X_test)
            rf_metrics = calculate_metrics(y_test, y_pred_rf, y_test_naive)
            all_results.append({
                "Crop": crop,
                "Horizon": f"{h}d",
                "Model": "Random Forest",
                **rf_metrics
            })
            joblib.dump(rf, os.path.join(MODELS_DIR, f"{crop.lower()}_h{h}_rf.joblib"))
            print(f"  [Random Forest]    MAPE: {rf_metrics['MAPE (%)']}% | RMSE: {rf_metrics['RMSE']} | RRMSE: {rf_metrics['RRMSE (vs Naive)']}")

            # 3. XGBoost Regressor
            xgb_reg = xgb.XGBRegressor(
                n_estimators=120,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=4
            )
            xgb_reg.fit(X_train, y_train)
            y_pred_xgb = xgb_reg.predict(X_test)
            xgb_metrics = calculate_metrics(y_test, y_pred_xgb, y_test_naive)
            all_results.append({
                "Crop": crop,
                "Horizon": f"{h}d",
                "Model": "XGBoost",
                **xgb_metrics
            })
            joblib.dump(xgb_reg, os.path.join(MODELS_DIR, f"{crop.lower()}_h{h}_xgb.joblib"))
            print(f"  [XGBoost]          MAPE: {xgb_metrics['MAPE (%)']}% | RMSE: {xgb_metrics['RMSE']} | RRMSE: {xgb_metrics['RRMSE (vs Naive)']}")

            # 4. LightGBM Regressor
            lgb_reg = LGBMRegressor(
                n_estimators=120,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=4,
                verbose=-1
            )
            lgb_reg.fit(X_train, y_train)
            y_pred_lgb = lgb_reg.predict(X_test)
            lgb_metrics = calculate_metrics(y_test, y_pred_lgb, y_test_naive)
            all_results.append({
                "Crop": crop,
                "Horizon": f"{h}d",
                "Model": "LightGBM",
                **lgb_metrics
            })
            joblib.dump(lgb_reg, os.path.join(MODELS_DIR, f"{crop.lower()}_h{h}_lgbm.joblib"))
            print(f"  [LightGBM]         MAPE: {lgb_metrics['MAPE (%)']}% | RMSE: {lgb_metrics['RMSE']} | RRMSE: {lgb_metrics['RRMSE (vs Naive)']}")

            # 5. Stacking Ensemble Regressor
            # Combines RF, XGBoost, and LightGBM with RidgeCV meta-estimator
            estimators = [
                ('rf', RandomForestRegressor(n_estimators=60, max_depth=8, random_state=42, n_jobs=2)),
                ('xgb', xgb.XGBRegressor(n_estimators=80, max_depth=4, learning_rate=0.05, random_state=42, n_jobs=2)),
                ('lgb', LGBMRegressor(n_estimators=80, max_depth=4, learning_rate=0.05, random_state=42, n_jobs=2, verbose=-1))
            ]
            stack_reg = StackingRegressor(
                estimators=estimators,
                final_estimator=RidgeCV(),
                cv=3,
                n_jobs=2
            )
            stack_reg.fit(X_train, y_train)
            y_pred_stack = stack_reg.predict(X_test)
            stack_metrics = calculate_metrics(y_test, y_pred_stack, y_test_naive)
            all_results.append({
                "Crop": crop,
                "Horizon": f"{h}d",
                "Model": "Stacking Ensemble",
                **stack_metrics
            })
            joblib.dump(stack_reg, os.path.join(MODELS_DIR, f"{crop.lower()}_h{h}_stack.joblib"))
            print(f"  [Stacking Ensemble] MAPE: {stack_metrics['MAPE (%)']}% | RMSE: {stack_metrics['RMSE']} | RRMSE: {stack_metrics['RRMSE (vs Naive)']}")

            # Compute TreeSHAP explanations for primary horizon (h=7)
            if h == 7:
                print(f"  Computing TreeSHAP feature attribution for {crop}...")
                booster = xgb_reg.get_booster()
                dtest = xgb.DMatrix(X_test)
                # Native TreeSHAP via XGBoost C++ engine
                shap_contribs = booster.predict(dtest, pred_contribs=True)
                # Last column is expected value / bias
                shap_vals = shap_contribs[:, :-1]
                mean_abs_shap = np.mean(np.abs(shap_vals), axis=0)

                top_indices = np.argsort(mean_abs_shap)[::-1][:10]
                top_features = []
                for idx in top_indices:
                    top_features.append({
                        "feature": features[idx],
                        "mean_abs_shap": round(float(mean_abs_shap[idx]), 3),
                        "correlation_with_target": round(float(np.corrcoef(X_test[features[idx]], y_test)[0, 1]), 3)
                    })
                shap_summaries[crop] = {
                    "base_value": round(float(shap_contribs[0, -1]), 2),
                    "top_features": top_features
                }

    # Save Results
    results_df = pd.DataFrame(all_results)
    csv_report_path = os.path.join(REPORTS_DIR, "model_evaluation_metrics.csv")
    results_df.to_csv(csv_report_path, index=False)

    json_report_path = os.path.join(REPORTS_DIR, "model_evaluation_metrics.json")
    with open(json_report_path, "w") as f:
        json.dump(all_results, f, indent=2)

    shap_path = os.path.join(REPORTS_DIR, "shap_explanations.json")
    with open(shap_path, "w") as f:
        json.dump(shap_summaries, f, indent=2)

    print("\n===========================================================================")
    print("                    PHASE 2 MODEL BENCHMARK SUMMARY                        ")
    print("===========================================================================")
    print(results_df.to_string(index=False))
    print(f"\nAll models serialized to: {MODELS_DIR}")
    print(f"Evaluation report saved to: {csv_report_path}")
    print(f"SHAP explanation summary saved to: {shap_path}")

if __name__ == "__main__":
    train_and_evaluate_all()
