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
    "n/a":                   "Not Applicable",
    "select":                "Not Assessed",
}

COLORS = {
    "Compliant":           "#22c55e",
    "Partially Compliant": "#f59e0b",
    "Not Compliant":       "#ef4444",
    "Not Applicable":      "#64748b",
    "Not Assessed":        "#334155",
}

FILE_LABELS = {
    "basic_cybersecurity_framework":      "Basic Framework",
    "annex_1_cybersecurity_control":      "Annex I",
    "annex2_cybersecurity_":              "Annex II",
    "annex3_cybersecurity":               "Annex III",
    "annex4_cybersecurity_control":       "Annex IV",
}

CHART_BG = "rgba(0,0,0,0)"


def _log(event_type, action, detail=""):
    try:
        from module7_audit import log_event
        log_event(event_type, action, detail, module="module3")
    except Exception:
        pass


def _chart_settings():
    is_light = st.session_state.get("theme", "dark") == "light"
    if is_light:
        return (
            dict(family="IBM Plex Sans", color="#334155", size=11),
            "#e2e8f0", "#f1f5f9", "#f0f4f8",
        )
    return (
        dict(family="IBM Plex Sans", color="#7a92b4", size=11),
        "#1a2f52", "#0a1628", "#04090f",
    )


def _clean_file_label(raw_name):
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


def process_file(file):
    """
    Parse a filled control template.
    ALL rows with a non-blank Requirement are counted as controls.
    'Select' (unfilled default) rows are marked 'Not Assessed'.
    """
    df = pd.read_excel(file, engine="openpyxl", header=2)
    df.columns = df.columns.astype(str).str.strip()

    impl_col = find_col(df, CONTROL_COL)
    req_col  = find_col(df, "requirement")

    if not impl_col or not req_col:
        return None

    # Keep only rows that have an actual Requirement (real control rows)
    df = df[
        df[req_col].notna() &
        (df[req_col].astype(str).str.strip().str.lower() != "nan") &
        (df[req_col].astype(str).str.strip() != "")
    ].copy()

    if df.empty:
        return None

    df["_status"] = df[impl_col].apply(
        lambda v: STATUS_NORM.get(str(v).strip().lower(), "Not Assessed")
    )
    df["_source"]       = file.name
    df["_source_label"] = _clean_file_label(file.name)
    return df


# ── Charts ────────────────────────────────────────────────────────────────────

def gauge_chart(pct, risk):
    CHART_FONT, GRID_COLOR, GAUGE_BG, PIE_LINE = _chart_settings()
    color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 60 else "#ef4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 40, "color": color, "family": "Rajdhani"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": GRID_COLOR,
                     "tickfont": {"color": CHART_FONT["color"], "size": 9}},
            "bar":  {"color": color, "thickness": 0.22},
            "bgcolor": GAUGE_BG,
            "borderwidth": 0,
            "steps": [
                {"range": [0,  60], "color": "rgba(239,68,68,0.07)"},
                {"range": [60, 80], "color": "rgba(245,158,11,0.07)"},
                {"range": [80,100], "color": "rgba(34,197,94,0.07)"},
            ],
            "threshold": {"line": {"color": color, "width": 3},
                          "thickness": 0.78, "value": pct},
        },
        title={"text": f"<b>{risk}</b>",
               "font": {"size": 12, "color": CHART_FONT["color"], "family": "IBM Plex Sans"}},
    ))
    fig.update_layout(
        height=255, margin=dict(t=28, b=8, l=28, r=28),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, font=CHART_FONT,
    )
    return fig


def donut_chart(compliant, partial, non, na, not_assessed):
    CHART_FONT, GRID_COLOR, GAUGE_BG, PIE_LINE = _chart_settings()
    raw = [
        ("Compliant",           compliant,    "#22c55e"),
        ("Partially Compliant", partial,      "#f59e0b"),
        ("Not Compliant",       non,          "#ef4444"),
        ("Not Applicable",      na,           "#64748b"),
        ("Not Assessed",        not_assessed, "#334155"),
    ]
    filtered = [(l, v, c) for l, v, c in raw if v > 0]
    if not filtered:
        filtered = [("No Data", 1, "#334155")]

    f_labels = [x[0] for x in filtered]
    f_values = [x[1] for x in filtered]
    f_colors = [x[2] for x in filtered]

    fig = go.Figure(go.Pie(
        labels=f_labels, values=f_values,
        hole=0.62,
        marker=dict(colors=f_colors, line=dict(color=PIE_LINE, width=2)),
        textinfo="percent",
        textfont=dict(size=10, color="white"),
        hovertemplate="%{label}: %{value} controls (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        height=270, margin=dict(t=8, b=8, l=8, r=8),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, font=CHART_FONT,
        legend=dict(orientation="v", x=1.02, y=0.5,
                    font=dict(size=10, color=CHART_FONT["color"]),
                    bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def compliance_heatmap(all_data):
    """Horizontal bar — compliance % per annex."""
    CHART_FONT, GRID_COLOR, GAUGE_BG, PIE_LINE = _chart_settings()
    rows = []
    for df in all_data:
        name  = df["_source_label"].iloc[0]
        total = len(df)
        na    = (df["_status"] == "Not Applicable").sum()
        nass  = (df["_status"] == "Not Assessed").sum()
        eff   = total - na - nass
        comp  = (df["_status"] == "Compliant").sum()
        pct   = round((comp / eff) * 100, 1) if eff > 0 else 0
        rows.append({"Annex": name, "Compliance %": pct, "Total": total,
                     "Assessed": total - nass})

    df_h = pd.DataFrame(rows)
    colors = ["#22c55e" if p >= 80 else "#f59e0b" if p >= 60 else "#ef4444"
              for p in df_h["Compliance %"]]

    fig = go.Figure(go.Bar(
        x=df_h["Compliance %"],
        y=df_h["Annex"],
        orientation="h",
        marker_color=colors,
        text=[f"{p}%" for p in df_h["Compliance %"]],
        textposition="outside",
        customdata=df_h[["Total", "Assessed"]].values,
        hovertemplate="<b>%{y}</b><br>Compliance: %{x}%<br>Controls: %{customdata[0]}<br>Assessed: %{customdata[1]}<extra></extra>",
    ))
    fig.update_layout(
        height=max(160, len(rows) * 56 + 40),
        margin=dict(t=10, b=10, l=10, r=65),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, font=CHART_FONT,
        xaxis=dict(range=[0, 120], showgrid=True, gridcolor=GRID_COLOR,
                   title="Compliance %", ticksuffix="%"),
        yaxis=dict(showgrid=False),
        bargap=0.35,
    )
    return fig


def bar_by_file(all_data):
    CHART_FONT, GRID_COLOR, GAUGE_BG, PIE_LINE = _chart_settings()
    rows = []
    for df in all_data:
        name = df["_source_label"].iloc[0]
        vc   = df["_status"].value_counts()
        rows.append({
            "Annex":               name,
            "Compliant":           vc.get("Compliant", 0),
            "Partially Compliant": vc.get("Partially Compliant", 0),
            "Not Compliant":       vc.get("Not Compliant", 0),
            "Not Applicable":      vc.get("Not Applicable", 0),
            "Not Assessed":        vc.get("Not Assessed", 0),
        })

    df_plot = pd.DataFrame(rows)
    status_cols = [c for c in ["Compliant", "Partially Compliant", "Not Compliant",
                                "Not Applicable", "Not Assessed"]
                   if c in df_plot.columns and df_plot[c].sum() > 0]

    fig = px.bar(
        df_plot, x="Annex", y=status_cols,
        barmode="stack", color_discrete_map=COLORS,
    )
    fig.update_layout(
        height=290, margin=dict(t=8, b=65, l=8, r=8),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, font=CHART_FONT,
        legend=dict(orientation="h", y=-0.44, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(tickangle=-20, showgrid=False, title=""),
        yaxis=dict(gridcolor=GRID_COLOR, title="Controls"),
        bargap=0.3,
    )
    fig.update_traces(marker_line_width=0)
    return fig


def section_chart(combined):
    CHART_FONT, GRID_COLOR, GAUGE_BG, PIE_LINE = _chart_settings()
    sec_col = find_col(combined, "section")
    if not sec_col:
        return None

    combined = combined.copy()
    combined["_sec_short"] = combined[sec_col].astype(str).str.slice(0, 28)

    pivot = (
        combined.groupby(["_sec_short", "_status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"_sec_short": "Section"})
    )

    bar_cols = [c for c in ["Compliant", "Partially Compliant", "Not Compliant", "Not Assessed"]
                if c in pivot.columns]
    pivot["_total"]    = pivot[bar_cols].sum(axis=1)
    pivot["_comp_pct"] = (
        pivot.get("Compliant", pd.Series([0]*len(pivot), dtype=float)) /
        pivot["_total"].replace(0, 1) * 100
    ).round(1)

    fig = px.bar(
        pivot, x="Section", y=bar_cols,
        barmode="group", color_discrete_map=COLORS,
        labels={"value": "Controls", "variable": "Status"},
    )
    fig.add_scatter(
        x=pivot["Section"], y=pivot["_comp_pct"],
        mode="lines+markers", name="Compliance %", yaxis="y2",
        line=dict(color="#c9a84c", width=2, dash="dot"),
        marker=dict(size=7, color="#c9a84c", symbol="diamond"),
        hovertemplate="Compliance: %{y:.1f}%<extra></extra>",
    )
    fig.update_layout(
        height=330, margin=dict(t=10, b=95, l=10, r=55),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, font=CHART_FONT,
        legend=dict(orientation="h", y=-0.52, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(tickangle=-30, showgrid=False),
        yaxis=dict(gridcolor=GRID_COLOR, title="Controls"),
        yaxis2=dict(title="Compliance %", overlaying="y", side="right",
                    range=[0, 115], showgrid=False,
                    tickfont=dict(color="#c9a84c", size=10),
                    title_font=dict(color="#c9a84c")),
        bargap=0.25,
    )
    fig.update_traces(marker_line_width=0, selector=dict(type="bar"))
    return fig


def _render_dashboard(combined, all_data, file_names):
    counts       = combined["_status"].value_counts().to_dict()
    total        = len(combined)
    compliant    = counts.get("Compliant", 0)
    partial      = counts.get("Partially Compliant", 0)
    non          = counts.get("Not Compliant", 0)
    na           = counts.get("Not Applicable", 0)
    not_assessed = counts.get("Not Assessed", 0)

    effective = total - na - not_assessed
    pct       = round((compliant / effective) * 100, 1) if effective > 0 else 0

    if pct >= 80:   risk, risk_color, risk_badge = "Low Risk",      "#22c55e", "badge-green"
    elif pct >= 60: risk, risk_color, risk_badge = "Moderate Risk", "#f59e0b", "badge-amber"
    else:           risk, risk_color, risk_badge = "High Risk",     "#ef4444", "badge-red"

    # Files pill row
    labels_uploaded = [_clean_file_label(n) for n in file_names]
    pills_html = " ".join(
        f'<span class="rbi-badge badge-grey">{lbl}</span>'
        for lbl in labels_uploaded
    )
    st.markdown(f"""
    <div style="margin-bottom:14px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
        <span style="font-size:11px; color:var(--text-dim);">Files loaded:</span>
        {pills_html}
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Strip ──────────────────────────────────────────────
    st.markdown('<div class="rbi-section-title">Overview</div>', unsafe_allow_html=True)
    assessed_pct = round(((total - not_assessed) / total * 100), 1) if total else 0

    st.markdown(f"""
    <div class="rbi-stat-strip">
        <div class="rbi-stat-item">
            <div class="stat-label">Total Controls</div>
            <div class="stat-value">{total}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Compliant</div>
            <div class="stat-value" style="color:var(--compliant);">{compliant}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Partial</div>
            <div class="stat-value" style="color:var(--partial);">{partial}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Non-Compliant</div>
            <div class="stat-value" style="color:var(--noncompliant);">{non}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Not Applicable</div>
            <div class="stat-value" style="color:var(--na);">{na}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Not Assessed</div>
            <div class="stat-value" style="color:#64748b;">{not_assessed}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Score</div>
            <div class="stat-value" style="color:{risk_color};">{pct}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Not-assessed banner
    if not_assessed > 0:
        st.markdown(f"""
        <div style="background:rgba(71,85,105,0.12); border:1px solid #334155;
                    border-left:3px solid #64748b; border-radius:10px;
                    padding:10px 16px; margin-bottom:14px; font-size:12px;
                    color:var(--text-secondary);">
            ⚠️ <strong>{not_assessed}</strong> control(s) not yet assessed (status still "Select").
            Score is calculated on assessed controls only
            (<strong>{total - not_assessed}</strong> of <strong>{total}</strong>).
            Fill-rate: <strong>{assessed_pct}%</strong>
        </div>
        """, unsafe_allow_html=True)

    # ── Row 1: Gauge · Donut · Compliance % per annex ─────────
    st.markdown('<div class="rbi-section-title">Compliance Score</div>', unsafe_allow_html=True)
    g1, g2, g3 = st.columns([1.15, 1.15, 1.7])

    with g1:
        st.plotly_chart(gauge_chart(pct, risk), use_container_width=True)
        st.markdown(
            f'<div style="text-align:center;margin-top:-12px;">'
            f'<span class="rbi-badge {risk_badge}">{risk.upper()}</span></div>',
            unsafe_allow_html=True,
        )

    with g2:
        st.markdown('<div class="rbi-label" style="margin-bottom:4px; margin-left:6px;">STATUS SPLIT</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(donut_chart(compliant, partial, non, na, not_assessed),
                        use_container_width=True)

    with g3:
        if all_data:
            st.markdown('<div class="rbi-label" style="margin-bottom:4px; margin-left:6px;">COMPLIANCE % BY ANNEX</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(compliance_heatmap(all_data), use_container_width=True)
        else:
            st.info("Upload files to see per-annex compliance %.")

    # ── Row 2: Stacked bar by annex ────────────────────────────
    if all_data:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="rbi-section-title">Controls by Annex'
                    '<span style="font-size:10px; color:var(--text-dim); font-weight:400; margin-left:8px;">'
                    '— stacked by status</span></div>', unsafe_allow_html=True)
        st.plotly_chart(bar_by_file(all_data), use_container_width=True)

    # ── Row 3: Section breakdown ───────────────────────────────
    fig_sec = section_chart(combined)
    if fig_sec:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="rbi-section-title">Section-wise Breakdown'
            '<span style="font-size:10px; color:var(--text-dim); font-weight:400; margin-left:8px;">'
            '— bars = control counts &nbsp;·&nbsp; gold line = compliance %</span></div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig_sec, use_container_width=True)

    # Annex IV callout
    if any("annex4" in n.lower().replace("-","").replace(" ","").replace("_","")
           for n in file_names):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="rbi-card rbi-card-blue" style="padding:14px 20px;">
            <div style="font-family:'Rajdhani',sans-serif;font-size:14px;
                        font-weight:700;color:#a855f7;margin-bottom:6px;">
                📙 Annex IV — Governance Controls Note
            </div>
            <div style="font-size:12px;color:var(--text-secondary);line-height:1.7;">
                Annex IV controls cover C-SOC setup, CISO appointment, and Board-level IT governance
                committees. Ensure responses reflect <strong>actual committee formations and documented
                policies</strong>. Non-compliant governance controls are
                <strong style="color:var(--noncompliant);">High Priority</strong> gaps.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Progress bar ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;margin-bottom:8px;align-items:center;">
        <div class="rbi-label">Overall Compliance Progress</div>
        <div style="font-family:'Rajdhani',sans-serif;font-size:20px;
                    font-weight:700;color:{risk_color};">{pct}%</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(pct / 100)

    # ── Detailed data expander ─────────────────────────────────
    with st.expander("📋  View & Download Detailed Control Data"):
        display_cols = []
        for kw in ["sr", "section", "sub-section", "requirement"]:
            c = find_col(combined, kw)
            if c and c not in display_cols:
                display_cols.append(c)
        for kw in ["_status", "_source_label"]:
            c = next((col for col in combined.columns if kw.lower() in col.lower()), None)
            if c and c not in display_cols:
                display_cols.append(c)
        display_cols = [c for c in display_cols if c in combined.columns]

        show_df = combined[display_cols].rename(columns={
            "_status": "Status", "_source_label": "Annex"
        })

        status_filter = st.multiselect(
            "Filter by Status",
            options=["Compliant", "Partially Compliant", "Not Compliant",
                     "Not Applicable", "Not Assessed"],
            default=["Compliant", "Partially Compliant", "Not Compliant",
                     "Not Applicable", "Not Assessed"],
            key="m3_status_filter",
        )
        show_df_f = show_df[show_df["Status"].isin(status_filter)]
        st.dataframe(show_df_f, use_container_width=True, height=340)
        csv = show_df_f.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Control Data (CSV)", csv,
            file_name="Compliance_Data.csv", mime="text/csv",
            use_container_width=True,
        )

    # ── Save to session ────────────────────────────────────────
    st.session_state["compliance_summary"] = {
        "total":        total,
        "compliant":    compliant,
        "partial":      partial,
        "non":          non,
        "na":           na,
        "not_assessed": not_assessed,
        "percent":      pct,
        "risk":         risk,
    }
    st.session_state["combined_df"] = combined


def show_module3():
    st.markdown("""
    <div class="rbi-page-header">
        <h1>📊 MODULE 3 — COMPLIANCE DASHBOARD</h1>
        <p>Upload your filled control templates to generate a real-time compliance analysis</p>
    </div>
    """, unsafe_allow_html=True)

    level = st.session_state.get("bank_level", "")
    if level == "Level-IV":
        st.markdown("""
        <div class="rbi-card rbi-card-blue" style="padding:14px 20px;margin-bottom:16px;
             display:flex;align-items:center;gap:14px;">
            <div style="font-size:22px;flex-shrink:0;">📙</div>
            <div style="font-size:12.5px;color:var(--text-secondary);line-height:1.6;">
                <strong style="color:#a855f7;">Level-IV Bank Detected</strong> — Upload all
                <strong>5 template files</strong> (Basic + Annex I + II + III + IV) for a complete
                dashboard covering all <strong>122 controls</strong>. Unfilled rows (status = "Select")
                are counted as <strong>Not Assessed</strong> and excluded from the score.
            </div>
        </div>
        """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload Filled Control Files", type=["xlsx"],
        accept_multiple_files=True, label_visibility="collapsed",
    )

    saved_summary  = st.session_state.get("compliance_summary")
    saved_combined = st.session_state.get("combined_df")

    if not uploaded_files:
        if saved_summary and saved_combined is not None and not saved_combined.empty:
            saved_file_names = st.session_state.get("_m3_files", [])
            st.info("📂 Showing previously saved dashboard data. Upload new files above to refresh.")
            _render_dashboard(saved_combined, [], saved_file_names)
        else:
            expected = {
                "Level-I":   "2 files  (Basic + Annex I = 60 controls)",
                "Level-II":  "3 files  (Basic + Annex I + II = 83 controls)",
                "Level-III": "4 files  (Basic + Annex I + II + III = 108 controls)",
                "Level-IV":  "5 files  (Basic + Annex I + II + III + IV = 122 controls)",
            }.get(level, "all applicable template files")
            st.markdown(f"""
            <div class="rbi-card" style="text-align:center;padding:52px 32px;color:var(--text-dim);">
                <div style="font-size:42px;margin-bottom:14px;">📂</div>
                <div style="font-family:'Rajdhani',sans-serif;font-size:19px;color:var(--text-secondary);">
                    Upload your filled template files to view the compliance dashboard
                </div>
                <div style="font-size:12px;color:var(--text-dim);margin-top:8px;">
                    Accepts .xlsx — upload {expected}
                </div>
            </div>
            """, unsafe_allow_html=True)
        return

    all_data, file_names, skipped = [], [], []
    for f in uploaded_files:
        df = process_file(f)
        if df is not None and not df.empty:
            all_data.append(df)
            file_names.append(f.name)
        else:
            skipped.append(f.name)

    if skipped:
        st.warning(f"⚠️ Skipped (no valid data / missing columns): {', '.join(skipped)}")
    if not all_data:
        st.error("No valid data found. Please check the file format.")
        return

    prev_files = st.session_state.get("_m3_files", [])
    if sorted(file_names) != sorted(prev_files):
        _log("upload", f"{len(file_names)} file(s) uploaded to Dashboard",
             detail=", ".join(file_names))
        st.session_state["_m3_files"] = file_names

    combined = pd.concat(all_data, ignore_index=True)
    _render_dashboard(combined, all_data, file_names)