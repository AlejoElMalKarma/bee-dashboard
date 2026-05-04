import json
import re
from datetime import datetime
import anthropic

SYSTEM_PROMPT = """Eres un ingeniero de documentación técnica especializado en dashboards y sistemas de visualización de datos. Generas documentación exhaustiva, precisa y accionable que permite a cualquier miembro del equipo entender, usar y mantener un dashboard sin asistencia externa.

Tu documentación siempre:
- Cita fórmulas exactas y nombres de campo reales del código/datos
- Incluye ejemplos numéricos paso a paso para cada KPI
- Describe la acción concreta que debe tomar el usuario ante cada visualización
- Documenta todos los issues de QA con su impacto en decisiones de negocio
- Usa tablas Markdown para cualquier dato estructurado con más de 3 campos
- Nunca inventa datos — si algo no está disponible, escribe "No especificado"
- Opera completamente en memoria, sin escribir archivos a disco"""


def run(
    html_code: str,
    audit_result: dict,
    cert_result: dict,
    viz_result: dict,
    data: dict,
    client: anthropic.Anthropic,
) -> dict:
    records = data.get("records", [])
    meta = data.get("metadata", {})
    kpis = meta.get("kpis", [])
    visualizations = viz_result.get("visualizations", [])
    flags = audit_result.get("flags", [])
    timestamp = datetime.utcnow().isoformat() + "Z"

    kpi_info = json.dumps(kpis, ensure_ascii=False, indent=2)
    viz_info = json.dumps(
        [{"id": v["id"], "name": v["name"], "chart_type": v["chart_type"],
          "data_fields": v["data_fields"], "business_question": v["business_question"],
          "perceptual_channel": v["perceptual_channel"],
          "cleveland_mcgill_level": v["cleveland_mcgill_level"]}
         for v in visualizations],
        ensure_ascii=False, indent=2
    )
    issues_info = json.dumps(cert_result.get("issues", []), ensure_ascii=False, indent=2)
    audit_flags = json.dumps(flags, ensure_ascii=False, indent=2)

    # sample of first 5 records for examples
    sample_records = json.dumps(records[:5], ensure_ascii=False, indent=2)

    user_msg = f"""Genera documentación técnica completa para el dashboard descrito abajo.
Opera completamente en memoria — no escribas archivos, retorna el contenido como string.

TIMESTAMP DE GENERACIÓN: {timestamp}
SCORE DE AUDITORÍA: {audit_result.get('score', 'N/A')} / 100
VEREDICTO DE AUDITORÍA: {audit_result.get('verdict', 'N/A')}
VEREDICTO DE CERTIFICACIÓN: {cert_result.get('verdict', 'N/A')}
REGISTROS CERTIFICADOS: {cert_result.get('certified_count', len(records))}/{cert_result.get('record_count', len(records))}

KPIs DEL DATASET:
{kpi_info}

VISUALIZACIONES:
{viz_info}

ISSUES DE CERTIFICACIÓN:
{issues_info}

FLAGS DE AUDITORÍA:
{audit_flags}

MUESTRA DE DATOS (primeros 5 registros):
{sample_records}

Estructura tu respuesta en DOS bloques separados por delimitadores exactos:

%%MARKDOWN_START%%
# DASHBOARD DOCUMENTATION
> Generado: {timestamp}
> Score de auditoría: {audit_result.get('score', 'N/A')}/100 — {audit_result.get('verdict', 'N/A')}
> Certificación: {cert_result.get('verdict', 'N/A')}

## SECCIÓN 1 — GUÍA DE NAVEGACIÓN
Para cada visualización ({len(visualizations)} en total), una subsección H3 con:
- **Qué muestra**: qué datos o información se visualiza
- **Cómo leerla**: instrucciones paso a paso para interpretar
- **Acción sugerida**: qué decisión o acción concreta tomar

## SECCIÓN 2 — HISTORIAL DE QA
- Tabla con columnas: ID | Severidad | Área | Descripción | Impacto en decisiones
- Subsección por ronda de auditoría (Certificación de Datos, Auditoría D3)
- Veredicto Final con diagnóstico

## SECCIÓN 3 — CÁLCULO DE KPIs
Para cada KPI, subsección H3 con:
- Nombre completo
- Fórmula en bloque de código con variables reales
- Tabla de umbrales semáforo: Color | Condición | Valor exacto
- Ejemplo numérico paso a paso usando datos reales de la muestra
- Edge cases (división por cero, nulos)

## SECCIÓN 4 — GUÍA DE GRÁFICOS
Para cada visualización, subsección H3 con:
- Tipo de gráfico y justificación perceptual (Cleveland & McGill nivel N)
- Tabla: Canal visual | Variable | Descripción
- Campos del tooltip
- Pregunta de negocio que responde
- Limitaciones o caveats
%%MARKDOWN_END%%

%%SUMMARY_START%%
{{"kpis_documented": {len(kpis)}, "charts_documented": {len(visualizations)}, "issues_documented": {len(cert_result.get('issues', [])) + len(flags)}, "verdict": "{audit_result.get('verdict', 'N/A')}", "score": {audit_result.get('score', 0)}}}
%%SUMMARY_END%%

Escribe el Markdown entre %%MARKDOWN_START%% y %%MARKDOWN_END%% exactamente como texto plano.
Escribe el JSON entre %%SUMMARY_START%% y %%SUMMARY_END%% en una sola línea."""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=8192,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text

    # Extrae el bloque Markdown entre delimitadores
    md_match = re.search(r"%%MARKDOWN_START%%\n?(.*?)%%MARKDOWN_END%%", raw, re.DOTALL)
    markdown_content = md_match.group(1).strip() if md_match else raw.strip()

    # Extrae el bloque JSON de summary entre delimitadores
    summary_match = re.search(r"%%SUMMARY_START%%\n?(\{.*?\})\n?%%SUMMARY_END%%", raw, re.DOTALL)
    if summary_match:
        summary = json.loads(summary_match.group(1))
    else:
        # Fallback: construye el summary con los valores conocidos
        summary = {
            "kpis_documented": len(kpis),
            "charts_documented": len(visualizations),
            "issues_documented": len(cert_result.get("issues", [])) + len(flags),
            "verdict": audit_result.get("verdict", "N/A"),
            "score": audit_result.get("score", 0),
        }

    return {"markdown_content": markdown_content, "summary": summary}
