/**
 * dashboard.js — Coordinador principal
 * Carga datos desde data/sales_report.json con d3.json()
 * Llama a cada módulo de gráfico que expone window.Charts.*
 */

(function () {
  'use strict';

  function showError(msg) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.innerHTML = `
        <div style="background:#fee2e2;color:#b91c1c;padding:20px 32px;border-radius:8px;font-size:14px;max-width:480px;text-align:center;">
          <strong>Error al cargar el dashboard</strong><br/><br/>${msg}
        </div>
      `;
    }
  }

  function updateDate() {
    const el = document.getElementById('update-date');
    if (!el) return;
    const now = new Date();
    el.textContent = now.toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric' });
  }

  function initDashboard(data) {
    updateDate();

    // Ocultar overlay
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'none';

    // Mostrar contenido
    const main = document.getElementById('dashboard-main');
    if (main) main.style.opacity = '1';

    // ── Inicializar cada visualización ─────────────────────────
    // Orden: las críticas primero (tabla y heatmap), luego las analíticas
    window.Charts.alertsTable(data, 'viz-7');
    window.Charts.heatmap(data,      'viz-5');
    window.Charts.dotPlot(data,      'viz-2');
    window.Charts.lineChart(data,    'viz-4');
    window.Charts.bulletChart(data,  'viz-3');
    window.Charts.scatter(data,      'viz-6');
    window.Charts.bans(data,         'viz-1');
  }

  function start() {
    if (typeof d3 === 'undefined') {
      showError('D3.js no se pudo cargar. Verifica tu conexión a internet.');
      return;
    }

    d3.json('./data/sales_report.json')
      .then(data => {
        if (!data || !data.records) throw new Error('Formato de datos inválido');
        initDashboard(data);
      })
      .catch(err => {
        console.error('Dashboard error:', err);
        showError(err.message);
      });
  }

  // Esperar a que todos los scripts chart estén cargados
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
