import streamlit as st
import os

# Exact filenames as they appear on disk
TEMPLATES = {
    "basic": {
        "file":     "Basic Cybersecurity Framework.xlsx",
        "download": "Basic_CSF.xlsx",
        "title":    "Basic Cybersecurity Framework",
        "tag":      "MANDATORY · ALL LEVELS",
        "desc":     "Core cybersecurity controls applicable to every UCB regardless of tier. Covers governance, access control, patch management, incident response, and more.",
        "controls": "49 Controls",
        "card_cls": "rbi-card-gold",
        "badge":    "badge-gold",
        "icon":     "📄",
    },
    "annex1": {
        "file":     "Annex -1 cybersecurity control.xlsx",
        "download": "Annex_1.xlsx",
        "title":    "Annex I — Baseline Controls",
        "tag":      "MANDATORY · ALL LEVELS",
        "desc":     "Baseline security controls required for all UCBs. Supplements the Basic Framework with additional governance and operational security requirements.",
        "controls": "13 Controls",
        "card_cls": "rbi-card-gold",
        "badge":    "badge-blue",
        "icon":     "📘",
    },
    "annex2": {
        "file":     "Annex-2 Cybersecurity .xlsx",
        "download": "Annex_2.xlsx",
        "title":    "Annex II — Advanced Controls",
        "tag":      "LEVEL-II, III & IV",
        "desc":     "Additional controls for UCBs offering digital channels or holding CPS sub-membership. Covers network security, data protection, and digital banking security.",
        "controls": "24 Controls",
        "card_cls": "rbi-card-amber",
        "badge":    "badge-amber",
        "icon":     "📗",
    },
    "annex3": {
        "file":     "Annex-3 Cybersecurity.xlsx",
        "download": "Annex_3.xlsx",
        "title":    "Annex III — Enhanced Controls",
        "tag":      "LEVEL-III & IV ONLY",
        "desc":     "Advanced security controls for UCBs with direct CPS membership, own ATM switch, or SWIFT interface. Includes advanced threat defence and risk-based transaction monitoring.",
        "controls": "26 Controls",
        "card_cls": "rbi-card-red",
        "badge":    "badge-red",
        "icon":     "📕",
    },
}


def get_filepath(filename):
    base = st.session_state.get("BASE_DIR", os.getcwd())
    return os.path.join(base, filename)


def _template_card(key):
    t        = TEMPLATES[key]
    filepath = get_filepath(t["file"])

    st.markdown(f"""
    <div class="rbi-card {t['card_cls']}">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
            <div>
                <div style="font-family:'Rajdhani',sans-serif; font-size:18px; font-weight:700;
                            color:var(--text-primary);">{t['icon']} {t['title']}</div>
                <span class="rbi-badge {t['badge']}" style="margin-top:5px; display:inline-block;">{t['tag']}</span>
            </div>
            <div style="text-align:right;">
                <div class="rbi-label">CONTROLS</div>
                <div style="font-family:'Rajdhani',sans-serif; font-size:20px; font-weight:700;
                            color:var(--gold);">{t['controls']}</div>
            </div>
        </div>
        <p style="color:var(--text-secondary); font-size:13px; margin:0 0 12px 0; line-height:1.5;">{t['desc']}</p>
    </div>
    """, unsafe_allow_html=True)

    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            st.download_button(
                f"⬇️  Download {t['title']}",
                f,
                file_name=t["download"],
                width="stretch",
                key=f"dl_{key}"
            )
    else:
        st.error(f"❌ File not found: `{t['file']}` — looked in: `{filepath}`")


def show_module2():

    st.markdown("""
    <div class="rbi-page-header">
        <h1>📥 MODULE 2 — DOWNLOAD TEMPLATES</h1>
        <p>Download the control assessment templates applicable to your bank's compliance tier</p>
    </div>
    """, unsafe_allow_html=True)

    level = st.session_state.get("bank_level")

    if not level:
        st.warning("⚠️ Please complete Module 1 first to identify your compliance level.")
        return

    bank_name = st.session_state.get("bank_name", "Your Bank")

    applicable = {
        "Level-I":   ["basic", "annex1"],
        "Level-II":  ["basic", "annex1", "annex2"],
        "Level-III": ["basic", "annex1", "annex2", "annex3"],
        "Level-IV":  ["basic", "annex1", "annex2", "annex3"],
    }.get(level, ["basic", "annex1"])

    total_controls = sum(int(TEMPLATES[k]["controls"].split()[0]) for k in applicable)
    level_color = {
        "Level-I":   "#4fc3f7",
        "Level-II":  "#f59e0b",
        "Level-III": "#ef4444",
        "Level-IV":  "#a855f7",
    }.get(level, "#c9a84c")

    st.markdown(f"""
    <div class="rbi-card" style="margin-bottom:20px; display:flex; flex-wrap:wrap; align-items:center; gap:24px;">
        <div>
            <div class="rbi-label">Bank</div>
            <div style="font-family:'Rajdhani',sans-serif; font-size:20px; color:var(--text-primary); font-weight:600;">{bank_name}</div>
        </div>
        <div style="width:1px; height:40px; background:var(--border);"></div>
        <div>
            <div class="rbi-label">Compliance Tier</div>
            <div style="font-family:'Rajdhani',sans-serif; font-size:20px; color:{level_color}; font-weight:700;">{level}</div>
        </div>
        <div style="width:1px; height:40px; background:var(--border);"></div>
        <div>
            <div class="rbi-label">Total Controls</div>
            <div style="font-family:'Rajdhani',sans-serif; font-size:20px; color:var(--gold); font-weight:700;">{total_controls}</div>
        </div>
        <div style="width:1px; height:40px; background:var(--border);"></div>
        <div>
            <div class="rbi-label">Templates Required</div>
            <div style="font-family:'Rajdhani',sans-serif; font-size:20px; color:var(--text-primary); font-weight:600;">{len(applicable)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="rbi-section-title">Applicable Templates</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        _template_card("basic")
    with col2:
        _template_card("annex1")

    if level in ["Level-II", "Level-III", "Level-IV"]:
        col3, col4 = st.columns(2)
        with col3:
            _template_card("annex2")
        if level in ["Level-III", "Level-IV"]:
            with col4:
                _template_card("annex3")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="rbi-card" style="margin-bottom:12px; font-size:13px; color:var(--text-secondary);">
        <div class="rbi-label" style="margin-bottom:10px;">INSTRUCTIONS</div>
        <ol style="margin:0; padding-left:18px; line-height:2.2;">
            <li>Download all applicable templates above</li>
            <li>Fill the <strong style="color:var(--gold);">"Control Implemented?"</strong> column:
                Compliant / Partially Compliant / Not Compliant / Not Applicable</li>
            <li>Add observations and supporting artefacts in the respective columns</li>
            <li>Save and upload in <strong style="color:var(--gold);">Module 3</strong> (Dashboard) and <strong style="color:var(--gold);">Module 4</strong> (Gap Analysis)</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)