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
- <80 o cualquier CRÍTICO presente → RECHAZADO"""


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

    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        raw = stream.get_final_text().strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


FIX_SYSTEM_PROMPT = """Eres un experto en D3.js y HTML. Tu única tarea es recibir un dashboard HTML con bugs CRÍTICOS ya identificados y devolver el HTML completo corregido.

## REGLAS ABSOLUTAS
1. Corrige TODOS los issues CRÍTICOS listados. Son bloqueantes — sin excepción.
2. No cambies nada que no esté en la lista — preserva diseño, colores, fuentes y estructura.
3. Devuelve el archivo HTML COMPLETO (<!DOCTYPE html> ... </body></html>). NUNCA truncar.
4. Si el HTML es largo, reduce verbosidad de comentarios o CSS decorativo, pero incluye TODOS los gráficos.

## PATRONES DE CORRECCIÓN REQUERIDOS

### Visualización ausente o truncada
Si el auditor dice que falta una visualización:
- Busca el `<div id="viz-N">` en el HTML y añade su función JS completa al bloque de inicialización.
- Si el código estaba truncado, completa el cierre de la función y el bloque DOMContentLoaded.

### División por cero
```js
if (!arr || arr.length === 0) { container.innerHTML = "<p>Sin datos</p>"; return; }
const val = divisor !== 0 ? numerador / divisor : 0;
```

### Escala hardcodeada
```js
// MAL: .domain([0, 100])
// BIEN:
const ext = d3.extent(data, d => d.campo);
scale.domain([ext[0] * 0.9, ext[1] * 1.1]);
```

### Eje sin unidad/label
```js
svg.append("text")
  .attr("transform", "rotate(-90)")
  .attr("y", -margin.left + 12).attr("x", -height / 2)
  .attr("text-anchor", "middle").text("Ventas (USD)");
```

### Loading state ausente
```html
<div id="loading" style="text-align:center;padding:2rem">Cargando...</div>
<script>document.addEventListener('DOMContentLoaded',()=>{ document.getElementById('loading').style.display='none'; });</script>
```

### Selector roto
Verifica que `d3.select("#id")` tenga el `<div id="id">` correspondiente en el HTML."""


def fix_html(html_code: str, flags: list, client: anthropic.Anthropic) -> str:
    """Aplica correcciones quirúrgicas al HTML existente — solo issues CRÍTICOS, con opus+32K."""
    # Focus only on CRITICOs since those block the score
    critical = [f for f in flags if f.get("type") in ("CRÍTICO", "CRITICAL")]
    all_flags = critical if critical else flags  # fallback to all if no CRITICOs

    issues_numbered = "\n".join(
        f"{i+1}. {f.get('area','')}: {f.get('issue','')}"
        for i, f in enumerate(all_flags)
    )

    user_msg = f"""El dashboard HTML tiene {len(all_flags)} issues CRÍTICOS que debes corregir uno por uno.

ISSUES CRÍTICOS A CORREGIR (TODOS obligatorios para aprobar la auditoría):
{issues_numbered}

HTML ACTUAL DEL DASHBOARD:
{html_code}

Instrucciones:
- Corrige cada issue listado aplicando los patrones de corrección del system prompt.
- NO cambies nada que no esté en la lista.
- El archivo DEBE terminar exactamente con </body></html>.
- Si el código original estaba truncado (falta </body></html>), completa el código faltante.

Devuelve SOLO el HTML completo corregido. Sin explicaciones."""

    with client.messages.stream(
        model="claude-opus-4-5",
        max_tokens=32000,
        system=[{"type": "text", "text": FIX_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        html = stream.get_final_text().strip()

    if html.startswith("```"):
        html = html.split("\n", 1)[1] if "\n" in html else html
        html = html.rsplit("```", 1)[0] if "```" in html else html
    html = html.strip()

    # Truncation recovery: if output was cut off, close the document
    if not html.lower().rstrip().endswith("</html>"):
        if "</body>" not in html.lower():
            html += "\n</body></html>"
        else:
            html += "\n</html>"
    return html
