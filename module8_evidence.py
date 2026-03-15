"""
module8_evidence.py — Evidence Repository
Upload, store and track evidence files for each control across all annexes.
Fixed: HTML rendering bug when Level-I bank selected.
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


# ── Annex → controls mapping ───────────────────────────────────────────────
ANNEX_CONTROLS = {
    "Basic Framework": [
        "B-1. Information Security Policy",
        "B-2. IT Asset Management",
        "B-3. Access Control Policy",
        "B-4. Password Management",
        "B-5. Physical & Environmental Security",
        "B-6. Network Security Management",
        "B-7. Secure Configuration",
        "B-8. Patch & Vulnerability Management",
        "B-9. Removable Media Controls",
        "B-10. Antivirus & Malware Protection",
        "B-11. Secure Software Development",
        "B-12. Data Backup & Recovery",
        "B-13. Incident Response & Management",
        "B-14. Business Continuity Planning",
        "B-15. Cybersecurity Awareness Training",
        "B-16. Third-Party / Vendor Risk Management",
        "B-17. Audit Logging & Monitoring",
        "B-18. Data Classification & Handling",
        "B-19. Email & Internet Usage Policy",
        "B-20. Change Management",
    ],
    "Annex I": [
        "I-1. IT Governance Framework",
        "I-2. IS Policy Review",
        "I-3. Risk Assessment Process",
        "I-4. Cybersecurity Roles & Responsibilities",
        "I-5. Security Awareness Program",
        "I-6. Privileged Access Management",
        "I-7. Network Perimeter Security",
        "I-8. Encryption Standards",
        "I-9. Secure Disposal of Media",
        "I-10. Cybersecurity Incident Reporting to RBI",
        "I-11. Vendor Access Controls",
        "I-12. Security Testing",
        "I-13. Log Retention Policy",
    ],
    "Annex II": [
        "II-1. Data Loss Prevention Strategy",
        "II-2. Anti-Phishing Controls",
        "II-3. VA/PT of Critical Applications",
        "II-4. Internet Banking Security",
        "II-5. Mobile Banking Security",
        "II-6. Network Segmentation",
        "II-7. Web Application Firewall",
        "II-8. Database Activity Monitoring",
        "II-9. SIEM Implementation",
        "II-10. Digital Certificate Management",
        "II-11. API Security",
        "II-12. Fraud Detection Controls",
        "II-13. Customer Awareness Programme",
        "II-14. Two-Factor Authentication",
        "II-15. Secure Coding Standards",
    ],
    "Annex III": [
        "III-1. Advanced Threat Defence",
        "III-2. Real-time Transaction Monitoring",
        "III-3. ATM Security Controls",
        "III-4. SWIFT Security Controls",
        "III-5. Red Team Exercises",
        "III-6. Threat Intelligence Programme",
        "III-7. Advanced Persistent Threat Defence",
        "III-8. Forensic Investigation Capability",
        "III-9. Security Operations Monitoring",
        "III-10. Cyber Crisis Management Plan",
    ],
    "Annex IV": [
        "1.1 C-SOC — Expectations & Capabilities",
        "1.2 C-SOC — Technological Setup Steps",
        "2.1 Participation in Cyber Drills (CERT-IN / IDRBT)",
        "3.1 Incident Response in Interconnected Systems & Networks",
        "3.2 SOC, Incident Response & Digital Forensics Policy",
        "4.1 Forensic Metrics — KPIs & KRIs",
        "4.2 Network Forensics / DDoS Mitigation Arrangement",
        "5.1 Board-Approved IT Strategy & Policy",
        "6.1 Cyber Security Team / Function",
        "6.2 IT Strategy Committee (Board Level)",
        "6.3 IT Steering Committee",
        "6.4 Chief Information Security Officer (CISO)",
        "6.5 Information Security Committee",
        "6.6 Audit Committee of Board (ACB) — IS Audit Role",
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
    if "evidence_store" not in st.session_state:
        st.session_state["evidence_store"] = {}
    return st.session_state["evidence_store"]


def _coverage_stats():
    store  = _evidence_store()
    pairs  = _all_controls_for_level()
    total  = len(pairs)
    covered = sum(1 for (a, c) in pairs if store.get(f"{a}||{c}"))
    return total, covered


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

    applicable_annexes = _get_applicable_annexes()
    total_controls, covered = _coverage_stats()
    pct     = round((covered / total_controls) * 100, 1) if total_controls else 0
    pending = total_controls - covered
    store   = _evidence_store()
    total_files = sum(len(v) for v in store.values())
    total_kb    = sum(e.get("size_kb", 0) for entries in store.values() for e in entries)
    total_mb    = round(total_kb / 1024, 2)

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
            st.markdown('<div class="rbi-section-title" style="margin-top:14px;">Files Ready to Save</div>', unsafe_allow_html=True)
            for f in uploaded_files:
                size_kb = round(len(f.getvalue()) / 1024, 1)
                ext = f.name.rsplit(".", 1)[-1].upper() if "." in f.name else "FILE"
                # Use st.markdown with unsafe_allow_html=True — fixes the raw HTML bug
                st.markdown(f"""
                <div class="rbi-card" style="padding:10px 16px; margin-bottom:6px;
                     display:flex; align-items:center; gap:12px;">
                    <div style="font-size:20px;">📎</div>
                    <div style="flex:1; min-width:0;">
                        <div style="font-size:13px; font-weight:600;
                                    color:var(--text-primary); white-space:nowrap;
                                    overflow:hidden; text-overflow:ellipsis;">{f.name}</div>
                        <div style="font-size:11px; color:var(--text-dim); margin-top:1px;">
                            {ext} &nbsp;·&nbsp; {size_kb} KB
                        </div>
                    </div>
                    <span class="rbi-badge badge-gold">{ev_type}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅  Save to Repository", key="ev_save_btn",
                         width='stretch', type="primary"):
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
                    store[key].append(entry)
                    saved += 1
                st.session_state["evidence_store"] = store
                _log("upload", f"Evidence saved: {selected_control}",
                     detail=f"{saved} file(s) · {selected_annex} · {ev_type}")
                st.success(f"✅ {saved} file(s) saved for **{selected_control}**")
                st.rerun()

        # Existing evidence for selected control
        key_sel  = f"{selected_annex}||{selected_control}"
        existing = _evidence_store().get(key_sel, [])
        if existing:
            st.markdown('<div class="rbi-section-title" style="margin-top:18px;">Existing Evidence for This Control</div>', unsafe_allow_html=True)
            for i, entry in enumerate(existing):
                c1, c2, c3 = st.columns([3.5, 1.5, 0.7])
                with c1:
                    notes_html = f"<div style='font-size:11px;color:var(--text-secondary);margin-top:2px;'>{entry['notes']}</div>" if entry.get("notes") else ""
                    st.markdown(f"""
                    <div style="padding:6px 0;">
                        <div style="font-size:13px; font-weight:600;
                                    color:var(--text-primary);">📎 {entry['file_name']}</div>
                        <div style="font-size:11px; color:var(--text-dim); margin-top:2px;">
                            {entry['evidence_type']} &nbsp;·&nbsp; {entry['size_kb']} KB
                            &nbsp;·&nbsp; {entry['uploaded_at']}
                        </div>
                        {notes_html}
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    if entry.get("file_bytes"):
                        st.download_button(
                            "⬇️ Download", data=entry["file_bytes"],
                            file_name=entry["file_name"],
                            key=f"dl_up_{key_sel}_{i}", width='stretch',
                        )
                with c3:
                    if st.button("🗑️", key=f"del_up_{key_sel}_{i}", width='stretch'):
                        store = _evidence_store()
                        # ── Delete from DB first (uses _db_id stored on entry) ──
                        try:
                            from db_store import delete_evidence_entry
                            db_id = entry.get("_db_id")
                            if db_id:
                                delete_evidence_entry(db_id)
                        except Exception:
                            pass
                        store[key_sel].pop(i)
                        if not store[key_sel]:
                            del store[key_sel]
                        st.session_state["evidence_store"] = store
                        _log("change", f"Evidence deleted: {entry['file_name']}",
                             detail=selected_control)
                        st.rerun()
                st.divider()

    # ══════════════════════════════════════════════════════════
    #  TAB 2 — REGISTRY
    # ══════════════════════════════════════════════════════════
    with tab2:
        store = _evidence_store()

        if not store:
            st.markdown("""
            <div class="rbi-card" style="text-align:center; padding:48px 32px;">
                <div style="font-size:40px; margin-bottom:12px;">📂</div>
                <div style="font-family:'Rajdhani',sans-serif; font-size:18px;
                            color:var(--text-secondary);">No Evidence Uploaded Yet</div>
                <div style="font-size:12px; color:var(--text-dim); margin-top:6px;">
                    Switch to the Upload tab to add evidence files.
                </div>
            </div>
            """, unsafe_allow_html=True)
            return

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
            annex, control = k.split("||", 1)
            if annex not in filter_annex:
                continue
            for entry in entries:
                if search and search.lower() not in control.lower() \
                        and search.lower() not in entry["file_name"].lower():
                    continue
                rows.append({"annex": annex, "control": control,
                              "key": k, "entry": entry})

        if not rows:
            st.info("No evidence matches the current filters.")
        else:
            st.markdown(f"""
            <div style="font-size:12px; color:var(--text-dim); margin-bottom:12px;">
                Showing <strong style="color:var(--text-secondary);">{len(rows)}</strong> files
            </div>
            """, unsafe_allow_html=True)

            current_annex = None
            for row in rows:
                if row["annex"] != current_annex:
                    current_annex = row["annex"]
                    st.markdown(f"""
                    <div style="font-size:10px; font-weight:700; letter-spacing:1.5px;
                                text-transform:uppercase; color:var(--text-dim);
                                margin:18px 0 8px 0; padding-bottom:5px;
                                border-bottom:1px solid var(--border);">
                        {current_annex}
                    </div>
                    """, unsafe_allow_html=True)

                entry = row["entry"]
                k     = row["key"]
                idx   = store.get(k, []).index(entry) if entry in store.get(k, []) else 0
                c1, c2, c3 = st.columns([3.5, 1.5, 0.7])
                with c1:
                    notes_html = f"<div style='font-size:11px;color:var(--text-secondary);'>{entry['notes']}</div>" if entry.get("notes") else ""
                    st.markdown(f"""
                    <div style="padding:6px 0;">
                        <div style="font-size:11px; color:var(--text-dim);">{row['control']}</div>
                        <div style="font-size:13px; font-weight:600;
                                    color:var(--text-primary);">📎 {entry['file_name']}</div>
                        <div style="font-size:11px; color:var(--text-dim); margin-top:2px;">
                            <span class="rbi-badge badge-grey">{entry['evidence_type']}</span>
                            &nbsp; {entry['size_kb']} KB &nbsp;·&nbsp; {entry['uploaded_at']}
                        </div>
                        {notes_html}
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    if entry.get("file_bytes"):
                        st.download_button(
                            "⬇️ Download", data=entry["file_bytes"],
                            file_name=entry["file_name"],
                            key=f"dl_reg_{k}_{idx}", width='stretch',
                        )
                with c3:
                    if st.button("🗑️", key=f"del_reg_{k}_{idx}", width='stretch'):
                        # ── Delete from DB first (uses _db_id stored on entry) ──
                        try:
                            from db_store import delete_evidence_entry
                            db_id = entry.get("_db_id")
                            if db_id:
                                delete_evidence_entry(db_id)
                        except Exception:
                            pass
                        store[k].pop(idx)
                        if not store[k]:
                            del store[k]
                        st.session_state["evidence_store"] = store
                        _log("change", f"Evidence deleted: {entry['file_name']}",
                             detail=row["control"])
                        st.rerun()

            # Export
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
                width='stretch',
            )

    # ══════════════════════════════════════════════════════════
    #  TAB 3 — COVERAGE REPORT
    # ══════════════════════════════════════════════════════════
    with tab3:
        store = _evidence_store()
        st.markdown('<div class="rbi-section-title">Coverage by Annex</div>', unsafe_allow_html=True)

        for annex in applicable_annexes:
            controls  = ANNEX_CONTROLS.get(annex, [])
            total_a   = len(controls)
            covered_a = sum(1 for c in controls if store.get(f"{annex}||{c}"))
            pct_a     = round((covered_a / total_a) * 100) if total_a else 0
            bar_color = "#22c55e" if pct_a >= 80 else "#f59e0b" if pct_a >= 50 else "#ef4444"
            badge_cls = "badge-green" if pct_a >= 80 else "badge-amber" if pct_a >= 50 else "badge-red"

            # Card header + progress bar
            st.markdown(f"""
            <div class="rbi-card" style="margin-bottom:14px; padding:18px 22px;">
                <div style="display:flex; justify-content:space-between;
                            align-items:center; margin-bottom:10px;">
                    <div style="font-family:'Rajdhani',sans-serif; font-size:16px;
                                font-weight:700; color:var(--text-primary);">{annex}</div>
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="font-size:12px; color:var(--text-secondary);">
                            {covered_a} / {total_a} controls evidenced
                        </span>
                        <span class="rbi-badge {badge_cls}">{pct_a}%</span>
                    </div>
                </div>
                <div style="background:var(--border); border-radius:6px;
                            height:7px; overflow:hidden; margin-bottom:12px;">
                    <div style="width:{pct_a}%; height:100%; background:{bar_color};
                                border-radius:6px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Control dots — rendered as individual st.markdown calls
            # (avoids the raw-HTML bug caused by unclosed tags in single block)
            cols = st.columns(3)
            for ci, ctrl in enumerate(controls):
                key_c   = f"{annex}||{ctrl}"
                has_ev  = bool(store.get(key_c))
                dot_col = "#22c55e" if has_ev else "var(--border)"
                count   = len(store.get(key_c, []))
                cnt_txt = f" ({count})" if has_ev else ""
                txt_col = "var(--text-primary)" if has_ev else "var(--text-dim)"
                with cols[ci % 3]:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:6px;'
                        f'padding:3px 0;">'
                        f'<div style="width:8px;height:8px;border-radius:50%;'
                        f'background:{dot_col};flex-shrink:0;"></div>'
                        f'<div style="font-size:11.5px;color:{txt_col};">'
                        f'{ctrl}{cnt_txt}</div></div>',
                        unsafe_allow_html=True,
                    )

            st.markdown("<br>", unsafe_allow_html=True)

        # Overall progress
        overall_color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 50 else "#ef4444"
        st.markdown('<div class="rbi-section-title">Overall Evidence Coverage</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;
                    align-items:center;margin-bottom:8px;">
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