import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed", "harvest_advisory.db")

def get_connection(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=DB_PATH):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Mandi Prices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        arrival_date TEXT NOT NULL,
        commodity TEXT NOT NULL,
        commodity_code INTEGER,
        state TEXT NOT NULL,
        district TEXT NOT NULL,
        market TEXT NOT NULL,
        variety TEXT,
        grade TEXT,
        min_price REAL,
        max_price REAL,
        modal_price REAL NOT NULL,
        is_interpolated INTEGER DEFAULT 0,
        source TEXT DEFAULT 'historical_archive'
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_crop_market_date ON prices(commodity, market, arrival_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(arrival_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_market ON prices(market);")

    # 2. Historical & Forecast Weather Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        location TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        temp_max REAL,
        temp_min REAL,
        temp_mean REAL,
        precipitation REAL,
        relative_humidity REAL,
        wind_speed_max REAL,
        UNIQUE(date, location)
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_weather_loc_date ON weather(location, date);")

    # 3. ICAR / DES Agricultural Economics Lookup Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crop_economics (
        commodity TEXT PRIMARY KEY,
        avg_yield_q_per_ha REAL NOT NULL,
        cost_cultivation_per_ha REAL NOT NULL,
        cost_production_per_q REAL NOT NULL,
        growing_period_days INTEGER NOT NULL,
        primary_season TEXT NOT NULL,
        source TEXT NOT NULL
    );
    """)

    # 4. FAO EcoCrop Agro-Climatic Suitability Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crop_suitability (
        commodity TEXT PRIMARY KEY,
        temp_min_absolute REAL NOT NULL,
        temp_min_optimal REAL NOT NULL,
        temp_max_optimal REAL NOT NULL,
        temp_max_absolute REAL NOT NULL,
        rainfall_min_optimal REAL NOT NULL,
        rainfall_max_optimal REAL NOT NULL,
        description TEXT
    );
    """)

    # 5. Logistics, Mandi Cess and Inter-market Distances
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logistics_assumptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_location TEXT NOT NULL,
        to_mandi TEXT NOT NULL,
        distance_km REAL NOT NULL,
        transport_rate_per_q_km REAL NOT NULL,
        mandi_cess_percent REAL NOT NULL,
        middleman_commission_percent REAL NOT NULL,
        loading_unloading_per_q REAL NOT NULL,
        UNIQUE(from_location, to_mandi)
    );
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized successfully at {db_path}")

if __name__ == "__main__":
    init_db()
