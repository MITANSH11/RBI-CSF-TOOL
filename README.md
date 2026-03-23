# 🏦 RBI CSF Compliance Tool

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35.0-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

**A full-stack Streamlit web application for Urban Cooperative Banks (UCBs) to assess, track, and manage cybersecurity compliance under the RBI Graded Approach Framework.**

[📸 Screenshots](#-screenshots) · [🚀 Getting Started](#-getting-started) · [✨ Features](#-features) · [🗺️ Roadmap](#️-roadmap) · [🤝 Contributing](#-contributing)

</div>

---

## 📖 Overview

The **RBI CSF Compliance Tool** is a guided, end-to-end compliance assessment platform built for Urban Cooperative Banks (UCBs) regulated by the Reserve Bank of India. It implements the **RBI Cybersecurity Framework (CSF) Graded Approach**, helping banks identify their compliance tier (Level I–IV), assess controls across all applicable annexes, visualise gaps, and generate audit-ready reports.

### Why This Tool?

RBI mandates UCBs to self-assess against the Cybersecurity Framework — a process that spans **5 Excel templates**, **122+ controls**, and 4 compliance tiers. Doing this manually is error-prone and time-consuming. This tool automates the entire workflow:

```
Level Identification → Template Download → Control Assessment → 
Compliance Dashboard → Gap Analysis → Report Generation → Evidence Repository
```

---

## ✨ Features

### 🎯 Core Modules

| Module | Description |
|--------|-------------|
| **Module 1 — Level Identification** | Automatically determines your bank's RBI compliance tier (Level I–IV) based on operational parameters like CPS membership, digital channels, ATM switch, SWIFT interface, and data centre presence |
| **Module 2 — Template Download** | Downloads the exact Excel control templates applicable to your identified tier (Basic Framework + Annex I through IV) |
| **Module 3 — Compliance Dashboard** | Upload filled templates to get real-time visualisations — gauge chart, donut chart, per-annex compliance bars, and section-wise breakdowns using Plotly |
| **Module 4 — Gap Analysis** | Identifies all Non-Compliant and Partially Compliant controls, assigns priority (Critical / High / Medium), and provides filterable gap registers |
| **Module 5 — Gap Analysis Report** | Generates a fully formatted, downloadable **Word (.docx)** report with coloured tables, recommendations, and Annex IV governance checklists |
| **Module 6 — Audit Trail Log** | Timestamped log of every action across all modules — uploads, exports, config changes, logins — with CSV export |
| **Module 7 — Evidence Repository** | Upload, store, and track supporting evidence files (PDFs, screenshots, policy docs) mapped to each individual control |

### 🔒 Security & Authentication

- **PBKDF2-SHA256** password hashing with per-user salts (260,000 iterations)
- Isolated data rows per organisation — no cross-user data leakage
- Persistent session storage — data survives page refreshes and browser closes
- Transparent auto-save after every render cycle

### 💅 UI/UX

- Dark / Light theme toggle with full CSS variable theming
- Responsive layout with sidebar navigation
- Real-time compliance score ring in sidebar
- Progress tracking across all modules
- Mobile-friendly design

---

## 🏗️ Architecture

```
rbi-csf-tool/
│
├── App.py                          # Main entry point, routing, auth gate, auto-save
├── auth.py                         # Login / Register UI, PBKDF2 auth
├── db_store.py                     # SQLite persistence layer (all CRUD operations)
├── style.css                       # Global CSS with CSS variable theming
│
├── module1.py                      # Level Identification
├── module2.py                      # Template Download
├── module3.py                      # Compliance Dashboard (Plotly charts)
├── module4_gap.py                  # Gap Analysis
├── module5.py                      # Word Report Generator
├── module7_audit.py                # Audit Trail
├── module8_evidence.py             # Evidence Repository
│
├── Basic_Cybersecurity_Framework.xlsx
├── Annex_1_cybersecurity_control.xlsx
├── Annex2_Cybersecurity_.xlsx
├── Annex3_Cybersecurity.xlsx
├── Annex4_Cybersecurity_control.xlsx
│
└── requirements.txt
```

### Database Schema (SQLite)

```sql
users              -- Credentials, roles, login timestamps
bank_profiles      -- Module 1: bank name, level, checkbox flags (JSON)
compliance_data    -- Module 3: summary dict + combined DataFrame (CSV)
gap_data           -- Module 4: gap DataFrame (CSV)
evidence_files     -- Module 7: binary evidence BLOBs + metadata
audit_events       -- Module 6: full timestamped event log
compliance_history -- Trend tracking for compliance score over time
gap_history        -- Trend tracking for gap counts over time
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/MITANSH11/RBI-CSF-TOOL.git
cd RBI-CSF-TOOL

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
streamlit run App.py
```

The app will open at `http://localhost:8501`

### First Run

1. Click **Register** and create an account with your bank name
2. Go to **Module 1** and select your bank's operational parameters
3. Your compliance tier (Level I–IV) is automatically determined
4. Download your applicable templates from **Module 2**
5. Fill in the `Control Implemented?` column in each Excel file
6. Upload the filled files in **Module 3** and **Module 4**
7. Export your gap analysis report from **Module 5**

---

## 📋 RBI Compliance Levels

| Tier | Applicable Banks | Templates | Controls |
|------|-----------------|-----------|----------|
| **Level-I** | All UCBs | Basic + Annex I | 60 |
| **Level-II** | CPS Sub-member + Internet/Mobile Banking or CTS/IMPS/UPI | Basic + Annex I + II | 83 |
| **Level-III** | Direct CPS member / Own ATM Switch / SWIFT Interface | Basic + Annex I + II + III | 108 |
| **Level-IV** | CPS member with ATM+SWIFT, or UCBs hosting Data Centre | Basic + Annex I + II + III + IV | 122 |

---

## 📸 Screenshots

> Coming soon — add screenshots of each module here

| Module 1 — Level Identification | Module 3 — Compliance Dashboard |
|--------------------------------|----------------------------------|
| *(screenshot)* | *(screenshot)* |

| Module 4 — Gap Analysis | Module 5 — Word Report |
|-------------------------|------------------------|
| *(screenshot)* | *(screenshot)* |

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RBI_DB_PATH` | `./rbi_csf_data.db` | Override the SQLite database file path (useful for cloud deployments) |

```bash
# Example: store DB in a persistent volume on cloud
export RBI_DB_PATH=/data/rbi_csf_data.db
streamlit run App.py
```

### Deploying to Streamlit Cloud

1. Push your repo to GitHub (ensure Excel template files are included)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New App
3. Set the main file to `App.py`
4. Add `RBI_DB_PATH` in Secrets if using a mounted volume
5. Deploy

> **Note:** On Streamlit Community Cloud, the SQLite DB resets on each deploy. For persistent storage, point `RBI_DB_PATH` to an external volume or migrate to PostgreSQL (see below).

### Migrating to PostgreSQL

The `db_store.py` module is designed for easy database swap. Replace `_conn()` with a `psycopg2` connection and change `?` placeholders to `%s`:

```python
import psycopg2

def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])
```

All public function signatures remain unchanged.

---

## 🗺️ Roadmap

### Planned Enhancements

- [ ] **Multi-user admin panel** — Admin dashboard to view all registered banks and their compliance scores
- [ ] **Email notifications** — Automated reminders for pending assessments and RBI submission deadlines
- [ ] **Compliance trend charts** — Historical compliance score line charts across assessment cycles
- [ ] **Bulk evidence upload** — ZIP import for mass evidence attachment
- [ ] **PDF report export** — Alternative to Word for read-only report sharing
- [ ] **API endpoints** — REST API for integrating with bank's existing GRC platforms
- [ ] **Role-based access control** — Separate roles for CISO, IT Officer, and Board members
- [ ] **Control tagging** — Tag controls by NIST CSF, ISO 27001, or CIS benchmarks for cross-framework mapping
- [ ] **Remediation tracker** — Assign owners, due dates, and status to each gap
- [ ] **PostgreSQL / Supabase support** — First-class cloud database support out of the box

### Known Issues / In Progress

- Evidence tab coverage counter shows 0 on fresh load (fixed in latest commit)
- Module 1 widget keys cleared on navigation (fixed with `_seed_widget_keys` guard)

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | [Streamlit](https://streamlit.io) 1.35.0 |
| Charts | [Plotly](https://plotly.com/python/) 5.22.0 |
| Data Processing | [Pandas](https://pandas.pydata.org/) 2.2.2 |
| Excel Parsing | [openpyxl](https://openpyxl.readthedocs.io/) 3.1.2 |
| Word Generation | [python-docx](https://python-docx.readthedocs.io/) 1.1.2 |
| Database | SQLite (via `sqlite3`) |
| Auth | PBKDF2-SHA256 (stdlib `hashlib`) |
| Deployment | Streamlit Community Cloud / Any Python host |

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

```bash
# Fork the repo, then:
git checkout -b feature/your-feature-name
# Make your changes
git commit -m "feat: describe your change"
git push origin feature/your-feature-name
# Open a Pull Request
```

### Contribution Guidelines

- Follow the existing module structure (`show_moduleN()` entry point)
- All DB operations go through `db_store.py` — do not write to DB directly from modules
- Log user-triggered events via `log_event()` from `module7_audit.py`
- Keep CSS changes in `style.css` using existing CSS variables

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [Reserve Bank of India](https://www.rbi.org.in) — Cybersecurity Framework for Urban Cooperative Banks circular and graded approach guidelines
- [Streamlit](https://streamlit.io) — Open-source app framework
- [Plotly](https://plotly.com) — Interactive charting library

---

## 📬 Contact

**Mitansh** · [@MITANSH11](https://github.com/MITANSH11)

Project Link: [https://github.com/MITANSH11/RBI-CSF-TOOL](https://github.com/MITANSH11/RBI-CSF-TOOL)

---

<div align="center">
<sub>Built with ❤️ for Urban Cooperative Banks navigating RBI cybersecurity compliance</sub>
</div>
