import json
import re
import anthropic

SYSTEM_PROMPT = """Eres un ingeniero de datos senior especializado en aseguramiento de calidad, curación y certificación de datasets. Tu única responsabilidad es revisar, validar, enriquecer y certificar cualquier dataset antes de que sea consumido por un sistema downstream (dashboard, modelo, API, reporte). No construyes el sistema downstream; entregas los datos listos y certificados para quien lo construya.

## FASE 1 — AUDITORÍA ESTRUCTURAL
Verifica: conteo de registros vs esperado, presencia de todos los campos del diccionario, tipos de dato, unicidad de clave primaria, completitud (nulos, vacíos, NaN, valores centinela).

## FASE 2 — VALIDACIÓN DE DOMINIO Y CONSISTENCIA
Verifica: catálogos y enumeraciones, coherencia entre campos relacionados, rangos y umbrales (CRITICAL si imposible, WARNING si improbable), recálculo de métricas derivadas con tolerancia de redondeo, recálculo de clasificaciones/semáforos, consistencia referencial.

## FASE 3 — DETECCIÓN DE ANOMALÍAS
Detecta: outliers estadísticos (z-score > 2.5 por defecto), anomalías de tendencia (variación > 40% vs período anterior), duplicados lógicos, huecos en cobertura de dimensiones, distribuciones extremas por categoría.

## FASE 4 — ENRIQUECIMIENTO (CAPA SEMÁNTICA GOLD)
Añade campos de gap (valor_real − benchmark), clasificación consolidada, rankings por métrica clave, vistas pre-agregadas (suma, promedio, mín, máx, conteo por dimensión).

## FASE 5 — QA SCORECARD Y CERTIFICACIÓN
Produce: resumen ejecutivo (máx 5 líneas), tabla de hallazgos con Issue ID/Fase/Severidad/Campo/Registro/Descripción/Acción, log de decisiones de curación, firma de certificación.

Severidades:
- CRITICAL: bloquea certificación si no se resuelve con corrección determinista
- WARNING: documenta pero no bloquea
- INFO: observación sin impacto

Estado final:
- APROBADO: sin issues CRITICAL
- APROBADO CON OBSERVACIONES: solo WARNING/INFO
- RECHAZADO: al menos un CRITICAL sin resolución determinista"""

OUTPUT_INSTRUCTIONS = """
Responde ÚNICAMENTE con este JSON válido — sin markdown fences, sin texto extra:

{
  "verdict": "APROBADO | APROBADO CON OBSERVACIONES | RECHAZADO",
  "completeness_pct": <número 0-100>,
  "record_count": <entero>,
  "certified_count": <entero>,
  "issues": [
    {
      "id": "ISS-N",
      "phase": "Fase N",
      "severity": "CRITICAL | WARNING | INFO",
      "field": "<campo afectado o 'global'>",
      "records": "<ID(s) de registro afectados o 'N/A'>",
      "description": "<descripción concisa del hallazgo>",
      "action": "<acción tomada o recomendada>"
    }
  ],
  "summary": "<2-3 oraciones con diagnóstico general y decisión de certificación>"
}"""


def run(data: dict, client: anthropic.Anthropic) -> dict:
    records = data.get("records", [])
    fields = list(records[0].keys()) if records else []
    meta = data.get("metadata", {})
    kpis = meta.get("kpis", [])

    kpi_rules = "\n".join(
        f"- {k['name']}: fórmula={k['formula']}, benchmark={k['benchmark']}, "
        f"green={k['status_rules']['green']}, yellow={k['status_rules']['yellow']}, red={k['status_rules']['red']}"
        for k in kpis
    ) if kpis else "No hay KPIs en los metadatos."

    user_msg = f"""Audita el siguiente dataset.

DICCIONARIO DE DATOS:
- Campos: {', '.join(fields)}
- Clave primaria: id
- Registros esperados: {len(records)}
- Granularidad: un registro por (rep_id, period)

REGLAS DE NEGOCIO:
{kpi_rules}
- revenue y target deben ser > 0
- leads debe ser > 0; deals_closed debe ser <= leads
- kpi_meta = (revenue / target) * 100, redondeo 1 decimal
- kpi_conversion = (deals_closed / leads) * 100, redondeo 1 decimal
- kpi_meta_status y kpi_conversion_status deben coincidir con los umbrales

DATASET (primeros 5 registros de muestra):
{json.dumps(records[:5], indent=2, ensure_ascii=False)}

DATASET COMPLETO ({len(records)} registros):
{json.dumps(records, ensure_ascii=False)}

{OUTPUT_INSTRUCTIONS}"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)
