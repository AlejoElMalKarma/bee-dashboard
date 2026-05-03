# Audit Report — Bee Dashboard
Fecha: 2026-04-28

## Resumen ejecutivo

**Estado general: PASA CON OBSERVACIONES**

- **3 bugs críticos** (bloquean la conformidad con CLAUDE.md / WCAG)
- **6 advertencias** (funcionan pero son incorrectos por diseño o especificación)
- **4 mejoras sugeridas** (no bloquean, mejoran calidad)

El dashboard carga y renderiza correctamente los 7 módulos visuales. No hay errores de sintaxis JS. Los datos fuente son matemáticamente íntegros. Los problemas principales son: (1) una anotación estadística hardcodeada incorrecta en el scatter plot, (2) tres combinaciones de color que violan WCAG 4.5:1 en elementos de texto prominentes del BAN, y (3) ausencia total de atributos de accesibilidad SVG.

---

## Bugs críticos (bloquean el funcionamiento o conformidad)

### BUG-1 — Anotación OLS hardcodeada incorrecta en scatter.js

- **Archivo:** `js/charts/scatter.js`, línea 152
- **Línea aproximada:** 152
- **Descripción:** El texto `'OLS r≈+0.6'` está hardcodeado, pero el coeficiente de correlación de Pearson calculado sobre los datos reales es **r = 0.944** (no 0.6). El propio código calcula la pendiente e intercepto OLS dinámicamente (líneas 133–146) pero no usa el resultado para la anotación. El valor mostrado es factualmente falso y contradice la línea de regresión dibujada.
- **Corrección:** Calcular `r` dinámicamente a partir de los datos y usarlo en la anotación:
  ```js
  // Agregar después de calcular slope/intercept:
  const sdX = Math.sqrt(d3.sum(xVals.map(x => (x - mx) ** 2)) / n);
  const sdY = Math.sqrt(d3.sum(yVals.map(y => (y - my) ** 2)) / n);
  const r   = (d3.sum(xVals.map((x, i) => (x - mx) * (yVals[i] - my))) / n) / (sdX * sdY);
  // Luego cambiar la línea 152:
  .text(`OLS r≈${r >= 0 ? '+' : ''}${r.toFixed(2)}`);
  ```

---

### BUG-2 — Valores de color de BANs no cumplen WCAG 4.5:1 (texto grande prominente)

- **Archivo:** `js/charts/bans.js` (líneas 45–52) y `css/dashboard.css` (líneas 202–204)
- **Línea aproximada:** bans.js: 45–52; CSS: 202–204
- **Descripción:** Las clases `.ban-value.green` (`#10b981` sobre `#ffffff`) y `.ban-value.yellow` (`#f59e0b` sobre `#ffffff`) usadas para el texto principal de 36px de los KPI no alcanzan el mínimo WCAG AA:

  | Color | Ratio | Mínimo AA | Estado |
  |---|---|---|---|
  | `#10b981` (verde sem) / blanco | 2.54:1 | 4.5:1 | **FALLA** |
  | `#f59e0b` (amarillo sem) / blanco | 2.15:1 | 4.5:1 | **FALLA** |
  | `#ef4444` (rojo sem) / blanco | 3.76:1 | 4.5:1 | **FALLA** (pasa 3:1 para texto grande ≥18pt bold) |

  CLAUDE.md establece explícitamente: *"Contraste mínimo WCAG: 4.5:1 texto/fondo"*.

- **Corrección:** Reemplazar los colores semáforo por los de la paleta WCAG definida en las variables CSS del propio dashboard:
  ```css
  /* En dashboard.css, líneas 202-204: */
  .ban-value.green  { color: var(--color-green-text);  } /* #15803d — 5.02:1 ✓ */
  .ban-value.yellow { color: var(--color-yellow-text); } /* #b45309 — 5.02:1 ✓ */
  .ban-value.red    { color: var(--color-red-text);    } /* #b91c1c — 6.47:1 ✓ */
  ```

---

### BUG-3 — Color de etiquetas de eje `#9ca3af` no cumple WCAG 4.5:1

- **Archivo:** `js/charts/dot_plot.js` (líneas 108, 184), `js/charts/line_chart.js` (líneas 87–88), y en múltiples gráficos SVG que usan `fill: '#9ca3af'`
- **Línea aproximada:** múltiples (dot_plot: 108, 184; line_chart: 88; scatter: 121, 129)
- **Descripción:** El color `#9ca3af` sobre fondo blanco produce un contraste de **2.54:1**, muy por debajo del mínimo WCAG AA de 4.5:1. Este color se usa para etiquetas de panel (`'KPI META (%) — benchmark 100%'`), subtítulos y texto de eje. CLAUDE.md prohíbe explícitamente *"gris claro sobre blanco"*.
- **Corrección:** Reemplazar `#9ca3af` en labels relevantes por `#6b7280` (4.83:1, ya aprobado en el CSS) o `#4b5563` (7.45:1) para textos de mayor importancia comunicativa.

---

## Advertencias (funcionan pero son incorrectos por diseño o especificación)

### WARN-1 — Ausencia total de atributos de accesibilidad en SVG

- **Archivos:** `js/charts/dot_plot.js`, `js/charts/bullet_chart.js`, `js/charts/line_chart.js`, `js/charts/heatmap.js`, `js/charts/scatter.js`
- **Descripción:** Ningún elemento SVG tiene `role="img"`, `aria-label`, ni `<title>` descriptivo. Los usuarios de lectores de pantalla no reciben información alguna sobre los gráficos. CLAUDE.md no lo prohíbe explícitamente, pero es una omisión grave para cualquier dashboard que pretenda ser WCAG conforme.
- **Corrección:** Añadir al menos en cada SVG raíz:
  ```js
  svg.attr('role', 'img')
     .attr('aria-label', 'Descripción del gráfico...');
  // Y opcionalmente un <title> como primer child:
  svg.append('title').text('Descripción para lectores de pantalla');
  ```

---

### WARN-2 — Heatmap usa ▲ como icono de estado Amarillo en lugar de ⚠ (CLAUDE.md)

- **Archivo:** `js/charts/heatmap.js`, línea 59
- **Descripción:** La guía CLAUDE.md establece que el estado "Atención / en riesgo" debe usar el icono **⚠** (triángulo de advertencia estándar). El heatmap usa `▲` (triángulo simple) para el estado yellow de `kpi_conversion_status`. Esto es inconsistente con el resto del dashboard (bullet_chart, bans, alerts_table usan ⚠) y con la especificación.
- **Corrección:** En `heatmap.js`, línea 59:
  ```js
  // Cambiar:
  const convSymbol = { green: '✓', yellow: '▲', red: '✕' };
  // Por:
  const convSymbol = { green: '✓', yellow: '⚠', red: '✕' };
  ```

---

### WARN-3 — Dot plot y Bullet chart usan "peor registro" como estado de rep/región, no la media

- **Archivos:** `js/charts/dot_plot.js` (líneas 66–69), `js/charts/bullet_chart.js` (líneas 31–33)
- **Descripción:** El color del punto/barra de cada representante/región refleja el peor registro histórico, no el estado del promedio anual. Esto crea inconsistencias visuales graves: por ejemplo, **Ana Martínez** se muestra en rojo en el dot plot (kpi_meta_mean = 100.5%, estado real: VERDE) porque tuvo un solo mes rojo (REC-024). **Norte** aparece en rojo en el bullet chart a pesar de superar su target acumulado (807K vs 805K, +0.2%). El título de la tarjeta del bullet chart ("Centro y Norte superan su target") contradice el color rojo mostrado para Norte.
- **Corrección en dot_plot.js:**
  ```js
  // Calcular status basado en la MEDIA, no en el peor registro:
  const meanStatus = metaMean >= 100 ? 'green' : metaMean >= 80 ? 'yellow' : 'red';
  return { ..., status: meanStatus };
  ```
- **Corrección en bullet_chart.js:** Igual — usar `kpiMeta >= 100` para determinar el status de color.

---

### WARN-4 — Etiqueta de eje en bullet_chart muestra "$1000K" en lugar de "$1M"

- **Archivo:** `js/charts/bullet_chart.js`, línea 67
- **Descripción:** El scale X tiene dominio `[0, 1_000_000]`. Con `.ticks(5)`, D3 genera el tick en 1,000,000. El `tickFormat` `d => \`$\${d / 1000}K\`` produce `$1000K`, que es confuso e incorrecto (debería ser `$1M`).
- **Corrección:**
  ```js
  .tickFormat(d => d >= 1_000_000 ? `$${d/1_000_000}M` : `$${d/1000}K`)
  ```

---

### WARN-5 — Anotación scatter "REC-011 y REC-005 son outliers en ambas dimensiones" es inexacta

- **Archivo:** `index.html`, línea 138 (card-subtitle del VIZ-6)
- **Descripción:** El card-subtitle dice: *"REC-011 y REC-005 son outliers críticos en ambas dimensiones"*. Sin embargo, en el eje X (leads), REC-011 tiene 45 leads (mínimo del dataset) y REC-005 tiene 58 leads. Ambos están en el cuadrante inferior-izquierdo pero no son outliers extremos en la dimensión X comparados con REC-018 (110 leads) o REC-007 (102). Son outliers en kpi_meta (rojo) y kpi_conversion (bajos), no necesariamente en leads. El lenguaje de la descripción es impreciso.
- **Corrección sugerida:** Cambiar a: *"REC-011 y REC-005 combinan bajo volumen de leads con conversión crítica — peores registros en eficiencia"*.

---

### WARN-6 — "Estado AMARILLO (98.9% meta)" del spec no coincide con los datos calculados

- **Archivo:** `data/sales_report.json` (todos los registros)
- **Descripción:** La especificación de la auditoría indica el estado global como "98.9% meta, 26.3% conversión". El cálculo real sobre los 25 registros da **99.4% meta** (suma de kpi_meta / 25 = 2485.7 / 25) y **26.3% conversión**. La discrepancia en meta (~0.5 puntos) sugiere que la especificación fue calculada manualmente con redondeo distinto. El código (`bans.js`) calcula correctamente 99.43% y lo clasifica como AMARILLO (< 100%), que es el resultado correcto. No es un bug del código sino una imprecisión documental.
- **Acción:** Actualizar la especificación del proyecto para reflejar el valor exacto: **99.4% meta**.

---

## Mejoras sugeridas (no bloquean, mejoran calidad)

### OPT-1 — Migrar de patrón `append()` imperativo a `data().join()` idiomático en D3 v7

- **Archivos:** Todos los archivos en `js/charts/`
- **Descripción:** Ningún gráfico usa el patrón de selección de datos D3 (`.data().join()`). Todos usan `forEach` + `.append()` directo. Para datos estáticos cargados una vez esto funciona correctamente, pero no es el patrón idiomático de D3 v7. Si en el futuro se requieren actualizaciones dinámicas (filtros, animaciones de transición), el código deberá reescribirse.
- **Mejora:** Adoptar el patrón `.selectAll().data().join()` al menos en los gráficos con múltiples elementos homogéneos (heatmap, scatter, dot_plot).

---

### OPT-2 — Añadir `<title>` y `aria-describedby` para lectores de pantalla en SVG

- **Archivos:** Todos los SVG en `js/charts/`
- **Descripción:** Complemento a WARN-1. Además de `role="img"`, cada SVG debería tener un `<title>` como primer hijo y, para gráficos complejos (heatmap, scatter), un `<desc>` con el resumen de la visualización.

---

### OPT-3 — Tooltip del heatmap: no muestra el ID del registro (útil para auditoría)

- **Archivo:** `js/charts/heatmap.js`, líneas 178–188
- **Descripción:** El tooltip del heatmap muestra Revenue, Target, Leads, Deals, KPI Meta y KPI Conv, pero omite el `id` del registro (ej. `REC-024`). Dado que las alertas críticas se identifican por ID, añadirlo mejoraría la trazabilidad entre el heatmap y la tabla de alertas.
- **Mejora:** Añadir `<div class="tooltip-row"><span>ID</span><span class="tooltip-val">${rec.id}</span></div>` en el tooltip.

---

### OPT-4 — Bullet chart: reducir el dominio X de 1M a valor dinámico basado en los datos

- **Archivo:** `js/charts/bullet_chart.js`, línea 45
- **Descripción:** El `maxVal` está hardcodeado a `1_000_000`. El valor máximo real de revenue regional es $908K (Centro). El dominio hardcodeado desperdicia ~10% del ancho visual y comprime las barras innecesariamente. Calcular el máximo dinámicamente mejora la resolución visual.
- **Mejora:**
  ```js
  const maxVal = Math.ceil(Math.max(...regionData.map(d => Math.max(d.revenue, d.target))) / 100000) * 100000;
  ```

---

## Verificaciones que PASAN

- **Sintaxis JS:** Cero errores en `node --check` para los 8 archivos JS (7 charts + dashboard.js).
- **Registro de módulos:** Todos los 7 módulos exponen correctamente su función en `window.Charts.*` (bans, dotPlot, bulletChart, lineChart, heatmap, scatter, alertsTable).
- **Llamadas en dashboard.js:** Los 7 módulos son invocados con los container IDs correctos (`viz-1` a `viz-7`).
- **Integridad matemática de datos:** Los 25 registros tienen `kpi_meta = (revenue/target)*100` y `kpi_conversion = (deals_closed/leads)*100` correctos (tolerancia ±0.1%).
- **Flags de estado:** Los 25 registros tienen `kpi_meta_status` y `kpi_conversion_status` correctamente asignados según las reglas del JSON metadata.
- **Registros críticos:** Los 4 registros con `kpi_meta_status = 'red'` son exactamente REC-005, REC-011, REC-017, REC-024. Aparecen correctamente en la tabla de alertas (VIZ-7) y marcados con contorno rojo en el scatter (VIZ-6).
- **Posición de BANs:** VIZ-1 (BANs) está en la primera sección "Resumen Ejecutivo" — correcta posición superior izquierda según patrón F/Z (Shneiderman).
- **Ley de Miller:** 7 elementos visuales en la vista principal (VIZ-1 a VIZ-7), dentro del límite máximo de 7.
- **Lie Factor (barras):** El bullet chart (único gráfico de barras) tiene su eje X comenzando desde 0. Los dot plots y scatter no son gráficos de barras, por lo que las restricciones de eje en cero no aplican.
- **Redundancia visual en semáforos:** Todos los semáforos en BANs, bullet chart, alerts table y heatmap combinan color + icono (✓/⚠/✗), cumpliendo la regla de CLAUDE.md para usuarios con daltonismo.
- **Sin chartjunk:** No hay efectos 3D, degradados decorativos ni fondos pesados. Box-shadows son mínimos y funcionales.
- **Tooltip viewport overflow:** Los 3 módulos con tooltip (dot_plot, heatmap, scatter) implementan protección contra salida del viewport con `window.innerWidth`/`window.innerHeight`.
- **Tooltip singleton:** El tooltip global de HTML (#global-tooltip) es reutilizado por todos los módulos. El patrón `getTooltip()` busca primero el elemento existente y solo crea uno nuevo como fallback.
- **Heatmap celdas vacías:** El heatmap maneja correctamente los 35 pares rep×mes sin datos, mostrando fondo gris y guión "—" en lugar de romper el render.
- **Dominios de escalas dentro de rango:** Todos los valores de datos están dentro de los dominios declarados en los scales (dot_plot xMeta [40-135], xConv [10-42]; scatter xScale [0-120] y yScale [0-45]; bullet chart [0, 1M]; line_chart yLeft [80-115] y yRight [20-35]).
- **Paleta de color para badges y tabla:** Los componentes HTML puros (kpi-badge, status-badge, gap-bar) usan las variables CSS de la paleta WCAG correcta (`--color-red-text: #b91c1c`, `--color-yellow-text: #b45309`, `--color-green-text: #15803d`), que superan el umbral de 4.5:1.
- **Contraste de tooltip:** Texto `#f9fafb` sobre fondo `#111827` en tooltip: 16.98:1 — excelente.
- **Agregación por trimestre:** Medias de KPI Meta por trimestre (Q1: 98.1%, Q2: 95.2%, Q3: 104.0%, Q4: 102.8%) son correctas. Q3 es el mejor trimestre. La anotación "Mejor trimestre" en VIZ-4 es correcta.
- **Regresión OLS calculada:** La línea de regresión en scatter.js se calcula dinámicamente con fórmulas OLS correctas (pendiente = 0.4195, intercepto = -6.52). El bug es solo la anotación textual del r.
- **Carga de datos:** `dashboard.js` usa `d3.json('./data/sales_report.json')` con manejo de error (`catch`) y validación de estructura (`if (!data || !data.records)`).
- **Títulos narrativos:** Todas las tarjetas de gráficos tienen títulos que comunican hallazgos, no solo contenido (cumple pauta de "títulos narrativos" de CLAUDE.md).
