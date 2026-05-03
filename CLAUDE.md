# Dashboard Design Guide

Guía de referencia para diseñar y construir dashboards. Aplica a cualquier proyecto de visualización de datos, independientemente de la herramienta o fuente de datos.

Basada en los notebooks "dashboard creation" (68 fuentes) y el segundo notebook de visualización (90 fuentes), con principios de Tufte, Shneiderman, Munzner, Cairo, Cleveland & McGill, Bertin y Stephen Few.

---

## Fase 0 — Descubrimiento (antes de diseñar nada)

Responder estas preguntas antes de elegir un solo gráfico:

1. **¿Quién es la audiencia?** CEO estratégico (métricas macro, sin filtros) vs. analista técnico (granularidad, drill-down). El mismo dashboard no sirve para ambos.
2. **¿Cuál es la pregunta de negocio en una frase?** Si no se puede resumir en una frase, el dashboard será un volcado de datos inútil.
3. **¿Qué decisión o acción se tomará con cada KPI?** Cada métrica debe tener un propietario y un plan de acción si cae fuera del umbral.
4. **¿Cuál es la cadencia de decisión?**
   - Tiempo real → dashboard **Operativo**
   - Diario/semanal → dashboard **Táctico**
   - Mensual/anual → dashboard **Estratégico**

---

## Fase 1 — Arquitectura de datos

### Capas de datos (Arquitectura Medallón)
- **Bronce:** datos crudos tal como llegan de la fuente.
- **Plata:** datos limpios, deduplicados, con tipos correctos.
- **Oro:** datos modelados y pre-agregados, listos para consumo visual.
- El dashboard **solo se conecta a la capa Oro.**

### Modelado dimensional (Kimball)
Esquema Estrella: una tabla central de **Hechos** (transacciones/eventos) rodeada de tablas de **Dimensiones** (Tiempo, Persona, Región, Producto, etc.).

### Capa semántica centralizada
Las fórmulas de KPIs se definen **una sola vez** en la capa semántica, nunca en el gráfico. Esto garantiza una única fuente de verdad: el mismo cálculo en toda la organización.

### Rendimiento
Si el dataset es grande, crear vistas materializadas o tablas pre-agregadas (ej. ventas por mes y región). El dashboard debe cargar en milisegundos, no segundos.

### Estrategias de actualización
| Estrategia | Cuándo usarla |
|---|---|
| Batch (por lotes) | Reportes diarios/mensuales sin urgencia |
| Incremental | Datasets grandes que crecen continuamente |
| Streaming (tiempo real) | Operaciones críticas que requieren datos al instante |

---

## Fase 2 — Layout y estructura visual

### Principio de jerarquía (Shneiderman)
> "Vista general primero → zoom y filtro → detalles bajo demanda."

### Posicionamiento (Patrón F/Z)
En culturas occidentales la vista empieza en la esquina superior izquierda. Ahí van los **BANs (Big Ass Numbers):** los 2–3 KPIs más críticos del negocio.

### Pirámide Invertida
- **Superior:** estado actual (semáforos, BANs)
- **Medio:** tendencias y comparativas
- **Inferior:** detalle transaccional (drill-down)

### Límite cognitivo (Ley de Miller)
Máximo **5–7 elementos visuales** por vista. Si hay más, usar revelación progresiva (drill-down, pestañas, tooltips). El cerebro satura con más de 7 bloques simultáneos.

### Grid y espaciado
- Retícula de **12 columnas**
- Separaciones entre tarjetas: **16–24 px**
- Márgenes exteriores: **32–48 px**
- Sistema de 8 puntos para consistencia

---

## Fase 3 — Selección de gráficos

### Jerarquía de percepción (Cleveland & McGill)
El cerebro decodifica datos cuantitativos con esta precisión, de mayor a menor:

1. **Posición en escala común** — barras, puntos, scatter plots ✅ usar para datos críticos
2. **Posición en escalas no alineadas** — small multiples
3. **Longitud / dirección / ángulo** — barras apiladas, pie charts ⚠️ menor precisión
4. **Área** — burbujas, treemaps ⚠️ el cerebro subestima áreas
5. **Volumen / curvatura** — gráficos 3D ❌ evitar
6. **Sombreado / saturación de color** — mapas de calor ❌ solo para patrones globales, nunca para valores exactos

**Regla:** asignar los datos más importantes al canal perceptual más alto posible.

### Tabla de selección de gráfico por objetivo

| Objetivo | Gráfico recomendado | Prohibido |
|---|---|---|
| Comparar categorías | Barras horizontales (nombres largos) o columnas (nombres cortos), ordenadas de mayor a menor | Pie charts, donut charts, gauges |
| Evolución en el tiempo | Líneas | Barras para series continuas |
| Volumen acumulado | Áreas | — |
| Correlación entre variables | Scatter plot | — |
| Tres variables | Burbujas (con cautela por distorsión de área) | — |
| Distribución | Histograma (una variable) / Box plot (comparar distribuciones) | — |
| Cumplimiento de meta / progreso | Bullet chart o barra de progreso | Gauges, medidores circulares |
| Geografía — magnitudes exactas | Mapa de símbolos proporcionales (burbujas) | Mapas coropléticos para valores exactos |
| Geografía — tasas o densidades | Mapa coroplético (color) | — |

> "Guarda los pasteles para el postre." — Stephen Few. Nunca pie charts ni donut charts.

---

## Fase 4 — Data storytelling

Todo dashboard debe contar una historia con estructura:

### Estructura narrativa (Aristóteles aplicado a datos)
- **Inicio (Contexto):** vista general con KPIs principales. Responde "¿Qué está pasando?"
- **Nudo (Análisis):** tendencias, anomalías, comparativas. Responde "¿Por qué?"
- **Desenlace (Acción):** recomendación o llamado a la acción. Responde "¿Qué hacemos?"

### Títulos narrativos
Nunca títulos genéricos. El título comunica el hallazgo, no el contenido:
- ❌ "Ventas globales por región"
- ✅ "La región Norte supera la meta; Sur lleva 3 meses en rojo"

### Anotaciones ("Mostrar Y Contar")
No asumir que el gráfico se explica solo. Agregar texto breve en el gráfico para explicar picos, caídas o hitos:
- "Promoción de verano → +40% ventas"
- "Cambio de equipo en julio"

---

## Fase 5 — Color, accesibilidad y semáforos

### Regla base: nunca solo color
El **8% de los hombres** tiene daltonismo rojo-verde. El color siempre va acompañado de un icono o símbolo:

| Estado | Color | Icono obligatorio |
|---|---|---|
| Bueno / sobre meta | Verde | ✓ o ↑ |
| Atención / en riesgo | Amarillo | ⚠ |
| Crítico / bajo meta | Rojo | ✗ o ↓ |

### Paleta
- Rojo y verde **solo para alertas críticas.** El resto de gráficos usa tonos neutros o monocromáticos para no competir con las alertas.
- Contraste mínimo WCAG: **4.5:1** texto/fondo (3:1 para texto grande). Nunca gris claro sobre blanco.

### Data-Ink Ratio (Tufte)
Cada píxel debe comunicar datos. Eliminar:
- Efectos 3D (reducen comprensión hasta un 30%)
- Degradados y sombras decorativas
- Fondos y marcos pesados
- Líneas de cuadrícula excesivas
- Logos repetitivos

Preferir etiquetas de datos directas sobre las barras antes que ejes secundarios.

---

## Fase 6 — Honestidad visual (Lie Factor de Tufte)

Un gráfico honesto tiene **Lie Factor = 1.0** (efecto visual = efecto real en los datos).

Reglas para no engañar:
- **Eje Y siempre desde cero** en gráficos de barras. Truncar el eje exagera diferencias pequeñas.
- **No escalar dimensiones incorrectamente:** si un valor se duplica, solo duplicar el área matemáticamente, no el alto y el ancho (que cuadruplicaría el área).
- **Sin efectos 3D:** distorsionan la geometría. Un pie chart 3D hace que los sectores frontales parezcan más grandes.
- **Escalas consistentes:** no comprimir ni expandir arbitrariamente. Incluir comparativas temporales y métricas deflactadas si se habla de dinero.

---

## Fase 7 — Evaluación del dashboard

### Regla de los 5 segundos
El usuario debe responder su pregunta principal en **menos de 5–10 segundos**. Si tarda más, el diseño falló.

### Framework CARE
| Criterio | Pregunta |
|---|---|
| **C**laridad | ¿Es legible sin explicaciones externas? |
| **A**lineación | ¿Cada métrica se vincula a un objetivo de negocio? |
| **R**elevancia | ¿El usuario puede tomar una decisión con esto? |
| **E**jecución | ¿Existe un plan de acción ante desviaciones? |

### Métricas de UX
- **TSR (Tasa de Éxito de Tareas):** % de tareas críticas completadas sin errores.
- **TTV (Tiempo de Valor):** segundos hasta identificar una anomalía tras abrir el panel.
- **Tasa de adopción:** eliminar el 20% de widgets menos usados en cada iteración.

### Densidad (Tufte)
Usar sparklines para mostrar tendencias de forma compacta. "Algo poderoso ocurre cuando la información se ve junta, al mismo tiempo."

---

## Elección de herramienta

| Herramienta | Mejor para | Considerar si... |
|---|---|---|
| **Power BI** | Ecosistema Microsoft, transformación de datos potente (Power Query), costo bajo | El equipo ya usa Office 365 |
| **Tableau** | Visualizaciones exploratorias de alta calidad, comunidad grande | Se priorizan gráficos complejos y análisis ad-hoc |
| **Looker Studio** | Gratuito, integración nativa con Google Analytics, BigQuery, Sheets | El ecosistema es Google |
| **Python** (Matplotlib, Seaborn, Plotly) | Control total, reproducibilidad, integración con pipelines de datos | El equipo es técnico y necesita automatización |
| **D3.js** | Visualizaciones web personalizadas con máximo control visual | Se requiere algo que ninguna herramienta BI ofrece; curva empinada |

---

## Autores y frameworks de referencia

| Autor | Contribución clave |
|---|---|
| **Edward Tufte** | Data-Ink Ratio, Chartjunk, Lie Factor |
| **Ben Shneiderman** | "Overview first, zoom, details-on-demand"; Ley de Miller aplicada a UX |
| **Tamara Munzner** | Nested Model (4 niveles: dominio → abstracción → codificación → algoritmos) |
| **Alberto Cairo** | "El Arte Funcional": la función restringe la forma; visualización como tecnología cognitiva |
| **Cleveland & McGill** | Jerarquía de percepción gráfica (posición > longitud > ángulo > área > color) |
| **Jacques Bertin** | Variables visuales (posición, tamaño, valor, textura, color, orientación, forma) |
| **Stephen Few** | Diseño de dashboards BI, crítica al abuso de pie charts |
| **Ralph Kimball** | Modelado dimensional, Esquema Estrella |
