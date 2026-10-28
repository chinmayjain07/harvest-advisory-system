import pandas as pd

files = {
    'potato': 'data/raw/Agri-Research Large Potato Dataset.csv',
    'tomato': 'data/raw/Agri-Research Large Tomato Dataset.csv',
    'onion': 'data/raw/Agri-Research Large Onion Dataset.csv'
}

for crop, path in files.items():
    df = pd.read_csv(path)
    df['Clean_Date'] = pd.to_datetime(df['Arrival_Date'], dayfirst=True)
    df['Clean_Market'] = df['Market'].astype(str).str.replace(r'\s+APMC$', '', regex=True).str.strip()
    
    # Check duplicates on all original columns except index
    dups_all = df.duplicated(subset=['Clean_Date', 'Clean_Market', 'Commodity', 'Variety', 'Grade', 'Min_Price', 'Max_Price', 'Modal_Price'])
    print(f"=== {crop.upper()} ===")
    print(f"Duplicates with identical prices: {dups_all.sum()}")
    
    # Check duplicates on key (Date, Market, Variety)
    dups_key = df.duplicated(subset=['Clean_Date', 'Clean_Market', 'Variety'], keep=False)
    print(f"Rows sharing same (Date, Market, Variety): {dups_key.sum()}")
    if dups_key.sum() > 0:
        print("Sample collisions:")
        print(df[dups_key].sort_values(by=['Clean_Date', 'Clean_Market']).head(6)[['Clean_Date', 'Clean_Market', 'Variety', 'Min_Price', 'Max_Price', 'Modal_Price']])
