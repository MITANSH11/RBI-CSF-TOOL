import streamlit as st
import pandas as pd
from datetime import date
import io


def _log(event_type, action, detail=""):
    try:
        from module7_audit import log_event
        log_event(event_type, action, detail, module="module5")
    except Exception:
        pass


# ══════════════════════════════════════════════════════
#  WORD REPORT GENERATOR
# ══════════════════════════════════════════════════════
def generate_docx(bank_name, level, today, summary, gaps):
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    doc = Document()
    for sec in doc.sections:
        sec.left_margin = sec.right_margin = Cm(2.5)
        sec.top_margin  = sec.bottom_margin = Cm(2)

    NAVY  = RGBColor(0x1e, 0x3a, 0x5f)
    GOLD  = RGBColor(0x92, 0x66, 0x0a)
    BLACK = RGBColor(0x0f, 0x17, 0x2a)
    GREY  = RGBColor(0x47, 0x55, 0x69)
    GREEN = RGBColor(0x15, 0x80, 0x3d)
    AMBER = RGBColor(0xb4, 0x53, 0x09)
    RED   = RGBColor(0xb9, 0x1c, 0x1c)

    pct = summary["percent"]
    risk = summary["risk"]
    risk_color = GREEN if pct >= 80 else AMBER if pct >= 60 else RED

    def heading(text, lvl=1, color=None):
        p = doc.add_heading(text, level=lvl)
        if p.runs:
            p.runs[0].font.color.rgb = color or NAVY
            p.runs[0].font.bold = True
        return p

    def para(text, color=None, bold=False, size=10, align=None):
        p = doc.add_paragraph()
        r = p.add_run(text)
        r.font.size       = Pt(size)
        r.font.bold       = bold
        r.font.color.rgb  = color or BLACK
        if align:
            p.alignment = align
        return p

    def shade_cell(cell, hex_color):
        tc   = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd  = OxmlElement("w:shd")
        shd.set(qn("w:val"),   "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"),  hex_color)
        tcPr.append(shd)

    # Title
    t = doc.add_heading("RBI CYBERSECURITY GAP ANALYSIS REPORT", 0)
    if t.runs:
        t.runs[0].font.color.rgb = NAVY
        t.runs[0].font.size = Pt(18)

    para("Primary Urban Cooperative Banks — RBI Graded Approach Framework", color=GREY, size=10)
    doc.add_paragraph()

    # Bank details
    heading("Bank Details", 1)
    dt = doc.add_table(rows=2, cols=4)
    dt.style = "Table Grid"
    labels = ["Bank Name", "Compliance Level", "Report Date", "Risk Category"]
    vals   = [bank_name, level, today, risk]
    for i, (lbl, val) in enumerate(zip(labels, vals)):
        row_i, col_i = divmod(i, 2)
        cell_lbl = dt.rows[row_i].cells[col_i * 2]
        cell_val = dt.rows[row_i].cells[col_i * 2 + 1]
        cell_lbl.text = lbl
        cell_val.text = val
        shade_cell(cell_lbl, "EFF6FF")
        cell_lbl.paragraphs[0].runs[0].font.bold      = True
        cell_lbl.paragraphs[0].runs[0].font.color.rgb = NAVY
        cell_lbl.paragraphs[0].runs[0].font.size      = Pt(9)
        cell_val.paragraphs[0].runs[0].font.size       = Pt(9)
    doc.add_paragraph()

    # Score
    heading("Compliance Score", 1)
    sc = doc.add_table(rows=1, cols=3)
    sc.style = "Table Grid"
    sc.rows[0].cells[0].text = f"Score: {pct}%"
    sc.rows[0].cells[1].text = f"Risk: {risk}"
    if pct >= 80:   verdict_txt = "Strong compliance posture."
    elif pct >= 60: verdict_txt = "Moderate compliance — gaps require attention."
    else:           verdict_txt = "Critical deficiencies — immediate action required."
    sc.rows[0].cells[2].text = verdict_txt
    shade_clr = "F0FDF4" if pct >= 80 else "FFFBEB" if pct >= 60 else "FEF2F2"
    for i, cell in enumerate(sc.rows[0].cells):
        shade_cell(cell, shade_clr)
        run = cell.paragraphs[0].runs[0] if cell.paragraphs[0].runs else cell.paragraphs[0].add_run(cell.text)
        run.font.bold      = (i < 2)
        run.font.color.rgb = risk_color
        run.font.size      = Pt(10 if i < 2 else 9)
    doc.add_paragraph()

    # Metrics
    heading("Compliance Metrics", 1)
    mt = doc.add_table(rows=1, cols=2)
    mt.style = "Table Grid"
    for cell, txt in zip(mt.rows[0].cells, ["Metric", "Value"]):
        cell.text = txt
        shade_cell(cell, "1E3A5F")
        r = cell.paragraphs[0].runs[0]
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        r.font.bold = True
        r.font.size = Pt(9)

    for i, (lbl, val) in enumerate([
        ("Total Controls Assessed",  str(summary["total"])),
        ("Compliant Controls",        str(summary["compliant"])),
        ("Partially Compliant",       str(summary["partial"])),
        ("Non-Compliant Controls",    str(summary["non"])),
        ("Not Applicable",            str(summary["na"])),
        ("Compliance Score",          f"{pct}%"),
        ("Risk Category",             risk),
    ]):
        row = mt.add_row()
        row.cells[0].text = lbl
        row.cells[1].text = val
        fill = "F8FAFC" if i % 2 == 0 else "FFFFFF"
        shade_cell(row.cells[0], fill)
        shade_cell(row.cells[1], fill)
        for cell in row.cells:
            if cell.paragraphs[0].runs:
                cell.paragraphs[0].runs[0].font.size = Pt(9)
    doc.add_paragraph()

    # Gaps
    if gaps is not None and not gaps.empty:
        heading("Key Compliance Gaps", 1)
        sec_col = next((c for c in gaps.columns if "section"     in c.lower()), None)
        req_col = next((c for c in gaps.columns if "requirement" in c.lower()), None)
        sc_col  = "_status"  if "_status"  in gaps.columns else None
        pc_col  = "Priority" if "Priority" in gaps.columns else None
        show_c  = [c for c in [sec_col, req_col, sc_col, pc_col] if c and c in gaps.columns]

        if show_c:
            gap_show = gaps[show_c].rename(columns={"_status": "Status"}).head(25)
            gt = doc.add_table(rows=1, cols=len(show_c))
            gt.style = "Table Grid"
            for i, col in enumerate(gap_show.columns):
                cell = gt.rows[0].cells[i]
                cell.text = col
                shade_cell(cell, "1E3A5F")
                r = cell.paragraphs[0].runs[0]
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                r.font.bold = True
                r.font.size = Pt(8)
            for ri, (_, row) in enumerate(gap_show.iterrows()):
                tr   = gt.add_row()
                fill = "F8FAFC" if ri % 2 == 0 else "FFFFFF"
                for i, val in enumerate(row):
                    tr.cells[i].text = str(val) if val is not None else ""
                    shade_cell(tr.cells[i], fill)
                    if tr.cells[i].paragraphs[0].runs:
                        tr.cells[i].paragraphs[0].runs[0].font.size = Pt(8)
        doc.add_paragraph()

    # Recommendations
    heading("Recommendations", 1)
    recs = []
    if summary["non"]     > 0: recs.append(f"Immediately remediate {summary['non']} non-compliant controls.")
    if summary["partial"] > 0: recs.append(f"Develop a 90-day action plan for {summary['partial']} partially compliant controls.")
    if pct < 80:
        recs.append("Conduct cybersecurity awareness training for all relevant staff.")
        recs.append("Assign a dedicated Cybersecurity Officer to track remediation progress.")
        recs.append("Perform quarterly internal compliance re-assessments and maintain evidence artefacts.")
        recs.append("Submit compliance reports to RBI as per prescribed timelines.")

    for i, rec in enumerate(recs, 1):
        p = doc.add_paragraph(style="List Number")
        r = p.add_run(rec)
        r.font.size      = Pt(10)
        r.font.color.rgb = BLACK

    doc.add_paragraph()
    para(
        f"This report was auto-generated on {today} using the RBI CSF Compliance Assessment Tool. "
        "For internal use only.",
        color=GREY, size=8,
    )

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════
#  MODULE 5 UI
# ══════════════════════════════════════════════════════
def show_module5():

    st.markdown("""
    <div class="rbi-page-header">
        <h1>📊 MODULE 5 — GAP ANALYSIS REPORT</h1>
        <p>Review your compliance posture and export the gap analysis report in Word format</p>
    </div>
    """, unsafe_allow_html=True)

    # Log view
    _log("view", "Gap Analysis Report viewed")

    summary    = st.session_state.get("compliance_summary")
    gaps       = st.session_state.get("gap_dataframe")
    bank_name  = st.session_state.get("bank_name",  "Not Specified")
    bank_level = st.session_state.get("bank_level", "Not Set")

    if not summary:
        st.warning("⚠️ Please complete Module 3 (Compliance Dashboard) first to generate the report.")
        return

    today = date.today().strftime("%d %B %Y")
    pct   = summary["percent"]
    risk  = summary["risk"]

    risk_color = {"Low Risk": "#15803d", "Moderate Risk": "#b45309", "High Risk": "#b91c1c"}[risk]
    risk_badge = {"Low Risk": "badge-green", "Moderate Risk": "badge-amber", "High Risk": "badge-red"}[risk]

    if pct >= 80:
        verdict = "The bank demonstrates a <strong style='color:#15803d;'>strong compliance posture</strong> with the RBI Cybersecurity Framework."
    elif pct >= 60:
        verdict = "The bank shows <strong style='color:#b45309;'>moderate compliance</strong> but has significant gaps requiring attention."
    else:
        verdict = "The bank has <strong style='color:#b91c1c;'>critical compliance deficiencies</strong> that require immediate remediation."

    # ── Report header ──────────────────────────────────────────
    st.markdown(f"""
    <div class="rbi-card rbi-card-gold" style="padding:24px 28px; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px;">
            <div>
                <div style="font-family:'Rajdhani',sans-serif; font-size:24px; font-weight:700;
                            color:var(--text-primary);">🏦 {bank_name}</div>
                <div style="font-size:11px; color:var(--text-dim); margin-top:4px; letter-spacing:0.8px;
                            text-transform:uppercase;">
                    RBI Cybersecurity · Gap Analysis Report
                </div>
            </div>
            <div style="text-align:right;">
                <div class="rbi-label">Report Date</div>
                <div style="font-family:'IBM Plex Mono',monospace; font-size:14px; color:var(--gold);">{today}</div>
                <div style="margin-top:6px;"><span class="rbi-badge badge-gold">{bank_level}</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Strip ──────────────────────────────────────────────
    st.markdown('<div class="rbi-section-title">Compliance Summary</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="rbi-stat-strip">
        <div class="rbi-stat-item">
            <div class="stat-label">Total Controls</div>
            <div class="stat-value">{summary['total']}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Compliant</div>
            <div class="stat-value" style="color:var(--compliant);">{summary['compliant']}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Partial</div>
            <div class="stat-value" style="color:var(--partial);">{summary['partial']}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">Non-Compliant</div>
            <div class="stat-value" style="color:var(--noncompliant);">{summary['non']}</div>
        </div>
        <div class="rbi-stat-item">
            <div class="stat-label">N/A</div>
            <div class="stat-value" style="color:var(--na);">{summary['na']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Score Banner ───────────────────────────────────────────
    st.markdown(f"""
    <div class="rbi-card" style="display:flex; align-items:center; gap:24px; flex-wrap:wrap; margin-bottom:8px;">
        <div>
            <div class="rbi-label">Compliance Score</div>
            <div style="font-family:'Rajdhani',sans-serif; font-size:52px; font-weight:700;
                        color:{risk_color}; line-height:1;">{pct}%</div>
        </div>
        <div style="width:1px; height:64px; background:var(--border);"></div>
        <div>
            <div class="rbi-label">Risk Category</div>
            <span class="rbi-badge {risk_badge}" style="font-size:12px; padding:5px 14px; margin-top:4px; display:inline-block;">
                {risk.upper()}
            </span>
        </div>
        <div style="width:1px; height:64px; background:var(--border);"></div>
        <div style="flex:1; min-width:220px;">
            <div class="rbi-label">Assessment Verdict</div>
            <div style="font-size:13px; color:var(--text-secondary); margin-top:6px; line-height:1.65;">{verdict}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(pct / 100)

    # ── Gaps Preview ───────────────────────────────────────────
    if gaps is not None and not gaps.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="rbi-section-title">Key Compliance Gaps</div>', unsafe_allow_html=True)
        high = (gaps.get("Priority", "") == "🔴 High").sum()  if "Priority" in gaps.columns else "—"
        med  = (gaps.get("Priority", "") == "🟡 Medium").sum() if "Priority" in gaps.columns else "—"
        st.markdown(f"""
        <div class="rbi-stat-strip" style="margin-bottom:14px;">
            <div class="rbi-stat-item">
                <div class="stat-label">Total Gaps</div>
                <div class="stat-value" style="color:var(--noncompliant);">{len(gaps)}</div>
            </div>
            <div class="rbi-stat-item">
                <div class="stat-label">High Priority</div>
                <div class="stat-value" style="color:var(--noncompliant);">{high}</div>
            </div>
            <div class="rbi-stat-item">
                <div class="stat-label">Medium Priority</div>
                <div class="stat-value" style="color:var(--partial);">{med}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        sec_col = next((c for c in gaps.columns if "section"     in c.lower()), None)
        req_col = next((c for c in gaps.columns if "requirement" in c.lower()), None)
        sc      = "_status"  if "_status"  in gaps.columns else None
        pc      = "Priority" if "Priority" in gaps.columns else None
        show_c  = [c for c in [sec_col, req_col, sc, pc] if c and c in gaps.columns]
        if show_c:
            st.dataframe(
                gaps[show_c].rename(columns={"_status": "Status"}).head(20),
                use_container_width=True,
                height=250,
            )

    # ── Recommendations ────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="rbi-section-title">Recommendations</div>', unsafe_allow_html=True)
    recs = []
    if summary["non"]     > 0: recs.append(f"Immediately remediate the **{summary['non']} non-compliant controls** identified in the Gap Analysis.")
    if summary["partial"] > 0: recs.append(f"Develop a 90-day action plan for the **{summary['partial']} partially compliant controls**.")
    if pct < 80:
        recs.append("Conduct a cybersecurity awareness and training program for all relevant staff.")
        recs.append("Assign a dedicated Cybersecurity Officer to oversee remediation tracking.")
    recs.append("Perform quarterly internal compliance re-assessments and maintain updated evidence artefacts.")
    recs.append("Submit compliance status reports to RBI as per prescribed timelines and guidelines.")

    st.markdown('<div class="rbi-card">', unsafe_allow_html=True)
    for i, rec in enumerate(recs, 1):
        st.markdown(f"{i}. {rec}")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Export ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="rbi-section-title">Export Report</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="rbi-card rbi-card-gold" style="padding:18px 22px; margin-bottom:12px; display:flex; align-items:center; gap:18px;">
        <div style="font-size:32px;">📘</div>
        <div>
            <div style="font-family:'Rajdhani',sans-serif; font-size:16px; font-weight:600; color:var(--text-primary);">
                Word Report
            </div>
            <div style="font-size:12px; color:var(--text-secondary); margin-top:3px;">
                Light theme &nbsp;·&nbsp; Fully editable .docx &nbsp;·&nbsp; Coloured tables &amp; compliance summary
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    safe_name = bank_name.replace(" ", "_")

    try:
        docx_buf = generate_docx(bank_name, bank_level, today, summary, gaps)
        if st.download_button(
            "⬇️  Download Word Report",
            docx_buf,
            file_name=f"Gap_Analysis_Report_{safe_name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        ):
            _log("export", "Word Report downloaded",
                 detail=f"{bank_name} · {bank_level} · Score: {pct}%")
    except Exception as e:
        st.error(f"Word generation error: {e}")