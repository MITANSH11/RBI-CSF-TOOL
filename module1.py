import streamlit as st


def _log(event_type, action, detail=""):
    """Safe audit log helper — works even if module7 isn't loaded yet."""
    try:
        from module7_audit import log_event
        log_event(event_type, action, detail, module="module1")
    except Exception:
        pass


def show_module1():

    st.markdown("""
    <div class="rbi-page-header">
        <h1>📋 MODULE 1 — LEVEL IDENTIFICATION</h1>
        <p>Determine your bank's RBI Cybersecurity compliance tier based on operational parameters</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Bank Name ──────────────────────────────────────────────
    st.markdown('<div class="rbi-section-title">Bank Information</div>', unsafe_allow_html=True)
    bank_name = st.text_input(
        "Bank Name",
        placeholder="Enter Full Bank Name (e.g. Saraswat Co-operative Bank Ltd.)",
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Assessment Criteria ────────────────────────────────────
    st.markdown('<div class="rbi-section-title">Operational Assessment</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:var(--text-secondary); font-size:13px; margin-bottom:16px;">'
        'Select all infrastructure and service parameters applicable to your bank as per RBI Graded Approach</p>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="rbi-card rbi-card-gold"><div class="rbi-label">CPS Membership</div></div>', unsafe_allow_html=True)
        cps_sub    = st.checkbox("Sub-member of CPS")
        cps_direct = st.checkbox("Direct Member of CPS")

    with col2:
        st.markdown('<div class="rbi-card rbi-card-gold"><div class="rbi-label">Digital Channels</div></div>', unsafe_allow_html=True)
        internet_banking = st.checkbox("Offers Internet Banking")
        mobile_banking   = st.checkbox("Provides Mobile Banking")
        cts_imps_upi     = st.checkbox("Direct Member of CTS / IMPS / UPI")

    with col3:
        st.markdown('<div class="rbi-card rbi-card-gold"><div class="rbi-label">Infrastructure</div></div>', unsafe_allow_html=True)
        atm_switch  = st.checkbox("Own ATM Switch")
        swift       = st.checkbox("SWIFT Interface")
        data_centre = st.checkbox("Hosts Data Centre / Provides Software Support to Other Banks")

    # ── RBI Level Logic ────────────────────────────────────────
    digital_channel = internet_banking or mobile_banking or cts_imps_upi
    cps_any         = cps_sub or cps_direct

    if cps_any and ((atm_switch and swift) or data_centre):
        level = "Level-IV"
    elif cps_direct or atm_switch or swift:
        level = "Level-III"
    elif cps_sub and digital_channel:
        level = "Level-II"
    else:
        level = "Level-I"

    # Log if bank name or level changed
    prev_level = st.session_state.get("bank_level")
    prev_name  = st.session_state.get("bank_name")

    if bank_name and bank_name != prev_name:
        _log("identify", f"Bank name set: {bank_name}", detail=f"Level → {level}")
    if level != prev_level and prev_level is not None:
        _log("change", f"Compliance level changed: {prev_level} → {level}",
             detail=f"Bank: {bank_name or 'unnamed'}")

    st.session_state["bank_name"]  = bank_name
    st.session_state["bank_level"] = level

    # ── Result Display ─────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="rbi-section-title">Identified Compliance Tier</div>', unsafe_allow_html=True)

    level_meta = {
        "Level-I": {
            "color":   "#4fc3f7",
            "border":  "rbi-card-gold",
            "badge":   "badge-blue",
            "desc":    "Basic Framework + Annex I controls are applicable.",
            "applies": "All Urban Cooperative Banks (UCBs)",
            "annexes": "Basic Framework, Annex I",
            "extra":   "Bank-specific email communication as per RBI circular dated Oct 19, 2018.",
        },
        "Level-II": {
            "color":   "#f59e0b",
            "border":  "rbi-card-amber",
            "badge":   "badge-amber",
            "desc":    "Basic + Annex I + Annex II controls applicable.",
            "applies": "CPS Sub-members with Internet / Mobile Banking or CTS/IMPS/UPI membership",
            "annexes": "Basic Framework, Annex I, Annex II",
            "extra":   "Additional controls: Data Loss Prevention Strategy, Anti-Phishing, VA/PT of critical applications.",
        },
        "Level-III": {
            "color":   "#ef4444",
            "border":  "rbi-card-red",
            "badge":   "badge-red",
            "desc":    "Basic + Annex I + II + III controls applicable.",
            "applies": "UCBs with Direct CPS membership, Own ATM Switch, or SWIFT Interface",
            "annexes": "Basic Framework, Annex I, Annex II, Annex III",
            "extra":   "Additional controls: Advanced Real-time Threat Defence & Management, Risk-based Transaction Monitoring.",
        },
        "Level-IV": {
            "color":   "#a855f7",
            "border":  "rbi-card-red",
            "badge":   "badge-purple",
            "desc":    "Full framework — Basic + Annex I + II + III + IV controls applicable.",
            "applies": "CPS members/sub-members with ATM Switch + SWIFT, or hosting Data Centre / providing Software Support to other banks",
            "annexes": "Basic Framework, Annex I, Annex II, Annex III, Annex IV",
            "extra":   "Additional controls: Cyber Security Operation Center (C-SOC), IT and IS Governance Framework.",
        },
    }

    m = level_meta[level]

    st.markdown(f"""
    <div class="rbi-card {m['border']}" style="margin-top:8px;">
        <div style="display:flex; align-items:center; gap:14px; margin-bottom:18px;">
            <div style="font-family:'Rajdhani',sans-serif; font-size:42px; font-weight:700; color:{m['color']}; line-height:1;">
                {level}
            </div>
            <div>
                <span class="rbi-badge {m['badge']}">IDENTIFIED</span>
                <div style="font-size:12px; color:var(--text-secondary); margin-top:6px;">{m['desc']}</div>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
            <div>
                <div class="rbi-label">Applicable To</div>
                <div style="font-size:13px; color:var(--text-primary); margin-top:3px;">{m['applies']}</div>
            </div>
            <div>
                <div class="rbi-label">Required Templates</div>
                <div style="font-size:13px; color:var(--gold); margin-top:3px; font-weight:600;">{m['annexes']}</div>
            </div>
            <div style="grid-column:span 2;">
                <div class="rbi-label">Additional Controls Note</div>
                <div style="font-size:12px; color:var(--text-secondary); margin-top:3px; line-height:1.6;">{m['extra']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Reference Table ────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="rbi-section-title">Full Reference — RBI Graded Approach</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="rbi-card" style="font-size:13px; padding:20px 22px;">
        <table style="width:100%; border-collapse:collapse; font-size:12px;">
            <thead>
                <tr style="border-bottom:1px solid var(--border);">
                    <th style="text-align:left; padding:8px 12px; color:var(--text-dim); text-transform:uppercase; letter-spacing:1px; font-size:10px;">Tier</th>
                    <th style="text-align:left; padding:8px 12px; color:var(--text-dim); text-transform:uppercase; letter-spacing:1px; font-size:10px;">Criteria</th>
                    <th style="text-align:left; padding:8px 12px; color:var(--text-dim); text-transform:uppercase; letter-spacing:1px; font-size:10px;">Controls</th>
                    <th style="text-align:left; padding:8px 12px; color:var(--text-dim); text-transform:uppercase; letter-spacing:1px; font-size:10px;">Additional Requirements</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:10px 12px; color:#4fc3f7; font-weight:700; font-family:'Rajdhani',sans-serif; font-size:15px;">Level-I</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">All UCBs</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">Basic + Annex I</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">Bank-specific controls per RBI circular (Oct 2018)</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border); background:rgba(255,255,255,0.015);">
                    <td style="padding:10px 12px; color:#f59e0b; font-weight:700; font-family:'Rajdhani',sans-serif; font-size:15px;">Level-II</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">CPS Sub-member + Internet / Mobile Banking or CTS/IMPS/UPI</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">Basic + Annex I + II</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">DLP Strategy, Anti-Phishing, VA/PT of critical apps</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:10px 12px; color:#ef4444; font-weight:700; font-family:'Rajdhani',sans-serif; font-size:15px;">Level-III</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">Direct CPS member / Own ATM Switch / SWIFT Interface</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">Basic + Annex I + II + III</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">Advanced Real-time Threat Defence, Risk-based Transaction Monitoring</td>
                </tr>
                <tr style="background:rgba(255,255,255,0.015);">
                    <td style="padding:10px 12px; color:#a855f7; font-weight:700; font-family:'Rajdhani',sans-serif; font-size:15px;">Level-IV</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">CPS member/sub-member + (ATM Switch &amp; SWIFT) or Data Centre / Software support</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">Basic + Annex I + II + III + IV</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">C-SOC setup, IT &amp; IS Governance Framework</td>
                </tr>
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)