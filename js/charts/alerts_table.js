/**
 * VIZ-7 — Panel de Alertas de Registros Críticos
 * Tabla estructurada con visualización inline
 * 4 registros con kpi_meta_status = "red", ordenados por kpi_meta% ascendente (peor primero)
 */

(function () {
  'use strict';

  window.Charts = window.Charts || {};

  window.Charts.alertsTable = function init(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Filtrar y ordenar registros críticos (peor kpi_meta primero)
    const criticals = data.records
      .filter(r => r.kpi_meta_status === 'red')
      .map(r => ({
        ...r,
        gap: r.revenue - r.target,
      }))
      .sort((a, b) => a.kpi_meta - b.kpi_meta);

    const maxGapAbs = Math.max(...criticals.map(r => Math.abs(r.gap)));

    function fmtK(v) {
      return '$' + (Math.abs(v) / 1000).toFixed(0) + 'K';
    }

    function fmtMonth(period) {
      const parts = period.split('-');
      const m = parseInt(parts[1]);
      const monthNames = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                          'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
      return monthNames[m - 1] + ' ' + parts[0];
    }

    function badgeHtml(value, status) {
      const icons = { red: '✗', yellow: '⚠', green: '✓' };
      const icon = icons[status] || '';
      return `<span class="kpi-badge ${status}">${icon} ${value}</span>`;
    }

    container.innerHTML = '';

    // Header
    const header = document.createElement('div');
    header.className = 'alerts-header';
    header.innerHTML = `
      <span class="card-title">Registros Críticos — Requieren Atención</span>
      <span class="alerts-badge">${criticals.length}</span>
    `;
    container.appendChild(header);

    // Tabla
    const table = document.createElement('table');
    table.className = 'alerts-table';

    const thead = document.createElement('thead');
    thead.innerHTML = `
      <tr>
        <th>ID</th>
        <th>Mes</th>
        <th>Representante</th>
        <th>Región</th>
        <th>Revenue</th>
        <th>Gap vs Target</th>
        <th>KPI Meta</th>
        <th>KPI Conv</th>
      </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    criticals.forEach((r, i) => {
      const isWorst = i === 0;
      const tr = document.createElement('tr');
      if (isWorst) tr.className = 'worst-row';

      const gapPct = Math.round((Math.abs(r.gap) / maxGapAbs) * 100);

      tr.innerHTML = `
        <td><strong style="font-size:12px;color:#374151;">${r.id}</strong></td>
        <td style="color:#6b7280;white-space:nowrap;">${fmtMonth(r.period)}</td>
        <td style="font-weight:500;white-space:nowrap;">${r.rep_name}</td>
        <td style="color:#6b7280;">${r.region}</td>
        <td style="font-weight:500;white-space:nowrap;">$${(r.revenue / 1000).toFixed(0)}K</td>
        <td>
          <div class="gap-bar-cell">
            <span class="gap-value">-${fmtK(r.gap)}</span>
            <div class="gap-bar-track">
              <div class="gap-bar-fill" style="width:${gapPct}%;"></div>
            </div>
          </div>
        </td>
        <td>${badgeHtml(r.kpi_meta.toFixed(1) + '%', r.kpi_meta_status)}</td>
        <td>${badgeHtml(r.kpi_conversion.toFixed(1) + '%', r.kpi_conversion_status)}</td>
      `;

      tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.appendChild(table);
  };
})();
