"""
Script to generate an architecture flowchart image for Section 7 of the project report.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def generate_system_architecture_diagram():
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.axis('off')

    # Draw boxes
    boxes = [
        ("Data Foundation & Ingestion\n• Agmarknet APMC (75k records: 2001-2026)\n• Open-Meteo Weather (18k daily records)\n• ICAR Costs & FAO EcoCrop Baselines", 0.05, 0.70, 0.40, 0.22, "#e0f2fe", "#0284c7"),
        ("Feature Engineering Matrix (47 Features)\n• Autoregressive Lags (1, 2, 3, 7, 14, 30)\n• 7/14/30d Rolling Statistics & EWMA\n• Fourier Annual Harmonics (sin/cos)\n• Bioclimatic Stress (GDD, THI Index)", 0.55, 0.70, 0.40, 0.22, "#f0fdf4", "#16a34a"),
        ("Dynamic Ensemble Regressors\n• Random Forest (Variance reduction)\n• XGBoost (Sequential boosting)\n• LightGBM (Multi-horizon speed)\n• Stacking Ensemble (Ridge Meta-model)", 0.05, 0.38, 0.40, 0.22, "#fef3c7", "#d97706"),
        ("Supply-Chain Friction Engine\n• Transit Tariffs (₹1.75/q/km)\n• APMC Market Cess (1.05%)\n• Middleman Commission (4.0%)\n• Weighing & Handling Fee (₹15/q)", 0.55, 0.38, 0.40, 0.22, "#fee2e2", "#dc2626"),
        ("Explainable AI (TreeSHAP)\n• Native C++ Game-Theoretic Attribution\n• Plain-Language Farmer Rationales\n• Anomaly & Supply Shock Detection", 0.05, 0.06, 0.40, 0.22, "#f3e8ff", "#9333ea"),
        ("Dual-Mode TOPSIS MCDA Engine\n• Mode A: Which Crop to Cultivate?\n• Mode B: When & Where to Sell?\n• 5 Stakeholder Risk Sensitivity Profiles", 0.55, 0.06, 0.40, 0.22, "#fce7f3", "#db2777")
    ]

    from matplotlib.patches import FancyBboxPatch
    for title, x, y, w, h, bg, border in boxes:
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015,rounding_size=0.02",
                              facecolor=bg, edgecolor=border, linewidth=2, transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, title, ha="center", va="center", fontsize=9.5, fontweight="bold",
                transform=ax.transAxes, color="#0f172a")

    # Connectors
    arrows = [
        ((0.45, 0.81), (0.55, 0.81)),  # Data to Features
        ((0.75, 0.70), (0.75, 0.60)),  # Features to Logistics
        ((0.25, 0.70), (0.25, 0.60)),  # Data to Ensembles
        ((0.25, 0.38), (0.25, 0.28)),  # Ensembles to XAI
        ((0.45, 0.49), (0.55, 0.49)),  # Price to Friction
        ((0.75, 0.38), (0.75, 0.28)),  # Friction to TOPSIS
        ((0.45, 0.17), (0.55, 0.17)),  # XAI to TOPSIS
    ]

    for p1, p2 in arrows:
        ax.annotate('', xy=p2, xytext=p1, xycoords='axes fraction', textcoords='axes fraction',
                    arrowprops=dict(arrowstyle="->", color="#334155", lw=2, shrinkA=5, shrinkB=5))

    ax.set_title("End-to-End System Architecture: Predictive & Prescriptive Pipeline", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    out_path = FIGURES_DIR / "system_architecture_diagram.png"
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {out_path}")
    return out_path

if __name__ == "__main__":
    generate_system_architecture_diagram()
