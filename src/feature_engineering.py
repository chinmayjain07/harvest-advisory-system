import os
import sqlite3
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List
from database import get_connection

def build_crop_feature_matrix(
    commodity: str, 
    market: str = "Pune", 
    weather_loc: str = "Pune"
) -> pd.DataFrame:
    """
    Constructs a complete daily multivariate feature matrix combining
    mandi price history, multi-order lags, rolling statistical windows,
    Fourier/cyclical seasonality, and meteorological indicators.
    """
    conn = get_connection()
    
    # 1. Fetch Price Series
    query = """
    SELECT arrival_date, modal_price, min_price, max_price
    FROM prices
    WHERE commodity = ? AND market = ?
    ORDER BY arrival_date ASC;
    """
    df_prices = pd.read_sql_query(query, conn, params=(commodity, market))
    if df_prices.empty:
        conn.close()
        raise ValueError(f"No price data found for {commodity} in market {market}")

    df_prices['arrival_date'] = pd.to_datetime(df_prices['arrival_date'])
    # Aggregate any duplicates by taking mean
    df_prices = df_prices.groupby('arrival_date', as_index=False).agg({
        'modal_price': 'mean',
        'min_price': 'min',
        'max_price': 'max'
    })

    # Create continuous daily index
    min_date = df_prices['arrival_date'].min()
    max_date = df_prices['arrival_date'].max()
    full_date_idx = pd.date_range(start=min_date, end=max_date, freq='D')
    
    df_continuous = pd.DataFrame({'arrival_date': full_date_idx})
    df_continuous = df_continuous.merge(df_prices, on='arrival_date', how='left')
    
    # Forward-fill prices for Sundays and holidays (mandis closed)
    df_continuous['is_market_closed'] = df_continuous['modal_price'].isna().astype(int)
    df_continuous['modal_price'] = df_continuous['modal_price'].ffill().bfill()
    df_continuous['min_price'] = df_continuous['min_price'].ffill().bfill()
    df_continuous['max_price'] = df_continuous['max_price'].ffill().bfill()

    # 2. Fetch Weather Series
    weather_query = """
    SELECT date, temp_max, temp_min, temp_mean, precipitation, relative_humidity, wind_speed_max
    FROM weather
    WHERE location = ?
    ORDER BY date ASC;
    """
    df_weather = pd.read_sql_query(weather_query, conn, params=(weather_loc,))
    conn.close()

    df_weather['date'] = pd.to_datetime(df_weather['date'])
    df_continuous = df_continuous.merge(df_weather, left_on='arrival_date', right_on='date', how='left')
    df_continuous = df_continuous.drop(columns=['date'])

    # Fill any missing weather values with ffill/bfill
    weather_cols = ['temp_max', 'temp_min', 'temp_mean', 'precipitation', 'relative_humidity', 'wind_speed_max']
    for wc in weather_cols:
        if wc in df_continuous.columns:
            df_continuous[wc] = df_continuous[wc].ffill().bfill()

    # 3. Construct Price Lags
    for lag in [1, 2, 3, 7, 14, 21, 30]:
        df_continuous[f'price_lag_{lag}'] = df_continuous['modal_price'].shift(lag)

    # 4. Construct Rolling Window Features
    for window in [7, 14, 30]:
        df_continuous[f'price_roll_mean_{window}'] = df_continuous['modal_price'].shift(1).rolling(window).mean()
        df_continuous[f'price_roll_std_{window}'] = df_continuous['modal_price'].shift(1).rolling(window).std()
        df_continuous[f'price_roll_min_{window}'] = df_continuous['modal_price'].shift(1).rolling(window).min()
        df_continuous[f'price_roll_max_{window}'] = df_continuous['modal_price'].shift(1).rolling(window).max()

    # Price momentum
    df_continuous['price_pct_change_7'] = (df_continuous['modal_price'].shift(1) - df_continuous['modal_price'].shift(8)) / (df_continuous['modal_price'].shift(8) + 1e-6)
    df_continuous['price_pct_change_14'] = (df_continuous['modal_price'].shift(1) - df_continuous['modal_price'].shift(15)) / (df_continuous['modal_price'].shift(15) + 1e-6)

    # 5. Calendar & Seasonality
    dt = df_continuous['arrival_date'].dt
    df_continuous['month'] = dt.month
    df_continuous['day_of_week'] = dt.dayofweek
    df_continuous['day_of_year'] = dt.dayofyear
    
    # Cyclical sin/cos encoding
    df_continuous['sin_month'] = np.sin(2 * np.pi * df_continuous['month'] / 12.0)
    df_continuous['cos_month'] = np.cos(2 * np.pi * df_continuous['month'] / 12.0)
    df_continuous['sin_day'] = np.sin(2 * np.pi * df_continuous['day_of_year'] / 365.25)
    df_continuous['cos_day'] = np.cos(2 * np.pi * df_continuous['day_of_year'] / 365.25)

    # Agro-climatic seasons in Maharashtra
    # Monsoon: June (6) to Sept (9)
    df_continuous['is_monsoon'] = df_continuous['month'].isin([6, 7, 8, 9]).astype(int)
    # Winter/Rabi: Oct (10) to Feb (2)
    df_continuous['is_winter'] = df_continuous['month'].isin([10, 11, 12, 1, 2]).astype(int)
    # Summer: March (3) to May (5)
    df_continuous['is_summer'] = df_continuous['month'].isin([3, 4, 5]).astype(int)

    # 6. Meteorological Features & Rolling Weather
    df_continuous['temp_diurnal_range'] = df_continuous['temp_max'] - df_continuous['temp_min']
    df_continuous['rain_7d_sum'] = df_continuous['precipitation'].rolling(7).sum()
    df_continuous['rain_14d_sum'] = df_continuous['precipitation'].rolling(14).sum()
    df_continuous['rain_30d_sum'] = df_continuous['precipitation'].rolling(30).sum()
    df_continuous['temp_7d_mean'] = df_continuous['temp_mean'].rolling(7).mean()
    df_continuous['humidity_7d_mean'] = df_continuous['relative_humidity'].rolling(7).mean()

    # Extreme weather stress indicators
    df_continuous['extreme_heat_day'] = (df_continuous['temp_max'] >= 38.0).astype(int)
    df_continuous['heavy_rain_day'] = (df_continuous['precipitation'] >= 30.0).astype(int)
    df_continuous['heat_days_last_14d'] = df_continuous['extreme_heat_day'].rolling(14).sum()
    df_continuous['heavy_rain_days_last_14d'] = df_continuous['heavy_rain_day'].rolling(14).sum()

    # 7. Multi-Horizon Forecast Targets
    # h=7 days ahead, h=14 days ahead, h=30 days ahead
    df_continuous['target_h7'] = df_continuous['modal_price'].shift(-7)
    df_continuous['target_h14'] = df_continuous['modal_price'].shift(-14)
    df_continuous['target_h30'] = df_continuous['modal_price'].shift(-30)

    # Naive Baselines (t-h / current price)
    df_continuous['naive_h7'] = df_continuous['modal_price']
    df_continuous['naive_h14'] = df_continuous['modal_price']
    df_continuous['naive_h30'] = df_continuous['modal_price']

    # Crop and market identifiers
    df_continuous['commodity'] = commodity
    df_continuous['market'] = market

    return df_continuous

def get_feature_columns() -> List[str]:
    """Returns the standardized list of predictor feature names."""
    return [
        'price_lag_1', 'price_lag_2', 'price_lag_3', 'price_lag_7', 'price_lag_14', 'price_lag_21', 'price_lag_30',
        'price_roll_mean_7', 'price_roll_std_7', 'price_roll_min_7', 'price_roll_max_7',
        'price_roll_mean_14', 'price_roll_std_14', 'price_roll_min_14', 'price_roll_max_14',
        'price_roll_mean_30', 'price_roll_std_30', 'price_roll_min_30', 'price_roll_max_30',
        'price_pct_change_7', 'price_pct_change_14',
        'month', 'day_of_week', 'day_of_year',
        'sin_month', 'cos_month', 'sin_day', 'cos_day',
        'is_monsoon', 'is_winter', 'is_summer',
        'temp_max', 'temp_min', 'temp_mean', 'temp_diurnal_range',
        'precipitation', 'relative_humidity', 'wind_speed_max',
        'rain_7d_sum', 'rain_14d_sum', 'rain_30d_sum',
        'temp_7d_mean', 'humidity_7d_mean',
        'extreme_heat_day', 'heavy_rain_day',
        'heat_days_last_14d', 'heavy_rain_days_last_14d'
    ]

if __name__ == "__main__":
    for c in ["Potato", "Tomato", "Onion"]:
        df_feat = build_crop_feature_matrix(c, "Pune")
        print(f"{c} Feature Matrix: {df_feat.shape}, Date Range: {df_feat['arrival_date'].min().date()} to {df_feat['arrival_date'].max().date()}")
        print(f"Features: {len(get_feature_columns())} input variables")
