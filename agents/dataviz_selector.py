import json
import re
import anthropic

SYSTEM_PROMPT = """Eres un agente experto en selección y justificación de visualizaciones de datos. Tu trabajo es analizar la descripción de un conjunto de datos y un objetivo de negocio, y recomendar exactamente qué gráficos usar, por qué, y cuáles evitar. Tu razonamiento se basa en ciencia perceptual, no en estética.

Sigues el Modelo Anidado de Tamara Munzner: primero entiendes el dominio, luego abstraes los datos y tareas, y solo entonces propones la codificación visual.

## JERARQUÍA DE PERCEPCIÓN DE CLEVELAND & McGILL (mayor a menor precisión)
1. Posición en escala común → barras, scatter ✅ para datos críticos
2. Posición en escalas no alineadas → small multiples
3. Longitud / ángulo → barras apiladas, pie charts ⚠️
4. Área → burbujas, treemaps ⚠️ (el cerebro subestima áreas)
5. Volumen / curvatura → gráficos 3D ❌
6. Color / sombreado → mapas de calor ❌ solo para patrones globales

## TABLA DE SELECCIÓN DE GRÁFICO
| Objetivo | Gráfico correcto | Prohibido |
|---|---|---|
| Comparar categorías | Barras horizontales/columnas ordenadas | Pie, radar, gauge |
| Evolución temporal | Líneas | Barras para series continuas |
| Correlación 2 vars | Scatter plot | — |
| Correlación 3 vars | Burbujas (área = magnitud) | Escalar radio |
| Composición ≤5 grupos | Barras apiladas | Pie/donut >5 categorías |
| Distribución | Histograma / Box plot | — |
| Progreso hacia meta | Bullet chart / barra progreso | Gauge, speedometer |
| Geografía — magnitudes | Símbolos proporcionales | Coroplético para valores absolutos |
| Geografía — tasas | Coroplético | — |

## VARIABLES VISUALES DE BERTIN
- Tono (hue): solo para separar categorías nominales
- Luminancia (claro→oscuro): para datos ordinales/cuantitativos secuenciales
- Nunca codificar magnitudes cuantitativas con color cuando hay posición disponible

## RESTRICCIONES ABSOLUTAS
- No recomiendas pie charts con más de 5 categorías
- No recomiendas gauges ni speedometers
- No recomiendas gráficos 3D bajo ninguna circunstancia
- No justificas con "se ve mejor" — siempre con principio perceptual"""

OUTPUT_INSTRUCTIONS = """
Responde ÚNICAMENTE con este JSON válido — sin markdown fences, sin texto extra:

{
  "visualizations": [
    {
      "id": "VIZ-N",
      "name": "<nombre descriptivo>",
      "chart_type": "<tipo de gráfico>",
      "objective": "<comparar|evolucionar|correlacionar|componer|distribuir>",
      "data_fields": ["<campo1>", "<campo2>"],
      "perceptual_channel": "<posición|longitud|área|color>",
      "cleveland_mcgill_level": <1-6>,
      "justification": "<principio perceptual concreto>",
      "configuration": "<ordenamiento, escala, etiquetas clave>",
      "avoid": "<qué gráfico tentador evitar y por qué>",
      "business_question": "<pregunta de negocio que responde>"
    }
  ],
  "layout": "<descripción del layout sugerido con justificación patrón F/Z y Ley de Miller>",
  "summary": "<2 oraciones de resumen>"
}"""


def run(data: dict, cert_result: dict, client: anthropic.Anthropic) -> dict:
    records = data.get("records", [])
    fields = list(records[0].keys()) if records else []
    meta = data.get("metadata", {})

    numeric_fields = [f for f in fields if records and isinstance(records[0].get(f), (int, float))]
    categorical_fields = [f for f in fields if records and isinstance(records[0].get(f), str)]
    categories = {}
    for f in categorical_fields:
        categories[f] = list({r[f] for r in records})[:10]

    user_msg = f"""Analiza este dataset y recomienda las visualizaciones para un dashboard ejecutivo de ventas.

ESTRUCTURA DEL DATASET:
- Total registros: {len(records)}
- Campos numéricos: {', '.join(numeric_fields)}
- Campos categóricos: {', '.join(categorical_fields)}
- Categorías por campo: {json.dumps(categories, ensure_ascii=False)}
- KPIs disponibles: {', '.join(k['name'] for k in meta.get('kpis', []))}

CONTEXTO DE NEGOCIO:
- Dashboard de rendimiento de ventas
- Audiencia: ejecutivos y managers de ventas
- Pregunta principal: ¿Cómo está el equipo vs las metas y benchmarks?
- Decisiones: asignación de recursos, planes de mejora por rep/región

RESULTADO DE CERTIFICACIÓN:
- Veredicto: {cert_result.get('verdict', 'N/A')}
- Registros certificados: {cert_result.get('certified_count', len(records))}/{cert_result.get('record_count', len(records))}

MUESTRA DE DATOS:
{json.dumps(records[:3], indent=2, ensure_ascii=False)}

Genera entre 6 y 8 visualizaciones que cubran: KPIs globales (BANs), comparación por entidad, evolución temporal, distribución/correlación, y alertas.

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
