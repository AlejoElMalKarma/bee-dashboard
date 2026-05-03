/**
 * VIZ-1 — BANs de Estado Global del Equipo
 * 4 tarjetas KPI + badge de estado central
 */

(function () {
  'use strict';

  window.Charts = window.Charts || {};

  window.Charts.bans = function init(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const records = data.records;
    const revenueTotal = d3.sum(records, d => d.revenue);
    const targetTotal  = d3.sum(records, d => d.target);
    const kpiMetaMean  = d3.mean(records, d => d.kpi_meta);
    const kpiConvMean  = d3.mean(records, d => d.kpi_conversion);
    const nGreen  = records.filter(d => d.kpi_meta_status === 'green').length;
    const nYellow = records.filter(d => d.kpi_meta_status === 'yellow').length;
    const nRed    = records.filter(d => d.kpi_meta_status === 'red').length;

    const revDiff    = revenueTotal - targetTotal;
    const revDiffPct = ((revDiff / targetTotal) * 100).toFixed(1);
    const revSign    = revDiff >= 0 ? '+' : '';

    function fmtCurrency(v) {
      if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(2)}M`;
      if (Math.abs(v) >= 1e3) return `$${(v / 1000).toFixed(0)}K`;
      return `$${v}`;
    }

    const bans = [
      {
        label: 'Revenue Total',
        value: fmtCurrency(revenueTotal),
        valueClass: '',
        sublabel: `${revSign}${fmtCurrency(revDiff)} vs target (${revSign}${revDiffPct}%)`,
        sublabelClass: revDiff >= 0 ? 'positive' : 'danger',
      },
      {
        label: 'KPI Meta Promedio',
        value: `${kpiMetaMean.toFixed(1)}%`,
        valueClass: kpiMetaMean >= 100 ? 'green' : kpiMetaMean >= 80 ? 'yellow' : 'red',
        sublabel: 'benchmark: 100%',
        sublabelClass: '',
      },
      {
        label: 'KPI Conversión Prom.',
        value: `${kpiConvMean.toFixed(1)}%`,
        valueClass: kpiConvMean >= 25 ? 'green' : kpiConvMean >= 15 ? 'yellow' : 'red',
        sublabel: 'benchmark: 25%',
        sublabelClass: '',
      },
      {
        label: 'Registros Críticos',
        value: `${nRed} / ${records.length}`,
        valueClass: nRed > 0 ? 'red' : 'green',
        sublabel: 'en rojo — requieren acción',
        sublabelClass: nRed > 0 ? 'danger' : '',
      },
    ];

    const teamStatus = kpiMetaMean >= 100 ? 'green' : kpiMetaMean >= 80 ? 'yellow' : 'red';
    const statusMeta = {
      green:  { icon: '✓', text: 'ESTADO: VERDE',    cls: 'green' },
      yellow: { icon: '⚠', text: 'ESTADO: AMARILLO', cls: 'yellow' },
      red:    { icon: '✗', text: 'ESTADO: ROJO',     cls: 'red' },
    };

    container.innerHTML = '';

    const wrapper = document.createElement('div');
    wrapper.id = 'bans-container';

    bans.forEach(b => {
      const card = document.createElement('div');
      card.className = 'ban-card';
      card.innerHTML = `
        <div class="ban-label">${b.label}</div>
        <div class="ban-value ${b.valueClass}">${b.value}</div>
        <div class="ban-sublabel ${b.sublabelClass}">${b.sublabel}</div>
      `;
      wrapper.appendChild(card);
    });

    const sm = statusMeta[teamStatus];
    const badge = document.createElement('div');
    badge.className = `status-badge ${sm.cls}`;
    badge.innerHTML = `
      <div class="status-badge-icon">${sm.icon}</div>
      <div class="status-badge-text">${sm.text}</div>
      <div class="status-badge-label">Equipo 2025</div>
    `;
    wrapper.appendChild(badge);

    container.appendChild(wrapper);
  };
})();
