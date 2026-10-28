# AI TASK SPECIFICATION: PHASE 4 - DAILY UPDATING & AUTOMATION PIPELINE
**Assigned Team Member**: Tanmay  
**Project**: Intelligent Harvest Advisory & Mandi Price Prediction Framework Using Ensemble Regressors and MCDA  
**Branch/Work Area**: `src/` (Daily Pipeline & Automation Engine)

---

> ### 📋 HOW TO USE THIS DOCUMENT WITH AN AI ASSISTANT:
> Copy and paste this entire document into your AI coding assistant (ChatGPT, Claude, Gemini, Antigravity).  
> Then add the instruction:  
> *"Please act as my senior python engineer and implement all the modules and test scripts described in this specification, adhering strictly to the architecture, database schema, and interface contracts specified below."*

---

## 1. PROJECT BACKGROUND & CURRENT STATE

Our team is building an Intelligent Harvest Advisory system for three key vegetable crops in Maharashtra (Pune & Junnar districts): **Potato**, **Tomato**, and **Onion**.

### What Has Already Been Built (Do NOT Re-implement):
1. **Database** (`data/processed/harvest_advisory.db`):
   - SQLite database already contains **75,890 cleaned mandi price records** (2001–2026) and **18,890 daily weather records** for Pune and Junnar.
   - Tables:
     - `prices`: (`id`, `arrival_date`, `commodity`, `state`, `district`, `market`, `variety`, `grade`, `min_price`, `max_price`, `modal_price`, `is_interpolated`, `source`)
     - `weather`: (`id`, `date`, `location`, `latitude`, `longitude`, `temp_max`, `temp_min`, `temp_mean`, `precipitation`, `relative_humidity`, `wind_speed_max`)
     - `crop_economics`: Cultivation cost, average yield, production cost per quintal.
     - `crop_suitability`: FAO EcoCrop thermal and rainfall ranges.
     - `logistics_assumptions`: Transport rate per km, mandi cess (1.05%), middleman fee (5%).
2. **Database Connector** (`src/database.py`):
   - Call `get_connection()` to get an open SQLite connection with WAL mode enabled.
3. **Price Predictors & Feature Engineering**:
   - `src/feature_engineering.py`: Function `build_crop_feature_matrix(commodity, market)` constructs the 47-feature matrix.
   - `models/*.joblib`: 36 trained ensemble models (RF, XGBoost, LightGBM, Stacking) saved on disk for horizons 7, 14, 30 days.

---

## 2. YOUR RESPONSIBILITY: PHASE 4 PIPELINE

According to the official project plan, mandi prices are published once a day (not real-time). The system needs a robust daily pipeline that operates reliably even during college vivas when government APIs fail.

You need to build 4 core modules in `src/` and an integration test in `tests/`:

```
silly-noether/
├── src/
│   ├── daily_updater.py       <-- Task 1: Scheduled daily fetch & append
│   ├── replay_service.py      <-- Task 2: 60-day historical replay simulator
│   ├── upload_service.py      <-- Task 3: Manual CSV/Excel upload processor
│   └── retrain_service.py     <-- Task 4: Incremental forecast refresher
└── tests/
    └── test_daily_pipeline.py <-- Task 5: End-to-end integration test
```

---

## 3. DETAILED MODULE SPECIFICATIONS

### Task 1: `src/daily_updater.py` (Daily Fetch & Ingestion)
- **Objective**: Runs a daily job (or callable on demand) to pull the latest daily quotes from `data.gov.in` (Agmarknet Resource ID: `9ef84268-d588-465a-a308-a864a43d0070`).
- **Core Requirements**:
  1. Read `DATA_GOV_IN_API_KEY` from environment variables / `.env`.
  2. If the API key is not present or the API returns non-200 / timeout:
     - Fall back gracefully to `replay_service.py` or keep the last known records.
     - Record the "last successful update" timestamp in a JSON file `reports/sync_status.json`.
  3. Clean incoming records using our standard rules:
     - Merge ` APMC` suffix (e.g. `Pune APMC` -> `Pune`).
     - Standardize dates to `YYYY-MM-DD`.
     - Filter/scale per-kg typos ($< 50$ Rs/q).
  4. Deduplicate: Do not insert records that already exist in `prices` for the same `(arrival_date, commodity, market, variety)`.
- **Public API**:
  ```python
  class DailyUpdater:
      def run_daily_sync(self, date_override: Optional[str] = None) -> Dict[str, Any]:
          """
          Returns:
          {
              "status": "success" | "fallback" | "failed",
              "records_added": int,
              "source": "api" | "simulation" | "cached",
              "last_sync_timestamp": str,
              "details": str
          }
          """
  ```

### Task 2: `src/replay_service.py` (60-Day Viva/Demo Simulator)
- **Objective**: Project plan page 4 explicitly requires: *"For the demo, add a replay mode that feeds the last 60 days of held-out data in day by day, clearly labeled as a simulation, alongside the real feed."*
- **Core Requirements**:
  1. Identify the latest 60 distinct dates present in `prices`.
  2. Maintain a state pointer (e.g., in `data/processed/simulation_state.json`) tracking which simulation day is currently active (e.g., Day 1 to Day 60).
  3. `step_forward()`: Advance by 1 day, "reveals" that day's real mandi prices, triggers forecast refresh, and returns the newly revealed records.
  4. `reset_simulation()`: Resets the simulation pointer back to Day 1.
  5. `get_current_simulation_status()`: Returns current simulation date, progress (e.g., Day 14 of 60), and records count.
- **Public API**:
  ```python
  class ReplayService:
      def step_forward(self) -> Dict[str, Any]: ...
      def reset_simulation(self) -> Dict[str, Any]: ...
      def get_status(self) -> Dict[str, Any]: ...
  ```

### Task 3: `src/upload_service.py` (Manual CSV Upload Handler)
- **Objective**: Allow farmers/examiners to drop an Agmarknet or MSAMB CSV/Excel export directly into the system.
- **Core Requirements**:
  1. Accept a file path or in-memory file buffer (CSV or `.xlsx`).
  2. Automatically detect headers: handle both Agmarknet format (`Arrival_Date`, `Market`, `Commodity`, `Modal_Price`) and generic sheets.
  3. Parse dates (support mixed `DD/MM/YYYY` and `YYYY-MM-DD`).
  4. Strip trailing ` APMC` tags.
  5. Deduplicate against existing SQLite records.
  6. Return a summary dictionary showing rows parsed, duplicates skipped, and rows successfully inserted into `prices`.
- **Public API**:
  ```python
  class MandiUploadService:
      def process_uploaded_file(self, file_path_or_buffer) -> Dict[str, Any]:
          """
          Returns:
          {
              "success": bool,
              "rows_processed": int,
              "rows_inserted": int,
              "duplicates_skipped": int,
              "commodity_summary": Dict[str, int],
              "message": str
          }
          """
  ```

### Task 4: `src/retrain_service.py` (Incremental Forecast Refresher)
- **Objective**: Whenever new daily prices arrive (via updater, replay, or upload), re-compute the feature row and generate updated predictions for 7, 14, and 30 days ahead.
- **Core Requirements**:
  1. Query the latest updated records for Potato, Tomato, and Onion in Pune.
  2. Compute the current lags, 7d/14d rolling means, and recent weather values using `src/feature_engineering.py`.
  3. Load the best models (`models/{crop}_h{h}_xgb.joblib` or `_lgbm.joblib`).
  4. Generate new forecasted modal prices for $t+7$, $t+14$, and $t+30$ days.
  5. Save the updated predictions into a new table or JSON cache `reports/latest_forecasts.json` so that Prithviraj's frontend can instantly render them!
- **Public API**:
  ```python
  class ForecastRefresher:
      def refresh_all_forecasts(self) -> Dict[str, Any]:
          """
          Generates updated 7d, 14d, 30d predictions for Potato, Tomato, Onion.
          Saves to reports/latest_forecasts.json.
          """
  ```

### Task 5: `tests/test_daily_pipeline.py` (Verification Test)
- **Objective**: Run an end-to-end integration test verifying that:
  1. Replay simulation steps forward smoothly.
  2. Upload service correctly parses a test CSV.
  3. Daily updater handles missing API key gracefully without crashing.
  4. Forecast refresher updates `reports/latest_forecasts.json`.

---

## 4. INTEGRATION CONTRACT

- **Database Path**: Use `from database import get_connection` (always connects to `data/processed/harvest_advisory.db`).
- **Models Path**: Load models from `os.path.join(PROJECT_ROOT, "models")`.
- **Output Cache**: Write your forecast updates to `reports/latest_forecasts.json`. Prithviraj's UI (Phase 5) will read from this exact JSON file!
- **Dependencies**: Everything must work with standard packages: `pandas`, `sqlite3`, `joblib`, `requests`, `xgboost`, `lightgbm`.

---

## 5. DEFINITION OF DONE FOR TANMAY
1. All 4 `.py` files in `src/` are fully implemented and free of syntax/runtime errors.
2. `tests/test_daily_pipeline.py` passes 100% when executed with `python tests/test_daily_pipeline.py`.
3. `reports/latest_forecasts.json` is generated with real predictions for Potato, Tomato, and Onion.
