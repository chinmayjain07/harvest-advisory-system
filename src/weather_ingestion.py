import os
import time
import requests
import pandas as pd
from database import get_connection, init_db

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
WEATHER_DIR = os.path.join(DATA_DIR, "weather")

LOCATIONS = {
    "Pune": {"latitude": 18.5204, "longitude": 73.8567},
    "Junnar": {"latitude": 19.2064, "longitude": 73.8765}
}

ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"

DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "relative_humidity_2m_mean",
    "wind_speed_10m_max"
]

def fetch_weather_archive(location_name: str, lat: float, lon: float, start_date: str = "2001-01-01", end_date: str = "2026-10-20") -> pd.DataFrame:
    print(f"Fetching historical weather archive for {location_name} ({start_date} to {end_date})...")
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": DAILY_VARS,
        "timezone": "Asia/Kolkata"
    }

    resp = requests.get(ARCHIVE_API_URL, params=params, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Open-Meteo Archive API failed ({resp.status_code}): {resp.text}")

    data = resp.json().get("daily", {})
    df = pd.DataFrame(data)
    df["location"] = location_name
    df["latitude"] = lat
    df["longitude"] = lon
    return df

def fetch_weather_recent_and_forecast(location_name: str, lat: float, lon: float, past_days: int = 14, forecast_days: int = 14) -> pd.DataFrame:
    print(f"Fetching recent & 14-day forecast weather for {location_name}...")
    params = {
        "latitude": lat,
        "longitude": lon,
        "past_days": past_days,
        "forecast_days": forecast_days,
        "daily": DAILY_VARS,
        "timezone": "Asia/Kolkata"
    }

    resp = requests.get(FORECAST_API_URL, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"Warning: Open-Meteo Forecast API returned {resp.status_code}. Using archive only.")
        return pd.DataFrame()

    data = resp.json().get("daily", {})
    df = pd.DataFrame(data)
    df["location"] = location_name
    df["latitude"] = lat
    df["longitude"] = lon
    return df

def pull_and_store_weather():
    os.makedirs(WEATHER_DIR, exist_ok=True)
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear previous weather
    cursor.execute("DELETE FROM weather;")
    conn.commit()

    all_weather_dfs = []

    for loc, coords in LOCATIONS.items():
        # 1. Fetch archive
        df_archive = fetch_weather_archive(loc, coords["latitude"], coords["longitude"])
        print(f"  Received {len(df_archive)} archive records for {loc}")

        # Rate limit courtesy
        time.sleep(1)

        # 2. Fetch recent + forecast
        try:
            df_forecast = fetch_weather_recent_and_forecast(loc, coords["latitude"], coords["longitude"])
            print(f"  Received {len(df_forecast)} recent/forecast records for {loc}")
        except Exception as e:
            print(f"  Notice: Forecast fetch skipped: {e}")
            df_forecast = pd.DataFrame()

        # Combine & deduplicate by date
        combined = pd.concat([df_archive, df_forecast], ignore_index=True)
        combined = combined.drop_duplicates(subset=["time", "location"], keep="last")
        combined = combined.sort_values("time").reset_index(drop=True)

        # Save local CSV backup
        csv_path = os.path.join(WEATHER_DIR, f"{loc.lower()}_daily_weather.csv")
        combined.to_csv(csv_path, index=False)
        print(f"  Saved {len(combined)} daily weather records to {csv_path}")

        all_weather_dfs.append(combined)

    master_weather = pd.concat(all_weather_dfs, ignore_index=True)

    # Insert into SQLite
    records_to_insert = []
    for _, row in master_weather.iterrows():
        records_to_insert.append((
            row["time"],
            row["location"],
            float(row["latitude"]),
            float(row["longitude"]),
            float(row["temperature_2m_max"]) if pd.notna(row["temperature_2m_max"]) else None,
            float(row["temperature_2m_min"]) if pd.notna(row["temperature_2m_min"]) else None,
            float(row["temperature_2m_mean"]) if pd.notna(row["temperature_2m_mean"]) else None,
            float(row["precipitation_sum"]) if pd.notna(row["precipitation_sum"]) else 0.0,
            float(row["relative_humidity_2m_mean"]) if pd.notna(row["relative_humidity_2m_mean"]) else None,
            float(row["wind_speed_10m_max"]) if pd.notna(row["wind_speed_10m_max"]) else None
        ))

    cursor.executemany("""
    INSERT OR REPLACE INTO weather (
        date, location, latitude, longitude,
        temp_max, temp_min, temp_mean,
        precipitation, relative_humidity, wind_speed_max
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, records_to_insert)

    conn.commit()

    cursor.execute("""
    SELECT location, COUNT(*), MIN(date), MAX(date), 
           ROUND(AVG(temp_mean), 1), ROUND(MAX(temp_max), 1), ROUND(SUM(precipitation), 1)
    FROM weather
    GROUP BY location;
    """)
    summary = cursor.fetchall()
    print("\nWeather Table Summary in SQLite:")
    print(f"{'Location':<10} {'Records':<9} {'Min Date':<12} {'Max Date':<12} {'Avg Temp':<10} {'Max Temp':<10} {'Total Rain (mm)':<15}")
    print("-" * 85)
    for row in summary:
        print(f"{row[0]:<10} {row[1]:<9} {row[2]:<12} {row[3]:<12} {row[4]:<10} {row[5]:<10} {row[6]:<15}")

    conn.close()
    print("\nPhase 1 Data Foundation: Weather successfully pulled and loaded into SQLite!")

if __name__ == "__main__":
    pull_and_store_weather()
