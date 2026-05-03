/**
 * VIZ-5 — Semáforo de Registros por Representante × Mes
 * Heatmap 5 representantes × 12 meses
 * 3 canales: color de fondo (kpi_meta_status), símbolo (kpi_conversion_status), número (kpi_meta)
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
        if (top  + 200 > window.innerHeight) top  = event.clientY - 200 - offset;
        el.style.left = left + 'px';
        el.style.top  = top  + 'px';
      },
      hide() { el.classList.remove('visible'); },
    };
  }

  window.Charts.heatmap = function init(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const records = data.records;

    // Construir índice rep×mes
    const dataMap = {};
    records.forEach(r => {
      dataMap[r.rep_name + '__' + r.period] = r;
    });

    const repOrder = ['Laura Gómez', 'Ana Martínez', 'Miguel Torres', 'Sofía Herrera', 'Carlos Ruiz'];
    const months = [];
    for (let i = 1; i <= 12; i++) {
      months.push('2025-' + String(i).padStart(2, '0'));
    }
    const monthLabels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

    const metaBg     = { green: '#dcfce7', yellow: '#fef3c7', red: '#fee2e2', null: '#f3f4f6' };
    const convSymbol = { green: '✓', yellow: '⚠', red: '✕' };
    const convColor  = { green: '#15803d', yellow: '#b45309', red: '#b91c1c' };

    const cellW  = 42;
    const cellH  = 38;
    const colGap = 4;
    const rowH   = cellH + 5;
    const marginTop    = 52;
    const marginLeft   = 106;
    const marginRight  = 12;
    const marginBottom = 20;

    function colX(i) {
      return marginLeft + i * cellW + Math.floor(i / 3) * colGap;
    }

    const totalW = colX(12) + marginRight;
    const totalH = marginTop + repOrder.length * rowH + marginBottom;

    const tooltip = getTooltip();

    container.innerHTML = '';

    // Leyenda
    const legendDiv = document.createElement('div');
    legendDiv.className = 'heatmap-legend';
    legendDiv.innerHTML = `
      <span style="font-size:10px;font-weight:600;color:#6b7280;">Fondo = KPI Meta:</span>
      <span class="heatmap-legend-item">
        <span class="heatmap-legend-cell" style="background:#dcfce7;color:#15803d;font-size:9px;">✓</span>
        <span>Verde ≥100%</span>
      </span>
      <span class="heatmap-legend-item">
        <span class="heatmap-legend-cell" style="background:#fef3c7;color:#b45309;font-size:9px;">▲</span>
        <span>Amarillo ≥80%</span>
      </span>
      <span class="heatmap-legend-item">
        <span class="heatmap-legend-cell" style="background:#fee2e2;color:#b91c1c;font-size:9px;">✕</span>
        <span>Rojo &lt;80%</span>
      </span>
      <span style="margin-left:6px;font-size:10px;font-weight:600;color:#6b7280;">Símbolo = KPI Conv.</span>
    `;
    container.appendChild(legendDiv);

    const svgEl = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svgEl.setAttribute('class', 'chart-svg');
    svgEl.setAttribute('role', 'img');
    svgEl.setAttribute('aria-label', 'Heatmap semáforo de KPI Meta y Conversión por representante y mes');
    svgEl.setAttribute('width', '100%');
    svgEl.setAttribute('height', String(totalH));
    svgEl.setAttribute('viewBox', `0 0 ${totalW} ${totalH}`);
    container.appendChild(svgEl);

    const svg = d3.select(svgEl);

    // Etiquetas de trimestre
    ['Q1', 'Q2', 'Q3', 'Q4'].forEach((q, qi) => {
      const startIdx = qi * 3;
      const midX = (colX(startIdx) + colX(startIdx + 2) + cellW) / 2;
      svg.append('text')
        .attr('x', midX).attr('y', marginTop - 30)
        .attr('text-anchor', 'middle')
        .attr('font-size', '9px').attr('font-weight', '700')
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .attr('fill', '#6b7280')
        .text(q);
    });

    // Etiquetas de meses
    months.forEach((m, i) => {
      svg.append('text')
        .attr('x', colX(i) + cellW / 2).attr('y', marginTop - 14)
        .attr('text-anchor', 'middle')
        .attr('font-size', '9px')
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .attr('fill', '#6b7280')
        .text(monthLabels[i]);
    });

    // Separadores de trimestre (líneas verticales sutiles)
    [3, 6, 9].forEach(idx => {
      const sepX = colX(idx) - colGap / 2;
      svg.append('line')
        .attr('x1', sepX).attr('x2', sepX)
        .attr('y1', marginTop - 5).attr('y2', marginTop + repOrder.length * rowH)
        .attr('stroke', '#d1d5db').attr('stroke-width', 1)
        .attr('stroke-dasharray', '2,2');
    });

    // Filas de representantes
    repOrder.forEach((rep, ri) => {
      const rowY = marginTop + ri * rowH;

      // Nombre (abreviado)
      const parts = rep.split(' ');
      const abbr  = parts[0] + ' ' + (parts[1] ? parts[1].charAt(0) + '.' : '');
      svg.append('text')
        .attr('x', marginLeft - 8).attr('y', rowY + cellH / 2 + 4)
        .attr('text-anchor', 'end')
        .attr('font-size', '11px').attr('font-weight', '500')
        .attr('font-family', "'Inter', system-ui, sans-serif")
        .attr('fill', '#374151')
        .text(abbr);

      // Celdas
      months.forEach((m, mi) => {
        const key = rep + '__' + m;
        const rec = dataMap[key] || null;
        const x = colX(mi);
        const y = rowY;
        const bg = rec ? metaBg[rec.kpi_meta_status] : metaBg['null'];

        // Fondo de celda
        const rect = svg.append('rect')
          .attr('x', x + 1).attr('y', y + 1)
          .attr('width', cellW - 2).attr('height', cellH - 2)
          .attr('fill', bg).attr('rx', 3);

        if (rec) {
          rect.style('cursor', 'pointer')
            .on('mouseover', function(event) {
              tooltip.show(event, `
                <strong>${rec.rep_name} · ${rec.period}</strong>
                <div class="tooltip-row"><span>ID</span><span class="tooltip-val">${rec.id}</span></div>
                <div class="tooltip-row"><span>Revenue</span><span class="tooltip-val">$${(rec.revenue/1000).toFixed(0)}K</span></div>
                <div class="tooltip-row"><span>Target</span><span class="tooltip-val">$${(rec.target/1000).toFixed(0)}K</span></div>
                <div class="tooltip-row"><span>Leads</span><span class="tooltip-val">${rec.leads}</span></div>
                <div class="tooltip-row"><span>Deals</span><span class="tooltip-val">${rec.deals_closed}</span></div>
                <div class="tooltip-row"><span>KPI Meta</span><span class="tooltip-val">${rec.kpi_meta.toFixed(1)}%</span></div>
                <div class="tooltip-row"><span>KPI Conv</span><span class="tooltip-val">${rec.kpi_conversion.toFixed(1)}%</span></div>
              `);
            })
            .on('mousemove', function(event) { tooltip.move(event); })
            .on('mouseout', function() { tooltip.hide(); });

          // Número KPI Meta (centro)
          svg.append('text')
            .attr('x', x + cellW / 2).attr('y', y + cellH / 2 + 4)
            .attr('text-anchor', 'middle')
            .attr('font-size', '10px').attr('font-weight', '600')
            .attr('font-family', "'Inter', system-ui, sans-serif")
            .attr('fill', '#374151')
            .attr('pointer-events', 'none')
            .text(rec.kpi_meta.toFixed(0) + '%');

          // Símbolo KPI Conversión (esquina superior derecha)
          const sym = convSymbol[rec.kpi_conversion_status] || '?';
          svg.append('text')
            .attr('x', x + cellW - 4).attr('y', y + 10)
            .attr('text-anchor', 'end')
            .attr('font-size', '9px').attr('font-weight', '700')
            .attr('font-family', "'Inter', system-ui, sans-serif")
            .attr('fill', convColor[rec.kpi_conversion_status] || '#9ca3af')
            .attr('pointer-events', 'none')
            .text(sym);
        } else {
          // Celda vacía
          svg.append('text')
            .attr('x', x + cellW / 2).attr('y', y + cellH / 2 + 5)
            .attr('text-anchor', 'middle')
            .attr('font-size', '14px')
            .attr('font-family', "'Inter', system-ui, sans-serif")
            .attr('fill', '#d1d5db')
            .text('—');
        }
      });
    });
  };
})();
