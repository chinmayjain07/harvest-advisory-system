import xgboost as xgb
import numpy as np

# Create tiny dummy data
X = np.random.randn(50, 5)
y = X[:, 0] * 2 + X[:, 1] * -1.5 + np.random.randn(50) * 0.1

reg = xgb.XGBRegressor(n_estimators=10, max_depth=3)
reg.fit(X, y)

# Compute native TreeSHAP
dmatrix = xgb.DMatrix(X)
shap_values = reg.get_booster().predict(dmatrix, pred_contribs=True)

print("Native TreeSHAP shape:", shap_values.shape)
print("SHAP base value (bias):", shap_values[0, -1])
print("Sample feature contributions for row 0:", shap_values[0, :-1])
print("Sum + bias == Prediction:", np.isclose(shap_values[0].sum(), reg.predict(X[:1])[0]))
