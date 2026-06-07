import copy
import json
import re
import statistics
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


# ── Deterministic auto-fix engine ──────────────────────────────────────────────

def _apply_auto_fixes(records: list) -> tuple[list, list]:
    """Apply deterministic fixes to records. Returns (fixed_records, fix_log).
    Rules: fix only when there is one correct answer; never invent or impute data."""
    if not records:
        return records, []

    fixed = copy.deepcopy(records)
    fixes: list[dict] = []
    fields = list(fixed[0].keys())
    _counter = [1]

    def _fid() -> str:
        fid = f"FIX-{_counter[0]:03d}"
        _counter[0] += 1
        return fid

    # FIX 1 — Duplicate primary key → composite key
    pk_field = next((f for f in fields if f.lower() in ("id", "record_id", "pk")), None)
    if pk_field:
        ids = [str(r.get(pk_field, "")) for r in fixed]
        if len(ids) != len(set(ids)):
            period_field = next(
                (f for f in fields if f.lower() in
                 ("period", "trimestre", "quarter", "mes", "month", "fecha", "date")),
                None,
            )
            if period_field:
                for r in fixed:
                    r["record_id"] = f"{r.get(pk_field, '')}_{r.get(period_field, '')}"
                fixes.append({
                    "fix_id": _fid(),
                    "type": "CLAVE_COMPUESTA",
                    "field": pk_field,
                    "description": f"Generado 'record_id' = {pk_field} + '_' + {period_field} para resolver clave primaria duplicada",
                    "records_affected": len(fixed),
                    "reversible": True,
                })
                fields = list(fixed[0].keys())  # refresh

    # FIX 2 — Proportions (0-1) → add _pct enriched field
    for field in list(fields):
        vals = [r[field] for r in fixed if isinstance(r.get(field), (int, float))]
        if (len(vals) >= 3
                and all(0.0 <= v <= 1.0 for v in vals)
                and not any(k in field.lower() for k in ("pct", "rate", "ratio", "score", "flag"))):
            pct_field = f"{field}_pct"
            if pct_field not in fields:
                for r in fixed:
                    if isinstance(r.get(field), (int, float)):
                        r[pct_field] = round(r[field] * 100, 2)
                fixes.append({
                    "fix_id": _fid(),
                    "type": "ENRIQUECIDO",
                    "field": field,
                    "description": f"Agregado '{pct_field}' = {field} × 100 (valores detectados como proporciones 0-1)",
                    "records_affected": len(vals),
                    "reversible": True,
                })
                fields = list(fixed[0].keys())

    # FIX 3 — Whitespace normalization in string fields
    for field in list(fields):
        changed = 0
        for r in fixed:
            val = r.get(field)
            if isinstance(val, str) and val != val.strip():
                r[field] = val.strip()
                changed += 1
        if changed:
            fixes.append({
                "fix_id": _fid(),
                "type": "NORMALIZADO",
                "field": field,
                "description": f"Eliminado whitespace en {changed} registros del campo '{field}'",
                "records_affected": changed,
                "reversible": True,
            })

    # FIX 4 — Outlier flagging (z-score > 2.5) — value untouched, flag added
    for field in list(fields):
        if any(k in field.lower() for k in ("outlier_", "flag", "record_id", "_pct")):
            continue
        vals = [r[field] for r in fixed if isinstance(r.get(field), (int, float))]
        if len(vals) < 4:
            continue
        try:
            mean = statistics.mean(vals)
            stdev = statistics.stdev(vals)
            if stdev == 0:
                continue
            flag_field = f"outlier_{field}"
            if flag_field in fields:
                continue
            outlier_count = 0
            for r in fixed:
                val = r.get(field)
                if isinstance(val, (int, float)):
                    r[flag_field] = abs((val - mean) / stdev) > 2.5
                    if r[flag_field]:
                        outlier_count += 1
            if outlier_count:
                fixes.append({
                    "fix_id": _fid(),
                    "type": "FLAGGEADO",
                    "field": field,
                    "description": f"Agregado 'outlier_{field}' en {outlier_count} registros con z-score > 2.5 (valores NO modificados)",
                    "records_affected": outlier_count,
                    "reversible": True,
                })
        except Exception:
            pass

    return fixed, fixes


# ── Main run function ──────────────────────────────────────────────────────────

def run(data: dict, client: anthropic.Anthropic) -> dict:
    records = data.get("records", [])
    meta = data.get("metadata", {})
    kpis = meta.get("kpis", [])

    # Step 1: deterministic Python fixes
    fixed_records, auto_fixes = _apply_auto_fixes(records)
    fixed_data = {**data, "records": fixed_records}
    fields = list(fixed_records[0].keys()) if fixed_records else []

    kpi_rules = "\n".join(
        f"- {k['name']}: fórmula={k['formula']}, benchmark={k['benchmark']}, "
        f"green={k['status_rules']['green']}, yellow={k['status_rules']['yellow']}, red={k['status_rules']['red']}"
        for k in kpis
    ) if kpis else "No hay KPIs en los metadatos."

    fixes_note = ""
    if auto_fixes:
        fixes_note = "\nFIXES AUTO-APLICADOS ANTES DE ESTA AUDITORÍA (no reportar como CRITICAL):\n" + "\n".join(
            f"- [{f['type']}] {f['field']}: {f['description']}"
            for f in auto_fixes
        ) + "\n"

    user_msg = f"""Audita el siguiente dataset.

DICCIONARIO DE DATOS:
- Campos: {', '.join(fields)}
- Clave primaria: id / record_id
- Registros esperados: {len(fixed_records)}
- Granularidad: un registro por (rep_id, period)

REGLAS DE NEGOCIO:
{kpi_rules}
- revenue y target deben ser > 0
- leads debe ser > 0; deals_closed debe ser <= leads
- kpi_meta = (revenue / target) * 100, redondeo 1 decimal
- kpi_conversion = (deals_closed / leads) * 100, redondeo 1 decimal
- kpi_meta_status y kpi_conversion_status deben coincidir con los umbrales
{fixes_note}
DATASET (primeros 5 registros de muestra):
{json.dumps(fixed_records[:5], indent=2, ensure_ascii=False)}

DATASET COMPLETO ({len(fixed_records)} registros):
{json.dumps(fixed_records, ensure_ascii=False)}

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
    result = json.loads(raw)

    # Step 2: attach Python-side metadata
    result["auto_fixes_applied"] = auto_fixes
    result["requires_human"] = [
        {
            "issue_id": iss.get("id", ""),
            "reason": iss.get("description", ""),
            "suggested_action": iss.get("action", ""),
        }
        for iss in result.get("issues", [])
        if iss.get("severity") == "CRITICAL"
    ]
    result["certified_data"] = fixed_data

    return result
