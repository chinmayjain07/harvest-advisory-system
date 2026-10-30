"""
Daily Mandi Price Fetcher & Ingestion Pipeline.
Pulls daily quotes from data.gov.in (Agmarknet Resource ID: 9ef84268-d588-465a-a308-a864a43d0070),
cleans and deduplicates records, and gracefully falls back to ReplayService if API is unavailable.
"""

import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import requests
import pandas as pd

try:
    from database import get_connection
except ImportError:
    from src.database import get_connection

try:
    from replay_service import ReplayService
except ImportError:
    from src.replay_service import ReplayService

try:
    from retrain_service import ForecastRefresher
except ImportError:
    from src.retrain_service import ForecastRefresher

logger = logging.getLogger(__name__)

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SYNC_STATUS_FILE = PROJECT_ROOT / "reports" / "sync_status.json"
AGMARKNET_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
BASE_API_URL = f"https://api.data.gov.in/resource/{AGMARKNET_RESOURCE_ID}"


def load_env_file(env_path: Path):
    """Load simple key=value pairs from .env if present."""
    if not env_path.exists():
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val
    except Exception as e:
        logger.warning(f"Error reading .env file: {e}")


# Load project .env
load_env_file(PROJECT_ROOT / ".env")


class DailyUpdater:
    def __init__(self, api_key: Optional[str] = None, sync_file: Optional[Path] = None):
        self.api_key = api_key or os.getenv("DATA_GOV_IN_API_KEY")
        self.sync_file = Path(sync_file) if sync_file else SYNC_STATUS_FILE
        self.sync_file.parent.mkdir(parents=True, exist_ok=True)

    def _record_sync_status(self, payload: Dict[str, Any]):
        """Persist sync status to reports/sync_status.json."""
        try:
            self.sync_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.sync_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write sync status: {e}")

    def clean_record(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Clean an incoming record:
        - Merge APMC suffix (e.g., Pune APMC -> Pune)
        - Standardize date to YYYY-MM-DD
        - Filter/scale per-kg typos (< 50 Rs/q)
        """
        try:
            date_raw = raw.get("arrival_date") or raw.get("Arrival_Date") or raw.get("Date")
            if not date_raw:
                return None
            parsed_date = pd.to_datetime(date_raw, dayfirst=True, errors='coerce')
            if pd.isna(parsed_date):
                return None
            arrival_date = parsed_date.strftime("%Y-%m-%d")

            market_raw = raw.get("market") or raw.get("Market") or ""
            market = re.sub(r'\s+APMC\b', '', str(market_raw), flags=re.IGNORECASE).strip().title()

            commodity_raw = raw.get("commodity") or raw.get("Commodity") or ""
            commodity = str(commodity_raw).strip().title()

            state = str(raw.get("state") or raw.get("State") or "Maharashtra").strip().title()
            district = str(raw.get("district") or raw.get("District") or "Pune").strip().title()
            variety = str(raw.get("variety") or raw.get("Variety") or "Other").strip().title()
            grade = str(raw.get("grade") or raw.get("Grade") or "FAQ").strip().upper()

            modal_raw = raw.get("modal_price") or raw.get("Modal_Price") or 0.0
            modal_price = float(modal_raw)
            min_price = float(raw.get("min_price") or raw.get("Min_Price") or modal_price * 0.95)
            max_price = float(raw.get("max_price") or raw.get("Max_Price") or modal_price * 1.05)

            # Filter/scale per-kg typos (< 50 Rs/q)
            if 0 < modal_price < 50:
                modal_price *= 100
                min_price *= 100
                max_price *= 100

            if modal_price < 50:
                return None

            return {
                "arrival_date": arrival_date,
                "commodity": commodity,
                "state": state,
                "district": district,
                "market": market,
                "variety": variety,
                "grade": grade,
                "min_price": min_price,
                "max_price": max_price,
                "modal_price": modal_price,
                "is_interpolated": 0,
                "source": "data_gov_in_api"
            }
        except Exception:
            return None

    def _fetch_from_api(self, date_override: Optional[str] = None) -> Optional[list]:
        """Fetch records from data.gov.in Agmarknet API."""
        if not self.api_key:
            logger.info("DATA_GOV_IN_API_KEY is not configured.")
            return None

        params = {
            "api-key": self.api_key,
            "format": "json",
            "limit": 1000,
            "filters[state]": "Maharashtra"
        }
        if date_override:
            params["filters[arrival_date]"] = date_override

        try:
            resp = requests.get(BASE_API_URL, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("records", [])
                return records
            else:
                logger.warning(f"data.gov.in returned status code {resp.status_code}: {resp.text[:200]}")
                return None
        except Exception as e:
            logger.warning(f"Failed to connect to data.gov.in: {e}")
            return None

    def run_daily_sync(self, date_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs daily sync pipeline. If API is down or key missing,
        gracefully falls back to 60-day ReplayService.
        """
        timestamp_now = datetime.now().isoformat()
        raw_records = self._fetch_from_api(date_override)

        # If API succeeded and returned records
        if raw_records is not None and len(raw_records) > 0:
            conn = get_connection()
            cursor = conn.cursor()
            inserted_count = 0

            for raw in raw_records:
                rec = self.clean_record(raw)
                if not rec:
                    continue

                check_q = """
                SELECT 1 FROM prices
                WHERE arrival_date = ? AND LOWER(commodity) = LOWER(?) AND LOWER(market) = LOWER(?) AND LOWER(variety) = LOWER(?)
                LIMIT 1
                """
                exists = cursor.execute(check_q, (
                    rec["arrival_date"], rec["commodity"], rec["market"], rec["variety"]
                )).fetchone()

                if not exists:
                    cursor.execute("""
                    INSERT INTO prices (
                        arrival_date, commodity, state, district, market, variety, grade,
                        min_price, max_price, modal_price, is_interpolated, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rec["arrival_date"], rec["commodity"], rec["state"], rec["district"],
                        rec["market"], rec["variety"], rec["grade"],
                        rec["min_price"], rec["max_price"], rec["modal_price"],
                        rec["is_interpolated"], rec["source"]
                    ))
                    inserted_count += 1

            conn.commit()
            conn.close()

            if inserted_count > 0:
                try:
                    ForecastRefresher().refresh_all_forecasts()
                except Exception as e:
                    logger.warning(f"Forecast refresher error: {e}")

            result = {
                "status": "success",
                "records_added": inserted_count,
                "source": "api",
                "last_sync_timestamp": timestamp_now,
                "details": f"Fetched {len(raw_records)} records from data.gov.in; inserted {inserted_count} new entries."
            }
            self._record_sync_status(result)
            return result

        # Fallback to replay simulation
        logger.info("Falling back gracefully to ReplayService simulator.")
        try:
            replay = ReplayService()
            step_result = replay.step_forward()
            records_count = step_result.get("records_revealed", 0)

            result = {
                "status": "fallback",
                "records_added": records_count,
                "source": "simulation",
                "last_sync_timestamp": timestamp_now,
                "details": f"API unavailable (or key missing); gracefully advanced ReplayService simulation to Day {step_result.get('simulation_day')} ({step_result.get('current_date')}) revealing {records_count} records."
            }
            self._record_sync_status(result)
            return result
        except Exception as e:
            logger.error(f"Fallback to ReplayService failed: {e}")
            result = {
                "status": "failed",
                "records_added": 0,
                "source": "cached",
                "last_sync_timestamp": timestamp_now,
                "details": f"Sync failed and fallback simulation encountered error: {str(e)}"
            }
            self._record_sync_status(result)
            return result
