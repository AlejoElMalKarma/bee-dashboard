import json
import re
import subprocess
import anthropic

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/d7669a1c-9470-456f-b335-0f544d244dfc"

SYSTEM_PROMPT = """Eres @storytelling-architect, experto en data storytelling aplicado a dashboards ejecutivos. Tu trabajo es tomar los datos de un dataset y las visualizaciones recomendadas, y construir una narrativa coherente que guíe al espectador hacia una decisión de negocio clara.

## ESTRUCTURAS NARRATIVAS DISPONIBLES

### 3 ACTOS (Aristóteles aplicado a datos)
- Acto 1 (Contexto): ¿Qué está pasando? → KPIs generales, estado actual
- Acto 2 (Conflicto): ¿Por qué? → Tendencias, anomalías, comparativas
- Acto 3 (Resolución): ¿Qué hacemos? → Recomendación, call to action

### ABT (And-But-Therefore)
- AND: contexto y situación actual de los datos
- BUT: el problema, tensión o anomalía detectada
- THEREFORE: la acción recomendada

### PIRÁMIDE INVERTIDA (periodismo de datos)
- Cima: el hallazgo más importante primero (BLUF: Bottom Line Up Front)
- Medio: evidencia y contexto
- Base: detalles y metodología

### KABOB (para métricas paralelas)
- Estructura horizontal donde cada visualización es independiente pero cohesionada por un hilo narrativo

## REGLAS DE TÍTULOS NARRATIVOS
- NUNCA descriptivos: "Ventas por región" ❌
- SIEMPRE con hallazgo: "La región Norte supera meta; Sur lleva 3 meses en rojo" ✅
- Prueba de lógica horizontal: leer solo los títulos debe contar la historia completa
- Máximo 10 palabras por título

## JERARQUÍA VISUAL NARRATIVA
1. BANs con estado general (¿cómo vamos?)
2. Comparativas y rankings (¿quién lidera/rezaga?)
3. Tendencias temporales (¿hacia dónde vamos?)
4. Distribuciones y correlaciones (¿por qué?)
5. Drill-down y detalle (solo si necesario)

## ARCOS DE AUDIENCIA
- c_level: máximo 3 KPIs críticos, sin granularidad, call to action ejecutivo
- analista: granularidad completa, drill-down, correlaciones
- comparativa: énfasis en benchmarks y gaps vs meta"""

DEFAULT_RESULT = {
    "narrativa_principal": "Los datos presentan métricas de rendimiento clave para la toma de decisiones ejecutivas.",
    "estructura": "piramide_invertida",
    "jerarquia_visual": [],
    "titulos": {},
    "call_to_action": "Revisar las métricas en rojo y definir plan de acción inmediato para las áreas bajo umbral.",
    "arco_audiencia": "c_level",
    "principios_aplicados": ["Pirámide Invertida (BLUF)", "Títulos con hallazgo", "Jerarquía visual narrativa"],
    "summary": "Dashboard ejecutivo con estructura de pirámide invertida: hallazgo crítico primero, evidencia después. Orientado a decisiones de C-level con mínimo tiempo de lectura.",
}


def _try_notebooklm(question: str) -> str | None:
    try:
        result = subprocess.run(
            ["claude", "-p",
             f"Use the notebooklm skill to query the notebook at {NOTEBOOK_URL}. "
             f"Respond only with the answer, no preamble. Question: {question}"],
            capture_output=True, text=True, timeout=90,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def run(data: dict, viz_result: dict, client: anthropic.Anthropic) -> dict:
    records = data.get("records", [])
    fields = list(records[0].keys()) if records else []
    meta = data.get("metadata", {})
    vizs = viz_result.get("visualizations", [])

    viz_list_str = ", ".join(f"{v['id']}: {v['name']}" for v in vizs)
    viz_ids = [v["id"] for v in vizs]

    data_type = "ventas y rendimiento" if any(
        k in " ".join(fields).lower() for k in ("sale", "venta", "revenue", "ingreso", "quota")
    ) else "métricas de negocio"

    q1 = (f"¿Qué estructura narrativa (3 actos, ABT, Pirámide Invertida) es más apropiada "
          f"para datos de {data_type} con campos {', '.join(fields[:5])} para audiencia ejecutiva?")
    q2 = f"¿Cómo ordenar visualmente estas visualizaciones para maximizar el impacto narrativo: {viz_list_str}?"
    q3 = f"Genera títulos narrativos con prueba de lógica horizontal para: {viz_list_str}"

    notebooklm_context = ""
    answers = []
    for q in [q1, q2, q3]:
        ans = _try_notebooklm(q)
        if ans:
            answers.append(f"P: {q}\nR: {ans}")
    if answers:
        notebooklm_context = "\n\nCONSULTA A NOTEBOOKLM:\n" + "\n\n".join(answers)

    titulos_template = ", ".join(f'"{v["id"]}": "<título narrativo>"' for v in vizs)
    viz_details = [
        {
            "id": v["id"],
            "name": v["name"],
            "chart_type": v.get("chart_type", ""),
            "objective": v.get("objective", ""),
            "business_question": v.get("business_question", ""),
        }
        for v in vizs
    ]

    user_msg = f"""Construye la narrativa para un dashboard ejecutivo basado en estos datos.

DATASET:
- Registros: {len(records)}
- Campos: {', '.join(fields)}
- Tipo de datos: {data_type}
- KPIs declarados: {', '.join(k['name'] for k in meta.get('kpis', []))}
- Muestra: {json.dumps(records[:2], ensure_ascii=False)}

VISUALIZACIONES:
{json.dumps(viz_details, ensure_ascii=False, indent=2)}
{notebooklm_context}

Responde ÚNICAMENTE con este JSON válido — sin markdown fences, sin texto extra:

{{
  "narrativa_principal": "<1 oración que capture el arco narrativo central>",
  "estructura": "<3_actos | ABT | piramide_invertida | kabob>",
  "jerarquia_visual": {json.dumps(viz_ids)},
  "titulos": {{{titulos_template}}},
  "call_to_action": "<acción concreta que debe tomar el ejecutivo>",
  "arco_audiencia": "<c_level | analista | comparativa>",
  "principios_aplicados": ["<principio 1>", "<principio 2>", "<principio 3>"],
  "summary": "<2-3 oraciones del enfoque narrativo elegido>"
}}"""

    try:
        with client.messages.stream(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            raw = stream.get_final_text().strip()
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        result = json.loads(raw)
        for k, v in DEFAULT_RESULT.items():
            result.setdefault(k, v)
        return result
    except Exception:
        return DEFAULT_RESULT
