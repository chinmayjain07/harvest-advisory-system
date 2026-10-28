import pandas as pd

files = {
    'potato': ('data/raw/Agri-Research Large Potato Dataset.csv', 100, 5000),
    'tomato': ('data/raw/Agri-Research Large Tomato Dataset.csv', 50, 8000),
    'onion': ('data/raw/Agri-Research Large Onion Dataset.csv', 50, 8000)
}

for crop, (path, low, high) in files.items():
    df = pd.read_csv(path)
    df['Clean_Date'] = pd.to_datetime(df['Arrival_Date'], dayfirst=True)
    df['Clean_Market'] = df['Market'].astype(str).str.replace(r'\s+APMC$', '', regex=True).str.strip()
    
    print(f"=== {crop.upper()} Low (< {low}) ===")
    lows = df[df['Modal_Price'] < low]
    print(f"Count: {len(lows)}")
    print(lows[['Clean_Date', 'Clean_Market', 'Variety', 'Min_Price', 'Max_Price', 'Modal_Price']])
    
    print(f"\n=== {crop.upper()} High (> {high}) ===")
    highs = df[df['Modal_Price'] > high]
    print(f"Count: {len(highs)}")
    print(highs[['Clean_Date', 'Clean_Market', 'Variety', 'Min_Price', 'Max_Price', 'Modal_Price']])
    print("=" * 60)
