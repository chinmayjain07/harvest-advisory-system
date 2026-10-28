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
    
    print(f"=== {crop.upper()} OUTLIERS ===")
    print("Top 10 highest modal prices:")
    print(df.nlargest(10, 'Modal_Price')[['Clean_Date', 'Clean_Market', 'Variety', 'Min_Price', 'Max_Price', 'Modal_Price']])
    print("\nBottom 10 lowest modal prices:")
    print(df.nsmallest(10, 'Modal_Price')[['Clean_Date', 'Clean_Market', 'Variety', 'Min_Price', 'Max_Price', 'Modal_Price']])
    print("-" * 60)
