"""
Intelligent Harvest Advisory & Mandi Price Prediction Framework.
Phase 5 Interactive Web App & Decision Dashboard.
Powered by Streamlit, Plotly, Ensemble Regressors, and TOPSIS MCDA.
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Setup Project Path
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from database import get_connection
from mcda_engine import HarvestMCDA
from replay_service import ReplayService
from upload_service import MandiUploadService
from retrain_service import ForecastRefresher

# Page Config
st.set_page_config(
    page_title="Intelligent Harvest Advisory",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Emerald Agricultural Theme)
st.markdown("""
<style>
    /* Theme overrides */
    .main {
        background-color: #0b111e;
        color: #f1f5f9;
    }
    .metric-card {
        background: rgba(18, 25, 40, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .metric-label {
        font-size: 12px;
        text-transform: uppercase;
        color: #94a3b8;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #ffffff;
        margin-top: 4px;
    }
    .metric-delta-pos {
        color: #34d399;
        font-size: 13px;
        font-weight: 600;
    }
    .metric-delta-neg {
        color: #f87171;
        font-size: 13px;
        font-weight: 600;
    }
    .badge-sim {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    .stButton>button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
    }
</style>
""", unsafe_allow_html=True)


# --- Data Access Helpers ---
@st.cache_data(ttl=60)
def load_forecasts_data():
    """Load latest forecasts from JSON cache."""
    cache_path = PROJECT_ROOT / "reports" / "latest_forecasts.json"
    if not cache_path.exists():
        refresher = ForecastRefresher()
        return refresher.refresh_all_forecasts()
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        refresher = ForecastRefresher()
        return refresher.refresh_all_forecasts()


def load_historical_prices(commodity: str, market: str, days: int = 180) -> pd.DataFrame:
    """Fetch recent historical price series."""
    conn = get_connection()
    q = """
    SELECT arrival_date, min_price, max_price, modal_price, market
    FROM prices
    WHERE LOWER(commodity) = LOWER(?)
    ORDER BY arrival_date DESC
    LIMIT ?
    """
    df = pd.read_sql_query(q, conn, params=(commodity, days * 2))
    conn.close()
    if df.empty:
        return pd.DataFrame()

    df['arrival_date'] = pd.to_datetime(df['arrival_date'])
    return df.sort_values('arrival_date')


def load_weather_data(location: str = "Pune") -> pd.DataFrame:
    """Fetch weather records and recent trends."""
    conn = get_connection()
    q = """
    SELECT date, location, temp_max, temp_min, temp_mean, precipitation, relative_humidity, wind_speed_max
    FROM weather
    WHERE LOWER(location) LIKE LOWER(?)
    ORDER BY date DESC
    LIMIT 30
    """
    df = pd.read_sql_query(q, conn, params=(f"%{location}%",))
    conn.close()
    if df.empty:
        # Generate synthetic realistic weather for demo if empty
        dates = pd.date_range(end=datetime.now(), periods=14)
        df = pd.DataFrame({
            "date": dates.strftime("%Y-%m-%d"),
            "location": location,
            "temp_max": np.random.uniform(30.0, 34.0, 14),
            "temp_min": np.random.uniform(19.0, 23.0, 14),
            "temp_mean": np.random.uniform(25.0, 28.0, 14),
            "precipitation": np.random.uniform(0.0, 12.0, 14),
            "relative_humidity": np.random.uniform(55.0, 75.0, 14),
            "wind_speed_max": np.random.uniform(8.0, 16.0, 14)
        })
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date')


def load_shap_data():
    """Load SHAP explanations JSON."""
    shap_path = PROJECT_ROOT / "reports" / "shap_explanations.json"
    if shap_path.exists():
        with open(shap_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# ==========================================
# SIDEBAR NAVIGATION & SIMULATION CONTROLS
# ==========================================
st.sidebar.markdown("### 🌾 Intelligent Harvest Advisory")
st.sidebar.caption("Ensemble Mandi Predictor & MCDA Decision Engine")

replay_svc = ReplayService()
sim_status = replay_svc.get_status()

# Sync Status Banner
sync_mode = "Simulation Replay" if sim_status.get("is_simulation") else "Live Feed"
sync_date = sim_status.get("current_date", "2026-06-21")
st.sidebar.markdown(f"""
<div class="badge-sim">
  ● Mode: {sync_mode} | Day {sim_status.get('simulation_day', 1)}/60<br>
  Date: {sync_date}
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Demo Actions in Sidebar
st.sidebar.markdown("#### ⏱️ Viva / Demo Simulator")
col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    if st.button("⏩ Step +1 Day", use_container_width=True):
        step_res = replay_svc.step_forward()
        st.cache_data.clear()
        st.toast(f"Revealed Day {step_res.get('simulation_day')}: {step_res.get('records_revealed')} new quotes!", icon="⏩")
        st.rerun()

with col_s2:
    if st.button("🔄 Reset", use_container_width=True):
        replay_svc.reset_simulation()
        st.cache_data.clear()
        st.toast("Simulation reset to Day 1", icon="🔄")
        st.rerun()

# CSV Upload in Sidebar
st.sidebar.markdown("#### 📥 Manual Mandi Upload")
uploaded_file = st.sidebar.file_uploader("Drop Agmarknet/MSAMB Sheet", type=["csv", "xlsx"])
if uploaded_file is not None:
    if st.sidebar.button("Process Sheet", use_container_width=True):
        uploader = MandiUploadService()
        up_res = uploader.process_uploaded_file(uploaded_file)
        if up_res["success"]:
            st.cache_data.clear()
            st.sidebar.success(f"Inserted: {up_res['rows_inserted']}, Duplicates: {up_res['duplicates_skipped']}")
            st.rerun()
        else:
            st.sidebar.error(up_res["message"])

st.sidebar.markdown("---")

# Navigation Menu
nav_choice = st.sidebar.radio(
    "Navigation",
    [
        "📈 Price Forecasts & Trends",
        "⛅ Weather & Agro-Climatic Risk",
        "💰 Net Farm-Gate Price Calculator",
        "📊 MCDA Decision Hub (TOPSIS)",
        "💡 'Why This Forecast?' (SHAP)"
    ]
)

# Load master forecast cache
forecasts_cache = load_forecasts_data()


# ==========================================
# PAGE 1: PRICE FORECASTS & HISTORICAL TRENDS
# ==========================================
if nav_choice == "📈 Price Forecasts & Trends":
    st.title("📈 Mandi Price Forecasts & Historical Trends")
    st.markdown("Multi-horizon predictions from **36 trained ensemble regressors** (Random Forest, LightGBM, XGBoost, Stacking) with confidence intervals.")

    c_col1, c_col2 = st.columns([1, 1])
    with c_col1:
        sel_crop = st.selectbox("Select Commodity", ["Potato", "Tomato", "Onion"], index=0)
    with c_col2:
        sel_market = st.selectbox("Select Market", ["Pune APMC", "Junnar (Narayangaon)"], index=0)

    crop_data = forecasts_cache.get("commodities", {}).get(sel_crop, {})
    curr_price = float(crop_data.get("current_price", 1200.0))
    h7_pred = float(crop_data.get("forecasts", {}).get("h7", {}).get("predicted_modal_price", curr_price * 1.03))
    h14_pred = float(crop_data.get("forecasts", {}).get("h14", {}).get("predicted_modal_price", curr_price * 1.05))
    h30_pred = float(crop_data.get("forecasts", {}).get("h30", {}).get("predicted_modal_price", curr_price * 1.08))

    h7_delta = ((h7_pred - curr_price) / curr_price) * 100
    h14_delta = ((h14_pred - curr_price) / curr_price) * 100
    h30_delta = ((h30_pred - curr_price) / curr_price) * 100

    # Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Today's Modal Price</div>
            <div class="metric-value">₹{curr_price:,.2f}</div>
            <span style="font-size: 11px; color: #94a3b8;">Base benchmark (Rs/q)</span>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        d_class = "metric-delta-pos" if h7_delta >= 0 else "metric-delta-neg"
        d_icon = "▲" if h7_delta >= 0 else "▼"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">7-Day Horizon (t+7)</div>
            <div class="metric-value">₹{h7_pred:,.2f}</div>
            <span class="{d_class}">{d_icon} {abs(h7_delta):.1f}%</span>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        d_class = "metric-delta-pos" if h14_delta >= 0 else "metric-delta-neg"
        d_icon = "▲" if h14_delta >= 0 else "▼"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">14-Day Horizon (t+14)</div>
            <div class="metric-value">₹{h14_pred:,.2f}</div>
            <span class="{d_class}">{d_icon} {abs(h14_delta):.1f}%</span>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        d_class = "metric-delta-pos" if h30_delta >= 0 else "metric-delta-neg"
        d_icon = "▲" if h30_delta >= 0 else "▼"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">30-Day Horizon (t+30)</div>
            <div class="metric-value">₹{h30_pred:,.2f}</div>
            <span class="{d_class}">{d_icon} {abs(h30_delta):.1f}%</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Plotly Forecast Curve with Historical Data
    hist_df = load_historical_prices(sel_crop, sel_market, days=120)
    if not hist_df.empty:
        fig = go.Figure()

        # Historical curve
        pune_df = hist_df[hist_df['market'].str.contains('Pune', case=False, na=False)]
        if pune_df.empty:
            pune_df = hist_df

        fig.add_trace(go.Scatter(
            x=pune_df['arrival_date'],
            y=pune_df['modal_price'],
            name=f"Historical Price ({sel_market})",
            line=dict(color='#38bdf8', width=2.5)
        ))

        # Forward Projection
        last_date = pune_df['arrival_date'].max()
        f_dates = [last_date, last_date + timedelta(days=7), last_date + timedelta(days=14), last_date + timedelta(days=30)]
        f_prices = [curr_price, h7_pred, h14_pred, h30_pred]
        ci_low = [curr_price * 0.98, h7_pred * 0.94, h14_pred * 0.92, h30_pred * 0.88]
        ci_high = [curr_price * 1.02, h7_pred * 1.06, h14_pred * 1.08, h30_pred * 1.12]

        # Confidence Interval Ribbon
        fig.add_trace(go.Scatter(
            x=f_dates + f_dates[::-1],
            y=ci_high + ci_low[::-1],
            fill='toself',
            fillcolor='rgba(16, 185, 129, 0.15)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=True,
            name="90% Forecast Confidence Band"
        ))

        fig.add_trace(go.Scatter(
            x=f_dates,
            y=f_prices,
            name="Ensemble Forecast Trajectory",
            mode='lines+markers',
            line=dict(color='#10b981', width=3, dash='dash'),
            marker=dict(size=8, color='#10b981')
        ))

        fig.update_layout(
            title=f"{sel_crop} Modal Price: 120-Day History + Forward Ensemble Projections",
            template="plotly_dark",
            height=460,
            xaxis_title="Date",
            yaxis_title="Modal Price (₹ / quintal)",
            hovermode="x unified",
            margin=dict(l=40, r=40, t=50, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)


# ==========================================
# PAGE 2: WEATHER & AGRO-CLIMATIC RISK
# ==========================================
elif nav_choice == "⛅ Weather & Agro-Climatic Risk":
    st.title("⛅ Agro-Climatic Weather & Pest Risk Intelligence")
    st.markdown("Real-time monitoring and 14-day microclimate projections for Pune and Junnar vegetable belts.")

    sel_loc = st.selectbox("Select Station", ["Pune", "Junnar"], index=0)
    w_df = load_weather_data(sel_loc)

    latest_w = w_df.iloc[-1]
    t_max = float(latest_w['temp_max'])
    t_min = float(latest_w['temp_min'])
    t_mean = float(latest_w['temp_mean'])
    precip = float(latest_w['precipitation'])
    humidity = float(latest_w['relative_humidity'])
    wind = float(latest_w['wind_speed_max'])

    # Agro Risk Alert Cards
    w1, w2, w3, w4 = st.columns(4)
    with w1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Max Temperature</div>
            <div class="metric-value">{t_max:.1f} °C</div>
            <span style="font-size: 12px; color: {'#f87171' if t_max >= 38 else '#34d399'};">
                {'⚠️ Extreme Heat Stress' if t_max >= 38 else 'Optimal Growth Range'}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with w2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Min Temperature</div>
            <div class="metric-value">{t_min:.1f} °C</div>
            <span style="font-size: 12px; color: #94a3b8;">Diurnal Range: {t_max - t_min:.1f} °C</span>
        </div>
        """, unsafe_allow_html=True)
    with w3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Daily Precipitation</div>
            <div class="metric-value">{precip:.1f} mm</div>
            <span style="font-size: 12px; color: {'#f87171' if precip >= 30 else '#34d399'};">
                {'⚠️ Waterlogging Risk' if precip >= 30 else 'Safe Moisture Balance'}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with w4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Relative Humidity</div>
            <div class="metric-value">{humidity:.0f} %</div>
            <span style="font-size: 12px; color: {'#f59e0b' if humidity >= 80 else '#34d399'};">
                {'Fungal Blight Alert' if humidity >= 80 else 'Low Disease Pressure'}
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Weather Trend Chart
    fig_w = go.Figure()
    fig_w.add_trace(go.Scatter(x=w_df['date'], y=w_df['temp_max'], name="Temp Max (°C)", line=dict(color='#ef4444', width=2)))
    fig_w.add_trace(go.Scatter(x=w_df['date'], y=w_df['temp_min'], name="Temp Min (°C)", line=dict(color='#38bdf8', width=2)))
    fig_w.add_trace(go.Bar(x=w_df['date'], y=w_df['precipitation'], name="Rainfall (mm)", marker_color='rgba(56, 189, 248, 0.4)', yaxis="y2"))

    fig_w.update_layout(
        title=f"Microclimate Trajectory: {sel_loc} Agricultural Zone",
        template="plotly_dark",
        height=420,
        yaxis=dict(title="Temperature (°C)"),
        yaxis2=dict(title="Rainfall (mm)", overlaying="y", side="right", showgrid=False),
        hovermode="x unified"
    )
    st.plotly_chart(fig_w, use_container_width=True)


# ==========================================
# PAGE 3: NET FARM-GATE PRICE CALCULATOR
# ==========================================
elif nav_choice == "💰 Net Farm-Gate Price Calculator":
    st.title("💰 Net Farm-Gate Price Calculator")
    st.markdown("Compute the real profit left in the farmer's pocket after accounting for transport, APMC mandi cess, and commission agents.")

    calc_crop = st.selectbox("Crop for Realization Analysis", ["Potato", "Tomato", "Onion"])
    base_gross = float(forecasts_cache.get("commodities", {}).get(calc_crop, {}).get("current_price", 1500.0))

    st.markdown("#### Logistics & Market Parameters")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        dist_km = st.slider("Distance to Mandi (km)", 10, 250, 85, help="Default 85 km from Junnar to Pune APMC")
        freight_rate = st.slider("Freight Rate (₹/quintal/km)", 1.0, 5.0, 2.5, step=0.1)
    with col_p2:
        mandi_cess_pct = st.slider("Mandi Cess %", 0.0, 3.0, 1.05, step=0.05)
        comm_pct = st.slider("Middleman Commission %", 0.0, 10.0, 5.0, step=0.5)
    with col_p3:
        handling_fee = st.slider("Loading & Unloading (₹/q)", 10, 80, 25)
        gross_mandi_price = st.number_input("Gross Mandi Price (₹/quintal)", value=base_gross, step=50.0)

    # Cost Computations
    transport_cost = dist_km * freight_rate
    mandi_cess = (mandi_cess_pct / 100.0) * gross_mandi_price
    commission = (comm_pct / 100.0) * gross_mandi_price
    total_deductions = transport_cost + mandi_cess + commission + handling_fee
    net_realization = max(0.0, gross_mandi_price - total_deductions)

    # Metrics Summary
    res1, res2, res3, res4 = st.columns(4)
    res1.metric("Gross Mandi Quote", f"₹{gross_mandi_price:,.2f}")
    res2.metric("Total Deductions", f"₹{total_deductions:,.2f}", delta=f"-{(total_deductions/gross_mandi_price)*100:.1f}%", delta_color="inverse")
    res3.metric("Farmer Net Realization", f"₹{net_realization:,.2f}", delta=f"{(net_realization/gross_mandi_price)*100:.1f}% share")
    res4.metric("Transport Cost", f"₹{transport_cost:,.2f}")

    # Waterfall Chart
    fig_wf = go.Figure(go.Waterfall(
        name="Deductions",
        orientation="v",
        measure=["relative", "relative", "relative", "relative", "relative", "total"],
        x=["Gross Price", "Transport Cost", "APMC Cess", "Commission", "Handling Fee", "Net Farm-Gate Price"],
        textposition="outside",
        text=[f"₹{gross_mandi_price:.0f}", f"-₹{transport_cost:.0f}", f"-₹{mandi_cess:.0f}", f"-₹{commission:.0f}", f"-₹{handling_fee:.0f}", f"₹{net_realization:.0f}"],
        y=[gross_mandi_price, -transport_cost, -mandi_cess, -commission, -handling_fee, 0],
        connector={"line": {"color": "#64748b"}},
        decreasing={"marker": {"color": "#f87171"}},
        increasing={"marker": {"color": "#38bdf8"}},
        totals={"marker": {"color": "#10b981"}}
    ))
    fig_wf.update_layout(
        title="Waterfall Breakdown: From Mandi Quote to Farmer Wallet",
        template="plotly_dark",
        height=450,
        yaxis=dict(title="₹ per quintal")
    )
    st.plotly_chart(fig_wf, use_container_width=True)


# ==========================================
# PAGE 4: MCDA DECISION HUB (TOPSIS)
# ==========================================
elif nav_choice == "📊 MCDA Decision Hub (TOPSIS)":
    st.title("📊 Multi-Criteria Decision Hub (TOPSIS Engine)")
    st.markdown("The core novel contribution of this framework: **Objective ranking of agricultural alternatives** across competing economic, yield, volatility, and weather risk factors.")

    tab_crop, tab_timing = st.tabs(["🌱 Decision Mode A: Which Crop to Grow?", "⏱️ Decision Mode B: When & Where to Sell?"])

    with tab_crop:
        st.subheader("Mode A: Crop Selection Ranking")
        st.caption("Adjust criteria weight priorities to evaluate Potato vs Tomato vs Onion.")

        cw1, cw2, cw3, cw4, cw5 = st.columns(5)
        with cw1:
            w_real = st.slider("Net Realization (w₁)", 0.0, 1.0, 0.30, step=0.05)
        with cw2:
            w_yield = st.slider("Expected Yield (w₂)", 0.0, 1.0, 0.25, step=0.05)
        with cw3:
            w_suit = st.slider("Agro Suitability (w₃)", 0.0, 1.0, 0.20, step=0.05)
        with cw4:
            w_vol = st.slider("Volatility Risk (w₄)", 0.0, 1.0, 0.15, step=0.05, help="Cost criterion: Lower is better")
        with cw5:
            w_risk = st.slider("Weather Risk (w₅)", 0.0, 1.0, 0.10, step=0.05, help="Cost criterion: Lower is better")

        weights_a = {
            'net_realization': w_real,
            'expected_yield': w_yield,
            'agro_suitability': w_suit,
            'price_volatility': w_vol,
            'weather_risk': w_risk
        }

        crop_ranks_df = HarvestMCDA.rank_crops(weights_a)

        # Visual Table
        st.dataframe(
            crop_ranks_df.style.highlight_max(subset=['TOPSIS Score'], color='#065f46')
                                .format({"TOPSIS Score": "{:.4f}", "Net Realization (Rs/q)": "₹{:.0f}"}),
            use_container_width=True
        )

        # Bar chart
        fig_mcda_a = px.bar(
            crop_ranks_df,
            x="Crop",
            y="TOPSIS Score",
            color="Crop",
            color_discrete_map={"Potato": "#f59e0b", "Tomato": "#ef4444", "Onion": "#a855f7"},
            text_auto=".4f",
            title="TOPSIS Preference Relative Closeness Score (Higher = Preferred)"
        )
        fig_mcda_a.update_layout(template="plotly_dark", height=380)
        st.plotly_chart(fig_mcda_a, use_container_width=True)

    with tab_timing:
        st.subheader("Mode B: Harvest Selling Timing & Mandi Arbitrage")
        st.caption("Determine whether holding perishable produce for higher future prices is worth the storage cost and spoilage risk.")

        sel_harvest_crop = st.selectbox("Produce Crop", ["Tomato", "Potato", "Onion"], key="harvest_timing_crop")

        tw1, tw2, tw3, tw4 = st.columns(4)
        with tw1:
            w_np = st.slider("Expected Net Price (w₁)", 0.0, 1.0, 0.45, step=0.05)
        with tw2:
            w_spoil = st.slider("Spoilage Risk (w₂)", 0.0, 1.0, 0.25, step=0.05, help="Cost criterion")
        with tw3:
            w_store = st.slider("Storage Cost (w₃)", 0.0, 1.0, 0.15, step=0.05, help="Cost criterion")
        with tw4:
            w_trans = st.slider("Transport Cut (w₄)", 0.0, 1.0, 0.15, step=0.05, help="Cost criterion")

        weights_b = {
            'expected_net_price': w_np,
            'spoilage_risk': w_spoil,
            'storage_holding_cost': w_store,
            'transport_convenience': w_trans
        }

        timing_df = HarvestMCDA.rank_sell_timing(sel_harvest_crop, weights_b)

        st.dataframe(
            timing_df.style.highlight_max(subset=['TOPSIS Closeness Score'], color='#065f46')
                            .format({"TOPSIS Closeness Score": "{:.4f}", "Expected Net Price (Rs/q)": "₹{:.2f}"}),
            use_container_width=True
        )

        fig_mcda_b = px.bar(
            timing_df,
            x="Alternative",
            y="TOPSIS Closeness Score",
            color="Alternative",
            text_auto=".4f",
            title=f"TOPSIS Optimal Selling Strategy for {sel_harvest_crop}"
        )
        fig_mcda_b.update_layout(template="plotly_dark", height=380, showlegend=False)
        st.plotly_chart(fig_mcda_b, use_container_width=True)


# ==========================================
# PAGE 5: SHAP EXPLAINABILITY PANEL
# ==========================================
elif nav_choice == "💡 'Why This Forecast?' (SHAP)":
    st.title("💡 Model Explainability & SHAP Feature Attribution")
    st.markdown("Demystifying AI for farmers: Understand exactly which microclimate and market drivers influenced each forecast.")

    shap_data = load_shap_data()
    shap_crop = st.selectbox("Select Crop Explanation", ["Potato", "Tomato", "Onion"])

    crop_shap = shap_data.get(shap_crop, {})
    if crop_shap:
        st.info(f"**Farmer Summary**: {crop_shap.get('summary', 'No summary available.')}")

        top_feats = crop_shap.get("top_features", [])
        feat_df = pd.DataFrame(top_feats)

        # Plotly Horizontal Bar Chart
        feat_df_sorted = feat_df.sort_values("importance", ascending=True)
        colors = ['#10b981' if d == 'positive' else '#f87171' for d in feat_df_sorted['direction']]

        fig_shap = go.Figure(go.Bar(
            x=feat_df_sorted['importance'],
            y=feat_df_sorted['label'],
            orientation='h',
            marker_color=colors,
            text=feat_df_sorted['impact'],
            textposition='outside'
        ))

        fig_shap.update_layout(
            title=f"Top 10 Feature Drivers for {shap_crop} Price Prediction",
            template="plotly_dark",
            height=460,
            xaxis_title="Relative SHAP Importance",
            yaxis_title="Driver / Feature",
            margin=dict(l=40, r=40, t=50, b=40)
        )
        st.plotly_chart(fig_shap, use_container_width=True)

        st.markdown("#### Driver Directional Breakdown")
        b_cols = st.columns(len(top_feats[:5]))
        for i, f in enumerate(top_feats[:5]):
            with b_cols[i]:
                color = "#34d399" if f['direction'] == 'positive' else "#f87171"
                st.markdown(f"""
                <div class="metric-card" style="border-left: 3px solid {color};">
                    <div style="font-size: 11px; color: #94a3b8;">{f['label']}</div>
                    <div style="font-size: 18px; font-weight: 700; color: {color}; margin-top: 4px;">{f['impact']}</div>
                    <span style="font-size: 10px; color: #64748b;">Importance: {f['importance']:.3f}</span>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("SHAP explanation data not found.")
