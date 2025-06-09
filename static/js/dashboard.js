
document.addEventListener("DOMContentLoaded", () => {
  const chartData = window.chartData;

  function formatTitle(metric) {
    if (/^[a-z]+([A-Z][a-z]*)+$/.test(metric)) {
      // camelCase: split before uppercase letters and capitalize each word
      return metric.replace(/([a-z])([A-Z])/g, '$1 $2')
                  .replace(/\b\w/g, char => char.toUpperCase());
    } else if (metric.length <= 3) {
      return metric.toUpperCase();
    } else {
      return metric.charAt(0).toUpperCase() + metric.slice(1);
    }
  }


  for (const metric in chartData) {
    const chart = echarts.init(document.getElementById(metric), 'dark');
    const series = Object.entries(chartData[metric]).map(([node, data]) => ({
      name: node,
      type: 'line',
      smooth: true,
      data: data.map(([ts, value]) => [
        ts,
        metric === 'temperature' ? (value * 9 / 5 + 32).toFixed(2) : value
      ])
    }));
    chart.setOption({
      title: { text: formatTitle(metric) + (metric === 'temperature' ? ' (°F)' : '') },
      tooltip: { trigger: 'axis' },
      legend: { data: Object.keys(chartData[metric]) },
      xAxis: { type: 'time' },
      yAxis: { type: 'value' },
      series: series
    });
  }

  fetch('/nodes')
    .then(res => res.json())
    .then(nodes => {
      const nav = document.getElementById('node-links');
      nav.innerHTML = nodes.map(n =>
        `<a href="/node/${n.id}" style="margin-right: 10px;">${n.name}</a>`
      ).join('');
    });

  function updateLatest() {
    fetch('/latest-data')
      .then(res => res.json())
      .then(data => {
        const tbody = document.getElementById('latest-rows');
        tbody.innerHTML = '';
        for (const node in data.metrics) {
          const temp = data.metrics[node].temperature;
          const rh = data.metrics[node].relativeHumidity;
          const updated = data.lastSeen[node]
            ? new Date(data.lastSeen[node] * 1000).toLocaleString()
            : '—';
          tbody.innerHTML += `<tr>
            <td>${node}</td>
            <td>${temp !== null ? (temp * 9 / 5 + 32).toFixed(2) : '—'}</td>
            <td>${rh !== null ? rh.toFixed(2) : '—'}</td>
            <td>${updated}</td>
          </tr>`;
        }
      });
  }

  updateLatest();
  setInterval(updateLatest, 15000);

  const cooldownMinutes = 5;
  const cooldownKey = "lastTelemetryRequest";
  const button = document.getElementById("telemetry-button");
  const form = document.getElementById("telemetry-form");

  function updateCooldownState() {
    const lastRequest = localStorage.getItem(cooldownKey);
    if (lastRequest) {
      const elapsed = (Date.now() - parseInt(lastRequest, 10)) / 60000;
      if (elapsed < cooldownMinutes) {
        const remaining = Math.ceil(cooldownMinutes - elapsed);
        button.disabled = true;
        button.innerText = `⏳ Wait ${remaining} min...`;
        return;
      }
    }
    button.disabled = false;
    button.innerText = "📡 Request Telemetry";
  }

  form.addEventListener("submit", () => {
    localStorage.setItem(cooldownKey, Date.now().toString());
    updateCooldownState();
    document.getElementById('loading-overlay').style.display = 'flex';
  });

  updateCooldownState();
  setInterval(updateCooldownState, 30000);
// Add refresh on new data logic
  const pageLoadTime = Date.now();
  setInterval(() => {
    fetch('/latest-data')
      .then(res => res.json())
      .then(data => {
        if (data.lastUpdated * 1000 > pageLoadTime) {
          location.reload();
        }
      });
  }, 10000);
});
