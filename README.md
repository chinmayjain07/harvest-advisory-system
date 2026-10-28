# Intelligent Harvest Advisory & Mandi Price Prediction Framework

This repository implements the semester prototype of **"An Intelligent Harvest Advisory and Mandi Price Prediction Framework Using Ensemble Regressors and MCDA"**.

## Phase 1: Data Foundation (Completed)

1. **Cleaned Historical Datasets**:
   - **Potato**: 20,021 cleaned rows (2001-2026), outlier typos corrected, duplicates removed.
   - **Tomato**: 26,720 cleaned rows (2003-2026), authentic July-August 2023 price surge (up to Rs 15,000/q) preserved.
   - **Onion**: 29,149 cleaned rows (2001-2026), erroneous Rs 75,000/q entry typos filtered, 2019 crisis peaks preserved.
   - **Market Normalization**: All trailing ` APMC` market names consolidated (e.g., `Pune APMC` -> `Pune`).

2. **Unified SQLite Database** (`data/processed/harvest_advisory.db`):
   - `prices`: 75,890 total cleaned mandi price records across Potato, Tomato, and Onion with indexed queries.
   - `weather`: 18,890 daily weather records for Pune and Junnar from 2001 to 2026 (including 14-day forward forecast) via Open-Meteo.
   - `crop_economics`: Cultivation cost, average yield, and cost of production per quintal based on ICAR and Maharashtra DES data.
   - `crop_suitability`: FAO EcoCrop temperature and rainfall optimal/absolute ranges.
   - `logistics_assumptions`: Transport cost per quintal-km, APMC cess (1.05%), and middleman commission (5%).

3. **API & Data Ingestion Clients**:
   - `src/clean_prices.py`: Standardizes raw mandi records, performs outlier handling, and loads into SQLite.
   - `src/weather_ingestion.py`: Pulls daily historical archive and forecast weather from Open-Meteo API.
   - `src/agmarknet_client.py`: Client for `data.gov.in` Mandi Price API (Resource ID: `9ef84268-d588-465a-a308-a864a43d0070`) with simulation replay fallback.

## Execution

Verify Phase 1:
```bash
python tests/verify_phase1.py
```
