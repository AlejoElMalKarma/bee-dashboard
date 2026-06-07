"""
Generate D3 chart functions in batches of 2 and assemble them into the HTML shell.
Handles validation and retry of missing visualizations.
"""
import json
import re
import anthropic

CHARTS_SYSTEM_PROMPT = """You are an expert D3.js v7 engineer. Your task is to generate JavaScript chart functions that will be inserted into an existing HTML dashboard shell.

## YOUR OUTPUT
- Pure JavaScript only — NO HTML, NO CSS, NO <!DOCTYPE>, NO <script> tags
- One `function chartVizN(DATA)` per visualization requested
- Function naming rule: "VIZ-N" → chartVizN

## FUNCTION CONTRACT
```js
function chartVizN(DATA) {
  const records = (DATA.records || []).filter(d => /* relevant fields not null */);
  if (records.length === 0) {
    d3.select("#VIZ-N").append("p").style("color","#8B90A8").text("Sin datos disponibles");
    return;
  }
  // ... chart code ...
}
```

## AVAILABLE GLOBALS (defined in the shell — DO NOT redefine)
- `DATA` — passed as argument, also available as global
- `COLOR` — `{ positive, negative, neutral, accent }`
- `fmtC(v)` — currency format ($142K, $1.2M)
- `fmtP(v)` — percent format (+9.6%, -18.2%)
- `fmtS(v)` — string format
- `tooltip` — D3 selection of the shared tooltip div

## TOOLTIP PATTERN
```js
.on('mouseover', (event, d) => {
  tooltip.style('display','block')
    .html(`<strong>${fmtS(d.name)}</strong><br/>${fmtC(d.value)}`);
})
.on('mousemove', event => {
  tooltip.style('left', (event.pageX+12)+'px').style('top',(event.pageY-28)+'px');
})
.on('mouseout', () => tooltip.style('display','none'));
```

## MANDATORY RULES (apply to EVERY function)

### RESPONSIVE SVG
```js
const W = 600, H = 350;
const margin = {top:40, right:30, bottom:50, left:60};
const svg = d3.select("#VIZ-N")
  .append("svg")
  .attr("viewBox", `0 0 ${W} ${H}`)
  .attr("preserveAspectRatio","xMidYMid meet")
  .style("width","100%").style("height","auto")
  .attr("role","img").attr("aria-label","[chart description]");
```

### DYNAMIC SCALES (never hardcode domain values)
```js
const xScale = d3.scaleBand().domain(data.map(d => d.field)).range([margin.left, W-margin.right]).padding(0.2);
const yExtent = d3.extent(data, d => d.value);
const yScale = d3.scaleLinear().domain([0, yExtent[1]*1.1]).range([H-margin.bottom, margin.top]);
```

### AXIS LABELS WITH UNITS
```js
svg.append("text").attr("transform","rotate(-90)")
  .attr("y", margin.left - 45).attr("x", -(H/2))
  .attr("text-anchor","middle").attr("fill","#8B90A8").attr("font-size",11)
  .text("Ventas (USD)");
svg.append("text").attr("x", W/2).attr("y", H - 5)
  .attr("text-anchor","middle").attr("fill","#8B90A8").attr("font-size",11)
  .text("Período");
```

### VALUE LABELS ON BARS
```js
svg.selectAll(".val-label")
  .data(data).join("text").attr("class","val-label")
  .attr("x", d => xScale(d.key) + xScale.bandwidth()/2)
  .attr("y", d => yScale(d.value) - 4)
  .attr("text-anchor","middle").attr("font-size",10).attr("fill","#E8EAF2")
  .text(d => fmtC(d.value));
```

### LEGEND (for multi-series charts)
```js
const legend = svg.append("g").attr("transform", `translate(${margin.left}, ${H - 15})`);
[{label:"Serie A", color:COLOR.positive},{label:"Serie B",color:COLOR.neutral}].forEach((s,i) => {
  legend.append("rect").attr("x",i*120).attr("width",12).attr("height",12).attr("fill",s.color);
  legend.append("text").attr("x",i*120+16).attr("y",10).attr("font-size",10).attr("fill","#8B90A8").text(s.label);
});
```

### NULL/DIVISION SAFETY
```js
const ratio = (denominator !== 0 && denominator != null) ? numerator / denominator : 0;
```

### BULLET CHART SPECIFICS
- Background range bar: opacity 0.15
- Actual value bar: opacity 0.9
- Target line: stroke-width 3, opacity 1.0, label "Meta: $X.XM" BELOW the line
- Label: right of bar if above target, inside if below

Return ONLY the JavaScript function(s). No explanations, no markdown fences.

CRÍTICO: Debes incluir TODAS las funciones chartVizN(DATA) solicitadas, completamente implementadas.
Sin excepción. Sin placeholders. Sin funciones vacías. Si se piden 2 funciones, el output debe contener exactamente 2 funciones completas con código D3 real."""


def _viz_to_fn(viz_id: str) -> str:
    num = viz_id.split("-")[-1] if "-" in viz_id else viz_id
    return f"chartViz{num}"


def generate_batch(
    batch_vizs: list,
    sample_records: list,
    fields: list,
    css_vars: str,
    narrative_titles: dict,
    brand_paleta: dict,
    client: anthropic.Anthropic,
) -> str:
    """Generate D3 functions for a batch of visualizations. Returns JS code only."""
    viz_specs = "\n".join(
        f"- {v['id']} → function {_viz_to_fn(v['id'])}(DATA)\n"
        f"  Container: d3.select(\"#{v['id']}\")\n"
        f"  Chart type: {v.get('chart_type','')}\n"
        f"  Fields to use: {', '.join(v.get('data_fields', []))}\n"
        f"  Business question: {v.get('business_question','')}\n"
        f"  Narrative title: {narrative_titles.get(v['id'], v.get('name',''))}\n"
        f"  Justification: {v.get('justification','')}"
        for v in batch_vizs
    )

    color_positive = brand_paleta.get("teal", "#00C9A7")
    color_negative = brand_paleta.get("red",  "#FF4560")
    color_accent   = brand_paleta.get("acento", "#F5C842")

    user_msg = f"""Generate D3 v7 chart functions for these {len(batch_vizs)} visualization(s).

VISUALIZATIONS TO IMPLEMENT:
{viz_specs}

DATA STRUCTURE (sample — full DATA is already const in the HTML):
- Fields available: {', '.join(fields)}
- Sample records: {json.dumps(sample_records[:4], ensure_ascii=False)}

COLOR VALUES to use for const COLOR (already defined globally — use these values):
- COLOR.positive = "{color_positive}"
- COLOR.negative = "{color_negative}"
- COLOR.neutral  = "#6b7280"
- COLOR.accent   = "{color_accent}"

CSS VARIABLES available via var():
{css_vars}

REQUIREMENTS:
1. Each function: `function chartVizN(DATA)` targeting container `#VIZ-N`
2. Responsive SVG with viewBox (NO fixed width/height on SVG root)
3. Dynamic scales using d3.extent() / d3.max() — NEVER hardcoded domains
4. Axis labels with units on both axes where relevant
5. Value labels on every bar/point
6. Tooltip on every interactive element (use shared `tooltip` variable)
7. Legend for any multi-series chart
8. Guard: `if (!records || records.length === 0) return;`
9. Null/division-by-zero safety on every calculation
10. Apply BULLET CHART rules if chart_type contains "bullet"

Output ONLY the JavaScript function(s). No HTML, no CSS, no markdown."""

    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=8192,
        system=[{"type": "text", "text": CHARTS_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        js = stream.get_final_text().strip()

    # Strip accidental markdown fences
    js = re.sub(r"^```(?:javascript|js)?\n?", "", js)
    js = re.sub(r"\n?```$", "", js)
    return js.strip()


def validate_html(html: str, expected_viz: list) -> dict:
    issues = []
    for viz_id in expected_viz:
        if f'id="{viz_id}"' not in html:
            issues.append(f"{viz_id}: contenedor faltante")
            continue
        fn = _viz_to_fn(viz_id)
        if fn not in html:
            issues.append(f"{viz_id}: función {fn} no generada")
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "coverage": f"{len(expected_viz) - len(issues)}/{len(expected_viz)}",
    }


def _insert_js(html: str, js_code: str) -> str:
    """Insert JS code before DOMContentLoaded (or before </script> as fallback)."""
    marker = "document.addEventListener('DOMContentLoaded'"
    if marker in html:
        return html.replace(marker, js_code + "\n\n" + marker, 1)
    return html.replace("</script>", js_code + "\n</script>", 1)


def run(
    html_shell: str,
    viz_result: dict,
    data: dict,
    story_result: dict,
    design_result: dict,
    brand_result: dict,
    client: anthropic.Anthropic,
    progress_callback=None,  # callable(msg: str, pct: int) | None
) -> str:
    story_result  = story_result  or {}
    design_result = design_result or {}
    brand_result  = brand_result  or {}

    vizs           = viz_result.get("visualizations", [])
    records        = data.get("records", [])
    fields         = list(records[0].keys()) if records else []
    sample_records = records[:5]
    narrative_titles = story_result.get("titulos", {})
    css_vars       = brand_result.get("css_variables", "") or design_result.get("css_variables", "")
    brand_paleta   = brand_result.get("paleta", {})

    # Split vizs into batches of 2
    batches = [vizs[i:i+2] for i in range(0, len(vizs), 2)]
    n_batches = len(batches)

    all_js_parts: list[str] = []

    for idx, batch in enumerate(batches):
        ids_str = " + ".join(v["id"] for v in batch)
        if progress_callback:
            pct = 30 + int((idx / n_batches) * 55)   # 30% → 85%
            progress_callback(f"📊 Generando {ids_str}…", pct)

        js = generate_batch(
            batch_vizs=batch,
            sample_records=sample_records,
            fields=fields,
            css_vars=css_vars,
            narrative_titles=narrative_titles,
            brand_paleta=brand_paleta,
            client=client,
        )
        all_js_parts.append(js)

    # Assemble into shell
    combined_js = "\n\n".join(all_js_parts)
    if "/* VIZ_FUNCTIONS_PLACEHOLDER */" in html_shell:
        html = html_shell.replace("/* VIZ_FUNCTIONS_PLACEHOLDER */", combined_js)
    else:
        html = _insert_js(html_shell, combined_js)

    # Quick sanity check: if fewer chartViz functions than expected, force retry of all
    fn_count = html.count("function chartViz")
    if fn_count < len(vizs):
        if progress_callback:
            progress_callback(f"⚠ Solo {fn_count}/{len(vizs)} funciones generadas — reintentando…", 87)
        # Regenerate all in one shot with a stricter prompt
        for v in vizs:
            all_js_parts.append(f"// MISSING: {_viz_to_fn(v['id'])} — forcing regeneration")
        retry_all_js = generate_batch(
            batch_vizs=vizs,
            sample_records=sample_records,
            fields=fields,
            css_vars=css_vars,
            narrative_titles=narrative_titles,
            brand_paleta=brand_paleta,
            client=client,
        )
        # Replace combined_js with the fresh full generation
        if "/* VIZ_FUNCTIONS_PLACEHOLDER */" in html_shell:
            html = html_shell.replace("/* VIZ_FUNCTIONS_PLACEHOLDER */", retry_all_js)
        else:
            html = _insert_js(html_shell, retry_all_js)

    # Validate coverage
    viz_ids = [v["id"] for v in vizs]
    validation = validate_html(html, viz_ids)

    if not validation["valid"]:
        # Retry missing visualizations (max 2 passes)
        for _attempt in range(2):
            missing_ids = {iss.split(":")[0].strip() for iss in validation["issues"]
                          if "función" in iss}
            if not missing_ids:
                break
            missing_vizs = [v for v in vizs if v["id"] in missing_ids]
            if not missing_vizs:
                break

            if progress_callback:
                progress_callback(f"🔄 Reintentando {', '.join(missing_ids)}…", 88)

            # Retry in one batch regardless of size
            retry_js = generate_batch(
                batch_vizs=missing_vizs,
                sample_records=sample_records,
                fields=fields,
                css_vars=css_vars,
                narrative_titles=narrative_titles,
                brand_paleta=brand_paleta,
                client=client,
            )
            html = _insert_js(html, retry_js)
            validation = validate_html(html, viz_ids)
            if validation["valid"]:
                break

    if progress_callback:
        progress_callback("🔗 Ensamblando dashboard final…", 92)

    if not html.lower().rstrip().endswith("</html>"):
        html += "\n</body></html>" if "</body>" not in html.lower() else "\n</html>"

    return html, validation
