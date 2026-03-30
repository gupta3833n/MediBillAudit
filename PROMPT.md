# PROMPT.md — MediBill Audit

## Title
**MediBill Audit — AI-Powered Hospital Bill Checker for Patients**

## The Problem
Patients in India have no practical way to verify whether their hospital bill is fair. Overcharging, duplicate entries, unbundling fraud, and inflated consumable rates are rampant — yet patients pay without question because they lack the domain knowledge to challenge a bill. Chartered Accountants possess deep audit skills that can be applied to healthcare billing to protect patients.

## What This App Does
1. **Upload a hospital bill** — photo (JPG/PNG) or PDF
2. **AI extracts every line item** — using Google Gemini's vision/OCR capabilities
3. **Compares each item against benchmark rates** — 60+ hospital charge types sourced from CGHS guidelines, NABH tariffs, and Tier-1 city hospital studies
4. **Flags problems** — overcharges (red), suspicious/duplicate charges (orange), slightly high (yellow), fair (green)
5. **Computes a Bill Health Score (0–100)** — reflecting what fraction of the total bill is within fair limits
6. **Estimates potential savings** — shows how much the patient could recover
7. **Generates a downloadable PDF audit report** — professional report with all findings

### Demo Mode
The app includes a **fully functional demo mode** (no API key required) with a pre-loaded sample cardiac patient bill (30 line items, ₹3.9L total, 31% overcharge detected).

## Tech Stack
| Component | Technology |
|-----------|-----------|
| Frontend / Web App | Python + Streamlit |
| AI / OCR / Vision | Google Gemini 1.5 Pro API |
| Benchmark Database | Custom JSON (60+ charge types) |
| Charts & Visuals | Plotly |
| PDF Report Generation | ReportLab |
| Data Processing | pandas |

## AICA Modules Used
| Module | Application |
|--------|------------|
| Module 3 — Computer Vision | Gemini Vision API to extract line items from bill photos/PDFs |
| Module 6 — Python for AI | Core application logic, data processing, analysis engine |
| Module 7 — Full-Stack Web App | Streamlit-based interactive web application |
| Module 10 — Agentic AI | AI-driven bill analysis workflow — extraction → matching → scoring → reporting |

## How to Recreate This From Scratch Using AI

### Step 1: Set up the project
```
mkdir MediBillAudit && cd MediBillAudit
pip install streamlit google-generativeai python-dotenv Pillow PyPDF2 reportlab plotly pandas
```

### Step 2: Prompt an AI assistant with this description
> "Build a Streamlit web app called MediBill Audit. It should let patients upload a hospital bill (photo or PDF). Use Google Gemini 1.5 Pro's vision API to extract line items (item name, quantity, unit rate, total amount). Compare each extracted item against a JSON benchmark database of 60+ hospital charge types with min/max/benchmark rates for Indian Tier-1 cities. Flag items as MAJOR OVERCHARGE (>50% above benchmark), OVERCHARGED (20-50%), SLIGHTLY HIGH (5-20%), FAIR, SUSPICIOUS (duplicates), or BELOW BENCHMARK. Compute a Bill Health Score from 0-100. Show results in a dashboard with Plotly charts (category breakdown, overcharge distribution). Generate a downloadable PDF audit report using ReportLab. Include a demo mode with a pre-loaded sample cardiac patient bill that works without any API key."

### Step 3: Build the benchmark database
Create `benchmarks/rates.json` with rate ranges for categories: Room Charges, Doctor Fees, Diagnostics, Procedures, OT & Anesthesia, Medicines, Consumables, Nursing, Administrative. Source rates from CGHS guidelines and NABH published tariffs.

### Step 4: Add demo data
Create a realistic sample bill (cardiac patient, 4-day admission, ~30 line items) with intentional overcharges so the demo showcases the app's detection capabilities.

### Step 5: Test and iterate
Run `streamlit run app.py`, test with demo mode first, then test with real bills using a Gemini API key.

## File Structure
```
MediBillAudit/
├── app.py                  # Main Streamlit application (UI + orchestration)
├── analyzer.py             # Core bill analysis engine (matching, scoring, flagging)
├── config.py               # API key loading & app configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Template for API key setup
├── benchmarks/
│   └── rates.json          # Benchmark rates for 60+ hospital charge types
└── utils/
    ├── demo_data.py        # Sample hospital bill data (30 line items)
    ├── pdf_handler.py      # File reading & Gemini API integration
    └── report_generator.py # PDF audit report generation (ReportLab)
```

---
*AICA (AI for CA) Level 2 Capstone Project — March 2026*
