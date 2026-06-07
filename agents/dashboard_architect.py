"""
Orchestrates shell + charts agents to produce a complete dashboard HTML.
Public API: run() — same signature as before + optional progress_callback.
"""
import json
import anthropic

from agents.dashboard_architect_shell  import run as _run_shell
from agents.dashboard_architect_charts import run as _run_charts


def run(
    data: dict,
    viz_result: dict,
    cert_result: dict,
    client: anthropic.Anthropic,
    story_result: dict = None,
    design_result: dict = None,
    audit_result: dict = None,
    brand_result: dict = None,
    progress_callback=None,   # callable(msg: str, pct: int) | None
) -> str:
    story_result  = story_result  or {}
    design_result = design_result or {}
    audit_result  = audit_result  or {}
    brand_result  = brand_result  or {}

    # ── When the auditor rejected the previous build, delegate to the fix agent ──
    # (handled upstream in app.py via audit_fix_html; audit_result here is unused
    #  in normal flow but kept for backward compatibility)

    # ── Step 1: generate HTML shell ────────────────────────────────────────────
    if progress_callback:
        progress_callback("🏗 Generando estructura HTML…", 10)

    html_shell = _run_shell(
        data=data,
        viz_result=viz_result,
        cert_result=cert_result,
        story_result=story_result,
        design_result=design_result,
        brand_result=brand_result,
        client=client,
    )

    if progress_callback:
        progress_callback("✅ Estructura lista — iniciando gráficos…", 15)

    # ── Step 2: generate D3 chart functions in batches ────────────────────────
    html_final, validation = _run_charts(
        html_shell=html_shell,
        viz_result=viz_result,
        data=data,
        story_result=story_result,
        design_result=design_result,
        brand_result=brand_result,
        client=client,
        progress_callback=progress_callback,
    )

    if progress_callback:
        coverage = validation.get("coverage", "?")
        progress_callback(f"✅ Dashboard ensamblado — cobertura {coverage}", 100)

    return html_final
