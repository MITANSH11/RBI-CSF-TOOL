"""
module8_evidence.py — Evidence Repository
Upload, store and track evidence files for each control across all annexes.
Fixes: coverage counter showed 0; deletion race condition; DB key mismatch.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io


def _log(event_type, action, detail="", module="module8"):
    try:
        from module7_audit import log_event
        log_event(event_type, action, detail, module=module)
    except Exception:
        pass


# ── Annex → controls mapping (matches actual Excel rows exactly) ───────────
ANNEX_CONTROLS = {
    "Basic Framework": [
        "CP4-1. Cyber Security Policy (Board Approved)",
        "CP4-2. Cyber Security Policy distinct from IT/IS Policy",
        "CP4-3. IT Architecture / Security Framework Compliance",
        "CP4-4. Cyber Crisis Management Plan (CERT-In)",
        "CP5.   Organisational Arrangements for Security",
        "CP6.   Cyber Security Staff Awareness & Familiarisation",
        "CP7.   Customer Data Protection Steps",
        "CP8.   Unusual Cyber Incident Reporting",
        "CP9.   Circular placed before Board / Administrator",
        "S1-1.  IT Asset Inventory Register",
        "S1-2.  Data / Information Classification",
        "S1-3.  Data Protection Inside/Outside Network",
        "S2-1.  Authorised Software / Application Inventory",
        "S2-2.  Software Installation Control Mechanism",
        "S2-3.  Web Browser Auto-Update & Script Control",
        "S2-4.  Internet Usage Restriction",
        "S3-1.  Physical Security of Critical Assets",
        "S3-2.  Environmental Breach Monitoring",
        "S4-1.  Network Device Configuration & Periodic Review",
        "S4-2.  Default Password Change on Network Devices",
        "S4-3.  Wireless LAN / Access Point Security",
        "S4-4.  Critical Infrastructure Segmentation (NEFT/RTGS/SWIFT/CBS/ATM)",
        "S5-1.  Firewall Configuration (Highest Security Level)",
        "S5-2.  Dedicated Systems — Network / App / DB / Server",
        "S6-1.  Vulnerability Identification & Monitoring",
        "S6-2.  Antivirus / Anti-malware on Servers & Endpoints",
        "S7-1.  No Admin Rights on End-User Workstations",
        "S7-2.  Complex Password Policy",
        "S7-3.  Remote Desktop Protocol (RDP) Controls",
        "S7-4.  Centralised Access / Privilege Management",
        "S8-1.  Secure Mail & Messaging Systems",
        "S8-2.  Email Server Specific Controls",
        "S9-1.  Removable Media Default Prohibition",
        "S9-2.  Secure Use of Removable Media on Endpoints",
        "S9-3.  Removable Media Malware Scan",
        "S10-1. Security Policy Communication to Staff & Vendors",
        "S10-2. Staff IS Awareness / Training",
        "S10-3. Board IT Risk / Cyber Security Briefing",
        "S10-4. End-User Phishing / Email Awareness",
        "S11-1. Customer Cyber Security Awareness",
        "S11-2. Customer Card / PIN Security Education",
        "S12-1. Periodic Offline Data Backup",
        "S13-1. Outsourcing SLA Cyber Security Requirements",
        "S13-2. Grievance Redressal Mechanism in SLAs",
        "S13-3. Vendor SLA Periodic Performance Review",
        "ADV1.  Cyber Security Self-Assessment Review (Dec 2020 Advisory)",
        "ADV2.  Self-Assessment Completion Date (if Fully Implemented)",
        "ADV3.  Sponsor Bank Transaction Reconciliation (Feb 2021 Advisory)",
    ],
    "Annex I": [
        "AI-CP4.  Self-Assessment of Compliance Level (45-day reporting)",
        "AI-CP7.  Circular Placed Before Board of Directors",
        "AI-S1-1. Bank-Specific Email Domain Implementation",
        "AI-S1-2. Anti-Phishing, Anti-Malware & DMARC Controls",
        "AI-S1-3. Two-Factor Authentication for CBS & Applications",
        "AI-S1-4. Security Review of Internet Banking PCs / Terminals",
        "AI-S1-5. Password Management Policy (Strong, No Reuse)",
        "AI-S1-6. Staff Phishing Link Awareness Education",
        "AI-S1-7. Cyber Incident Reporting Mechanism",
        "AI-S2-1. Vendor Security Risk Management & Assurance",
        "AI-S2-2. Vendor Service Provider Agreement Requirements",
        "AI-S2-3. Vendor / Third-Party Credential Verification",
    ],
    "Annex II": [
        "AII-CP.  Identification of IS / Cybersecurity Official (CISO-equivalent)",
        "AII-S1-1. Authorised Device Inventory & Boundary Defences",
        "AII-S1-2. Multi-Layer Firewall / IPS / IDS Boundary Defence",
        "AII-S1-3. LAN Segmentation — ATM / CBS / Branch Networks",
        "AII-S2.  Baseline Security Configuration for All Device Categories",
        "AII-S3-1. Dev / Test / Production Environment Segregation",
        "AII-S3-2. Secure Coding Principles in SDLC",
        "AII-S4.  Robust Change Management Process",
        "AII-S5-1. Periodic VA/PT of Internal & External Systems",
        "AII-S5-2. VA/PT for CBS on Shared ASP Infrastructure",
        "AII-S5-3. Application Security Testing of Web/Mobile Apps",
        "AII-S5-4. Prompt Vulnerability Remediation",
        "AII-S5-5. Penetration Testing of Public-Facing & Critical Apps",
        "AII-S6.  Secure Remote Access to UCB Assets",
        "AII-S7-1. Internet Banking / Mobile Banking Security Checks",
        "AII-S7-2. Authentication Framework for Customer Verification",
        "AII-S8.  Anti-Phishing / Anti-Rogue Application Subscription",
        "AII-S9-1. Data Loss / Leakage Prevention (DLP) Strategy",
        "AII-S9-2. DLP at Vendor-Managed Facilities",
        "AII-S10-1. Audit Log Capture — User Actions",
        "AII-S10-2. Alert Mechanism for Log Setting Changes",
        "AII-S11-1. Incident Response Programme",
        "AII-S11-2. RBI Incident Management Requirements Compliance",
    ],
    "Annex III": [
        "AIII-S1-1. Mechanism to Detect & Remedy Unusual Network / System Activity",
        "AIII-S1-2. Outbound Connection Firewall Rules & Reverse Proxy",
        "AIII-S2-1. Disable Remote Connections to Critical Infrastructure",
        "AIII-S2-2. IP Table Restrictions — SWIFT / ATM Switch Servers",
        "AIII-S2-3. ATM Switch / SWIFT Software Integrity Checks",
        "AIII-S2-4. Disable PowerShell on Non-Required Servers / Desktops",
        "AIII-S2-5. Restrict Default Shares (IPC$ & Admin Shares)",
        "AIII-S3-1. Source Code Audit of Critical Business Applications",
        "AIII-S3-2. Security Requirements in Application Design (Access / Authorisation)",
        "AIII-S3-3. Secure Development Practices (Defence-in-Depth)",
        "AIII-S3-4. New Technology Evaluation for Cyber Risks",
        "AIII-S4-1. Centralised Authentication / IAM (Identity & Access Management)",
        "AIII-S4-2. Centralised Policies via Active Directory / Endpoint Mgmt",
        "AIII-S5-1. Advanced Malware Defence — Installation / Spread / Execution",
        "AIII-S5-2. Internet Whitelisting",
        "AIII-S6-1. Audit Log Scope, Frequency & Storage Consultation",
        "AIII-S6-2. Systematic Audit Log Management & Analysis",
        "AIII-S6-3. Audit / Activity Log Capture Settings — Periodic Validation",
        "AIII-S7-1. BCP/DR Aligned to Cyber Security Requirements",
        "AIII-S7-2. Documented DR Procedure with Service Providers",
        "AIII-S7-3. Lessons-Learnt Mechanism for Continuous BCP Improvement",
        "AIII-S8-1. Suspicious Behaviour Incident Reporting Culture",
        "AIII-S8-2. Mandatory Cyber Awareness for New Recruits & Web-Based Training",
        "AIII-S8-3. Board Cyber Security Sensitisation Programme",
        "AIII-S9.  Risk-Based Transaction Monitoring / Surveillance",
    ],
    "Annex IV": [
        "AIV-1.1. C-SOC Expectations & Capabilities (SIEM, Surveillance, Escalation)",
        "AIV-1.2. C-SOC Technological Setup Steps",
        "AIV-2.1. Cyber Drill Participation — CERT-IN / IDRBT",
        "AIV-3.1. Incident Response in All Interconnected Systems & Networks",
        "AIV-3.2. SOC, IR & Digital Forensics Policy / Framework",
        "AIV-4.1. Forensic Metrics — KPIs & KRIs for Security Operations",
        "AIV-4.2. Network Forensics / DDoS Mitigation Arrangement",
        "AIV-5.1. Board-Approved IT Strategy & Policy",
        "AIV-6.1. Dedicated Cyber Security Team / Function",
        "AIV-6.2. IT Strategy Committee (Board Level)",
        "AIV-6.3. IT Steering Committee (Executive Level)",
        "AIV-6.4. Chief Information Security Officer (CISO) Appointment",
        "AIV-6.5. Information Security Committee (Quarterly Reviews)",
        "AIV-6.6. Audit Committee of Board — IS Audit Oversight",
    ],
}

LEVEL_ANNEXES = {
    "Level-I":   ["Basic Framework", "Annex I"],
    "Level-II":  ["Basic Framework", "Annex I", "Annex II"],
    "Level-III": ["Basic Framework", "Annex I", "Annex II", "Annex III"],
    "Level-IV":  ["Basic Framework", "Annex I", "Annex II", "Annex III", "Annex IV"],
}

EVIDENCE_TYPES = [
    "Policy Document",
    "Procedure Document",
    "Screenshot Evidence",
    "Audit Report",
    "VA/PT Report",
    "Training Certificate",
    "Configuration File",
    "Meeting Minutes",
    "Vendor Certificate",
    "Other",
]


def _get_applicable_annexes():
    level = st.session_state.get("bank_level", "Level-I")
    return LEVEL_ANNEXES.get(level, ["Basic Framework", "Annex I"])


def _all_controls_for_level():
    pairs = []
    for annex in _get_applicable_annexes():
        for ctrl in ANNEX_CONTROLS.get(annex, []):
            pairs.append((annex, ctrl))
    return pairs


def _evidence_store():
    """Return the live evidence store from session state, always initialised."""
    if "evidence_store" not in st.session_state:
        st.session_state["evidence_store"] = {}
    return st.session_state["evidence_store"]


def _coverage_stats():
    """
    Count how many controls have at least one evidence file.
    Iterates the actual store keys — never depends on ANNEX_CONTROLS name matching.
    """
    store  = _evidence_store()
    pairs  = _all_controls_for_level()
    total  = len(pairs)

    # Build a set of (annex, control) tuples that have evidence
    evidenced_keys = set()
    for k, entries in store.items():
        if entries:                          # non-empty list
            parts = k.split("||", 1)
            if len(parts) == 2:
                evidenced_keys.add((parts[0], parts[1]))

    covered = sum(1 for (a, c) in pairs if (a, c) in evidenced_keys)
    return total, covered


def _delete_entry(store_key: str, db_id, file_name: str, control: str):
    """
    Safely delete an evidence entry:
    1. Remove from DB by _db_id (if available).
    2. Remove from session_state by matching _db_id or file_name.
    3. Rerun.
    """
    # 1 — DB delete
    if db_id:
        try:
            from db_store import delete_evidence_entry
            delete_evidence_entry(db_id)
        except Exception:
            pass

    # 2 — Session delete (match by db_id or file_name to avoid index drift)
    store = _evidence_store()
    if store_key in store:
        store[store_key] = [
            e for e in store[store_key]
            if not (
                (db_id and e.get("_db_id") == db_id) or
                (not db_id and e.get("file_name") == file_name)
            )
        ]
        if not store[store_key]:
            del store[store_key]
    st.session_state["evidence_store"] = store

    _log("change", f"Evidence deleted: {file_name}", detail=control)
    st.rerun()


# ══════════════════════════════════════════════════════════════
#  MAIN MODULE
# ══════════════════════════════════════════════════════════════
def show_module8():

    st.markdown("""
    <div class="rbi-page-header">
        <h1>📁 MODULE 7 — EVIDENCE REPOSITORY</h1>
        <p>Upload and manage supporting evidence for each cybersecurity control</p>
    </div>
    """, unsafe_allow_html=True)

    _log("view", "Evidence Repository viewed")

    level = st.session_state.get("bank_level")
    if not level:
        st.warning("⚠️ Please complete Module 1 first to identify your compliance level.")
        return

    applicable_annexes          = _get_applicable_annexes()
    total_controls, covered     = _coverage_stats()
    pct                         = round((covered / total_controls) * 100, 1) if total_controls else 0
    pending                     = total_controls - covered
    store                       = _evidence_store()
    total_files                 = sum(len(v) for v in store.values())
    total_kb                    = sum(e.get("size_kb", 0) for entries in store.values() for e in entries)
    total_mb                    = round(total_kb / 1024, 2)

    # ── KPI Strip ──────────────────────────────────────────────
    pct_color = "var(--compliant)" if pct >= 80 else "var(--partial)" if pct >= 50 else "var(--noncompliant)"
    st.markdown(f"""
    <div class="rbi-stat-strip">
        <div class="rbi-stat-item">
            <div class="stat-label">Total Controls</div>
            <div class="stat-value">{total_controls}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Evidenced</div>
            <div class="stat-value" style="color:var(--compliant);">{covered}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Pending</div>
            <div class="stat-value" style="color:var(--partial);">{pending}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Coverage</div>
            <div class="stat-value" style="color:{pct_color};">{pct}%</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Files Uploaded</div>
            <div class="stat-value">{total_files}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Storage Used</div>
            <div class="stat-value" style="font-size:1.15rem;">{total_mb} MB</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ───────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["⬆️  Upload Evidence", "📋  Evidence Registry", "📊  Coverage Report"])

    # ══════════════════════════════════════════════════════════
    #  TAB 1 — UPLOAD
    # ══════════════════════════════════════════════════════════
    with tab1:
        st.markdown('<div class="rbi-section-title">Select Control</div>', unsafe_allow_html=True)

        u1, u2 = st.columns(2)
        with u1:
            selected_annex = st.selectbox(
                "Annex", options=applicable_annexes, key="ev_annex_select",
            )
        with u2:
            selected_control = st.selectbox(
                "Control",
                options=ANNEX_CONTROLS.get(selected_annex, []),
                key="ev_control_select",
            )

        u3, u4 = st.columns(2)
        with u3:
            ev_type = st.selectbox("Evidence Type", options=EVIDENCE_TYPES, key="ev_type_select")
        with u4:
            ev_notes = st.text_input(
                "Notes (optional)",
                placeholder="Brief description...",
                key="ev_notes_input",
            )

        st.markdown("<br>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Drop evidence files here",
            accept_multiple_files=True,
            key="ev_file_uploader",
            label_visibility="collapsed",
        )

        if uploaded_files:
            st.markdown('<div class="rbi-section-title" style="margin-top:14px;">Files Ready to Save</div>',
                        unsafe_allow_html=True)
            for f in uploaded_files:
                size_kb = round(len(f.getvalue()) / 1024, 1)
                ext = f.name.rsplit(".", 1)[-1].upper() if "." in f.name else "FILE"
                st.markdown(f"""
                <div class="rbi-card" style="padding:10px 16px;margin-bottom:6px;
                     display:flex;align-items:center;gap:12px;">
                    <div style="font-size:20px;">📎</div>
                    <div style="flex:1;min-width:0;">
                        <div style="font-size:13px;font-weight:600;color:var(--text-primary);
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{f.name}</div>
                        <div style="font-size:11px;color:var(--text-dim);margin-top:1px;">
                            {ext} &nbsp;·&nbsp; {size_kb} KB
                        </div>
                    </div>
                    <span class="rbi-badge badge-gold">{ev_type}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅  Save to Repository", key="ev_save_btn",
                         use_container_width=True, type="primary"):
                store = _evidence_store()
                key   = f"{selected_annex}||{selected_control}"
                if key not in store:
                    store[key] = []
                saved = 0
                for f in uploaded_files:
                    file_bytes = f.getvalue()
                    entry = {
                        "annex":         selected_annex,
                        "control":       selected_control,
                        "file_name":     f.name,
                        "file_ext":      f.name.rsplit(".", 1)[-1].lower() if "." in f.name else "",
                        "evidence_type": ev_type,
                        "notes":         ev_notes,
                        "file_bytes":    file_bytes,
                        "size_kb":       round(len(file_bytes) / 1024, 1),
                        "uploaded_at":   datetime.now().strftime("%d %b %Y  %H:%M:%S"),
                    }
                    # Immediately persist to DB and store _db_id
                    try:
                        uid = st.session_state.get("user_id")
                        if uid:
                            from db_store import save_evidence_entry
                            entry["_db_id"] = save_evidence_entry(uid, entry)
                    except Exception:
                        pass
                    store[key].append(entry)
                    saved += 1

                st.session_state["evidence_store"] = store
                # Update snap count so autosave doesn't try to re-save
                st.session_state["_snap_ev_count"] = sum(
                    len(v) for v in store.values()
                )
                _log("upload", f"Evidence saved: {selected_control}",
                     detail=f"{saved} file(s) · {selected_annex} · {ev_type}")
                st.success(f"✅ {saved} file(s) saved for **{selected_control}**")
                st.rerun()

        # ── Existing evidence for the selected control ─────────
        key_sel  = f"{selected_annex}||{selected_control}"
        existing = list(_evidence_store().get(key_sel, []))   # copy — safe to iterate
        if existing:
            st.markdown(
                '<div class="rbi-section-title" style="margin-top:18px;">'
                f'Existing Evidence — {selected_control}'
                f' <span style="color:var(--gold);font-size:11px;">({len(existing)} file(s))</span>'
                '</div>',
                unsafe_allow_html=True,
            )
            for entry in existing:
                _render_entry_row(entry, key_sel, tab="up")

    # ══════════════════════════════════════════════════════════
    #  TAB 2 — REGISTRY
    # ══════════════════════════════════════════════════════════
    with tab2:
        store = _evidence_store()

        if not store:
            st.markdown("""
            <div class="rbi-card" style="text-align:center;padding:48px 32px;">
                <div style="font-size:40px;margin-bottom:12px;">📂</div>
                <div style="font-family:'Rajdhani',sans-serif;font-size:18px;
                            color:var(--text-secondary);">No Evidence Uploaded Yet</div>
                <div style="font-size:12px;color:var(--text-dim);margin-top:6px;">
                    Switch to the Upload tab to add evidence files.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            f1, f2 = st.columns(2)
            with f1:
                filter_annex = st.multiselect(
                    "Filter by Annex", options=applicable_annexes,
                    default=applicable_annexes, key="reg_annex_filter",
                )
            with f2:
                search = st.text_input(
                    "Search", placeholder="🔍  Control or file name...",
                    key="reg_search", label_visibility="collapsed",
                )

            rows = []
            for k, entries in store.items():
                if not entries:
                    continue
                parts = k.split("||", 1)
                if len(parts) != 2:
                    continue
                annex, control = parts
                if annex not in filter_annex:
                    continue
                for entry in entries:
                    if search and search.lower() not in control.lower() \
                            and search.lower() not in entry["file_name"].lower():
                        continue
                    rows.append({"annex": annex, "control": control, "key": k, "entry": entry})

            if not rows:
                st.info("No evidence matches the current filters.")
            else:
                st.markdown(f"""
                <div style="font-size:12px;color:var(--text-dim);margin-bottom:12px;">
                    Showing <strong style="color:var(--text-secondary);">{len(rows)}</strong> file(s)
                    across <strong>{len({r['key'] for r in rows})}</strong> controls
                </div>
                """, unsafe_allow_html=True)

                current_annex = None
                for row in rows:
                    if row["annex"] != current_annex:
                        current_annex = row["annex"]
                        st.markdown(f"""
                        <div style="font-size:10px;font-weight:700;letter-spacing:1.5px;
                                    text-transform:uppercase;color:var(--text-dim);
                                    margin:18px 0 8px 0;padding-bottom:5px;
                                    border-bottom:1px solid var(--border);">
                            {current_annex}
                        </div>
                        """, unsafe_allow_html=True)
                    _render_entry_row(row["entry"], row["key"], control_label=row["control"], tab="reg")

                st.markdown("<br>", unsafe_allow_html=True)
                export_rows = [{
                    "Annex":         r["annex"],
                    "Control":       r["control"],
                    "File Name":     r["entry"]["file_name"],
                    "Evidence Type": r["entry"]["evidence_type"],
                    "Size (KB)":     r["entry"]["size_kb"],
                    "Notes":         r["entry"].get("notes", ""),
                    "Uploaded At":   r["entry"]["uploaded_at"],
                } for r in rows]
                csv = pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️  Export Evidence Index (CSV)", csv,
                    file_name="Evidence_Index.csv", mime="text/csv",
                    use_container_width=True,
                )

    # ══════════════════════════════════════════════════════════
    #  TAB 3 — COVERAGE REPORT
    # ══════════════════════════════════════════════════════════
    with tab3:
        store = _evidence_store()
        st.markdown('<div class="rbi-section-title">Coverage by Annex</div>', unsafe_allow_html=True)

        # Build evidenced set once
        evidenced_keys = {
            (k.split("||", 1)[0], k.split("||", 1)[1])
            for k, v in store.items() if v and "||" in k
        }

        for annex in applicable_annexes:
            controls  = ANNEX_CONTROLS.get(annex, [])
            total_a   = len(controls)
            covered_a = sum(1 for c in controls if (annex, c) in evidenced_keys)
            pct_a     = round((covered_a / total_a) * 100) if total_a else 0
            bar_color = "#22c55e" if pct_a >= 80 else "#f59e0b" if pct_a >= 50 else "#ef4444"
            badge_cls = "badge-green" if pct_a >= 80 else "badge-amber" if pct_a >= 50 else "badge-red"

            st.markdown(f"""
            <div class="rbi-card" style="margin-bottom:14px;padding:18px 22px;">
                <div style="display:flex;justify-content:space-between;
                            align-items:center;margin-bottom:10px;">
                    <div style="font-family:'Rajdhani',sans-serif;font-size:16px;
                                font-weight:700;color:var(--text-primary);">{annex}</div>
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:12px;color:var(--text-secondary);">
                            {covered_a} / {total_a} controls evidenced
                        </span>
                        <span class="rbi-badge {badge_cls}">{pct_a}%</span>
                    </div>
                </div>
                <div style="background:var(--border);border-radius:6px;
                            height:7px;overflow:hidden;margin-bottom:12px;">
                    <div style="width:{pct_a}%;height:100%;background:{bar_color};
                                border-radius:6px;transition:width 0.4s ease;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(3)
            for ci, ctrl in enumerate(controls):
                has_ev  = (annex, ctrl) in evidenced_keys
                count   = len(store.get(f"{annex}||{ctrl}", []))
                dot_col = "#22c55e" if has_ev else "var(--border)"
                cnt_txt = f" ({count})" if has_ev else ""
                txt_col = "var(--text-primary)" if has_ev else "var(--text-dim)"
                with cols[ci % 3]:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:6px;padding:3px 0;">'
                        f'<div style="width:8px;height:8px;border-radius:50%;'
                        f'background:{dot_col};flex-shrink:0;"></div>'
                        f'<div style="font-size:11px;color:{txt_col};">{ctrl}{cnt_txt}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            st.markdown("<br>", unsafe_allow_html=True)

        # Overall
        overall_color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 50 else "#ef4444"
        st.markdown('<div class="rbi-section-title">Overall Evidence Coverage</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div class="rbi-label">Progress</div>
            <div style="font-family:'Rajdhani',sans-serif;font-size:22px;
                        font-weight:700;color:{overall_color};">{pct}%</div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(pct / 100)
        st.markdown(f"""
        <div style="font-size:12px;color:var(--text-dim);margin-top:6px;text-align:right;">
            {covered} of {total_controls} controls have supporting evidence
        </div>
        """, unsafe_allow_html=True)


def _render_entry_row(entry: dict, store_key: str,
                      control_label: str = "", tab: str = "up"):
    """Render a single evidence entry row with download + delete."""
    db_id     = entry.get("_db_id")
    file_name = entry["file_name"]
    # Unique widget key using db_id when available, else hash of filename+uploaded_at
    uid_part  = str(db_id) if db_id else str(abs(hash(file_name + entry.get("uploaded_at", ""))))
    key_base  = f"{tab}_{store_key}_{uid_part}"

    notes_html = (
        f"<div style='font-size:11px;color:var(--text-secondary);margin-top:2px;'>"
        f"{entry['notes']}</div>"
        if entry.get("notes") else ""
    )

    c1, c2, c3 = st.columns([3.5, 1.5, 0.7])
    with c1:
        ctrl_line = (
            f"<div style='font-size:11px;color:var(--text-dim);'>{control_label}</div>"
            if control_label else ""
        )
        st.markdown(f"""
        <div style="padding:6px 0;">
            {ctrl_line}
            <div style="font-size:13px;font-weight:600;color:var(--text-primary);">
                📎 {file_name}
            </div>
            <div style="font-size:11px;color:var(--text-dim);margin-top:2px;">
                <span class="rbi-badge badge-grey">{entry['evidence_type']}</span>
                &nbsp; {entry['size_kb']} KB &nbsp;·&nbsp; {entry['uploaded_at']}
            </div>
            {notes_html}
        </div>
        """, unsafe_allow_html=True)
    with c2:
        if entry.get("file_bytes"):
            st.download_button(
                "⬇️ Download",
                data=bytes(entry["file_bytes"]),
                file_name=file_name,
                key=f"dl_{key_base}",
                use_container_width=True,
            )
    with c3:
        if st.button("🗑️", key=f"del_{key_base}", use_container_width=True,
                     help=f"Delete {file_name}"):
            _delete_entry(store_key, db_id, file_name, entry.get("control", ""))

    st.divider()