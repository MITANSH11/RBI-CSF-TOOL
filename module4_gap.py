import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CONTROL_COL = "control implemented"

STATUS_NORM = {
    "fully implemented":     "Compliant",
    "compliant":             "Compliant",
    "partially implemented": "Partially Compliant",
    "partially compliant":   "Partially Compliant",
    "no":                    "Not Compliant",
    "not compliant":         "Not Compliant",
    "not applicable":        "Not Applicable",
    "n/a":                   "Not Applicable",
    "select":                None,
}

COLORS   = {"Not Compliant": "#ef4444", "Partially Compliant": "#f59e0b"}
CHART_BG = "rgba(0,0,0,0)"

FILE_LABELS = {
    "basic_cybersecurity_framework": "Basic Framework",
    "annex_1_cybersecurity_control": "Annex I",
    "annex2_cybersecurity_":         "Annex II",
    "annex3_cybersecurity":          "Annex III",
    "annex4_cybersecurity_control":  "Annex IV",
    "annex-1":                       "Annex I",
    "annex-2":                       "Annex II",
    "annex-3":                       "Annex III",
    "annex-4":                       "Annex IV",
}

ANNEX4_CRITICAL = {
    "c-soc", "csoc", "cyber security operation",
    "ciso", "chief information security",
    "it strategy committee", "it steering committee",
    "information security committee",
    "audit committee",
}


def _log(event_type, action, detail=""):
    try:
        from module7_audit import log_event
        log_event(event_type, action, detail, module="module4")
    except Exception:
        pass


def _is_light():
    return st.session_state.get("theme", "dark") == "light"


def _chart_settings():
    if _is_light():
        return (dict(family="IBM Plex Sans", color="#334155", size=11), "#e2e8f0", "#f0f4f8")
    return (dict(family="IBM Plex Sans", color="#7a92b4", size=11), "#1a2f52", "#04090f")


def _clean_label(raw_name):
    key = raw_name.lower().replace(".xlsx", "").strip()
    for pattern, label in FILE_LABELS.items():
        if pattern in key:
            return label
    return raw_name.replace(".xlsx", "").replace("_", " ").strip()


def find_col(df, keyword):
    for col in df.columns:
        if keyword in col.lower():
            return col
    return None


# ── Helper: render a stat strip via components.html (never raw tags) ──────────
def _stat_strip_html(items, is_light):
    """items = list of (label, value, color_or_None)"""
    if is_light:
        bg, bdr, val_default, lbl_clr = "#ffffff", "#e2e8f0", "#8b5c0a", "#94a3b8"
    else:
        bg, bdr, val_default, lbl_clr = "#08121f", "#162540", "#c9a84c", "#6e87a8"

    css = (
        "body{margin:0;padding:0;background:transparent;font-family:IBM Plex Sans,system-ui,sans-serif;}"
        ".strip{background:" + bg + ";border:1px solid " + bdr + ";border-radius:14px;"
        "padding:14px 8px;display:flex;align-items:center;flex-wrap:wrap;}"
        ".item{flex:1;min-width:90px;padding:6px 16px;border-right:1px solid " + bdr + ";text-align:center;}"
        ".item:last-child{border-right:none;}"
        ".lbl{font-size:9.5px;font-weight:700;letter-spacing:0.9px;text-transform:uppercase;"
        "color:" + lbl_clr + ";margin-bottom:5px;}"
        ".val{font-family:Rajdhani,sans-serif;font-size:26px;font-weight:700;line-height:1.1;}"
    )

    cells = ""
    for label, value, color in items:
        c = color if color else val_default
        cells += (
            '<div class="item">'
            '<div class="lbl">' + label + '</div>'
            '<div class="val" style="color:' + c + ';">' + str(value) + '</div>'
            '</div>'
        )

    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>" + css + "</style></head><body>"
        '<div class="strip">' + cells + "</div>"
        "</body></html>"
    )


def _info_card_html(text, accent, is_light):
    if is_light:
        bg, bdr, txt_clr = "#ffffff", "#e2e8f0", "#334155"
    else:
        bg, bdr, txt_clr = "#0d1a30", "#162540", "#8a9ab8"
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>body{margin:0;padding:0;background:transparent;"
        "font-family:IBM Plex Sans,system-ui,sans-serif;}"
        ".card{background:" + bg + ";border:1px solid " + bdr + ";"
        "border-left:3px solid " + accent + ";border-radius:12px;"
        "padding:14px 18px;font-size:12.5px;color:" + txt_clr + ";line-height:1.7;}"
        "</style></head><body>"
        '<div class="card">' + text + "</div>"
        "</body></html>"
    )


def _render_gaps(gap_df, file_names):
    """Render the gap analysis from an existing gap DataFrame."""

    def assign_priority(row):
        status  = row.get("_status", "")
        req_col = find_col(gap_df, "requirement")
        req_txt = str(row.get(req_col, "")).lower() if req_col else ""
        src_lbl = str(row.get("_source_label", "")).lower()
        is_annex4     = "annex iv" in src_lbl or "annex-4" in src_lbl or "annex_4" in src_lbl
        is_governance = any(kw in req_txt for kw in ANNEX4_CRITICAL)
        if status == "Not Compliant":
            return "High" if not (is_annex4 and is_governance) else "Critical"
        return "Medium"

    if "Priority" not in gap_df.columns:
        gap_df["Priority"] = gap_df.apply(assign_priority, axis=1)

    total_gaps    = len(gap_df)
    critical_gaps = (gap_df["Priority"] == "Critical").sum()
    high_gaps     = (gap_df["Priority"] == "High").sum()
    med_gaps      = (gap_df["Priority"] == "Medium").sum()
    light         = _is_light()

    # ── KPI Strip via components.html ─────────────────────────
    st.markdown('<div class="rbi-section-title">Gap Summary</div>', unsafe_allow_html=True)

    strip_items = [("Total Gaps", total_gaps, None)]
    if critical_gaps > 0:
        strip_items.append(("Critical (Gov.)", critical_gaps, "#a855f7"))
    strip_items += [
        ("High Priority",   high_gaps,        "#ef4444"),
        ("Medium Priority", med_gaps,          "#f59e0b"),
        ("Files Analysed",  len(file_names),   None),
    ]
    components.html(_stat_strip_html(strip_items, light), height=95, scrolling=False)

    # ── Critical governance callout ────────────────────────────
    if critical_gaps > 0:
        accent = "#a855f7"
        body   = (
            '<strong style="color:' + accent + '">' +
            str(critical_gaps) +
            ' Critical Governance Gap(s) Detected</strong>' +
            ' — Annex IV mandates C-SOC setup, CISO appointment, and Board-level IT committees.' +
            ' These require <strong>immediate Board-level action</strong> and cannot be deferred.'
        )
        components.html(_info_card_html(body, accent, light), height=80, scrolling=False)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ─────────────────────────────────────────────────
    st.markdown('<div class="rbi-section-title">Gap Distribution</div>', unsafe_allow_html=True)
    ch1, ch2 = st.columns(2)

    with ch1:
        CHART_FONT, GRID_COLOR, PIE_LINE = _chart_settings()
        pie_labels  = ["High Priority", "Medium Priority"]
        pie_values  = [high_gaps, med_gaps]
        pie_colors  = ["#ef4444", "#f59e0b"]
        if critical_gaps > 0:
            pie_labels.insert(0, "Critical")
            pie_values.insert(0, critical_gaps)
            pie_colors.insert(0, "#a855f7")
        fig_pie = go.Figure(go.Pie(
            labels=pie_labels, values=pie_values,
            hole=0.58,
            marker=dict(colors=pie_colors, line=dict(color=PIE_LINE, width=2)),
            textinfo="percent+label",
            textfont=dict(size=10, color="white"),
        ))
        fig_pie.update_layout(
            height=250, margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor=CHART_BG, font=CHART_FONT, showlegend=False,
        )
        st.markdown('<div class="rbi-label" style="margin-bottom:4px;">PRIORITY SPLIT</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(fig_pie, use_container_width=True)

    with ch2:
        CHART_FONT, GRID_COLOR, PIE_LINE = _chart_settings()
        file_gap = gap_df.groupby(["_source_label", "_status"]).size().reset_index(name="Count")
        fig_bar = px.bar(
            file_gap, x="_source_label", y="Count", color="_status",
            barmode="stack", color_discrete_map=COLORS,
            labels={"_source_label": "Annex", "_status": "Status"},
        )
        fig_bar.update_layout(
            height=250, margin=dict(t=10, b=60, l=10, r=10),
            paper_bgcolor=CHART_BG, font=CHART_FONT,
            legend=dict(orientation="h", y=-0.42, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(tickangle=-20, showgrid=False, title=""),
            yaxis=dict(gridcolor=GRID_COLOR, title=""),
            bargap=0.35,
        )
        fig_bar.update_traces(marker_line_width=0)
        st.markdown('<div class="rbi-label" style="margin-bottom:4px;">GAPS BY ANNEX</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Section bar ────────────────────────────────────────────
    sec_col = find_col(gap_df, "section")
    if sec_col:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="rbi-section-title">Gaps by Section</div>', unsafe_allow_html=True)
        sec_gap = gap_df.groupby([sec_col, "_status"]).size().reset_index(name="Count")
        CHART_FONT, GRID_COLOR, PIE_LINE = _chart_settings()
        fig_sec = px.bar(
            sec_gap, x=sec_col, y="Count", color="_status",
            barmode="group", color_discrete_map=COLORS,
            labels={sec_col: "Section", "_status": "Status"},
        )
        fig_sec.update_layout(
            height=290, margin=dict(t=10, b=80, l=10, r=10),
            paper_bgcolor=CHART_BG, font=CHART_FONT,
            legend=dict(orientation="h", y=-0.45, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(tickangle=-30, showgrid=False),
            yaxis=dict(gridcolor=GRID_COLOR, title=""),
            bargap=0.3,
        )
        fig_sec.update_traces(marker_line_width=0)
        st.plotly_chart(fig_sec, use_container_width=True)

    # ── Filters + Gap Register ─────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="rbi-section-title">Gap Register</div>', unsafe_allow_html=True)

    priority_opts = sorted(gap_df["Priority"].unique().tolist())
    f1, f2, f3 = st.columns(3)
    with f1:
        pf = st.multiselect("Filter by Priority", priority_opts, default=priority_opts,
                             key="m4_priority_filter")
    with f2:
        source_opts = gap_df["_source_label"].unique().tolist()
        sf = st.multiselect("Filter by Annex", source_opts, default=source_opts,
                             key="m4_source_filter")
    with f3:
        search = st.text_input("Search requirement", placeholder="keyword...",
                               label_visibility="collapsed", key="m4_search")

    filtered = gap_df[gap_df["Priority"].isin(pf) & gap_df["_source_label"].isin(sf)]
    if search:
        req_col_s = find_col(filtered, "requirement")
        if req_col_s:
            filtered = filtered[
                filtered[req_col_s].astype(str).str.lower().str.contains(search.lower(), na=False)
            ]

    display_cols = []
    for kw in ["sr", "section", "sub-section", "requirement"]:
        c = find_col(filtered, kw)
        if c and c not in display_cols:
            display_cols.append(c)
    for kw in ["_status", "_source_label", "priority"]:
        c = next((col for col in filtered.columns if kw.lower() in col.lower()), None)
        if c and c not in display_cols:
            display_cols.append(c)

    display_cols = [c for c in display_cols if c in filtered.columns]
    show_df = filtered[display_cols].rename(columns={
        "_status":       "Status",
        "_source_label": "Annex",
        "Priority":      "Priority",
    })

    # Showing X of Y counter via components.html
    light = _is_light()
    cnt_bg  = "#ffffff" if light else "#08121f"
    cnt_bdr = "#e2e8f0" if light else "#162540"
    cnt_txt = "#334155" if light else "#6e87a8"
    cnt_hi  = "#8b5c0a" if light else "#dde4f0"
    components.html(
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>body{margin:0;padding:0;background:transparent;"
        "font-family:IBM Plex Sans,system-ui,sans-serif;font-size:12px;color:" + cnt_txt + ";}"
        "</style></head><body>"
        "Showing <strong style='color:" + cnt_hi + ";'>" + str(len(show_df)) + "</strong>"
        " of " + str(total_gaps) + " gaps"
        "</body></html>",
        height=28, scrolling=False,
    )
    st.dataframe(show_df, use_container_width=True, height=380)

    # ── Export ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    csv = show_df.to_csv(index=False).encode("utf-8")
    if st.download_button(
        "Download  Gap Register as CSV", csv,
        file_name="Gap_Analysis_Report.csv", mime="text/csv",
        use_container_width=True,
    ):
        _log("export", "Gap Register exported as CSV",
             detail=str(len(show_df)) + " rows / " + str(len(file_names)) + " file(s)")

    st.session_state["gap_dataframe"] = gap_df


def show_module4():
    st.markdown(
        '<div class="rbi-page-header">'
        '<h1>&#9888;&#65039; MODULE 4 — GAP ANALYSIS</h1>'
        '<p>Identify and prioritize compliance gaps requiring remediation across all annexes</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    level = st.session_state.get("bank_level", "")
    if level == "Level-IV":
        light  = _is_light()
        accent = "#a855f7"
        body   = (
            '<strong style="color:' + accent + ';">Level-IV</strong>' +
            ' — Upload all 5 files for a complete gap picture. ' +
            'Annex IV governance gaps (C-SOC, CISO, IT Committees) are flagged as ' +
            '<strong style="color:#ef4444;">Critical</strong> priority.'
        )
        components.html(_info_card_html(body, accent, light), height=72, scrolling=False)
        st.markdown("<br>", unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload Filled Control Files", type=["xlsx"],
        accept_multiple_files=True, label_visibility="collapsed",
    )

    saved_gap = st.session_state.get("gap_dataframe")

    if not uploaded_files:
        if saved_gap is not None and not saved_gap.empty:
            saved_file_names = st.session_state.get("_m4_files", [])
            st.info("Showing previously saved gap analysis. Upload new files above to refresh.")
            _render_gaps(saved_gap.copy(), saved_file_names)
        else:
            st.markdown(
                '<div class="rbi-card" style="text-align:center;padding:52px 32px;color:var(--text-dim);">'
                '<div style="font-size:42px;margin-bottom:14px;">&#128269;</div>'
                '<div style="font-family:Rajdhani,sans-serif;font-size:19px;color:var(--text-secondary);">'
                'Upload your filled template files to identify compliance gaps</div>'
                '<div style="font-size:12px;color:var(--text-dim);margin-top:8px;">'
                'Accepts .xlsx — upload all applicable annexes for a complete analysis</div></div>',
                unsafe_allow_html=True,
            )
        return

    gap_rows   = []
    all_rows   = []
    file_names = []

    for file in uploaded_files:
        df = pd.read_excel(file, engine="openpyxl", header=2)
        df.columns = df.columns.astype(str).str.strip()
        impl_col = find_col(df, CONTROL_COL)
        if not impl_col:
            continue
        df["_status"] = df[impl_col].apply(
            lambda v: STATUS_NORM.get(str(v).strip().lower(), None)
        )
        df = df[df["_status"].notna()].copy()
        df["_source"]       = file.name
        df["_source_label"] = _clean_label(file.name)
        all_rows.append(df)

        gaps = df[df["_status"].isin(["Not Compliant", "Partially Compliant"])].copy()
        if not gaps.empty:
            gap_rows.append(gaps)
        file_names.append(file.name)

    prev_files = st.session_state.get("_m4_files", [])
    if sorted(file_names) != sorted(prev_files):
        _log("upload", str(len(file_names)) + " file(s) uploaded to Gap Analysis",
             detail=", ".join(file_names))
        st.session_state["_m4_files"] = file_names

    if not gap_rows:
        st.markdown(
            '<div class="rbi-card rbi-card-green" style="text-align:center;padding:36px;">'
            '<div style="font-size:34px;">&#127881;</div>'
            '<div style="font-family:Rajdhani,sans-serif;font-size:20px;color:#22c55e;margin-top:8px;">'
            'No Gaps Identified</div>'
            '<div style="color:var(--text-secondary);font-size:13px;margin-top:6px;">'
            'All controls are compliant or not applicable across all uploaded annexes.</div></div>',
            unsafe_allow_html=True,
        )
        return

    gap_df = pd.concat(gap_rows, ignore_index=True)
    _render_gaps(gap_df, file_names)