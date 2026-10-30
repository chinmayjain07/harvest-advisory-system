"""
Automated PowerPoint Presentation Generator.
Generates the updated 12-slide presentation matching the PCCOE Pioneers Summit theme,
with real numbers, merged redundant slides, and 2 dedicated prototype walkthrough slides.
"""

import sys
import os
from pathlib import Path
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
OUTPUT_PPTX = REPORTS_DIR / "CEP_PRESENTATION_UPDATED.pptx"

# Images
LOGO_PATH = PROJECT_ROOT / "extracted_media" / "word" / "media" / "image1.jpeg"
ARCH_FIG = FIGURES_DIR / "system_architecture_diagram.png"
RRMSE_FIG = FIGURES_DIR / "model_comparison_rrmse.png"
WATERFALL_FIG = FIGURES_DIR / "net_price_waterfall.png"
TOPSIS_FIG = FIGURES_DIR / "topsis_sensitivity_profiles.png"
DASHBOARD_SCREENSHOT = Path(r"C:\Users\Rahul\.gemini\antigravity\brain\176cbfd5-9da1-4173-99d0-67b077068d91\.user_uploaded\media_1793382613917.png")


def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Colors
    NAVY = RGBColor(15, 41, 66)
    BLUE_HEADER = RGBColor(30, 58, 138)
    CARD_BG = RGBColor(241, 245, 249)
    CARD_BORDER = RGBColor(203, 213, 225)
    DARK_TEXT = RGBColor(15, 23, 42)
    GRAY_TEXT = RGBColor(100, 116, 139)
    WHITE = RGBColor(255, 255, 255)
    ACCENT_GREEN = RGBColor(16, 185, 129)
    ACCENT_AMBER = RGBColor(217, 119, 6)

    def add_header(slide, title_text, page_num):
        # PCCOE Logo
        if LOGO_PATH.exists():
            slide.shapes.add_picture(str(LOGO_PATH), Inches(0.5), Inches(0.3), width=Inches(0.9))

        # Title
        txBox = slide.shapes.add_textbox(Inches(1.6), Inches(0.3), Inches(11.2), Inches(0.9))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.name = "Times New Roman"
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = DARK_TEXT

        # Footer
        footerBox = slide.shapes.add_textbox(Inches(0.8), Inches(7.0), Inches(11.7), Inches(0.4))
        ftf = footerBox.text_frame
        p_ft = ftf.paragraphs[0]
        p_ft.text = "CSE (AI&ML) Pioneers Summit 2026"
        p_ft.font.name = "Times New Roman"
        p_ft.font.size = Pt(11)
        p_ft.font.italic = True
        p_ft.font.color.rgb = GRAY_TEXT

        # Page No on right
        p_num = ftf.add_paragraph()
        p_num.text = f"PAGE NO. {page_num}"
        p_num.alignment = PP_ALIGN.RIGHT
        p_num.font.name = "Times New Roman"
        p_num.font.size = Pt(11)
        p_num.font.italic = True
        p_num.font.color.rgb = GRAY_TEXT

    # ==============================================================
    # SLIDE 1: Title Slide
    # ==============================================================
    slide1 = prs.slides.add_slide(blank_layout)

    # Logo
    if LOGO_PATH.exists():
        slide1.shapes.add_picture(str(LOGO_PATH), Inches(0.8), Inches(0.5), width=Inches(1.3))

    tb_inst = slide1.shapes.add_textbox(Inches(2.3), Inches(0.4), Inches(8.7), Inches(1.2))
    tf1 = tb_inst.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "Pimpri Chinchwad Education Trust's\nPimpri Chinchwad College of Engineering\nDepartment of CSE (AI&ML)"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Times New Roman"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = DARK_TEXT

    # CEP Presentation Banner
    tb_cep = slide1.shapes.add_textbox(Inches(1.5), Inches(1.9), Inches(10.3), Inches(0.8))
    p_cep = tb_cep.text_frame.paragraphs[0]
    p_cep.text = "CEP Presentation"
    p_cep.alignment = PP_ALIGN.CENTER
    p_cep.font.name = "Times New Roman"
    p_cep.font.size = Pt(36)
    p_cep.font.bold = True
    p_cep.font.color.rgb = NAVY

    # Project Title
    tb_title = slide1.shapes.add_textbox(Inches(1.0), Inches(2.9), Inches(11.3), Inches(1.5))
    tf_t = tb_title.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = "Research Paper Title: An Intelligent Harvest Advisory and Mandi Price Prediction Framework Using Ensemble Regressors and Multi-Criteria Decision Analysis (MCDA)"
    p_t.alignment = PP_ALIGN.CENTER
    p_t.font.name = "Times New Roman"
    p_t.font.size = Pt(22)
    p_t.font.bold = True
    p_t.font.color.rgb = BLUE_HEADER

    # Authors
    tb_auth = slide1.shapes.add_textbox(Inches(2.5), Inches(4.7), Inches(8.3), Inches(2.2))
    tf_a = tb_auth.text_frame
    authors = [
        "Student Name: Chinmay Jain",
        "Student Name: Prithviraj Sapkal",
        "Student Name: Tanmay Joshi",
        "Guide Name: Prof. Sarika Bartakke"
    ]
    for i, a in enumerate(authors):
        p_a = tf_a.paragraphs[0] if i == 0 else tf_a.add_paragraph()
        p_a.text = a
        p_a.alignment = PP_ALIGN.CENTER
        p_a.font.name = "Times New Roman"
        p_a.font.size = Pt(17)
        p_a.font.bold = True
        p_a.font.color.rgb = DARK_TEXT

    # ==============================================================
    # SLIDE 2: Introduction & Problem Statement
    # ==============================================================
    slide2 = prs.slides.add_slide(blank_layout)
    add_header(slide2, "Introduction & Problem Statement", 1)

    cards = [
        ("Domain Context", "Small farmers decide what to grow, harvest, and sell under severe climatic variability and price uncertainty.\n\nPerishable cash crops like Potato, Tomato, and Onion are most exposed to abrupt market shocks.", Inches(1.5)),
        ("The Core Bottleneck", "Price forecasts are disconnected from farm decisions: conventional systems deliver static prices, fixed risk assumptions, and single-objective alerts.\n\nQuoted wholesale prices ignore transport tariffs, APMC market cess, and intermediary commissions.", Inches(3.2)),
        ("Business / Research Impact", "Bridging predictive ML with prescriptive MCDA enables better crop selection pre-sowing and optimal sell timing at harvest.\n\nReduces information asymmetry and significantly improves realized net farm-gate income for smallholders.", Inches(4.9))
    ]

    for title, text, top_pos in cards:
        # Header block
        hb = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), top_pos, Inches(2.6), Inches(1.4))
        hb.fill.solid()
        hb.fill.fore_color.rgb = NAVY
        hb.line.color.rgb = NAVY
        p = hb.text_frame.paragraphs[0]
        p.text = title
        p.alignment = PP_ALIGN.CENTER
        p.font.name = "Times New Roman"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = WHITE

        # Content block
        cb = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.8), top_pos, Inches(8.5), Inches(1.4))
        cb.fill.solid()
        cb.fill.fore_color.rgb = CARD_BG
        cb.line.color.rgb = CARD_BORDER
        p = cb.text_frame.paragraphs[0]
        p.text = text
        p.font.name = "Times New Roman"
        p.font.size = Pt(13.5)
        p.font.color.rgb = DARK_TEXT

    # ==============================================================
    # SLIDE 3: Objectives & Scope
    # ==============================================================
    slide3 = prs.slides.add_slide(blank_layout)
    add_header(slide3, "Objectives & Scope", 2)

    v_cards = [
        ("Primary Goal", [
            "Integrated harvest advisory and mandi price prediction engine.",
            "Dynamic ensemble ML coupled with TOPSIS multi-criteria decision making.",
            "Transparent pre-sowing crop selection and post-harvest sales advice."
        ], Inches(1.0)),
        ("Key Targets", [
            "Accurate multi-horizon forecasts (7d, 14d, 30d) evaluated by RMSE, MAE, RRMSE.",
            "Explainable AI (TreeSHAP) feature attribution for farmer trust.",
            "Net Farm-Gate Price realization after deducting logistics and mandi costs.",
            "Dual-mode TOPSIS ranking for crop planning and timing arbitrage."
        ], Inches(4.9)),
        ("Scope & Constraints", [
            "Geographic focus: Pune District, Western Maharashtra (Pune & Junnar APMCs).",
            "Target crops: Potato, Tomato, Onion.",
            "Historical APMC data spanning 25 years (2001–2026).",
            "Deployed via Streamlit interactive web portal + REST fallback panel.",
            "Leverages Open-Meteo 14-day weather forecasts."
        ], Inches(8.8))
    ]

    for title, bullets, left_pos in v_cards:
        # Header top
        hb = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, Inches(1.5), Inches(3.5), Inches(0.7))
        hb.fill.solid()
        hb.fill.fore_color.rgb = NAVY
        hb.line.color.rgb = NAVY
        p = hb.text_frame.paragraphs[0]
        p.text = title
        p.alignment = PP_ALIGN.CENTER
        p.font.name = "Times New Roman"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = WHITE

        # Body card
        cb = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, Inches(2.3), Inches(3.5), Inches(4.4))
        cb.fill.solid()
        cb.fill.fore_color.rgb = CARD_BG
        cb.line.color.rgb = CARD_BORDER
        tf = cb.text_frame
        tf.word_wrap = True
        for i, b in enumerate(bullets):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = f"• {b}"
            p.font.name = "Times New Roman"
            p.font.size = Pt(13)
            p.font.color.rgb = DARK_TEXT
            p.space_after = Pt(10)

    # ==============================================================
    # SLIDE 4: Dataset & Preprocessing (Updated with Real Numbers!)
    # ==============================================================
    slide4 = prs.slides.add_slide(blank_layout)
    add_header(slide4, "Dataset & Preprocessing", 3)

    # Left: Dataset Table Card
    hb_d = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.4), Inches(5.3), Inches(0.6))
    hb_d.fill.solid()
    hb_d.fill.fore_color.rgb = NAVY
    p = hb_d.text_frame.paragraphs[0]
    p.text = "Dataset Specification (Updated)"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Times New Roman"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = WHITE

    cb_d = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.6))
    cb_d.fill.solid()
    cb_d.fill.fore_color.rgb = CARD_BG
    cb_d.line.color.rgb = CARD_BORDER
    tf = cb_d.text_frame
    tf.word_wrap = True
    d_rows = [
        ("Source:", "APMC Records (Agmarknet) + Open-Meteo Weather Archive"),
        ("Period:", "2001–2026 (25 Continuous Years)"),
        ("Volume:", "75,890 Verified Mandi Records (Potato: 20k, Tomato: 26.7k, Onion: 29.1k)"),
        ("Weather:", "18,890 Daily Weather Days + 14-Day Forecasts"),
        ("Crops:", "Solanum tuberosum, Solanum lycopersicum, Allium cepa"),
        ("Data Split:", "Chronological Out-of-Sample: Train pre-2025 | Test: Last 12 months")
    ]
    for i, (k, v) in enumerate(d_rows):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"{k} {v}"
        p.font.name = "Times New Roman"
        p.font.size = Pt(12)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(8)

    # Right: Preprocessing & Feature Matrix Card
    hb_p = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.4), Inches(5.5), Inches(0.6))
    hb_p.fill.solid()
    hb_p.fill.fore_color.rgb = NAVY
    p = hb_p.text_frame.paragraphs[0]
    p.text = "Preprocessing & Feature Engineering"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Times New Roman"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = WHITE

    cb_p = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(2.1), Inches(5.5), Inches(4.6))
    cb_p.fill.solid()
    cb_p.fill.fore_color.rgb = CARD_BG
    cb_p.line.color.rgb = CARD_BORDER
    tf_p = cb_p.text_frame
    tf_p.word_wrap = True
    p_bullets = [
        "Data Cleansing: Anomaly filtering, non-trading Sunday handling via forward-fill with rolling 14-day median fallback.",
        "47 Engineered Predictors: Autoregressive price lags (1, 2, 3, 7, 14, 21, 30 days) and rolling volatility windows.",
        "Deterministic Seasonality: Fourier harmonic transforms (sin/cos cycles) capturing annual monsoon harvest flushes.",
        "Bioclimatic Indicators: Growing Degree Days (GDD), Temperature-Humidity Index (THI), and 14-day cumulative rainfall.",
        "Temporal Integrity: Strict chronological validation preventing lookahead bias or future data leakage."
    ]
    for i, b in enumerate(p_bullets):
        p = tf_p.paragraphs[0] if i == 0 else tf_p.add_paragraph()
        p.text = f"• {b}"
        p.font.name = "Times New Roman"
        p.font.size = Pt(12)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(8)

    # ==============================================================
    # SLIDE 5: Dataset Snapshot
    # ==============================================================
    slide5 = prs.slides.add_slide(blank_layout)
    add_header(slide5, "Dataset Snapshot & Data Schema", 4)

    # Table on Left
    table_shape = slide5.shapes.add_table(rows=7, cols=5, left=Inches(0.8), top=Inches(1.5), width=Inches(8.2), height=Inches(4.8))
    table = table_shape.table
    headers = ["Arrival Date", "Commodity", "Market", "Min / Max (₹/q)", "Modal Price (Target)"]
    for c_idx, h in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        for p in cell.text_frame.paragraphs:
            p.font.name = "Times New Roman"
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = WHITE

    sample_rows = [
        ("08/01/2025", "Potato", "Junnar", "1000 / 1300", "₹1,100 / q"),
        ("18/01/2025", "Potato", "Junnar", "700 / 1600", "₹1,300 / q"),
        ("22/02/2025", "Potato", "Pune", "400 / 1200", "₹800 / q"),
        ("15/03/2025", "Tomato", "Junnar", "500 / 1100", "₹900 / q"),
        ("29/03/2025", "Onion", "Pune", "800 / 1200", "₹1,000 / q"),
        ("18/10/2025", "Onion", "Junnar", "1200 / 2600", "₹2,200 / q")
    ]
    for r_idx, row in enumerate(sample_rows):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 1 else WHITE
            for p in cell.text_frame.paragraphs:
                p.font.name = "Times New Roman"
                p.font.size = Pt(10.5)
                p.font.color.rgb = DARK_TEXT

    # Info card on Right
    cb_info = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.3), Inches(1.5), Inches(3.2), Inches(4.8))
    cb_info.fill.solid()
    cb_info.fill.fore_color.rgb = CARD_BG
    cb_info.line.color.rgb = CARD_BORDER
    tf = cb_info.text_frame
    tf.word_wrap = True
    info_lines = [
        "Core Target Variable:",
        "Modal Price represents prevailing daily transaction price for wholesale lots.",
        "Key Fields:",
        "Date, Commodity, Market, Variety, Min Price, Max Price, Modal Price.",
        "Temporal Structure:",
        "Raw rows arrive unordered across APMCs; pipeline indexes chronologically to enforce causality.",
        "Integrated SQLite Database:",
        "Stores 75,890 records with ACID compliance and instant indexed retrieval."
    ]
    for i, line in enumerate(info_lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.name = "Times New Roman"
        p.font.size = Pt(11.5)
        if i % 2 == 0:
            p.font.bold = True
            p.font.color.rgb = BLUE_HEADER
        else:
            p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(6)

    # ==============================================================
    # SLIDE 6: Literature Survey
    # ==============================================================
    slide6 = prs.slides.add_slide(blank_layout)
    add_header(slide6, "Literature Survey & Benchmark Insights", 5)

    t_survey = slide6.shapes.add_table(rows=6, cols=5, left=Inches(0.8), top=Inches(1.4), width=Inches(11.7), height=Inches(5.0))
    ts = t_survey.table
    col_w = [Inches(2.1), Inches(2.3), Inches(2.4), Inches(2.1), Inches(2.8)]
    for i, w in enumerate(col_w):
        ts.columns[i].width = w

    surv_headers = ["Paper (Year)", "What They Did", "What We Learnt", "Limitation", "How It Benefits Us"]
    for c_idx, h in enumerate(surv_headers):
        cell = ts.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        for p in cell.text_frame.paragraphs:
            p.font.name = "Times New Roman"
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = WHITE

    surv_rows = [
        ("Qureshi et al., 2026\nEnsemble Learning", "Reviewed Bagging, Boosting, and Stacking architectures.", "Combining learners cuts variance and corrects residual errors.", "General ML review; not agricultural price specific.", "Theoretical basis for our RF, boosting, and Stacking layer."),
        ("Pahmeyer et al., 2021\n'Fruchtfolge' DSS", "Crop-choice decision support under spatial constraints.", "Farm planning requires multi-criteria data, not price alone.", "Static decision model; not coupled with dynamic price forecasts.", "Supports coupling price predictions with agro-climatic suitability."),
        ("Bergquist & Dinerstein, 2020\nKenya Markets", "Field experiment on market competition and trader entry.", "Wholesale price does not equal farm-gate income.", "Kenyan context; no predictive machine learning forecasting.", "Directly motivates our Net Realized Farm-Gate Price adjustment."),
        ("Assouto et al., 2020\nBenin Farmers", "Investigated price and yield production uncertainty.", "Price risk and limited hedging shape farmer decisions.", "Single case study; no dynamic advisory tool.", "Motivates joint market, weather, and economic multi-criteria."),
        ("Mitra et al., 2018\nIndian Potato Farmers", "Experiment on middleman margins & information asymmetry.", "Farmers receive significantly less than wholesale rates.", "Potato only; purely retrospective econometric study.", "Supports transport, cess, handling, and commission deductions.")
    ]
    for r_idx, row in enumerate(surv_rows):
        for c_idx, val in enumerate(row):
            cell = ts.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 1 else WHITE
            for p in cell.text_frame.paragraphs:
                p.font.name = "Times New Roman"
                p.font.size = Pt(10)
                p.font.color.rgb = DARK_TEXT

    # ==============================================================
    # SLIDE 7: Proposed Solution & Multi-Criteria Innovation (Merged Old 7 & 8)
    # ==============================================================
    slide7 = prs.slides.add_slide(blank_layout)
    add_header(slide7, "Proposed Solution & Multi-Criteria Innovation (MCDA)", 6)

    # 4 Pillar Boxes Across Top
    pillars = [
        ("Dynamic Ensemble\nPrediction", "RF, XGBoost, LightGBM, and Stacking retrained dynamically as new market data arrives.", Inches(0.8)),
        ("Supply-Chain\nAdjustment", "Net Farm-Gate Price = Mandi Price minus transport, cess, commission, and handling fees.", Inches(3.8)),
        ("TOPSIS Multi-Criteria\nRanking", "Ranks alternatives on price, weather risk, yield, and suitability—not price alone.", Inches(6.8)),
        ("Explainable AI\nby Design", "TreeSHAP game-theoretic attributions explain every prediction and ranking in plain language.", Inches(9.8))
    ]
    for title, text, left_pos in pillars:
        box = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, Inches(1.4), Inches(2.7), Inches(2.2))
        box.fill.solid()
        box.fill.fore_color.rgb = CARD_BG
        box.line.color.rgb = BLUE_HEADER
        box.line.width = Pt(1.5)
        tf = box.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.name = "Times New Roman"
        p0.font.size = Pt(13)
        p0.font.bold = True
        p0.font.color.rgb = BLUE_HEADER
        p0.space_after = Pt(4)
        p1 = tf.add_paragraph()
        p1.text = text
        p1.font.name = "Times New Roman"
        p1.font.size = Pt(10.5)
        p1.font.color.rgb = DARK_TEXT

    # Bottom Two Comparison Cards
    b_left = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(3.9), Inches(5.7), Inches(2.8))
    b_left.fill.solid()
    b_left.fill.fore_color.rgb = CARD_BG
    b_left.line.color.rgb = CARD_BORDER
    tf_l = b_left.text_frame
    tf_l.word_wrap = True
    p = tf_l.paragraphs[0]
    p.text = "How TOPSIS MCDA Works"
    p.font.name = "Times New Roman"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.space_after = Pt(6)
    t_steps = [
        "1. Decision Matrix: Evaluates candidate crops across 5 heterogeneous criteria.",
        "2. Normalization: Vector normalization puts benefit and cost criteria on comparable scale.",
        "3. Ideal & Negative-Ideal: Computes Euclidean distances (S_i+, S_i-) to best & worst points.",
        "4. Closeness Ranking (C_i* in [0, 1]): Recommends the alternative closest to ideal."
    ]
    for step in t_steps:
        p = tf_l.add_paragraph()
        p.text = step
        p.font.name = "Times New Roman"
        p.font.size = Pt(11.5)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(3)

    b_right = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(3.9), Inches(5.7), Inches(2.8))
    b_right.fill.solid()
    b_right.fill.fore_color.rgb = CARD_BG
    b_right.line.color.rgb = CARD_BORDER
    tf_r = b_right.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "Why It Sets Our Framework Apart"
    p.font.name = "Times New Roman"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.space_after = Pt(6)
    diff_points = [
        "Highest Price ≠ Best Crop: A crop with high gross price but 40% disease risk or high input cost is penalized.",
        "Most Tools Stop at Price: We convert raw predictions into prescriptive farm actions.",
        "Solves the Transit Illusion: Accounts for ₹1.75/km freight so farmers avoid uneconomic central market trips.",
        "Dual-Mode Utility: Solves Mode A (What to sow?) and Mode B (When & where to sell?)."
    ]
    for d in diff_points:
        p = tf_r.add_paragraph()
        p.text = f"• {d}"
        p.font.name = "Times New Roman"
        p.font.size = Pt(11.5)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(3)

    # ==============================================================
    # SLIDE 8: System Architecture & Advisory Pipeline
    # ==============================================================
    slide8 = prs.slides.add_slide(blank_layout)
    add_header(slide8, "System Architecture & End-to-End Pipeline", 7)

    if ARCH_FIG.exists():
        slide8.shapes.add_picture(str(ARCH_FIG), Inches(1.5), Inches(1.4), width=Inches(10.3))
    else:
        # Fallback card
        tb = slide8.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.3), Inches(4.0))
        tb.text_frame.text = "Architecture Diagram: Data Ingestion -> Feature Matrix -> Ensembles -> Logistics -> TOPSIS MCDA"

    # ==============================================================
    # SLIDE 9: Methodology & Multi-Horizon Benchmarking Results (Merged Old 10 & 11)
    # ==============================================================
    slide9 = prs.slides.add_slide(blank_layout)
    add_header(slide9, "Methodology & Multi-Horizon Benchmarking Results", 8)

    # Left: Empirical Model Results Table
    t_perf = slide9.shapes.add_table(rows=7, cols=5, left=Inches(0.6), top=Inches(1.4), width=Inches(7.2), height=Inches(5.0))
    tp = t_perf.table
    col_wp = [Inches(1.2), Inches(1.0), Inches(1.8), Inches(1.5), Inches(1.7)]
    for i, w in enumerate(col_wp):
        tp.columns[i].width = w

    perf_headers = ["Crop", "Horizon", "Best Model", "RMSE (₹/q)", "RRMSE vs Naive"]
    for c_idx, h in enumerate(perf_headers):
        cell = tp.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        for p in cell.text_frame.paragraphs:
            p.font.name = "Times New Roman"
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = WHITE

    perf_data = [
        ("Onion", "7-Day", "LightGBM ⭐", "468.30", "0.7229 (+27.7%)"),
        ("Onion", "14-Day", "LightGBM ⭐", "483.86", "0.7324 (+26.8%)"),
        ("Onion", "30-Day", "LightGBM ⭐", "564.10", "0.8236 (+17.6%)"),
        ("Potato", "14-Day", "XGBoost ⭐", "171.13", "0.8900 (+11.0%)"),
        ("Potato", "30-Day", "LightGBM ⭐", "194.46", "0.7756 (+22.4%)"),
        ("Tomato", "30-Day", "Stacking ⭐", "587.01", "0.8466 (+15.3%)")
    ]
    for r_idx, row in enumerate(perf_data):
        for c_idx, val in enumerate(row):
            cell = tp.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 1 else WHITE
            for p in cell.text_frame.paragraphs:
                p.font.name = "Times New Roman"
                p.font.size = Pt(10.5)
                p.font.color.rgb = DARK_TEXT

    # Right: Analytical Insights
    cb_an = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.1), Inches(1.4), Inches(4.6), Inches(5.0))
    cb_an.fill.solid()
    cb_an.fill.fore_color.rgb = CARD_BG
    cb_an.line.color.rgb = CARD_BORDER
    tf = cb_an.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "When Do Ensembles Beat Naive?"
    p.font.name = "Times New Roman"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.space_after = Pt(8)

    insights = [
        "Multi-Week Turning Points (14d & 30d): Naive persistence (y_{t+h} = y_t) fails during harvest gluts. Tree ensembles cut error by 22.4% (Potato 30d) and 26.8% (Onion 14d) using Fourier harmonics and EWMA momentum.",
        "Speculative Spikes (Onion): Onion exhibits extreme policy and arrival volatility; LightGBM beats naive baseline even at 7 days by 27.7%.",
        "Short-Term Inertia Regime (7d Potato/Tomato): High price autocorrelation (>0.92) makes yesterday's price hard to beat over 24-48 hours (RRMSE ~0.97).",
        "Stacking Meta-Learner: Combines complementary regressors using Ridge meta-model, preventing overfitting during volatile tomato swings."
    ]
    for ins in insights:
        p = tf.add_paragraph()
        p.text = f"• {ins}"
        p.font.name = "Times New Roman"
        p.font.size = Pt(11)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(6)

    # ==============================================================
    # SLIDE 10: Prototype Part 1: Resources & Net Farm-Gate Price Engine (NEW!)
    # ==============================================================
    slide10 = prs.slides.add_slide(blank_layout)
    add_header(slide10, "Prototype Implementation: Resources & Farm-Gate Price Engine", 9)

    # Left: Resources & Architecture Box
    cb_res = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.4), Inches(5.6), Inches(5.2))
    cb_res.fill.solid()
    cb_res.fill.fore_color.rgb = CARD_BG
    cb_res.line.color.rgb = CARD_BORDER
    tf = cb_res.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "Prototype Resources & Pipeline Architecture"
    p.font.name = "Times New Roman"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.space_after = Pt(6)

    res_points = [
        ("Tech Stack:", "Python 3.14, Streamlit, Plotly, Scikit-learn, XGBoost, LightGBM, SQLite3."),
        ("Live Data Ingestion:", "Real-time daily sync with Agmarknet APMC APIs + Open-Meteo weather."),
        ("Historical Replay Simulator:", "Allows examiners to step forward in time to simulate market dynamics."),
        ("How Price Forecasts are Generated:", "47 engineered features feed pre-trained multi-horizon tree ensembles generating 7d, 14d, and 30d modal projections with confidence bounds."),
        ("Zero-Dependency Server:", "Fallback native Python HTTP server on port 8000 for low-resource devices.")
    ]
    for k, v in res_points:
        p = tf.add_paragraph()
        p.text = f"{k} {v}"
        p.font.name = "Times New Roman"
        p.font.size = Pt(11.5)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(6)

    # Right: Waterfall Diagram or Screenshot
    if WATERFALL_FIG.exists():
        slide10.shapes.add_picture(str(WATERFALL_FIG), Inches(6.8), Inches(1.4), width=Inches(5.7))

    # ==============================================================
    # SLIDE 11: Prototype Part 2: Interactive TOPSIS Decision Hub & 3 Case Studies (NEW!)
    # ==============================================================
    slide11 = prs.slides.add_slide(blank_layout)
    add_header(slide11, "Prototype Implementation: TOPSIS Decision Hub & Case Studies", 10)

    # Left: Prototype Screenshot or MCDA formulation
    if DASHBOARD_SCREENSHOT.exists():
        slide11.shapes.add_picture(str(DASHBOARD_SCREENSHOT), Inches(0.6), Inches(1.4), width=Inches(5.8))

    # Right: 3 Real-World Case Studies Table
    t_cases = slide11.shapes.add_table(rows=4, cols=4, left=Inches(6.6), top=Inches(1.4), width=Inches(6.1), height=Inches(3.2))
    tc = t_cases.table
    col_wc = [Inches(1.8), Inches(1.3), Inches(1.4), Inches(1.6)]
    for i, w in enumerate(col_wc):
        tc.columns[i].width = w

    case_headers = ["Tactical Case", "Naive Action", "System Action", "Net Financial Gain"]
    for c_idx, h in enumerate(case_headers):
        cell = tc.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        for p in cell.text_frame.paragraphs:
            p.font.name = "Times New Roman"
            p.font.size = Pt(10)
            p.font.bold = True
            p.font.color.rgb = WHITE

    case_rows = [
        ("Tomato Glut\n(Falling Trend)", "Hold 14d & ship to Pune\n(₹70,740)", "Sell locally today at Junnar\n(₹1,19,622)", "+₹48,881 (+69.1%)\nAvoids 16% decay"),
        ("Onion Shortage\n(Rising Trend)", "Spot sale today at Junnar\n(₹2,07,590)", "14d chawl storage & Pune haul\n(₹2,47,402)", "+₹39,812 (+19.2%)\nCaptures ₹650/q rise"),
        ("Potato Rain Threat\n(75mm Rain Shock)", "Delay harvest in rain\n(₹40,630)", "Pre-rain 48h harvest sprint\n(₹1,03,420)", "+₹62,790 (+154.6%)\nPrevents 35% rot")
    ]
    for r_idx, row in enumerate(case_rows):
        for c_idx, val in enumerate(row):
            cell = tc.cell(r_idx + 1, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 1 else WHITE
            for p in cell.text_frame.paragraphs:
                p.font.name = "Times New Roman"
                p.font.size = Pt(9.5)
                p.font.color.rgb = DARK_TEXT

    # Bottom summary box on right
    cb_bot = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.6), Inches(4.8), Inches(6.1), Inches(1.8))
    cb_bot.fill.solid()
    cb_bot.fill.fore_color.rgb = CARD_BG
    cb_bot.line.color.rgb = CARD_BORDER
    tf_b = cb_bot.text_frame
    tf_b.word_wrap = True
    p = tf_b.paragraphs[0]
    p.text = "How TOPSIS Solves the Farmer's Decision:"
    p.font.name = "Times New Roman"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = BLUE_HEADER
    p.space_after = Pt(2)

    p1 = tf_b.add_paragraph()
    p1.text = "• Mode A (Pre-Sowing): Onion ranks #1 (₹2.71L/ha net profit) over tomato across 4 of 5 risk profiles.\n• Mode B (Harvest Timing): For tomato, selling locally today beats distant shipping due to 7% weekly rot."
    p1.font.name = "Times New Roman"
    p1.font.size = Pt(10.5)
    p1.font.color.rgb = DARK_TEXT

    # ==============================================================
    # SLIDE 12: Future Scope & References (Merged Final Slide)
    # ==============================================================
    slide12 = prs.slides.add_slide(blank_layout)
    add_header(slide12, "Future Scope & Key References", 11)

    # Left: Future Scope (3 Pillars)
    f_cards = [
        ("Model Enhancements", "• Expand to more crops (Garlic, Ginger, Cabbage)\n• Soil moisture & disease risk integration\n• IoT field sensor telemetry", Inches(0.8)),
        ("System Scaling", "• Spatial scaling across 36 Maharashtra districts\n• National e-NAM marketplace integration\n• Low-bandwidth SMS/WhatsApp advisory bot", Inches(3.8)),
        ("Research Vision", "• Satellite remote sensing + DSSAT crop models\n• LLM/NLP extraction of policy & export shocks\n• Real-time participatory farmer feedback in MCDA", Inches(6.8))
    ]
    for title, text, left_pos in f_cards:
        box = slide12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, Inches(1.4), Inches(2.7), Inches(2.2))
        box.fill.solid()
        box.fill.fore_color.rgb = CARD_BG
        box.line.color.rgb = BLUE_HEADER
        box.line.width = Pt(1.5)
        tf = box.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.name = "Times New Roman"
        p0.font.size = Pt(13)
        p0.font.bold = True
        p0.font.color.rgb = BLUE_HEADER
        p0.space_after = Pt(4)
        p1 = tf.add_paragraph()
        p1.text = text
        p1.font.name = "Times New Roman"
        p1.font.size = Pt(10)
        p1.font.color.rgb = DARK_TEXT

    # Live Demo Banner on Right
    b_demo = slide12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.8), Inches(1.4), Inches(2.7), Inches(2.2))
    b_demo.fill.solid()
    b_demo.fill.fore_color.rgb = NAVY
    tf_d = b_demo.text_frame
    tf_d.word_wrap = True
    p = tf_d.paragraphs[0]
    p.text = "Live Prototype Demo"
    p.font.name = "Times New Roman"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.space_after = Pt(6)
    p1 = tf_d.add_paragraph()
    p1.text = "Web Portal:\nhttp://localhost:8501\n\nGitHub Repo:\ngithub.com/chinmayjain07/\nharvest-advisory-system"
    p1.font.name = "Times New Roman"
    p1.font.size = Pt(11)
    p1.font.color.rgb = RGBColor(52, 211, 153)

    # Bottom: References Box
    cb_ref = slide12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(3.9), Inches(11.7), Inches(2.8))
    cb_ref.fill.solid()
    cb_ref.fill.fore_color.rgb = CARD_BG
    cb_ref.line.color.rgb = CARD_BORDER
    tf_r = cb_ref.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "Key Academic References"
    p.font.name = "Times New Roman"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.space_after = Pt(4)

    refs_text = [
        "[1] H. Qureshi et al., 'Ensemble learning techniques: Bagging, boosting, and stacking,' arXiv preprint, 2026.",
        "[2] L. F. Bergquist & M. Dinerstein, 'Competition and entry in agricultural markets: Evidence from Kenya,' Am. Econ. Rev., 2020.",
        "[3] S. Mitra et al., 'Asymmetric information and middleman margins: An experiment with Indian potato farmers,' Rev. Econ. Stat., 2018.",
        "[4] C. Pahmeyer et al., '“Fruchtfolge”: A crop rotation decision support system,' Comput. Electron. Agric., 2021.",
        "[5] S. L. Gebre et al., 'Multi-criteria decision making methods to address rural land allocation,' Int. Soil Water Conserv. Res., 2021."
    ]
    for r in refs_text:
        p = tf_r.add_paragraph()
        p.text = r
        p.font.name = "Times New Roman"
        p.font.size = Pt(10)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(2)

    prs.save(str(OUTPUT_PPTX))
    print(f"SUCCESS: Generated updated presentation deck: {OUTPUT_PPTX}")
    return OUTPUT_PPTX

if __name__ == "__main__":
    create_deck()
