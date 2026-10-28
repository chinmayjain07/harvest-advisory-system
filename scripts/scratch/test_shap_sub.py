import sys
print("Testing individual shap submodules...")
try:
    import slicer
    print("slicer ok")
    import shap.explainers
    print("shap.explainers ok")
except Exception as e:
    print("Error:", e)
