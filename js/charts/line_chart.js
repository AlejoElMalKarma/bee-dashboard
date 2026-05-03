/**
 * VIZ-4 — Evolución Trimestral del KPI de Meta
 * Line chart de doble eje: kpi_meta (izq, azul) + kpi_conversion (der, violeta)
 * 4 puntos en eje X ordinal Q1–Q4
 */

(function () {
  'use strict';

  window.Charts = window.Charts || {};

  window.Charts.lineChart = function init(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Agregar por trimestre desde datos crudos
    const quarterMap = {};
    data.records.forEach(r => {
      if (!quarterMap[r.quarter]) {
        quarterMap[r.quarter] = { quarter: r.quarter, kpi_meta_vals: [], kpi_conv_vals: [], count: 0 };
      }
      quarterMap[r.quarter].kpi_meta_vals.push(r.kpi_meta);
      quarterMap[r.quarter].kpi_conv_vals.push(r.kpi_conversion);
      quarterMap[r.quarter].count++;
    });

    const qOrder  = ['Q1', 'Q2', 'Q3', 'Q4'];
    const qLabels = { Q1: 'Ene–Mar', Q2: 'Abr–Jun', Q3: 'Jul–Sep', Q4: 'Oct–Dic' };
    const qData   = qOrder.map(q => ({
      quarter: q,
      label: qLabels[q],
      kpi_meta_mean: d3.mean(quarterMap[q] ? quarterMap[q].kpi_meta_vals : [0]),
      kpi_conv_mean: d3.mean(quarterMap[q] ? quarterMap[q].kpi_conv_vals : [0]),
      records: quarterMap[q] ? quarterMap[q].count : 0,
    }));

    const margin = { top: 32, right: 68, bottom: 56, left: 52 };
    const w = container.clientWidth || 560;
    const h = 280;
    const innerW = w - margin.left - margin.right;
    const innerH = h - margin.top - margin.bottom;

    container.innerHTML = '';
    const svg = d3.select(container)
      .append('svg')
      .attr('class', 'chart-svg')
      .attr('role', 'img')
      .attr('aria-label', 'Línea de evolución trimestral de KPI Meta y KPI Conversión')
      .attr('width', '100%')
      .attr('height', h)
      .attr('viewBox', `0 0 ${w} ${h}`);

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    // Escalas
    const xScale = d3.scalePoint().domain(qOrder).range([0, innerW]).padding(0.35);
    const yLeft  = d3.scaleLinear().domain([80, 115]).range([innerH, 0]);
    const yRight = d3.scaleLinear().domain([20, 35]).range([innerH, 0]);

    // Zona verde (kpi_meta >= 100) — franja de fondo
    const y100 = yLeft(100);
    g.append('rect')
      .attr('x', 0).attr('y', 0)
      .attr('width', innerW).attr('height', y100)
      .attr('fill', '#dcfce7').attr('opacity', 0.35);

    // Eje X
    g.append('g').attr('transform', `translate(0,${innerH})`).call(
      d3.axisBottom(xScale).tickSize(0)
    ).call(ax => {
      ax.select('.domain').remove();
      ax.selectAll('text').attr('y', 10).attr('font-size', '12px').attr('font-weight', '600');
    });

    // Etiquetas de meses (fila secundaria)
    qData.forEach(d => {
      g.append('text')
        .attr('x', xScale(d.quarter))
        .attr('y', innerH + 30)
        .attr('text-anchor', 'middle')
        .attr('font-size', '9px')
        .attr('fill', '#6b7280')
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .text(d.label);
    });

    // Eje Y izquierdo (azul)
    g.append('g').call(
      d3.axisLeft(yLeft).ticks(5).tickFormat(d => d + '%').tickSize(3)
    ).call(ax => ax.select('.domain').remove())
      .selectAll('text').attr('font-size', '10px').attr('fill', '#3b82f6');

    // Eje Y derecho (violeta)
    g.append('g').attr('transform', `translate(${innerW},0)`).call(
      d3.axisRight(yRight).ticks(5).tickFormat(d => d + '%').tickSize(3)
    ).call(ax => ax.select('.domain').remove())
      .selectAll('text').attr('font-size', '10px').attr('fill', '#8b5cf6');

    // Benchmark 100% meta (línea verde horizontal)
    g.append('line')
      .attr('x1', 0).attr('x2', innerW)
      .attr('y1', yLeft(100)).attr('y2', yLeft(100))
      .attr('stroke', '#10b981').attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '5,4').attr('opacity', 0.7);

    g.append('text')
      .attr('x', 3).attr('y', yLeft(100) - 5)
      .attr('font-size', '9px').attr('fill', '#10b981')
      .attr('font-family', "'Inter', system-ui, sans-serif")
      .text('100% meta');

    // Benchmark 25% conversión
    g.append('line')
      .attr('x1', 0).attr('x2', innerW)
      .attr('y1', yRight(25)).attr('y2', yRight(25))
      .attr('stroke', '#8b5cf6').attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,3').attr('opacity', 0.4);

    // Línea KPI Meta (azul)
    const lineMeta = d3.line()
      .x(d => xScale(d.quarter))
      .y(d => yLeft(d.kpi_meta_mean))
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(qData)
      .attr('fill', 'none')
      .attr('stroke', '#3b82f6')
      .attr('stroke-width', 2.5)
      .attr('d', lineMeta);

    // Línea KPI Conversión (violeta punteada)
    const lineConv = d3.line()
      .x(d => xScale(d.quarter))
      .y(d => yRight(d.kpi_conv_mean))
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(qData)
      .attr('fill', 'none')
      .attr('stroke', '#8b5cf6')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '5,4')
      .attr('d', lineConv);

    // Puntos KPI Meta
    const rScale = d3.scaleSqrt().domain([0, 8]).range([0, 9]);

    qData.forEach(d => {
      const cx = xScale(d.quarter);
      const cy = yLeft(d.kpi_meta_mean);
      const r  = Math.max(5, rScale(d.records));

      g.append('circle')
        .attr('cx', cx).attr('cy', cy).attr('r', r)
        .attr('fill', '#3b82f6').attr('stroke', '#fff').attr('stroke-width', 1.5);

      g.append('text')
        .attr('x', cx).attr('y', cy - r - 5)
        .attr('text-anchor', 'middle')
        .attr('font-size', '11px').attr('font-weight', '600').attr('fill', '#3b82f6')
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .text(d.kpi_meta_mean.toFixed(1) + '%');
    });

    // Puntos KPI Conversión
    qData.forEach(d => {
      const cx = xScale(d.quarter);
      const cy = yRight(d.kpi_conv_mean);

      g.append('circle')
        .attr('cx', cx).attr('cy', cy).attr('r', 4)
        .attr('fill', '#8b5cf6').attr('stroke', '#fff').attr('stroke-width', 1.5);

      g.append('text')
        .attr('x', cx).attr('y', cy + 16)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px').attr('font-weight', '600').attr('fill', '#8b5cf6')
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .text(d.kpi_conv_mean.toFixed(1) + '%');
    });

    // Anotación "Mejor trimestre" en Q3
    const q3 = qData.find(d => d.quarter === 'Q3');
    if (q3) {
      const ax = xScale('Q3');
      const ay = yLeft(q3.kpi_meta_mean);
      g.append('text')
        .attr('x', ax + 8).attr('y', ay - 18)
        .attr('font-size', '10px').attr('font-weight', '600')
        .attr('fill', '#15803d')
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .text('Mejor trimestre');
      g.append('line')
        .attr('x1', ax).attr('x2', ax)
        .attr('y1', ay - 14).attr('y2', ay - 8)
        .attr('stroke', '#15803d').attr('stroke-width', 1)
        .attr('stroke-dasharray', '2,2');
    }

    // Leyenda
    const legY = innerH + 46;
    const legItems = [
      { color: '#3b82f6', label: 'KPI Meta %', dash: '' },
      { color: '#8b5cf6', label: 'KPI Conversión %', dash: '5,4' },
    ];
    let lx = 0;
    legItems.forEach(item => {
      g.append('line')
        .attr('x1', lx).attr('x2', lx + 20).attr('y1', legY).attr('y2', legY)
        .attr('stroke', item.color).attr('stroke-width', 2)
        .attr('stroke-dasharray', item.dash);
      g.append('text')
        .attr('x', lx + 24).attr('y', legY + 4)
        .attr('font-size', '10px').attr('fill', '#6b7280')
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .text(item.label);
      lx += 130;
    });
  };
})();
