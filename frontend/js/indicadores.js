(function () {
  'use strict';

  const donutDefaults = {
    plugins: { legend: { display: false } },
    cutout: '72%',
    animation: { animateRotate: true, duration: 700 },
  };

  new Chart(document.getElementById('chartTipo'), {
    type: 'doughnut',
    data: {
      labels: CHART_DATA.porTipo.labels,
      datasets: [{
        data: CHART_DATA.porTipo.values,
        backgroundColor: CHART_DATA.porTipo.cores,
        borderWidth: 3,
        borderColor: '#ffffff',
        hoverBorderWidth: 3,
      }],
    },
    options: { ...donutDefaults },
  });

  new Chart(document.getElementById('chartConclusao'), {
    type: 'doughnut',
    data: {
      labels: ['Concluídos', 'Não concluídos'],
      datasets: [{
        data: [
          CHART_DATA.conclusao.concluidos,
          CHART_DATA.conclusao.naoConcluidos,
        ],
        backgroundColor: ['#16a34a', '#dc2626'],
        borderWidth: 3,
        borderColor: '#ffffff',
        hoverBorderWidth: 3,
      }],
    },
    options: { ...donutDefaults },
  });

  new Chart(document.getElementById('chartLine'), {
    type: 'line',
    data: {
      labels: CHART_DATA.lineDays,
      datasets: [
        {
          label: 'Chamados Criados',
          data: CHART_DATA.lineCriados,
          borderColor: '#f43f5e',
          backgroundColor: 'rgba(244,63,94,.08)',
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: '#f43f5e',
          tension: 0.35,
          fill: true,
        },
        {
          label: 'Chamados Resolvidos',
          data: CHART_DATA.lineResolvidos,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37,99,235,.08)',
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: '#2563eb',
          tension: 0.35,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1e293b',
          titleColor: '#94a3b8',
          bodyColor: '#f1f5f9',
          padding: 10,
          cornerRadius: 8,
        },
      },
      scales: {
        x: {
          grid: { color: '#f1f5f9' },
          ticks: { color: '#9ca3af', font: { size: 11 } },
        },
        y: {
          grid: { color: '#f1f5f9' },
          ticks: {
            color: '#9ca3af',
            font: { size: 11 },
            stepSize: 5,
          },
          min: 0,
          max: 40,
        },
      },
    },
  });

})();
