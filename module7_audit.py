"""
module7_audit.py — Audit Trail & History Log
Tracks every user action across all modules: uploads, exports,
level changes, dashboard views, and gap analysis runs.
"""

import streamlit as st
from datetime import datetime
import pandas as pd


# ── Event type metadata ─────────────────────────────────────────────────────
EVENT_META = {
    "upload":    {"icon": "⬆️",  "css": "event-upload",  "badge": "badge-blue",   "label": "Upload"},
    "export":    {"icon": "⬇️",  "css": "event-export",  "badge": "badge-green",  "label": "Export"},
    "view":      {"icon": "👁️",  "css": "event-view",    "badge": "badge-amber",  "label": "View"},
    "change":    {"icon": "✏️",  "css": "event-change",  "badge": "badge-red",    "label": "Change"},
    "identify":  {"icon": "🏷️",  "css": "event-view",    "badge": "badge-gold",   "label": "Identify"},
    "analysis":  {"icon": "🔍",  "css": "event-upload",  "badge": "badge-purple", "label": "Analysis"},
    "system":    {"icon": "⚙️",  "css": "",              "badge": "badge-grey",   "label": "System"},
}

MODULE_LABELS = {
    "module1": "Level Identification",
    "module2": "Download Templates",
    "module3": "Compliance Dashboard",
    "module4": "Gap Analysis",
    "module5": "Gap Report",
    "module7": "Audit Trail log",
    "app":     "Application",
}


def _now() -> str:
    return datetime.now().strftime("%d %b %Y  %H:%M:%S")


def _short_now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log_event(event_type: str, action: str, detail: str = "", module: str = "app"):
    """
    Call this from any module to record an action.
    event_type : one of EVENT_META keys
    action     : short human-readable description
    detail     : optional extra context
    module     : source module key (e.g. 'module3')
    """
    if "audit_log" not in st.session_state:
        st.session_state["audit_log"] = []

    st.session_state["audit_log"].append({
        "timestamp": _now(),
        "type":      event_type,
        "action":    action,
        "detail":    detail,
        "module":    module,
    })

    # Cap log at 500 entries to avoid memory growth
    if len(st.session_state["audit_log"]) > 500:
        st.session_state["audit_log"] = st.session_state["audit_log"][-500:]


def _empty_state():
    st.markdown("""
    <div class="rbi-card" style="text-align:center; padding:56px 32px;">
        <div style="font-size:44px; margin-bottom:14px;">📋</div>
        <div style="font-family:'Rajdhani',sans-serif; font-size:20px; color:var(--text-secondary);">
            No Activity Recorded Yet
        </div>
        <div style="font-size:13px; color:var(--text-dim); margin-top:8px; max-width:360px; margin-left:auto; margin-right:auto; line-height:1.6;">
            Actions across all modules — uploads, exports, level changes, dashboard views —
            will appear here automatically.
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_module7():
    st.markdown("""
    <div class="rbi-page-header">
        <h1>📋 MODULE 6 — AUDIT TRAIL Log </h1>
        <p>Complete timestamped log of all actions performed across every module</p>
    </div>
    """, unsafe_allow_html=True)

    # Log this view
    log_event("view", "Audit Trail viewed", module="module7")

    log = st.session_state.get("audit_log", [])

    if not log:
        _empty_state()
        return

    # ── KPI Strip ──────────────────────────────────────────────
    total_events = len(log)
    uploads  = sum(1 for e in log if e["type"] == "upload")
    exports  = sum(1 for e in log if e["type"] == "export")
    changes  = sum(1 for e in log if e["type"] == "change")
    analyses = sum(1 for e in log if e["type"] in ("analysis", "view"))

    st.markdown(f"""
    <div class="rbi-stat-strip">
        <div class="rbi-stat-item">
            <div class="stat-label">Total Events</div>
            <div class="stat-value">{total_events}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Uploads</div>
            <div class="stat-value" style="color:var(--blue-ice);">{uploads}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Exports</div>
            <div class="stat-value" style="color:var(--compliant);">{exports}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Config Changes</div>
            <div class="stat-value" style="color:var(--noncompliant);">{changes}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Views / Analysis</div>
            <div class="stat-value" style="color:var(--partial);">{analyses}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Filters ────────────────────────────────────────────────
    st.markdown('<div class="rbi-section-title">Filter Events</div>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns([1.2, 1.2, 1])
    with f1:
        all_types   = sorted(set(e["type"] for e in log))
        filter_type = st.multiselect(
            "Event Type",
            options=all_types,
            default=all_types,
            key="audit_type_filter",
        )
    with f2:
        all_modules   = sorted(set(e.get("module","app") for e in log))
        filter_module = st.multiselect(
            "Module",
            options=all_modules,
            default=all_modules,
            format_func=lambda k: MODULE_LABELS.get(k, k),
            key="audit_mod_filter",
        )
    with f3:
        search_text = st.text_input(
            "Search",
            placeholder="🔍  keyword...",
            key="audit_search",
            label_visibility="collapsed",
        )

    # Apply filters
    filtered = [
        e for e in reversed(log)
        if e["type"] in filter_type
        and e.get("module", "app") in filter_module
        and (
            not search_text
            or search_text.lower() in e["action"].lower()
            or search_text.lower() in e.get("detail","").lower()
        )
    ]

    st.markdown(f"""
    <div style="font-size:12px; color:var(--text-dim); margin-bottom:14px;">
        Showing <strong style="color:var(--text-secondary);">{len(filtered)}</strong>
        of {total_events} events &nbsp;·&nbsp; most recent first
    </div>
    """, unsafe_allow_html=True)

    # ── Timeline ───────────────────────────────────────────────
    st.markdown('<div class="rbi-section-title">Event Timeline</div>', unsafe_allow_html=True)

    if not filtered:
        st.markdown("""
        <div class="rbi-card" style="text-align:center; padding:32px; color:var(--text-dim);">
            No events match the current filters.
        </div>
        """, unsafe_allow_html=True)
    else:
        # Group by day for visual separation
        from itertools import groupby

        def day_key(e):
            # Extract date part from timestamp string like "14 Jan 2025  09:32:11"
            return e["timestamp"].split("  ")[0]

        st.markdown('<div class="audit-timeline">', unsafe_allow_html=True)

        current_day = None
        for event in filtered:
            day = day_key(event)
            if day != current_day:
                current_day = day
                st.markdown(f"""
                <div style="font-size:10px; font-weight:700; letter-spacing:1.5px;
                            text-transform:uppercase; color:var(--text-dim);
                            margin: 18px 0 10px -30px; padding-left:4px;
                            border-bottom:1px solid var(--border); padding-bottom:5px;">
                    {day}
                </div>
                """, unsafe_allow_html=True)

            meta    = EVENT_META.get(event["type"], EVENT_META["system"])
            mod_lbl = MODULE_LABELS.get(event.get("module","app"), event.get("module",""))
            time_part = event["timestamp"].split("  ")[-1] if "  " in event["timestamp"] else event["timestamp"]

            st.markdown(f"""
            <div class="audit-event {meta['css']}">
                <div class="ae-header">
                    <div class="ae-action">
                        {meta['icon']}&nbsp; {event['action']}
                    </div>
                    <div class="ae-time">{time_part}</div>
                </div>
                <div class="ae-detail" style="margin-top:6px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                    <span class="rbi-badge {meta['badge']}">{meta['label']}</span>
                    <span class="rbi-badge badge-grey">{mod_lbl}</span>
                    {"<span style='color:var(--text-secondary);font-size:11.5px;'>" + event['detail'] + "</span>" if event.get('detail') else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Export ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="rbi-section-title">Export Log</div>', unsafe_allow_html=True)

    ec1, ec2 = st.columns(2)

    with ec1:
        if filtered:
            export_df = pd.DataFrame(filtered)
            export_df["module"] = export_df["module"].map(lambda k: MODULE_LABELS.get(k, k))
            export_df.rename(columns={
                "timestamp": "Timestamp", "type": "Event Type",
                "action": "Action", "detail": "Detail", "module": "Module"
            }, inplace=True)
            csv = export_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️  Export Filtered Log (CSV)",
                csv,
                file_name="Audit_Trail_Log.csv",
                mime="text/csv",
                width="stretch",
            )

    with ec2:
        if st.button("🗑️  Clear Audit Log", width="stretch"):
            st.session_state["audit_log"] = []
            log_event("system", "Audit log cleared by user", module="module7")
            st.success("Log cleared.")
            st.rerun()