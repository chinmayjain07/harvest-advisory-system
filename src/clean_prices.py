import os
import sqlite3
import pandas as pd
import numpy as np
from database import get_connection, init_db

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")

DATASET_FILES = {
    "Potato": os.path.join(RAW_DIR, "Agri-Research Large Potato Dataset.csv"),
    "Tomato": os.path.join(RAW_DIR, "Agri-Research Large Tomato Dataset.csv"),
    "Onion": os.path.join(RAW_DIR, "Agri-Research Large Onion Dataset.csv"),
}

def clean_and_normalize_commodity_data(commodity_name: str, file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Source file not found: {file_path}")

    print(f"\nProcessing {commodity_name} from: {os.path.basename(file_path)}")
    df = pd.read_csv(file_path)
    initial_count = len(df)
    print(f"  Raw row count: {initial_count:,}")

    # Standardize column names
    col_mapping = {c: c.strip().lower() for c in df.columns}
    df = df.rename(columns=col_mapping)

    # 1. Parse Dates
    # Format is mixed (DD/MM/YYYY and DD-MM-YYYY)
    df['arrival_date'] = pd.to_datetime(df['arrival_date'], dayfirst=True, errors='coerce')
    null_dates = df['arrival_date'].isna().sum()
    if null_dates > 0:
        print(f"  Dropping {null_dates} rows with unparseable dates")
        df = df.dropna(subset=['arrival_date'])
    df['arrival_date_str'] = df['arrival_date'].dt.strftime('%Y-%m-%d')

    # 2. Merge APMC market names
    # e.g., 'Pune APMC' -> 'Pune', 'Pune(Khadiki) APMC' -> 'Pune(Khadiki)'
    raw_market_count = df['market'].nunique()
    df['market'] = df['market'].astype(str).str.replace(r'\s+APMC$', '', regex=True).str.strip()
    clean_market_count = df['market'].nunique()
    print(f"  Markets consolidated from {raw_market_count} to {clean_market_count} distinct markets (APMC suffixes merged)")

    # 3. Standardize text fields
    df['commodity'] = commodity_name
    df['variety'] = df['variety'].astype(str).str.strip() if 'variety' in df.columns else 'Other'
    df['grade'] = df['grade'].astype(str).str.strip() if 'grade' in df.columns else 'FAQ'
    df['district'] = df['district'].astype(str).str.strip() if 'district' in df.columns else 'Pune'
    df['state'] = df['state'].astype(str).str.strip() if 'state' in df.columns else 'Maharashtra'

    # Numeric fields
    for col in ['min_price', 'max_price', 'modal_price']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows where modal_price is missing or zero
    df = df.dropna(subset=['modal_price'])
    df = df[df['modal_price'] > 0]

    # Ensure min <= modal <= max consistency where both exist
    invalid_bounds = (df['min_price'] > df['max_price'])
    if invalid_bounds.sum() > 0:
        # Swap where min > max
        df.loc[invalid_bounds, ['min_price', 'max_price']] = df.loc[invalid_bounds, ['max_price', 'min_price']].values

    # If min_price is missing or > modal_price, adjust to modal_price
    df['min_price'] = df['min_price'].fillna(df['modal_price'])
    df.loc[df['min_price'] > df['modal_price'], 'min_price'] = df['modal_price']
    df['max_price'] = df['max_price'].fillna(df['modal_price'])
    df.loc[df['max_price'] < df['modal_price'], 'max_price'] = df['modal_price']

    # 4. Outlier Handling
    # Low outliers (< 50 Rs/quintal): Values like Rs 6, 10, 13, 14, 15, 20 are obvious per-kg typos
    low_outliers = (df['modal_price'] < 50)
    low_count = low_outliers.sum()
    if low_count > 0:
        print(f"  Identified {low_count} low price anomalies (< Rs 50/quintal). Correcting (100x kg-to-quintal factor) or filtering:")
        # Check if multiplying by 100 puts them into realistic mandi price range (500 - 3000)
        df.loc[low_outliers & (df['modal_price'] * 100 >= 500) & (df['modal_price'] * 100 <= 4000), 'min_price'] *= 100
        df.loc[low_outliers & (df['modal_price'] * 100 >= 500) & (df['modal_price'] * 100 <= 4000), 'max_price'] *= 100
        df.loc[low_outliers & (df['modal_price'] * 100 >= 500) & (df['modal_price'] * 100 <= 4000), 'modal_price'] *= 100
        # If any remain below 50, drop them
        remaining_low = (df['modal_price'] < 50)
        if remaining_low.sum() > 0:
            df = df[~remaining_low]

    # High outliers
    if commodity_name == "Onion":
        # Erroneous records: Rs 75,000, 40,000, 25,000 in Junnar(Alephata)
        # Legitimate historic peak during Nov-Dec 2019 onion shortage was ~Rs 12,000/quintal
        onion_err = (df['modal_price'] > 20000)
        print(f"  Removing {onion_err.sum()} extreme Onion data entry typos (> Rs 20,000/quintal, e.g. Rs 75,000 typo)")
        df = df[~onion_err]

    elif commodity_name == "Potato":
        # Two isolated entries of Rs 16,000 in Pune where surrounding days were Rs 1,600
        potato_10x_typos = (df['modal_price'] >= 14000)
        if potato_10x_typos.sum() > 0:
            print(f"  Fixing {potato_10x_typos.sum()} Potato 10x typos (> Rs 14,000 scaled down to Rs 1,400-1,600 range)")
            df.loc[potato_10x_typos, 'min_price'] /= 10
            df.loc[potato_10x_typos, 'max_price'] /= 10
            df.loc[potato_10x_typos, 'modal_price'] /= 10

    elif commodity_name == "Tomato":
        # Preserve July-August 2023 authentic crisis spike (up to Rs 15,000 - 19,000)
        # Verify no impossible spike > Rs 25,000 exists
        tomato_err = (df['modal_price'] > 25000)
        if tomato_err.sum() > 0:
            print(f"  Removing {tomato_err.sum()} Tomato anomalies > Rs 25,000")
            df = df[~tomato_err]
        spike_2023 = df[(df['arrival_date_str'] >= '2023-07-01') & (df['arrival_date_str'] <= '2023-08-31') & (df['modal_price'] >= 8000)]
        print(f"  Verified authentic 2023 Tomato price surge preserved: {len(spike_2023)} records with modal price >= Rs 8,000")

    # 5. Drop Duplicates
    # First drop exact duplicate rows
    exact_dups = df.duplicated(subset=['arrival_date_str', 'market', 'commodity', 'variety', 'grade', 'modal_price']).sum()
    df = df.drop_duplicates(subset=['arrival_date_str', 'market', 'commodity', 'variety', 'grade', 'modal_price'])
    print(f"  Dropped {exact_dups} duplicate price records")

    # If there are duplicate daily quotes for same market & variety with slightly different prices, aggregate to daily mean modal price
    collision_mask = df.duplicated(subset=['arrival_date_str', 'market', 'commodity', 'variety'], keep=False)
    collision_count = collision_mask.sum()
    if collision_count > 0:
        print(f"  Deduplicating {collision_count} records sharing identical (date, market, variety) by taking average modal price")
        df = df.groupby(['arrival_date_str', 'market', 'commodity', 'variety'], as_index=False).agg({
            'arrival_date': 'first',
            'commodity_code': 'first',
            'state': 'first',
            'district': 'first',
            'grade': 'first',
            'min_price': 'min',
            'max_price': 'max',
            'modal_price': 'mean'
        })

    final_count = len(df)
    print(f"  Clean row count: {final_count:,} (Date span: {df['arrival_date_str'].min()} to {df['arrival_date_str'].max()})")
    return df

def clean_and_load_all():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing prices table
    cursor.execute("DELETE FROM prices;")
    conn.commit()

    all_dfs = []
    for crop, path in DATASET_FILES.items():
        clean_df = clean_and_normalize_commodity_data(crop, path)
        all_dfs.append(clean_df)

    combined_df = pd.concat(all_dfs, ignore_index=True)
    print(f"\n==================================================")
    print(f"Total Unified Clean Records across 3 Crops: {len(combined_df):,}")

    # Prepare for insert
    records_to_insert = []
    for _, row in combined_df.iterrows():
        records_to_insert.append((
            row['arrival_date_str'],
            row['commodity'],
            int(row['commodity_code']) if pd.notna(row.get('commodity_code')) else None,
            row['state'],
            row['district'],
            row['market'],
            row['variety'],
            row['grade'],
            float(row['min_price']),
            float(row['max_price']),
            round(float(row['modal_price']), 2),
            0,
            'historical_archive'
        ))

    cursor.executemany("""
    INSERT INTO prices (
        arrival_date, commodity, commodity_code, state, district,
        market, variety, grade, min_price, max_price, modal_price,
        is_interpolated, source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, records_to_insert)

    conn.commit()

    # Summary query
    cursor.execute("""
    SELECT commodity, COUNT(*), MIN(arrival_date), MAX(arrival_date), 
           ROUND(MIN(modal_price), 2), ROUND(AVG(modal_price), 2), ROUND(MAX(modal_price), 2)
    FROM prices
    GROUP BY commodity;
    """)
    summary = cursor.fetchall()
    print("\nPrices Table Summary in SQLite:")
    print(f"{'Crop':<10} {'Rows':<8} {'Min Date':<12} {'Max Date':<12} {'Min (Rs)':<10} {'Avg (Rs)':<10} {'Max (Rs)':<10}")
    print("-" * 75)
    for row in summary:
        print(f"{row[0]:<10} {row[1]:<8} {row[2]:<12} {row[3]:<12} {row[4]:<10} {row[5]:<10} {row[6]:<10}")

    conn.close()
    print("\nPhase 1 Data Foundation: Prices cleaned and loaded into SQLite successfully!")

if __name__ == "__main__":
    clean_and_load_all()
