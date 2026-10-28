# AI TASK SPECIFICATION: PHASE 5 - INTERACTIVE WEB APP & DECISION DASHBOARD
**Assigned Team Member**: Prithviraj  
**Project**: Intelligent Harvest Advisory & Mandi Price Prediction Framework Using Ensemble Regressors and MCDA  
**Branch/Work Area**: `app/` or `streamlit_app.py` (Frontend & Visual UI)

---

> ### 📋 HOW TO USE THIS DOCUMENT WITH AN AI ASSISTANT:
> Copy and paste this entire document into your AI coding assistant (ChatGPT, Claude, Gemini, Antigravity).  
> Then add the instruction:  
> *"Please act as my senior full-stack / UI engineer and implement the interactive dashboard described in this specification, using Streamlit (recommended in the project plan) or FastAPI with rich charts, connecting to our existing SQLite database, models, and MCDA engine."*

---

## 1. PROJECT BACKGROUND & CURRENT STATE

Our team is building an Intelligent Harvest Advisory system for three major vegetable crops in Maharashtra: **Potato**, **Tomato**, and **Onion**.

### What Has Already Been Built by Rahul and Tanmay (You Can Directly Import and Use):
1. **SQLite Database** (`data/processed/harvest_advisory.db`):
   - Access via `from src.database import get_connection`.
   - Contains:
     - `prices`: 75,890 cleaned mandi quotes (2001–2026) for Pune and Junnar.
     - `weather`: 18,890 daily weather records (temperature, rainfall, humidity, wind) + 14-day forecasts.
     - `crop_economics`: Cultivation cost, average yield, and cost of production per quintal.
     - `crop_suitability`: FAO EcoCrop temperature and rainfall optimal ranges.
     - `logistics_assumptions`: Distance, transport rate, mandi cess (1.05%), and commission (5%).
2. **Trained Models & Reports** (`models/` & `reports/`):
   - 36 trained ensemble models (RF, XGBoost, LightGBM, Stacking) in `models/`.
   - Evaluation metrics in `reports/model_evaluation_metrics.csv`.
   - Feature attribution in `reports/shap_explanations.json`.
3. **MCDA Engine** (`src/mcda_engine.py` built by Rahul):
   - `HarvestMCDA.rank_crops(weights: Dict)`: Returns TOPSIS rankings for Potato, Tomato, Onion.
   - `HarvestMCDA.rank_sell_timing(crop: str, weights: Dict)`: Returns rankings for Sell Now vs +7d vs +14d vs Alternate Mandi.
4. **Daily Updater & Simulation Services** (`src/` built by Tanmay):
   - `ReplayService().step_forward()`: Advances the simulation clock by 1 day for live demos.
   - `MandiUploadService().process_uploaded_file(file)`: Ingests user-dropped CSV/Excel sheets.
   - `reports/latest_forecasts.json`: Holds current model predictions.

---

## 2. YOUR RESPONSIBILITY: PHASE 5 DASHBOARD

The project plan explicitly specifies:
> *"Phase 5: Website. Pages: price forecast with history, weather, net-price calculator, crop ranking with weights, and a 'why this forecast' SHAP panel. A good stack is Python with FastAPI plus a simple frontend, or Streamlit for faster development."*

You need to build an intuitive, visually impressive dashboard in `app.py` (or `src/app.py`) using **Streamlit** (or FastAPI + HTML/Tailwind) that your professors and examiners can interact with during the viva.

---

## 3. CORE PAGES & FEATURES TO IMPLEMENT

Your application should feature a sidebar navigation with **5 core sections**:

### 📈 Page 1: Price Forecasts & Historical Trends
- **Controls**: Dropdown to select crop (**Potato**, **Tomato**, **Onion**) and market (**Pune APMC** or **Junnar Narayangaon**).
- **KPI Metrics Cards**:
  - Today's Modal Price (₹/quintal)
  - 7-Day Forecast (₹/q) & Expected Δ%
  - 14-Day Forecast (₹/q) & Expected Δ%
  - 30-Day Forecast (₹/q) & Expected Δ%
- **Interactive Chart (Plotly)**:
  - Historical price curve for the past 6 to 12 months.
  - Forward forecast trajectory (+7d, +14d, +30d) with confidence intervals.
  - Secondary comparison line: Pune vs Junnar price spread.

### 🌦️ Page 2: Weather & Agro-Climatic Risk
- **Controls**: Select Location (**Pune** or **Junnar**).
- **Current & 14-Day Forecast**:
  - Temperature range ($T_{\text{min}}$ to $T_{\text{max}}$).
  - 7-Day and 14-Day cumulative rainfall forecast.
  - Relative humidity and wind speed.
- **Crop Risk Alert Badges**:
  - Extreme Heat Stress Warning (if $T_{\text{max}} \ge 38^\circ\text{C}$).
  - Heavy Rainfall / Waterlogging Alert (if Rain $\ge 30\text{ mm/day}$).
  - Tuberization / Fruit Set Suitability score (based on FAO EcoCrop optimal ranges in `crop_suitability`).

### 💰 Page 3: Net Farm-Gate Price Calculator
- **Formula**: $P_{\text{net}} = P_{\text{pred}} - (\text{Transport} + \text{Mandi Cess} + \text{Middleman Commission} + \text{Handling})$
- **Interactive Input Sliders**:
  - Distance from Farm to Mandi (km) (default: 85 km for Junnar $\rightarrow$ Pune).
  - Freight Rate (₹/quintal/km) (default: ₹2.5/q/km).
  - APMC Mandi Cess % (default: 1.05%).
  - Middleman / Commission Agent % (default: 5.0%).
  - Loading & Unloading fee (₹/quintal) (default: ₹25/q).
- **Visual Breakdown**:
  - Waterfall or Donut chart showing Gross Mandi Price vs. Transportation vs. Mandi Cess vs. Middleman Cut vs. **Final Net Farmer Realization ($P_{\text{net}}$)**.

### ⚖️ Page 4: Interactive MCDA Decision Hub (The Core Contribution!)
The paper's flagship novelty is Multi-Criteria Decision Analysis using TOPSIS.
- **Mode A: Which Crop to Grow?**
  - Alternatives: **Potato** vs. **Tomato** vs. **Onion**.
  - **5 Interactive Weight Sliders (summing to 100% or normalized)**:
    1. Net Farm-Gate Realization ($w_1$)
    2. Expected Yield ($w_2$)
    3. Agro-Climatic Suitability ($w_3$)
    4. Price Volatility Risk ($w_4$ - lower is better)
    5. Weather Risk / Blight Probability ($w_5$ - lower is better)
  - **Dynamic TOPSIS Ranking Table & Bar Chart**: As the user moves the sliders, the ranking immediately shifts in real time!
- **Mode B: When & Where to Sell?**
  - Choose one crop (e.g. Tomato).
  - Alternatives: **Sell Today (Pune)** vs. **Sell +7 Days (Pune)** vs. **Sell +14 Days (Pune)** vs. **Sell at Junnar Mandi**.
  - Real-time ranking showing whether holding the harvest is worth the price rise after accounting for storage risk and transport costs!

### 🔍 Page 5: "Why This Forecast?" (SHAP Explainability)
- Visualizes model explainability from `reports/shap_explanations.json`.
- Displays:
  - Top 10 feature importance bar chart (e.g. `price_roll_mean_7`, `rain_30d_sum`, `temp_7d_mean`, `cos_day`).
  - Directional impact badges: Which features pushed the price **UP** (green) and which dragged it **DOWN** (red).
  - Plain-English farmer summary (e.g. *"Heavy rain over the past 30 days pushed onion prices higher due to supply bottleneck"*).

### 🔄 Header / Sidebar: Demo & Simulation Controls
- **"Step Forward 1 Day (Replay Mode)"**: Button that calls Tanmay's `ReplayService().step_forward()`, advancing the simulation clock and refreshing the dashboard with newly revealed prices!
- **"Upload Today's Mandi CSV"**: File uploader for testing manual CSV ingestion.
- **Sync Badge**: Displays `Last Updated: [Date] | Mode: [Simulation Replay / Live Feed]`.

---

## 4. UI/UX GUIDELINES
1. **Clean, Modern Theme**: Professional agricultural dashboard (use dark green / emerald accents, clean cards, responsive layout).
2. **Zero Hardcoded Data**: Everything must be pulled dynamically from `data/processed/harvest_advisory.db`, `reports/`, or the MCDA/Model classes.
3. **Execution Command**: Must launch cleanly with:
   ```bash
   streamlit run app.py
   ```
   or if FastAPI: `uvicorn app.main:app --reload`.

---

## 5. DEFINITION OF DONE FOR PRITHVIRAJ
1. `app.py` is fully implemented and starts cleanly without any errors.
2. All 5 pages render interactive charts (Plotly / Streamlit native) and respond dynamically to user sliders.
3. The MCDA weight sliders visibly alter the TOPSIS rankings in real-time.
4. "Step Forward" simulation button successfully triggers a day advance.
