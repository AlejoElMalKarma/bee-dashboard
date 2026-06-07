# BRAND CONFIGURATION
# El dashboard_architect lee este archivo antes de generar
# cualquier HTML. Todos los campos son opcionales excepto
# empresa e industria.

## Identidad
empresa: Kellogg's LATAM
industria: retail
estilo: bold

## Logo
# Opción A — URL pública (se descarga y embebe en base64)
logo_url: https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Kellogg%27s_2019_logo.svg/1200px-Kellogg%27s_2019_logo.svg.png

# Opción B — Path local relativo al proyecto
# logo_path: assets/logo.png

# Opción C — Dejar vacío para usar inicial de la empresa

## Colores
color_primario: "#C8102E"
color_secundario: "#FFB81C"
color_acento: "#C8102E"

# Si se dejan vacíos, se detectan automáticamente por industria:
# retail     → #FF6B35 + #1A1A2E
# fintech    → #0A2540 + #00D4AA
# salud      → #0066CC + #00B4D8
# logistica  → #FFD60A + #003566
# default    → #F5C842 + #07080F (Beesualization)

## Tipografía
# Si se deja vacío, se elige automáticamente por estilo:
# bold        → Bebas Neue + IBM Plex Mono
# moderno     → Syne + DM Mono
# conservador → DM Serif Display + IBM Plex Mono
# minimalista → Outfit + Chivo Mono
font_display: "Bebas Neue"
font_mono: "IBM Plex Mono"
font_body: "Outfit"

## Tono narrativo
# Define cómo el storytelling_architect redacta los títulos
# ejecutivo | técnico | comercial | motivacional
tono: comercial

## Personalización del header
tagline: "Panel de Rendimiento Comercial"
footer_text: "Kellogg's LATAM · Analytics powered by Beesualization"
