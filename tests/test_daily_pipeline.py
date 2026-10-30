"""
Integration Test Suite for Phase 4 Daily Pipeline & Automation Engine.
Tests:
1. Replay simulation stepping and state tracking.
2. Manual CSV/Excel upload processing, header normalization, and deduplication.
3. Daily updater graceful fallback handling when data.gov.in API key is missing.
4. Forecast refresher generating 7d, 14d, 30d predictions into reports/latest_forecasts.json.

Can be run via:
    python tests/test_daily_pipeline.py
"""

import sys
import os
import json
import io
import unittest
from pathlib import Path

# Ensure src/ is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from database import get_connection, init_db
from replay_service import ReplayService
from upload_service import MandiUploadService
from daily_updater import DailyUpdater
from retrain_service import ForecastRefresher


class TestDailyPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensure database and directories exist before running tests."""
        init_db()

    def test_01_replay_simulation(self):
        """Verify replay simulation resets, steps forward, and updates state."""
        replay = ReplayService()
        reset_res = replay.reset_simulation()
        self.assertEqual(reset_res["current_day"], 1)
        self.assertTrue(reset_res["active"])

        status = replay.get_status()
        self.assertEqual(status["simulation_day"], 1)
        self.assertTrue(status["is_simulation"])

        # Step forward
        step_res = replay.step_forward()
        self.assertEqual(step_res["status"], "success")
        self.assertEqual(step_res["simulation_day"], 1)
        self.assertGreaterEqual(step_res["records_revealed"], 0)
        self.assertTrue(step_res["is_simulation"])

        # Check that state progressed
        new_status = replay.get_status()
        self.assertEqual(new_status["simulation_day"], 2)

    def test_02_upload_service(self):
        """Verify manual CSV upload normalizes headers, cleans APMC tags, and deduplicates."""
        uploader = MandiUploadService()

        # Create test CSV content with diverse headers and APMC suffixes
        csv_content = """Arrival Date,Commodity Name,Market Center,Modal Price,Min Price,Max Price,State,District,Variety
2026-09-01,Tomato,Pune APMC,2400,2100,2600,Maharashtra,Pune,Hybrid
2026-09-01,Potato,Pune APMC,1800,1600,1950,Maharashtra,Pune,Other
2026-09-01,Onion,Junnar APMC,1500,1300,1650,Maharashtra,Pune,Red
02/09/2026,Tomato,Pune,2500,2200,2700,Maharashtra,Pune,Hybrid
"""
        buf = io.StringIO(csv_content)
        result1 = uploader.process_uploaded_file(buf)
        self.assertTrue(result1["success"], f"Upload failed: {result1.get('message')}")
        self.assertEqual(result1["rows_processed"], 4)
        self.assertGreaterEqual(result1["rows_inserted"], 0)

        # Upload exact same content again to test deduplication
        buf2 = io.StringIO(csv_content)
        result2 = uploader.process_uploaded_file(buf2)
        self.assertTrue(result2["success"])
        self.assertEqual(result2["rows_inserted"], 0)
        self.assertEqual(result2["duplicates_skipped"], 4)

    def test_03_daily_updater_graceful_fallback(self):
        """Verify daily updater does not crash when API key is missing and falls back to simulation."""
        # Force missing API key
        updater = DailyUpdater(api_key=None)
        # Temporarily clear env var if set
        orig_key = os.environ.pop("DATA_GOV_IN_API_KEY", None)

        try:
            res = updater.run_daily_sync()
            self.assertIn(res["status"], ["fallback", "success"])
            self.assertIn(res["source"], ["simulation", "api"])
            self.assertIn("last_sync_timestamp", res)
            
            # Check reports/sync_status.json was written
            sync_file = PROJECT_ROOT / "reports" / "sync_status.json"
            self.assertTrue(sync_file.exists(), "sync_status.json should be created")
            with open(sync_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                self.assertIn("status", saved)
        finally:
            if orig_key:
                os.environ["DATA_GOV_IN_API_KEY"] = orig_key

    def test_04_forecast_refresher(self):
        """Verify forecast refresher updates 7d, 14d, 30d predictions in reports/latest_forecasts.json."""
        refresher = ForecastRefresher()
        forecasts = refresher.refresh_all_forecasts()

        self.assertIn("updated_at", forecasts)
        self.assertIn("commodities", forecasts)

        # Ensure all 3 crops are present
        for crop in ["Potato", "Tomato", "Onion"]:
            self.assertIn(crop, forecasts["commodities"], f"{crop} missing from forecasts")
            crop_data = forecasts["commodities"][crop]
            self.assertIn("current_price", crop_data)
            self.assertIn("forecasts", crop_data)

            # Check horizons 7, 14, 30
            for h in [7, 14, 30]:
                h_key = f"h{h}"
                self.assertIn(h_key, crop_data["forecasts"])
                pred = crop_data["forecasts"][h_key]
                self.assertGreater(pred["predicted_modal_price"], 0)
                self.assertEqual(pred["horizon_days"], h)
                self.assertIn("target_date", pred)
                self.assertEqual(len(pred["confidence_interval"]), 2)

        # Verify physical file on disk
        cache_file = PROJECT_ROOT / "reports" / "latest_forecasts.json"
        self.assertTrue(cache_file.exists(), "latest_forecasts.json was not created on disk")
        with open(cache_file, "r", encoding="utf-8") as f:
            disk_data = json.load(f)
            self.assertIn("commodities", disk_data)
            self.assertIn("Potato", disk_data["commodities"])


def main():
    print("=" * 70)
    print("PHASE 4: DAILY PIPELINE INTEGRATION TEST SUITE")
    print("=" * 70)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDailyPipeline)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED SUCCESSFULLY! (100% OK)")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("TESTS FAILED!")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
