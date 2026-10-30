"""
Replay Simulator Service for Viva/Demo.
Feeds the last 60 days of held-out mandi data day-by-day, clearly labeled
as a simulation, and triggers forecast updates.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from database import get_connection
except ImportError:
    from src.database import get_connection

logger = logging.getLogger(__name__)

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
STATE_FILE_PATH = PROJECT_ROOT / "data" / "processed" / "simulation_state.json"


class ReplayService:
    def __init__(self, state_file: Optional[Path] = None, total_days: int = 60):
        self.state_file = Path(state_file) if state_file else STATE_FILE_PATH
        self.total_days = total_days
        self.simulation_dates = self._fetch_latest_dates(limit=self.total_days)
        self._ensure_state_initialized()

    def _fetch_latest_dates(self, limit: int = 60) -> List[str]:
        """Fetch the latest distinct dates present in prices table in ascending order."""
        conn = get_connection()
        query = """
        SELECT DISTINCT arrival_date
        FROM prices
        WHERE arrival_date IS NOT NULL
        ORDER BY arrival_date DESC
        LIMIT ?
        """
        rows = conn.execute(query, (limit,)).fetchall()
        conn.close()
        dates = [row[0] for row in rows if row[0]]
        # Return in chronological order
        dates.reverse()
        return dates

    def _ensure_state_initialized(self):
        """Initialize state file if it doesn't exist."""
        if not self.state_file.exists():
            self.reset_simulation()

    def _read_state(self) -> Dict[str, Any]:
        """Read state from JSON file."""
        if not self.state_file.exists():
            return self.reset_simulation()
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self.reset_simulation()

    def _write_state(self, state: Dict[str, Any]):
        """Write state to JSON file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def reset_simulation(self) -> Dict[str, Any]:
        """Reset the simulation pointer back to Day 1."""
        if not self.simulation_dates:
            self.simulation_dates = self._fetch_latest_dates(limit=self.total_days)

        start_date = self.simulation_dates[0] if self.simulation_dates else None
        end_date = self.simulation_dates[-1] if self.simulation_dates else None

        state = {
            "active": True,
            "current_day": 1,
            "total_days": len(self.simulation_dates),
            "current_date": start_date,
            "start_date": start_date,
            "end_date": end_date,
            "is_simulation": True,
            "last_stepped_at": None,
            "message": "Simulation reset to Day 1"
        }
        self._write_state(state)
        return state

    def get_status(self) -> Dict[str, Any]:
        """Get the current simulation status."""
        state = self._read_state()
        current_day = state.get("current_day", 1)
        total_days = state.get("total_days", len(self.simulation_dates))
        progress_pct = round((current_day / max(1, total_days)) * 100, 1)

        return {
            "status": "active" if current_day <= total_days else "completed",
            "simulation_day": current_day,
            "total_days": total_days,
            "progress_percent": progress_pct,
            "current_date": state.get("current_date"),
            "start_date": state.get("start_date"),
            "end_date": state.get("end_date"),
            "is_simulation": True,
            "last_stepped_at": state.get("last_stepped_at"),
            "message": f"Day {current_day} of {total_days} ({state.get('current_date')})"
        }

    def get_current_simulation_status(self) -> Dict[str, Any]:
        """Alias for get_status() as requested in spec."""
        return self.get_status()

    def step_forward(self) -> Dict[str, Any]:
        """
        Advance by 1 day: reveals that day's real mandi prices,
        triggers forecast refresh, and returns the newly revealed records.
        """
        state = self._read_state()
        current_day = state.get("current_day", 1)
        total_days = len(self.simulation_dates)

        if current_day > total_days:
            return {
                "status": "completed",
                "simulation_day": current_day,
                "total_days": total_days,
                "current_date": state.get("current_date"),
                "records_revealed": 0,
                "records": [],
                "is_simulation": True,
                "message": "Simulation has already reached the final day. Call reset_simulation() to restart."
            }

        target_date = self.simulation_dates[current_day - 1]

        # Fetch records for this date
        conn = get_connection()
        query = """
        SELECT arrival_date, commodity, state, district, market, variety, grade,
               min_price, max_price, modal_price
        FROM prices
        WHERE arrival_date = ?
        """
        rows = conn.execute(query, (target_date,)).fetchall()
        conn.close()

        revealed_records = [dict(row) for row in rows]
        for r in revealed_records:
            r["source"] = "simulation_replay"
            r["is_simulation"] = True

        # Trigger forecast refresh
        forecast_status = "skipped"
        try:
            try:
                from retrain_service import ForecastRefresher
            except ImportError:
                from src.retrain_service import ForecastRefresher
            refresher = ForecastRefresher()
            refresher.refresh_all_forecasts()
            forecast_status = "refreshed"
        except Exception as e:
            logger.warning(f"Forecast refresh during simulation step failed: {e}")
            forecast_status = f"warning: {str(e)}"

        # Advance state
        next_day = current_day + 1
        next_date = self.simulation_dates[next_day - 1] if next_day <= total_days else target_date

        state["current_day"] = next_day
        state["current_date"] = target_date
        state["last_stepped_at"] = datetime.now().isoformat()
        self._write_state(state)

        return {
            "status": "success",
            "simulation_day": current_day,
            "total_days": total_days,
            "current_date": target_date,
            "next_date": next_date,
            "records_revealed": len(revealed_records),
            "records": revealed_records,
            "forecast_status": forecast_status,
            "is_simulation": True,
            "message": f"Successfully revealed Day {current_day}/{total_days} ({target_date}) with {len(revealed_records)} records"
        }
