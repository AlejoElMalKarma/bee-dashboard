"""
Generate the HTML shell: structure, CSS, DATA embedding, helpers, placeholder.
No D3 chart code — only the scaffold the charts agent will populate.
"""
import json
import re
import anthropic

SHELL_SYSTEM_PROMPT = """You are an expert HTML/CSS engineer. Your task is to generate the structural foundation of a dashboard — everything EXCEPT the D3 chart functions.

## YOUR OUTPUT CONTAINS
1. <!DOCTYPE html> + <head> with complete CSS + Google Fonts @import
2. <body>: brand header, main CSS-grid layout, one <div> container per visualization
3. <script> block with:
   a. D3.js v7 CDN script tag
   b. `const DATA = { metadata: ..., records: [...] };`  ← embedded JSON
   c. `const COLOR = { positive, negative, neutral, accent };`
   d. Format helpers: fmtC, fmtP, fmtS (exact code provided below)
   e. Tooltip div + setup code (exact code provided below)
   f. EXACTLY this comment on its own line: /* VIZ_FUNCTIONS_PLACEHOLDER */
   g. DOMContentLoaded block calling each chart function

## CONTAINER IDs — MANDATORY
Each visualization container MUST use the viz ID as the HTML id attribute:
  <div id="VIZ-1" class="chart-container"></div>
  <div id="VIZ-2" class="chart-container"></div>
  etc.

## FUNCTION CALL NAMES — MANDATORY
DOMContentLoaded calls: chartViz1(DATA), chartViz2(DATA), chartViz3(DATA) …
Function name rule: "VIZ-N" → chartVizN  (drop the hyphen, keep the number)

## REQUIRED HELPERS (copy exactly)
```js
const fmtC = v => {
  if (v == null) return 'N/A';
  const a = Math.abs(v);
  if (a >= 1e6) return '$' + (v/1e6).toFixed(1) + 'M';
  if (a >= 1e3) return '$' + (v/1e3).toFixed(0) + 'K';
  return '$' + v.toLocaleString();
};
const fmtP = v => v == null ? 'N/A' : (v >= 0 ? '+' : '') + v.toFixed(1) + '%';
const fmtS = v => v == null ? 'N/A' : String(v);
```

## REQUIRED TOOLTIP SETUP (copy exactly)
```js
const tooltip = d3.select('body').append('div')
  .attr('id','tooltip')
  .style('position','absolute').style('pointer-events','none')
  .style('display','none').style('background','var(--bg2,#0D0F1C)')
  .style('border','1px solid var(--border,#1E2235)').style('border-radius','6px')
  .style('padding','8px 12px').style('font-size','12px')
  .style('color','var(--text,#E8EAF2)').style('z-index','999');
```

## RULES
- Complete CSS grid layout (12 columns), responsive
- Brand header: logo img + company name + tagline
- Brand footer: footer text
- DOMContentLoaded must guard: `if (!DATA || !DATA.records || DATA.records.length === 0) return;`
- File must end with </body></html>
- DO NOT write any D3 chart drawing code — only the /* VIZ_FUNCTIONS_PLACEHOLDER */ comment
- The placeholder must appear between the tooltip setup and the DOMContentLoaded"""


def _viz_to_fn(viz_id: str) -> str:
    """'VIZ-3' → 'chartViz3'"""
    num = viz_id.split("-")[-1] if "-" in viz_id else viz_id
    return f"chartViz{num}"


def run(data: dict, viz_result: dict, cert_result: dict,
        story_result: dict, design_result: dict, brand_result: dict,
        client: anthropic.Anthropic) -> str:

    story_result  = story_result  or {}
    design_result = design_result or {}
    brand_result  = brand_result  or {}

    records = data.get("records", [])
    vizs    = viz_result.get("visualizations", [])
    layout  = viz_result.get("layout", "")
    fields  = list(records[0].keys()) if records else []

    # Viz containers + DOMContentLoaded call list for the prompt
    viz_containers = "\n".join(
        f'  <div id="{v["id"]}" class="chart-container" style="min-height:320px"></div>'
        for v in vizs
    )
    dom_calls = "\n    ".join(f"{_viz_to_fn(v['id'])}(DATA);" for v in vizs)

    # Brand info
    br_empresa  = brand_result.get("empresa", "Dashboard")
    br_tagline  = brand_result.get("tagline", "")
    br_footer   = brand_result.get("footer_text", "")
    br_logo     = brand_result.get("logo_base64", "")
    br_gf_url   = brand_result.get("google_fonts_url", "")
    br_css_vars = brand_result.get("css_variables", ":root{}")
    br_paleta   = brand_result.get("paleta", {})

    # Design overrides
    ds_css_vars = design_result.get("css_variables", "")
    ds_fonts    = design_result.get("fuentes", {})

    # Narrative summary
    narrativa = story_result.get("narrativa_principal", "")
    cta       = story_result.get("call_to_action", "")

    color_positive = br_paleta.get("teal", "#00C9A7")
    color_negative = br_paleta.get("red",  "#FF4560")
    color_neutral  = "#6b7280"
    color_accent   = br_paleta.get("acento", "#F5C842")

    user_msg = f"""Generate the HTML shell for this dashboard.

BRAND:
- Company: {br_empresa}
- Tagline: {br_tagline}
- Footer: {br_footer}
- Logo (embed as src): {br_logo[:60]}...
- Google Fonts URL: {br_gf_url}
- CSS Variables for :root: {br_css_vars}
{f"- Design override CSS vars: {ds_css_vars}" if ds_css_vars else ""}

COLORS FOR const COLOR object:
- positive (above target / good): {color_positive}
- negative (below target / alert): {color_negative}
- neutral (reference): {color_neutral}
- accent (KPI highlight): {color_accent}

NARRATIVE CONTEXT (use for section headings and h1):
- Main narrative: {narrativa}
- Call to action: {cta}

VISUALIZATIONS — create one container div per viz:
{chr(10).join(f"  {v['id']}: {v['name']} ({v['chart_type']})" for v in vizs)}

LAYOUT SUGGESTION: {layout}

CONTAINER DIVS TO INCLUDE IN BODY:
{viz_containers}

DOMCONTENTLOADED MUST CALL (in order):
    {dom_calls}

EMBEDDED DATA (include verbatim as `const DATA = ...;`):
{json.dumps(data, ensure_ascii=False)}

OUTPUT: Complete HTML file from <!DOCTYPE html> to </body></html>.
Include /* VIZ_FUNCTIONS_PLACEHOLDER */ exactly as shown.
Do NOT include any D3 chart drawing code."""

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=[{"type": "text", "text": SHELL_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        html = stream.get_final_text().strip()

    if html.startswith("```"):
        html = html.split("\n", 1)[1] if "\n" in html else html
        html = html.rsplit("```", 1)[0] if "```" in html else html
    html = html.strip()

    # Ensure placeholder exists (insert if model forgot it)
    if "/* VIZ_FUNCTIONS_PLACEHOLDER */" not in html:
        marker = "document.addEventListener('DOMContentLoaded'"
        if marker in html:
            html = html.replace(marker, "/* VIZ_FUNCTIONS_PLACEHOLDER */\n\n" + marker, 1)
        else:
            html = html.replace("</script>", "/* VIZ_FUNCTIONS_PLACEHOLDER */\n</script>", 1)

    # Ensure containers exist (insert if model forgot any)
    for v in vizs:
        if f'id="{v["id"]}"' not in html:
            html = html.replace(
                "/* VIZ_FUNCTIONS_PLACEHOLDER */",
                f'<!-- auto-injected --><div id="{v["id"]}" class="chart-container" style="min-height:300px"></div>\n/* VIZ_FUNCTIONS_PLACEHOLDER */',
            )

    if not html.lower().rstrip().endswith("</html>"):
        html += "\n</body></html>" if "</body>" not in html.lower() else "\n</html>"

    return html
