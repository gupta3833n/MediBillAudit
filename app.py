"""
MediBill Audit — AI-Powered Hospital Bill Checker for Patients
AICA (AI for CA) Level 2 Capstone Project

Run with:
    streamlit run app.py
"""

import io
import json
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from analyzer import analyze_bill, get_category_summary
from utils.demo_data import DEMO_BILL_ITEMS, DEMO_PATIENT

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MediBill Audit",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "MediBill Audit — AICA Capstone Project\nAI-powered hospital bill checker for patients.",
    },
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] { background: #F8FAFF; }
[data-testid="stSidebar"] { background: #0D47A1; color: white; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label { color: white !important; }

/* ── Hero banner ── */
.hero {
    background: linear-gradient(135deg, #1565C0 0%, #0D47A1 60%, #01579B 100%);
    color: white;
    padding: 32px 28px;
    border-radius: 12px;
    margin-bottom: 24px;
    text-align: center;
}
.hero h1 { font-size: 2.6rem; margin-bottom: 6px; font-weight: 800; }
.hero p  { font-size: 1.1rem; opacity: 0.9; margin-bottom: 0; }
.hero .badge {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.35);
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    margin-top: 10px;
}

/* ── Metric cards ── */
.metric-card {
    background: white;
    border-radius: 10px;
    padding: 20px 16px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-top: 4px solid #1565C0;
}
.metric-card .value { font-size: 1.9rem; font-weight: 800; }
.metric-card .label { font-size: 0.83rem; color: #757575; margin-top: 4px; }
.card-red   { border-top-color: #C62828 !important; }
.card-green { border-top-color: #2E7D32 !important; }
.card-orange{ border-top-color: #E65100 !important; }
.card-blue  { border-top-color: #1565C0 !important; }

/* ── Flag badges ── */
.flag-red    { background:#FFEBEE; color:#C62828; padding:3px 8px; border-radius:4px; font-weight:700; font-size:0.8rem; white-space:nowrap; }
.flag-orange { background:#FFF3E0; color:#E65100; padding:3px 8px; border-radius:4px; font-weight:700; font-size:0.8rem; white-space:nowrap; }
.flag-yellow { background:#FFF8E1; color:#F57F17; padding:3px 8px; border-radius:4px; font-weight:700; font-size:0.8rem; white-space:nowrap; }
.flag-green  { background:#E8F5E9; color:#2E7D32; padding:3px 8px; border-radius:4px; font-weight:700; font-size:0.8rem; white-space:nowrap; }
.flag-grey   { background:#F5F5F5; color:#616161; padding:3px 8px; border-radius:4px; font-weight:700; font-size:0.8rem; white-space:nowrap; }
.flag-blue   { background:#E3F2FD; color:#1565C0; padding:3px 8px; border-radius:4px; font-weight:700; font-size:0.8rem; white-space:nowrap; }

/* ── How it works ── */
.step-card {
    background: white;
    border-radius: 10px;
    padding: 18px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.07);
    text-align: center;
    height: 100%;
}
.step-number {
    width: 40px; height: 40px;
    background: #1565C0; color: white;
    border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 1.2rem; font-weight: 800;
    margin-bottom: 10px;
}
.step-card h4 { color: #0D47A1; margin-bottom: 6px; font-size: 1rem; }
.step-card p  { color: #616161; font-size: 0.87rem; margin:0; }

/* ── Result table ── */
.result-table-wrap { border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.07); }
.result-table-wrap table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
.result-table-wrap th {
    background: #0D47A1; color: white;
    padding: 10px 12px; text-align: left;
    font-weight: 600; letter-spacing: 0.3px;
}
.result-table-wrap td { padding: 9px 12px; border-bottom: 1px solid #E0E0E0; vertical-align: middle; }
.result-table-wrap tr:hover td { background: #F5F5F5; }
.row-red    td { background: #FFEBEE; }
.row-orange td { background: #FFF3E0; }
.row-yellow td { background: #FFF8E1; }
.row-green  td { background: #F1F8E9; }

/* ── Score ring ── */
.score-container { text-align:center; padding:10px; }
.score-label { font-size:0.9rem; color:#757575; margin-top:4px; }

/* ── Info box ── */
.info-box {
    background:#E3F2FD; border-left: 4px solid #1565C0;
    border-radius:0 8px 8px 0; padding: 12px 16px;
    margin-bottom: 14px; font-size: 0.9rem;
}
.warn-box {
    background:#FFF3E0; border-left: 4px solid #E65100;
    border-radius:0 8px 8px 0; padding: 12px 16px;
    margin-bottom: 14px; font-size: 0.9rem;
}
.success-box {
    background:#E8F5E9; border-left: 4px solid #2E7D32;
    border-radius:0 8px 8px 0; padding: 12px 16px;
    margin-bottom: 14px; font-size: 0.9rem;
}

/* ── Disclaimer ── */
.disclaimer {
    background: #FAFAFA;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 14px;
    font-size: 0.8rem;
    color: #9E9E9E;
    margin-top: 24px;
}

/* Hide Streamlit default elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

FLAG_HTML = {
    "MAJOR OVERCHARGE": '<span class="flag-red">🔴 MAJOR OVERCHARGE</span>',
    "OVERCHARGED":      '<span class="flag-red">🔴 OVERCHARGED</span>',
    "SLIGHTLY HIGH":    '<span class="flag-yellow">🟡 SLIGHTLY HIGH</span>',
    "FAIR":             '<span class="flag-green">🟢 FAIR</span>',
    "BELOW BENCHMARK":  '<span class="flag-blue">🔵 BELOW BENCHMARK</span>',
    "SUSPICIOUS":       '<span class="flag-orange">🟠 SUSPICIOUS</span>',
    "UNKNOWN":          '<span class="flag-grey">⚪ UNMATCHED</span>',
}

ROW_CLASS = {
    "MAJOR OVERCHARGE": "row-red",
    "OVERCHARGED":      "row-red",
    "SLIGHTLY HIGH":    "row-yellow",
    "FAIR":             "row-green",
    "SUSPICIOUS":       "row-orange",
    "BELOW BENCHMARK":  "",
    "UNKNOWN":          "",
}


def _fmt_inr(amount: float) -> str:
    """Format number as Indian Rupees with commas."""
    return f"₹{amount:,.0f}"


def _score_color(score: int) -> str:
    if score >= 75:
        return "#2E7D32"
    if score >= 50:
        return "#F57F17"
    return "#C62828"


def _score_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 50:
        return "Fair"
    if score >= 35:
        return "Poor"
    return "Very Poor"


def make_gauge(score: int) -> go.Figure:
    color = _score_color(score)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            number={"suffix": "/100", "font": {"size": 36, "color": color}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#BDBDBD"},
                "bar": {"color": color, "thickness": 0.35},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "#FFCDD2"},
                    {"range": [40, 65], "color": "#FFF9C4"},
                    {"range": [65, 100], "color": "#C8E6C9"},
                ],
            },
        )
    )
    fig.update_layout(
        height=230,
        margin=dict(t=20, b=10, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def make_overcharge_chart(category_summary: list[dict]) -> go.Figure:
    cats = [c["category"] for c in category_summary if c["overcharge"] > 0]
    vals = [c["overcharge"] for c in category_summary if c["overcharge"] > 0]

    if not cats:
        return None

    colors_list = []
    for v, c in zip(vals, cats):
        if v > 20000:
            colors_list.append("#C62828")
        elif v > 5000:
            colors_list.append("#E65100")
        else:
            colors_list.append("#F57F17")

    fig = go.Figure(
        go.Bar(
            x=cats,
            y=vals,
            marker_color=colors_list,
            text=[f"₹{v:,.0f}" for v in vals],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Overcharge Amount by Category (₹)",
        xaxis_title="",
        yaxis_title="Overcharge (₹)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FAFAFA",
        height=340,
        margin=dict(t=40, b=60, l=60, r=20),
        font=dict(size=12),
    )
    fig.update_yaxes(gridcolor="#E0E0E0")
    return fig


def make_bill_breakdown_chart(summary: dict) -> go.Figure:
    labels = ["Fair Amount", "Overcharge"]
    values = [
        max(0, summary["total_fair"]),
        max(0, summary["potential_savings"]),
    ]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            marker_colors=["#2E7D32", "#C62828"],
            hole=0.55,
            textinfo="label+percent",
            textfont_size=13,
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        height=260,
        margin=dict(t=20, b=20, l=10, r=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    return fig


def render_results_table(results: list[dict]) -> None:
    """Render a colour-coded HTML table of bill items."""
    rows = []
    for r in results:
        flag = r.get("flag", "UNKNOWN").upper()
        row_cls = ROW_CLASS.get(flag, "")
        flag_html = FLAG_HTML.get(flag, f'<span class="flag-grey">{flag}</span>')

        bench = (
            f"₹{r['benchmark_min']:,.0f}–₹{r['benchmark_max']:,.0f}"
            if r.get("benchmark_min") is not None
            else "—"
        )
        var = (
            f"{r['variance_pct']:+.0f}%"
            if r.get("variance_pct") is not None
            else "—"
        )
        qty = f"{r.get('quantity',1):.0f}"
        unit_rate = _fmt_inr(r.get("unit_rate", r.get("amount", 0)))
        amount = _fmt_inr(r.get("amount", 0))
        fair = _fmt_inr(r.get("fair_amount", r.get("amount", 0)))

        rows.append(
            f'<tr class="{row_cls}">'
            f"<td><b>{r.get('name','')}</b></td>"
            f"<td>{r.get('category','')}</td>"
            f"<td style='text-align:center'>{qty}</td>"
            f"<td style='text-align:right'>{unit_rate}</td>"
            f"<td style='text-align:right'>{bench}</td>"
            f"<td style='text-align:center'>{var}</td>"
            f"<td style='text-align:right'><b>{amount}</b></td>"
            f"<td style='text-align:right'>{fair}</td>"
            f"<td style='text-align:center'>{flag_html}</td>"
            f"</tr>"
        )

    html = f"""
<div class="result-table-wrap">
<table>
<thead>
<tr>
  <th>Item Description</th>
  <th>Category</th>
  <th style="text-align:center">Qty</th>
  <th style="text-align:right">Billed Rate</th>
  <th style="text-align:right">Benchmark Range</th>
  <th style="text-align:center">Variance</th>
  <th style="text-align:right">Billed Amount</th>
  <th style="text-align:right">Fair Amount</th>
  <th style="text-align:center">Status</th>
</tr>
</thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</div>"""
    st.markdown(html, unsafe_allow_html=True)


def render_recommendations(results: list[dict], summary: dict) -> None:
    overcharged = [r for r in results if "OVERCHARGE" in r.get("flag", "").upper()]
    suspicious = [r for r in results if r.get("flag", "").upper() == "SUSPICIOUS"]
    savings = summary.get("potential_savings", 0)

    st.markdown("#### What you should do")

    if savings > 0:
        st.markdown(
            f'<div class="warn-box">💰 <b>You may be eligible for a refund of approximately {_fmt_inr(savings)}.</b> '
            f"Request an itemised bill review from the hospital's billing department.</div>",
            unsafe_allow_html=True,
        )

    if overcharged:
        top = sorted(overcharged, key=lambda x: x.get("overcharge_amount", 0), reverse=True)[:5]
        names_md = "\n".join(
            f"- **{r['name']}** — billed {_fmt_inr(r['amount'])}, fair estimate {_fmt_inr(r['fair_amount'])} "
            f"(overcharge: {_fmt_inr(r['overcharge_amount'])})"
            for r in top
        )
        with st.expander("🔴 Top overcharged items — ask the hospital to justify these rates"):
            st.markdown(names_md)

    if suspicious:
        names_md = "\n".join(
            f"- **{r['name']}** — {r.get('flag_reason','')}" for r in suspicious
        )
        with st.expander("🟠 Suspicious / potentially duplicate items"):
            st.markdown(names_md)

    st.markdown(
        '<div class="info-box">📋 <b>Your rights as a patient in India:</b><br>'
        "• You have the right to an <b>itemised bill</b> from any hospital under the Consumer Protection Act.<br>"
        "• For overcharging complaints, contact your State's <b>Medical Council</b> or the "
        "<b>National Consumer Disputes Redressal Commission (NCDRC)</b>.<br>"
        "• You can also approach the <b>Insurance Ombudsman</b> if insured.</div>",
        unsafe_allow_html=True,
    )

    if summary.get("health_score", 100) < 50:
        st.markdown(
            '<div class="warn-box">⚠️ <b>Low Bill Health Score detected.</b> '
            "Consider consulting a medical billing advocate or a Chartered Accountant with healthcare expertise "
            "before making payment.</div>",
            unsafe_allow_html=True,
        )


# ─── Sidebar ──────────────────────────────────────────────────────────────────

def render_sidebar() -> str:
    """Render the sidebar and return the selected mode."""
    with st.sidebar:
        st.markdown("## 🏥 MediBill Audit")
        st.markdown("*AI-Powered Bill Checker*")
        st.divider()

        mode = st.radio(
            "Select Mode",
            ["🎯 Demo Mode", "📤 Upload My Bill"],
            help="Demo mode uses a pre-loaded sample bill. Upload mode lets you analyse your own bill.",
        )

        st.divider()

        if config.is_api_configured():
            st.success("✅ Gemini API: Connected")
            st.caption(f"Model: **{config.GEMINI_MODEL}** ({config.GEMINI_MODEL_SOURCE})")
        else:
            st.warning("⚠️ Gemini API: Not configured")
            with st.expander("How to add API key"):
                st.markdown(
                    "**Option 1 — Streamlit Cloud:**\n"
                    "Add `GEMINI_API_KEY` in your app's *Secrets* settings.\n\n"
                    "**Option 2 — Local:**\n"
                    "Create a `.env` file in the project folder:\n\n"
                    "```\nGEMINI_API_KEY=your_key_here\n```\n\n"
                    "Get a free key at [Google AI Studio](https://aistudio.google.com/)"
                )

        st.divider()
        st.markdown("#### 📊 Colour Legend")
        st.markdown(
            """
<small>
🔴 <b>Overcharged</b> — Rate significantly above benchmark<br>
🟡 <b>Slightly High</b> — Rate marginally above benchmark<br>
🟢 <b>Fair</b> — Rate within acceptable range<br>
🟠 <b>Suspicious</b> — Duplicate or unusual charge<br>
🔵 <b>Below Benchmark</b> — Better than expected<br>
⚪ <b>Unmatched</b> — No benchmark data available<br>
</small>""",
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown(
            "<small>AICA Capstone Project v1.0<br>© 2026 MediBill Audit</small>",
            unsafe_allow_html=True,
        )

    return mode


# ─── How It Works ──────────────────────────────────────────────────────────────

def render_how_it_works() -> None:
    with st.expander("ℹ️ How MediBill Audit works", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        steps = [
            ("1", "Upload Your Bill", "📄", "Upload a photo or PDF of your hospital bill, or use our demo sample."),
            ("2", "AI Extracts Items", "🤖", "Our AI reads every line item — room charges, medicines, tests, procedures."),
            ("3", "Compare to Benchmarks", "📊", "Each item is compared against standard rates for Indian hospitals."),
            ("4", "Get Your Report", "📋", "Receive a colour-coded report with your Bill Health Score and savings estimate."),
        ]
        for col, (num, title, icon, desc) in zip([c1, c2, c3, c4], steps):
            with col:
                st.markdown(
                    f'<div class="step-card">'
                    f'<div class="step-number">{num}</div><br>'
                    f'<div style="font-size:2rem">{icon}</div>'
                    f"<h4>{title}</h4><p>{desc}</p></div>",
                    unsafe_allow_html=True,
                )
        st.markdown("")
        st.markdown(
            '<div class="info-box">'
            "📌 <b>Benchmark data</b> is sourced from CGHS (Central Government Health Scheme) rates, "
            "NABH guidelines, and published hospital tariff studies for Tier-1 Indian cities. "
            "Actual rates vary by hospital category, location, and insurance agreements.</div>",
            unsafe_allow_html=True,
        )


# ─── Demo Mode ────────────────────────────────────────────────────────────────

def render_demo_mode() -> None:
    st.markdown("### 🎯 Demo Mode — Sample Hospital Bill")
    st.markdown(
        '<div class="info-box">This is a pre-loaded sample bill for a cardiac patient. '
        "It contains a realistic mix of fair charges, overcharges, and suspicious items. "
        "Click <b>Analyse Bill</b> to see the full audit.</div>",
        unsafe_allow_html=True,
    )

    # Patient info card
    p = DEMO_PATIENT
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**Patient:** {p['name']}")
        st.markdown(f"**Age/Gender:** {p['age']} yrs / {p['gender']}")
        st.markdown(f"**Diagnosis:** {p['diagnosis']}")
    with c2:
        st.markdown(f"**Hospital:** {p['hospital']}, {p['city']}")
        st.markdown(f"**Admission:** {p['admission_date']}")
        st.markdown(f"**Discharge:** {p['discharge_date']} ({p['duration_days']} days)")
    with c3:
        st.markdown(f"**Bill No:** {p['bill_number']}")
        st.markdown(f"**Doctor:** {p['attending_doctor']}")

    st.markdown("---")
    total = sum(i["amount"] for i in DEMO_BILL_ITEMS)
    st.markdown(f"**{len(DEMO_BILL_ITEMS)} line items** — Total billed: **{_fmt_inr(total)}**")

    if st.button("🔍 Analyse This Bill", type="primary", width="stretch"):
        with st.spinner("Analysing bill against benchmark rates..."):
            results, summary = analyze_bill(DEMO_BILL_ITEMS)
        st.session_state["results"] = results
        st.session_state["summary"] = summary
        st.session_state["patient_info"] = DEMO_PATIENT
        st.session_state["analysed"] = True
        st.rerun()


# ─── Upload Mode ──────────────────────────────────────────────────────────────

def render_upload_mode() -> None:
    st.markdown("### 📤 Upload Your Hospital Bill")

    api_ready = config.is_api_configured()

    if not api_ready:
        st.markdown(
            '<div class="warn-box">⚠️ <b>Gemini API key not configured.</b> '
            "To analyse your own bill, add your API key to a <code>.env</code> file. "
            "See sidebar for instructions.<br><br>"
            "👉 <b>Try Demo Mode</b> (sidebar) to see the full app without an API key.</div>",
            unsafe_allow_html=True,
        )

    uploaded = st.file_uploader(
        "Upload hospital bill (PDF, JPG, or PNG)",
        type=["pdf", "jpg", "jpeg", "png", "webp"],
        help="Upload a clear photo or scan of your hospital bill.",
        disabled=not api_ready,
    )

    st.markdown("#### Patient Information (optional)")
    c1, c2 = st.columns(2)
    with c1:
        patient_name = st.text_input("Patient Name", placeholder="e.g., Ramesh Kumar")
        hospital_name = st.text_input("Hospital Name", placeholder="e.g., Apollo Hospital, Delhi")
        diagnosis = st.text_input("Diagnosis / Reason for Admission", placeholder="e.g., Appendicitis")
    with c2:
        bill_number = st.text_input("Bill Number", placeholder="e.g., INV-2026-00123")
        admission_date = st.text_input("Admission Date", placeholder="e.g., 15-Mar-2026")
        discharge_date = st.text_input("Discharge Date", placeholder="e.g., 18-Mar-2026")

    if uploaded and api_ready:
        st.success(f"✅ File uploaded: **{uploaded.name}** ({uploaded.size / 1024:.1f} KB)")

        if st.button("🔍 Analyse My Bill", type="primary", width="stretch"):
            from utils.pdf_handler import parse_bill_with_gemini, read_uploaded_file

            with st.spinner("Reading your bill with AI... this may take 20–40 seconds..."):
                try:
                    mime, file_bytes = read_uploaded_file(uploaded)
                    items = parse_bill_with_gemini(
                        file_bytes,
                        mime,
                        config.GEMINI_API_KEY,
                        config.GEMINI_MODEL,
                    )

                    if not items:
                        st.error(
                            "❌ Could not extract bill items from the uploaded file. "
                            "Please ensure the image is clear and the bill is visible. "
                            "Try Demo Mode to see an example."
                        )
                        return

                    with st.spinner(f"Analysing {len(items)} items against benchmark rates..."):
                        results, summary = analyze_bill(items)

                    patient_info = {
                        "name": patient_name or "Patient",
                        "hospital": hospital_name or "Hospital",
                        "diagnosis": diagnosis or "N/A",
                        "bill_number": bill_number or "N/A",
                        "admission_date": admission_date or "N/A",
                        "discharge_date": discharge_date or "N/A",
                        "bill_date": datetime.now().strftime("%d-%b-%Y"),
                        "age": "N/A",
                        "gender": "N/A",
                        "attending_doctor": "N/A",
                        "duration_days": "N/A",
                    }

                    st.session_state["results"] = results
                    st.session_state["summary"] = summary
                    st.session_state["patient_info"] = patient_info
                    st.session_state["analysed"] = True
                    st.rerun()

                except RuntimeError as e:
                    st.error(f"❌ Error calling Gemini API: {e}")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {e}")


# ─── Results Section ──────────────────────────────────────────────────────────

def render_results(results: list[dict], summary: dict, patient_info: dict) -> None:
    st.markdown("---")
    st.markdown("## 📊 Audit Results")

    # ── Summary metrics ──────────────────────────────────────────────────────
    score = summary["health_score"]
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)

    with mc1:
        st.markdown(
            f'<div class="metric-card card-red">'
            f'<div class="value" style="color:#C62828">{_fmt_inr(summary["total_billed"])}</div>'
            f'<div class="label">Total Billed</div></div>',
            unsafe_allow_html=True,
        )
    with mc2:
        st.markdown(
            f'<div class="metric-card card-green">'
            f'<div class="value" style="color:#2E7D32">{_fmt_inr(summary["total_fair"])}</div>'
            f'<div class="label">Fair Estimate</div></div>',
            unsafe_allow_html=True,
        )
    with mc3:
        st.markdown(
            f'<div class="metric-card card-orange">'
            f'<div class="value" style="color:#E65100">{_fmt_inr(summary["potential_savings"])}</div>'
            f'<div class="label">Potential Savings</div></div>',
            unsafe_allow_html=True,
        )
    with mc4:
        flag_counts = (
            f"🔴 {summary['items_overcharged']} overcharged &nbsp;|&nbsp; "
            f"🟠 {summary['items_suspicious']} suspicious &nbsp;|&nbsp; "
            f"🟢 {summary['items_fair']} fair"
        )
        st.markdown(
            f'<div class="metric-card card-blue">'
            f'<div class="value" style="color:#1565C0">{summary["total_items"]}</div>'
            f'<div class="label">Total Items Checked</div></div>',
            unsafe_allow_html=True,
        )
    with mc5:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="value" style="color:{_score_color(score)}">{score}/100</div>'
            f'<div class="label">Bill Health Score — {_score_label(score)}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gauge + breakdown ────────────────────────────────────────────────────
    gc1, gc2, gc3 = st.columns([1.2, 1, 1.8])

    with gc1:
        st.markdown("#### Bill Health Score")
        st.plotly_chart(make_gauge(score), width="stretch", config={"displayModeBar": False})
        st.markdown(
            f"<div style='text-align:center;font-size:0.85rem;color:#757575'>"
            f"Overcharge: <b>{summary['overcharge_pct']:.1f}%</b> of total bill</div>",
            unsafe_allow_html=True,
        )

    with gc2:
        st.markdown("#### Bill Breakdown")
        pie = make_bill_breakdown_chart(summary)
        if pie:
            st.plotly_chart(pie, width="stretch", config={"displayModeBar": False})

    with gc3:
        st.markdown("#### Overcharge by Category")
        cat_summary = get_category_summary(results)
        bar = make_overcharge_chart(cat_summary)
        if bar:
            st.plotly_chart(bar, width="stretch", config={"displayModeBar": False})
        else:
            st.markdown(
                '<div class="success-box">✅ No significant overcharges found by category.</div>',
                unsafe_allow_html=True,
            )

    # ── Item-wise details table ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🗒️ Item-by-Item Analysis")
    st.markdown(
        '<small style="color:#757575">Each line item in your bill compared against benchmark rates. '
        "🔴 = Overcharged &nbsp; 🟡 = Slightly high &nbsp; 🟢 = Fair &nbsp; "
        "🟠 = Suspicious &nbsp; ⚪ = No benchmark data</small>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    render_results_table(results)

    # ── Expandable details ────────────────────────────────────────────────────
    with st.expander("📋 View full details & explanations for each item"):
        for r in results:
            flag = r.get("flag", "UNKNOWN").upper()
            if "OVERCHARGE" in flag or flag == "SUSPICIOUS":
                icon = "🔴" if "OVERCHARGE" in flag else "🟠"
                st.markdown(
                    f"**{icon} {r['name']}** — Billed: {_fmt_inr(r['amount'])} | "
                    f"Fair: {_fmt_inr(r.get('fair_amount', r['amount']))} | "
                    f"Overcharge: {_fmt_inr(r.get('overcharge_amount', 0))}\n\n"
                    f"> {r.get('flag_reason', '')}"
                )

    # ── Recommendations ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💡 Recommendations & Next Steps")
    render_recommendations(results, summary)

    # ── Download report ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Download Audit Report")

    c_dl1, c_dl2, _ = st.columns([1, 1, 2])

    with c_dl1:
        try:
            from utils.report_generator import generate_pdf_report

            pdf_bytes = generate_pdf_report(patient_info, results, summary)
            st.download_button(
                label="⬇️ Download PDF Report",
                data=pdf_bytes,
                file_name=f"MediBill_Audit_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                width="stretch",
                type="primary",
            )
        except Exception as e:
            st.error(f"PDF generation failed: {e}")

    with c_dl2:
        # Always offer JSON download as fallback
        json_data = json.dumps(
            {"patient": patient_info, "summary": summary, "results": results},
            indent=2,
            ensure_ascii=False,
        )
        st.download_button(
            label="⬇️ Download JSON Data",
            data=json_data,
            file_name=f"MediBill_Audit_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            width="stretch",
        )

    # ── Reset button ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Analyse Another Bill", width="content"):
        for k in ["results", "summary", "patient_info", "analysed"]:
            st.session_state.pop(k, None)
        st.rerun()

    # ── Disclaimer ────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="disclaimer">'
        "⚠️ <b>Disclaimer:</b> This report is generated by an AI system for informational purposes only. "
        "Benchmark rates are indicative averages for Tier-1 Indian cities and may vary by hospital category, "
        "accreditation level, location, and specific clinical circumstances. "
        "This tool does not constitute legal, medical, or financial advice. "
        "Consult a qualified healthcare advocate, Chartered Accountant, or legal professional for formal disputes."
        "</div>",
        unsafe_allow_html=True,
    )


# ─── Main App ─────────────────────────────────────────────────────────────────

def main() -> None:
    # Initialise session state
    if "analysed" not in st.session_state:
        st.session_state["analysed"] = False

    mode = render_sidebar()

    # ── Hero banner ───────────────────────────────────────────────────────────
    st.markdown(
        """
<div class="hero">
  <h1>🏥 MediBill Audit</h1>
  <p>AI-Powered Hospital Bill Checker for Patients</p>
  <span class="badge">AICA Capstone Project &nbsp;|&nbsp; Powered by Google Gemini</span>
</div>""",
        unsafe_allow_html=True,
    )

    # ── How it works ──────────────────────────────────────────────────────────
    render_how_it_works()

    # ── Main content ──────────────────────────────────────────────────────────
    if st.session_state.get("analysed"):
        render_results(
            st.session_state["results"],
            st.session_state["summary"],
            st.session_state["patient_info"],
        )
    else:
        if "Demo" in mode:
            render_demo_mode()
        else:
            render_upload_mode()


if __name__ == "__main__":
    main()
