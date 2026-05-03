/**
 * VIZ-6 — Scatter Plot: Leads vs Conversión (Eficiencia comercial)
 * Posición XY (leads vs kpi_conversion) + tamaño (revenue) + color (rep_name)
 * Línea de regresión OLS + registros críticos con contorno rojo
 */

(function () {
  'use strict';

  window.Charts = window.Charts || {};

  function getTooltip() {
    let el = document.getElementById('global-tooltip');
    if (!el) {
      el = document.createElement('div');
      el.id = 'global-tooltip';
      el.className = 'd3-tooltip';
      document.body.appendChild(el);
    }
    return {
      show(event, html) {
        el.innerHTML = html;
        el.classList.add('visible');
        this.move(event);
      },
      move(event) {
        const offset = 14;
        let left = event.clientX + offset;
        let top  = event.clientY + offset;
        if (left + 270 > window.innerWidth)  left = event.clientX - 270 - offset;
        if (top  + 220 > window.innerHeight) top  = event.clientY - 220 - offset;
        el.style.left = left + 'px';
        el.style.top  = top  + 'px';
      },
      hide() { el.classList.remove('visible'); },
    };
  }

  window.Charts.scatter = function init(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const records = data.records;

    // Paleta Okabe-Ito (accesible para daltonismo) — 5 representantes
    const repNames = ['Ana Martínez', 'Carlos Ruiz', 'Laura Gómez', 'Miguel Torres', 'Sofía Herrera'];
    const okabeIto = ['#0072b2', '#e69f00', '#009e73', '#cc79a7', '#56b4e9'];
    const colorScale = d3.scaleOrdinal().domain(repNames).range(okabeIto);

    const margin = { top: 20, right: 156, bottom: 52, left: 56 };
    const w = container.clientWidth || 940;
    const h = 300;
    const innerW = w - margin.left - margin.right;
    const innerH = h - margin.top - margin.bottom;

    container.innerHTML = '';
    const svg = d3.select(container)
      .append('svg')
      .attr('class', 'chart-svg')
      .attr('role', 'img')
      .attr('aria-label', 'Scatter plot de leads vs tasa de conversión por representante')
      .attr('width', '100%')
      .attr('height', h)
      .attr('viewBox', `0 0 ${w} ${h}`);

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    // Escalas
    const xScale = d3.scaleLinear().domain([0, 120]).range([0, innerW]).nice();
    const yScale = d3.scaleLinear().domain([0, 45]).range([innerH, 0]).nice();
    const rScale = d3.scaleSqrt()
      .domain(d3.extent(records, d => d.revenue))
      .range([6, 18]);

    // Gridlines
    g.append('g').attr('class', 'grid').call(
      d3.axisLeft(yScale).tickSize(-innerW).tickFormat('')
    ).call(ax => ax.select('.domain').remove());

    g.append('g').attr('class', 'grid')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(xScale).ticks(6).tickSize(-innerH).tickFormat(''))
      .call(ax => ax.select('.domain').remove());

    // Línea benchmark 25% (verde)
    g.append('line')
      .attr('x1', 0).attr('x2', innerW)
      .attr('y1', yScale(25)).attr('y2', yScale(25))
      .attr('stroke', '#10b981').attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '6,4').attr('opacity', 0.7);
    g.append('text')
      .attr('x', 3).attr('y', yScale(25) - 4)
      .attr('font-size', '9px').attr('fill', '#10b981')
      .attr('font-family', "'Inter', system-ui, sans-serif")
      .text('25% benchmark');

    // Línea umbral 15% (rojo)
    g.append('line')
      .attr('x1', 0).attr('x2', innerW)
      .attr('y1', yScale(15)).attr('y2', yScale(15))
      .attr('stroke', '#ef4444').attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,3').attr('opacity', 0.5);
    g.append('text')
      .attr('x', 3).attr('y', yScale(15) - 4)
      .attr('font-size', '9px').attr('fill', '#ef4444')
      .attr('font-family', "'Inter', system-ui, sans-serif")
      .text('15% umbral crítico');

    // Ejes
    g.append('g').attr('transform', `translate(0,${innerH})`).call(
      d3.axisBottom(xScale).ticks(6).tickSize(4)
    ).call(ax => ax.select('.domain').remove())
      .selectAll('text').attr('font-size', '10px');

    g.append('g').call(
      d3.axisLeft(yScale).ticks(6).tickSize(4).tickFormat(d => d + '%')
    ).call(ax => ax.select('.domain').remove())
      .selectAll('text').attr('font-size', '10px');

    // Etiquetas de eje
    g.append('text')
      .attr('x', innerW / 2).attr('y', innerH + 38)
      .attr('text-anchor', 'middle').attr('font-size', '11px').attr('fill', '#6b7280')
      .attr('font-family', "'Inter', system-ui, sans-serif")
      .text('Número de Leads');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerH / 2).attr('y', -42)
      .attr('text-anchor', 'middle').attr('font-size', '11px').attr('fill', '#6b7280')
      .attr('font-family', "'Inter', system-ui, sans-serif")
      .text('Tasa de Conversión (%)');

    // Regresión OLS
    const xVals = records.map(d => d.leads);
    const yVals = records.map(d => d.kpi_conversion);
    const n  = xVals.length;
    const mx = d3.mean(xVals);
    const my = d3.mean(yVals);
    const slope = d3.sum(xVals.map((x, i) => (x - mx) * (yVals[i] - my))) /
                  d3.sum(xVals.map(x => (x - mx) ** 2));
    const intercept = my - slope * mx;

    g.append('line')
      .attr('x1', xScale(0)).attr('x2', xScale(120))
      .attr('y1', yScale(intercept)).attr('y2', yScale(intercept + slope * 120))
      .attr('stroke', '#9ca3af').attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '8,5').attr('opacity', 0.5);

    const ssXY = d3.sum(xVals.map((x, i) => (x - mx) * (yVals[i] - my)));
    const ssX  = d3.sum(xVals.map(x => (x - mx) ** 2));
    const ssY  = d3.sum(yVals.map(y => (y - my) ** 2));
    const pearsonR  = ssXY / Math.sqrt(ssX * ssY);
    const rSign     = pearsonR >= 0 ? '+' : '';

    g.append('text')
      .attr('x', xScale(112)).attr('y', yScale(intercept + slope * 112) - 6)
      .attr('text-anchor', 'end').attr('font-size', '9px').attr('fill', '#6b7280')
      .attr('font-family', "'Inter', system-ui, sans-serif")
      .text(`OLS r≈${rSign}${pearsonR.toFixed(2)}`);

    // Tooltip
    const tooltip = getTooltip();

    // Ordenar: no críticos primero, críticos encima
    const sorted = [...records].sort((a, b) => {
      const aC = a.kpi_meta_status === 'red' ? 1 : 0;
      const bC = b.kpi_meta_status === 'red' ? 1 : 0;
      return aC - bC;
    });

    sorted.forEach(d => {
      const cx = xScale(d.leads);
      const cy = yScale(d.kpi_conversion);
      const r  = rScale(d.revenue);
      const isCrit = d.kpi_meta_status === 'red';

      const circle = g.append('circle')
        .attr('cx', cx).attr('cy', cy).attr('r', r)
        .attr('fill', colorScale(d.rep_name))
        .attr('opacity', 0.82)
        .attr('stroke', isCrit ? '#b91c1c' : '#fff')
        .attr('stroke-width', isCrit ? 2.5 : 1.5)
        .style('cursor', 'pointer');

      circle
        .on('mouseover', function(event) {
          tooltip.show(event, `
            <strong>${d.id} — ${d.rep_name}</strong>
            <div class="tooltip-row"><span>Leads</span><span class="tooltip-val">${d.leads}</span></div>
            <div class="tooltip-row"><span>KPI Conv</span><span class="tooltip-val">${d.kpi_conversion.toFixed(1)}%</span></div>
            <div class="tooltip-row"><span>KPI Meta</span><span class="tooltip-val">${d.kpi_meta.toFixed(1)}%</span></div>
            <div class="tooltip-row"><span>Revenue</span><span class="tooltip-val">$${(d.revenue/1000).toFixed(0)}K</span></div>
            <div class="tooltip-row"><span>Período</span><span class="tooltip-val">${d.period}</span></div>
          `);
          d3.select(this).attr('opacity', 1).attr('r', r + 2);
        })
        .on('mousemove', function(event) { tooltip.move(event); })
        .on('mouseout', function() {
          tooltip.hide();
          d3.select(this).attr('opacity', 0.82).attr('r', r);
        });

      // Etiqueta solo para críticos
      if (isCrit) {
        g.append('text')
          .attr('x', cx + r + 3).attr('y', cy - 3)
          .attr('font-size', '9px').attr('font-weight', '600')
          .attr('fill', '#b91c1c')
          .attr('font-family', "'Inter', system-ui, sans-serif")
          .text(d.id);
      }
    });

    // Leyenda de representantes (margen derecho)
    const legG = svg.append('g')
      .attr('class', 'scatter-legend')
      .attr('transform', `translate(${margin.left + innerW + 14}, ${margin.top + 8})`);

    legG.append('text')
      .attr('y', -6).attr('font-size', '10px').attr('font-weight', '600')
      .attr('fill', '#6b7280').attr('font-family', "'Inter', system-ui, sans-serif")
      .text('Representante');

    repNames.forEach((rep, i) => {
      const ly = i * 22;
      legG.append('circle')
        .attr('cx', 7).attr('cy', ly + 10)
        .attr('r', 7).attr('fill', colorScale(rep)).attr('opacity', 0.9);
      legG.append('text')
        .attr('x', 18).attr('y', ly + 14)
        .attr('font-size', '10px').attr('fill', '#374151')
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .text(rep.split(' ')[0]);
    });

    // Indicador de crítico
    const critY = repNames.length * 22 + 14;
    legG.append('circle')
      .attr('cx', 7).attr('cy', critY + 10)
      .attr('r', 7).attr('fill', '#d1d5db')
      .attr('stroke', '#b91c1c').attr('stroke-width', 2.5);
    legG.append('text')
      .attr('x', 18).attr('y', critY + 14)
      .attr('font-size', '10px').attr('fill', '#b91c1c')
      .attr('font-family', "'Inter', system-ui, sans-serif")
      .text('Crítico');
  };
})();
