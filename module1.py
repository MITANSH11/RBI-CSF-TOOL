import streamlit as st


def _log(event_type, action, detail=""):
    try:
        from module7_audit import log_event
        log_event(event_type, action, detail, module="module1")
    except Exception:
        pass


def _save_to_db(user_id, bank_name, bank_level, flags):
    """Persist profile to DB silently."""
    try:
        from db_store import save_bank_profile
        save_bank_profile(user_id, bank_name, bank_level, flags)
    except Exception:
        pass


# Keys for all checkbox widgets
_FLAG_KEYS = [
    "m1_cps_sub", "m1_cps_direct",
    "m1_internet", "m1_mobile", "m1_cts",
    "m1_atm", "m1_swift", "m1_dc",
]


def _seed_widget_keys():
    """
    On first load after login, copy saved module1_flags from session state
    into individual widget keys so checkboxes render pre-ticked.
    Called BEFORE widgets are rendered.
    """
    if st.session_state.get("_m1_seeded"):
        return

    flags = st.session_state.get("module1_flags", {})

    # Also seed bank_name text input key
    if flags.get("bank_name") and not st.session_state.get("m1_bank_name"):
        st.session_state["m1_bank_name"] = flags.get("bank_name", "")
    elif st.session_state.get("bank_name") and not st.session_state.get("m1_bank_name"):
        st.session_state["m1_bank_name"] = st.session_state.get("bank_name", "")

    for key in _FLAG_KEYS:
        if key not in st.session_state:
            st.session_state[key] = flags.get(key, False)

    st.session_state["_m1_seeded"] = True


def show_module1():

    # ── Pre-seed widget keys from saved profile ────────────────
    _seed_widget_keys()

    st.markdown(
        '<div class="rbi-page-header">'
        '<h1>&#128203; MODULE 1 — LEVEL IDENTIFICATION</h1>'
        '<p>Determine your bank\'s RBI Cybersecurity compliance tier based on operational parameters</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Bank Name ──────────────────────────────────────────────
    st.markdown('<div class="rbi-section-title">Bank Information</div>', unsafe_allow_html=True)
    bank_name = st.text_input(
        "Bank Name",
        placeholder="Enter Full Bank Name (e.g. Saraswat Co-operative Bank Ltd.)",
        label_visibility="collapsed",
        key="m1_bank_name",
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
        cps_sub    = st.checkbox("Sub-member of CPS",    key="m1_cps_sub")
        cps_direct = st.checkbox("Direct Member of CPS", key="m1_cps_direct")

    with col2:
        st.markdown('<div class="rbi-card rbi-card-gold"><div class="rbi-label">Digital Channels</div></div>', unsafe_allow_html=True)
        internet_banking = st.checkbox("Offers Internet Banking",         key="m1_internet")
        mobile_banking   = st.checkbox("Provides Mobile Banking",         key="m1_mobile")
        cts_imps_upi     = st.checkbox("Direct Member of CTS / IMPS / UPI", key="m1_cts")

    with col3:
        st.markdown('<div class="rbi-card rbi-card-gold"><div class="rbi-label">Infrastructure</div></div>', unsafe_allow_html=True)
        atm_switch  = st.checkbox("Own ATM Switch",                                          key="m1_atm")
        swift       = st.checkbox("SWIFT Interface",                                         key="m1_swift")
        data_centre = st.checkbox("Hosts Data Centre / Provides Software Support to Other Banks", key="m1_dc")

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

    # ── Build flags dict for persistence ──────────────────────
    current_flags = {
        "bank_name":   bank_name,
        "m1_cps_sub":  cps_sub,
        "m1_cps_direct": cps_direct,
        "m1_internet": internet_banking,
        "m1_mobile":   mobile_banking,
        "m1_cts":      cts_imps_upi,
        "m1_atm":      atm_switch,
        "m1_swift":    swift,
        "m1_dc":       data_centre,
    }

    # ── Detect changes & save ──────────────────────────────────
    prev_level = st.session_state.get("bank_level")
    prev_name  = st.session_state.get("bank_name")
    prev_flags = st.session_state.get("module1_flags", {})

    changed = (
        bank_name  != prev_name  or
        level      != prev_level or
        current_flags != prev_flags
    )

    if bank_name and bank_name != prev_name:
        _log("identify", f"Bank name set: {bank_name}", detail=f"Level → {level}")
    if level != prev_level and prev_level is not None:
        _log("change", f"Compliance level changed: {prev_level} → {level}",
             detail=f"Bank: {bank_name or 'unnamed'}")

    # Always keep session state current
    st.session_state["bank_name"]      = bank_name
    st.session_state["bank_level"]     = level
    st.session_state["module1_flags"]  = current_flags

    # Persist to DB whenever anything changed
    if changed:
        user_id = st.session_state.get("user_id")
        if user_id:
            _save_to_db(user_id, bank_name, level, current_flags)

    # ── Saved indicator ────────────────────────────────────────
    if bank_name and st.session_state.get("user_id"):
        st.markdown(
            '<div style="font-size:11px; color:#22c55e; margin-top:4px; margin-bottom:2px;">'
            '&#10003; Profile saved — will reload automatically on next login</div>',
            unsafe_allow_html=True,
        )

    # ── Result Display ─────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="rbi-section-title">Identified Compliance Tier</div>', unsafe_allow_html=True)

    level_meta = {
        "Level-I": {
            "color":      "#4fc3f7",
            "border":     "rbi-card-blue",
            "badge":      "badge-blue",
            "templates":  2,
            "total_ctrl": "62",
            "desc":       "Basic Framework + Annex I controls are applicable.",
            "applies":    "All Urban Cooperative Banks (UCBs)",
            "annexes":    "Basic Framework, Annex I",
            "extra":      "Bank-specific email communication as per RBI circular dated Oct 19, 2018. Covers governance, access control, patch management, incident response, and baseline IS controls.",
        },
        "Level-II": {
            "color":      "#f59e0b",
            "border":     "rbi-card-amber",
            "badge":      "badge-amber",
            "templates":  3,
            "total_ctrl": "86",
            "desc":       "Basic + Annex I + Annex II controls applicable.",
            "applies":    "CPS Sub-members with Internet / Mobile Banking or CTS / IMPS / UPI membership",
            "annexes":    "Basic Framework, Annex I, Annex II",
            "extra":      "Additional controls: Data Loss Prevention (DLP) Strategy, Anti-Phishing controls, VA/PT of critical applications, Internet & Mobile Banking security, Network Segmentation, WAF, and Two-Factor Authentication.",
        },
        "Level-III": {
            "color":      "#ef4444",
            "border":     "rbi-card-red",
            "badge":      "badge-red",
            "templates":  4,
            "total_ctrl": "112",
            "desc":       "Basic + Annex I + II + III controls applicable.",
            "applies":    "UCBs with Direct CPS membership, Own ATM Switch, or SWIFT Interface",
            "annexes":    "Basic Framework, Annex I, Annex II, Annex III",
            "extra":      "Additional controls: Advanced Real-time Threat Defence, Risk-based Transaction Monitoring, ATM & SWIFT security controls, Red Team Exercises, Threat Intelligence, Forensic Investigation Capability, and Cyber Crisis Management Plan.",
        },
        "Level-IV": {
            "color":      "#a855f7",
            "border":     "rbi-card-blue",
            "badge":      "badge-purple",
            "templates":  5,
            "total_ctrl": "127",
            "desc":       "Full framework — Basic + Annex I + II + III + IV controls applicable.",
            "applies":    "CPS members/sub-members with ATM Switch + SWIFT, or UCBs hosting a Data Centre / providing Software Support to other banks",
            "annexes":    "Basic Framework, Annex I, Annex II, Annex III, Annex IV",
            "extra":      "Annex IV mandates: C-SOC (Cyber Security Operation Centre) with 24x7 surveillance & SIEM integration · CERT-IN / IDRBT Cyber Drill participation · Incident Response & Digital Forensics framework · Board-approved IT Strategy & Policy · Dedicated CISO appointment · IT Strategy Committee (Board level) · IT Steering Committee · Information Security Committee (quarterly reviews) · Audit Committee of Board (ACB) IS Audit oversight.",
        },
    }

    m = level_meta[level]

    st.markdown(f"""
    <div class="rbi-card {m['border']}" style="margin-top:8px;">
        <div style="display:flex; align-items:center; gap:14px; margin-bottom:18px; flex-wrap:wrap;">
            <div style="font-family:'Rajdhani',sans-serif; font-size:46px; font-weight:700;
                        color:{m['color']}; line-height:1;">
                {level}
            </div>
            <div style="flex:1; min-width:200px;">
                <span class="rbi-badge {m['badge']}">IDENTIFIED</span>
                <div style="font-size:12px; color:var(--text-secondary); margin-top:6px;">{m['desc']}</div>
            </div>
            <div style="display:flex; gap:20px; flex-shrink:0;">
                <div style="text-align:center;">
                    <div class="rbi-label">Templates</div>
                    <div style="font-family:'Rajdhani',sans-serif; font-size:28px; font-weight:700;
                                color:{m['color']};">{m['templates']}</div>
                </div>
                <div style="width:1px; background:var(--border);"></div>
                <div style="text-align:center;">
                    <div class="rbi-label">Controls</div>
                    <div style="font-family:'Rajdhani',sans-serif; font-size:28px; font-weight:700;
                                color:var(--gold);">{m['total_ctrl']}</div>
                </div>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
            <div>
                <div class="rbi-label">Applicable To</div>
                <div style="font-size:13px; color:var(--text-primary); margin-top:3px; line-height:1.5;">{m['applies']}</div>
            </div>
            <div>
                <div class="rbi-label">Required Templates</div>
                <div style="font-size:13px; color:var(--gold); margin-top:3px; font-weight:600; line-height:1.6;">{m['annexes']}</div>
            </div>
            <div style="grid-column:span 2; border-top:1px solid var(--border); padding-top:14px; margin-top:2px;">
                <div class="rbi-label">Controls &amp; Requirements</div>
                <div style="font-size:12px; color:var(--text-secondary); margin-top:5px; line-height:1.75;">{m['extra']}</div>
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
                    <th style="text-align:left; padding:8px 12px; color:var(--text-dim); text-transform:uppercase; letter-spacing:1px; font-size:10px; white-space:nowrap;">Tier</th>
                    <th style="text-align:left; padding:8px 12px; color:var(--text-dim); text-transform:uppercase; letter-spacing:1px; font-size:10px;">Criteria</th>
                    <th style="text-align:left; padding:8px 12px; color:var(--text-dim); text-transform:uppercase; letter-spacing:1px; font-size:10px; white-space:nowrap;">Controls</th>
                    <th style="text-align:left; padding:8px 12px; color:var(--text-dim); text-transform:uppercase; letter-spacing:1px; font-size:10px;">Additional Requirements</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:10px 12px; color:#4fc3f7; font-weight:700; font-family:'Rajdhani',sans-serif; font-size:15px; white-space:nowrap;">Level-I</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">All UCBs</td>
                    <td style="padding:10px 12px; color:var(--text-secondary); white-space:nowrap;">Basic + Annex I<br><span style="font-size:10px; color:var(--text-dim);">~62 controls</span></td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">Bank-specific controls per RBI circular (Oct 2018)</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border); background:rgba(255,255,255,0.015);">
                    <td style="padding:10px 12px; color:#f59e0b; font-weight:700; font-family:'Rajdhani',sans-serif; font-size:15px; white-space:nowrap;">Level-II</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">CPS Sub-member + Internet / Mobile Banking or CTS / IMPS / UPI</td>
                    <td style="padding:10px 12px; color:var(--text-secondary); white-space:nowrap;">Basic + Annex I + II<br><span style="font-size:10px; color:var(--text-dim);">~86 controls</span></td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">DLP Strategy, Anti-Phishing, VA/PT of critical apps, 2FA, WAF</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:10px 12px; color:#ef4444; font-weight:700; font-family:'Rajdhani',sans-serif; font-size:15px; white-space:nowrap;">Level-III</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">Direct CPS member / Own ATM Switch / SWIFT Interface</td>
                    <td style="padding:10px 12px; color:var(--text-secondary); white-space:nowrap;">Basic + Annex I + II + III<br><span style="font-size:10px; color:var(--text-dim);">~112 controls</span></td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">Advanced Threat Defence, Real-time Transaction Monitoring, ATM/SWIFT security, Forensics, Red Team</td>
                </tr>
                <tr style="background:rgba(168,85,247,0.04);">
                    <td style="padding:10px 12px; color:#a855f7; font-weight:700; font-family:'Rajdhani',sans-serif; font-size:15px; white-space:nowrap;">Level-IV</td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">CPS member/sub-member + (ATM Switch &amp; SWIFT) or Data Centre / Software support to other banks</td>
                    <td style="padding:10px 12px; color:var(--text-secondary); white-space:nowrap;">Basic + Annex I + II + III + IV<br><span style="font-size:10px; color:var(--text-dim);">~127 controls</span></td>
                    <td style="padding:10px 12px; color:var(--text-secondary);">C-SOC (24x7 SIEM), CERT-IN Cyber Drills, CISO appointment, IT Strategy &amp; Steering Committees, IS Committee, ACB IS Audit oversight, Board-approved IT Strategy</td>
                </tr>
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)