import streamlit as st
import streamlit.components.v1 as components
import os

st.set_page_config(
    page_title="RBI CSF Compliance Tool",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── BASE_DIR ───────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
st.session_state["BASE_DIR"] = BASE_DIR

# ── Theme + active module state ────────────────────────────────
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
if "active_module" not in st.session_state:
    st.session_state["active_module"] = 0
if "audit_log" not in st.session_state:
    st.session_state["audit_log"] = []

is_light = st.session_state["theme"] == "light"

# ══════════════════════════════════════════════════════════════
#  DARK THEME
# ══════════════════════════════════════════════════════════════
DARK_CSS = """
:root {
    --bg-base:        #04090f;
    --bg-card:        #0a1628;
    --bg-card-hover:  #0f1f3d;
    --border:         #1a2f52;
    --border-glow:    #1e4080;
    --gold:           #c9a84c;
    --gold-light:     #e8c97a;
    --gold-dim:       rgba(201,168,76,0.12);
    --blue-ice:       #4fc3f7;
    --compliant:      #22c55e;
    --partial:        #f59e0b;
    --noncompliant:   #ef4444;
    --na:             #64748b;
    --text-primary:   #e8edf5;
    --text-secondary: #7a92b4;
    --text-dim:       #3d5478;
    --divider:        #1a2f52;
    --input-bg:       #0a1628;
}
.stApp                              { background-color: #04090f !important; }
section[data-testid="stSidebar"]    { background: #060e1c !important; border-right: 1px solid #1a2f52 !important; }
header[data-testid="stHeader"]      { background: #04090f !important; }
[data-testid="stMetricValue"]       { color: #c9a84c !important; }
[data-testid="metric-container"]    { background: #0a1628 !important; border-color: #1a2f52 !important; }
.stTextInput input                  { background: #0a1628 !important; color: #e8edf5 !important; border-color: #1a2f52 !important; }
.stCheckbox label, .stCheckbox label span { color: #e8edf5 !important; }
.stProgress > div                   { background: #1a2f52 !important; }
[data-baseweb="select"] > div       { background: #0a1628 !important; border-color: #1a2f52 !important; color: #e8edf5 !important; }
[data-baseweb="menu"]               { background: #0a1628 !important; }
[data-baseweb="menu"] li            { color: #e8edf5 !important; }
.stMultiSelect [data-baseweb="tag"] { background: #1a2f52 !important; color: #e8edf5 !important; }
section[data-testid="stSidebar"] .stRadio label span { color: #94a3b8 !important; }
.sidebar-brand-title    { color: #c9a84c !important; }
.sidebar-brand-subtitle { color: #3d5478 !important; }
.sidebar-section-label  { color: #3d5478 !important; }
.sidebar-footer         { color: #3d5478 !important; }
"""

# ══════════════════════════════════════════════════════════════
#  LIGHT THEME
# ══════════════════════════════════════════════════════════════
LIGHT_CSS = """
:root {
    --bg-base:        #f5f7fa;
    --bg-card:        #ffffff;
    --bg-card-hover:  #f8fafc;
    --border:         #e2e8f0;
    --border-glow:    #7c4f0a;
    --gold:           #8b5c0a;
    --gold-light:     #a0650e;
    --gold-dim:       rgba(139,92,10,0.08);
    --blue-ice:       #0369a1;
    --compliant:      #15803d;
    --partial:        #b45309;
    --noncompliant:   #b91c1c;
    --na:             #64748b;
    --text-primary:   #1e293b;
    --text-secondary: #475569;
    --text-dim:       #94a3b8;
    --divider:        #e2e8f0;
    --input-bg:       #ffffff;
}

.stApp, .block-container            { background-color: #f5f7fa !important; }
header[data-testid="stHeader"]      { background: linear-gradient(180deg,#ffffff 0%,#f5f7fa 100%) !important;
                                      border-bottom: 1px solid #e2e8f0 !important; }
header[data-testid="stHeader"] *    { color: #334155 !important; }
header[data-testid="stHeader"] button svg { fill: #475569 !important; }

section[data-testid="stSidebar"]    { background: linear-gradient(180deg,#ffffff 0%,#faf9f7 100%) !important;
                                      border-right: 1px solid #e8e3d8 !important;
                                      box-shadow: 2px 0 12px rgba(0,0,0,0.04) !important; }
section[data-testid="stSidebar"] *  { font-family: 'IBM Plex Sans', sans-serif !important; }

.material-symbols-rounded,
span.material-symbols-rounded,
[data-testid="stSidebar"] .material-symbols-rounded,
[data-testid="collapsedControl"] span,
header[data-testid="stHeader"] .material-symbols-rounded,
header[data-testid="stHeader"] button span { font-family: 'Material Symbols Rounded' !important; }

section[data-testid="stSidebar"] hr { border-color: #e8e3d8 !important; opacity:1 !important; }
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stRadio label span,
section[data-testid="stSidebar"] .stRadio label p   { color: #64748b !important; font-size:13px !important; }
section[data-testid="stSidebar"] .stRadio label:hover,
section[data-testid="stSidebar"] .stRadio label:hover span { color: #8b5c0a !important; }
section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg,#8b5c0a 0%,#a0650e 100%) !important;
    color: #ffffff !important; border: none !important;
    box-shadow: 0 2px 8px rgba(139,92,10,0.20) !important; font-weight:600 !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg,#7c4f0a 0%,#8b5c0a 100%) !important;
    box-shadow: 0 4px 12px rgba(139,92,10,0.30) !important; transform:translateY(-1px) !important;
}

.stApp .block-container p,
.stApp .block-container li,
.stApp .block-container span,
.stApp .block-container div,
.stApp .block-container label       { color: #1e293b; }

[data-testid="metric-container"]    { background:#ffffff !important; border:1px solid #e2e8f0 !important;
                                      box-shadow:0 1px 3px rgba(0,0,0,0.05) !important; border-radius:16px !important; }
[data-testid="metric-container"]:hover { box-shadow:0 6px 20px rgba(0,0,0,0.09) !important; border-color:#cbd5e1 !important; }
[data-testid="stMetricValue"]       { color: #8b5c0a !important; }
[data-testid="stMetricLabel"]       { color: #64748b !important; }

.stTextInput input                  { background:#ffffff !important; color:#1e293b !important;
                                      border:1.5px solid #e2e8f0 !important; border-radius:10px !important; }
.stTextInput input::placeholder     { color: #94a3b8 !important; }
.stTextInput input:focus            { border-color:#8b5c0a !important; box-shadow:0 0 0 3px rgba(139,92,10,0.10) !important; }

.stCheckbox label, .stCheckbox label span,
.stCheckbox label p                 { color: #1e293b !important; font-size:14px !important; }
.stProgress > div                   { background: #e2e8f0 !important; border-radius:8px !important; }

[data-testid="stFileUploader"]      { background:#ffffff !important; border:2px dashed #cbd5e1 !important; border-radius:16px !important; }
[data-testid="stFileUploader"]:hover { border-color:#8b5c0a !important; background:#fefcf8 !important; }
[data-testid="stFileUploader"] *    { color: #475569 !important; }

[data-testid="stDataFrame"]         { border:1px solid #e2e8f0 !important; background:#ffffff !important; border-radius:14px !important; }

.stAlert                            { background:#fffbeb !important; border-color:#f59e0b !important; border-radius:12px !important; }
.stAlert p, .stAlert span           { color: #1e293b !important; }

.stApp .block-container [data-baseweb="select"] > div { background:#ffffff !important; border:1.5px solid #e2e8f0 !important; color:#1e293b !important; border-radius:10px !important; }
.stApp .block-container [data-baseweb="menu"]         { background:#ffffff !important; border:1px solid #e2e8f0 !important; box-shadow:0 4px 16px rgba(0,0,0,0.08) !important; border-radius:10px !important; }
.stApp .block-container [data-baseweb="menu"] li      { color: #1e293b !important; }
.stApp .block-container [data-baseweb="menu"] li:hover { background: #fef8f0 !important; }
.stMultiSelect [data-baseweb="tag"] { background:#fef3d6 !important; color:#8b5c0a !important; border:1px solid #e8d5a8 !important; }
[data-baseweb="select"] [data-baseweb="single-value"],
[data-baseweb="select"] [data-baseweb="placeholder"]  { color: #1e293b !important; }

.stApp .block-container .stDownloadButton > button,
.stApp .block-container .stButton > button            { background:#ffffff !important; color:#8b5c0a !important;
                                      border:1.5px solid #8b5c0a !important; border-radius:10px !important; font-weight:600 !important; }
.stApp .block-container .stDownloadButton > button:hover,
.stApp .block-container .stButton > button:hover      { background:#fef8f0 !important; box-shadow:0 2px 8px rgba(139,92,10,0.12) !important; transform:translateY(-1px) !important; }

.rbi-card           { background:#ffffff !important; border:1px solid #e2e8f0 !important; box-shadow:0 1px 3px rgba(0,0,0,0.04) !important; }
.rbi-card:hover     { box-shadow:0 6px 20px rgba(0,0,0,0.08) !important; border-color:#cbd5e1 !important; }
.rbi-card p, .rbi-card div, .rbi-card span { color: #1e293b; }
.rbi-card table, .rbi-card table td { color: #475569 !important; }
.rbi-card table th  { color: #94a3b8 !important; }
.rbi-page-header    { background:linear-gradient(135deg,#ffffff 0%,#fefcf8 100%) !important;
                      border:1px solid #e2e8f0 !important; border-left:4px solid #8b5c0a !important;
                      box-shadow:0 2px 8px rgba(0,0,0,0.04) !important; }
.rbi-page-header h1 { color: #1e293b !important; }
.rbi-page-header p  { color: #475569 !important; }
.rbi-section-title  { color: #475569 !important; border-bottom-color:#e2e8f0 !important; }
.rbi-label          { color: #94a3b8 !important; }
.rbi-info-item .value { color: #1e293b !important; }

.rbi-stat-strip              { background:#ffffff !important; border:1px solid #e2e8f0 !important; }
.rbi-stat-item               { border-right-color:#e2e8f0 !important; }
.rbi-stat-item:hover         { background:#f8fafc !important; }
.rbi-stat-item .stat-label   { color:#94a3b8 !important; }
.rbi-stat-item .stat-value   { color:#8b5c0a !important; }

.audit-event                 { background:#ffffff !important; border:1px solid #e2e8f0 !important; }
.audit-event:hover           { border-color:#cbd5e1 !important; }
.audit-event .ae-action      { color:#1e293b !important; }
.audit-event .ae-time        { color:#94a3b8 !important; }
.audit-event .ae-detail      { color:#475569 !important; }
.audit-timeline::before      { background:linear-gradient(to bottom, #8b5c0a, #e2e8f0) !important; }
.audit-event::before         { border-color:#f5f7fa !important; }

.sidebar-bank-card  { background:#f8f5f0 !important; border:1px solid #e8e3d8 !important; }
.sidebar-bank-card .bank-name  { color: #8b5c0a !important; }
.sidebar-bank-card .bank-level { color: #64748b !important; }
.sidebar-brand-title    { color: #8b5c0a !important; }
.sidebar-brand-subtitle { color: #94a3b8 !important; }
.sidebar-section-label  { color: #94a3b8 !important; }
.sidebar-footer         { color: #94a3b8 !important; }
.step-indicator         { color: #94a3b8 !important; }
.step-indicator.done    { color: #15803d !important; background: rgba(21,128,61,0.08) !important; }
.step-indicator.active  { color: #8b5c0a !important; background: rgba(139,92,10,0.08) !important; border-left-color:#8b5c0a !important; }

::-webkit-scrollbar-track       { background:#f5f7fa; }
::-webkit-scrollbar-thumb       { background:#cbd5e1; border-radius:4px; }
::-webkit-scrollbar-thumb:hover { background:#8b5c0a; }
"""

# ══════════════════════════════════════════════════════════════
#  LOCK SIDEBAR
# ══════════════════════════════════════════════════════════════
LOCK_SIDEBAR_CSS = """
button[data-testid="collapsedControl"],
[data-testid="collapsedControl"],
button[kind="header"][aria-label="Close sidebar"],
section[data-testid="stSidebar"] button[aria-label="Close sidebar"],
section[data-testid="stSidebar"] > div:first-child > div > button {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}

header[data-testid="stHeader"] button[aria-label="Open sidebar"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}

section[data-testid="stSidebar"] {
    transform: none !important;
    visibility: visible !important;
    display: block !important;
    min-width: 272px !important;
    width: 272px !important;
}
"""

theme_css = LIGHT_CSS if is_light else DARK_CSS

# ── Load base CSS ──────────────────────────────────────────────
css_path = os.path.join(BASE_DIR, "style.css")
base_css  = ""
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        base_css = f.read()

st.markdown(f"<style>{base_css}\n{theme_css}\n{LOCK_SIDEBAR_CSS}</style>", unsafe_allow_html=True)

# ── Sidebar lock JS ────────────────────────────────────────────
components.html("""
<script>
(function () {
    function lockSidebar() {
        var doc     = window.parent.document;
        var sidebar = doc.querySelector('section[data-testid="stSidebar"]');
        if (!sidebar) return;
        if (sidebar.getAttribute('aria-expanded') === 'false')
            sidebar.setAttribute('aria-expanded', 'true');
        var toggleBtns = doc.querySelectorAll(
            'button[data-testid="collapsedControl"], ' +
            '[data-testid="collapsedControl"], ' +
            '[data-testid="stSidebarCollapsedControl"], ' +
            'header button[aria-label="Open sidebar"], ' +
            'section[data-testid="stSidebar"] button[aria-label="Close sidebar"]'
        );
        toggleBtns.forEach(function (btn) {
            btn.style.setProperty('display',        'none',   'important');
            btn.style.setProperty('visibility',     'hidden', 'important');
            btn.style.setProperty('pointer-events', 'none',   'important');
        });
    }
    function init() {
        lockSidebar();
        new MutationObserver(lockSidebar).observe(
            window.parent.document.body,
            { attributes: true, subtree: true, childList: true }
        );
    }
    window.parent.document.body
        ? init()
        : window.parent.addEventListener('DOMContentLoaded', init);
    var n = 0;
    var iv = setInterval(function () { lockSidebar(); if (++n >= 30) clearInterval(iv); }, 200);
}());
</script>
""", height=0, scrolling=False)

# ── Light theme checkbox fixer ─────────────────────────────────
if is_light:
    components.html("""
    <script>
    (function() {
        var CHECK_BG_UNCHECKED = '#ffffff';
        var CHECK_BORDER       = '#94a3b8';
        var CHECK_BG_CHECKED   = '#8b5c0a';
        var CHECK_TICK         = '#ffffff';
        function patchOne(el) {
            if (!el.closest) return;
            var container = el.closest('[data-baseweb="checkbox"]');
            if (!container) return;
            var box = container.querySelector('div[style]');
            if (!box) return;
            var input = container.querySelector('input[type="checkbox"]');
            var isChecked = input ? input.checked : false;
            if (isChecked) {
                box.style.setProperty('background-color', CHECK_BG_CHECKED, 'important');
                box.style.setProperty('border-color',     CHECK_BG_CHECKED, 'important');
            } else {
                box.style.setProperty('background-color', CHECK_BG_UNCHECKED, 'important');
                box.style.setProperty('border-color',     CHECK_BORDER,       'important');
            }
            box.style.setProperty('border-radius', '4px',   'important');
            box.style.setProperty('border-width',  '2px',   'important');
            box.style.setProperty('border-style',  'solid', 'important');
            var svg = box.querySelector('svg');
            if (svg) {
                svg.style.setProperty('fill',  CHECK_TICK, 'important');
                svg.style.setProperty('color', CHECK_TICK, 'important');
            }
        }
        function patchAll() {
            window.parent.document.querySelectorAll('[data-baseweb="checkbox"]').forEach(function(c) {
                patchOne(c.querySelector('div') || c);
            });
        }
        function init() {
            new MutationObserver(patchAll).observe(window.parent.document.body,
                { childList:true, subtree:true, attributes:true, attributeFilter:['style','class'] });
            patchAll();
        }
        window.parent.document.body ? init() : window.parent.addEventListener('DOMContentLoaded', init);
        var r = 0;
        var iv = setInterval(function () { patchAll(); if (++r > 30) clearInterval(iv); }, 500);
    })();
    </script>
    """, height=0, scrolling=False)

# ── Import Modules ─────────────────────────────────────────────
import module1
import module2
import module3
import module4_gap  as module4
import module5
import module7_audit as module7

from module7_audit import log_event

# ── Nav list ──────────────────────────────────────────────────
NAV_OPTIONS = [
    "01  Level Identification",
    "02  Download Templates",
    "03  Compliance Dashboard",
    "04  Gap Analysis",
    "05  Gap Analysis Report",
    "06  Audit Trail Log",
]

# ── Completed steps ────────────────────────────────────────────
completed = []
if st.session_state.get("bank_level"):                  completed.append(1)
if st.session_state.get("compliance_summary"):           completed.append(3)
if st.session_state.get("gap_dataframe") is not None:   completed.append(4)

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:

    st.markdown("""
    <div style="padding:8px 0 14px 0;">
        <div class="sidebar-brand-title"
             style="font-family:'Rajdhani',sans-serif;font-size:22px;font-weight:700;letter-spacing:1.5px;">
            🏦 RBI CSF Tool
        </div>
        <div class="sidebar-brand-subtitle"
             style="font-size:10px;margin-top:4px;letter-spacing:1.2px;text-transform:uppercase;">
            Cybersecurity Compliance Assessment
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Theme toggle
    toggle_label = "☀️  Light Theme" if not is_light else "🌙  Dark Theme"
    if st.button(toggle_label, width="stretch", key="theme_btn"):
        st.session_state["theme"] = "light" if not is_light else "dark"
        log_event("change", f"Theme switched to {'Light' if not is_light else 'Dark'}", module="app")
        st.rerun()

    st.divider()

    # Bank card
    bank  = st.session_state.get("bank_name",  "Not Identified")
    level = st.session_state.get("bank_level", "Not Set")

    level_badge = {
        "Level-I":   '<span class="rbi-badge badge-blue">LEVEL-I</span>',
        "Level-II":  '<span class="rbi-badge badge-amber">LEVEL-II</span>',
        "Level-III": '<span class="rbi-badge badge-red">LEVEL-III</span>',
        "Level-IV":  '<span class="rbi-badge badge-red" style="color:#a855f7;border-color:#a855f7;">LEVEL-IV</span>',
    }.get(level, '<span class="rbi-badge badge-gold">UNSET</span>')

    display_bank = bank if bank and bank != "Not Identified" else "Not Identified"

    st.markdown(f"""
    <div class="sidebar-bank-card">
        <div class="bank-name" title="{display_bank}">{display_bank}</div>
        <div class="bank-level" style="margin-top:6px;">{level_badge}</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Navigation
    st.markdown('<div class="sidebar-section-label">Modules</div>', unsafe_allow_html=True)

    menu = st.radio(
        "Navigation",
        NAV_OPTIONS,
        index=st.session_state["active_module"],
        key="nav_radio",
        label_visibility="collapsed",
    )
    st.session_state["active_module"] = NAV_OPTIONS.index(menu)

    st.divider()

    # Progress tracker with active state
    st.markdown('<div class="sidebar-section-label">Progress</div>', unsafe_allow_html=True)

    active_idx = st.session_state["active_module"]

    STEPS = [
        (1, "Level Identification",  0),
        (2, "Templates",             1),
        (3, "Dashboard",             2),
        (4, "Gap Analysis",          3),
        (5, "Gap Report",            4),
        (7, "Audit Trail",           5),
    ]

    for num, lbl, nav_i in STEPS:
        icon     = "✓" if num in completed else "○"
        is_done  = num in completed
        is_active = nav_i == active_idx
        cls = "done" if is_done else ("active" if is_active else "")
        st.markdown(
            f'<div class="step-indicator {cls}">{icon}&nbsp; {lbl}</div>',
            unsafe_allow_html=True,
        )

    # Audit log pill in sidebar
    audit_count = len(st.session_state.get("audit_log", []))
    if audit_count > 0:
        st.markdown(f"""
        <div style="margin-top:10px; text-align:center;">
            <span class="rbi-badge badge-gold">📋 {audit_count} events logged</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-footer">RBI Graded Approach Framework<br>Cybersecurity Assessment Tool</div>',
        unsafe_allow_html=True,
    )


# ── Routing ────────────────────────────────────────────────────
if   "Level Identification" in menu:
    module1.show_module1()
elif "Download Templates"   in menu:
    module2.show_module2()
elif "Compliance Dashboard" in menu:
    module3.show_module3()
elif "Gap Analysis Report"  in menu:
    module5.show_module5()
elif "Gap Analysis"         in menu:
    module4.show_module4()
elif "Audit Trail"          in menu:
    module7.show_module7()