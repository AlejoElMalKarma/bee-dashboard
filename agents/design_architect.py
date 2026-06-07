import json
import re
import anthropic

SYSTEM_PROMPT = """Eres @design-architect, experto en identidad visual premium para dashboards ejecutivos. Traduces una narrativa de datos en un sistema de diseño cohesionado que refuerza el mensaje y maximiza la legibilidad.

## TIPOGRAFÍA — REGLAS ABSOLUTAS

NUNCA usar: Inter, Roboto, Arial, Helvetica, Space Grotesk, system-ui ni fuentes del sistema.

SIEMPRE elegir de:
- Display/Headers: Syne, DM Serif Display, Fraunces, Cabinet Grotesk, Instrument Serif
- Body: Cabinet Grotesk, Chivo Mono
- Números y datos: IBM Plex Mono o DM Mono (OBLIGATORIO para cifras)

Combinaciones válidas:
- dark_premium: Syne (display) + IBM Plex Mono (datos) + Cabinet Grotesk (body)
- editorial: DM Serif Display (display) + DM Mono (datos) + Instrument Serif (body)
- terminal_financiero: Chivo Mono (display) + IBM Plex Mono (datos) + Chivo Mono (body)

## PALETA DARK PREMIUM (base — ajustar matiz ±10% según narrativa)
--bg: #07080F | --bg2: #0D0F1C | --accent: #F5C842
--teal: #00C9A7 | --red: #FF4560 | --border: #1E2235

## ANIMACIONES OBLIGATORIAS
- fadeUp: `@keyframes fadeUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }`
- Stagger: `animation: fadeUp 0.4s ease both; animation-delay: calc(var(--i,0) * 80ms);`
- Hover transitions: max 200ms

## LAYOUT ASIMÉTRICO
- Un elemento grid-breaking que rompa la retícula regular
- Columna principal 8/12, sidebar 4/12
- Al menos un elemento full-width para crear ritmo
- La asimetría establece jerarquía visual

## ALINEACIÓN CON NARRATIVA
- Alerta/crisis → acento rojo prominente, tipografía condensada
- Éxito/crecimiento → acento dorado/teal, tipografía amplia
- Comparativa → layout paralelo con contraste claro
- El call_to_action debe ser el elemento visualmente más prominente"""

DEFAULT_RESULT = {
    "tema_visual": "dark_premium",
    "fuentes": {
        "display": "Syne",
        "mono": "IBM Plex Mono",
        "body": "Cabinet Grotesk",
    },
    "paleta": {
        "bg": "#07080F",
        "bg2": "#0D0F1C",
        "accent": "#F5C842",
        "teal": "#00C9A7",
        "red": "#FF4560",
        "border": "#1E2235",
    },
    "css_variables": (
        ":root { --bg: #07080F; --bg2: #0D0F1C; --accent: #F5C842; "
        "--teal: #00C9A7; --red: #FF4560; --border: #1E2235; "
        "--font-display: 'Syne', sans-serif; "
        "--font-mono: 'IBM Plex Mono', monospace; "
        "--font-body: 'Cabinet Grotesk', sans-serif; }"
    ),
    "animaciones": ["fadeUp", "stagger-delay", "hover-scale"],
    "grid_layout": "Grid asimétrico 8/4, header full-width grid-breaking, cards con stagger animation",
    "justificacion": (
        "Paleta dark premium maximiza contraste y concentra atención en los datos. "
        "Syne proyecta autoridad técnica en títulos. IBM Plex Mono garantiza alineación perfecta de cifras. "
        "Asimetría 8/4 establece jerarquía visual entre insight principal y métricas secundarias."
    ),
    "summary": "Identidad dark premium con tipografía Syne y acento dorado que comunica autoridad ejecutiva y precisión analítica.",
}


def run(story_result: dict, viz_result: dict, cert_result: dict, client: anthropic.Anthropic) -> dict:
    vizs = viz_result.get("visualizations", [])
    narrativa = story_result.get("narrativa_principal", "")
    estructura = story_result.get("estructura", "piramide_invertida")
    call_to_action = story_result.get("call_to_action", "")
    arco = story_result.get("arco_audiencia", "c_level")

    user_msg = f"""Define el sistema de diseño visual para este dashboard ejecutivo.

NARRATIVA A REFORZAR:
- Narrativa principal: {narrativa}
- Estructura: {estructura}
- Audiencia: {arco}
- Call to action: {call_to_action}

VISUALIZACIONES ({len(vizs)} gráficos):
{', '.join(v.get('name', '') for v in vizs)}

CONTEXTO DE DATOS:
- Veredicto de certificación: {cert_result.get('verdict', 'N/A')}
- Issues detectados: {len(cert_result.get('issues', []))}

Elige el sistema que mejor refuerce la narrativa. Si hay issues críticos o la narrativa es de alerta, favorece terminal_financiero. Si es de éxito/crecimiento, usa dark_premium con acento dorado.

Responde ÚNICAMENTE con este JSON válido — sin markdown fences, sin texto extra:

{{
  "tema_visual": "<dark_premium | editorial | terminal_financiero>",
  "fuentes": {{
    "display": "<nombre fuente display>",
    "mono": "<nombre fuente mono>",
    "body": "<nombre fuente body>"
  }},
  "paleta": {{
    "bg": "#...", "bg2": "#...", "accent": "#...",
    "teal": "#...", "red": "#...", "border": "#..."
  }},
  "css_variables": "<:root {{ --bg:#...; --bg2:#...; --accent:#...; --teal:#...; --red:#...; --border:#...; --font-display:'...'; --font-mono:'...'; --font-body:'...'; }}>",
  "animaciones": ["fadeUp", "stagger-delay"],
  "grid_layout": "<descripción del layout y elemento grid-breaking>",
  "justificacion": "<3-4 líneas explicando decisiones de tipografía, color y layout en relación a la narrativa>",
  "summary": "<1 oración del concepto visual>"
}}"""

    try:
        with client.messages.stream(
            model="claude-sonnet-4-5",
            max_tokens=2048,
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
