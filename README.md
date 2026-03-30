# MediBill Audit
### AI-Powered Hospital Bill Checker for Patients

**AICA (AI for CA) Level 2 Capstone Project** | Powered by Google Gemini

---

## What it does

MediBill Audit is an AI-powered web app that helps patients verify whether their hospital bill is fair. It:

1. Accepts a hospital bill as a photo or PDF upload (or uses a built-in demo)
2. Extracts every line item using Google Gemini AI
3. Compares each item against standard benchmark rates for Indian hospitals
4. Flags overcharges (red), suspicious charges (orange), and fair items (green)
5. Computes a **Bill Health Score** (0–100)
6. Estimates potential savings and generates a downloadable PDF audit report

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

### 3. Demo mode (no API key needed)

Switch to **Demo Mode** in the sidebar. Click **Analyse This Bill** to see the full audit flow with a pre-loaded sample cardiac patient bill.

---

## Using your own bills (requires Gemini API key)

1. Get a free API key at [https://aistudio.google.com/](https://aistudio.google.com/)
2. Copy `.env.example` to `.env`:
   ```
   cp .env.example .env
   ```
3. Edit `.env` and paste your key:
   ```
   GEMINI_API_KEY=your_key_here
   ```
4. Restart the app — **Upload My Bill** mode will be activated.

---

## Project Structure

```
MediBillAudit/
├── app.py                  Main Streamlit application
├── analyzer.py             Core bill analysis engine
├── config.py               API key & app configuration
├── requirements.txt        Python dependencies
├── .env.example            Template for API key setup
│
├── benchmarks/
│   └── rates.json          Benchmark rates for 60+ hospital charge types
│
├── utils/
│   ├── demo_data.py        Sample hospital bill (30 line items)
│   ├── pdf_handler.py      File reading & Gemini API integration
│   └── report_generator.py PDF audit report generation (ReportLab)
│
└── assets/                 (logos, sample images)
```

---

## Benchmark Data

`benchmarks/rates.json` contains fair market rate ranges for **60+ hospital charge types** across:

| Category | Examples |
|----------|---------|
| Room Charges | General Ward, ICU, Private Room, ICCU |
| Doctor Fees | GP, Specialist, Cardiologist, Surgeon |
| Diagnostics | CBC, ECG, Echo, CT Scan, MRI, X-Ray |
| Procedures | Angioplasty, CABG, Appendectomy, Dialysis |
| OT & Anesthesia | Major OT, Minor OT, General/Spinal Anesthesia |
| Medicines | Aspirin, Statins, IV Fluids, Heparin, Antibiotics |
| Consumables | IV Set, Syringes, Gloves, Catheter |
| Nursing Services | Nursing, Physiotherapy, Dietitian |
| Administrative | Registration, Ambulance |

Rates are sourced from CGHS guidelines, NABH published tariffs, and hospital billing studies for Tier-1 Indian cities.

> **To update rates:** Edit `benchmarks/rates.json`. Each entry has `min_rate`, `max_rate`, `benchmark_rate`, and `flag_threshold_pct`.

---

## Flag Meanings

| Colour | Flag | Meaning |
|--------|------|---------|
| 🔴 Red | MAJOR OVERCHARGE | Rate > 50% above benchmark |
| 🔴 Red | OVERCHARGED | Rate 20–50% above benchmark |
| 🟡 Yellow | SLIGHTLY HIGH | Rate 5–20% above benchmark |
| 🟢 Green | FAIR | Rate within acceptable range |
| 🟠 Orange | SUSPICIOUS | Potentially duplicate or incorrect charge |
| 🔵 Blue | BELOW BENCHMARK | Rate better than expected |
| ⚪ Grey | UNMATCHED | No benchmark data available |

---

## Bill Health Score

The score reflects what fraction of the total bill is within fair benchmark limits:

| Score | Rating |
|-------|--------|
| 80–100 | Excellent |
| 65–79 | Good |
| 50–64 | Fair |
| 35–49 | Poor |
| 0–34 | Very Poor |

---

## Demo Bill Stats

The built-in sample bill (cardiac patient, 4-day admission) demonstrates:
- **Total Billed:** ~₹3,90,000
- **Fair Estimate:** ~₹2,68,000
- **Potential Savings:** ~₹1,22,000 (31% overcharge)
- **Health Score:** 64/100

---

## Tech Stack

- **Frontend:** Streamlit
- **AI/OCR:** Google Gemini 1.5 Pro
- **Charts:** Plotly
- **PDF Report:** ReportLab
- **Data:** pandas

---

## Disclaimer

This tool is for informational purposes only. Benchmark rates are indicative averages for Tier-1 Indian cities. Always consult a qualified healthcare advocate or legal professional for formal disputes.

---

*AICA Capstone Project — AI for CA | 2026*
