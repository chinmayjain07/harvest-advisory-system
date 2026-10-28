import sqlite3
from database import get_connection

def seed_lookup_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. ICAR / DES Agricultural Economics Lookup Table
    economics_data = [
        (
            "Potato", 
            210.0,      # avg_yield_q_per_ha
            85000.0,    # cost_cultivation_per_ha (INR)
            1100.0,     # cost_production_per_q (INR)
            100,        # growing_period_days
            "Rabi / Autumn",
            "ICAR-CPRI / DES Maharashtra Agricultural Statistics"
        ),
        (
            "Tomato", 
            320.0,      # avg_yield_q_per_ha
            185000.0,   # cost_cultivation_per_ha (INR)
            750.0,      # cost_production_per_q (INR)
            110,        # growing_period_days
            "Kharif / Rabi",
            "ICAR-IIHR / State Horticulture Dept Maharashtra"
        ),
        (
            "Onion", 
            200.0,      # avg_yield_q_per_ha
            95000.0,    # cost_cultivation_per_ha (INR)
            700.0,      # cost_production_per_q (INR)
            120,        # growing_period_days
            "Late Kharif / Rabi",
            "ICAR-DOGR / DES Maharashtra Baseline Studies"
        )
    ]

    cursor.executemany("""
    INSERT OR REPLACE INTO crop_economics (
        commodity, avg_yield_q_per_ha, cost_cultivation_per_ha, 
        cost_production_per_q, growing_period_days, primary_season, source
    ) VALUES (?, ?, ?, ?, ?, ?, ?);
    """, economics_data)

    # 2. FAO EcoCrop Agro-Climatic Suitability Table
    suitability_data = [
        ("Potato", 7.0, 15.0, 22.0, 30.0, 450.0, 600.0, "Cool-season tuber crop; tuberization severely inhibited when night temps > 22C"),
        ("Tomato", 10.0, 20.0, 27.0, 35.0, 600.0, 800.0, "Warm-season fruit; poor fruit set at temperatures < 13C or > 35C; susceptible to heavy rain blights"),
        ("Onion", 9.0, 15.0, 28.0, 38.0, 350.0, 550.0, "Vegetative growth at 15-20C, bulbing accelerates at 22-30C; sensitive to waterlogging")
    ]

    cursor.executemany("""
    INSERT OR REPLACE INTO crop_suitability (
        commodity, temp_min_absolute, temp_min_optimal, temp_max_optimal,
        temp_max_absolute, rainfall_min_optimal, rainfall_max_optimal, description
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, suitability_data)

    # 3. Logistics and Mandi Fee Assumptions
    logistics_data = [
        ("Junnar", "Pune", 85.0, 2.5, 1.05, 5.0, 25.0),
        ("Junnar", "Junnar(Narayangaon)", 15.0, 3.0, 1.05, 5.0, 20.0),
        ("Khed", "Pune", 40.0, 2.5, 1.05, 5.0, 25.0),
        ("Khed", "Khed(Chakan)", 10.0, 3.5, 1.05, 5.0, 20.0),
        ("Pune", "Pune", 10.0, 3.5, 1.05, 5.0, 25.0),
        ("Manchar", "Pune", 65.0, 2.5, 1.05, 5.0, 25.0),
        ("Manchar", "Manchar", 8.0, 3.5, 1.05, 5.0, 20.0)
    ]

    cursor.executemany("""
    INSERT OR REPLACE INTO logistics_assumptions (
        from_location, to_mandi, distance_km, transport_rate_per_q_km,
        mandi_cess_percent, middleman_commission_percent, loading_unloading_per_q
    ) VALUES (?, ?, ?, ?, ?, ?, ?);
    """, logistics_data)

    conn.commit()
    conn.close()
    print("Crop economics, suitability, and logistics lookup tables seeded successfully into SQLite!")

if __name__ == "__main__":
    seed_lookup_tables()
