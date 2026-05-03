# Especificaciones de Visualización — Dashboard de Ventas 2025
> Razonamiento basado en: Cleveland & McGill (1984), Munzner (2014), Bertin (1967), Tufte (1983)
> Dataset: 25 registros | 5 representantes | 5 regiones | 12 meses | 2 KPIs

---

## VIZ-1 — BANs de Estado Global del Equipo

**Objetivo analítico:** Componer (resumen ejecutivo de estado actual)

**Datos usados:** Agregados del dataset completo:
- `sum(revenue)` = $3,287,000
- `sum(target)` = $3,110,000
- `mean(kpi_meta)` = 98.9%
- `mean(kpi_conversion)` = 26.3%
- Estado global del equipo: AMARILLO
- Conteos: [G]=13, [A]=6, [R]=4 de 25 registros

**Tipo de gráfico:** Big Number Cards (BANs) — 4 tarjetas en fila horizontal + 1 badge de estado global

**Canal perceptual:** Posición (nivel 1 Cleveland & McGill) para la lectura izquierda-derecha, color categórico (nivel 6) como canal redundante de estado semaforo — el color nunca es el único canal

**Justificación:**
Los BANs son el patrón correcto para valores escalares sin dimensión comparativa. El usuario ejecutivo necesita absorber el estado en menos de 500ms (Ware, 2004). Un gráfico de barra para un único valor agrega carga cognitiva sin información adicional. El badge de estado global (AMARILLO) combina texto + color para doble redundancia perceptual — elimina la ambigüedad que tendría el color solo en pantallas con calibración imperfecta o para usuarios con daltonismo.

**Configuración clave:**
- BAN 1: Revenue Total `$3,287,000` | sub-etiqueta: `+$177K vs target (+5.7%)` | color de sub-etiqueta: verde
- BAN 2: KPI Meta Promedio `98.9%` | sub-etiqueta: `benchmark: 100%` | color del número: #F59E0B (amarillo, porque no alcanza el 100%)
- BAN 3: KPI Conversión Promedio `26.3%` | sub-etiqueta: `benchmark: 25%` | color del número: #10B981 (verde)
- BAN 4: Registros Críticos `4 / 25` | sub-etiqueta: `en rojo` | color del número: #EF4444 (rojo)
- Badge central: texto `ESTADO: AMARILLO` + fondo #F59E0B + icono de advertencia triangular
- Tipografía: número principal ≥ 36px, sub-etiqueta ≤ 14px
- Sin bordes decorativos, sin sombras, sin gradientes

**Prohibido aquí:**
- Gauge/velocímetro: el canal ángulo está en nivel 4 de Cleveland & McGill (inferior a posición). Para un único valor escalar contra benchmark, el gauge agrega área no codificada que el ojo interpreta como relevante.
- Donut chart para mostrar porcentaje: el ángulo de un arco es menos preciso que leer el número directamente.

**Datos de entrada para D3:**
```json
{
  "revenue_total": 3287000,
  "target_total": 3110000,
  "kpi_meta_mean": 98.9,
  "kpi_conversion_mean": 26.3,
  "kpi_meta_benchmark": 100,
  "kpi_conversion_benchmark": 25,
  "records_green": 13,
  "records_yellow": 6,
  "records_red": 4,
  "records_total": 25,
  "team_status": "yellow"
}
```

---

## VIZ-2 — Rendimiento por Representante (Doble KPI)

**Objetivo analítico:** Comparar (5 representantes en 2 dimensiones simultáneas)

**Datos usados:** Agregados por `rep_name`:
- `mean(kpi_meta)` por representante
- `mean(kpi_conversion)` por representante
- `kpi_meta_status_general` (verde/amarillo/rojo)
- `revenue_total` por representante

**Tipo de gráfico:** Dot Plot horizontal con dos canales (Diverging Dot Plot) — una fila por representante, dos puntos por fila: uno para kpi_meta (eje superior) y uno para kpi_conversion (eje inferior), ordenados por kpi_meta descendente

**Canal perceptual:** Posición a lo largo de un eje común (nivel 1 Cleveland & McGill) — el canal más preciso para comparación cuantitativa. Color categórico (nivel 6) como canal redundante de estado — no como canal primario.

**Justificación:**
Con 5 categorías nominales y 2 valores cuantitativos por categoría, el dot plot con ejes compartidos permite al ojo hacer comparaciones directas: la alineación vertical entre los dos puntos de un mismo representante revela inmediatamente si los dos KPIs van en la misma dirección o divergen. Bertin (1967) clasifica la posición como la variable visual de mayor selectividad y asociatividad. El gráfico de barras agrupadas con 2 barras por representante es válido, pero el dot plot reduce el chartjunk al eliminar la superficie de barra que no codifica información adicional (Tufte, 1983).

Las líneas de referencia verticales (benchmarks 100% y 25%) son el eje de decisión — el usuario no debe calcular mentalmente si un punto supera o no el benchmark.

**Configuración clave:**
- Ordenamiento: descendente por `kpi_meta` promedio (Laura Gómez arriba)
- Eje X (kpi_meta): rango [40%, 130%], línea de referencia roja punteada en 80%, línea verde sólida en 100%
- Eje X (kpi_conversion): rango [10%, 40%], línea de referencia roja punteada en 15%, línea verde sólida en 25%
- Color del punto: verde (#10B981) / amarillo (#F59E0B) / rojo (#EF4444) según `kpi_meta_status_general`
- Etiqueta directa del valor junto a cada punto (no leyenda flotante)
- Tamaño del punto proporcional a `revenue_total` (canal área como tercer canal, no crítico)
- Separación visual explícita entre los dos sub-gráficos (small multiples horizontales)

**Prohibido aquí:**
- Gráfico de barras apiladas: la comparación de partes acumuladas no es la tarea aquí; la tarea es comparar valores absolutos de KPIs contra un benchmark.
- Radar/spider chart: Bertin y Munzner coinciden en que los ejes radiales no comparten una escala común legible; el ojo compara áreas de polígono (canal área, nivel 4) en lugar de posición (nivel 1). Con solo 2 dimensiones, el radar es completamente innecesario.

**Datos de entrada para D3:**
```json
[
  { "rep_name": "Laura Gómez",   "kpi_meta_mean": 117.2, "kpi_conversion_mean": 33.5, "revenue_total": 908000,  "status": "green"  },
  { "rep_name": "Ana Martínez",  "kpi_meta_mean": 100.5, "kpi_conversion_mean": 27.0, "revenue_total": 807000,  "status": "green"  },
  { "rep_name": "Miguel Torres", "kpi_meta_mean": 96.4,  "kpi_conversion_mean": 26.0, "revenue_total": 551000,  "status": "yellow" },
  { "rep_name": "Sofía Herrera", "kpi_meta_mean": 91.7,  "kpi_conversion_mean": 21.1, "revenue_total": 423000,  "status": "yellow" },
  { "rep_name": "Carlos Ruiz",   "kpi_meta_mean": 89.0,  "kpi_conversion_mean": 23.5, "revenue_total": 598000,  "status": "yellow" }
]
```

---

## VIZ-3 — Comparación por Región (Revenue vs Target)

**Objetivo analítico:** Comparar (5 regiones, 2 valores cuantitativos superpuestos)

**Datos usados:** Agregados por `region`:
- `sum(revenue)` por región
- `sum(target)` por región
- `mean(kpi_meta)` por región
- `kpi_meta_status_general` por región

**Tipo de gráfico:** Bar Chart horizontal con barras superpuestas (Bullet Chart simplificado) — una barra de revenue real sobre una marca lineal de target, una fila por región

**Canal perceptual:** Longitud a lo largo de un eje común (nivel 2 Cleveland & McGill). La diferencia revenue-target se percibe como la distancia entre el extremo de la barra y la marca del target — una operación perceptual directa sin cálculo cognitivo.

**Justificación:**
La tarea es comparar magnitudes absolutas de revenue entre regiones Y simultáneamente ver si cada región supera su target. El bullet chart de Few (2006) resuelve esta doble comparación en un único canal espacial sin duplicar el área visual. Ordenar las regiones por `sum(revenue)` descendente (Centro arriba) aprovecha el efecto de primacía: el usuario lee el ranking inmediatamente. La dirección horizontal es correcta porque los nombres de región son etiquetas largas que en barras verticales se truncan o rotan.

**Configuración clave:**
- Ordenamiento: descendente por `sum(revenue)` (Centro: $908K arriba, Oeste: $423K abajo)
- Barra principal: revenue real, color determinado por estado semáforo de kpi_meta
  - Verde: #10B981 | Amarillo: #F59E0B | Rojo: #EF4444
- Marca de target: línea vertical fina negra (#1F2937) sobre la barra
- Eje X: desde 0 hasta $1,000,000 (sin truncar — Lie Factor = 1.0)
- Etiquetas directas: revenue ($xxx K) y target ($xxx K) al final de cada barra
- Sub-etiqueta del KPI meta promedio junto al nombre de región
- Sin leyenda flotante: el color se explica con una nota en el título del gráfico

**Prohibido aquí:**
- Pie chart de participación de revenue por región: la tarea no es ver proporciones del total, sino comparar regiones entre sí y contra sus targets individuales. El ángulo (nivel 4) es inferior a la longitud (nivel 2) para esta tarea.
- Mapa coroplético: las 5 regiones son etiquetas nominales (Norte/Sur/Este/Oeste/Centro), no unidades geográficas con coordenadas definidas en el dataset. Introducir un mapa implicaría una proyección que el dataset no valida.

**Datos de entrada para D3:**
```json
[
  { "region": "Centro", "revenue": 908000, "target": 775000, "kpi_meta_mean": 117.2, "status": "green"  },
  { "region": "Norte",  "revenue": 807000, "target": 670000, "kpi_meta_mean": 100.5, "status": "green"  },
  { "region": "Sur",    "revenue": 598000, "target": 635000, "kpi_meta_mean": 89.0,  "status": "yellow" },
  { "region": "Este",   "revenue": 551000, "target": 570000, "kpi_meta_mean": 96.4,  "status": "yellow" },
  { "region": "Oeste",  "revenue": 423000, "target": 460000, "kpi_meta_mean": 91.7,  "status": "yellow" }
]
```
> Nota: los targets por región se calculan como `sum(target)` de todos los registros de esa región en el dataset.

---

## VIZ-4 — Evolución Trimestral del KPI de Meta

**Objetivo analítico:** Evolucionar (tendencia temporal de KPI de meta promedio a lo largo de 4 trimestres)

**Datos usados:** Agregados por `quarter`:
- `mean(kpi_meta)` por trimestre
- `mean(kpi_conversion)` por trimestre
- Conteo de registros [G]/[A]/[R] por trimestre

**Tipo de gráfico:** Line Chart de doble eje con marcadores de punto — línea primaria para kpi_meta (eje Y izquierdo), línea secundaria para kpi_conversion (eje Y derecho), 4 puntos en eje X ordinal (Q1, Q2, Q3, Q4)

**Canal perceptual:** Posición vertical de cada punto a lo largo de un eje cuantitativo (nivel 1) + pendiente de la línea que conecta puntos consecutivos como canal de cambio — la inclinación de la línea codifica la tasa de cambio directamente en la retina (Mackinlay, 1986). El eje X es ordinal (Q1–Q4), no continuo, por lo que los 4 puntos están igualmente espaciados.

**Justificación:**
Con solo 4 puntos temporales (trimestres), un line chart con marcadores es el gráfico correcto: la línea conecta explícitamente los puntos en el tiempo para mostrar tendencia. Un bar chart de 4 trimestres mostraría los mismos valores pero ocultaría la narrativa de la trayectoria ascendente Q1→Q4. La narrativa clave del dataset es que Q3 es el mejor trimestre (104.0% meta) — esta es exactamente la historia que una pendiente positiva Q2→Q3 comunica en milisegundos.

El doble eje es justificable aquí porque las dos métricas (kpi_meta en rango 95–104%, kpi_conversion en rango 24–30%) son conceptualmente comparables como tasas porcentuales pero tienen benchmarks distintos — mantenerlas en el mismo eje distorsionaría la percepción de variación relativa de cada una.

**Configuración clave:**
- Eje X: Q1 | Q2 | Q3 | Q4 (equidistantes, etiquetado con nombre de meses: Ene-Mar | Abr-Jun | Jul-Sep | Oct-Dic)
- Eje Y izquierdo (kpi_meta): rango [80%, 115%], línea de referencia horizontal en 100% (benchmark), color #3B82F6 (azul)
- Eje Y derecho (kpi_conversion): rango [20%, 35%], línea de referencia horizontal en 25% (benchmark), color #8B5CF6 (violeta)
- Marcadores de punto: círculo relleno, tamaño proporcional al número de registros del trimestre (Q1=8, Q2=7, Q3=6, Q4=4)
- Etiqueta directa del valor encima/debajo de cada punto
- Anotación de texto en Q3: "Mejor trimestre" (sin flecha decorativa)
- Zona de fondo: franja verde semitransparente donde kpi_meta >= 100%, franja roja donde < 80%
- Sin gridlines secundarias, solo línea de referencia del benchmark

**Prohibido aquí:**
- Área rellena (area chart): solo es superior al line chart cuando la magnitud acumulada importa. Aquí la tarea es ver la tendencia de un promedio, no la suma — el área rellena desde cero crearía una ilusión de que Q3 tiene 104% "de algo" acumulado.
- Gráfico de barras para tiempo: las barras en el tiempo ocultan la continuidad de la tendencia; el ojo no puede leer pendientes entre barras con la misma facilidad que entre puntos conectados.

**Datos de entrada para D3:**
```json
[
  { "quarter": "Q1", "label": "Ene–Mar", "records": 8, "kpi_meta_mean": 96.1,  "kpi_conversion_mean": 24.4, "green": 3, "yellow": 3, "red": 1 },
  { "quarter": "Q2", "label": "Abr–Jun", "records": 7, "kpi_meta_mean": 95.4,  "kpi_conversion_mean": 25.2, "green": 3, "yellow": 2, "red": 1 },
  { "quarter": "Q3", "label": "Jul–Sep", "records": 6, "kpi_meta_mean": 104.0, "kpi_conversion_mean": 29.5, "green": 5, "yellow": 1, "red": 1 },
  { "quarter": "Q4", "label": "Oct–Dic", "records": 4, "kpi_meta_mean": 102.8, "kpi_conversion_mean": 27.5, "green": 4, "yellow": 0, "red": 1 }
]
```

---

## VIZ-5 — Semáforo de Registros por Representante × Mes

**Objetivo analítico:** Componer (distribución de estado semáforo en el espacio representante × tiempo)

**Datos usados:** Todos los 25 registros individuales:
- `rep_name` (nominal, 5 categorías)
- `period` (2025-01 a 2025-12, ordinal, 12 meses)
- `kpi_meta_status` (nominal: green/yellow/red)
- `kpi_conversion_status` (nominal: green/yellow/red)
- `kpi_meta` (cuantitativo, para tooltip)
- `kpi_conversion` (cuantitativo, para tooltip)

**Tipo de gráfico:** Heatmap de semáforo con redundancia visual — matriz 5 representantes × 12 meses, cada celda usa 3 canales simultáneos: (1) color de fondo por kpi_meta_status, (2) icono/símbolo interior por kpi_conversion_status, (3) número del KPI meta en la celda

**Canal perceptual:**
- Canal primario: color categórico (nivel 6 Cleveland & McGill) — verde/amarillo/rojo para kpi_meta
- Canal secundario redundante: símbolo/forma (nivel 7) — ícono check/warning/X para kpi_conversion_status
- Canal terciario: posición en la matriz (nivel 1) — qué representante en qué mes
La redundancia triple garantiza decodificación correcta bajo condiciones de daltonismo (8% de hombres) y pantallas de baja calidad.

**Justificación:**
La tarea es localizar patrones espaciales en un espacio bidimensional de categorías: ¿qué representante tuvo problemas en qué mes? ¿Hay meses recurrentemente malos? La matriz (heatmap) es el único gráfico que permite ver simultáneamente las dos dimensiones ordinales/nominales sin agregar información. Bertin (1967) denomina esto "implantatión en superficie" — la posición en la cuadrícula codifica dos variables sin sacrificar ninguna.

Las celdas vacías (meses donde el representante no tiene registro) se muestran en gris claro con texto "N/A" — la ausencia de dato es información explícita, no silencio visual ambiguo.

**Configuración clave:**
- Filas: representantes ordenados por kpi_meta_mean descendente (Laura Gómez arriba)
- Columnas: meses en orden cronológico (Ene a Dic), agrupados visualmente por trimestre con separador sutil
- Color de celda (kpi_meta_status):
  - Verde: #DCFCE7 (fondo suave, no saturado — el texto interior debe ser legible)
  - Amarillo: #FEF3C7
  - Rojo: #FEE2E2
- Símbolo interior (kpi_conversion_status):
  - Verde: ✓ en #15803D
  - Amarillo: ▲ en #B45309
  - Rojo: ✕ en #B91C1C
- Número de kpi_meta en la celda, tamaño 11px, centrado
- Celda vacía: fondo #F3F4F6, texto "—"
- Tooltip al hover: todos los campos del registro (revenue, target, leads, deals, ambos KPIs)
- Sin leyenda flotante: fila de leyenda visual encima de la matriz (muestra las 3 celdas de ejemplo)

**Prohibido aquí:**
- Gráfico de burbujas para mostrar estado: las burbujas requieren decodificar área (nivel 4) y color simultáneamente, sin el beneficio de la posición en cuadrícula para encontrar combinaciones representante×mes.
- 25 pie charts individuales (uno por registro): los ángulos de los sectores son el canal menos preciso para comparación, y multiplicar 25 pie charts destruye la posibilidad de comparación entre ellos.

**Datos de entrada para D3:**
```json
// Todos los 25 registros con estas columnas:
// { "rep_name", "period", "kpi_meta", "kpi_meta_status", "kpi_conversion", "kpi_conversion_status", "revenue", "target", "leads", "deals_closed" }
// + generar una matriz completa 5×12 rellenando con null los meses sin registro
```

---

## VIZ-6 — Scatter Plot: Leads vs Conversión (Eficiencia comercial)

**Objetivo analítico:** Correlacionar (¿genera más leads = más conversión, o hay representantes que convierten mejor con menos leads?)

**Datos usados:** Los 25 registros individuales:
- `leads` (cuantitativo continuo, eje X): rango 45–110
- `kpi_conversion` (cuantitativo continuo, eje Y): rango 13.3%–38.2%
- `revenue` (cuantitativo, canal tamaño de punto): rango $67K–$207K
- `rep_name` (nominal, canal color/forma del punto): 5 categorías
- `kpi_meta_status` (nominal, canal contorno del punto): para identificar críticos

**Tipo de gráfico:** Scatter Plot (gráfico de dispersión) con codificación triple — posición XY + tamaño de punto + color por representante

**Canal perceptual:**
- Posición X: número de leads (nivel 1 Cleveland & McGill)
- Posición Y: tasa de conversión % (nivel 1)
- Área del punto: revenue (nivel 4) — canal secundario, no crítico para la tarea principal
- Color/tono: representante (nivel 6) — 5 colores cualitativos distintos

**Justificación:**
Este gráfico expone el insight no obvio del dataset: el número de leads NO determina la tasa de conversión. REC-011 (Miguel Torres, 45 leads, 13.3% conversión) está en el cuadrante inferior-izquierdo, pero REC-007 (Laura Gómez, 102 leads, 37.3% conversión) está en el superior-derecho — hay una relación positiva débil, pero los outliers revelan que la calidad del lead o la habilidad de cierre varía significativamente entre representantes.

La correlación de Pearson estimada visualmente sugiere r ≈ +0.6, pero con varianza alta — eso es una historia de gestión: algunos representantes son eficientes con pocos leads, otros generan volumen sin convertir proporcionalmente.

Un line chart o bar chart no puede mostrar esta relación bivariada. El scatter plot es el único gráfico que codifica simultáneamente dos variables cuantitativas continuas usando el canal más preciso disponible (posición).

**Configuración clave:**
- Eje X (leads): desde 0 hasta 120, escala lineal, gridlines cada 20 leads
- Eje Y (kpi_conversion): desde 0% hasta 45%, línea de referencia horizontal en 25% (benchmark verde) y en 15% (umbral rojo)
- Línea de regresión simple (OLS) superpuesta — pendiente positiva confirma correlación, distancia de puntos a la línea revela outliers
- Color por representante (5 colores cualitativos accesibles): usar paleta Okabe-Ito para seguridad ante daltonismo
- Contorno de punto: borde rojo (#B91C1C) de 2px para los 4 registros críticos (kpi_meta_status = "red")
- Etiqueta directa de ID del registro solo para los 4 críticos (no etiquetar los 21 restantes — evitar crowding)
- Tamaño de punto: radio entre 6px (min revenue $67K) y 18px (max revenue $207K), escala de raíz cuadrada para Lie Factor = 1.0 en área
- Leyenda de color: pequeña, integrada en el margen derecho del gráfico (no flotante)

**Prohibido aquí:**
- Line chart conectando los puntos por representante: la tarea es correlación, no evolución temporal. Conectar los puntos implicaría una ordenación secuencial que no existe en el eje X (leads no es tiempo).
- Gráfico de barras de leads por representante: colapsa la dimensión de conversión, destruyendo precisamente el insight que el gráfico debe revelar.

**Datos de entrada para D3:**
```json
[
  { "id": "REC-001", "rep_name": "Ana Martínez",  "leads": 80,  "kpi_conversion": 30.0, "revenue": 142000, "kpi_meta_status": "green"  },
  { "id": "REC-002", "rep_name": "Carlos Ruiz",   "leads": 65,  "kpi_conversion": 18.5, "revenue": 98000,  "kpi_meta_status": "yellow" },
  { "id": "REC-003", "rep_name": "Laura Gómez",   "leads": 95,  "kpi_conversion": 32.6, "revenue": 175000, "kpi_meta_status": "green"  },
  { "id": "REC-004", "rep_name": "Ana Martínez",  "leads": 72,  "kpi_conversion": 26.4, "revenue": 118000, "kpi_meta_status": "yellow" },
  { "id": "REC-005", "rep_name": "Carlos Ruiz",   "leads": 58,  "kpi_conversion": 13.8, "revenue": 74000,  "kpi_meta_status": "red"    },
  { "id": "REC-006", "rep_name": "Miguel Torres", "leads": 88,  "kpi_conversion": 29.5, "revenue": 161000, "kpi_meta_status": "green"  },
  { "id": "REC-007", "rep_name": "Laura Gómez",   "leads": 102, "kpi_conversion": 37.3, "revenue": 193000, "kpi_meta_status": "green"  },
  { "id": "REC-008", "rep_name": "Sofía Herrera", "leads": 60,  "kpi_conversion": 16.7, "revenue": 89000,  "kpi_meta_status": "yellow" },
  { "id": "REC-009", "rep_name": "Ana Martínez",  "leads": 90,  "kpi_conversion": 31.1, "revenue": 155000, "kpi_meta_status": "green"  },
  { "id": "REC-010", "rep_name": "Carlos Ruiz",   "leads": 70,  "kpi_conversion": 20.0, "revenue": 102000, "kpi_meta_status": "yellow" },
  { "id": "REC-011", "rep_name": "Miguel Torres", "leads": 45,  "kpi_conversion": 13.3, "revenue": 67000,  "kpi_meta_status": "red"    },
  { "id": "REC-012", "rep_name": "Sofía Herrera", "leads": 78,  "kpi_conversion": 28.2, "revenue": 131000, "kpi_meta_status": "green"  },
  { "id": "REC-013", "rep_name": "Laura Gómez",   "leads": 85,  "kpi_conversion": 23.5, "revenue": 148000, "kpi_meta_status": "yellow" },
  { "id": "REC-014", "rep_name": "Ana Martínez",  "leads": 94,  "kpi_conversion": 35.1, "revenue": 168000, "kpi_meta_status": "green"  },
  { "id": "REC-015", "rep_name": "Carlos Ruiz",   "leads": 68,  "kpi_conversion": 25.0, "revenue": 110000, "kpi_meta_status": "yellow" },
  { "id": "REC-016", "rep_name": "Miguel Torres", "leads": 83,  "kpi_conversion": 28.9, "revenue": 152000, "kpi_meta_status": "green"  },
  { "id": "REC-017", "rep_name": "Sofía Herrera", "leads": 52,  "kpi_conversion": 13.5, "revenue": 79000,  "kpi_meta_status": "red"    },
  { "id": "REC-018", "rep_name": "Laura Gómez",   "leads": 110, "kpi_conversion": 38.2, "revenue": 207000, "kpi_meta_status": "green"  },
  { "id": "REC-019", "rep_name": "Ana Martínez",  "leads": 76,  "kpi_conversion": 26.3, "revenue": 133000, "kpi_meta_status": "yellow" },
  { "id": "REC-020", "rep_name": "Carlos Ruiz",   "leads": 74,  "kpi_conversion": 28.4, "revenue": 136000, "kpi_meta_status": "green"  },
  { "id": "REC-021", "rep_name": "Miguel Torres", "leads": 91,  "kpi_conversion": 31.9, "revenue": 171000, "kpi_meta_status": "green"  },
  { "id": "REC-022", "rep_name": "Sofía Herrera", "leads": 69,  "kpi_conversion": 26.1, "revenue": 124000, "kpi_meta_status": "green"  },
  { "id": "REC-023", "rep_name": "Laura Gómez",   "leads": 98,  "kpi_conversion": 35.7, "revenue": 185000, "kpi_meta_status": "green"  },
  { "id": "REC-024", "rep_name": "Ana Martínez",  "leads": 55,  "kpi_conversion": 16.4, "revenue": 91000,  "kpi_meta_status": "red"    },
  { "id": "REC-025", "rep_name": "Carlos Ruiz",   "leads": 100, "kpi_conversion": 32.0, "revenue": 178000, "kpi_meta_status": "green"  }
]
```

---

## VIZ-7 — Panel de Alertas de Registros Críticos

**Objetivo analítico:** Componer (tabla de atención focalizada en los 4 registros que requieren acción)

**Datos usados:** Los 4 registros con `kpi_meta_status = "red"` o `kpi_conversion_status = "red"`:
- REC-005, REC-011, REC-017, REC-024
- Campos: `id`, `period`, `rep_name`, `region`, `revenue`, `target`, `kpi_meta`, `kpi_meta_status`, `kpi_conversion`, `kpi_conversion_status`, diferencia revenue-target

**Tipo de gráfico:** Tabla estructurada con codificación visual inline (no es un gráfico, es una tabla de datos con visualización embebida)

**Canal perceptual:** Posición en la cuadrícula (nivel 1) para la estructura de la tabla. Barra de progreso inline (longitud, nivel 2) para kpi_meta. Color categórico (nivel 6) para estado de cada KPI. La tabla complementa — no reemplaza — los gráficos; su tarea es dar contexto de acción con datos exactos.

**Justificación:**
Munzner (2014) distingue entre tareas de "identificar" y "comparar". Para los 4 registros críticos, la tarea dominante es "identificar el origen y la magnitud del problema" — requiere datos exactos, no tendencias. Tufte (2001) defiende las tablas de datos cuando la precisión supera a la forma: aquí el manager necesita saber exactamente cuánto faltó ($46K en REC-005, $73K en REC-011) para tomar una acción correctiva. Ningún gráfico de barras comunica "$73,000 de brecha" con la misma precisión que el número.

La tabla es el único artefacto de visualización donde el canal texto supera a todos los canales visuales para recuperación de valores exactos (Stevens, 1946 — nivel de medición de razón).

**Configuración clave:**
- 4 filas (una por registro crítico), ordenadas por severidad (kpi_meta% ascendente — el peor primero: REC-011 con 47.9%)
- Columnas: ID | Mes | Representante | Región | Revenue | Gap vs Target | KPI Meta | KPI Conv
- Columna "Gap vs Target": valor negativo en rojo, barra inline de longitud proporcional al gap
- Columna "KPI Meta": badge de color (rojo/amarillo) con el valor numérico dentro
- Columna "KPI Conv": badge de color (rojo/amarillo) con el valor numérico dentro
- Fila del peor registro (REC-011) con fondo ligeramente más saturado (#FEE2E2 → #FECACA) para jerarquía visual
- Sin columnas decorativas, sin totales de fila que no aporten, sin bordes internos (solo líneas horizontales)
- Título: "Registros Críticos — Requieren Atención" con badge rojo "4"

**Prohibido aquí:**
- Gráfico de barras de los 4 KPIs críticos: la tarea no es comparar los 4 registros entre sí (aunque podría ser secundaria), sino proporcionar datos exactos para acción. Una tabla comunica los 8 valores numéricos relevantes (2 KPIs × 4 registros) con Lie Factor = 0 por definición.

**Datos de entrada para D3:**
```json
[
  { "id": "REC-011", "period": "2025-04", "rep_name": "Miguel Torres", "region": "Este",  "revenue": 67000,  "target": 140000, "gap": -73000, "kpi_meta": 47.9, "kpi_meta_status": "red",    "kpi_conversion": 13.3, "kpi_conversion_status": "red"    },
  { "id": "REC-005", "period": "2025-02", "rep_name": "Carlos Ruiz",   "region": "Sur",   "revenue": 74000,  "target": 120000, "gap": -46000, "kpi_meta": 61.7, "kpi_meta_status": "red",    "kpi_conversion": 13.8, "kpi_conversion_status": "red"    },
  { "id": "REC-024", "period": "2025-11", "rep_name": "Ana Martínez",  "region": "Norte", "revenue": 91000,  "target": 140000, "gap": -49000, "kpi_meta": 65.0, "kpi_meta_status": "red",    "kpi_conversion": 16.4, "kpi_conversion_status": "yellow" },
  { "id": "REC-017", "period": "2025-07", "rep_name": "Sofía Herrera", "region": "Oeste", "revenue": 79000,  "target": 115000, "gap": -36000, "kpi_meta": 68.7, "kpi_meta_status": "red",    "kpi_conversion": 13.5, "kpi_conversion_status": "red"    }
]
```

---

## LAYOUT SUGERIDO

### Principios de diseño aplicados

**Patrón F de lectura** (Nielsen, 2006): el ojo escanea de izquierda a derecha en la fila superior (información de mayor jerarquía), luego baja por el margen izquierdo. El layout coloca el estado global en la primera fila (escaneado horizontalmente) y los gráficos de mayor densidad en el margen izquierdo-centro.

**Ley de Miller** (1956): capacidad de memoria de trabajo = 7 ± 2 elementos. El dashboard tiene 7 elementos visuales totales (VIZ-1 a VIZ-7). Cada fila del layout no supera 3 elementos visuales simultáneos. Los BANs de VIZ-1 son 4 números + 1 badge = 5 chunks, dentro del límite.

**Jerarquía de atención**: lo más urgente (alertas rojas, VIZ-7) debe estar en zona de alta visibilidad — columna izquierda, segunda fila — no al fondo de la página. El ojo no debe buscar el problema.

---

### Disposición del Dashboard (grilla de 12 columnas)

```
┌─────────────────────────────────────────────────────────────────┐
│  FILA 1 — Zona de resumen ejecutivo (altura: 100px)             │
│                                                                  │
│  [VIZ-1: BANs de Estado Global] ───────────────── 12 columnas  │
│  Revenue Total | KPI Meta 98.9% | KPI Conv 26.3% | 4 Críticos  │
│  Badge AMARILLO centrado                                         │
└─────────────────────────────────────────────────────────────────┘
┌──────────────────────┬──────────────────────┬───────────────────┐
│  FILA 2 — Zona de    │                      │                   │
│  alertas y estado    │                      │                   │
│  (altura: 280px)     │                      │                   │
│                      │                      │                   │
│  [VIZ-7: Tabla de    │  [VIZ-5: Heatmap     │  [VIZ-2: Dot      │
│  Registros Críticos] │  Semáforo            │  Plot             │
│  4 columnas          │  Rep × Mes]          │  Representantes]  │
│                      │  5 columnas          │  3 columnas       │
│  Posición: arriba-   │                      │                   │
│  izquierda (zona F   │  Posición: centro    │  Posición:        │
│  de alta atención)   │  (mayor densidad     │  derecha          │
│                      │  de información)     │                   │
└──────────────────────┴──────────────────────┴───────────────────┘
┌───────────────────────────────┬─────────────────────────────────┐
│  FILA 3 — Zona analítica      │                                 │
│  (altura: 300px)              │                                 │
│                               │                                 │
│  [VIZ-4: Line Chart           │  [VIZ-3: Bullet Chart           │
│  Evolución Trimestral]        │  por Región]                    │
│  6 columnas                   │  6 columnas                     │
│                               │                                 │
│  Posición: abajo-izquierda    │  Posición: abajo-derecha        │
│  (tendencia = contexto        │  (comparación regional =        │
│  necesario para entender      │  complementa la tendencia       │
│  el estado actual)            │  temporal)                      │
└───────────────────────────────┴─────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  FILA 4 — Zona de insight avanzado (altura: 300px)              │
│                                                                  │
│  [VIZ-6: Scatter Plot Leads vs Conversión] ─── 12 columnas     │
│                                                                  │
│  Posición: abajo (zona de lectura secundaria — requiere         │
│  mayor atención cognitiva; el usuario llega aquí después        │
│  de haber procesado el contexto de las filas anteriores)        │
└─────────────────────────────────────────────────────────────────┘
```

---

### Justificación del orden de lectura

| Posición | Visualización | Razón de ubicación |
|---|---|---|
| Fila 1 completa | VIZ-1 BANs | Patrón F: primera franja horizontal = dato más importante. El estado global del equipo es la pregunta ejecutiva de primer nivel. |
| Fila 2 izquierda | VIZ-7 Alertas Críticas | Zona de alta visibilidad del patrón F (margen izquierdo). Los 4 registros rojos requieren acción inmediata — deben ser visibles sin scroll. |
| Fila 2 centro | VIZ-5 Heatmap | El elemento de mayor densidad informativa va al centro visual de la fila — atrae el ojo después de los BANs y las alertas. |
| Fila 2 derecha | VIZ-2 Dot Plot reps | Complementa el heatmap: el heatmap muestra el detalle mes a mes, el dot plot colapsa el año en un promedio por representante. |
| Fila 3 izquierda | VIZ-4 Tendencia | La trayectoria temporal responde a "¿por qué estamos en AMARILLO?". Va en posición de lectura descendente (patrón Z). |
| Fila 3 derecha | VIZ-3 Regiones | Complemento natural de la tendencia: qué regiones arrastran el promedio. Lectura en paralelo con VIZ-4. |
| Fila 4 completa | VIZ-6 Scatter | Insight avanzado (leads vs. conversión). Va al fondo porque requiere mayor carga cognitiva — el usuario la alcanza cuando ya tiene contexto. |

### Restricciones de implementación

- **Máximo 7 elementos** en la vista sin scroll (Ley de Miller): este layout tiene exactamente 7 visualizaciones, distribuidas en 4 filas — ninguna fila supera 3 elementos.
- **Responsividad**: en pantallas < 1200px, Fila 2 y Fila 3 colapsan a diseño de una columna (VIZ-7 primero, VIZ-5 segundo, etc.), manteniendo el orden de prioridad.
- **Color**: las 4 alertas críticas (VIZ-7) usan el mismo rojo (#EF4444) que los puntos críticos en VIZ-5 y VIZ-6 — consistencia de código de color en todo el dashboard.
- **Sin decoración de marca** en el área del gráfico: logos, degradados, ilustraciones y bordes decorativos van en el shell del dashboard, no en el espacio de datos.
