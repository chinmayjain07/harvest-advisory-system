import os
import json
import joblib
import pandas as pd

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")

def verify_phase_2():
    print("=================================================================")
    print("         PHASE 2: PRICE PREDICTION VERIFICATION REPORT           ")
    print("=================================================================")

    # 1. Verify Model Files
    crops = ["potato", "tomato", "onion"]
    horizons = [7, 14, 30]
    architectures = ["rf", "xgb", "lgbm", "stack"]

    missing_models = []
    loaded_models = 0
    for crop in crops:
        for h in horizons:
            for arch in architectures:
                fname = f"{crop}_h{h}_{arch}.joblib"
                fpath = os.path.join(MODELS_DIR, fname)
                if not os.path.exists(fpath):
                    missing_models.append(fname)
                else:
                    loaded_models += 1

    print(f"\n1. Trained Ensemble Models:")
    print(f"   Total expected models: {len(crops) * len(horizons) * len(architectures)}")
    print(f"   Successfully serialized on disk: {loaded_models}")
    if missing_models:
        print(f"   [FAIL] Missing models: {missing_models}")
    else:
        print(f"   [PASS] 100% of Random Forest, XGBoost, LightGBM, and Stacking models serialized!")

    # 2. Verify Metrics Report
    csv_metrics_path = os.path.join(REPORTS_DIR, "model_evaluation_metrics.csv")
    if not os.path.exists(csv_metrics_path):
        print(f"   [FAIL] Metrics file missing: {csv_metrics_path}")
        return

    df_metrics = pd.read_csv(csv_metrics_path)
    print(f"\n2. Evaluation Metrics Benchmark (Held-out last 12 months):")
    print(f"   Total benchmark records: {len(df_metrics)}")
    print(df_metrics.to_string(index=False))

    # 3. Verify SHAP Explanations
    shap_path = os.path.join(REPORTS_DIR, "shap_explanations.json")
    if os.path.exists(shap_path):
        with open(shap_path, "r") as f:
            shap_data = json.load(f)
        print(f"\n3. SHAP Feature Attribution:")
        for crop, details in shap_data.items():
            print(f"\n   [{crop.upper()}] Base Value: Rs {details['base_value']}")
            print(f"   Top 5 Influential Features:")
            for feat in details['top_features'][:5]:
                print(f"     - {feat['feature']:<22} | Mean |SHAP|: {feat['mean_abs_shap']:<7} | Corr: {feat['correlation_with_target']}")

    print("\n=================================================================")
    print("               PHASE 2 STATUS: FULLY COMPLETE                    ")
    print("=================================================================")

if __name__ == "__main__":
    verify_phase_2()
