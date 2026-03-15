import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CONTROL_COL = "control implemented"

# "Select" is the unfilled dropdown default in Annex IV — treat as None (skip)
STATUS_NORM = {
    "fully implemented":     "Compliant",
    "compliant":             "Compliant",
    "partially implemented": "Partially Compliant",
    "partially compliant":   "Partially Compliant",
    "no":                    "Not Compliant",
    "not compliant":         "Not Compliant",
    "not applicable":        "Not Applicable",
    "n/a":                   "Not Applicable",
    "select":                None,   # Annex IV unfilled default — ignore
}

COLORS = {
    "Compliant":           "#22c55e",
    "Partially Compliant": "#f59e0b",
    "Not Compliant":       "#ef4444",
    "Not Applicable":      "#64748b",
}

# Clean display labels for file names shown in charts
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
            "#e2e8f0",
            "#f1f5f9",
            "#f0f4f8",
        )
    return (
        dict(family="IBM Plex Sans", color="#7a92b4", size=11),
        "#1a2f52",
        "#0a1628",
        "#04090f",
    )


def _clean_file_label(raw_name):
    """Convert raw filename to readable annex label."""
    key = raw_name.lower().replace(".xlsx", "").strip()
    for pattern, label in FILE_LABELS.items():
        if pattern in key:
            return label
    # Fallback: strip extension and underscores
    return raw_name.replace(".xlsx", "").replace("_", " ").strip()


def find_col(df, keyword):
    for col in df.columns:
        if keyword in col.lower():
            return col
    return None


def process_file(file):
    df = pd.read_excel(file, engine="openpyxl", header=2)
    df.columns = df.columns.astype(str).str.strip()
    impl_col = find_col(df, CONTROL_COL)
    if not impl_col:
        return None
    df["_status"] = df[impl_col].apply(
        lambda v: STATUS_NORM.get(str(v).strip().lower(), None)
    )
    # Drop rows where status is None (unfilled "Select" entries or unrecognised values)
    df = df[df["_status"].notna()]
    df["_source"]       = file.name
    df["_source_label"] = _clean_file_label(file.name)
    return df


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
        title={
            "text": f"<b>{risk}</b>",
            "font": {"size": 12, "color": CHART_FONT["color"], "family": "IBM Plex Sans"},
        },
    ))
    fig.update_layout(
        height=255, margin=dict(t=28, b=8, l=28, r=28),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, font=CHART_FONT,
    )
    return fig


def donut_chart(compliant, partial, non, na):
    CHART_FONT, GRID_COLOR, GAUGE_BG, PIE_LINE = _chart_settings()
    labels = ["Compliant", "Partially Compliant", "Not Compliant", "Not Applicable"]
    fig = go.Figure(go.Pie(
        labels=labels, values=[compliant, partial, non, na],
        hole=0.62,
        marker=dict(colors=[COLORS[l] for l in labels],
                    line=dict(color=PIE_LINE, width=2)),
        textinfo="percent",
        textfont=dict(size=10, color="white"),
        hovertemplate="%{label}: %{value} controls<extra></extra>",
    ))
    fig.update_layout(
        height=270, margin=dict(t=8, b=8, l=8, r=8),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, font=CHART_FONT,
        legend=dict(
            orientation="v", x=1.02, y=0.5,
            font=dict(size=10, color=CHART_FONT["color"]),
            bgcolor="rgba(0,0,0,0)",
        ),
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
        })
    fig = px.bar(
        pd.DataFrame(rows), x="Annex",
        y=["Compliant", "Partially Compliant", "Not Compliant"],
        barmode="stack", color_discrete_map=COLORS,
    )
    fig.update_layout(
        height=270, margin=dict(t=8, b=60, l=8, r=8),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, font=CHART_FONT,
        legend=dict(orientation="h", y=-0.38, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(tickangle=-20, showgrid=False, title=""),
        yaxis=dict(gridcolor=GRID_COLOR, title=""),
        bargap=0.3,
    )
    fig.update_traces(marker_line_width=0)
    return fig


def section_chart(combined):
    """Grouped bar chart with compliance-% line overlay per section."""
    CHART_FONT, GRID_COLOR, GAUGE_BG, PIE_LINE = _chart_settings()
    sec_col = find_col(combined, "section")
    if not sec_col:
        return None

    pivot = (
        combined.groupby([sec_col, "_status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={sec_col: "Section"})
    )

    bar_cols = [c for c in ["Compliant", "Partially Compliant", "Not Compliant"]
                if c in pivot.columns]
    pivot["_total"]    = pivot[bar_cols].sum(axis=1)
    pivot["_comp_pct"] = (
        pivot.get("Compliant", 0) / pivot["_total"].replace(0, 1) * 100
    ).round(1)

    fig = px.bar(
        pivot, x="Section", y=bar_cols,
        barmode="group", color_discrete_map=COLORS,
        labels={"value": "Controls", "variable": "Status"},
    )
    fig.add_scatter(
        x=pivot["Section"], y=pivot["_comp_pct"],
        mode="lines+markers",
        name="Compliance %",
        yaxis="y2",
        line=dict(color="#c9a84c", width=2, dash="dot"),
        marker=dict(size=7, color="#c9a84c", symbol="diamond"),
        hovertemplate="Compliance: %{y:.1f}%<extra></extra>",
    )
    fig.update_layout(
        height=310, margin=dict(t=10, b=90, l=10, r=50),
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG, font=CHART_FONT,
        legend=dict(orientation="h", y=-0.48, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(tickangle=-30, showgrid=False),
        yaxis=dict(gridcolor=GRID_COLOR, title="Controls"),
        yaxis2=dict(
            title="Compliance %", overlaying="y", side="right",
            range=[0, 110], showgrid=False,
            tickfont=dict(color="#c9a84c", size=10),
            title_font=dict(color="#c9a84c"),
        ),
        bargap=0.25,
    )
    fig.update_traces(marker_line_width=0, selector=dict(type="bar"))
    return fig


def _render_dashboard(combined, all_data, file_names):
    """Render the compliance dashboard from a combined DataFrame."""
    counts    = combined["_status"].value_counts().to_dict()
    total     = len(combined)
    compliant = counts.get("Compliant", 0)
    partial   = counts.get("Partially Compliant", 0)
    non       = counts.get("Not Compliant", 0)
    na        = counts.get("Not Applicable", 0)
    effective = total - na
    pct       = round((compliant / effective) * 100, 1) if effective else 0

    if pct >= 80:   risk, risk_color, risk_badge = "Low Risk",      "#22c55e", "badge-green"
    elif pct >= 60: risk, risk_color, risk_badge = "Moderate Risk", "#f59e0b", "badge-amber"
    else:           risk, risk_color, risk_badge = "High Risk",     "#ef4444", "badge-red"

    # ── Files uploaded pill row ────────────────────────────────
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
            <div class="stat-label">Score</div>
            <div class="stat-value" style="color:{risk_color};">{pct}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Charts ─────────────────────────────────────────────────
    st.markdown('<div class="rbi-section-title">Compliance Score</div>', unsafe_allow_html=True)
    g1, g2, g3 = st.columns([1.15, 1.15, 1.7])

    with g1:
        st.plotly_chart(gauge_chart(pct, risk), width='stretch')
        st.markdown(
            f'<div style="text-align:center;margin-top:-12px;">'
            f'<span class="rbi-badge {risk_badge}">{risk.upper()}</span></div>',
            unsafe_allow_html=True,
        )

    with g2:
        st.markdown('<div class="rbi-label" style="margin-bottom:4px; margin-left:6px;">STATUS SPLIT</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(donut_chart(compliant, partial, non, na), width='stretch')

    with g3:
        st.markdown('<div class="rbi-label" style="margin-bottom:4px; margin-left:6px;">BY ANNEX</div>',
                    unsafe_allow_html=True)
        if all_data:
            st.plotly_chart(bar_by_file(all_data), width='stretch')
        else:
            st.info("Detailed per-annex chart requires re-uploading files.")

    # ── Section chart ──────────────────────────────────────────
    fig_sec = section_chart(combined)
    if fig_sec:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="rbi-section-title">Section-wise Breakdown'
            '  <span style="font-size:10px; color:var(--text-dim); font-weight:400;">'
            '— bars = control counts · gold line = compliance %</span></div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig_sec, width='stretch')

    # ── Annex IV specific callout ──────────────────────────────
    if any("annex-4" in n.lower() or "annex_4" in n.lower() for n in file_names):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="rbi-card rbi-card-blue" style="padding:14px 20px;">
            <div style="font-family:'Rajdhani',sans-serif; font-size:14px;
                        font-weight:700; color:#a855f7; margin-bottom:6px;">
                📙 Annex IV — Governance Controls Note
            </div>
            <div style="font-size:12px; color:var(--text-secondary); line-height:1.7;">
                Annex IV controls cover C-SOC setup, CISO appointment, and Board-level IT governance committees.
                These are organisational/governance controls — ensure your responses reflect
                <strong>actual committee formations and documented policies</strong>, not just intentions.
                Non-compliant governance controls are considered <strong style="color:var(--noncompliant);">High Priority</strong> gaps.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Progress Bar ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; margin-bottom:8px; align-items:center;">
        <div class="rbi-label">Overall Compliance Progress</div>
        <div style="font-family:'Rajdhani',sans-serif; font-size:20px;
                    font-weight:700; color:{risk_color};">{pct}%</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(pct / 100)

    # ── Save to session ────────────────────────────────────────
    st.session_state["compliance_summary"] = {
        "total": total, "compliant": compliant, "partial": partial,
        "non": non, "na": na, "percent": pct, "risk": risk,
    }
    st.session_state["combined_df"] = combined


def show_module3():
    st.markdown("""
    <div class="rbi-page-header">
        <h1>📊 MODULE 3 — COMPLIANCE DASHBOARD</h1>
        <p>Upload your filled control templates to generate a real-time compliance analysis</p>
    </div>
    """, unsafe_allow_html=True)

    # Level-IV guidance banner
    level = st.session_state.get("bank_level", "")
    if level == "Level-IV":
        st.markdown("""
        <div class="rbi-card rbi-card-blue" style="padding:14px 20px; margin-bottom:16px;
             display:flex; align-items:center; gap:14px;">
            <div style="font-size:22px; flex-shrink:0;">📙</div>
            <div style="font-size:12.5px; color:var(--text-secondary); line-height:1.6;">
                <strong style="color:#a855f7;">Level-IV Bank Detected</strong> — Upload all
                <strong>5 template files</strong> (Basic Framework + Annex I + II + III + IV)
                for a complete dashboard. Annex IV uses a dropdown — only filled rows
                (not "Select") are counted.
            </div>
        </div>
        """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload Filled Control Files", type=["xlsx"],
        accept_multiple_files=True, label_visibility="collapsed",
    )

    # ── Check for saved session data ───────────────────────────
    saved_summary = st.session_state.get("compliance_summary")
    saved_combined = st.session_state.get("combined_df")

    if not uploaded_files:
        if saved_summary and saved_combined is not None and not saved_combined.empty:
            # Restore from previously saved data
            saved_file_names = st.session_state.get("_m3_files", [])
            st.info("📂 Showing previously saved dashboard data. Upload new files above to refresh.")
            _render_dashboard(saved_combined, [], saved_file_names)
        else:
            expected = {
                "Level-I": "2", "Level-II": "3",
                "Level-III": "4", "Level-IV": "5",
            }.get(level, "all applicable")
            st.markdown(f"""
            <div class="rbi-card" style="text-align:center; padding:52px 32px; color:var(--text-dim);">
                <div style="font-size:42px; margin-bottom:14px;">📂</div>
                <div style="font-family:'Rajdhani',sans-serif; font-size:19px; color:var(--text-secondary);">
                    Upload your filled template files to view the compliance dashboard
                </div>
                <div style="font-size:12px; color:var(--text-dim); margin-top:8px;">
                    Accepts .xlsx — upload {expected} file(s) simultaneously for {level or 'your tier'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        return

    # ── Process files ──────────────────────────────────────────
    all_data   = []
    file_names = []
    skipped    = []
    for f in uploaded_files:
        df = process_file(f)
        if df is not None and not df.empty:
            all_data.append(df)
            file_names.append(f.name)
        else:
            skipped.append(f.name)

    if skipped:
        st.warning(f"⚠️ Skipped (no valid data / missing 'Control Implemented?' column): {', '.join(skipped)}")

    if not all_data:
        st.error("No valid data found in any uploaded file. Please check the file format.")
        return

    # Log uploads (only if changed)
    prev_files = st.session_state.get("_m3_files", [])
    if sorted(file_names) != sorted(prev_files):
        _log("upload", f"{len(file_names)} file(s) uploaded to Dashboard",
             detail=", ".join(file_names))
        st.session_state["_m3_files"] = file_names

    combined = pd.concat(all_data, ignore_index=True)
    _render_dashboard(combined, all_data, file_names)