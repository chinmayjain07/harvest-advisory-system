import os
import requests
import datetime
import pandas as pd
from typing import Optional, List, Dict, Any
from database import get_connection

AGMARKNET_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
BASE_URL = f"https://api.data.gov.in/resource/{AGMARKNET_RESOURCE_ID}"

class AgmarknetClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DATA_GOV_IN_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def fetch_live_mandi_prices(self, commodity: Optional[str] = None, district: str = "Pune", state: str = "Maharashtra", limit: int = 100) -> List[Dict[str, Any]]:
        if not self.is_configured():
            print("Notice: DATA_GOV_IN_API_KEY is not configured. Falling back to simulated / replay feed.")
            return []

        params = {
            "api-key": self.api_key,
            "format": "json",
            "limit": limit,
            "filters[state]": state,
            "filters[district]": district
        }
        if commodity:
            params["filters[commodity]"] = commodity

        try:
            resp = requests.get(BASE_URL, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("records", [])
                return records
            else:
                print(f"data.gov.in API returned HTTP {resp.status_code}: {resp.text}")
                return []
        except Exception as e:
            print(f"Error querying data.gov.in API: {e}. Utilizing fallback mechanism.")
            return []

    def backfill_and_append(self, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0

        conn = get_connection()
        cursor = conn.cursor()
        inserted_count = 0

        for r in records:
            date_raw = r.get("arrival_date") or r.get("Arrival_Date")
            if not date_raw:
                continue

            try:
                date_iso = pd.to_datetime(date_raw, dayfirst=True).strftime('%Y-%m-%d')
            except Exception:
                continue

            market_clean = str(r.get("market", "")).replace(" APMC", "").strip()
            commodity = str(r.get("commodity", "")).strip().title()
            variety = str(r.get("variety", "Other")).strip()
            grade = str(r.get("grade", "FAQ")).strip()

            try:
                modal = float(r.get("modal_price", 0))
                min_p = float(r.get("min_price", modal))
                max_p = float(r.get("max_price", modal))
            except (ValueError, TypeError):
                continue

            if modal <= 0:
                continue

            # Check if record already exists
            cursor.execute("""
            SELECT id FROM prices 
            WHERE arrival_date = ? AND commodity = ? AND market = ? AND variety = ?;
            """, (date_iso, commodity, market_clean, variety))

            if cursor.fetchone() is None:
                cursor.execute("""
                INSERT INTO prices (
                    arrival_date, commodity, state, district, market,
                    variety, grade, min_price, max_price, modal_price,
                    is_interpolated, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'data_gov_in_feed');
                """, (
                    date_iso, commodity, r.get("state", "Maharashtra"),
                    r.get("district", "Pune"), market_clean, variety, grade,
                    min_p, max_p, modal
                ))
                inserted_count += 1

        conn.commit()
        conn.close()
        return inserted_count

class MandiReplaySimulator:
    """
    Simulation replay mode for demonstrations (per project plan Phase 4).
    Feeds held-out historical dates day-by-day to simulate daily update runs.
    """
    def __init__(self):
        pass

    def get_simulation_dates(self, num_days: int = 60) -> List[str]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT DISTINCT arrival_date FROM prices 
        ORDER BY arrival_date DESC LIMIT ?;
        """, (num_days,))
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        return sorted(dates)

    def fetch_replay_day(self, date_str: str) -> pd.DataFrame:
        conn = get_connection()
        df = pd.read_sql_query("""
        SELECT arrival_date, commodity, market, variety, min_price, max_price, modal_price 
        FROM prices 
        WHERE arrival_date = ?;
        """, conn, params=(date_str,))
        conn.close()
        return df

if __name__ == "__main__":
    client = AgmarknetClient()
    print("AgmarknetClient status:", "Configured with API Key" if client.is_configured() else "No API Key provided (Fallback Mode active)")
    simulator = MandiReplaySimulator()
    dates = simulator.get_simulation_dates(5)
    print(f"Sample simulation replay dates available: {dates}")
