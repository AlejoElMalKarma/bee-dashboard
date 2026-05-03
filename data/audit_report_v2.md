# Audit Report v2 — Bee Dashboard
Fecha: 2026-04-28

## Estado general: PASA CON OBSERVACIONES
2 bugs críticos nuevos · 3 advertencias anteriores pendientes · 3 mejoras sugeridas

---

## Verificación de bugs críticos corregidos

### BUG-1 — CORREGIDO ✓
**Archivo:** `js/charts/scatter.js` líneas 133–158

El coeficiente r de Pearson se calcula correctamente de forma dinámica:

```js
const ssXY = d3.sum(xVals.map((x, i) => (x - mx) * (yVals[i] - my)));
const ssX  = d3.sum(xVals.map(x => (x - mx) ** 2));
const ssY  = d3.sum(yVals.map(y => (y - my) ** 2));
const r    = ssXY / Math.sqrt(ssX * ssY);
```

Verificación manual con los 25 registros: r = 0.9442. El texto OLS muestra `OLS r≈+0.94`, que coincide con el valor calculado. La corrección es completa y matemáticamente correcta.

---

### BUG-2 — CORREGIDO ✓
**Archivo:** `css/dashboard.css` líneas 202–204

```css
.ban-value.green  { color: var(--color-green-text); }
.ban-value.yellow { color: var(--color-yellow-text); }
.ban-value.red    { color: var(--color-red-text); }
```

Las variables apuntan a `#15803d` (verde, contraste 5.1:1), `#b45309` (amarillo, 4.77:1) y `#b91c1c` (rojo, 4.63:1). Los tres valores superan el umbral WCAG AA de 4.5:1 sobre fondo blanco. Corrección verificada.

---

### BUG-3 — CORREGIDO ✓
**Archivos:** `js/charts/dot_plot.js`, `js/charts/heatmap.js`, `js/charts/line_chart.js`, `js/charts/scatter.js`

Todas las etiquetas de texto de ejes y paneles usan `#6b7280` (contraste 4.83:1 sobre blanco, cumple WCAG AA). Verificado en cada archivo:

- `dot_plot.js` líneas 111, 185: `'#6b7280'`
- `heatmap.js` líneas 121, 133: `'#6b7280'`
- `line_chart.js` línea 215: `'#6b7280'`
- `scatter.js` líneas 121, 130, 156: `'#6b7280'`

---

## Estado de advertencias anteriores

### WARN-1 — PENDIENTE
**Ningún SVG tiene `role="img"` ni `aria-label`.**

Todos los gráficos crean SVGs con `.append('svg').attr('class','chart-svg')` pero sin atributos ARIA. El estándar WCAG 1.1.1 requiere alternativa textual para contenido no textual. Afecta a los 6 SVGs generados por D3 (VIZ-2, VIZ-3, VIZ-4, VIZ-5, VIZ-6 y VIZ-7-equivalente). No fue corregido entre v1 y v2.

---

### WARN-2 — PENDIENTE
**Heatmap usa `▲` para amarillo; CLAUDE.md manda `⚠`.**

`js/charts/heatmap.js` línea 59:
```js
const convSymbol = { green: '✓', yellow: '▲', red: '✕' };
```

`CLAUDE.md` línea 134 especifica explícitamente `⚠` para el estado de atención/amarillo. El error persiste tanto en el símbolo de las celdas SVG como en la leyenda HTML (línea 95 del mismo archivo muestra `▲` en la leyenda). Nota: `bullet_chart.js` sí usa `⚠` correctamente — la inconsistencia es exclusiva del heatmap.

---

### WARN-3 — PENDIENTE
**El color del dot en el dot plot se deriva del peor registro histórico, no del promedio.**

La lógica actual en `js/charts/dot_plot.js` líneas 66–68:
```js
const hasRed    = rep.statuses.includes('red');
const hasYellow = rep.statuses.includes('yellow');
const status = hasRed ? 'red' : hasYellow ? 'yellow' : 'green';
```

Resultado con los datos actuales:
- **Ana Martínez:** media KPI Meta = 100.45% (sobre benchmark), pero aparece en **rojo** porque tiene 1 registro rojo (REC-024, nov-2025).
- **Miguel Torres:** media = 96.40%, aparece en rojo por REC-011.
- **Sofía Herrera:** media = 91.70%, aparece en rojo por REC-017.
- **Carlos Ruiz:** media = 90.78%, aparece en rojo por REC-005.

Solo Laura Gómez aparece en amarillo (no tiene registros rojos). El gráfico comunica una imagen más negativa que la realidad anual del equipo. La corrección apropiada sería colorear por `status` de la media (aplicando las mismas reglas: `>= 100` verde, `>= 80` amarillo, `< 80` rojo).

---

### WARN-4 — PENDIENTE
**Eje X del bullet chart muestra `$1000K` en lugar de `$1M`.**

`js/charts/bullet_chart.js` línea 67:
```js
.tickFormat(d => `$${d / 1000}K`)
```

Con `domain([0, maxVal])` donde `maxVal = 1_000_000`, D3 genera 6 ticks en `[0, 200000, 400000, 600000, 800000, 1000000]`. El tick de `1000000` se formatea como `$1000K` en lugar de `$1M`. Aunque el máximo de datos es $908K (Centro), el dominio fijo incluye ese tick y este valor se renderiza incorrectamente.

Corrección sugerida:
```js
.tickFormat(d => d >= 1_000_000 ? `$${d/1_000_000}M` : `$${d/1000}K`)
```

---

### WARN-5 — PENDIENTE (agravado)
**El subtítulo del scatter describe incorrectamente la relación leads-conversión.**

El título dice: `"Más leads no garantiza más conversión"`.

Sin embargo, el coeficiente de Pearson calculado dinámicamente es **r = 0.94**, que indica una correlación positiva muy fuerte entre leads y conversión. El mensaje contradice directamente la estadística que el propio gráfico calcula y muestra. Un r = 0.94 significa exactamente lo contrario: más leads sí se asocia con más conversión en este dataset.

La segunda parte del título (`REC-011 y REC-005 son outliers críticos en ambas dimensiones`) es correcta: ambos registros están por debajo de la línea de regresión con baja conversión y pocos leads.

Corrección sugerida para el título:
```
"Alta correlación leads-conversión (r=0.94) — REC-011 y REC-005 quedan muy por debajo de la tendencia"
```

---

### WARN-6 — PENDIENTE
**El BAN de "KPI Meta Promedio" muestra 99.4%, diferente del 98.9% documentado en el reporte anterior.**

El cálculo en `js/charts/bans.js` línea 18 es:
```js
const kpiMetaMean = d3.mean(records, d => d.kpi_meta);
```

Con los 25 registros, la media aritmética de los valores `kpi_meta` almacenados es **99.43%**, que se muestra como **99.4%**. El valor es matemáticamente correcto para la media de los 25 valores almacenados en el JSON. La discrepancia de 0.5pp respecto al reporte anterior (98.9%) se debe a que el reporte v1 calculaba la cifra de forma diferente (posiblemente sobre revenue/target agregado = 3,387K/3,370K = 100.5%). No hay inconsistencia en el código actual — la advertencia se mantiene como nota de documentación que debería aclararse.

---

## Nuevos bugs críticos encontrados

### NUEVO-BUG-1 — El título del line chart muestra el KPI de Conversión de Q3 incorrecto
**Severidad: Alta (dato incorrecto visible al usuario)**
**Archivo:** `index.html` línea 118

```html
<div class="card-title">Q3 fue el mejor trimestre (104% meta, 29.5% conv.) — Q4 mantiene el impulso sobre benchmark</div>
```

El valor **29.5% conv.** es incorrecto. El promedio real de KPI Conversión en Q3 (calculado por `line_chart.js` sobre los datos) es **27.87%**. El `29.5%` que aparece en el título corresponde al valor de conversión de un único registro (REC-006, Miguel Torres, Feb-2025), no al promedio trimestral.

El valor de KPI Meta (104%) sí es correcto (media real: 103.98% ≈ 104%).

**Corrección:** cambiar `29.5% conv.` por `27.9% conv.` en el título de la sección de evolución temporal.

---

### NUEVO-BUG-2 — La variable `r` se usa como radio de burbuja y como coeficiente de Pearson en el mismo scope
**Severidad: Media (riesgo de colisión de nombre de variable)**
**Archivo:** `js/charts/scatter.js` líneas 151 y 173

```js
// línea 151 — Pearson r
const r = ssXY / Math.sqrt(ssX * ssY);

// línea 173 — radio de burbuja (dentro de forEach)
const r = rScale(d.revenue);  // shadowing de la variable exterior
```

Dentro del `forEach` en la línea 173, se declara `const r = rScale(d.revenue)`, lo cual hace *shadowing* de la variable `r` de Pearson definida en el scope exterior. En el `mouseout` handler (línea 198) se usa `r` sin especificar cuál, pero por clausura captura el `r` local (radio), lo cual es correcto en este caso. Sin embargo, el shadowing es ambiguo, propenso a errores de mantenimiento y generará advertencias en linters estrictos. No hay bug funcional actualmente porque los scopes están bien delimitados, pero la práctica viola el principio de nombres únicos y claros.

**Corrección sugerida:** renombrar la variable interior a `bubbleR` o `circleR`.

---

## Nuevas advertencias

### NUEVA-WARN-A — El dot plot no muestra "Miguel Torres" en todos los meses y el heatmap tiene 35 celdas vacías
**Severidad: Baja (comportamiento esperado, pero no documentado)**

El heatmap tiene 60 posibles celdas (5 reps × 12 meses) pero solo 25 registros en el JSON. Esto genera 35 celdas vacías (mostradas con `—`). El diseño lo maneja correctamente con `metaBg['null']` y el guión, pero el usuario podría interpretar las celdas vacías como ausencia de actividad del representante cuando en realidad son meses en que ese rep simplemente no tiene un registro asignado en el dataset. Una nota explicativa en la leyenda del heatmap mejoraría la comprensión.

---

### NUEVA-WARN-B — Bullet chart: el subtítulo dice "Línea negra = target asignado" pero la leyenda dice "= Target asignado"
**Severidad: Baja (inconsistencia menor entre HTML y JS)**

El subtítulo en `index.html` línea 87 dice `"Línea negra = target asignado"`. La leyenda generada en `bullet_chart.js` línea 153 dice `"= Target asignado"` (sin mencionar el color). Hay una pequeña inconsistencia de capitalización ("target" vs "Target") y el subtítulo HTML describe la línea por su color mientras la leyenda JS no lo hace. No es un error crítico, pero la consistencia es recomendable.

---

## Verificaciones que PASAN

- Los 25 registros tienen sus campos `kpi_meta_status` y `kpi_conversion_status` correctamente asignados según las reglas del JSON metadata (>=100 verde, >=80 amarillo, <80 rojo para meta; >=25 verde, >=15 amarillo, <15 rojo para conversión). Ningún record tiene status incorrecto.
- Los 4 registros críticos (rojo) identificados por `alerts_table.js` son correctos: REC-005, REC-011, REC-017, REC-024. Ordenados correctamente por kpi_meta ascendente (peor primero: REC-011 con 47.9%).
- El bullet chart ordena regiones por revenue descendente correctamente: Centro ($908K) > Norte ($807K) > Sur ($698K) > Este ($551K) > Oeste ($423K).
- El título del bullet chart es facualmente correcto: Centro y Norte sí superan su target acumulado anual; Sur, Este y Oeste no.
- El título del dot plot es facualmente correcto: Laura Gómez lidera (117.2% meta, 33.5% conv.); Sofía (91.7% meta, 21.1% conv.) y Carlos (90.8% meta, 23.0% conv.) no alcanzan benchmarks en ninguno de los dos KPIs.
- El heatmap título es correcto: Carlos Ruiz acumula exactamente 3 meses en amarillo (Ene-2025, Abr-2025, Jun-2025).
- Los dominios de los ejes del scatter son adecuados: X=[0,120] cubre max leads=110; Y=[0,45] cubre max conversión=38.2%.
- Los dominios del line chart no recortan datos: yLeft=[80,115] cubre Q1=98.1%, Q2=95.2%, Q3=104.0%, Q4=102.8%; yRight=[20,35] cubre todos los promedios de conversión trimestral (25.6%–27.9%).
- La anotación "Mejor trimestre" en Q3 es correcta: Q3 tiene la media de KPI Meta más alta (103.98%).
- La paleta Okabe-Ito del scatter es accesible para daltonismo (confirmado por diseño).
- El CSS define correctamente `--color-green-text: #15803d` (contraste 5.1:1), `--color-yellow-text: #b45309` (4.77:1), `--color-red-text: #b91c1c` (4.63:1), todos sobre blanco.
- La función `fmtCurrency` en `bans.js` formatea correctamente $3,387,000 como `$3.39M`.
- El badge de estado del equipo usa `⚠` para amarillo, `✓` para verde y `✗` para rojo, cumpliendo CLAUDE.md.
- El bullet chart usa `statusIcons = { green: '✓', yellow: '⚠', red: '✗' }`, cumpliendo CLAUDE.md.
- El sistema de color usa tokens CSS centralizados correctamente; los gráficos usan valores hexadecimales directos solo para colores de datos (no semáforos de BAN).
- El dashboard carga desde `d3.json('./data/sales_report.json')` con manejo de error correcto.
- La estructura HTML sigue la pirámide invertida de CLAUDE.md: BANs arriba, análisis en el medio, detalle transaccional (alertas) abajo. La navegación F/Z está correctamente implementada.
- Todos los títulos de sección son narrativos (no genéricos), conforme a la Fase 4 de CLAUDE.md ("Títulos narrativos").
- No hay efectos 3D, degradados decorativos ni pie charts, conforme a Tufte y CLAUDE.md.
- El eje Y de la barra de revenue empieza en 0 (Tufte: Lie Factor = 1.0).
- Los tooltips tienen contraste adecuado: texto `#f9fafb` sobre fondo `rgba(17,24,39,0.95)` (~16:1).

---

## Recomendación final

**El dashboard NO está listo para producción.** Requiere correcciones antes de mostrarse a usuarios:

### Crítico — corregir antes de publicar:
1. **NUEVO-BUG-1:** El título del line chart muestra `29.5% conv.` para Q3, pero el valor real es `27.87%`. Es un dato incorrecto visible en el heading narrativo de la sección. Corrección: cambiar a `27.9% conv.` en `index.html` línea 118.

### Moderado — corregir en el mismo sprint:
2. **WARN-4:** El eje X del bullet chart muestra `$1000K` para el tick de 1 millón. Corrección de una línea en `bullet_chart.js`.
3. **WARN-5:** El subtítulo del scatter contradice r=0.94. Corrección editorial en `index.html` línea 138.
4. **WARN-2:** El heatmap usa `▲` para amarillo en lugar de `⚠` (CLAUDE.md lo exige). Corrección en `heatmap.js` línea 59 y leyenda HTML (línea 95).
5. **WARN-3:** El color del dot en el dot plot refleja el peor registro histórico, no el promedio anual. Ana Martínez (media 100.45%) aparece en rojo. La lógica de coloración debería basarse en la media calculada.

### Baja prioridad — puede diferirse:
6. **WARN-1:** Agregar `role="img"` y `aria-label` descriptivo a los 6 SVGs generados.
7. **NUEVO-BUG-2:** Renombrar la variable `r` interna del forEach en `scatter.js` para evitar shadowing con el coeficiente de Pearson.
8. **NUEVA-WARN-A:** Agregar nota en la leyenda del heatmap explicando que las celdas vacías son meses sin asignación en el dataset.
