"""
App.py — RBI CSF Compliance Tool
Main entry point with:
  • Auth gate (login / register)
  • Session load from DB on first login
  • Transparent auto-save to DB after every render cycle
  • Module routing
"""

import streamlit as st
import streamlit.components.v1 as components
import os

st.set_page_config(
    page_title="RBI CSF Compliance Tool",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── BASE_DIR ───────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
st.session_state["BASE_DIR"] = BASE_DIR

# ── Initialise DB ──────────────────────────────────────────────
from db_store import init_db
init_db()

# ── Auth gate ─────────────────────────────────────────────────
from auth import show_auth, render_change_password_widget
if not show_auth():
    st.stop()

# ── Load session from DB once after login ──────────────────────
if not st.session_state.get("_session_loaded", True):
    from db_store import load_full_session
    _uid   = st.session_state["user_id"]
    _saved = load_full_session(_uid)
    for k, v in _saved.items():
        st.session_state[k] = v
    if st.session_state.get("_prefill_bank_name") and not st.session_state.get("bank_name"):
        st.session_state["bank_name"] = st.session_state.pop("_prefill_bank_name")
    st.session_state["_snap_bank"]       = st.session_state.get("bank_name", "")
    st.session_state["_snap_level"]      = st.session_state.get("bank_level", "")
    st.session_state["_snap_compliance"] = str(st.session_state.get("compliance_summary", ""))
    st.session_state["_snap_gaps"]       = id(st.session_state.get("gap_dataframe"))
    st.session_state["_snap_ev_count"]   = sum(
        len(v) for v in st.session_state.get("evidence_store", {}).values()
    )
    st.session_state["_session_loaded"]  = True
    st.rerun()

# ── Patch log_event to also persist every event to DB ─────────
import module7_audit as _m7
_orig_log = _m7.log_event

def _db_log(event_type, action, detail="", module="app"):
    _orig_log(event_type, action, detail, module)
    uid = st.session_state.get("user_id")
    if uid:
        try:
            from db_store import save_audit_event
            from datetime import datetime
            save_audit_event(uid, {
                "timestamp": datetime.now().strftime("%d %b %Y  %H:%M:%S"),
                "type": event_type, "action": action,
                "detail": detail, "module": module,
            })
        except Exception:
            pass

_m7.log_event = _db_log
from module7_audit import log_event

# ══════════════════════════════════════════════════════════════
#  THEME CSS
# ══════════════════════════════════════════════════════════════
if "theme"         not in st.session_state: st.session_state["theme"]         = "dark"
if "active_module" not in st.session_state: st.session_state["active_module"] = 0

is_light = st.session_state["theme"] == "light"

DARK_CSS = """
:root {
    --bg-base:#04090f;--bg-card:#08121f;--bg-card-hover:#0d1a30;
    --border:#162540;--border-glow:#1e3a6e;
    --gold:#c9a84c;--gold-light:#e2b95e;--gold-dim:rgba(201,168,76,0.10);
    --blue-ice:#4fc3f7;--compliant:#22c55e;--partial:#f59e0b;
    --noncompliant:#ef4444;--na:#64748b;
    --text-primary:#dde4f0;--text-secondary:#6e87a8;--text-dim:#2e4668;
    --divider:#162540;--input-bg:#06101c;
}
.stApp{background-color:#04090f!important;}
.block-container{background-color:#04090f!important;}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#060d1a 0%,#04090f 100%)!important;border-right:1px solid #162540!important;}
header[data-testid="stHeader"]{background:#04090f!important;border-bottom:1px solid #162540!important;}
[data-testid="stMetricValue"]{color:#c9a84c!important;}
[data-testid="metric-container"]{background:#08121f!important;border-color:#162540!important;}
.stTextInput input{background:#06101c!important;color:#dde4f0!important;border-color:#162540!important;}
.stCheckbox label,.stCheckbox label span{color:#dde4f0!important;}
.stProgress > div{background:#162540!important;}
[data-baseweb="select"]>div{background:#06101c!important;border-color:#162540!important;color:#dde4f0!important;}
[data-baseweb="menu"]{background:#08121f!important;border:1px solid #162540!important;}
[data-baseweb="menu"] li{color:#dde4f0!important;}
.stMultiSelect [data-baseweb="tag"]{background:#162540!important;color:#dde4f0!important;}
section[data-testid="stSidebar"] .stRadio label span{color:#6e87a8!important;}
.sidebar-brand-title{color:#c9a84c!important;}
.sidebar-brand-subtitle,.sidebar-section-label,.sidebar-footer{color:#2e4668!important;}
.stTabs [data-baseweb="tab-list"]{background:#08121f!important;border-radius:13px!important;padding:5px!important;gap:4px!important;border:1px solid #162540!important;}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:#6e87a8!important;border-radius:9px!important;font-size:12.5px!important;}
.stTabs [aria-selected="true"]{background:rgba(201,168,76,0.10)!important;color:#c9a84c!important;font-weight:700!important;border:1px solid rgba(201,168,76,0.2)!important;}
.stTabs [data-baseweb="tab-border"],.stTabs [data-baseweb="tab-highlight"]{display:none!important;}
[data-testid="stFileUploader"]{background:#06101c!important;border:2px dashed #1e3a6e!important;border-radius:14px!important;}
"""

LIGHT_CSS = """
:root {
    --bg-base:#f5f7fa;--bg-card:#ffffff;--bg-card-hover:#f8fafc;
    --border:#e2e8f0;--border-glow:#7c4f0a;
    --gold:#8b5c0a;--gold-light:#a0650e;--gold-dim:rgba(139,92,10,0.08);
    --blue-ice:#0369a1;--compliant:#15803d;--partial:#b45309;
    --noncompliant:#b91c1c;--na:#64748b;
    --text-primary:#1e293b;--text-secondary:#475569;--text-dim:#94a3b8;
    --divider:#e2e8f0;--input-bg:#ffffff;
}
.stApp,.block-container{background-color:#f5f7fa!important;}
header[data-testid="stHeader"]{background:linear-gradient(180deg,#fff 0%,#f5f7fa 100%)!important;border-bottom:1px solid #e2e8f0!important;}
header[data-testid="stHeader"] *{color:#334155!important;}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#fff 0%,#faf9f7 100%)!important;border-right:1px solid #e8e3d8!important;box-shadow:2px 0 12px rgba(0,0,0,0.04)!important;}
section[data-testid="stSidebar"] .stButton>button{background:linear-gradient(135deg,#8b5c0a 0%,#a0650e 100%)!important;color:#fff!important;border:none!important;font-weight:600!important;}
[data-testid="metric-container"]{background:#fff!important;border:1px solid #e2e8f0!important;border-radius:16px!important;}
[data-testid="stMetricValue"]{color:#8b5c0a!important;}
.stTextInput input{background:#fff!important;color:#1e293b!important;border:1.5px solid #e2e8f0!important;border-radius:10px!important;}
.stCheckbox label,.stCheckbox label span,.stCheckbox label p{color:#1e293b!important;}
.stProgress > div{background:#e2e8f0!important;}
[data-testid="stFileUploader"]{background:#fff!important;border:2px dashed #cbd5e1!important;border-radius:16px!important;}
.stApp .block-container [data-baseweb="select"]>div{background:#fff!important;border:1.5px solid #e2e8f0!important;color:#1e293b!important;border-radius:10px!important;}
.stApp .block-container [data-baseweb="menu"]{background:#fff!important;}
.stApp .block-container [data-baseweb="menu"] li{color:#1e293b!important;}
.stMultiSelect [data-baseweb="tag"]{background:#fef3d6!important;color:#8b5c0a!important;border:1px solid #e8d5a8!important;}
.stApp .block-container .stDownloadButton>button,.stApp .block-container .stButton>button{background:#fff!important;color:#8b5c0a!important;border:1.5px solid #8b5c0a!important;border-radius:10px!important;font-weight:600!important;}
.rbi-card{background:#fff!important;border:1px solid #e2e8f0!important;}
.rbi-page-header{background:linear-gradient(135deg,#fff 0%,#fefcf8 100%)!important;border:1px solid #e2e8f0!important;border-left:4px solid #8b5c0a!important;}
.rbi-page-header h1{color:#1e293b!important;}
.rbi-stat-strip{background:#fff!important;border:1px solid #e2e8f0!important;}
.sidebar-brand-title{color:#8b5c0a!important;}
.sidebar-brand-subtitle,.sidebar-section-label,.sidebar-footer{color:#94a3b8!important;}
.step-indicator{color:#94a3b8!important;}
.step-indicator.done{color:#15803d!important;background:rgba(21,128,61,0.08)!important;}
.step-indicator.active{color:#8b5c0a!important;background:rgba(139,92,10,0.08)!important;border-left-color:#8b5c0a!important;}
.stTabs [data-baseweb="tab-list"]{background:#f1f5f9!important;border-radius:12px!important;padding:4px!important;border:1px solid #e2e8f0!important;}
.stTabs [data-baseweb="tab"]{color:#64748b!important;border-radius:10px!important;}
.stTabs [aria-selected="true"]{background:rgba(139,92,10,0.10)!important;color:#8b5c0a!important;font-weight:600!important;}
.stTabs [data-baseweb="tab-border"],.stTabs [data-baseweb="tab-highlight"]{display:none!important;}
::-webkit-scrollbar-track{background:#f5f7fa;}
::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:4px;}
::-webkit-scrollbar-thumb:hover{background:#8b5c0a;}
"""

LOCK_CSS = """
button[data-testid="collapsedControl"],[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
section[data-testid="stSidebar"] button[aria-label="Close sidebar"],
header[data-testid="stHeader"] button[aria-label="Open sidebar"]{
    display:none!important;visibility:hidden!important;pointer-events:none!important;
}
section[data-testid="stSidebar"]{transform:none!important;visibility:visible!important;min-width:272px!important;width:272px!important;}
"""

css_path = os.path.join(BASE_DIR, "style.css")
base_css = open(css_path, encoding="utf-8").read() if os.path.exists(css_path) else ""
st.markdown(f"<style>{base_css}\n{LIGHT_CSS if is_light else DARK_CSS}\n{LOCK_CSS}</style>", unsafe_allow_html=True)

components.html("""<script>
(function(){
  function lock(){
    var d=window.parent.document,s=d.querySelector('section[data-testid="stSidebar"]');
    if(!s)return;
    if(s.getAttribute('aria-expanded')==='false')s.setAttribute('aria-expanded','true');
    d.querySelectorAll('button[data-testid="collapsedControl"],[data-testid="stSidebarCollapsedControl"],header button[aria-label="Open sidebar"],section[data-testid="stSidebar"] button[aria-label="Close sidebar"]')
     .forEach(function(b){b.style.setProperty('display','none','important');});
  }
  window.parent.document.body?lock():window.parent.addEventListener('DOMContentLoaded',lock);
  new MutationObserver(lock).observe(window.parent.document.body||document,{subtree:true,childList:true,attributes:true});
  var i=0,t=setInterval(function(){lock();if(++i>20)clearInterval(t);},300);
})();
</script>""", height=0, scrolling=False)

if is_light:
    components.html("""<script>
    (function(){
      function patch(){window.parent.document.querySelectorAll('[data-baseweb="checkbox"]').forEach(function(c){var b=c.querySelector('div[style]'),inp=c.querySelector('input[type="checkbox"]');if(!b)return;var chk=inp&&inp.checked;b.style.setProperty('background-color',chk?'#8b5c0a':'#fff','important');b.style.setProperty('border-color',chk?'#8b5c0a':'#94a3b8','important');b.style.setProperty('border-radius','4px','important');b.style.setProperty('border-width','2px','important');b.style.setProperty('border-style','solid','important');var s=b.querySelector('svg');if(s)s.style.setProperty('fill','#fff','important');});}
      window.parent.document.body?patch():window.parent.addEventListener('DOMContentLoaded',patch);
      new MutationObserver(patch).observe(window.parent.document.body||document,{childList:true,subtree:true,attributes:true,attributeFilter:['style','class']});
      var i=0,t=setInterval(function(){patch();if(++i>30)clearInterval(t);},500);
    })();
    </script>""", height=0, scrolling=False)

# ── Import modules ─────────────────────────────────────────────
import module1, module2, module3
import module4_gap   as module4
import module5
import module7_audit as module7
try:
    import module8_evidence as module8; _has_m8 = True
except ImportError:
    _has_m8 = False

# ══════════════════════════════════════════════════════════════
#  AUTO-SAVE  — fingerprint-based, runs after every render
# ══════════════════════════════════════════════════════════════
def _autosave():
    uid = st.session_state.get("user_id")
    if not uid:
        return
    from db_store import save_bank_profile, save_compliance, save_gaps, save_evidence_entry
    ss = st.session_state

    # Module 1
    b, lv = ss.get("bank_name",""), ss.get("bank_level","")
    if b != ss.get("_snap_bank") or lv != ss.get("_snap_level"):
        if b or lv:
            save_bank_profile(uid, b, lv, ss.get("module1_flags", {}))
        ss["_snap_bank"] = b; ss["_snap_level"] = lv

    # Module 3
    sc = str(ss.get("compliance_summary",""))
    if sc != ss.get("_snap_compliance","") and ss.get("compliance_summary"):
        save_compliance(uid, ss["compliance_summary"], ss.get("combined_df"))
        ss["_snap_compliance"] = sc

    # Module 4
    gid = id(ss.get("gap_dataframe"))
    if gid != ss.get("_snap_gaps") and ss.get("gap_dataframe") is not None:
        save_gaps(uid, ss["gap_dataframe"]); ss["_snap_gaps"] = gid

    # Module 8 — incremental (only unsaved entries)
    ev_store = ss.get("evidence_store", {})
    cur_ev   = sum(len(v) for v in ev_store.values())
    if cur_ev > ss.get("_snap_ev_count", 0):
        for entries in ev_store.values():
            for entry in entries:
                if "_db_id" not in entry:
                    try:
                        entry["_db_id"] = save_evidence_entry(uid, entry)
                    except Exception:
                        pass
        ss["_snap_ev_count"] = cur_ev


# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════
NAV_OPTIONS = [
    "01  Level Identification",
    "02  Download Templates",
    "03  Compliance Dashboard",
    "04  Gap Analysis",
    "05  Gap Analysis Report",
    "06  Audit Trail Log",
]
if _has_m8:
    NAV_OPTIONS.append("07  Evidence Repository")

completed = []
if st.session_state.get("bank_level"):                completed.append(1)
if st.session_state.get("compliance_summary"):         completed.append(3)
if st.session_state.get("gap_dataframe") is not None: completed.append(4)
if any(v for v in st.session_state.get("evidence_store",{}).values()): completed.append(8)

summary   = st.session_state.get("compliance_summary")
score_pct = summary["percent"] if summary else None
username  = st.session_state.get("username", "User")
user_id   = st.session_state.get("user_id")

with st.sidebar:
    st.markdown(f"""
    <div style="padding:10px 0 10px 0;">
        <div class="sidebar-brand-title" style="font-family:'Rajdhani',sans-serif;font-size:21px;font-weight:700;letter-spacing:1.5px;">
            🏦 RBI CSF Tool
        </div>
        <div class="sidebar-brand-subtitle" style="font-size:9.5px;margin-top:3px;letter-spacing:1.3px;text-transform:uppercase;">
            Cybersecurity Compliance Assessment
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    toggle_label = "☀️  Light Theme" if not is_light else "🌙  Dark Theme"
    if st.button(toggle_label, width="stretch", key="theme_btn"):
        st.session_state["theme"] = "light" if not is_light else "dark"
        log_event("change", f"Theme switched", module="app")
        st.rerun()

    st.divider()

    # Bank card + score ring
    bank  = st.session_state.get("bank_name",  "Not Identified")
    level = st.session_state.get("bank_level", "Not Set")
    level_badge = {
        "Level-I":   '<span class="rbi-badge badge-blue">LEVEL-I</span>',
        "Level-II":  '<span class="rbi-badge badge-amber">LEVEL-II</span>',
        "Level-III": '<span class="rbi-badge badge-red">LEVEL-III</span>',
        "Level-IV":  '<span class="rbi-badge badge-purple">LEVEL-IV</span>',
    }.get(level, '<span class="rbi-badge badge-gold">UNSET</span>')

    if score_pct is not None:
        rc = "#22c55e" if score_pct>=80 else "#f59e0b" if score_pct>=60 else "#ef4444"
        circ = 2*3.14159*18
        dash = circ*score_pct/100
        ring = f'<svg width="44" height="44" style="flex-shrink:0;"><circle cx="22" cy="22" r="18" fill="none" stroke="var(--border)" stroke-width="3"/><circle cx="22" cy="22" r="18" fill="none" stroke="{rc}" stroke-width="3" stroke-dasharray="{dash:.1f} {circ:.1f}" stroke-linecap="round" transform="rotate(-90 22 22)"/><text x="22" y="26" text-anchor="middle" font-family="Rajdhani,sans-serif" font-size="9" font-weight="700" fill="{rc}">{int(score_pct)}%</text></svg>'
    else:
        ring = ""

    st.markdown(f"""
    <div class="sidebar-bank-card" style="display:flex;align-items:center;gap:10px;">
        <div style="flex:1;min-width:0;">
            <div style="font-size:9.5px;color:var(--text-dim);letter-spacing:0.8px;text-transform:uppercase;margin-bottom:2px;">👤 {username}</div>
            <div style="font-family:'Rajdhani',sans-serif;font-size:14px;font-weight:700;color:var(--gold);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:155px;" title="{bank}">{bank if bank != "Not Identified" else "Not Identified"}</div>
            <div style="margin-top:4px;">{level_badge}</div>
        </div>
        {ring}
    </div>
    <div style="text-align:center;margin-top:5px;">
        <span class="rbi-badge badge-green" style="font-size:8px;">🔄 Auto-saving</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="sidebar-section-label">Modules</div>', unsafe_allow_html=True)
    menu = st.radio(
        "Navigation", NAV_OPTIONS,
        index=min(st.session_state.get("active_module",0), len(NAV_OPTIONS)-1),
        key="nav_radio", label_visibility="collapsed",
    )
    st.session_state["active_module"] = NAV_OPTIONS.index(menu)

    st.divider()

    st.markdown('<div class="sidebar-section-label">Progress</div>', unsafe_allow_html=True)
    STEPS = [(1,"Level Identification",0),(2,"Templates",1),(3,"Dashboard",2),(4,"Gap Analysis",3),(5,"Gap Report",4),(7,"Audit Trail",5)]
    if _has_m8: STEPS.append((8,"Evidence",6))
    active_idx = st.session_state["active_module"]
    for num, lbl, nav_i in STEPS:
        cls = "done" if num in completed else ("active" if nav_i==active_idx else "")
        icon = "✓" if num in completed else "○"
        st.markdown(f'<div class="step-indicator {cls}">{icon}&nbsp; {lbl}</div>', unsafe_allow_html=True)

    audit_count = len(st.session_state.get("audit_log",[]))
    if audit_count > 0:
        st.markdown(f'<div style="margin-top:8px;text-align:center;"><span class="rbi-badge badge-gold">📋 {audit_count} events</span></div>', unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="sidebar-section-label">Account</div>', unsafe_allow_html=True)
    render_change_password_widget()

    if st.button("🚪  Sign Out", width="stretch", key="logout_btn"):
        from db_store import save_full_session
        save_full_session(user_id, dict(st.session_state))
        log_event("system", f"User '{username}' signed out", module="app")
        _theme = st.session_state.get("theme","dark")
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.session_state["theme"] = _theme
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer">RBI Graded Approach Framework<br>Cybersecurity Assessment Tool</div>', unsafe_allow_html=True)

# ── Routing ────────────────────────────────────────────────────
if   "Level Identification" in menu: module1.show_module1()
elif "Download Templates"   in menu: module2.show_module2()
elif "Compliance Dashboard" in menu: module3.show_module3()
elif "Gap Analysis Report"  in menu: module5.show_module5()
elif "Gap Analysis"         in menu: module4.show_module4()
elif "Audit Trail"          in menu: module7.show_module7()
elif "Evidence Repository"  in menu and _has_m8: module8.show_module8()

# ── Auto-save at end of every render ──────────────────────────
_autosave()