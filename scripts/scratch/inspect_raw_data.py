import os
import pandas as pd
import glob

raw_files = {
    'potato': 'data/raw/Agri-Research Large Potato Dataset.csv',
    'tomato': 'data/raw/Agri-Research Large Tomato Dataset.csv',
    'onion': 'data/raw/Agri-Research Large Onion Dataset.csv'
}

for crop, path in raw_files.items():
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
    df = pd.read_csv(path)
    print(f"=== {crop.upper()} ===")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print("Sample rows:")
    print(df.head(3))
    print("\nMarkets summary:")
    print(df['Market'].value_counts().head(10) if 'Market' in df.columns else "No Market column")
    print("\nPrice stats (modal/modal_price):")
    modal_col = [c for c in df.columns if 'modal' in c.lower()]
    if modal_col:
        print(df[modal_col[0]].describe())
    print("\nDate sample:")
    date_col = [c for c in df.columns if 'date' in c.lower()]
    if date_col:
        print(df[date_col[0]].sample(5, random_state=42).tolist())
    print("-" * 50)
