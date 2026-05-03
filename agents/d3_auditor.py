import json
import re
import anthropic

SYSTEM_PROMPT = """Eres un agente revisor especializado en DASHBOARDS y VISUALIZACIONES D3.js.
Tu función es auditar código y especificaciones de dashboards generados por IA antes de entregarlos a equipos corporativos.

## CRITERIOS DE REVISIÓN

### CRÍTICO (bloquear entrega) — cada uno resta 25 pts:
- Schema de datos incompleto o incompatible con la visualización propuesta
- Ejes sin labels o sin unidades definidas
- División por cero o valores null no manejados
- Gráfico tipo incorrecto para el dato (e.g. pie chart con >7 categorías)
- Código D3 con selectores rotos o referencias a elementos inexistentes
- Ausencia de estado vacío / loading state

### ADVERTENCIA (revisar con cliente) — cada una resta 10 pts:
- Paleta de colores no accesible (contraste insuficiente, WCAG AA mínimo 4.5:1 texto / 3:1 UI)
- Sin responsive breakpoints definidos
- Tooltips incompletos (faltan campos relevantes para el usuario de negocio)
- Escalas hardcodeadas en lugar de dinámicas derivadas del extent de los datos
- Sin manejo de datos extremos (outliers que rompen el layout)
- Filtros que no actualizan todos los charts conectados

### INFO (mejora recomendada) — cada uno resta 2 pts:
- Animaciones que pueden distraer en contexto corporativo (preferir transiciones ≤300ms)
- Falta de exportación a imagen/PDF
- Labels que se solapan en datasets grandes
- Sin indicador de última actualización

## SCORE Y VEREDICTO
- Inicio: 100 puntos
- Cada CRÍTICO: −25 pts | Cada ADVERTENCIA: −10 pts | Cada INFO: −2 pts | Mínimo: 0
- 80–100 sin ningún CRÍTICO → APROBADO
- 50–79 o cualquier ADVERTENCIA presente → REVISAR
- <50 o cualquier CRÍTICO presente → RECHAZADO"""


def run(html_code: str, viz_result: dict, client: anthropic.Anthropic) -> dict:
    viz_specs = json.dumps(
        [{"id": v["id"], "chart_type": v["chart_type"], "data_fields": v["data_fields"]}
         for v in viz_result.get("visualizations", [])],
        ensure_ascii=False
    )

    # truncate html for context if very long
    html_sample = html_code if len(html_code) <= 60000 else html_code[:60000] + "\n\n[... truncado por longitud ...]"

    user_msg = f"""Audita el siguiente dashboard D3.js generado por IA.

ESPECIFICACIÓN DE VISUALIZACIONES ESPERADAS:
{viz_specs}

CÓDIGO HTML COMPLETO DEL DASHBOARD:
{html_sample}

Audita el código como un sistema completo. Verifica:
1. Que cada visualización especificada está implementada
2. Que los selectores D3 apuntan a elementos que existen en el HTML
3. Correctitud de escalas, ejes, tooltips y manejo de datos
4. Accesibilidad (WCAG AA, daltonismo)
5. Manejo de estados vacíos/carga/error
6. Data-Ink Ratio y ausencia de chartjunk

Responde SOLO con este JSON válido — sin markdown, sin texto extra:

{{
  "score": <número 0-100>,
  "verdict": "<APROBADO|REVISAR|RECHAZADO>",
  "flags": [
    {{
      "type": "<CRÍTICO|ADVERTENCIA|INFO>",
      "area": "<componente o área específica>",
      "issue": "<descripción concisa y accionable del problema y cómo corregirlo>"
    }}
  ],
  "summary": "<1-2 oraciones con el diagnóstico general y la acción principal requerida>"
}}"""

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
