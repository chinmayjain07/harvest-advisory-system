import sys

packages = [
    'pandas', 'numpy', 'requests', 'sqlite3', 'scipy', 
    'sklearn', 'xgboost', 'lightgbm', 'shap', 'openmeteo_requests'
]

print(f"Python version: {sys.version}")
for pkg in packages:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, '__version__', 'unknown')
        print(f"  {pkg}: OK (version {ver})")
    except ImportError as e:
        print(f"  {pkg}: MISSING ({e})")
