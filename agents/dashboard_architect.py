import json
import anthropic

SYSTEM_PROMPT = """Eres un agente experto en diseño y creación de dashboards. Tu conocimiento integra arquitectura de datos, psicología cognitiva y diseño UX/UI. Aplicas rigurosamente los frameworks de Tamara Munzner (Nested Model), Edward Tufte (Data-Ink Ratio), Ben Shneiderman (Information Seeking Mantra), Stephen Few (perceptual design), y Alberto Cairo.

## REGLAS DE LAYOUT
- BANs (Big Ass Numbers) con KPIs críticos en esquina superior izquierda (patrón F/Z)
- Máximo 5-7 elementos por vista (Ley de Miller)
- Grid de 12 columnas, separaciones 16-24px, márgenes 32-48px
- Pirámide Invertida: estado (arriba) → tendencias (medio) → detalle (abajo)
- Agrupación temática bajo encabezados de sección

## REGLAS DE GRÁFICOS
- Sin pie charts, sin gauges, sin efectos 3D
- Barras siempre desde cero (Lie Factor = 1.0)
- Etiquetado directo (no leyendas flotantes)
- Data-Ink Ratio: eliminar chartjunk

## REGLAS DE COLOR Y ACCESIBILIDAD
- Verde/amarillo/rojo SIEMPRE con icono redundante (✓↑ / ⚠ / ✗↓)
- Contraste mínimo WCAG AA: 4.5:1 texto/fondo
- Paleta neutra para análisis; rojo/verde solo para alertas críticas
- Paleta accesible para daltonismo en series múltiples (Okabe-Ito)

## STACK TÉCNICO
- D3.js v7 desde CDN: https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js
- Datos cargados con d3.json() desde data/sales_report.json
- Módulos como IIFE que registran en window.Charts.*
- Sin ES modules (evitar problemas CORS con file://)
- Font: Inter desde Google Fonts
- Paleta: Verde #15803d | Amarillo #b45309 | Rojo #b91c1c | Neutro #374151 | Fondo #f9fafb
- Todos los SVG deben tener role="img" y aria-label

## CRITERIOS DE AUTOEVALUACIÓN (Framework CARE)
- Claridad: legible sin explicaciones externas
- Accionabilidad: decisión concreta inmediata
- Relevancia: cada elemento es necesario
- Ejecución: plan de acción ante desviaciones"""


def run(data: dict, viz_result: dict, cert_result: dict, client: anthropic.Anthropic) -> str:
    records = data.get("records", [])
    visualizations = viz_result.get("visualizations", [])
    layout = viz_result.get("layout", "")

    viz_specs = "\n".join(
        f"- {v['id']}: {v['name']} ({v['chart_type']}) — {v['business_question']}"
        for v in visualizations
    )

    # Detecta campos dinámicamente
    fields = list(records[0].keys()) if records else []
    # Busca columnas categóricas para dar contexto al agente
    categorical_summary = {}
    for f in fields:
        vals = [r[f] for r in records if isinstance(r.get(f), str)]
        unique = list(set(vals))
        if 1 < len(unique) <= 20:
            categorical_summary[f] = unique[:10]

    period_hint = ""
    for pf in ("period", "date", "fecha", "mes", "month"):
        if pf in fields:
            period_hint = f"- Período: {records[0].get(pf, '')} → {records[-1].get(pf, '')}"
            break

    cat_lines = "\n".join(f"- {k}: {', '.join(str(v) for v in vs)}" for k, vs in categorical_summary.items())

    user_msg = f"""Genera un dashboard HTML completo y funcional para el siguiente dataset.

DATASET COMPLETO:
- {len(records)} registros
- Campos disponibles: {', '.join(fields)}
{period_hint}
- Valores únicos por campo categórico:
{cat_lines if cat_lines else '  (no se detectaron campos categóricos)'}
- Muestra de los primeros 3 registros: {json.dumps(records[:3], ensure_ascii=False)}

VISUALIZACIONES RECOMENDADAS POR EL DATAVIZ SELECTOR:
{viz_specs}

LAYOUT SUGERIDO:
{layout}

RESULTADO DE CERTIFICACIÓN:
- Estado: {cert_result.get('verdict', 'N/A')}
- Issues: {len(cert_result.get('issues', []))} hallazgos

DATASET COMPLETO PARA EMBEBER (usa exactamente este JSON):
{json.dumps(data, ensure_ascii=False)}

INSTRUCCIONES CRÍTICAS:
1. Entrega UN SOLO archivo HTML completo y funcional — todo en un solo bloque, inline.
2. OBLIGATORIO: los datos deben estar embebidos como `const DATA = <json>;` dentro de una etiqueta <script> en el HTML.
   NO uses d3.json(), NO uses fetch(), NO hagas ninguna llamada HTTP a archivos externos para los datos.
   El dashboard debe funcionar al abrir el archivo HTML directamente en el browser (file://) sin servidor.
3. Usa D3.js v7 desde CDN: https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js
4. Carga la fuente Inter desde Google Fonts.
5. Inicializa los gráficos con `document.addEventListener('DOMContentLoaded', ...)` usando los datos de `const DATA`.
6. Maneja arrays vacíos y valores nulos en todos los gráficos (evita división por cero).
7. Aplica todas las reglas de diseño del system prompt.
8. Títulos narrativos que comunican el hallazgo, no solo el contenido.
9. Semáforos con redundancia visual (color + icono) — NUNCA solo color.
10. Todos los SVG con role="img" y aria-label.
11. Sin código truncado — el HTML debe estar completo hasta </html>.

Responde SOLO con el código HTML completo, comenzando con <!DOCTYPE html> y terminando con </html>. Sin texto adicional, sin explicaciones."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=16000,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    )
    html = response.content[0].text.strip()
    # strip any accidental markdown fences
    if html.startswith("```"):
        html = html.split("\n", 1)[1] if "\n" in html else html
        html = html.rsplit("```", 1)[0] if "```" in html else html
    return html.strip()
