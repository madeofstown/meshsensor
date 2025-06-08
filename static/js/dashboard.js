document.addEventListener("DOMContentLoaded", () => {
  const chartData = window.chartData;
  const cooldownMinutes = 5;
  const cooldownKey = "lastTelemetryRequest";
  const form = document.getElementById("telemetry-form");
  const button = document.getElementById("telemetry-button");

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

  let lastKnownUpdate = 0;

  function checkForUpdates() {
    fetch('/latest-data')
      .then(res => res.json())
      .then(data => {
        const ts = Math.floor(data.lastUpdated || 0);
        if (ts > window.initialLastTimestamp) {
          location.reload(); // Only refresh if there's newer data
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
});
