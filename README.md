# 🏦 RBI CSF Compliance Tool

A web-based Cybersecurity Compliance Assessment Tool for Urban Cooperative Banks (UCBs) built on the **RBI Graded Approach Framework**. Helps banks identify their compliance tier, assess controls, analyse gaps, and generate audit-ready reports.

---

## 🌐 Live Demo

> **http://35.244.61.159**
> 
> Hosted on Google Cloud VM — asia-south1-a (Mumbai)

---

## 📋 Features

| Module | Description |
|--------|-------------|
| **Module 1 — Level Identification** | Determines RBI compliance tier (Level I–IV) based on bank's operational parameters |
| **Module 2 — Download Templates** | Downloads applicable control assessment templates (Basic + Annex I/II/III/IV) |
| **Module 3 — Compliance Dashboard** | Upload filled templates and generate real-time compliance charts and scores |
| **Module 4 — Gap Analysis** | Identifies and prioritises non-compliant and partially compliant controls |
| **Module 5 — Gap Analysis Report** | Generates a downloadable Word (.docx) report with recommendations |
| **Module 6 — Audit Trail** | Timestamped log of all actions across every module |
| **Module 7 — Evidence Repository** | Upload and manage supporting evidence files per control |

---

## 🏗️ RBI Graded Approach — Compliance Tiers

| Tier | Criteria | Controls |
|------|----------|----------|
| **Level-I** | All UCBs | Basic Framework + Annex I (60 controls) |
| **Level-II** | CPS Sub-member + Internet/Mobile Banking or CTS/IMPS/UPI | + Annex II (83 controls) |
| **Level-III** | Direct CPS member / Own ATM Switch / SWIFT Interface | + Annex III (108 controls) |
| **Level-IV** | CPS member + ATM & SWIFT, or hosts Data Centre | + Annex IV (122 controls) |

---

## 🛠️ Tech Stack

- **Frontend/Backend** — [Streamlit](https://streamlit.io/)
- **Database** — SQLite (via `db_store.py`)
- **Charts** — Plotly
- **Report Generation** — python-docx
- **Data Processing** — Pandas, OpenPyXL
- **Web Server** — Nginx (reverse proxy)
- **Process Manager** — systemd
- **Hosting** — Google Cloud Compute Engine (e2 series, asia-south1-a)

---

## 🚀 Deployment Guide (Google Cloud VM)

### Prerequisites
- Google Cloud VM instance running Ubuntu 22.04+
- VM external IP noted (e.g. `35.244.61.159`)
- Firewall rules open for TCP ports `80` and `8501`

### 1. SSH into your VM
Click the **SSH** button in Google Cloud Console.

### 2. Install dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx git
```

### 3. Upload project files
Use the ⚙️ gear icon in the SSH browser window → **Upload file**.
Upload all `.py`, `.xlsx`, `.css`, and `requirements.txt` files, then:
```bash
mkdir -p ~/rbi_app
mv ~/*.py ~/rbi_app/
mv ~/*.xlsx ~/rbi_app/
mv ~/*.css ~/rbi_app/
mv ~/*.txt ~/rbi_app/
```

### 4. Set up Python virtual environment
```bash
cd ~/rbi_app
python3 -m venv venv
source venv/bin/activate
pip install streamlit pandas openpyxl plotly python-docx Pillow
```

### 5. Create systemd service (runs 24/7)
```bash
sudo nano /etc/systemd/system/rbi_app.service
```

Paste:
```ini
[Unit]
Description=RBI CSF Streamlit App
After=network.target

[Service]
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/rbi_app
ExecStart=/home/YOUR_USERNAME/rbi_app/venv/bin/streamlit run App.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable rbi_app
sudo systemctl start rbi_app
```

### 6. Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/rbi_app
```

Paste:
```nginx
server {
    listen 80;
    server_name YOUR_IP_OR_DOMAIN;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/rbi_app /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 7. Open firewall ports in Google Cloud
Go to **VPC Network → Firewall → Create Firewall Rule**:
- Port `80` (HTTP) — source `0.0.0.0/0`
- Port `8501` (Streamlit) — source `0.0.0.0/0`

---

## 🔄 Updating the App

Whenever you change any file:

```bash
# 1. Upload the changed file via SSH gear icon, then move it
mv ~/changed_file.py ~/rbi_app/

# 2. Restart the app — one command, done
sudo systemctl restart rbi_app
```

---

## 🧰 Useful Commands

```bash
# Check if app is running
sudo systemctl status rbi_app

# View live logs
sudo journalctl -u rbi_app -f

# Restart app
sudo systemctl restart rbi_app

# Restart nginx
sudo systemctl restart nginx
```

---

## 🗄️ Database

Uses **SQLite** stored locally at `rbi_csf_data.db`. Each user/bank has fully isolated data rows. The database is auto-created on first run — no setup needed.

**Schema includes:**
- `users` — credentials (PBKDF2-SHA256 hashed)
- `bank_profiles` — Module 1 level and flags
- `compliance_data` — Module 3 scores and DataFrames
- `gap_data` — Module 4 gap register
- `evidence_files` — Module 7 binary file attachments
- `audit_events` — Full timestamped audit log
- `compliance_history` — Trend tracking snapshots
- `gap_history` — Gap trend tracking

---

## 📁 Project Structure

```
rbi_app/
│
├── App.py                          # Main entry point, routing, auth gate, auto-save
├── auth.py                         # Login / register UI
├── db_store.py                     # SQLite persistence layer
├── module1.py                      # Level Identification
├── module2.py                      # Template Downloads
├── module3.py                      # Compliance Dashboard
├── module4_gap.py                  # Gap Analysis
├── module5.py                      # Gap Analysis Report + Word export
├── module7_audit.py                # Audit Trail
├── module8_evidence.py             # Evidence Repository
├── style.css                       # Global CSS (dark + light theme)
│
├── Basic_Cybersecurity_Framework.xlsx
├── Annex_1_cybersecurity_control.xlsx
├── Annex2_Cybersecurity_.xlsx
├── Annex3_Cybersecurity.xlsx
├── Annex4_Cybersecurity_control.xlsx
│
└── requirements.txt
```

---

## 🔒 Security

- Passwords hashed with **PBKDF2-SHA256** (260,000 iterations)
- Each bank's data is **fully isolated** by `user_id`
- Session persistence across logins
- Auto-save after every render cycle

---

## 📦 Requirements

```
streamlit==1.35.0
pandas==2.2.2
openpyxl==3.1.2
plotly==5.22.0
python-docx==1.1.2
Pillow==10.3.0
```

---

## 👤 Author

**Mitansh Prajapati**  
GitHub: [@MITANSH11](https://github.com/MITANSH11)

---

## 📄 License

This project is for internal compliance use by Urban Cooperative Banks under the RBI Cybersecurity Framework guidelines.
