document.addEventListener("DOMContentLoaded", () => {
  const chartData = window.chartData;
  const cooldownMinutes = 5;
  const cooldownKey = "lastTelemetryRequest";
  const form = document.getElementById("telemetry-form");
  const button = document.getElementById("telemetry-button");

  // Build charts
  for (const metric in chartData) {
    const chart = echarts.init(document.getElementById(metric), 'dark');
    const series = Object.entries(chartData[metric]).map(([node, data]) => {
      const convertedData = metric === 'temperature'
        ? data.map(([ts, c]) => [ts, (c * 9 / 5) + 32])
        : data;
      return {
        name: node,
        type: 'line',
        smooth: true,
        data: convertedData
      };
    });
    chart.setOption({
      title: {
        text: metric === 'temperature'
          ? 'Temperature (°F) Over Time'
          : metric + ' Over Time'
      },
      tooltip: { trigger: 'axis' },
      legend: { data: Object.keys(chartData[metric]) },
      xAxis: { type: 'time' },
      yAxis: { type: 'value' },
      series: series
    });
  }

  // Cooldown logic
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

  function checkForUpdates() {
    fetch('/latest-data')
      .then(res => res.json())
      .then(data => {
        const ts = Math.floor(data.lastUpdated || 0);
        if (ts > window.initialLastTimestamp) {
          location.reload();
        }

        const tbody = document.getElementById('latest-rows');
        tbody.innerHTML = '';
        for (const node in data.metrics) {
          const c = data.metrics[node].temperature;
          const temp = c != null ? ((c * 9 / 5) + 32).toFixed(2) : '—';
          const rh = data.metrics[node].relativeHumidity?.toFixed(2) ?? '—';
          const updatedTs = data.lastTimestamps[node];
          const updated = updatedTs
            ? `<span class="live-timer" data-timestamp="${updatedTs}"></span>`
            : '—';
          tbody.innerHTML += `<tr>
            <td>${node}</td>
            <td>${temp}</td>
            <td>${rh}</td>
            <td>${updated}</td>
          </tr>`;
        }
      });
  }

  checkForUpdates();
  setInterval(checkForUpdates, 15000);

  fetch('/nodes')
    .then(res => res.json())
    .then(nodes => {
      const nav = document.getElementById('node-links');
      nav.innerHTML = nodes.map(n =>
        `<a href="/node/${n.id}" style="margin-right: 10px;">${n.name}</a>`
      ).join('');
    });

  function updateTimers() {
    const now = Math.floor(Date.now() / 1000);
    document.querySelectorAll('.live-timer').forEach(el => {
      const ts = parseInt(el.dataset.timestamp);
      const diff = now - ts;
      const min = Math.floor(diff / 60);
      const sec = diff % 60;
      el.textContent = min > 0
        ? `${min} min ${sec} sec ago`
        : `${sec} sec ago`;
    });
  }

  updateTimers();
  setInterval(updateTimers, 1000);
});
