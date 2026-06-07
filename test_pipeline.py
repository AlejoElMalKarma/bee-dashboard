# test_pipeline.py

import anthropic
import json
import time
from dotenv import load_dotenv

load_dotenv()  # carga ANTHROPIC_API_KEY desde .env

client = anthropic.Anthropic()

# Cargar dataset
print("📁 Cargando dataset...")
with open("data/sales_report.json", "r") as f:
    raw = json.load(f)

# sales_report.json ya tiene estructura {metadata, records}
data = raw if "records" in raw else {
    "metadata": {"dataset": "sales_report", "kpis": []},
    "records": raw
}

from agents import (
    brand_reader,
    data_certifier,
    dataviz_selector,
    storytelling_advisor,
    design_architect,
    dashboard_architect,
    d3_auditor,
    docs_generator
)

# ── BRAND ──────────────────────────────────────
print("\n🎨 Leyendo BRAND.md...")
brand = brand_reader.run()
print(f"   Empresa: {brand.get('empresa')}")

# ── CERTIFIER ──────────────────────────────────
print("\n🔍 Certificando datos...")
start = time.time()
cert = data_certifier.run(data, client)
print(f"   Veredicto: {cert.get('verdict')}")
print(f"   Certificados: {cert.get('certified_count')}/{cert.get('record_count')}")
print(f"   Fixes automáticos: {len(cert.get('auto_fixes_applied', []))}")
print(f"   Tiempo: {time.time()-start:.1f}s")

# certified_data ya es {metadata, records} — usarlo directo
certified = cert.get("certified_data")
pipeline_data = certified if (certified and "records" in certified) else data

# ── DATAVIZ SELECTOR ───────────────────────────
print("\n📊 Seleccionando visualizaciones...")
start = time.time()
viz = dataviz_selector.run(pipeline_data, cert, client)
print(f"   Visualizaciones: {len(viz.get('visualizations', []))}")
for v in viz.get("visualizations", []):
    print(f"   → {v.get('id')}: {v.get('name')}")
print(f"   Tiempo: {time.time()-start:.1f}s")

# ── STORYTELLING ───────────────────────────────
print("\n📖 Generando narrativa...")
start = time.time()
story = storytelling_advisor.run(pipeline_data, viz, client)
print(f"   Estructura: {story.get('estructura')}")
print(f"   Narrativa: {story.get('narrativa_principal', '')[:80]}...")
print(f"   Tiempo: {time.time()-start:.1f}s")

# ── DESIGN ─────────────────────────────────────
print("\n🎨 Definiendo diseño...")
start = time.time()
design = design_architect.run(story, viz, cert, client)
print(f"   Tema: {design.get('tema_visual')}")
print(f"   Fuentes: {design.get('fuentes')}")
print(f"   Tiempo: {time.time()-start:.1f}s")

# ── DASHBOARD ARCHITECT ────────────────────────
print("\n🏗 Generando dashboard...")
print("   (puede tardar 60-90 segundos con Opus)")
start = time.time()
html = dashboard_architect.run(
    pipeline_data, viz, cert,
    story_result=story,
    design_result=design,
    brand_result=brand,
    client=client
)
n_viz = html.count("function chartViz")
n_lines = html.count("\n")
size_kb = len(html.encode()) / 1024
print(f"   Líneas: {n_lines:,}")
print(f"   Tamaño: {size_kb:.1f} KB")
print(f"   Funciones chartViz: {n_viz}/{len(viz.get('visualizations', []))}")
print(f"   Tiempo: {time.time()-start:.1f}s")

# Guardar HTML provisional
with open("output_test.html", "w", encoding="utf-8") as f:
    f.write(html)
print("   💾 Guardado: output_test.html")

# ── AUDITOR ────────────────────────────────────
print("\n🔎 Auditando dashboard...")
audit = {"score": "N/A", "verdict": "OMITIDO", "flags": []}
try:
    start = time.time()
    audit = d3_auditor.run(html, viz, client)
    print(f"   Score: {audit.get('score')}/100")
    print(f"   Veredicto: {audit.get('verdict')}")
    flags = audit.get("flags", [])
    criticos = [f for f in flags if f.get("type") in ("CRÍTICO", "CRITICAL")]
    warnings = [f for f in flags if f.get("type") in ("ADVERTENCIA", "WARNING")]
    print(f"   Críticos: {len(criticos)} | Warnings: {len(warnings)}")
    print(f"   Tiempo: {time.time()-start:.1f}s")
except Exception as e:
    print(f"   ⚠ Auditor omitido: {e}")

# ── DOCS ───────────────────────────────────────
print("\n📄 Generando documentación...")
md_content = ""
try:
    start = time.time()
    docs = docs_generator.run(
        html_code=html,
        audit_result=audit,
        cert_result=cert,
        viz_result=viz,
        data=pipeline_data,
        client=client,
    )
    md_content = docs.get("markdown_content", "")
    print(f"   Tamaño doc: {len(md_content)//1024} KB")
    print(f"   Tiempo: {time.time()-start:.1f}s")
    with open("output_docs.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    print("   💾 Guardado: output_docs.md")
except Exception as e:
    print(f"   ⚠ Docs omitido: {e}")

# ── RESUMEN FINAL ──────────────────────────────
print("\n" + "="*50)
print("RESUMEN DEL PIPELINE")
print("="*50)
print(f"✅ Certificación:     {cert.get('verdict')}")
print(f"✅ Visualizaciones:   {len(viz.get('visualizations', []))}")
print(f"✅ Score auditoría:   {audit.get('score')}/100")
print(f"✅ Veredicto final:   {audit.get('verdict')}")
print(f"✅ Dashboard:         output_test.html")
print(f"✅ Documentación:     output_docs.md")
print("="*50)