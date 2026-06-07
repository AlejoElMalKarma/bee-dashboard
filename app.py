import os
import json
import io
import anthropic
import streamlit as st
import markdown as md_lib
from dotenv import load_dotenv

from agents import data_certifier, dataviz_selector, storytelling_advisor, design_architect, dashboard_architect, d3_auditor, docs_generator, brand_reader
from agents.d3_auditor import fix_html as audit_fix_html

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Pipeline",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS — dark premium theme ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

[data-testid="stAppViewContainer"] { background: #07080F; color: #E8EAF2; }
[data-testid="stHeader"] { background: #07080F; border-bottom: 1px solid #1E2235; }
.main .block-container { padding: 2rem 3rem; max-width: 1200px; }

h1, h2, h3 { font-family: 'Syne', sans-serif !important; color: #E8EAF2 !important; }
h2 { font-size: 1.1rem !important; font-weight: 600 !important; }
h3 { font-size: 0.95rem !important; font-weight: 600 !important; }
p, li { font-family: 'Syne', sans-serif !important; color: #8B90A8 !important; }
label, .stMarkdown { color: #8B90A8 !important; }

.pipeline-bar {
  display: flex; align-items: center;
  background: #0D0F1C; border: 1px solid #1E2235;
  border-radius: 10px; padding: 1rem 1.5rem; margin-bottom: 2rem;
}
.pipe-step {
  display: flex; flex-direction: column; align-items: center;
  flex: 1; position: relative; cursor: default;
}
.pipe-step:not(:last-child)::after {
  content: ''; position: absolute; top: 18px; left: 60%;
  width: 80%; height: 1px; background: #1E2235; z-index: 0;
}
.pipe-step.done:not(:last-child)::after { background: #F5C842; opacity: 0.5; }
.pipe-icon {
  width: 36px; height: 36px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; position: relative; z-index: 1;
  border: 1px solid #1E2235; background: #07080F;
}
.pipe-step.done .pipe-icon  { background: #F5C84220; border-color: #F5C84240; }
.pipe-step.active .pipe-icon { background: #F5C84230; border-color: #F5C842; box-shadow: 0 0 12px #F5C84240; }
.pipe-label {
  font-family: 'IBM Plex Mono', monospace; font-size: 9px;
  color: #525870; margin-top: 6px; letter-spacing: 1px; text-transform: uppercase;
}
.pipe-step.done .pipe-label   { color: #F5C842; opacity: 0.7; }
.pipe-step.active .pipe-label { color: #F5C842; font-weight: 600; }

.card {
  background: #0D0F1C; border: 1px solid #1E2235;
  border-radius: 10px; padding: 1.25rem 1.5rem; margin-bottom: 1rem;
  font-family: 'Syne', sans-serif;
}
.card-success { border-color: #00C9A730; background: #00C9A708; }
.card-warn    { border-color: #F5C84230; background: #F5C84208; }
.card-error   { border-color: #FF456030; background: #FF456008; }
.card-info    { border-color: #7C6BF530; background: #7C6BF508; }

.badge {
  display: inline-block; padding: 2px 10px; border-radius: 4px;
  font-family: 'IBM Plex Mono', monospace; font-size: 10px;
  font-weight: 500; letter-spacing: 1px; text-transform: uppercase;
}
.badge-green  { background: #00C9A718; color: #00C9A7; border: 1px solid #00C9A730; }
.badge-yellow { background: #F5C84218; color: #F5C842; border: 1px solid #F5C84230; }
.badge-red    { background: #FF456018; color: #FF4560; border: 1px solid #FF456030; }
.badge-blue   { background: #7C6BF518; color: #7C6BF5; border: 1px solid #7C6BF530; }

.metric-grid { display: flex; gap: 12px; flex-wrap: wrap; margin: 1rem 0; }
.metric-tile {
  background: #07080F; border: 1px solid #1E2235;
  border-radius: 8px; padding: 12px 16px; min-width: 120px; flex: 1;
}
.metric-val { font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem; font-weight: 500; color: #E8EAF2; line-height: 1; }
.metric-lbl { font-family: 'IBM Plex Mono', monospace; font-size: 9px; color: #525870; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }

.issue-row { display: flex; gap: 8px; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid #1E2235; }
.sev-pill { font-family: 'IBM Plex Mono', monospace; padding: 2px 8px; border-radius: 4px; font-size: 9px; font-weight: 600; letter-spacing: 1px; white-space: nowrap; }
.sev-CRITICAL    { background: #FF456018; color: #FF4560; border: 1px solid #FF456030; }
.sev-WARNING     { background: #F5C84218; color: #F5C842; border: 1px solid #F5C84230; }
.sev-INFO        { background: #7C6BF518; color: #7C6BF5; border: 1px solid #7C6BF530; }
.sev-ADVERTENCIA { background: #F5C84218; color: #F5C842; border: 1px solid #F5C84230; }
.sev-CRÍTICO     { background: #FF456018; color: #FF4560; border: 1px solid #FF456030; }

.fix-row { display: flex; gap: 8px; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid #1E2235; }
.fix-auto  { font-family: 'IBM Plex Mono', monospace; padding: 2px 8px; border-radius: 4px; font-size: 9px; font-weight: 600; background: #00C9A718; color: #00C9A7; border: 1px solid #00C9A730; white-space: nowrap; }
.fix-human { font-family: 'IBM Plex Mono', monospace; padding: 2px 8px; border-radius: 4px; font-size: 9px; font-weight: 600; background: #F5C84218; color: #F5C842; border: 1px solid #F5C84230; white-space: nowrap; }

.viz-card { background: #07080F; border: 1px solid #1E2235; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; }
.viz-card:hover { border-color: #252A40; }
.viz-title { font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 600; color: #E8EAF2; }
.viz-meta  { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #525870; margin-top: 3px; }

.score-display { display: flex; align-items: center; gap: 1.5rem; padding: 1rem 0; }
.score-number  { font-family: 'IBM Plex Mono', monospace; font-size: 3.5rem; font-weight: 500; line-height: 1; }
.score-green   { color: #00C9A7; }
.score-yellow  { color: #F5C842; }
.score-red     { color: #FF4560; }

[data-testid="stButton"] > button {
  background: #F5C842; color: #07080F; border: none; border-radius: 6px;
  font-family: 'Syne', sans-serif; font-weight: 700; font-size: 13px;
  padding: 0.5rem 1.25rem; transition: background 0.15s;
}
[data-testid="stButton"] > button:hover { background: #E8A800; }
[data-testid="stButton"] > button[kind="secondary"] {
  background: #0D0F1C !important; color: #8B90A8 !important; border: 1px solid #1E2235 !important;
}

[data-testid="stDownloadButton"] > button {
  background: #00C9A720; color: #00C9A7; border: 1px solid #00C9A740;
  font-family: 'Syne', sans-serif; font-weight: 600;
}
[data-testid="stDownloadButton"] > button:hover { background: #00C9A730; }

.retry-btn > button { background: #FF456020 !important; color: #FF4560 !important; border: 1px solid #FF456040 !important; }

[data-testid="stFileUploader"] { background: #0D0F1C; border: 1px dashed #1E2235; border-radius: 8px; }
[data-testid="stExpander"]        { background: #0D0F1C; border: 1px solid #1E2235; border-radius: 8px; }
[data-testid="stExpanderDetails"] { background: #07080F; }

.html-preview {
  background: #07080F; border: 1px solid #1E2235; border-radius: 6px;
  padding: 12px; font-family: 'IBM Plex Mono', monospace; font-size: 11px;
  color: #525870; max-height: 280px; overflow-y: auto; white-space: pre;
}
.warn-banner {
  background: #F5C84210; border: 1px solid #F5C84230; border-radius: 8px;
  padding: 10px 14px; color: #F5C842; font-family: 'Syne', sans-serif; font-size: 13px; margin: 8px 0;
}
.section-title {
  font-family: 'IBM Plex Mono', monospace; font-size: 9px; color: #525870;
  text-transform: uppercase; letter-spacing: 2px;
  margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid #1E2235;
}
hr { border-color: #1E2235; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #07080F; }
::-webkit-scrollbar-thumb { background: #1E2235; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #252A40; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ─────────────────────────────────────────────────────────
STEPS = [
    ("📁", "Upload"),
    ("🔍", "Certify"),
    ("📊", "Visualize"),
    ("📖", "Story"),
    ("🎨", "Design"),
    ("🏗", "Build"),
    ("🔎", "Audit"),
    ("📄", "Docs"),
]

def init_state():
    defaults = {
        "current_step": 0,
        "brand_result": None,
        "uploaded_data": None,
        "cert_result": None,
        "viz_result": None,
        "story_result": None,
        "design_result": None,
        "html_code": None,
        "audit_result": None,
        "correction_summary": None,
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
    for k in ["uploaded_data", "cert_result", "viz_result", "story_result", "design_result", "html_code", "audit_result", "correction_summary", "docs_result", "error"]:
        st.session_state[k] = None
    st.session_state["current_step"] = 0
    st.rerun()


def retry_build():
    """Vuelve al Step 5 (Build) limpiando solo HTML y auditoría — conserva story y design."""
    st.session_state["html_code"] = None
    st.session_state["audit_result"] = None
    st.session_state["correction_summary"] = None
    st.session_state["docs_result"] = None
    st.session_state["current_step"] = 5
    st.session_state["error"] = None
    st.rerun()


def get_active_data() -> dict:
    """Return certified_data if available (post auto-fixes), else raw uploaded_data."""
    cert = st.session_state.get("cert_result") or {}
    return cert.get("certified_data") or st.session_state.get("uploaded_data") or {}


def markdown_to_pdf(md_content: str) -> bytes:
    """Convierte Markdown a PDF usando fpdf2 (puro Python, sin dependencias de sistema)."""
    import re
    from fpdf import FPDF

    _UNICODE_MAP = str.maketrans({
        "—": "--",   # em dash
        "–": "-",    # en dash
        "‘": "'",    # left single quote
        "’": "'",    # right single quote
        "“": '"',    # left double quote
        "”": '"',    # right double quote
        "…": "...",  # ellipsis
        "•": "*",    # bullet
        "→": "->",   # right arrow
        "←": "<-",   # left arrow
        "↑": "^",    # up arrow
        "↓": "v",    # down arrow
        "·": ".",    # middle dot
        " ": " ",    # non-breaking space
        "✓": "OK",   # check mark
        "✗": "X",    # cross mark
        "⚠": "!",    # warning sign
        "°": "deg",  # degree sign
        "×": "x",    # multiplication sign
        "÷": "/",    # division sign
        "±": "+/-",  # plus-minus
    })

    def _clean(text: str) -> str:
        text = text.translate(_UNICODE_MAP)
        return text.encode("latin-1", errors="replace").decode("latin-1")

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

    pw = pdf.w - pdf.l_margin - pdf.r_margin  # explicit page content width

    def mc(h, txt):
        """multi_cell with guaranteed left-margin reset — never fails on width."""
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pw, h, _clean(txt))

    for line in md_content.split("\n"):
        stripped = line.rstrip()

        if stripped.startswith("### "):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(55, 65, 81)
            pdf.ln(3)
            mc(6, stripped[4:])
            pdf.ln(1)

        elif stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(29, 78, 216)
            pdf.ln(4)
            mc(7, stripped[3:])
            pdf.set_draw_color(147, 197, 253)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)

        elif stripped.startswith("# "):
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(17, 24, 39)
            pdf.ln(4)
            mc(9, stripped[2:])
            pdf.set_draw_color(29, 78, 216)
            pdf.set_line_width(0.5)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.set_line_width(0.2)
            pdf.ln(4)

        elif stripped.startswith("> "):
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(107, 114, 128)
            mc(5, stripped[2:])

        elif stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(31, 41, 55)
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped[2:])
            text = re.sub(r"`(.+?)`", r"\1", text)
            mc(5, f"  * {text}")

        elif stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not cells or all(set(c) <= set("-: ") for c in cells):
                continue
            col_w = pw / max(len(cells), 1)
            if col_w < 12:
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(31, 41, 55)
                mc(5, " | ".join(cells))
                continue
            if pdf.get_y() > pdf.h - 30:
                pdf.add_page()
            pdf.set_x(pdf.l_margin)
            for i, cell in enumerate(cells):
                if i == 0:
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.set_fill_color(219, 234, 254)
                    pdf.set_text_color(30, 58, 138)
                else:
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_fill_color(249, 250, 251)
                    pdf.set_text_color(31, 41, 55)
                char_limit = max(5, int(col_w / 2.2))
                pdf.cell(col_w, 5, _clean(cell[:char_limit]), border=1, fill=True)
            pdf.ln()
            pdf.set_x(pdf.l_margin)

        elif stripped.startswith("```") or stripped == "---":
            pass

        elif stripped == "":
            pdf.ln(2)

        else:
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
            text = re.sub(r"`(.+?)`", r"\1", text)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(31, 41, 55)
            mc(5, text)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ── Brand: silently load BRAND.md once per session ────────────────────────────
if st.session_state["brand_result"] is None:
    st.session_state["brand_result"] = brand_reader.run()

_br = st.session_state["brand_result"]
st.markdown(f"<style>{_br['css_variables']}</style>", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
brand = st.session_state.get("brand_result", {})
empresa = brand.get("empresa", "Dashboard Pipeline")
logo_b64 = brand.get("logo_base64", None)
tagline = brand.get("tagline", "Orquestador de agentes IA")

col_logo, col_title, col_reset = st.columns([1, 6, 1])
with col_logo:
    if logo_b64:
        st.markdown(
            f'<img src="{logo_b64}" style="height:40px;margin-top:8px;object-fit:contain;">',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div style="font-size:1.5rem;margin-top:4px">🐝</div>', unsafe_allow_html=True)
with col_title:
    st.markdown(
        f'<p style="font-family:\'IBM Plex Mono\',monospace;font-size:9px;color:#525870;'
        f'letter-spacing:2px;text-transform:uppercase;margin-bottom:4px">'
        f'BEESUALIZATION · ANALYTICS</p>'
        f'<p style="font-family:\'Syne\',sans-serif;font-size:1.2rem;font-weight:700;'
        f'color:#E8EAF2;margin:0">{empresa} · Dashboard Pipeline</p>',
        unsafe_allow_html=True,
    )
with col_reset:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↺", help="Reiniciar pipeline"):
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
        auto_fixes = r.get("auto_fixes_applied", [])
        requires_human = r.get("requires_human", [])
        n_critical = sum(1 for i in issues if i.get("severity") == "CRITICAL")
        n_warning  = sum(1 for i in issues if i.get("severity") == "WARNING")
        n_info     = sum(1 for i in issues if i.get("severity") == "INFO")

        card_cls = "card-success" if "RECHAZADO" not in r.get("verdict","") and n_critical == 0 else (
            "card-error" if "RECHAZADO" in r.get("verdict","") else "card-warn"
        )

        st.markdown(f"""
        <div class="card {card_cls}">
          <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.75rem;flex-wrap:wrap">
            <span style="font-weight:700;color:#E8EAF2">Veredicto</span>
            {verdict_badge(r.get('verdict',''))}
            {"<span class='badge badge-green'>✓ " + str(len(auto_fixes)) + " auto-fixes aplicados</span>" if auto_fixes else ""}
          </div>
          <div class="metric-grid">
            <div class="metric-tile"><div class="metric-val">{r.get('completeness_pct', 'N/A')}%</div><div class="metric-lbl">Completitud</div></div>
            <div class="metric-tile"><div class="metric-val">{r.get('certified_count','N/A')}/{r.get('record_count','N/A')}</div><div class="metric-lbl">Certificados</div></div>
            <div class="metric-tile"><div class="metric-val" style="color:#FF4560">{n_critical}</div><div class="metric-lbl">Critical</div></div>
            <div class="metric-tile"><div class="metric-val" style="color:#F5C842">{n_warning}</div><div class="metric-lbl">Warning</div></div>
            <div class="metric-tile"><div class="metric-val" style="color:#7C6BF5">{n_info}</div><div class="metric-lbl">Info</div></div>
          </div>
          <p style="margin:0.75rem 0 0;font-size:0.82rem;color:#8B90A8">{r.get('summary','')}</p>
        </div>
        """, unsafe_allow_html=True)

        if auto_fixes:
            with st.expander(f"✅ {len(auto_fixes)} fixes auto-aplicados"):
                for fix in auto_fixes:
                    st.markdown(f"""
                    <div class="fix-row">
                      <span class="fix-auto">AUTO-CORREGIDO</span>
                      <div>
                        <span style="font-size:0.78rem;color:#E8EAF2;font-weight:600">{fix.get('fix_id','')} · {fix.get('type','')} · {fix.get('field','')}</span>
                        <div style="font-size:0.75rem;color:#8B90A8;margin-top:2px">{fix.get('description','')}</div>
                        <div style="font-size:0.72rem;color:#525870;margin-top:2px">{fix.get('records_affected',0)} registros afectados · reversible: {fix.get('reversible', True)}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

        if requires_human:
            with st.expander(f"⚠️ {len(requires_human)} issues requieren intervención humana"):
                for rh in requires_human:
                    st.markdown(f"""
                    <div class="fix-row">
                      <span class="fix-human">REQUIERE HUMANO</span>
                      <div>
                        <span style="font-size:0.78rem;color:#E8EAF2;font-weight:600">{rh.get('issue_id','')}</span>
                        <div style="font-size:0.75rem;color:#8B90A8;margin-top:2px">{rh.get('reason','')}</div>
                        <div style="font-size:0.72rem;color:#F5C842;margin-top:2px">→ {rh.get('suggested_action','')}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

        if issues:
            with st.expander(f"📋 Ver {len(issues)} hallazgos del auditor"):
                for iss in issues:
                    sev = iss.get("severity", "INFO")
                    st.markdown(f"""
                    <div class="issue-row">
                      <span class="sev-pill sev-{sev}">{sev}</span>
                      <div>
                        <span style="font-size:0.78rem;color:#E8EAF2;font-weight:600">{iss.get('id','')} · {iss.get('field','')}</span>
                        <div style="font-size:0.75rem;color:#8B90A8;margin-top:2px">{iss.get('description','')}</div>
                        <div style="font-size:0.72rem;color:#525870;margin-top:2px">→ {iss.get('action','')}</div>
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
                        get_active_data(),
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
# STEP 3 — STORYTELLING ADVISOR
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["cert_result"] and st.session_state["viz_result"]:
    st.divider()
    st.markdown("### Step 3 — Narrativa y Storytelling")

    if st.session_state["story_result"] is None:
        if st.button("▶ Ejecutar storytelling-architect", key="run_story"):
            with st.spinner("📖 Consultando base de conocimiento de storytelling…"):
                try:
                    client = get_client()
                    result = storytelling_advisor.run(
                        get_active_data(),
                        st.session_state["viz_result"],
                        client,
                    )
                    st.session_state["story_result"] = result
                    st.session_state["current_step"] = max(st.session_state["current_step"], 4)
                    st.session_state["error"] = None
                    st.rerun()
                except Exception as e:
                    st.session_state["story_result"] = {}
                    st.session_state["current_step"] = max(st.session_state["current_step"], 4)
                    st.session_state["error"] = f"storytelling-architect falló (continuando): {e}"
                    st.rerun()

    if st.session_state["story_result"] is not None:
        sr = st.session_state["story_result"]
        estructura = sr.get("estructura", "—")
        arco = sr.get("arco_audiencia", "—")
        titulos = sr.get("titulos", {})

        estructura_badge = f'<span class="badge badge-blue">{estructura}</span>'
        arco_badge = f'<span class="badge badge-green">{arco}</span>'

        titulos_html = "".join(
            f'<div style="font-size:0.78rem;color:#374151;padding:3px 0;border-bottom:1px solid #f3f4f6">'
            f'<span style="color:#6b7280;font-size:0.7rem">{vid}</span> — {titulo}</div>'
            for vid, titulo in titulos.items()
        ) if titulos else '<div style="color:#9ca3af;font-size:0.78rem">Sin títulos generados</div>'

        cta = sr.get("call_to_action", "")
        summary = sr.get("summary", "")
        principios = sr.get("principios_aplicados", [])

        st.markdown(f"""
        <div class="card card-info">
          <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;flex-wrap:wrap">
            <span style="font-weight:700;color:#1f2937">Estructura</span>
            {estructura_badge}
            <span style="font-weight:700;color:#1f2937;margin-left:0.5rem">Audiencia</span>
            {arco_badge}
          </div>
          <p style="margin:0 0 0.75rem;font-size:0.88rem;color:#111827;font-weight:600">
            {sr.get('narrativa_principal', '')}
          </p>
          <div style="margin-bottom:0.75rem">
            <div style="font-size:0.72rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">
              Títulos narrativos
            </div>
            {titulos_html}
          </div>
          <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:0.6rem 0.9rem;margin-bottom:0.75rem">
            <span style="font-size:0.7rem;font-weight:700;color:#1e40af;text-transform:uppercase;letter-spacing:0.5px">Call to Action</span>
            <div style="font-size:0.82rem;color:#1e3a8a;margin-top:2px;font-weight:600">{cta}</div>
          </div>
          <p style="margin:0;font-size:0.78rem;color:#6b7280">{summary}</p>
          {'<div style="margin-top:0.5rem;font-size:0.72rem;color:#9ca3af">Principios: ' + ' · '.join(principios) + '</div>' if principios else ''}
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — DESIGN ARCHITECT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["story_result"] is not None:
    st.divider()
    st.markdown("### Step 4 — Identidad Visual")

    if st.session_state["design_result"] is None:
        if st.button("▶ Ejecutar design-architect", key="run_design"):
            with st.spinner("🎨 Definiendo identidad visual del dashboard…"):
                try:
                    client = get_client()
                    result = design_architect.run(
                        st.session_state["story_result"],
                        st.session_state["viz_result"],
                        st.session_state["cert_result"],
                        client,
                    )
                    st.session_state["design_result"] = result
                    st.session_state["current_step"] = max(st.session_state["current_step"], 5)
                    st.session_state["error"] = None
                    st.rerun()
                except Exception as e:
                    st.session_state["design_result"] = {}
                    st.session_state["current_step"] = max(st.session_state["current_step"], 5)
                    st.session_state["error"] = f"design-architect falló (continuando): {e}"
                    st.rerun()

    if st.session_state["design_result"] is not None:
        dr = st.session_state["design_result"]
        tema = dr.get("tema_visual", "—")
        fuentes = dr.get("fuentes", {})
        paleta = dr.get("paleta", {})
        justificacion = dr.get("justificacion", "")
        summary_d = dr.get("summary", "")

        color_chips = "".join(
            f'<div style="display:inline-flex;align-items:center;gap:4px;margin-right:6px;margin-bottom:4px">'
            f'<div style="width:18px;height:18px;border-radius:3px;background:{hex_val};border:1px solid #d1d5db"></div>'
            f'<span style="font-size:0.68rem;color:#6b7280">{key}</span></div>'
            for key, hex_val in paleta.items() if hex_val
        )

        st.markdown(f"""
        <div class="card card-success">
          <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem">
            <span style="font-weight:700;color:#1f2937">Tema</span>
            <span class="badge badge-blue">{tema}</span>
          </div>
          <div class="metric-grid" style="margin-bottom:0.75rem">
            <div class="metric-tile">
              <div style="font-size:0.7rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px">Display</div>
              <div style="font-size:0.92rem;font-weight:700;color:#111827">{fuentes.get('display','—')}</div>
            </div>
            <div class="metric-tile">
              <div style="font-size:0.7rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px">Mono/Datos</div>
              <div style="font-size:0.92rem;font-weight:700;color:#111827">{fuentes.get('mono','—')}</div>
            </div>
            <div class="metric-tile">
              <div style="font-size:0.7rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px">Body</div>
              <div style="font-size:0.92rem;font-weight:700;color:#111827">{fuentes.get('body','—')}</div>
            </div>
          </div>
          <div style="margin-bottom:0.75rem">
            <div style="font-size:0.72rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px">Paleta</div>
            <div>{color_chips}</div>
          </div>
          <p style="margin:0 0 4px;font-size:0.78rem;color:#374151">{justificacion}</p>
          <p style="margin:0;font-size:0.75rem;color:#6b7280">{summary_d}</p>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — DASHBOARD ARCHITECT (shell + charts pipeline)
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["design_result"] is not None:
    st.divider()
    st.markdown("### Step 5 — Generación del Dashboard")
    st.caption("⚡ Sonnet 4.6 (shell) + Opus 4.7 (gráficos) — ~4-8 llamadas paralelas")

    if st.session_state["html_code"] is None:
        if st.button("▶ Ejecutar dashboard-architect", key="run_arch"):
            _stage_text = st.empty()
            _prog_bar   = st.progress(0)

            def _on_progress(msg: str, pct: int):
                _stage_text.markdown(
                    f'<div class="section-title">{msg}</div>',
                    unsafe_allow_html=True,
                )
                _prog_bar.progress(min(pct, 100) / 100)

            try:
                client = get_client()
                html = dashboard_architect.run(
                    get_active_data(),
                    st.session_state["viz_result"],
                    st.session_state["cert_result"],
                    client,
                    story_result=st.session_state["story_result"],
                    design_result=st.session_state["design_result"],
                    brand_result=st.session_state["brand_result"],
                    progress_callback=_on_progress,
                )
                _stage_text.empty()
                _prog_bar.empty()
                st.session_state["html_code"] = html
                st.session_state["current_step"] = max(st.session_state["current_step"], 6)
                st.session_state["error"] = None
                st.rerun()
            except Exception as e:
                _stage_text.empty()
                _prog_bar.empty()
                st.session_state["error"] = f"dashboard-architect falló: {e}"
                st.rerun()

    if st.session_state["html_code"]:
        html = st.session_state["html_code"]
        vizs     = (st.session_state.get("viz_result") or {}).get("visualizations", [])
        viz_ids  = [v["id"] for v in vizs]
        from agents.dashboard_architect_charts import validate_html as _validate
        val      = _validate(html, viz_ids)
        n_svg    = html.count("<svg")
        n_lines  = html.count("\n")
        size_kb  = len(html.encode()) / 1024

        card_cls = "card-success" if val["valid"] else "card-warn"
        st.markdown(f"""
        <div class="card {card_cls}">
          <div class="metric-grid">
            <div class="metric-tile"><div class="metric-val">{val['coverage']}</div><div class="metric-lbl">Gráficos generados</div></div>
            <div class="metric-tile"><div class="metric-val">{n_lines:,}</div><div class="metric-lbl">Líneas HTML</div></div>
            <div class="metric-tile"><div class="metric-val">{size_kb:.1f} KB</div><div class="metric-lbl">Tamaño</div></div>
            <div class="metric-tile"><div class="metric-val">{n_svg}</div><div class="metric-lbl">SVG</div></div>
          </div>
          {('<div style="margin-top:0.5rem;font-size:0.78rem;color:#F5C842">⚠ Faltantes: ' + ', '.join(val["issues"]) + '</div>') if not val["valid"] else ''}
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Preview del código HTML"):
            preview = html[:3000] + ("\n\n[... truncado ...]" if len(html) > 3000 else "")
            st.markdown(f'<div class="html-preview">{preview}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — D3 AUDITOR (con auto-corrección)
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["html_code"]:
    st.divider()
    st.markdown("### Step 6 — Auditoría de Calidad")

    if st.session_state["audit_result"] is None:
        if st.button("▶ Ejecutar d3-dashboard-auditor", key="run_audit"):
            with st.spinner("🔎 Auditando dashboard… si hay issues críticos se auto-corrige automáticamente"):
                try:
                    client = get_client()
                    first_result = d3_auditor.run(
                        st.session_state["html_code"],
                        st.session_state["viz_result"],
                        client,
                    )

                    if first_result.get("verdict") == "RECHAZADO":
                        # Auto-correction: surgical patch of specific flags, then re-audit
                        all_flags = first_result.get("flags", [])
                        corrected_html = audit_fix_html(
                            st.session_state["html_code"],
                            all_flags,
                            client,
                        )
                        final_result = d3_auditor.run(corrected_html, st.session_state["viz_result"], client)

                        old_flags = first_result.get("flags", [])
                        new_flags = final_result.get("flags", [])
                        old_crits = [f for f in old_flags if f.get("type") in ("CRÍTICO", "CRITICAL")]
                        new_crits = [f for f in new_flags if f.get("type") in ("CRÍTICO", "CRITICAL")]

                        st.session_state["html_code"] = corrected_html
                        st.session_state["audit_result"] = final_result
                        st.session_state["correction_summary"] = {
                            "old_score": first_result.get("score", 0),
                            "new_score": final_result.get("score", 0),
                            "old_verdict": first_result.get("verdict", ""),
                            "new_verdict": final_result.get("verdict", ""),
                            "old_flags": len(old_flags),
                            "new_flags": len(new_flags),
                            "old_critical": len(old_crits),
                            "new_critical": len(new_crits),
                            "issues_addressed": [
                                f"{f.get('area','')}: {f.get('issue','')}" for f in old_crits
                            ],
                        }
                    else:
                        st.session_state["audit_result"] = first_result
                        st.session_state["correction_summary"] = None

                    st.session_state["current_step"] = max(st.session_state["current_step"], 7)
                    st.session_state["error"] = None
                    st.rerun()
                except Exception as e:
                    st.session_state["error"] = f"d3-auditor falló: {e}"
                    st.rerun()

    if st.session_state["audit_result"]:
        # ── Correction summary card ─────────────────────────────────────────
        cs = st.session_state.get("correction_summary")
        if cs:
            score_delta = cs["new_score"] - cs["old_score"]
            delta_sign = "+" if score_delta >= 0 else ""
            crit_delta = cs["old_critical"] - cs["new_critical"]

            issues_html = "".join(
                f'<div style="font-size:0.75rem;color:#374151;padding:3px 0;border-bottom:1px solid #f3f4f6">'
                f'<span style="color:#dc2626;font-weight:600">CRÍTICO corregido:</span> {iss}</div>'
                for iss in cs["issues_addressed"]
            )
            st.markdown(f"""
            <div class="card card-warn" style="border-color:#2563eb;background:#eff6ff">
              <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem">
                <span style="font-size:1.1rem">🔄</span>
                <span style="font-weight:700;color:#1e40af;font-size:0.95rem">Auto-corrección aplicada</span>
                <span class="badge badge-blue">Paso 5 → re-generado</span>
              </div>
              <div class="metric-grid">
                <div class="metric-tile">
                  <div class="metric-val" style="color:{'#16a34a' if score_delta >= 0 else '#dc2626'}">{delta_sign}{score_delta}</div>
                  <div class="metric-lbl">Score ({cs['old_score']} → {cs['new_score']})</div>
                </div>
                <div class="metric-tile">
                  <div class="metric-val" style="color:#16a34a">{crit_delta}</div>
                  <div class="metric-lbl">Críticos resueltos ({cs['old_critical']} → {cs['new_critical']})</div>
                </div>
                <div class="metric-tile">
                  <div class="metric-val">{cs['old_flags'] - cs['new_flags']}</div>
                  <div class="metric-lbl">Flags totales resueltos</div>
                </div>
              </div>
              <div style="margin-top:0.5rem">{issues_html}</div>
            </div>
            """, unsafe_allow_html=True)

        # ── Main audit card ────────────────────────────────────────────────
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
              ⚠️ El dashboard sigue con issues críticos tras la auto-corrección. Puedes regenerar manualmente.
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="retry-btn">', unsafe_allow_html=True)
            if st.button("🔄 Regenerar Dashboard manualmente", key="retry_build", use_container_width=False):
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
                        <span style="font-size:0.78rem;color:#1f2937;font-weight:600">{flag.get('area','')}</span>
                        <div style="font-size:0.75rem;color:#6b7280;margin-top:2px">{flag.get('issue','')}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — DOCS GENERATOR + DOWNLOADS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["audit_result"]:
    st.divider()
    st.markdown("### Step 7 — Documentación Técnica")

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
                        data=get_active_data(),
                        client=client,
                    )
                    st.session_state["docs_result"] = result
                    st.session_state["current_step"] = 8
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
        render_pipeline_bar(8)
        st.markdown("""
        <div class="card card-success" style="text-align:center;padding:1.5rem">
          <div style="font-size:2rem">🎉</div>
          <div style="font-size:1.1rem;font-weight:700;color:#4ade80;margin:0.5rem 0">Pipeline completado</div>
          <div style="font-size:0.85rem;color:#94a3b8">
            Dataset certificado → Visualizaciones seleccionadas → Narrativa → Identidad visual → Dashboard generado → Auditado → Documentado
          </div>
        </div>
        """, unsafe_allow_html=True)
