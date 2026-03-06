import streamlit as st
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
}
COLORS   = {"Not Compliant": "#ef4444", "Partially Compliant": "#f59e0b"}
CHART_BG = "rgba(0,0,0,0)"


def _log(event_type, action, detail=""):
    try:
        from module7_audit import log_event
        log_event(event_type, action, detail, module="module4")
    except Exception:
        pass


def _chart_settings():
    is_light = st.session_state.get("theme", "dark") == "light"
    if is_light:
        return (
            dict(family="IBM Plex Sans", color="#334155", size=11),
            "#e2e8f0",
            "#f0f4f8",
        )
    return (
        dict(family="IBM Plex Sans", color="#7a92b4", size=11),
        "#1a2f52",
        "#04090f",
    )


def find_col(df, keyword):
    for col in df.columns:
        if keyword in col.lower():
            return col
    return None


def show_module4():
    st.markdown("""
    <div class="rbi-page-header">
        <h1>⚠️ MODULE 4 — GAP ANALYSIS</h1>
        <p>Identify and prioritize compliance gaps requiring remediation</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload Filled Control Files", type=["xlsx"],
        accept_multiple_files=True, label_visibility="collapsed",
    )

    if not uploaded_files:
        st.markdown("""
        <div class="rbi-card" style="text-align:center; padding:52px 32px; color:var(--text-dim);">
            <div style="font-size:42px; margin-bottom:14px;">🔍</div>
            <div style="font-family:'Rajdhani',sans-serif; font-size:19px; color:var(--text-secondary);">
                Upload your filled template files to identify compliance gaps
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Process
    gap_rows   = []
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
        df["_source"] = file.name
        gaps = df[df["_status"].isin(["Not Compliant", "Partially Compliant"])].copy()
        if not gaps.empty:
            gap_rows.append(gaps)
        file_names.append(file.name)

    # Audit log on new uploads
    prev_files = st.session_state.get("_m4_files", [])
    if sorted(file_names) != sorted(prev_files):
        _log("upload", f"{len(file_names)} file(s) uploaded to Gap Analysis",
             detail=", ".join(file_names))
        st.session_state["_m4_files"] = file_names

    if not gap_rows:
        st.markdown("""
        <div class="rbi-card rbi-card-green" style="text-align:center; padding:36px;">
            <div style="font-size:34px;">🎉</div>
            <div style="font-family:'Rajdhani',sans-serif; font-size:20px; color:#22c55e; margin-top:8px;">
                No Gaps Identified
            </div>
            <div style="color:var(--text-secondary); font-size:13px; margin-top:6px;">
                All controls are compliant or not applicable.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    gap_df = pd.concat(gap_rows, ignore_index=True)
    gap_df["Priority"] = gap_df["_status"].apply(
        lambda s: "🔴 High" if s == "Not Compliant" else "🟡 Medium"
    )

    total_gaps = len(gap_df)
    high_gaps  = (gap_df["Priority"] == "🔴 High").sum()
    med_gaps   = (gap_df["Priority"] == "🟡 Medium").sum()

    # ── KPI Strip ──────────────────────────────────────────────
    st.markdown('<div class="rbi-section-title">Gap Summary</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="rbi-stat-strip">
        <div class="rbi-stat-item">
            <div class="stat-label">Total Gaps</div>
            <div class="stat-value">{total_gaps}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">High Priority</div>
            <div class="stat-value" style="color:var(--noncompliant);">{high_gaps}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Medium Priority</div>
            <div class="stat-value" style="color:var(--partial);">{med_gaps}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Files Analysed</div>
            <div class="stat-value">{len(file_names)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ─────────────────────────────────────────────────
    st.markdown('<div class="rbi-section-title">Gap Distribution</div>', unsafe_allow_html=True)
    ch1, ch2 = st.columns(2)

    with ch1:
        CHART_FONT, GRID_COLOR, PIE_LINE = _chart_settings()
        pie_df = pd.DataFrame({
            "Priority": ["High Priority", "Medium Priority"],
            "Count":    [high_gaps, med_gaps],
        })
        fig_pie = go.Figure(go.Pie(
            labels=pie_df["Priority"], values=pie_df["Count"],
            hole=0.58,
            marker=dict(colors=["#ef4444", "#f59e0b"], line=dict(color=PIE_LINE, width=2)),
            textinfo="percent+label",
            textfont=dict(size=10, color="white"),
        ))
        fig_pie.update_layout(
            height=250, margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor=CHART_BG, font=CHART_FONT, showlegend=False,
        )
        st.markdown('<div class="rbi-label" style="margin-bottom:4px;">PRIORITY SPLIT</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_pie, use_container_width=True)

    with ch2:
        CHART_FONT, GRID_COLOR, PIE_LINE = _chart_settings()
        file_gap = gap_df.groupby(["_source", "_status"]).size().reset_index(name="Count")
        file_gap["_source"] = file_gap["_source"].str.replace(".xlsx", "").str.replace("_", " ")
        fig_bar = px.bar(
            file_gap, x="_source", y="Count", color="_status",
            barmode="stack", color_discrete_map=COLORS,
            labels={"_source": "File", "_status": "Status"},
        )
        fig_bar.update_layout(
            height=250, margin=dict(t=10, b=60, l=10, r=10),
            paper_bgcolor=CHART_BG, font=CHART_FONT,
            legend=dict(orientation="h", y=-0.42, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(tickangle=-20, showgrid=False),
            yaxis=dict(gridcolor=GRID_COLOR, title=""),
            bargap=0.35,
        )
        fig_bar.update_traces(marker_line_width=0)
        st.markdown('<div class="rbi-label" style="margin-bottom:4px;">GAPS BY FILE</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_bar, use_container_width=True)

    # Section bar
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

    # ── Filters + Register ─────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="rbi-section-title">Gap Register</div>', unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    with f1:
        pf = st.multiselect("Filter by Priority", ["🔴 High", "🟡 Medium"],
                             default=["🔴 High", "🟡 Medium"])
    with f2:
        sf = st.multiselect(
            "Filter by Source", gap_df["_source"].unique().tolist(),
            default=gap_df["_source"].unique().tolist(),
        )

    filtered = gap_df[gap_df["Priority"].isin(pf) & gap_df["_source"].isin(sf)]

    display_cols = []
    for kw in ["sr", "section", "sub-section", "requirement"]:
        c = find_col(filtered, kw)
        if c and c not in display_cols:
            display_cols.append(c)
    for kw in ["_status", "priority", "_source", "observation", "recommendation"]:
        c = next((col for col in filtered.columns if kw.lower() in col.lower()), None)
        if c and c not in display_cols:
            display_cols.append(c)

    display_cols = [c for c in display_cols if c in filtered.columns]
    show_df = filtered[display_cols].rename(
        columns={"_status": "Status", "_source": "Source", "Priority": "Priority"}
    )

    st.dataframe(show_df, use_container_width=True, height=380)

    # ── Export ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    csv = show_df.to_csv(index=False).encode("utf-8")
    if st.download_button(
        "⬇️  Export Gap Register as CSV", csv,
        file_name="Gap_Analysis_Report.csv", mime="text/csv",
        use_container_width=True,
    ):
        _log("export", "Gap Register exported as CSV",
             detail=f"{len(show_df)} rows · {len(file_names)} file(s)")

    st.session_state["gap_dataframe"] = gap_df