# TEAM PROJECT ROADMAP & INTEGRATION SPECIFICATION
**Project**: Intelligent Harvest Advisory & Mandi Price Prediction Framework Using Ensemble Regressors and MCDA  
**Team**: Rahul (Lead), Tanmay, Prithviraj  

---

## 1. WORK BREAKDOWN STRUCTURE (WBS)

```
                            [ Intelligent Harvest Advisory Framework ]
                                               │
         ┌─────────────────────────────────────┼─────────────────────────────────────┐
         │                                     │                                     │
   [ RAHUL (Lead) ]                     [ TANMAY ]                         [ PRITHVIRAJ ]
┌────────────────────────┐           ┌────────────────────────┐           ┌────────────────────────┐
│ Phase 1: Data Engine   │           │ Phase 4: Daily Update  │           │ Phase 5: Interactive   │
│  - Mandi Data Clean    │ (Done)    │  - data.gov.in fetch   │           │          Web Dashboard │
│  - Open-Meteo Weather  │ (Done)    │  - 60d Replay Engine   │           │  - Forecast & History  │
│  - SQLite Database     │ (Done)    │  - CSV/Excel Uploader  │           │  - Weather Risk Alert  │
│                        │           │  - Forecast Refresher  │           │  - Net Price Calc      │
│ Phase 2: Price Predict │           │  - Pipeline Unit Tests │           │  - MCDA Weight Sliders │
│  - 47 Features         │ (Done)    └────────────────────────┘           │  - SHAP Visualizer     │
│  - RF, XGB, LGBM, Stack│ (Done)                │                        │  - Demo Simulator Bar  │
│  - Multi-Horizon (7/14/30)(Done)               │                        └────────────────────────┘
│  - Native TreeSHAP     │ (Done)                │                                     │
│                        │                       │                                     │
│ Phase 3: MCDA & TOPSIS │                       │                                     │
│  - Net Price Formula   │                       │                                     │
│  - Mode A (Which Crop) │                       │                                     │
│  - Mode B (Sell Timing)│                       │                                     │
└────────────────────────┘                       │                                     │
         │                                       │                                     │
         └───────────────────────────────────────┴─────────────────────────────────────┘
                                                 │
                                 [ ALL MEMBERS: Phase 6 ]
                                 Academic Evaluation Report,
                             Sensitivity Analysis & Final Slide Deck
```

---

## 2. MEMBER ASSIGNMENTS & DELIVERABLES

| Member | Phases Owned | Key Files Created / Managed | Role & Objective |
| :--- | :--- | :--- | :--- |
| **Rahul (You)** | **Phase 1, 2 & 3** | `src/database.py`<br>`src/clean_prices.py`<br>`src/weather_ingestion.py`<br>`src/seed_economics.py`<br>`src/feature_engineering.py`<br>`src/train_models.py`<br>`src/mcda_engine.py` | **Core Architecture & Intelligence**: Data foundation, machine learning ensemble modeling, and mathematical TOPSIS multi-criteria optimization engine. |
| **Tanmay** | **Phase 4** | `src/daily_updater.py`<br>`src/replay_service.py`<br>`src/upload_service.py`<br>`src/retrain_service.py`<br>`tests/test_daily_pipeline.py` | **Data Operations & Automation**: Real-time government API client, 60-day viva simulation replay engine, manual CSV upload processor, and background retraining triggers. |
| **Prithviraj** | **Phase 5** | `app.py`<br>`src/ui_components.py`<br>`requirements.txt` | **Full-Stack & Frontend UI**: Modern, responsive Streamlit dashboard featuring multi-horizon price curves, weather alerts, net-price sliders, interactive MCDA decision matrices, and SHAP explainability. |
| **Joint Team** | **Phase 6** | `reports/semester_project_report.md`<br>`presentation_slides.pptx` | **Final Evaluation & Reporting**: Baseline RRMSE comparison tables, weight sensitivity analysis, UI screenshots, and viva demonstration script. |

---

## 3. MASTER INTEGRATION ARCHITECTURE

All 3 members integrate seamlessly around shared artifacts without editing each other's files:

1. **Shared Database**:
   - `data/processed/harvest_advisory.db` (SQLite with WAL mode).
   - Rahul seeds and cleans historical data; Tanmay appends new daily records; Prithviraj reads data for UI charts.
2. **Shared Models**:
   - `models/*.joblib` (Trained Random Forest, XGBoost, LightGBM, and Stacking regressors).
   - Rahul trained the models; Tanmay triggers inference refresh; Prithviraj displays the resulting forecasts.
3. **Shared Inter-Module Interfaces**:
   - `src/mcda_engine.py` (Rahul) provides `HarvestMCDA.rank_crops(weights)` and `HarvestMCDA.rank_sell_timing(crop, weights)` directly to Prithviraj's UI sliders.
   - `src/replay_service.py` (Tanmay) provides `ReplayService().step_forward()` directly to Prithviraj's simulation buttons.
   - `reports/latest_forecasts.json` provides the current cached predictions rendered across all dashboard KPI cards.

---

## 4. HOW TO DISPATCH THE WORK IMMEDIATELY

1. Send **[`docs/TASK_TANMAY_PHASE4.md`](file:///c:/Users/Rahul/Documents/antigravity/silly-noether/docs/TASK_TANMAY_PHASE4.md)** to **Tanmay**.
   - He can copy the entire file into his AI assistant to generate Phase 4 modules and integration tests.
2. Send **[`docs/TASK_PRITHVIRAJ_PHASE5.md`](file:///c:/Users/Rahul/Documents/antigravity/silly-noether/docs/TASK_PRITHVIRAJ_PHASE5.md)** to **Prithviraj**.
   - He can copy the entire file into his AI assistant to generate the interactive Streamlit application.
3. You (Rahul) proceed with **Phase 3: Net Price & MCDA (TOPSIS Engine)**.
