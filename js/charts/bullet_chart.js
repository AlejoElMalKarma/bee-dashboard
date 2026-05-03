/**
 * VIZ-3 — Comparación por Región (Revenue vs Target)
 * Bullet Chart horizontal: barra de revenue + marca de target
 * Ordenado por revenue descendente
 */

(function () {
  'use strict';

  window.Charts = window.Charts || {};

  window.Charts.bulletChart = function init(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Agregar por región
    const regionMap = {};
    data.records.forEach(r => {
      if (!regionMap[r.region]) {
        regionMap[r.region] = { region: r.region, revenue: 0, target: 0, kpi_meta_vals: [], statuses: [] };
      }
      regionMap[r.region].revenue += r.revenue;
      regionMap[r.region].target  += r.target;
      regionMap[r.region].kpi_meta_vals.push(r.kpi_meta);
      regionMap[r.region].statuses.push(r.kpi_meta_status);
    });

    const regionData = Object.values(regionMap).map(r => {
      const kpiMeta = d3.mean(r.kpi_meta_vals);
      const status = kpiMeta >= 100 ? 'green' : kpiMeta >= 80 ? 'yellow' : 'red';
      return { ...r, kpi_meta_mean: kpiMeta, status };
    }).sort((a, b) => b.revenue - a.revenue);

    const statusColors = { green: '#10b981', yellow: '#f59e0b', red: '#ef4444' };
    const statusBg     = { green: '#dcfce7', yellow: '#fef3c7', red: '#fee2e2' };
    const statusIcons  = { green: '✓', yellow: '⚠', red: '✗' };

    const margin = { top: 16, right: 90, bottom: 36, left: 72 };
    const w = container.clientWidth || 420;
    const rowH = 38;
    const totalH = margin.top + regionData.length * rowH + margin.bottom;
    const innerW = w - margin.left - margin.right;
    const maxVal = Math.ceil(d3.max(regionData, d => Math.max(d.revenue, d.target)) / 1e5) * 1e5;

    container.innerHTML = '';
    const svg = d3.select(container)
      .append('svg')
      .attr('class', 'chart-svg')
      .attr('role', 'img')
      .attr('aria-label', 'Bullet chart de revenue vs target por región')
      .attr('width', '100%')
      .attr('height', totalH)
      .attr('viewBox', `0 0 ${w} ${totalH}`);

    const xScale = d3.scaleLinear().domain([0, maxVal]).range([0, innerW]);
    const yScale = d3.scaleBand()
      .domain(regionData.map(d => d.region))
      .range([0, regionData.length * rowH])
      .padding(0.2);

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    // Eje X
    g.append('g').attr('transform', `translate(0,${regionData.length * rowH})`).call(
      d3.axisBottom(xScale)
        .ticks(5)
        .tickFormat(d => d >= 1e6 ? `$${d / 1e6}M` : `$${d / 1000}K`)
        .tickSize(4)
    ).call(ax => ax.select('.domain').remove())
      .selectAll('text').attr('font-size', '10px');

    // Gridlines verticales
    const gridG = g.append('g').attr('class', 'grid')
      .attr('transform', `translate(0,${regionData.length * rowH})`);
    gridG.call(
      d3.axisBottom(xScale).ticks(5).tickSize(-regionData.length * rowH).tickFormat('')
    ).call(ax => ax.select('.domain').remove());

    // Eje Y (nombres de región)
    g.append('g').call(
      d3.axisLeft(yScale).tickSize(0)
    ).call(ax => {
      ax.select('.domain').remove();
      ax.selectAll('text')
        .attr('x', -8)
        .attr('font-size', '12px')
        .attr('font-weight', '500')
        .attr('fill', '#374151');
    });

    // Filas de datos
    regionData.forEach(d => {
      const y   = yScale(d.region);
      const bh  = yScale.bandwidth();
      const bx  = xScale(d.revenue);
      const tx  = xScale(d.target);
      const midY = y + bh / 2;

      // Fondo suave
      g.append('rect')
        .attr('x', 0).attr('y', y)
        .attr('width', innerW).attr('height', bh)
        .attr('fill', statusBg[d.status]).attr('rx', 3).attr('opacity', 0.25);

      // Barra de revenue
      g.append('rect')
        .attr('x', 0).attr('y', y + bh * 0.18)
        .attr('width', Math.max(0, bx))
        .attr('height', bh * 0.64)
        .attr('fill', statusColors[d.status])
        .attr('rx', 2)
        .attr('opacity', 0.85);

      // Marca de target (línea vertical negra)
      g.append('line')
        .attr('x1', tx).attr('x2', tx)
        .attr('y1', y + 2).attr('y2', y + bh - 2)
        .attr('stroke', '#1f2937')
        .attr('stroke-width', 2)
        .attr('stroke-linecap', 'round');

      // Etiqueta revenue al final de la barra
      g.append('text')
        .attr('x', bx + 4)
        .attr('y', midY + 4)
        .attr('font-size', '11px')
        .attr('font-weight', '600')
        .attr('fill', '#374151')
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .text(`$${(d.revenue / 1000).toFixed(0)}K`);

      // Icono + KPI meta bajo el nombre de región
      g.append('text')
        .attr('x', -8).attr('y', y + bh + 2)
        .attr('text-anchor', 'end')
        .attr('font-size', '9px')
        .attr('fill', statusColors[d.status])
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .text(`${statusIcons[d.status]} ${d.kpi_meta_mean.toFixed(0)}%`);
    });

    // Leyenda de target
    const leg = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${totalH - 14})`);
    leg.append('line')
      .attr('x1', 0).attr('x2', 12).attr('y1', 0).attr('y2', 0)
      .attr('stroke', '#1f2937').attr('stroke-width', 2);
    leg.append('text')
      .attr('x', 16).attr('y', 4)
      .attr('font-size', '10px').attr('fill', '#6b7280')
      .attr('font-family', "'Inter', system-ui, sans-serif")
      .text('= Target asignado');
  };
})();
