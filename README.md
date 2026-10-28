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

## Phase 2: Price Prediction & Ensemble Modeling (Completed)

1. **Feature Engineering** (`src/feature_engineering.py`):
   - 47 features constructed: Price lags (1, 2, 3, 7, 14, 21, 30), rolling statistical windows (mean, min, max, std over 7, 14, 30 days), momentum returns, Fourier sin/cos calendar seasonality, monsoon/winter flags, and meteorological risk metrics (7d/14d/30d rain sum, 7d temp, heat stress days, heavy rain days).

2. **Model Training & Multi-Horizon Benchmarking** (`src/train_models.py`):
   - Trained **Random Forest**, **XGBoost**, **LightGBM**, and a **Stacking Ensemble** (with RidgeCV meta-estimator) across **7-day**, **14-day**, and **30-day** forecasting horizons for all 3 crops.
   - Evaluated chronologically on the held-out last 12 months using **RMSE**, **MAE**, **MAPE (%)**, **ME (bias)**, and **RRMSE** against the Naive baseline ($y_{t+h} = y_t$).

3. **Key Findings**:
   - **Onion**: LightGBM beats Naive baseline across all horizons, achieving **RRMSE of 0.7229** at 7 days (27.7% error reduction) and **0.7324** at 14 days (26.8% error reduction).
   - **Potato**: Models decisively outperform the naive baseline at longer horizons: LightGBM achieves **RRMSE of 0.7756** (22.4% error reduction) at 30 days.
   - **Tomato**: At 30 days, Stacking Ensemble achieves **RRMSE of 0.8466** (MAPE drops from 35.04% naive down to 25.56%).
   - **SHAP Feature Attribution**: Native TreeSHAP identifies short-term momentum (`price_lag_1`, `price_roll_mean_7`), long-term seasonality (`cos_day`), and weather risk factors (`rain_30d_sum`, `temp_7d_mean`) as top drivers.

## Phase 3: Net Price & MCDA Engine (Completed)

1. **Net Farm-Gate Price Deduction Model** (`src/mcda_engine.py`):
   - Formulated $P_{\text{net}} = P_{\text{pred}} - (\text{transport} + \text{mandi cess} + \text{commission} + \text{handling})$.
   - Implemented dynamic calculation taking into account distance, freight rates, 1.05% APMC cess, 5.0% commission agent cut, and loading fees.

2. **Agro-Climatic Suitability Scoring**:
   - Implemented FAO EcoCrop thermal envelope scoring ($T_{\text{min\_abs}}$, $T_{\text{min\_opt}}$, $T_{\text{max\_opt}}$, $T_{\text{max\_abs}}$) and rainfall/blight penalties against real 14-day Open-Meteo forecasts.

3. **TOPSIS Optimization Engine**:
   - Implemented vector normalization, weighted normalized matrices, ideal positive/negative solutions, and relative closeness calculation ($C_i^*$).
   - **Mode A (Which Crop to Grow?)**: Ranks Potato vs. Tomato vs. Onion on 5 criteria: Net Price, Expected Yield, Suitability, Price Volatility, and Weather Risk.
   - **Mode B (When & Where to Sell?)**: Ranks Sell Today vs. +7 Days vs. +14 Days vs. Alternate Mandi, incorporating crop-specific perishability and spoilage rates.
   - **Sensitivity Analysis**: Validated dynamic rank shifts under yield-maximizing vs. risk-averse weight scenarios.

## Verification Suite

- Phase 1: `python tests/verify_phase1.py`
- Phase 2: `python tests/verify_phase2.py`
- Phase 3: `python tests/verify_phase3.py`
