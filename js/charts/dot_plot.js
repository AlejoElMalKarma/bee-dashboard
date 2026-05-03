/**
 * VIZ-2 — Rendimiento por Representante (Doble KPI)
 * Dot Plot horizontal con dos paneles: KPI Meta y KPI Conversión
 * Ordenados por kpi_meta descendente (Laura Gómez arriba)
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
        if (left + 260 > window.innerWidth)  left = event.clientX - 260 - offset;
        if (top  + 180 > window.innerHeight) top  = event.clientY - 180 - offset;
        el.style.left = left + 'px';
        el.style.top  = top  + 'px';
      },
      hide() { el.classList.remove('visible'); },
    };
  }

  window.Charts.dotPlot = function init(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Agregar datos por representante
    const repMap = {};
    data.records.forEach(r => {
      if (!repMap[r.rep_name]) {
        repMap[r.rep_name] = {
          rep_name: r.rep_name,
          region: r.region,
          kpi_meta_vals: [],
          kpi_conv_vals: [],
          revenue_vals: [],
          statuses: [],
        };
      }
      repMap[r.rep_name].kpi_meta_vals.push(r.kpi_meta);
      repMap[r.rep_name].kpi_conv_vals.push(r.kpi_conversion);
      repMap[r.rep_name].revenue_vals.push(r.revenue);
      repMap[r.rep_name].statuses.push(r.kpi_meta_status);
    });

    const repData = Object.values(repMap).map(rep => {
      const metaMean = d3.mean(rep.kpi_meta_vals);
      const convMean = d3.mean(rep.kpi_conv_vals);
      const revTotal = d3.sum(rep.revenue_vals);
      const status = metaMean >= 100 ? 'green' : metaMean >= 80 ? 'yellow' : 'red';
      return { rep_name: rep.rep_name, region: rep.region, kpi_meta_mean: metaMean, kpi_conversion_mean: convMean, revenue_total: revTotal, status };
    }).sort((a, b) => b.kpi_meta_mean - a.kpi_meta_mean);

    const statusColors = { green: '#10b981', yellow: '#f59e0b', red: '#ef4444' };

    const margin = { top: 32, right: 64, bottom: 28, left: 110 };
    const w = container.clientWidth || 360;
    const panelH  = 130;
    const panelGap = 40;
    const totalH = margin.top + panelH + panelGap + panelH + margin.bottom;

    container.innerHTML = '';
    const svg = d3.select(container)
      .append('svg')
      .attr('class', 'chart-svg')
      .attr('role', 'img')
      .attr('aria-label', 'Dot plot de KPI Meta y KPI Conversión promedio por representante')
      .attr('width', '100%')
      .attr('height', totalH)
      .attr('viewBox', `0 0 ${w} ${totalH}`);

    const innerW = w - margin.left - margin.right;

    const yScale = d3.scaleBand()
      .domain(repData.map(d => d.rep_name))
      .range([0, panelH])
      .padding(0.4);

    // Radio de punto proporcional a revenue (escala raíz cuadrada)
    const rScale = d3.scaleSqrt()
      .domain(d3.extent(repData, d => d.revenue_total))
      .range([6, 14]);

    const tooltip = getTooltip();

    // ── Panel 1: KPI Meta ─────────────────────────────────────
    const xMeta = d3.scaleLinear().domain([40, 135]).range([0, innerW]);
    const g1 = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    g1.append('text')
      .attr('x', innerW / 2).attr('y', -18)
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px').attr('font-weight', '600')
      .attr('fill', '#6b7280')
      .attr('font-family', "'Inter', system-ui, sans-serif")
      .text('KPI META (%) — benchmark 100%');

    const metaTicks = [60, 80, 100, 120];
    // Grid
    metaTicks.forEach(t => {
      g1.append('line')
        .attr('x1', xMeta(t)).attr('x2', xMeta(t))
        .attr('y1', 0).attr('y2', panelH)
        .attr('stroke', t === 100 ? '#10b981' : '#e5e7eb')
        .attr('stroke-width', t === 100 ? 1.5 : 1)
        .attr('stroke-dasharray', t === 100 ? '0' : '3,3');
    });

    // Ref rojo 80%
    g1.append('line')
      .attr('x1', xMeta(80)).attr('x2', xMeta(80))
      .attr('y1', 0).attr('y2', panelH)
      .attr('stroke', '#ef4444').attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,3').attr('opacity', 0.5);

    // Eje X
    g1.append('g').attr('transform', `translate(0,${panelH})`).call(
      d3.axisBottom(xMeta).tickValues(metaTicks).tickFormat(d => d + '%').tickSize(3)
    ).call(g => g.select('.domain').remove())
      .selectAll('text').attr('font-size', '10px');

    // Eje Y
    g1.append('g').call(
      d3.axisLeft(yScale).tickSize(0)
    ).call(g => {
      g.select('.domain').remove();
      g.selectAll('text').attr('x', -8).attr('font-size', '11px').attr('fill', '#374151');
    });

    repData.forEach(d => {
      const cx = xMeta(d.kpi_meta_mean);
      const cy = yScale(d.rep_name) + yScale.bandwidth() / 2;
      const r  = rScale(d.revenue_total);

      g1.append('circle')
        .attr('cx', cx).attr('cy', cy).attr('r', r)
        .attr('fill', statusColors[d.status])
        .attr('opacity', 0.9)
        .attr('stroke', '#fff').attr('stroke-width', 1.5)
        .style('cursor', 'pointer')
        .on('mouseover', function(event) {
          tooltip.show(event, `
            <strong>${d.rep_name} — ${d.region}</strong>
            <div class="tooltip-row"><span>KPI Meta</span><span class="tooltip-val">${d.kpi_meta_mean.toFixed(1)}%</span></div>
            <div class="tooltip-row"><span>KPI Conv</span><span class="tooltip-val">${d.kpi_conversion_mean.toFixed(1)}%</span></div>
            <div class="tooltip-row"><span>Revenue</span><span class="tooltip-val">$${(d.revenue_total/1000).toFixed(0)}K</span></div>
          `);
        })
        .on('mousemove', function(event) { tooltip.move(event); })
        .on('mouseout', function() { tooltip.hide(); });

      g1.append('text')
        .attr('x', cx + r + 4).attr('y', cy + 4)
        .attr('font-size', '11px').attr('font-weight', '600')
        .attr('fill', statusColors[d.status])
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .text(d.kpi_meta_mean.toFixed(1) + '%');
    });

    // ── Panel 2: KPI Conversión ───────────────────────────────
    const xConv = d3.scaleLinear().domain([10, 42]).range([0, innerW]);
    const g2 = svg.append('g').attr('transform', `translate(${margin.left},${margin.top + panelH + panelGap})`);

    g2.append('text')
      .attr('x', innerW / 2).attr('y', -18)
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px').attr('font-weight', '600')
      .attr('fill', '#6b7280')
      .attr('font-family', "'Inter', system-ui, sans-serif")
      .text('KPI CONVERSIÓN (%) — benchmark 25%');

    const convTicks = [15, 20, 25, 30, 35, 40];
    convTicks.forEach(t => {
      g2.append('line')
        .attr('x1', xConv(t)).attr('x2', xConv(t))
        .attr('y1', 0).attr('y2', panelH)
        .attr('stroke', t === 25 ? '#10b981' : '#e5e7eb')
        .attr('stroke-width', t === 25 ? 1.5 : 1)
        .attr('stroke-dasharray', t === 25 ? '0' : '3,3');
    });

    // Ref rojo 15%
    g2.append('line')
      .attr('x1', xConv(15)).attr('x2', xConv(15))
      .attr('y1', 0).attr('y2', panelH)
      .attr('stroke', '#ef4444').attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,3').attr('opacity', 0.5);

    g2.append('g').attr('transform', `translate(0,${panelH})`).call(
      d3.axisBottom(xConv).tickValues(convTicks).tickFormat(d => d + '%').tickSize(3)
    ).call(g => g.select('.domain').remove())
      .selectAll('text').attr('font-size', '10px');

    g2.append('g').call(
      d3.axisLeft(yScale).tickSize(0)
    ).call(g => {
      g.select('.domain').remove();
      g.selectAll('text').attr('x', -8).attr('font-size', '11px').attr('fill', '#374151');
    });

    repData.forEach(d => {
      const cx = xConv(d.kpi_conversion_mean);
      const cy = yScale(d.rep_name) + yScale.bandwidth() / 2;
      const r  = rScale(d.revenue_total);
      const convStatus = d.kpi_conversion_mean >= 25 ? 'green' : d.kpi_conversion_mean >= 15 ? 'yellow' : 'red';

      g2.append('circle')
        .attr('cx', cx).attr('cy', cy).attr('r', r)
        .attr('fill', statusColors[convStatus])
        .attr('opacity', 0.9)
        .attr('stroke', '#fff').attr('stroke-width', 1.5)
        .style('cursor', 'pointer')
        .on('mouseover', function(event) {
          tooltip.show(event, `
            <strong>${d.rep_name} — ${d.region}</strong>
            <div class="tooltip-row"><span>KPI Conv</span><span class="tooltip-val">${d.kpi_conversion_mean.toFixed(1)}%</span></div>
            <div class="tooltip-row"><span>KPI Meta</span><span class="tooltip-val">${d.kpi_meta_mean.toFixed(1)}%</span></div>
            <div class="tooltip-row"><span>Revenue</span><span class="tooltip-val">$${(d.revenue_total/1000).toFixed(0)}K</span></div>
          `);
        })
        .on('mousemove', function(event) { tooltip.move(event); })
        .on('mouseout', function() { tooltip.hide(); });

      g2.append('text')
        .attr('x', cx + r + 4).attr('y', cy + 4)
        .attr('font-size', '11px').attr('font-weight', '600')
        .attr('fill', statusColors[convStatus])
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .text(d.kpi_conversion_mean.toFixed(1) + '%');
    });
  };
})();
