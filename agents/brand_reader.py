import base64
import re
import urllib.request
from pathlib import Path

# ── Industry palettes ──────────────────────────────────────────────────────────
_INDUSTRY_PALETTES = {
    "retail":    {"primario": "#FF6B35", "secundario": "#1A1A2E", "acento": "#FF6B35"},
    "fintech":   {"primario": "#0A2540", "secundario": "#00D4AA", "acento": "#00D4AA"},
    "salud":     {"primario": "#0066CC", "secundario": "#00B4D8", "acento": "#0066CC"},
    "logistica": {"primario": "#FFD60A", "secundario": "#003566", "acento": "#FFD60A"},
}
_DEFAULT_PALETTE = {"primario": "#F5C842", "secundario": "#07080F", "acento": "#F5C842"}

# ── Typography presets by style ────────────────────────────────────────────────
_STYLE_FONTS = {
    "bold":        {"display": "Bebas Neue",       "mono": "IBM Plex Mono", "body": "Outfit"},
    "moderno":     {"display": "Syne",             "mono": "DM Mono",       "body": "Cabinet Grotesk"},
    "conservador": {"display": "DM Serif Display", "mono": "IBM Plex Mono", "body": "Instrument Serif"},
    "minimalista": {"display": "Outfit",            "mono": "Chivo Mono",    "body": "Outfit"},
}
_DEFAULT_FONTS = _STYLE_FONTS["moderno"]

_DEFAULT_BRAND = {
    "empresa": "Beesualization",
    "industria": "default",
    "tagline": "Dashboard Pipeline",
    "footer_text": "Powered by Beesualization",
    "tono": "ejecutivo",
    "brand_detectado": False,
}


def _parse_brand_md(path: str) -> dict:
    """Parse BRAND.md key:value pairs, ignoring comments and blank lines."""
    fields: dict = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("##"):
                    continue
                if ":" in line:
                    key, _, val = line.partition(":")
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    # Strip inline comments (# comment after value)
                    val = re.sub(r"\s+#.*$", "", val).strip()
                    if val:
                        fields[key] = val
    except FileNotFoundError:
        pass
    return fields


def _svg_logo(inicial: str, color: str) -> str:
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'>"
        f"<rect width='48' height='48' rx='8' fill='{color}'/>"
        f"<text x='24' y='34' text-anchor='middle' font-family='sans-serif' "
        f"font-size='26' font-weight='bold' fill='white'>{inicial.upper()}</text>"
        f"</svg>"
    )


def _to_base64(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def _fetch_logo(url: str) -> str | None:
    """Download URL and return data-URI, or None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read()
        ct = r.headers.get_content_type() or "image/png"
        if "svg" in url.lower() or "svg" in ct:
            ct = "image/svg+xml"
        return _to_base64(raw, ct)
    except Exception:
        return None


def _load_local_logo(path: str, project_root: str) -> str | None:
    try:
        full = Path(project_root) / path
        raw = full.read_bytes()
        suffix = full.suffix.lower()
        mime = {"svg": "image/svg+xml", "png": "image/png",
                "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "webp": "image/webp"}.get(suffix.lstrip("."), "image/png")
        return _to_base64(raw, mime)
    except Exception:
        return None


def _google_fonts_url(display: str, mono: str, body: str) -> str:
    families = list({display, body, mono})
    params = "&family=".join(f.replace(" ", "+") + ":wght@400;700" for f in families)
    return f"https://fonts.googleapis.com/css2?family={params}&display=swap"


def run(brand_path: str = "BRAND.md", project_root: str | None = None) -> dict:
    """Read BRAND.md and return a brand config dict. Never raises."""
    if project_root is None:
        project_root = str(Path(__file__).parent.parent)

    full_path = str(Path(project_root) / brand_path)
    fields = _parse_brand_md(full_path)

    if not fields:
        brand = dict(_DEFAULT_BRAND)
        palette = _DEFAULT_PALETTE
        fonts = _DEFAULT_FONTS
    else:
        brand = {
            "empresa":    fields.get("empresa", "Beesualization"),
            "industria":  fields.get("industria", "default"),
            "tagline":    fields.get("tagline", "Dashboard Pipeline"),
            "footer_text": fields.get("footer_text", "Powered by Beesualization"),
            "tono":       fields.get("tono", "ejecutivo"),
            "brand_detectado": True,
        }
        industria = fields.get("industria", "default").lower()
        palette = _INDUSTRY_PALETTES.get(industria, _DEFAULT_PALETTE).copy()
        if fields.get("color_primario"):
            palette["primario"]   = fields["color_primario"]
        if fields.get("color_secundario"):
            palette["secundario"] = fields["color_secundario"]
        if fields.get("color_acento"):
            palette["acento"]     = fields["color_acento"]

        estilo = fields.get("estilo", "moderno").lower()
        fonts = _STYLE_FONTS.get(estilo, _DEFAULT_FONTS).copy()
        if fields.get("font_display"):
            fonts["display"] = fields["font_display"]
        if fields.get("font_mono"):
            fonts["mono"]    = fields["font_mono"]
        if fields.get("font_body"):
            fonts["body"]    = fields["font_body"]

    # ── Logo resolution ────────────────────────────────────────────────────────
    logo_b64: str | None = None
    if fields.get("logo_url"):
        logo_b64 = _fetch_logo(fields["logo_url"])
    if logo_b64 is None and fields.get("logo_path"):
        logo_b64 = _load_local_logo(fields["logo_path"], project_root)
    if logo_b64 is None:
        inicial = brand["empresa"][0] if brand["empresa"] else "B"
        svg = _svg_logo(inicial, palette["primario"])
        logo_b64 = _to_base64(svg.encode(), "image/svg+xml")

    is_svg = logo_b64.startswith("data:image/svg")

    # ── CSS variables ──────────────────────────────────────────────────────────
    css_variables = (
        f":root {{ "
        f"--brand-primary: {palette['primario']}; "
        f"--brand-secondary: {palette['secundario']}; "
        f"--brand-accent: {palette['acento']}; "
        f"--font-display: '{fonts['display']}', sans-serif; "
        f"--font-mono: '{fonts['mono']}', monospace; "
        f"--font-body: '{fonts['body']}', sans-serif; "
        f"}}"
    )

    # ── Google Fonts URL ───────────────────────────────────────────────────────
    google_fonts_url = _google_fonts_url(fonts["display"], fonts["mono"], fonts["body"])

    # ── Header HTML ───────────────────────────────────────────────────────────
    img_style = "width:48px;height:48px;object-fit:contain;" if not is_svg else "width:48px;height:48px;"
    header_html = (
        f'<header style="display:flex;align-items:center;gap:1rem;'
        f'padding:1rem 2rem;background:{palette["secundario"]};'
        f'border-bottom:3px solid {palette["primario"]};margin-bottom:1.5rem;">'
        f'<img src="{logo_b64}" alt="{brand["empresa"]} logo" style="{img_style}"/>'
        f'<div>'
        f'<div style="font-family:var(--font-display,sans-serif);font-size:1.4rem;'
        f'font-weight:700;color:{palette["primario"]};letter-spacing:1px;">'
        f'{brand["empresa"]}</div>'
        f'<div style="font-size:0.8rem;color:#ffffff99;">'
        f'{brand["tagline"]}</div>'
        f'</div>'
        f'</header>'
    )

    return {
        "empresa":          brand["empresa"],
        "tagline":          brand["tagline"],
        "footer_text":      brand["footer_text"],
        "tono":             brand["tono"],
        "industria":        brand["industria"],
        "logo_base64":      logo_b64,
        "paleta":           palette,
        "fuentes":          fonts,
        "css_variables":    css_variables,
        "google_fonts_url": google_fonts_url,
        "header_html":      header_html,
        "brand_detectado":  brand["brand_detectado"],
    }
