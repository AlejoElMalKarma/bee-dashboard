import os
import json
import io
import anthropic
import streamlit as st
import markdown as md_lib
from dotenv import load_dotenv

from agents import data_certifier, dataviz_selector, dashboard_architect, d3_auditor, docs_generator

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Pipeline",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS — light professional theme ─────────────────────────────────────
st.markdown("""
<style>
  /* Base */
  [data-testid="stAppViewContainer"] { background: #ffffff; color: #111827; }
  [data-testid="stHeader"] { background: #ffffff; border-bottom: 1px solid #e5e7eb; }
  .main .block-container { padding: 2rem 3rem; max-width: 1400px; }

  /* Typography */
  h1 { color: #111827; font-size: 1.75rem !important; font-weight: 700 !important; letter-spacing: -0.5px; }
  h2 { color: #1f2937; font-size: 1.2rem !important; font-weight: 600 !important; }
  h3 { color: #374151; font-size: 1rem !important; font-weight: 600 !important; }
  p, li { color: #374151; }
  label, .stMarkdown { color: #374151 !important; }

  /* Pipeline progress bar */
  .pipeline-bar {
    display: flex; align-items: center; gap: 0;
    background: #f9fafb; border-radius: 12px;
    padding: 1rem 1.5rem; margin-bottom: 2rem;
    border: 1px solid #e5e7eb;
  }
  .pipe-step {
    display: flex; flex-direction: column; align-items: center;
    flex: 1; position: relative; cursor: default;
  }
  .pipe-step:not(:last-child)::after {
    content: ''; position: absolute; top: 18px; left: 60%;
    width: 80%; height: 2px; background: #d1d5db; z-index: 0;
  }
  .pipe-step.done:not(:last-child)::after { background: #2563eb; }
  .pipe-icon {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; position: relative; z-index: 1;
    border: 2px solid #d1d5db; background: #f9fafb;
  }
  .pipe-step.done .pipe-icon { background: #2563eb; border-color: #2563eb; }
  .pipe-step.active .pipe-icon { background: #1d4ed8; border-color: #3b82f6; box-shadow: 0 0 10px #3b82f640; }
  .pipe-label { font-size: 0.65rem; color: #9ca3af; margin-top: 4px; text-align: center; }
  .pipe-step.done .pipe-label { color: #2563eb; font-weight: 600; }
  .pipe-step.active .pipe-label { color: #1d4ed8; font-weight: 700; }

  /* Cards */
  .card {
    background: #f9fafb; border: 1px solid #e5e7eb;
    border-radius: 10px; padding: 1.25rem 1.5rem; margin-bottom: 1rem;
  }
  .card-success { border-color: #16a34a; background: #f0fdf4; }
  .card-warn    { border-color: #d97706; background: #fffbeb; }
  .card-error   { border-color: #dc2626; background: #fef2f2; }
  .card-info    { border-color: #2563eb; background: #eff6ff; }

  /* Verdict badge */
  .badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px;
  }
  .badge-green  { background: #dcfce7; color: #15803d; border: 1px solid #16a34a; }
  .badge-yellow { background: #fef3c7; color: #92400e; border: 1px solid #d97706; }
  .badge-red    { background: #fee2e2; color: #991b1b; border: 1px solid #dc2626; }
  .badge-blue   { background: #dbeafe; color: #1e40af; border: 1px solid #2563eb; }

  /* Metric tiles */
  .metric-grid { display: flex; gap: 0.75rem; flex-wrap: wrap; margin: 0.75rem 0; }
  .metric-tile {
    background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;
    padding: 0.75rem 1rem; min-width: 130px; flex: 1;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
  }
  .metric-val { font-size: 1.6rem; font-weight: 700; color: #111827; line-height: 1; }
  .metric-lbl { font-size: 0.7rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }

  /* Issue rows */
  .issue-row { display: flex; gap: 0.5rem; align-items: flex-start; padding: 0.5rem 0; border-bottom: 1px solid #f3f4f6; }
  .sev-pill { padding: 2px 7px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; white-space: nowrap; }
  .sev-CRITICAL    { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
  .sev-WARNING     { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
  .sev-INFO        { background: #dbeafe; color: #1e40af; border: 1px solid #93c5fd; }
  .sev-ADVERTENCIA { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
  .sev-CRÍTICO     { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

  /* Viz card */
  .viz-card {
    background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;
    padding: 1rem; margin-bottom: 0.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
  }
  .viz-title { font-size: 0.85rem; font-weight: 600; color: #111827; }
  .viz-meta  { font-size: 0.72rem; color: #6b7280; margin-top: 2px; }

  /* Score display */
  .score-display { display: flex; align-items: center; gap: 1.5rem; padding: 1rem 0; }
  .score-number  { font-size: 3.5rem; font-weight: 800; line-height: 1; }
  .score-green   { color: #16a34a; }
  .score-yellow  { color: #d97706; }
  .score-red     { color: #dc2626; }

  /* Buttons */
  [data-testid="stButton"] > button {
    background: #2563eb; color: #fff; border: none; border-radius: 6px;
    font-weight: 600; padding: 0.5rem 1.25rem;
  }
  [data-testid="stButton"] > button:hover { background: #1d4ed8; }
  button[kind="secondary"] { background: #f3f4f6 !important; color: #374151 !important; border: 1px solid #d1d5db !important; }

  /* Download buttons */
  [data-testid="stDownloadButton"] > button {
    background: #16a34a; color: #fff; border: none; border-radius: 6px; font-weight: 600;
  }
  [data-testid="stDownloadButton"] > button:hover { background: #15803d; }

  /* Retry button (red) */
  .retry-btn > button { background: #dc2626 !important; color: #fff !important; }
  .retry-btn > button:hover { background: #b91c1c !important; }

  /* File uploader */
  [data-testid="stFileUploader"] { background: #f9fafb; border-radius: 8px; }

  /* Expander */
  [data-testid="stExpander"] { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; }
  [data-testid="stExpanderDetails"] { background: #ffffff; }

  /* Code preview */
  .html-preview {
    background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 6px;
    padding: 0.75rem; font-family: monospace; font-size: 0.72rem;
    color: #374151; max-height: 300px; overflow-y: auto; white-space: pre;
  }

  /* Warning banner */
  .warn-banner {
    background: #fffbeb; border: 1px solid #d97706; border-radius: 8px;
    padding: 0.75rem 1rem; color: #92400e; font-size: 0.85rem; margin: 0.5rem 0;
  }

  /* Divider */
  hr { border-color: #e5e7eb; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ─────────────────────────────────────────────────────────
STEPS = [
    ("📁", "Upload"),
    ("🔍", "Certify"),
    ("📊", "Visualize"),
    ("🏗", "Build"),
    ("🔎", "Audit"),
    ("📄", "Docs"),
]

def init_state():
    defaults = {
        "current_step": 0,
        "uploaded_data": None,
        "cert_result": None,
        "viz_result": None,
        "html_code": None,
        "audit_result": None,
        "docs_result": None,
        "error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Helpers ────────────────────────────────────────────────────────────────────
def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("❌ ANTHROPIC_API_KEY no encontrada. Configura tu archivo .env")
        st.stop()
    return anthropic.Anthropic(api_key=api_key)


def verdict_badge(verdict: str) -> str:
    v = verdict.upper()
    if "RECHAZADO" in v:
        return f'<span class="badge badge-red">✗ {verdict}</span>'
    if "OBSERVACIONES" in v or "REVISAR" in v:
        return f'<span class="badge badge-yellow">⚠ {verdict}</span>'
    return f'<span class="badge badge-green">✓ {verdict}</span>'


def score_color(score: int) -> str:
    if score >= 80:
        return "score-green"
    if score >= 50:
        return "score-yellow"
    return "score-red"


def render_pipeline_bar(current: int):
    parts = []
    for i, (icon, label) in enumerate(STEPS):
        cls = "done" if i < current else ("active" if i == current else "")
        parts.append(f"""
        <div class="pipe-step {cls}">
          <div class="pipe-icon">{icon}</div>
          <div class="pipe-label">{label}</div>
        </div>""")
    st.markdown(f'<div class="pipeline-bar">{"".join(parts)}</div>', unsafe_allow_html=True)


def reset():
    for k in ["uploaded_data", "cert_result", "viz_result", "html_code", "audit_result", "docs_result", "error"]:
        st.session_state[k] = None
    st.session_state["current_step"] = 0
    st.rerun()


def retry_build():
    """Vuelve al Step 3 limpiando HTML y resultado de auditoría."""
    st.session_state["html_code"] = None
    st.session_state["audit_result"] = None
    st.session_state["docs_result"] = None
    st.session_state["current_step"] = 3
    st.session_state["error"] = None
    st.rerun()


def markdown_to_pdf(md_content: str) -> bytes:
    """Convierte Markdown a PDF usando fpdf2 (puro Python, sin dependencias de sistema)."""
    import re
    from fpdf import FPDF

    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, "DASHBOARD DOCUMENTATION", align="R")
            self.ln(4)
            self.set_draw_color(200, 200, 200)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(4)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 8, f"Página {self.page_no()}", align="C")

    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    for line in md_content.split("\n"):
        stripped = line.rstrip()

        if stripped.startswith("### "):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(55, 65, 81)
            pdf.ln(3)
            pdf.multi_cell(0, 6, stripped[4:])
            pdf.ln(1)

        elif stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(29, 78, 216)
            pdf.ln(4)
            pdf.multi_cell(0, 7, stripped[3:])
            pdf.set_draw_color(147, 197, 253)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)

        elif stripped.startswith("# "):
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(17, 24, 39)
            pdf.ln(4)
            pdf.multi_cell(0, 9, stripped[2:])
            pdf.set_draw_color(29, 78, 216)
            pdf.set_line_width(0.5)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.set_line_width(0.2)
            pdf.ln(4)

        elif stripped.startswith("> "):
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(107, 114, 128)
            pdf.multi_cell(0, 5, stripped[2:])

        elif stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(31, 41, 55)
            clean = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped[2:])
            clean = re.sub(r"`(.+?)`", r"\1", clean)
            pdf.multi_cell(0, 5, f"  • {clean}")

        elif stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            col_w = max(1, (pdf.w - pdf.l_margin - pdf.r_margin) / max(len(cells), 1))
            is_header = pdf.get_x() == pdf.l_margin and pdf.get_font()[1] == "B"
            if pdf.get_y() > pdf.h - 30:
                pdf.add_page()
            for i, cell in enumerate(cells):
                if i == 0:
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.set_fill_color(219, 234, 254)
                    pdf.set_text_color(30, 58, 138)
                else:
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_fill_color(249, 250, 251)
                    pdf.set_text_color(31, 41, 55)
                pdf.cell(col_w, 5, cell[:40], border=1, fill=True)
            pdf.ln()

        elif stripped.startswith("```") or stripped == "---":
            pass

        elif stripped == "":
            pdf.ln(2)

        else:
            clean = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
            clean = re.sub(r"`(.+?)`", r"\1", clean)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(31, 41, 55)
            pdf.multi_cell(0, 5, clean)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ── Header ─────────────────────────────────────────────────────────────────────
col_title, col_reset = st.columns([5, 1])
with col_title:
    st.markdown("## 📊 Dashboard Pipeline")
    st.caption("Orquestador de agentes IA para generar dashboards D3.js certificados")
with col_reset:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↺ Reiniciar", use_container_width=True):
        reset()

render_pipeline_bar(st.session_state["current_step"])

if st.session_state["error"]:
    st.markdown(f'<div class="card card-error">⚠️ {st.session_state["error"]}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 0 — UPLOAD JSON
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### Step 0 — Cargar Dataset")

uploaded_file = st.file_uploader(
    "Sube un archivo JSON con la estructura `{metadata: {...}, records: [...]}`",
    type=["json"],
    key="file_uploader",
)

if uploaded_file and st.session_state["uploaded_data"] is None:
    try:
        raw = json.loads(uploaded_file.read().decode("utf-8"))
        # Normaliza: si el JSON raíz es una lista, lo envuelve en la estructura esperada
        if isinstance(raw, list):
            raw = {"metadata": {"dataset": uploaded_file.name.replace(".json", ""), "kpis": []}, "records": raw}
        elif not isinstance(raw, dict):
            raise ValueError(f"Formato no soportado: se esperaba un objeto o array JSON, se recibió {type(raw).__name__}")
        if "records" not in raw:
            # intenta detectar la primera clave que sea una lista
            list_keys = [k for k, v in raw.items() if isinstance(v, list)]
            if list_keys:
                raw = {"metadata": raw.get("metadata", {"kpis": []}), "records": raw[list_keys[0]]}
            else:
                raise ValueError("El JSON no contiene una clave 'records' ni ningún array de datos.")
        st.session_state["uploaded_data"] = raw
        st.session_state["current_step"] = max(st.session_state["current_step"], 1)
        st.session_state["error"] = None
    except Exception as e:
        st.session_state["error"] = f"Error parseando JSON: {e}"
        st.rerun()

if st.session_state["uploaded_data"]:
    data = st.session_state["uploaded_data"]
    records = data.get("records", [])
    fields = list(records[0].keys()) if records else []
    size_kb = len(json.dumps(data).encode()) / 1024

    st.markdown(f"""
    <div class="card card-info">
      <div class="metric-grid">
        <div class="metric-tile"><div class="metric-val">{len(records)}</div><div class="metric-lbl">Registros</div></div>
        <div class="metric-tile"><div class="metric-val">{len(fields)}</div><div class="metric-lbl">Campos</div></div>
        <div class="metric-tile"><div class="metric-val">{size_kb:.1f} KB</div><div class="metric-lbl">Tamaño</div></div>
        <div class="metric-tile"><div class="metric-val">{len(data.get('metadata', {}).get('kpis', []))}</div><div class="metric-lbl">KPIs definidos</div></div>
      </div>
      <p style="margin:0.5rem 0 0;font-size:0.8rem">
        <strong style="color:#93c5fd">Campos:</strong> {', '.join(fields[:12])}{'...' if len(fields) > 12 else ''}
      </p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — DATA CERTIFIER
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["uploaded_data"]:
    st.divider()
    st.markdown("### Step 1 — Certificación de Datos")

    if st.session_state["cert_result"] is None:
        if st.button("▶ Ejecutar data-certifier", key="run_cert"):
            with st.spinner("🔍 Auditando dataset con data-certifier (claude-sonnet-4-5)…"):
                try:
                    client = get_client()
                    result = data_certifier.run(st.session_state["uploaded_data"], client)
                    st.session_state["cert_result"] = result
                    st.session_state["current_step"] = max(st.session_state["current_step"], 2)
                    st.session_state["error"] = None
                    st.rerun()
                except Exception as e:
                    st.session_state["error"] = f"data-certifier falló: {e}"
                    st.rerun()

    if st.session_state["cert_result"]:
        r = st.session_state["cert_result"]
        issues = r.get("issues", [])
        n_critical = sum(1 for i in issues if i.get("severity") == "CRITICAL")
        n_warning  = sum(1 for i in issues if i.get("severity") == "WARNING")
        n_info     = sum(1 for i in issues if i.get("severity") == "INFO")

        card_cls = "card-success" if "RECHAZADO" not in r.get("verdict","") and n_critical == 0 else (
            "card-error" if "RECHAZADO" in r.get("verdict","") else "card-warn"
        )

        st.markdown(f"""
        <div class="card {card_cls}">
          <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.75rem">
            <span style="font-weight:700;color:#e2e8f0">Veredicto</span>
            {verdict_badge(r.get('verdict',''))}
          </div>
          <div class="metric-grid">
            <div class="metric-tile"><div class="metric-val">{r.get('completeness_pct', 'N/A')}%</div><div class="metric-lbl">Completitud</div></div>
            <div class="metric-tile"><div class="metric-val">{r.get('certified_count','N/A')}/{r.get('record_count','N/A')}</div><div class="metric-lbl">Certificados</div></div>
            <div class="metric-tile"><div class="metric-val" style="color:#f87171">{n_critical}</div><div class="metric-lbl">Critical</div></div>
            <div class="metric-tile"><div class="metric-val" style="color:#fbbf24">{n_warning}</div><div class="metric-lbl">Warning</div></div>
            <div class="metric-tile"><div class="metric-val" style="color:#93c5fd">{n_info}</div><div class="metric-lbl">Info</div></div>
          </div>
          <p style="margin:0.75rem 0 0;font-size:0.82rem;color:#94a3b8">{r.get('summary','')}</p>
        </div>
        """, unsafe_allow_html=True)

        if issues:
            with st.expander(f"📋 Ver {len(issues)} hallazgos"):
                for iss in issues:
                    sev = iss.get("severity", "INFO")
                    st.markdown(f"""
                    <div class="issue-row">
                      <span class="sev-pill sev-{sev}">{sev}</span>
                      <div>
                        <span style="font-size:0.78rem;color:#cbd5e1;font-weight:600">{iss.get('id','')} · {iss.get('field','')}</span>
                        <div style="font-size:0.75rem;color:#94a3b8;margin-top:2px">{iss.get('description','')}</div>
                        <div style="font-size:0.72rem;color:#64748b;margin-top:2px">→ {iss.get('action','')}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — DATAVIZ SELECTOR
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["cert_result"]:
    st.divider()
    st.markdown("### Step 2 — Selección de Visualizaciones")

    if st.session_state["viz_result"] is None:
        if st.button("▶ Ejecutar dataviz-selector", key="run_viz"):
            with st.spinner("📊 Analizando datos y seleccionando gráficos (claude-sonnet-4-5)…"):
                try:
                    client = get_client()
                    result = dataviz_selector.run(
                        st.session_state["uploaded_data"],
                        st.session_state["cert_result"],
                        client,
                    )
                    st.session_state["viz_result"] = result
                    st.session_state["current_step"] = max(st.session_state["current_step"], 3)
                    st.session_state["error"] = None
                    st.rerun()
                except Exception as e:
                    st.session_state["error"] = f"dataviz-selector falló: {e}"
                    st.rerun()

    if st.session_state["viz_result"]:
        vr = st.session_state["viz_result"]
        vizs = vr.get("visualizations", [])

        st.markdown(f"""
        <div class="card card-info">
          <div class="metric-grid">
            <div class="metric-tile"><div class="metric-val">{len(vizs)}</div><div class="metric-lbl">Visualizaciones</div></div>
            <div class="metric-tile"><div class="metric-val">{len(set(v['objective'] for v in vizs))}</div><div class="metric-lbl">Objetivos distintos</div></div>
          </div>
          <p style="margin:0.75rem 0 0;font-size:0.82rem;color:#94a3b8">{vr.get('summary','')}</p>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(2)
        for idx, viz in enumerate(vizs):
            with cols[idx % 2]:
                lvl = viz.get("cleveland_mcgill_level", "?")
                st.markdown(f"""
                <div class="viz-card">
                  <div style="display:flex;align-items:center;gap:0.5rem">
                    <span class="badge badge-blue">{viz.get('id','')}</span>
                    <span class="viz-title">{viz.get('name','')}</span>
                  </div>
                  <div class="viz-meta">
                    📈 {viz.get('chart_type','')} &nbsp;·&nbsp;
                    🧠 {viz.get('objective','')} &nbsp;·&nbsp;
                    👁 Cleveland & McGill nivel {lvl}
                  </div>
                  <div style="font-size:0.75rem;color:#64748b;margin-top:4px">
                    {viz.get('business_question','')}
                  </div>
                </div>
                """, unsafe_allow_html=True)

        if vr.get("layout"):
            with st.expander("🗺 Layout sugerido"):
                st.markdown(f"<p style='font-size:0.82rem;color:#94a3b8'>{vr['layout']}</p>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — DASHBOARD ARCHITECT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["viz_result"]:
    st.divider()
    st.markdown("### Step 3 — Generación del Dashboard")
    st.caption("⚡ Usa claude-opus-4-5 — puede tardar 30–60 segundos")

    if st.session_state["html_code"] is None:
        if st.button("▶ Ejecutar dashboard-architect", key="run_arch"):
            with st.spinner("🏗 Generando HTML completo con D3.js (claude-opus-4-5)…"):
                try:
                    client = get_client()
                    html = dashboard_architect.run(
                        st.session_state["uploaded_data"],
                        st.session_state["viz_result"],
                        st.session_state["cert_result"],
                        client,
                    )
                    st.session_state["html_code"] = html
                    st.session_state["current_step"] = max(st.session_state["current_step"], 4)
                    st.session_state["error"] = None
                    st.rerun()
                except Exception as e:
                    st.session_state["error"] = f"dashboard-architect falló: {e}"
                    st.rerun()

    if st.session_state["html_code"]:
        html = st.session_state["html_code"]
        n_charts = html.count("window.Charts.")
        n_svg    = html.count("<svg")
        n_lines  = html.count("\n")
        size_kb  = len(html.encode()) / 1024

        st.markdown(f"""
        <div class="card card-success">
          <div class="metric-grid">
            <div class="metric-tile"><div class="metric-val">{n_lines:,}</div><div class="metric-lbl">Líneas HTML</div></div>
            <div class="metric-tile"><div class="metric-val">{size_kb:.1f} KB</div><div class="metric-lbl">Tamaño</div></div>
            <div class="metric-tile"><div class="metric-val">{n_charts}</div><div class="metric-lbl">Módulos Charts</div></div>
            <div class="metric-tile"><div class="metric-val">{n_svg}</div><div class="metric-lbl">Elementos SVG</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Preview del código HTML"):
            preview = html[:3000] + ("\n\n[... truncado ...]" if len(html) > 3000 else "")
            st.markdown(f'<div class="html-preview">{preview}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — D3 AUDITOR
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["html_code"]:
    st.divider()
    st.markdown("### Step 4 — Auditoría de Calidad")

    if st.session_state["audit_result"] is None:
        if st.button("▶ Ejecutar d3-dashboard-auditor", key="run_audit"):
            with st.spinner("🔎 Auditando dashboard (claude-sonnet-4-5)…"):
                try:
                    client = get_client()
                    result = d3_auditor.run(
                        st.session_state["html_code"],
                        st.session_state["viz_result"],
                        client,
                    )
                    st.session_state["audit_result"] = result
                    st.session_state["current_step"] = max(st.session_state["current_step"], 5)
                    st.session_state["error"] = None
                    st.rerun()
                except Exception as e:
                    st.session_state["error"] = f"d3-auditor falló: {e}"
                    st.rerun()

    if st.session_state["audit_result"]:
        ar = st.session_state["audit_result"]
        score   = ar.get("score", 0)
        verdict = ar.get("verdict", "")
        flags   = ar.get("flags", [])
        n_crit  = sum(1 for f in flags if f.get("type") in ("CRÍTICO", "CRITICAL"))
        n_warn  = sum(1 for f in flags if f.get("type") in ("ADVERTENCIA", "WARNING"))
        n_info  = sum(1 for f in flags if f.get("type") == "INFO")

        if verdict == "RECHAZADO":
            st.markdown("""
            <div class="warn-banner">
              ⚠️ El auditor emitió veredicto <strong>RECHAZADO</strong> — el dashboard tiene issues críticos.
              Regenera el código o continúa a documentación de todas formas.
            </div>
            """, unsafe_allow_html=True)
            col_retry, col_continue = st.columns([1, 3])
            with col_retry:
                st.markdown('<div class="retry-btn">', unsafe_allow_html=True)
                if st.button("🔄 Regenerar Dashboard", key="retry_build", use_container_width=True):
                    retry_build()
                st.markdown('</div>', unsafe_allow_html=True)

        score_cls = score_color(score)
        card_cls = "card-success" if verdict == "APROBADO" else ("card-error" if verdict == "RECHAZADO" else "card-warn")

        st.markdown(f"""
        <div class="card {card_cls}">
          <div class="score-display">
            <div>
              <div class="score-number {score_cls}">{score}</div>
              <div style="font-size:0.7rem;color:#64748b;margin-top:2px">/ 100 pts</div>
            </div>
            <div>
              {verdict_badge(verdict)}
              <p style="margin:0.5rem 0 0;font-size:0.82rem;color:#94a3b8">{ar.get('summary','')}</p>
            </div>
          </div>
          <div class="metric-grid" style="margin-top:0.5rem">
            <div class="metric-tile"><div class="metric-val" style="color:#f87171">{n_crit}</div><div class="metric-lbl">Críticos</div></div>
            <div class="metric-tile"><div class="metric-val" style="color:#fbbf24">{n_warn}</div><div class="metric-lbl">Advertencias</div></div>
            <div class="metric-tile"><div class="metric-val" style="color:#93c5fd">{n_info}</div><div class="metric-lbl">Info</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if flags:
            with st.expander(f"📋 Ver {len(flags)} flags de auditoría"):
                for flag in flags:
                    t = flag.get("type", "INFO")
                    st.markdown(f"""
                    <div class="issue-row">
                      <span class="sev-pill sev-{t}">{t}</span>
                      <div>
                        <span style="font-size:0.78rem;color:#cbd5e1;font-weight:600">{flag.get('area','')}</span>
                        <div style="font-size:0.75rem;color:#94a3b8;margin-top:2px">{flag.get('issue','')}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — DOCS GENERATOR + DOWNLOADS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["audit_result"]:
    st.divider()
    st.markdown("### Step 5 — Documentación Técnica")

    if st.session_state["docs_result"] is None:
        if st.button("▶ Ejecutar dashboard-docs-generator", key="run_docs"):
            with st.spinner("📄 Generando documentación completa (claude-sonnet-4-5)…"):
                try:
                    client = get_client()
                    result = docs_generator.run(
                        html_code=st.session_state["html_code"],
                        audit_result=st.session_state["audit_result"],
                        cert_result=st.session_state["cert_result"],
                        viz_result=st.session_state["viz_result"],
                        data=st.session_state["uploaded_data"],
                        client=client,
                    )
                    st.session_state["docs_result"] = result
                    st.session_state["current_step"] = 6
                    st.session_state["error"] = None
                    st.rerun()
                except Exception as e:
                    st.session_state["error"] = f"docs-generator falló: {e}"
                    st.rerun()

    if st.session_state["docs_result"]:
        dr = st.session_state["docs_result"]
        summary = dr.get("summary", {})
        md_content = dr.get("markdown_content", "")
        md_bytes = md_content.encode("utf-8")
        html_bytes = (st.session_state["html_code"] or "").encode("utf-8")

        st.markdown(f"""
        <div class="card card-success">
          <div class="metric-grid">
            <div class="metric-tile"><div class="metric-val">{summary.get('kpis_documented',0)}</div><div class="metric-lbl">KPIs documentados</div></div>
            <div class="metric-tile"><div class="metric-val">{summary.get('charts_documented',0)}</div><div class="metric-lbl">Gráficos documentados</div></div>
            <div class="metric-tile"><div class="metric-val">{summary.get('issues_documented',0)}</div><div class="metric-lbl">Issues documentados</div></div>
            <div class="metric-tile"><div class="metric-val">{len(md_bytes)//1024} KB</div><div class="metric-lbl">Tamaño doc</div></div>
          </div>
          <div style="margin-top:0.75rem">
            {verdict_badge(summary.get('verdict',''))}
            <span style="margin-left:0.5rem;font-size:0.8rem;color:#94a3b8">Score: {summary.get('score',0)}/100</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📥 Descargas")
        with st.spinner("Generando PDF…"):
            pdf_bytes = markdown_to_pdf(md_content)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="⬇ dashboard.html",
                data=html_bytes,
                file_name="dashboard.html",
                mime="text/html",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                label="⬇ DASHBOARD_DOCS.md",
                data=md_bytes,
                file_name="DASHBOARD_DOCS.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col3:
            st.download_button(
                label="⬇ DASHBOARD_DOCS.pdf",
                data=pdf_bytes,
                file_name="DASHBOARD_DOCS.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        with st.expander("📖 Preview de la documentación"):
            st.markdown(md_content[:4000] + ("\n\n*[... truncado para preview ...]*" if len(md_content) > 4000 else ""))

        # Pipeline complete banner
        render_pipeline_bar(6)
        st.markdown("""
        <div class="card card-success" style="text-align:center;padding:1.5rem">
          <div style="font-size:2rem">🎉</div>
          <div style="font-size:1.1rem;font-weight:700;color:#4ade80;margin:0.5rem 0">Pipeline completado</div>
          <div style="font-size:0.85rem;color:#94a3b8">
            Dataset certificado → Visualizaciones seleccionadas → Dashboard generado → Auditado → Documentado
          </div>
        </div>
        """, unsafe_allow_html=True)
