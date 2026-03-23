import streamlit as st
import streamlit.components.v1 as components
import os

TEMPLATES = {
    "basic": {
        "files":    [
            "Basic_Cybersecurity_Framework.xlsx",
            "Basic Cybersecurity Framework.xlsx",
            "Basic-Cybersecurity-Framework.xlsx",
            "Basic Cybersecurity framework.xlsx",
        ],
        "download": "Basic_CSF.xlsx",
        "title":    "Basic Cybersecurity Framework",
        "tag":      "MANDATORY - ALL LEVELS",
        "desc":     "Core controls applicable to every UCB. Covers governance, access control, patch management, incident response and more.",
        "controls": "48",
        "card_cls": "rbi-card-gold",
        "badge":    "badge-gold",
        "color":    "var(--gold)",
    },
    "annex1": {
        "files":    [
            "Annex_1_cybersecurity_control.xlsx",
            "Annex 1 cybersecurity control.xlsx",
            "Annex -1 cybersecurity control.xlsx",
            "Annex-1 cybersecurity control.xlsx",
            "Annex1_cybersecurity_control.xlsx",
            "Annex 1 Cybersecurity control.xlsx",
            "Annex_1_Cybersecurity_control.xlsx",
        ],
        "download": "Annex_1_Controls.xlsx",
        "title":    "Annex I - Baseline Controls",
        "tag":      "MANDATORY - ALL LEVELS",
        "desc":     "Baseline controls for all UCBs. Covers governance, privileged access, encryption, secure disposal and incident reporting to RBI.",
        "controls": "12",
        "card_cls": "rbi-card-gold",
        "badge":    "badge-blue",
        "color":    "#4fc3f7",
    },
    "annex2": {
        "files":    [
            "Annex2_Cybersecurity_.xlsx",
            "Annex2 Cybersecurity .xlsx",
            "Annex-2 Cybersecurity .xlsx",
            "Annex 2 Cybersecurity.xlsx",
            "Annex-2 Cybersecurity.xlsx",
            "Annex2_Cybersecurity.xlsx",
            "Annex2 Cybersecurity.xlsx",
        ],
        "download": "Annex_2_Controls.xlsx",
        "title":    "Annex II - Advanced Controls",
        "tag":      "LEVEL-II, III and IV",
        "desc":     "Controls for UCBs with digital channels or CPS sub-membership. Covers DLP, Anti-Phishing, WAF, SIEM, API security and Two-Factor Authentication.",
        "controls": "23",
        "card_cls": "rbi-card-amber",
        "badge":    "badge-amber",
        "color":    "#f59e0b",
    },
    "annex3": {
        "files":    [
            "Annex3_Cybersecurity.xlsx",
            "Annex3 Cybersecurity.xlsx",
            "Annex-3 Cybersecurity.xlsx",
            "Annex 3 Cybersecurity.xlsx",
            "Annex3_Cybersecurity_.xlsx",
            "Annex3 Cybersecurity .xlsx",
        ],
        "download": "Annex_3_Controls.xlsx",
        "title":    "Annex III - Enhanced Controls",
        "tag":      "LEVEL-III and IV ONLY",
        "desc":     "Advanced controls for UCBs with direct CPS membership, own ATM switch or SWIFT interface.",
        "controls": "25",
        "card_cls": "rbi-card-red",
        "badge":    "badge-red",
        "color":    "#ef4444",
    },
    "annex4": {
        "files":    [
            "Annex4_Cybersecurity_control.xlsx",
            "Annex4 Cybersecurity control.xlsx",
            "Annex-4 Cybersecurity control.xlsx",
            "Annex 4 Cybersecurity control.xlsx",
            "Annex4_Cybersecurity_Control.xlsx",
        ],
        "download": "Annex_4_Controls.xlsx",
        "title":    "Annex IV - C-SOC and IT Governance",
        "tag":      "LEVEL-IV ONLY",
        "desc":     "Mandatory for UCBs hosting Data Centres or providing software support. Covers C-SOC setup, CISO appointment, and Board-level IT governance.",
        "controls": "14",
        "card_cls": "rbi-card-blue",
        "badge":    "badge-purple",
        "color":    "#a855f7",
    },
}

LEVEL_TEMPLATES = {
    "Level-I":   ["basic", "annex1"],
    "Level-II":  ["basic", "annex1", "annex2"],
    "Level-III": ["basic", "annex1", "annex2", "annex3"],
    "Level-IV":  ["basic", "annex1", "annex2", "annex3", "annex4"],
}

LEVEL_COLORS = {
    "Level-I":   "#4fc3f7",
    "Level-II":  "#f59e0b",
    "Level-III": "#ef4444",
    "Level-IV":  "#a855f7",
}


def _log(event_type, action, detail=""):
    try:
        from module7_audit import log_event
        log_event(event_type, action, detail, module="module2")
    except Exception:
        pass


def get_base():
    return st.session_state.get("BASE_DIR", os.getcwd())


def find_file(key):
    base = get_base()
    for fname in TEMPLATES[key]["files"]:
        path = os.path.join(base, fname)
        if os.path.exists(path):
            return path, fname
    return None, TEMPLATES[key]["files"][0]


def _template_card(key):
    t = TEMPLATES[key]
    filepath, found_name = find_file(key)
    exists = filepath is not None

    html = (
        '<div class="rbi-card ' + t["card_cls"] + '" style="min-height:185px;">'
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">'
        '<div style="flex:1;min-width:0;">'
        '<div style="font-family:Rajdhani,sans-serif;font-size:17px;font-weight:700;'
        'color:var(--text-primary);line-height:1.25;">' + t["title"] + '</div>'
        '<span class="rbi-badge ' + t["badge"] + '" style="margin-top:7px;display:inline-block;">'
        + t["tag"] + '</span>'
        '</div>'
        '<div style="text-align:right;flex-shrink:0;margin-left:14px;">'
        '<div style="font-family:Rajdhani,sans-serif;font-size:34px;font-weight:700;color:'
        + t["color"] + ';line-height:1;">' + t["controls"] + '</div>'
        '<div style="font-size:9px;color:var(--text-dim);letter-spacing:1px;'
        'text-transform:uppercase;margin-top:2px;">controls</div>'
        '</div></div>'
        '<p style="color:var(--text-secondary);font-size:12px;margin:0 0 6px 0;line-height:1.65;">'
        + t["desc"] + '</p></div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    if exists:
        with open(filepath, "rb") as f:
            data = f.read()
        if st.download_button(
            "⬇️  Download  " + t["title"],
            data=data,
            file_name=t["download"],
            use_container_width=True,
            key="dl_" + key,
        ):
            _log("export", f"Template downloaded: {t['title']}", detail=t["download"])
    else:
        tried = ", ".join(t["files"][:3])
        st.error(
            "File not found. Rename your Excel file to: **" + t["files"][0] + "**  "
            "(tried: " + tried + " …)"
        )


def _instructions_html(n_tmpl, level, is_light):
    if is_light:
        bg, bdr, gold, txt, lbl, purp = "#fff", "#e2e8f0", "#8b5c0a", "#475569", "#94a3b8", "#7c3aed"
    else:
        bg, bdr, gold, txt, lbl, purp = "#08121f", "#162540", "#c9a84c", "#8a9ab8", "#6e87a8", "#a855f7"

    annex4 = ""
    if level == "Level-IV":
        annex4 = (
            '<li>For <strong style="color:' + purp + ';">Annex IV</strong>'
            ' — C-SOC must be set up, CISO appointed, and Board-level IT committees'
            ' formed before completing the checklist.</li>'
        )

    css = (
        "body{margin:0;padding:0;background:transparent;font-family:system-ui,sans-serif;}"
        ".card{background:" + bg + ";border:1px solid " + bdr + ";"
        "border-left:3px solid " + gold + ";border-radius:14px;padding:18px 24px 20px;}"
        ".lbl{font-size:9.5px;font-weight:700;letter-spacing:1.1px;"
        "text-transform:uppercase;color:" + lbl + ";margin-bottom:12px;}"
        "ol{margin:0;padding-left:20px;line-height:2.4;font-size:13px;color:" + txt + ";}"
        "li{margin-bottom:1px;}"
        ".g{color:" + gold + ";font-weight:600;}"
    )

    items = (
        '<li>Download all <span class="g">' + str(n_tmpl) + ' template(s)</span> above</li>'
        '<li>Fill the <span class="g">Control Implemented?</span> column — '
        'Fully Implemented / Partially Implemented / No / Not Applicable</li>'
        '<li>Add observations and supporting artefacts in the respective columns</li>'
        + annex4 +
        '<li>Upload completed files in <span class="g">Module 3</span>'
        ' (Dashboard) and <span class="g">Module 4</span> (Gap Analysis)</li>'
        '<li>Upload evidence files in <span class="g">Module 7</span>'
        ' (Evidence Repository)</li>'
    )

    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<style>' + css + '</style></head><body>'
        '<div class="card"><div class="lbl">Instructions</div>'
        '<ol>' + items + '</ol></div></body></html>'
    )


def show_module2():
    st.markdown(
        '<div class="rbi-page-header">'
        '<h1>&#128229; MODULE 2 — DOWNLOAD TEMPLATES</h1>'
        '<p>Download the control assessment templates applicable to your bank compliance tier</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Ensure bank profile is persisted whenever this page is visited ────────
    # This fixes the bug where navigating to Module 2 and back loses Module 1 data
    _persist_bank_profile()

    level = st.session_state.get("bank_level")
    if not level:
        st.warning("⚠️  Please complete Module 1 first to identify your compliance level.")
        if st.button("→ Go to Module 1 (Level Identification)", key="m2_goto_m1"):
            st.session_state["active_module"] = 0
            st.rerun()
        return

    bank_name  = st.session_state.get("bank_name", "Your Bank")
    applicable = LEVEL_TEMPLATES.get(level, ["basic", "annex1"])
    lc         = LEVEL_COLORS.get(level, "var(--gold)")
    total_ctrl = sum(int(TEMPLATES[k]["controls"]) for k in applicable)

    _log("view", f"Templates page viewed — {level}", detail=bank_name)

    # ── Stats strip ────────────────────────────────────────────
    level_badge_cls = {
        "Level-I": "badge-blue", "Level-II": "badge-amber",
        "Level-III": "badge-red", "Level-IV": "badge-purple",
    }.get(level, "badge-gold")

    st.markdown(f"""
    <div class="rbi-stat-strip" style="margin-bottom:22px;">
        <div class="rbi-stat-item">
            <div class="stat-label">Bank</div>
            <div style="font-family:Rajdhani,sans-serif;font-size:15px;
                        color:var(--text-primary);font-weight:600;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
                        max-width:160px;" title="{bank_name}">{bank_name}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Compliance Tier</div>
            <div style="font-family:Rajdhani,sans-serif;font-size:22px;
                        color:{lc};font-weight:700;">{level}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Total Controls</div>
            <div class="stat-value">{total_ctrl}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Templates Required</div>
            <div class="stat-value" style="color:{lc};">{len(applicable)}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Status</div>
            <div style="margin-top:4px;">
                <span class="rbi-badge {level_badge_cls}">LEVEL CONFIRMED</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="rbi-section-title">Applicable Templates</div>', unsafe_allow_html=True)

    # Missing files warning
    base = get_base()
    missing_files = []
    for k in applicable:
        fp, fn = find_file(k)
        if not fp:
            missing_files.append(TEMPLATES[k]["files"][0])
    if missing_files:
        st.warning(
            "Some Excel files were not found. Place them in: **" + base + "**"
        )
        for mf in missing_files:
            st.code(mf)

    # Row 1 — Basic + Annex I (always shown)
    c1, c2 = st.columns(2)
    with c1:
        _template_card("basic")
    with c2:
        _template_card("annex1")

    # Row 2 — Annex II + III
    if level in ["Level-II", "Level-III", "Level-IV"]:
        c3, c4 = st.columns(2)
        with c3:
            _template_card("annex2")
        with c4:
            if level in ["Level-III", "Level-IV"]:
                _template_card("annex3")
            else:
                st.markdown(
                    '<div class="rbi-card" style="min-height:185px;display:flex;'
                    'align-items:center;justify-content:center;flex-direction:column;'
                    'gap:10px;opacity:0.35;border-style:dashed;">'
                    '<div style="font-size:28px;">🔒</div>'
                    '<div style="font-size:12px;color:var(--text-dim);text-align:center;">'
                    'Annex III not required<br>for Level-II banks</div></div>',
                    unsafe_allow_html=True,
                )

    # Row 3 — Annex IV
    if level == "Level-IV":
        c5, c6 = st.columns(2)
        with c5:
            _template_card("annex4")
        with c6:
            st.markdown(
                '<div class="rbi-card rbi-card-blue" style="min-height:185px;display:flex;'
                'align-items:center;justify-content:center;flex-direction:column;gap:12px;">'
                '<div style="font-size:36px;">🏆</div>'
                '<div style="font-family:Rajdhani,sans-serif;font-size:16px;font-weight:700;'
                'color:var(--text-primary);text-align:center;">Full Framework Applied</div>'
                '<div style="font-size:11.5px;color:var(--text-dim);text-align:center;line-height:1.7;">'
                'All 5 templates mandatory<br>for Level-IV UCBs</div>'
                '<span class="rbi-badge badge-purple">LEVEL-IV ONLY</span></div>',
                unsafe_allow_html=True,
            )

    # ── Instructions ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="rbi-section-title">Instructions</div>', unsafe_allow_html=True)
    is_light = st.session_state.get("theme", "dark") == "light"
    html_src = _instructions_html(len(applicable), level, is_light)
    components.html(html_src, height=(270 if level == "Level-IV" else 235), scrolling=False)

    # ── Next step nudge ────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="rbi-card" style="padding:14px 20px;display:flex;
         align-items:center;gap:14px;border-left:3px solid var(--gold);">
        <div style="font-size:20px;">💡</div>
        <div style="font-size:12.5px;color:var(--text-secondary);line-height:1.6;">
            After filling all <strong style="color:var(--gold);">{total_ctrl} controls</strong>
            in your {len(applicable)} template(s), go to
            <strong>Module 3</strong> (Compliance Dashboard) to upload and analyse your results.
        </div>
    </div>
    """, unsafe_allow_html=True)


def _persist_bank_profile():
    """
    Ensure the bank profile is saved to DB whenever Module 2 is visited.
    This prevents data loss when users navigate away from Module 1
    before the auto-save fires.
    """
    uid   = st.session_state.get("user_id")
    bank  = st.session_state.get("bank_name", "")
    level = st.session_state.get("bank_level", "")
    flags = st.session_state.get("module1_flags", {})
    if uid and (bank or level):
        try:
            from db_store import save_bank_profile
            save_bank_profile(uid, bank, level, flags)
        except Exception:
            pass