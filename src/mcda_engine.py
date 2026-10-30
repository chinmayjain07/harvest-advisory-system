import os
import sqlite3
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

from database import get_connection

class NetPriceCalculator:
    """
    Computes net farm-gate price realization per quintal:
    P_net = P_mandi - (Transport + Mandi Cess + Middleman Commission + Handling Fee)
    """
    def __init__(self):
        pass

    @staticmethod
    def calculate(
        gross_mandi_price: float,
        distance_km: float = 85.0,
        freight_rate_per_q_km: float = 2.5,
        mandi_cess_percent: float = 1.05,
        commission_percent: float = 5.0,
        handling_fee_per_q: float = 25.0
    ) -> Dict[str, float]:
        transport_cost = distance_km * freight_rate_per_q_km
        mandi_cess = gross_mandi_price * (mandi_cess_percent / 100.0)
        commission = gross_mandi_price * (commission_percent / 100.0)
        total_deductions = transport_cost + mandi_cess + commission + handling_fee_per_q
        net_price = max(0.0, gross_mandi_price - total_deductions)

        return {
            "gross_mandi_price": round(gross_mandi_price, 2),
            "transport_cost": round(transport_cost, 2),
            "mandi_cess": round(mandi_cess, 2),
            "middleman_commission": round(commission, 2),
            "handling_fee": round(handling_fee_per_q, 2),
            "total_deductions": round(total_deductions, 2),
            "net_farmgate_price": round(net_price, 2),
            "realization_ratio_pct": round((net_price / gross_mandi_price * 100.0), 2) if gross_mandi_price > 0 else 0.0
        }


class AgroSuitabilityEvaluator:
    """
    Evaluates temperature and precipitation conditions against FAO EcoCrop ranges.
    Returns a normalized score between 0.0 (completely unsuitable) and 1.0 (optimal).
    """
    def __init__(self):
        conn = get_connection()
        self.suitability_table = pd.read_sql_query("SELECT * FROM crop_suitability", conn)
        conn.close()

    def score_temperature(self, temp_c: float, crop: str) -> float:
        row = self.suitability_table[self.suitability_table['commodity'].str.lower() == crop.lower()]
        if row.empty:
            return 0.7  # Default fallback

        t_min_abs = row['temp_min_absolute'].values[0]
        t_min_opt = row['temp_min_optimal'].values[0]
        t_max_opt = row['temp_max_optimal'].values[0]
        t_max_abs = row['temp_max_absolute'].values[0]

        if temp_c < t_min_abs or temp_c > t_max_abs:
            return 0.0
        elif t_min_opt <= temp_c <= t_max_opt:
            return 1.0
        elif t_min_abs <= temp_c < t_min_opt:
            return (temp_c - t_min_abs) / (t_min_opt - t_min_abs)
        else:
            return (t_max_abs - temp_c) / (t_max_abs - t_max_opt)

    def evaluate_crop_suitability(self, crop: str, forecast_temps: List[float], forecast_rains: List[float]) -> Dict[str, Any]:
        temp_scores = [self.score_temperature(t, crop) for t in forecast_temps]
        avg_temp_score = float(np.mean(temp_scores)) if temp_scores else 0.7

        # Rain score: check if 14-day cumulative rain creates waterlogging/blight risk
        total_rain = sum(forecast_rains)
        heavy_rain_days = sum(1 for r in forecast_rains if r >= 25.0)
        extreme_heat_days = sum(1 for t in forecast_temps if t >= 36.0)

        # Weather risk penalty
        rain_risk_factor = min(1.0, heavy_rain_days * 0.25 + (total_rain / 150.0) * 0.3)
        heat_risk_factor = min(1.0, extreme_heat_days * 0.25)
        combined_weather_risk = min(10.0, round((rain_risk_factor + heat_risk_factor) * 5.0, 2))

        # Overall agro-climatic score (0 to 1)
        suitability_score = round(max(0.1, avg_temp_score * (1.0 - rain_risk_factor * 0.4)), 3)

        return {
            "suitability_score": suitability_score,
            "avg_temp_score": round(avg_temp_score, 3),
            "weather_risk_index": combined_weather_risk,
            "heavy_rain_days": heavy_rain_days,
            "extreme_heat_days": extreme_heat_days,
            "total_forecast_rain_mm": round(total_rain, 1)
        }


class TOPSIS:
    """
    Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS).
    Handles arbitrary alternatives and criteria with specified benefit/cost directions.
    """
    def __init__(self, decision_matrix: np.ndarray, weights: np.ndarray, directions: List[str]):
        """
        decision_matrix: shape (m, n) for m alternatives and n criteria
        weights: array of length n, will be normalized to sum to 1.0
        directions: list of length n, each either 'benefit' (higher is better) or 'cost' (lower is better)
        """
        self.X = np.array(decision_matrix, dtype=float)
        self.m, self.n = self.X.shape

        weights = np.array(weights, dtype=float)
        if weights.sum() == 0:
            self.weights = np.ones(self.n) / self.n
        else:
            self.weights = weights / weights.sum()

        self.directions = [d.lower() for d in directions]

    def solve(self) -> Tuple[np.ndarray, np.ndarray]:
        # 1. Vector Normalization: r_ij = x_ij / sqrt(sum(x_kj^2))
        col_norms = np.sqrt(np.sum(self.X ** 2, axis=0))
        # Prevent division by zero
        col_norms[col_norms == 0] = 1e-9
        R = self.X / col_norms

        # 2. Weighted Normalized Decision Matrix: V = R * w
        V = R * self.weights

        # 3. Determine Ideal Best (A+) and Ideal Worst (A-)
        v_plus = np.zeros(self.n)
        v_minus = np.zeros(self.n)

        for j in range(self.n):
            if self.directions[j] == 'benefit':
                v_plus[j] = np.max(V[:, j])
                v_minus[j] = np.min(V[:, j])
            else:  # 'cost'
                v_plus[j] = np.min(V[:, j])
                v_minus[j] = np.max(V[:, j])

        # 4. Separation Distances
        S_plus = np.sqrt(np.sum((V - v_plus) ** 2, axis=1))
        S_minus = np.sqrt(np.sum((V - v_minus) ** 2, axis=1))

        # 5. Closeness Coefficient: C_i = S_minus / (S_plus + S_minus)
        total_dist = S_plus + S_minus
        total_dist[total_dist == 0] = 1e-9
        closeness = S_minus / total_dist

        # Rankings: highest closeness is Rank 1
        rankings = np.argsort(-closeness) + 1  # 1-indexed

        return closeness, rankings


class HarvestMCDA:
    """
    Main Multi-Criteria Decision Analysis Engine for Harvest Advisory.
    Executes Mode A (Crop Selection) and Mode B (Sell Timing & Location).
    """
    def __init__(self):
        self.net_calc = NetPriceCalculator()
        self.suit_eval = AgroSuitabilityEvaluator()
        self.conn = get_connection()

    def get_latest_market_metrics(self) -> Dict[str, Dict[str, float]]:
        """Extracts recent price levels and 30-day volatility from SQLite."""
        metrics = {}
        for crop in ["Potato", "Tomato", "Onion"]:
            query = """
            SELECT arrival_date, modal_price 
            FROM prices 
            WHERE commodity = ? AND market = 'Pune'
            ORDER BY arrival_date DESC LIMIT 30;
            """
            df = pd.read_sql_query(query, self.conn, params=(crop,))
            if not df.empty:
                latest_p = float(df['modal_price'].iloc[0])
                volatility = float(df['modal_price'].std() / (df['modal_price'].mean() + 1e-6))
            else:
                latest_p = 1200.0
                volatility = 0.15
            metrics[crop] = {
                "latest_modal_price": latest_p,
                "price_volatility": round(volatility, 3)
            }
        return metrics

    def get_forecast_weather(self, location: str = "Pune", days: int = 14) -> Tuple[List[float], List[float]]:
        """Pulls upcoming weather forecast temperatures and rainfall."""
        query = """
        SELECT temp_mean, precipitation 
        FROM weather 
        WHERE location = ?
        ORDER BY date DESC LIMIT ?;
        """
        df = pd.read_sql_query(query, self.conn, params=(location, days))
        if df.empty:
            return [25.0] * days, [2.0] * days
        temps = df['temp_mean'].dropna().tolist()
        rains = df['precipitation'].fillna(0.0).tolist()
        return temps, rains

    def evaluate_mode_a_crop_selection(
        self,
        weights: Optional[Dict[str, float]] = None,
        farm_location: str = "Junnar",
        dest_mandi: str = "Pune"
    ) -> Dict[str, Any]:
        """
        Mode A: Which Crop to Grow?
        Alternatives: Potato vs. Tomato vs. Onion
        Criteria (5):
          1. Net Farm-Gate Price (Benefit)
          2. Expected Yield (Benefit)
          3. Agro-Climatic Suitability (Benefit)
          4. Price Volatility Risk (Cost)
          5. Weather Risk / Blight Index (Cost)
        """
        if weights is None:
            weights = {
                "net_price": 0.30,
                "expected_yield": 0.25,
                "suitability": 0.20,
                "volatility": 0.15,
                "weather_risk": 0.10
            }

        # Query Economics and Logistics
        df_econ = pd.read_sql_query("SELECT * FROM crop_economics", self.conn).set_index('commodity')
        df_log = pd.read_sql_query("""
            SELECT * FROM logistics_assumptions 
            WHERE from_location = ? AND to_mandi = ?;
        """, self.conn, params=(farm_location, dest_mandi))

        if not df_log.empty:
            dist = float(df_log['distance_km'].iloc[0])
            fr_rate = float(df_log['transport_rate_per_q_km'].iloc[0])
            cess = float(df_log['mandi_cess_percent'].iloc[0])
            comm = float(df_log['middleman_commission_percent'].iloc[0])
            hand = float(df_log['loading_unloading_per_q'].iloc[0])
        else:
            dist, fr_rate, cess, comm, hand = 85.0, 2.5, 1.05, 5.0, 25.0

        market_data = self.get_latest_market_metrics()
        temps, rains = self.get_forecast_weather(farm_location, 14)

        alternatives = ["Potato", "Tomato", "Onion"]
        decision_matrix = []
        detailed_criteria = []

        for crop in alternatives:
            gross_price = market_data[crop]["latest_modal_price"]
            net_res = self.net_calc.calculate(gross_price, dist, fr_rate, cess, comm, hand)
            net_p = net_res["net_farmgate_price"]

            yield_val = float(df_econ.loc[crop, 'avg_yield_q_per_ha'])
            cult_cost = float(df_econ.loc[crop, 'cost_cultivation_per_ha'])

            # Net profit per hectare = Net Price * Yield - Cultivation Cost
            net_profit_ha = net_p * yield_val - cult_cost

            weather_res = self.suit_eval.evaluate_crop_suitability(crop, temps, rains)
            suit_score = weather_res["suitability_score"]
            weather_risk = weather_res["weather_risk_index"]
            volatility = market_data[crop]["price_volatility"]

            # Row criteria vector: [Net Price, Yield, Suitability, Volatility, Weather Risk]
            row = [net_p, yield_val, suit_score, volatility, weather_risk]
            decision_matrix.append(row)

            detailed_criteria.append({
                "commodity": crop,
                "gross_mandi_price": gross_price,
                "net_farmgate_price": net_p,
                "expected_yield_q_ha": yield_val,
                "cultivation_cost_ha": cult_cost,
                "expected_net_profit_ha": round(net_profit_ha, 2),
                "suitability_score": suit_score,
                "price_volatility": volatility,
                "weather_risk_index": weather_risk
            })

        w_vector = [
            weights.get("net_price", 0.30),
            weights.get("expected_yield", 0.25),
            weights.get("suitability", 0.20),
            weights.get("volatility", 0.15),
            weights.get("weather_risk", 0.10)
        ]
        directions = ["benefit", "benefit", "benefit", "cost", "cost"]

        topsis = TOPSIS(np.array(decision_matrix), np.array(w_vector), directions)
        closeness, raw_ranks = topsis.solve()

        # Combine results into sorted leaderboard
        rankings = []
        for i, crop in enumerate(alternatives):
            rankings.append({
                "commodity": crop,
                "topsis_score": round(float(closeness[i]), 4),
                "details": detailed_criteria[i]
            })

        rankings = sorted(rankings, key=lambda x: x["topsis_score"], reverse=True)
        for idx, item in enumerate(rankings):
            item["rank"] = idx + 1

        return {
            "mode": "Crop Selection (Which Crop to Grow?)",
            "farm_location": farm_location,
            "target_mandi": dest_mandi,
            "weights_used": weights,
            "rankings": rankings
        }

    def evaluate_mode_b_sell_timing(
        self,
        commodity: str = "Tomato",
        weights: Optional[Dict[str, float]] = None,
        origin_location: str = "Junnar"
    ) -> Dict[str, Any]:
        """
        Mode B: When or Where to Sell?
        Alternatives for the chosen crop:
          1. Sell Today at Pune APMC
          2. Hold and Sell at +7 Days (Pune APMC)
          3. Hold and Sell at +14 Days (Pune APMC)
          4. Sell Today at Local Mandi (Junnar Narayangaon)
        Criteria (5):
          1. Net Farm-Gate Price (Benefit)
          2. Post-Harvest Yield Realization (Benefit: accounts for weight loss & spoilage)
          3. Market Access Convenience (Benefit)
          4. Price Volatility / Uncertainty (Cost)
          5. Transit & Storage Weather Risk (Cost)
        """
        if weights is None:
            weights = {
                "net_price": 0.40,
                "yield_realization": 0.25,
                "market_convenience": 0.15,
                "volatility": 0.10,
                "weather_risk": 0.10
            }

        market_data = self.get_latest_market_metrics()
        p0 = market_data[commodity]["latest_modal_price"]

        # Fetch forecasted prices from latest models or estimates
        # E.g. using seasonal momentum drift
        p_7d = round(p0 * 1.04, 2)   # E.g. +4% expected in 7d
        p_14d = round(p0 * 1.08, 2)  # E.g. +8% expected in 14d
        p_local = round(p0 * 0.94, 2) # Local mandi typically trades at 4-6% discount

        # Logistics
        # Pune APMC (85 km from Junnar)
        net_today_pune = self.net_calc.calculate(p0, distance_km=85.0)["net_farmgate_price"]
        net_7d_pune = self.net_calc.calculate(p_7d, distance_km=85.0)["net_farmgate_price"]
        net_14d_pune = self.net_calc.calculate(p_14d, distance_km=85.0)["net_farmgate_price"]
        # Junnar Local APMC (15 km from Junnar farm)
        net_today_local = self.net_calc.calculate(p_local, distance_km=15.0)["net_farmgate_price"]

        # Spoilage / shrinkage rates by crop perishability
        # Tomato is highly perishable; Potato and Onion store well
        if commodity.lower() == "tomato":
            yield_factors = [100.0, 93.0, 84.0, 100.0]  # Spoilage at +7d and +14d
            transit_risk = [3.0, 5.0, 7.0, 1.5]
        elif commodity.lower() == "onion":
            yield_factors = [100.0, 98.0, 95.0, 100.0]
            transit_risk = [2.0, 3.5, 5.0, 1.0]
        else:  # Potato
            yield_factors = [100.0, 99.0, 97.0, 100.0]
            transit_risk = [2.0, 3.0, 4.5, 1.0]

        alternatives = [
            "Sell Today (Pune APMC)",
            "Hold & Sell in +7 Days (Pune APMC)",
            "Hold & Sell in +14 Days (Pune APMC)",
            f"Sell Today Locally ({origin_location} Mandi)"
        ]

        # Matrix: [Net Price, Yield Realization %, Convenience Score, Volatility, Weather Risk]
        decision_matrix = [
            [net_today_pune, yield_factors[0], 0.70, 0.10, transit_risk[0]],
            [net_7d_pune, yield_factors[1], 0.70, 0.20, transit_risk[1]],
            [net_14d_pune, yield_factors[2], 0.70, 0.35, transit_risk[2]],
            [net_today_local, yield_factors[3], 0.95, 0.08, transit_risk[3]]
        ]

        w_vector = [
            weights.get("net_price", 0.40),
            weights.get("yield_realization", 0.25),
            weights.get("market_convenience", 0.15),
            weights.get("volatility", 0.10),
            weights.get("weather_risk", 0.10)
        ]
        directions = ["benefit", "benefit", "benefit", "cost", "cost"]

        topsis = TOPSIS(np.array(decision_matrix), np.array(w_vector), directions)
        closeness, _ = topsis.solve()

        rankings = []
        for i, alt in enumerate(alternatives):
            rankings.append({
                "strategy": alt,
                "topsis_score": round(float(closeness[i]), 4),
                "net_price_realization": round(decision_matrix[i][0], 2),
                "yield_retention_pct": decision_matrix[i][1],
                "convenience_score": decision_matrix[i][2],
                "risk_uncertainty": decision_matrix[i][3],
                "weather_spoilage_risk": decision_matrix[i][4]
            })

        rankings = sorted(rankings, key=lambda x: x["topsis_score"], reverse=True)
        for idx, item in enumerate(rankings):
            item["rank"] = idx + 1

        return {
            "mode": f"Sell Timing & Location Optimization for {commodity}",
            "commodity": commodity,
            "weights_used": weights,
            "rankings": rankings
        }

    @classmethod
    def rank_crops(cls, weights: Optional[Dict[str, float]] = None) -> pd.DataFrame:
        """Helper for UI: Mode A Crop Selection Ranking returning a styled DataFrame."""
        engine = cls() if isinstance(cls, type) else cls
        w_mapped = {}
        if weights:
            w_mapped["net_price"] = weights.get("net_realization", weights.get("net_price", 0.30))
            w_mapped["expected_yield"] = weights.get("expected_yield", 0.25)
            w_mapped["suitability"] = weights.get("agro_suitability", weights.get("suitability", 0.20))
            w_mapped["volatility"] = weights.get("price_volatility", weights.get("volatility", 0.15))
            w_mapped["weather_risk"] = weights.get("weather_risk", 0.10)

        eval_res = engine.evaluate_mode_a_crop_selection(weights=w_mapped)
        rows = []
        for r in eval_res["rankings"]:
            d = r["details"]
            rows.append({
                "Rank": r["rank"],
                "Crop": r["commodity"],
                "TOPSIS Score": r["topsis_score"],
                "Net Realization (Rs/q)": d["net_farmgate_price"],
                "Expected Yield (q/ha)": d["expected_yield_q_ha"],
                "Net Profit (Rs/ha)": d["expected_net_profit_ha"],
                "Suitability Score": d["suitability_score"],
                "Volatility Risk": d["price_volatility"],
                "Weather Risk": d["weather_risk_index"]
            })
        return pd.DataFrame(rows)

    @classmethod
    def rank_sell_timing(cls, commodity: str = "Tomato", weights: Optional[Dict[str, float]] = None) -> pd.DataFrame:
        """Helper for UI: Mode B Sell Timing & Market Arbitrage returning a styled DataFrame."""
        engine = cls() if isinstance(cls, type) else cls
        w_mapped = {}
        if weights:
            w_mapped["net_price"] = weights.get("expected_net_price", weights.get("net_price", 0.40))
            w_mapped["yield_realization"] = weights.get("spoilage_risk", weights.get("yield_realization", 0.25))
            w_mapped["market_convenience"] = weights.get("transport_convenience", weights.get("market_convenience", 0.15))
            w_mapped["volatility"] = weights.get("storage_holding_cost", weights.get("volatility", 0.10))
            w_mapped["weather_risk"] = weights.get("weather_risk", 0.10)

        eval_res = engine.evaluate_mode_b_sell_timing(commodity=commodity, weights=w_mapped)
        rows = []
        for r in eval_res["rankings"]:
            rows.append({
                "Rank": r["rank"],
                "Alternative": r["strategy"],
                "TOPSIS Closeness Score": r["topsis_score"],
                "Expected Net Price (Rs/q)": r["net_price_realization"],
                "Yield Retention (%)": f"{r['yield_retention_pct']*100:.1f}%",
                "Convenience Score": r["convenience_score"],
                "Market Volatility": r["risk_uncertainty"],
                "Weather Spoilage Risk": r["weather_spoilage_risk"]
            })
        return pd.DataFrame(rows)

if __name__ == "__main__":
    mcda = HarvestMCDA()
    print("--- Mode A: Which Crop to Grow? ---")
    res_a = mcda.evaluate_mode_a_crop_selection()
    for r in res_a["rankings"]:
        print(f"Rank {r['rank']}: {r['commodity']:<8} | TOPSIS Score: {r['topsis_score']} | Net Profit/ha: Rs {r['details']['expected_net_profit_ha']:,}")

    print("\n--- Mode B: When & Where to Sell? (Tomato) ---")
    res_b = mcda.evaluate_mode_b_sell_timing("Tomato")
    for r in res_b["rankings"]:
        print(f"Rank {r['rank']}: {r['strategy']:<38} | TOPSIS Score: {r['topsis_score']} | Net Price: Rs {r['net_price_realization']}")
