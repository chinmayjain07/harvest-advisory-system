import pandas as pd
import numpy as np

files = {
    'potato': 'data/raw/Agri-Research Large Potato Dataset.csv',
    'tomato': 'data/raw/Agri-Research Large Tomato Dataset.csv',
    'onion': 'data/raw/Agri-Research Large Onion Dataset.csv'
}

for crop, path in files.items():
    df = pd.read_csv(path)
    print(f"==================== {crop.upper()} ====================")
    # Check duplicates
    dups = df.duplicated().sum()
    print(f"Total rows: {len(df)}, Exact duplicate rows: {dups}")
    
    # Check markets with APMC
    markets = sorted(df['Market'].dropna().unique())
    apmc_markets = [m for m in markets if 'apmc' in m.lower()]
    print(f"Markets containing 'APMC': {apmc_markets}")
    print(f"All markets ({len(markets)}): {markets}")
    
    # Date parsing test
    try:
        parsed_dates = pd.to_datetime(df['Arrival_Date'], dayfirst=True)
        print(f"Date range: {parsed_dates.min()} to {parsed_dates.max()}")
        print(f"Null dates after parse: {parsed_dates.isna().sum()}")
    except Exception as e:
        print(f"Date parse error: {e}")
        
    # Check extreme prices
    print("\nModal_Price > 10,000:")
    print(df[df['Modal_Price'] > 10000][['Arrival_Date', 'Market', 'Variety', 'Min_Price', 'Max_Price', 'Modal_Price']])
    
    print("\nModal_Price < 50:")
    print(df[df['Modal_Price'] < 50][['Arrival_Date', 'Market', 'Variety', 'Min_Price', 'Max_Price', 'Modal_Price']])
