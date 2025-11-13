/**
 * DataViento - Weather Charts
 *
 * Handles Chart.js visualizations for all weather models:
 * - Weather Forecast
 * - Air Quality
 * - Marine Weather
 * - Satellite Radiation
 * - Climate Change
 */

console.log("weather-charts.js loaded");

// ========================================
// GLOBAL CHART INSTANCES
// ========================================

// Weather charts 
let weatherDailyChart = null;
let weatherPrecipChart = null;
let weatherWindChart = null;
let weatherUvChart = null;
let weatherHourlyTempChart = null;
let weatherHourlyPrecipChart = null;
let weatherHourlyWindChart = null;

// Air quality Charts
let airQualityAqiChart = null;
let airQualityPollutantsChart = null;
let airQualitySecondaryChart = null;

// Marine Charts
let marineWaveChart = null;
let marineDailyWaveChart = null;
let marineDailyPeriodChart = null;
let marineHourlyWaveChart = null;
let marineHourlyPeriodChart = null;

// Satellite Charts
let satelliteChart = null;
let satelliteDailyRadiationChart = null;
let satelliteDailyIrradianceChart = null;

// Climate Charts
let climateTempChart = null;                   
let climateTempTrendsChart = null;              
let climatePrecipHumidityChart = null;          
let climateWindRadiationChart = null; 

// ========================================
// WEATHER FORECAST CHARTS
// ========================================

/**
 * Create temperature forecast chart
 *
 * Shows 7-day temperature forecast with min/max temperatures
 *
 * @param {Array} data - Temperature data from backend
 */
function createWeatherDailyChart() {
  console.log("📊 Creating weather temperature chart...");

  const ctx = document.getElementById("weatherTempChart");

  if (!ctx) {
    console.warn("⚠️ weatherTempChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (weatherDailyChart) {
    weatherDailyChart.destroy();
  }

  weatherDailyChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Max Temperature (°C)",
          data: [],
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          tension: 0.4,
          fill: true,
        },
        {
          label: "Min Temperature (°C)",
          data: [],
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          mode: "index",
          intersect: false,
        },
      },
      scales: {
        y: {
          beginAtZero: false,
          title: {
            display: true,
            text: "Temperature (°C)",
          },
        },
        x: {
          title: {
            display: true,
            text: "Day",
          },
        },
      },
    },
  });

  return weatherDailyChart;
}

function createWeatherPrecipChart() {
  console.log("📊 Creating precipitation chart...");

  const ctx = document.getElementById("weatherPrecipChart");

  if (!ctx) {
    console.warn("⚠️ weatherPrecipChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (weatherPrecipChart) {
    weatherPrecipChart.destroy();
  }

  weatherPrecipChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          type: "bar",
          label: "Precipitation (mm)",
          data: [],
          backgroundColor: "rgba(59, 130, 246, 0.7)",
          borderColor: "rgb(59, 130, 246)",
          borderWidth: 1,
          yAxisID: "y",
        },
        {
          type: "line",
          label: "Probability (%)",
          data: [],
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              if (context.datasetIndex === 0) {
                const value = context.parsed.y;
                if (value === 0) return "No rain";
                if (value < 2.5) return "Light rain";
                if (value < 10) return "Moderate rain";
                if (value < 50) return "Heavy rain";
                return "Very heavy rain";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          beginAtZero: true,
          title: {
            display: true,
            text: "Precipitation (mm)",
          },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: "Probability (%)",
          },
          grid: {
            drawOnChartArea: false,
          },
        },
        x: {
          title: {
            display: true,
            text: "Day",
          },
        },
      },
    },
  });

  console.log("✅ Precipitation chart created");
  return weatherPrecipChart;
}

function updateWeatherPrecipChart(apiData) {
  console.log("📊 Updating precipitation chart...");

  if (!weatherPrecipChart) {
    console.warn("⚠️ Precipitation chart not initialized");
    return;
  }

  if (!apiData || apiData.length === 0) {
    console.warn("⚠️ No precipitation data available");
    return;
  }

  const labels = [];
  const precipSum = [];
  const precipProb = [];

  apiData.forEach((day) => {
    const dateParts = day.valid_date.split('-');
    const year = parseInt(dateParts[0]);
    const month = parseInt(dateParts[1]) - 1
    const dayNum = parseInt(dateParts[2])

    const date = new Date(Date.UTC(year,month,dayNum))

    const label = date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone : "UTC"
    });
    labels.push(label);

    precipSum.push(day.precipitation_sum || 0);
    precipProb.push(day.precipitation_probability_max || 0);
  });

  weatherPrecipChart.data.labels = labels;
  weatherPrecipChart.data.datasets[0].data = precipSum;
  weatherPrecipChart.data.datasets[1].data = precipProb;

  weatherPrecipChart.update();

  console.log("✅ Precipitation chart updated");
}

/**
 * Update weather daily chart with API data
 *
 * @param {Array} apiData - Daily forecast data from weather API
 */
function updateWeatherDailyChart(apiData) {
  console.log("📊 Updating weather daily chart with API data...", apiData);

  if (!weatherDailyChart) {
    console.warn("⚠️ weatherTempChart not initialized");
    return;
  }

  if (!apiData || apiData.length === 0) {
    console.warn("⚠️ No daily forecast data available");
    return;
  }

  // Transform API data to Chart.js format
  const labels = [];
  const maxTemps = [];
  const minTemps = [];

  apiData.forEach((day) => {
    // TODO use UTC date instead of local time
    const dateParts = day.valid_date.split('-');
    const year = parseInt(dateParts[0]);
    const month = parseInt(dateParts[1]) - 1
    const dayNum = parseInt(dateParts[2])

    const date = new Date(Date.UTC(year,month,dayNum))

    const label = date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone : "UTC"
    });
    labels.push(label);

    // Extract temperature data
    maxTemps.push(day.temperature_2m_max || null);
    minTemps.push(day.temperature_2m_min || null);
  });

  // Update chart data
  weatherDailyChart.data.labels = labels;
  weatherDailyChart.data.datasets[0].data = maxTemps; // Max temperature
  weatherDailyChart.data.datasets[1].data = minTemps; // Min temperature

  // Refresh the chart
  weatherDailyChart.update();

  console.log("✅ Weather daily chart updated successfully");
}

/**
 * Create wind speed chart
 *
 * Shows 24-hour wind speed forecast
 *
 * @param {Array} data - Wind speed data from backend
 */
function createWeatherWindChart() {
  console.log("📊 Creating wind speed chart...");

  const ctx = document.getElementById("weatherWindChart");

  if (!ctx) {
    console.warn("⚠️ weatherWindChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (weatherWindChart) {
    weatherWindChart.destroy();
  }

  weatherWindChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Max Wind Speed (km/h)",
          data: [],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 2,
        },
        {
          label: "Max Gusts (km/h)",
          data: [],
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          borderDash: [5, 5],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              if (context.datasetIndex === 0) {
                const value = context.parsed.y;
                if (value < 20) return "Light wind";
                if (value < 40) return "Moderate wind";
                if (value < 60) return "Strong wind";
                return "Very strong wind";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Speed (km/h)",
          },
        },
        x: {
          title: {
            display: true,
            text: "Day",
          },
        },
      },
    },
  });

  console.log("✅ Wind speed chart created");
  return weatherWindChart;
}

function updateWeatherWindChart(apiData) {
  console.log("📊 Updating wind chart...");

  if (!weatherWindChart) {
    console.warn("⚠️ Wind chart not initialized");
    return;
  }

  if (!apiData || apiData.length === 0) {
    console.warn("⚠️ No wind data available");
    return;
  }

  const labels = [];
  const windSpeed = [];
  const windGusts = [];

  apiData.forEach((day) => {
    const dateParts = day.valid_date.split('-');
    const year = parseInt(dateParts[0]);
    const month = parseInt(dateParts[1]) - 1
    const dayNum = parseInt(dateParts[2])

    const date = new Date(Date.UTC(year,month,dayNum))

    const label = date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone: "UTC"
    });
    labels.push(label);

    windSpeed.push(day.wind_speed_10m_max || 0);
    windGusts.push(day.wind_gusts_10m_max || 0);
  });

  weatherWindChart.data.labels = labels;
  weatherWindChart.data.datasets[0].data = windSpeed;
  weatherWindChart.data.datasets[1].data = windGusts;

  weatherWindChart.update();

  console.log("✅ Wind chart updated");
}

function createWeatherUvChart() {
  console.log("📊 Creating UV & sunshine chart...");

  const ctx = document.getElementById("weatherUvChart");

  if (!ctx) {
    console.warn("⚠️ weatherUvChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (weatherUvChart) {
    weatherUvChart.destroy();
  }

  weatherUvChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          type: "bar",
          label: "UV Index",
          data: [],
          backgroundColor: function(context) {
            // ✅ FIX: Validate context.parsed exists
            if (!context.parsed || context.parsed.y === undefined) {
              return "rgba(156, 163, 175, 0.7)"; // Gray default
            }
            
            const value = context.parsed.y;
            if (value <= 2) return "rgba(34, 197, 94, 0.7)"; // Green (Low)
            if (value <= 5) return "rgba(234, 179, 8, 0.7)"; // Yellow (Moderate)
            if (value <= 7) return "rgba(249, 115, 22, 0.7)"; // Orange (High)
            if (value <= 10) return "rgba(239, 68, 68, 0.7)"; // Red (Very High)
            return "rgba(139, 92, 246, 0.7)"; // Purple (Extreme)
          },
          borderColor: "rgba(0, 0, 0, 0.1)",
          borderWidth: 1,
          yAxisID: "y",
        },
        {
          type: "line",
          label: "Sunshine (hours)",
          data: [],
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 3,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              // ✅ FIX: Validate context.parsed exists
              if (!context.parsed || context.parsed.y === undefined) {
                return "";
              }
              
              if (context.datasetIndex === 0) {
                const value = context.parsed.y;
                if (value <= 2) return "🟢 Low - No protection needed";
                if (value <= 5) return "🟡 Moderate - Seek shade midday";
                if (value <= 7) return "🟠 High - Protection required";
                if (value <= 10) return "🔴 Very High - Extra protection";
                return "🟣 Extreme - Avoid sun";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          beginAtZero: true,
          max: 12,
          title: {
            display: true,
            text: "UV Index",
          },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          beginAtZero: true,
          max: 14,
          title: {
            display: true,
            text: "Sunshine Duration (hours)",
          },
          grid: {
            drawOnChartArea: false,
          },
        },
        x: {
          title: {
            display: true,
            text: "Day",
          },
        },
      },
    },
  });

  console.log("✅ UV & sunshine chart created");
  return weatherUvChart;
}

function updateWeatherUvChart(apiData) {
  console.log("📊 Updating UV & sunshine chart...");

  if (!weatherUvChart) {
    console.warn("⚠️ UV chart not initialized");
    return;
  }

  if (!apiData || apiData.length === 0) {
    console.warn("⚠️ No UV data available");
    return;
  }

  const labels = [];
  const uvIndex = [];
  const sunshineHours = [];

  apiData.forEach((day) => {
    const dateParts = day.valid_date.split('-');
    const year = parseInt(dateParts[0]);
    const month = parseInt(dateParts[1]) - 1
    const dayNum = parseInt(dateParts[2])

    const date = new Date(Date.UTC(year,month,dayNum))
    const label = date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone: "UTC"
    });
    labels.push(label);

    uvIndex.push(day.uv_index_max || 0);
    
    // Convert sunshine_duration from seconds to hours
    const sunshineInHours = day.sunshine_duration ? (day.sunshine_duration / 3600).toFixed(1) : 0;
    sunshineHours.push(parseFloat(sunshineInHours));
  });

  weatherUvChart.data.labels = labels;
  weatherUvChart.data.datasets[0].data = uvIndex;
  weatherUvChart.data.datasets[1].data = sunshineHours;

  weatherUvChart.update();

  console.log("✅ UV & sunshine chart updated");
}

function createWeatherHourlyTempChart() {
  console.log("📊 Creating hourly temperature & humidity chart...");

  const ctx = document.getElementById("weatherHourlyTempChart");

  if (!ctx) {
    console.warn("⚠️ weatherHourlyTempChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (weatherHourlyTempChart) {
    weatherHourlyTempChart.destroy();
  }

  weatherHourlyTempChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Temperature (°C)",
          data: [],
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 2,
          yAxisID: "y",
        },
        {
          label: "Humidity (%)",
          data: [],
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              if (context.datasetIndex === 0) {
                const value = context.parsed.y;
                if (value < 10) return "🥶 Cold";
                if (value < 20) return "😊 Mild";
                if (value < 30) return "🌞 Warm";
                return "🔥 Hot";
              }
              if (context.datasetIndex === 1) {
                const value = context.parsed.y;
                if (value < 30) return "🏜️ Dry";
                if (value < 60) return "👌 Comfortable";
                if (value < 80) return "💧 Humid";
                return "🌊 Very Humid";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          title: {
            display: true,
            text: "Temperature (°C)",
          },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: "Humidity (%)",
          },
          grid: {
            drawOnChartArea: false,
          },
        },
        x: {
          title: {
            display: true,
            text: "Hour",
          },
        },
      },
    },
  });

  console.log("✅ Hourly temperature & humidity chart created");
  return weatherHourlyTempChart;
}

/**
 * Update hourly temperature chart with API data
 */
function updateWeatherHourlyTempChart(apiData) {
  console.log("📊 Updating hourly temperature & humidity chart...");

  if (!weatherHourlyTempChart) {
    console.warn("⚠️ Hourly temp chart not initialized");
    return;
  }

  if (!apiData || !apiData.parameters) {
    console.warn("⚠️ No hourly temperature data available");
    return;
  }

  const temp = apiData.parameters.temp_2m;
  const humidity = apiData.parameters.humidity_2m;

  if (!temp || !humidity) {
    console.warn("⚠️ Missing temperature or humidity parameters");
    return;
  }

  // Format labels (hours)
  const labels = temp.times.map(formatHourLabel);

  weatherHourlyTempChart.data.labels = labels;
  weatherHourlyTempChart.data.datasets[0].data = temp.values;
  weatherHourlyTempChart.data.datasets[1].data = humidity.values;

  weatherHourlyTempChart.update();

  console.log("✅ Hourly temperature & humidity chart updated");
}

/**
 * Create hourly precipitation chart
 */
function createWeatherHourlyPrecipChart() {
  console.log("📊 Creating hourly precipitation chart...");

  const ctx = document.getElementById("weatherHourlyPrecipChart");

  if (!ctx) {
    console.warn("⚠️ weatherHourlyPrecipChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (weatherHourlyPrecipChart) {
    weatherHourlyPrecipChart.destroy();
  }

  weatherHourlyPrecipChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          type: "bar",
          label: "Precipitation (mm)",
          data: [],
          backgroundColor: "rgba(59, 130, 246, 0.7)",
          borderColor: "rgb(59, 130, 246)",
          borderWidth: 1,
          yAxisID: "y",
        },
        {
          type: "line",
          label: "Probability (%)",
          data: [],
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              if (context.datasetIndex === 0) {
                const value = context.parsed.y;
                if (value === 0) return "No rain";
                if (value < 1) return "Light rain";
                if (value < 4) return "Moderate rain";
                if (value < 10) return "Heavy rain";
                return "Very heavy rain";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          beginAtZero: true,
          title: {
            display: true,
            text: "Precipitation (mm)",
          },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: "Probability (%)",
          },
          grid: {
            drawOnChartArea: false,
          },
        },
        x: {
          title: {
            display: true,
            text: "Hour",
          },
        },
      },
    },
  });

  console.log("✅ Hourly precipitation chart created");
  return weatherHourlyPrecipChart;
}

/**
 * Update hourly precipitation chart with API data
 */
function updateWeatherHourlyPrecipChart(apiData) {
  console.log("📊 Updating hourly precipitation chart...");

  if (!weatherHourlyPrecipChart) {
    console.warn("⚠️ Hourly precip chart not initialized");
    return;
  }

  if (!apiData || !apiData.parameters) {
    console.warn("⚠️ No hourly precipitation data available");
    return;
  }

  const precip = apiData.parameters.precip;
  const precipProb = apiData.parameters.precip_prob;

  if (!precip || !precipProb) {
    console.warn("⚠️ Missing precipitation parameters");
    return;
  }

  // Format labels (hours)
  const labels = precip.times.map(formatHourLabel);

  weatherHourlyPrecipChart.data.labels = labels;
  weatherHourlyPrecipChart.data.datasets[0].data = precip.values;
  weatherHourlyPrecipChart.data.datasets[1].data = precipProb.values;

  weatherHourlyPrecipChart.update();

  console.log("✅ Hourly precipitation chart updated");
}

/**
 * Create hourly wind speed chart
 */
function createWeatherHourlyWindChart() {
  console.log("📊 Creating hourly wind speed chart...");

  const ctx = document.getElementById("weatherHourlyWindChart");

  if (!ctx) {
    console.warn("⚠️ weatherHourlyWindChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (weatherHourlyWindChart) {
    weatherHourlyWindChart.destroy();
  }

  weatherHourlyWindChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Wind Speed (km/h)",
          data: [],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 2,
          yAxisID: "y",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              const value = context.parsed.y;
              if (value < 10) return "🍃 Light breeze";
              if (value < 20) return "💨 Moderate wind";
              if (value < 40) return "🌬️ Strong wind";
              if (value < 60) return "⚠️ Very strong wind";
              return "🚨 Dangerous wind";
            },
            footer: function (tooltipItems) {
              // Show wind direction in footer
              const index = tooltipItems[0].dataIndex;
              const windDir = weatherHourlyWindChart.data.datasets[0].windDirections?.[index];
              if (windDir !== undefined) {
                const direction = getWindDirection(windDir);
                return `Direction: ${direction} (${windDir}°)`;
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Wind Speed (km/h)",
          },
        },
        x: {
          title: {
            display: true,
            text: "Hour",
          },
        },
      },
    },
  });

  console.log("✅ Hourly wind speed chart created");
  return weatherHourlyWindChart;
}

/**
 * Update hourly wind chart with API data
 */
function updateWeatherHourlyWindChart(apiData) {
  console.log("📊 Updating hourly wind speed chart...");

  if (!weatherHourlyWindChart) {
    console.warn("⚠️ Hourly wind chart not initialized");
    return;
  }

  if (!apiData || !apiData.parameters) {
    console.warn("⚠️ No hourly wind data available");
    return;
  }

  const windSpeed = apiData.parameters.wind_speed_10m;
  const windDir = apiData.parameters.wind_dir_10m;

  if (!windSpeed || !windDir) {
    console.warn("⚠️ Missing wind parameters");
    return;
  }

  // Format labels (hours)
  const labels = windSpeed.times.map(formatHourLabel);

  // Store wind directions in dataset for tooltip access
  weatherHourlyWindChart.data.labels = labels;
  weatherHourlyWindChart.data.datasets[0].data = windSpeed.values;
  weatherHourlyWindChart.data.datasets[0].windDirections = windDir.values;

  weatherHourlyWindChart.update();

  console.log("✅ Hourly wind speed chart updated");
}

/**
 * Helper function to convert wind direction degrees to compass direction
 * @param {number} degrees - Wind direction in degrees (0-360)
 * @returns {string} Compass direction (N, NE, E, etc.)
 */
function getWindDirection(degrees) {
  const directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
  const index = Math.round(degrees / 22.5) % 16;
  return directions[index];
}


// ========================================
// AIR QUALITY HOURLY CHARTS
// ========================================

/**
 * Helper function to format hour from ISO timestamp
 * @param {string} timestamp - ISO timestamp
 * @returns {string} Formatted hour (e.g., "14:00")
 */
function formatHourLabel(timestamp) {
  const date = new Date(timestamp);
  const hours = date.getHours().toString().padStart(2, '0');
  return `${hours}:00`;
}

/**
 * Create AQI trends chart (European vs US)
 */
function createAirQualityAqiChart() {
  console.log("📊 Creating AQI trends chart...");

  const ctx = document.getElementById("airQualityAqiChart");

  if (!ctx) {
    console.warn("⚠️ airQualityAqiChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (airQualityAqiChart) {
    airQualityAqiChart.destroy();
  }

  airQualityAqiChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "European AQI",
          data: [],
          borderColor: "#8b5cf6",
          backgroundColor: "rgba(139, 92, 246, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 2,
          yAxisID: "y",
        },
        {
          label: "US AQI",
          data: [],
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 2,
          yAxisID: "y",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              const value = context.parsed.y;
              
              // European AQI levels
              if (context.datasetIndex === 0) {
                if (value <= 20) return "🟢 Good";
                if (value <= 40) return "🟡 Fair";
                if (value <= 60) return "🟠 Moderate";
                if (value <= 80) return "🔴 Poor";
                if (value <= 100) return "🟣 Very Poor";
                return "⚫ Extremely Poor";
              }
              
              // US AQI levels
              if (context.datasetIndex === 1) {
                if (value <= 50) return "🟢 Good";
                if (value <= 100) return "🟡 Moderate";
                if (value <= 150) return "🟠 Unhealthy for Sensitive";
                if (value <= 200) return "🔴 Unhealthy";
                if (value <= 300) return "🟣 Very Unhealthy";
                return "⚫ Hazardous";
              }
              
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "AQI Value",
          },
        },
        x: {
          title: {
            display: true,
            text: "Hour",
          },
        },
      },
    },
  });

  console.log("✅ AQI trends chart created");
  return airQualityAqiChart;
}

/**
 * Update AQI trends chart with API data
 */
function updateAirQualityAqiChart(apiData) {
  console.log("📊 Updating AQI trends chart...");

  if (!airQualityAqiChart) {
    console.warn("⚠️ AQI chart not initialized");
    return;
  }

  if (!apiData || !apiData.parameters) {
    console.warn("⚠️ No AQI data available");
    return;
  }

  const europeanAqi = apiData.parameters.aqi_european;
  const usAqi = apiData.parameters.aqi_us;

  if (!europeanAqi || !usAqi) {
    console.warn("⚠️ Missing AQI parameters");
    return;
  }

  // Format labels (hours)
  const labels = europeanAqi.times.map(formatHourLabel);

  airQualityAqiChart.data.labels = labels;
  airQualityAqiChart.data.datasets[0].data = europeanAqi.values;
  airQualityAqiChart.data.datasets[1].data = usAqi.values;

  airQualityAqiChart.update();

  console.log("✅ AQI trends chart updated");
}

/**
 * Create major pollutants chart (PM2.5, PM10, NO2, O3)
 */
function createAirQualityPollutantsChart() {
  console.log("📊 Creating pollutants chart...");

  const ctx = document.getElementById("airQualityPollutantsChart");

  if (!ctx) {
    console.warn("⚠️ airQualityPollutantsChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (airQualityPollutantsChart) {
    airQualityPollutantsChart.destroy();
  }

  airQualityPollutantsChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "PM2.5 (µg/m³)",
          data: [],
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 2,
          yAxisID: "y",
        },
        {
          label: "PM10 (µg/m³)",
          data: [],
          borderColor: "#f97316",
          backgroundColor: "rgba(249, 115, 22, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          yAxisID: "y",
        },
        {
          label: "NO2 (µg/m³)",
          data: [],
          borderColor: "#eab308",
          backgroundColor: "rgba(234, 179, 8, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          yAxisID: "y",
        },
        {
          label: "O3 (µg/m³)",
          data: [],
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          yAxisID: "y",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              const value = context.parsed.y;
              const label = context.dataset.label;
              
              // PM2.5
              if (label.includes("PM2.5")) {
                if (value <= 12) return "🟢 Good";
                if (value <= 35.4) return "🟡 Moderate";
                if (value <= 55.4) return "🟠 Unhealthy for Sensitive";
                if (value <= 150.4) return "🔴 Unhealthy";
                if (value <= 250.4) return "🟣 Very Unhealthy";
                return "⚫ Hazardous";
              }
              
              // PM10
              if (label.includes("PM10")) {
                if (value <= 54) return "🟢 Good";
                if (value <= 154) return "🟡 Moderate";
                if (value <= 254) return "🟠 Unhealthy for Sensitive";
                if (value <= 354) return "🔴 Unhealthy";
                if (value <= 424) return "🟣 Very Unhealthy";
                return "⚫ Hazardous";
              }
              
              // NO2
              if (label.includes("NO2")) {
                if (value <= 53) return "🟢 Good";
                if (value <= 100) return "🟡 Moderate";
                return "🔴 Unhealthy";
              }
              
              // O3
              if (label.includes("O3")) {
                if (value <= 54) return "🟢 Good";
                if (value <= 70) return "🟡 Moderate";
                return "🔴 Unhealthy";
              }
              
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Concentration (µg/m³)",
          },
        },
        x: {
          title: {
            display: true,
            text: "Hour",
          },
        },
      },
    },
  });

  console.log("✅ Pollutants chart created");
  return airQualityPollutantsChart;
}

/**
 * Update pollutants chart with API data
 */
function updateAirQualityPollutantsChart(apiData) {
  console.log("📊 Updating pollutants chart...");

  if (!airQualityPollutantsChart) {
    console.warn("⚠️ Pollutants chart not initialized");
    return;
  }

  if (!apiData || !apiData.parameters) {
    console.warn("⚠️ No pollutants data available");
    return;
  }

  const pm25 = apiData.parameters.pm2_5;
  const pm10 = apiData.parameters.pm10;
  const no2 = apiData.parameters.no2;
  const o3 = apiData.parameters.o3;

  if (!pm25 || !pm10 || !no2 || !o3) {
    console.warn("⚠️ Missing pollutant parameters");
    return;
  }

  // Format labels (hours)
  const labels = pm25.times.map(formatHourLabel);

  airQualityPollutantsChart.data.labels = labels;
  airQualityPollutantsChart.data.datasets[0].data = pm25.values;
  airQualityPollutantsChart.data.datasets[1].data = pm10.values;
  airQualityPollutantsChart.data.datasets[2].data = no2.values;
  airQualityPollutantsChart.data.datasets[3].data = o3.values;

  airQualityPollutantsChart.update();

  console.log("✅ Pollutants chart updated");
}

/**
 * Create secondary pollutants chart (SO2, CO)
 */
function createAirQualitySecondaryChart() {
  console.log("📊 Creating secondary pollutants chart...");

  const ctx = document.getElementById("airQualitySecondaryChart");

  if (!ctx) {
    console.warn("⚠️ airQualitySecondaryChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (airQualitySecondaryChart) {
    airQualitySecondaryChart.destroy();
  }

  airQualitySecondaryChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "SO2 (µg/m³)",
          data: [],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 2,
          yAxisID: "y",
        },
        {
          label: "CO (µg/m³)",
          data: [],
          borderColor: "#64748b",
          backgroundColor: "rgba(100, 116, 139, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              const value = context.parsed.y;
              const label = context.dataset.label;
              
              // SO2
              if (label.includes("SO2")) {
                if (value <= 35) return "🟢 Good";
                if (value <= 75) return "🟡 Moderate";
                return "🔴 Unhealthy";
              }
              
              // CO
              if (label.includes("CO")) {
                if (value <= 4400) return "🟢 Good";
                if (value <= 9400) return "🟡 Moderate";
                return "🔴 Unhealthy";
              }
              
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "SO2 (µg/m³)",
          },
          position: "left",
        },
        y1: {
          beginAtZero: true,
          title: {
            display: true,
            text: "CO (µg/m³)",
          },
          position: "right",
          grid: {
            drawOnChartArea: false,
          },
        },
        x: {
          title: {
            display: true,
            text: "Hour",
          },
        },
      },
    },
  });

  console.log("✅ Secondary pollutants chart created");
  return airQualitySecondaryChart;
}

/**
 * Update secondary pollutants chart with API data
 */
function updateAirQualitySecondaryChart(apiData) {
  console.log("📊 Updating secondary pollutants chart...");

  if (!airQualitySecondaryChart) {
    console.warn("⚠️ Secondary chart not initialized");
    return;
  }

  if (!apiData || !apiData.parameters) {
    console.warn("⚠️ No secondary pollutants data available");
    return;
  }

  const so2 = apiData.parameters.so2;
  const co = apiData.parameters.co;

  if (!so2 || !co) {
    console.warn("⚠️ Missing secondary pollutant parameters");
    return;
  }

  // Format labels (hours)
  const labels = so2.times.map(formatHourLabel);

  airQualitySecondaryChart.data.labels = labels;
  airQualitySecondaryChart.data.datasets[0].data = so2.values;
  airQualitySecondaryChart.data.datasets[1].data = co.values;

  airQualitySecondaryChart.update();

  console.log("✅ Secondary pollutants chart updated");
}

// ========================================
// MARINE WEATHER CHARTS
// ========================================

/**
 * Create marine daily wave heights chart (7 days)
 * Shows total wave height, swell waves, and wind waves
 */
function createMarineDailyWaveChart() {
  console.log("📊 Creating marine daily wave heights chart...");

  const ctx = document.getElementById("marineDailyWaveChart");

  if (!ctx) {
    console.warn("⚠️ marineDailyWaveChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (marineDailyWaveChart) {
    marineDailyWaveChart.destroy();
  }

  marineDailyWaveChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Total Wave Height (m)",
          data: [],
          borderColor: "#0ea5e9",
          backgroundColor: "rgba(14, 165, 233, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 3,
        },
        {
          label: "Swell Wave Height (m)",
          data: [],
          borderColor: "#6366f1",
          backgroundColor: "rgba(99, 102, 241, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          borderDash: [5, 5],
        },
        {
          label: "Wind Wave Height (m)",
          data: [],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          borderDash: [3, 3],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              // Add wave condition interpretation
              if (context.datasetIndex === 0) {
                const value = context.parsed.y;
                if (value < 0.5) return "🟢 Calm";
                if (value < 1.25) return "🟡 Smooth";
                if (value < 2.5) return "🟠 Slight";
                if (value < 4.0) return "🔴 Moderate";
                if (value < 6.0) return "🟣 Rough";
                return "⚫ Very Rough";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Wave Height (meters)",
          },
          ticks: {
            callback: function (value) {
              return value + " m";
            },
          },
        },
        x: {
          title: {
            display: true,
            text: "Date",
          },
        },
      },
    },
  });

  console.log("✅ Marine daily wave heights chart created");
  return marineDailyWaveChart;
}

/**
 * Update marine daily wave chart with API data
 */
function updateMarineDailyWaveChart(apiData) {
  console.log("📊 Updating marine daily wave heights chart...");

  if (!marineDailyWaveChart) {
    console.warn("⚠️ Marine daily wave chart not initialized");
    return;
  }

  if (!apiData || apiData.length === 0) {
    console.warn("⚠️ No marine daily data available");
    return;
  }

  const labels = [];
  const waveHeights = [];
  const swellHeights = [];
  const windWaveHeights = [];

  apiData.forEach((day) => {
    // Format date: "2025-11-12" → "Nov 12"
    const dateParts = day.valid_date.split('-');
    const year = parseInt(dateParts[0]);
    const month = parseInt(dateParts[1]) - 1;
    const dayNum = parseInt(dateParts[2]);

    const date = new Date(Date.UTC(year, month, dayNum));
    const label = date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone: "UTC"
    });
    labels.push(label);

    // Extract wave data
    waveHeights.push(day.wave_height_max || 0);
    swellHeights.push(day.swell_wave_height_max || 0);
    windWaveHeights.push(day.wind_wave_height_max || 0);
  });

  marineDailyWaveChart.data.labels = labels;
  marineDailyWaveChart.data.datasets[0].data = waveHeights;
  marineDailyWaveChart.data.datasets[1].data = swellHeights;
  marineDailyWaveChart.data.datasets[2].data = windWaveHeights;

  marineDailyWaveChart.update();

  console.log("✅ Marine daily wave heights chart updated");
}

/**
 * Create marine daily wave period chart
 * Shows wave period trends over forecast period
 */
function createMarineDailyPeriodChart() {
  console.log("📊 Creating marine daily wave period chart...");

  const ctx = document.getElementById("marineDailyPeriodChart");

  if (!ctx) {
    console.warn("⚠️ marineDailyPeriodChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (marineDailyPeriodChart) {
    marineDailyPeriodChart.destroy();
  }

  marineDailyPeriodChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          type: "bar",
          label: "Wave Period (s)",
          data: [],
          backgroundColor: "rgba(59, 130, 246, 0.7)",
          borderColor: "rgb(59, 130, 246)",
          borderWidth: 1,
          yAxisID: "y",
        },
        {
          type: "line",
          label: "Wave Direction (°)",
          data: [],
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          yAxisID: "y1",
          hidden: true, // Hidden by default, can be toggled
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              if (context.datasetIndex === 0) {
                const value = context.parsed.y;
                if (value < 5) return "⚡ Short period - choppy";
                if (value < 8) return "🌊 Medium period - normal";
                if (value < 12) return "🌀 Long period - smooth";
                return "🌊 Very long period";
              }
              if (context.datasetIndex === 1) {
                const degrees = context.parsed.y;
                const direction = getWindDirection(degrees);
                return `From ${direction}`;
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          beginAtZero: true,
          title: {
            display: true,
            text: "Wave Period (seconds)",
          },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          beginAtZero: true,
          max: 360,
          title: {
            display: true,
            text: "Wave Direction (degrees)",
          },
          grid: {
            drawOnChartArea: false,
          },
        },
        x: {
          title: {
            display: true,
            text: "Date",
          },
        },
      },
    },
  });

  console.log("✅ Marine daily wave period chart created");
  return marineDailyPeriodChart;
}

/**
 * Update marine daily period chart with API data
 */
function updateMarineDailyPeriodChart(apiData) {
  console.log("📊 Updating marine daily wave period chart...");

  if (!marineDailyPeriodChart) {
    console.warn("⚠️ Marine daily period chart not initialized");
    return;
  }

  if (!apiData || apiData.length === 0) {
    console.warn("⚠️ No marine daily period data available");
    return;
  }

  const labels = [];
  const periods = [];
  const directions = [];

  apiData.forEach((day) => {
    // Format date: "2025-11-12" → "Nov 12"
    const dateParts = day.valid_date.split('-');
    const year = parseInt(dateParts[0]);
    const month = parseInt(dateParts[1]) - 1;
    const dayNum = parseInt(dateParts[2]);

    const date = new Date(Date.UTC(year, month, dayNum));
    const label = date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone: "UTC"
    });
    labels.push(label);

    // Extract period and direction data
    periods.push(day.wave_period_max || 0);
    directions.push(day.wave_direction_dominant || 0);
  });

  marineDailyPeriodChart.data.labels = labels;
  marineDailyPeriodChart.data.datasets[0].data = periods;
  marineDailyPeriodChart.data.datasets[1].data = directions;

  marineDailyPeriodChart.update();

  console.log("✅ Marine daily wave period chart updated");
}

/**
 * Create marine hourly wave heights chart (24 hours)
 * Shows total wave height, swell waves, and wind waves
 */
function createMarineHourlyWaveChart() {
  console.log("📊 Creating marine hourly wave heights chart...");

  const ctx = document.getElementById("marineHourlyWaveChart");

  if (!ctx) {
    console.warn("⚠️ marineHourlyWaveChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (marineHourlyWaveChart) {
    marineHourlyWaveChart.destroy();
  }

  marineHourlyWaveChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Total Wave Height (m)",
          data: [],
          borderColor: "#0ea5e9",
          backgroundColor: "rgba(14, 165, 233, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 3,
        },
        {
          label: "Swell Wave Height (m)",
          data: [],
          borderColor: "#6366f1",
          backgroundColor: "rgba(99, 102, 241, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          borderDash: [5, 5],
        },
        {
          label: "Wind Wave Height (m)",
          data: [],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          borderDash: [3, 3],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              // Add wave condition interpretation
              if (context.datasetIndex === 0) {
                const value = context.parsed.y;
                if (value < 0.5) return "🟢 Calm";
                if (value < 1.25) return "🟡 Smooth";
                if (value < 2.5) return "🟠 Slight";
                if (value < 4.0) return "🔴 Moderate";
                if (value < 6.0) return "🟣 Rough";
                return "⚫ Very Rough";
              }
              return "";
            },
            footer: function (tooltipItems) {
              // Show wave direction in footer
              const index = tooltipItems[0].dataIndex;
              const waveDir = marineHourlyWaveChart.data.datasets[0].waveDirections?.[index];
              if (waveDir !== undefined) {
                const direction = getWindDirection(waveDir);
                return `Direction: ${direction} (${waveDir}°)`;
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Wave Height (meters)",
          },
          ticks: {
            callback: function (value) {
              return value + " m";
            },
          },
        },
        x: {
          title: {
            display: true,
            text: "Hour",
          },
        },
      },
    },
  });

  console.log("✅ Marine hourly wave heights chart created");
  return marineHourlyWaveChart;
}

/**
 * Update marine hourly wave chart with API data
 */
function updateMarineHourlyWaveChart(apiData) {
  console.log("📊 Updating marine hourly wave heights chart...");

  if (!marineHourlyWaveChart) {
    console.warn("⚠️ Marine hourly wave chart not initialized");
    return;
  }

  if (!apiData || !apiData.parameters) {
    console.warn("⚠️ No marine hourly data available");
    return;
  }

  const waveHeight = apiData.parameters.wave_height;
  const swellHeight = apiData.parameters.swell_wave_height;
  const windWaveHeight = apiData.parameters.wind_wave_height;
  const waveDirection = apiData.parameters.wave_direction;

  if (!waveHeight || !swellHeight || !windWaveHeight) {
    console.warn("⚠️ Missing wave height parameters");
    return;
  }

  // Format labels (hours)
  const labels = waveHeight.times.map(formatHourLabel);

  marineHourlyWaveChart.data.labels = labels;
  marineHourlyWaveChart.data.datasets[0].data = waveHeight.values;
  marineHourlyWaveChart.data.datasets[0].waveDirections = waveDirection?.values || [];
  marineHourlyWaveChart.data.datasets[1].data = swellHeight.values;
  marineHourlyWaveChart.data.datasets[2].data = windWaveHeight.values;

  marineHourlyWaveChart.update();

  console.log("✅ Marine hourly wave heights chart updated");
}

/**
 * Create marine hourly wave period & temperature chart
 * Shows wave period and sea surface temperature
 */
function createMarineHourlyPeriodChart() {
  console.log("📊 Creating marine hourly period & temperature chart...");

  const ctx = document.getElementById("marineHourlyPeriodChart");

  if (!ctx) {
    console.warn("⚠️ marineHourlyPeriodChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (marineHourlyPeriodChart) {
    marineHourlyPeriodChart.destroy();
  }

  marineHourlyPeriodChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Wave Period (s)",
          data: [],
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 2,
          yAxisID: "y",
        },
        {
          label: "Sea Temperature (°C)",
          data: [],
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              if (context.datasetIndex === 0) {
                const value = context.parsed.y;
                if (value < 5) return "⚡ Short period - choppy";
                if (value < 8) return "🌊 Medium period - normal";
                if (value < 12) return "🌀 Long period - smooth";
                return "🌊 Very long period";
              }
              if (context.datasetIndex === 1) {
                const value = context.parsed.y;
                if (value < 10) return "🥶 Very cold";
                if (value < 15) return "❄️ Cold";
                if (value < 20) return "😊 Cool";
                if (value < 25) return "🏊 Comfortable";
                if (value < 30) return "🌞 Warm";
                return "🔥 Very warm";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          beginAtZero: true,
          title: {
            display: true,
            text: "Wave Period (seconds)",
          },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          beginAtZero: false,
          title: {
            display: true,
            text: "Temperature (°C)",
          },
          grid: {
            drawOnChartArea: false,
          },
        },
        x: {
          title: {
            display: true,
            text: "Hour",
          },
        },
      },
    },
  });

  console.log("✅ Marine hourly period & temperature chart created");
  return marineHourlyPeriodChart;
}

/**
 * Update marine hourly period chart with API data
 */
function updateMarineHourlyPeriodChart(apiData) {
  console.log("📊 Updating marine hourly period & temperature chart...");

  if (!marineHourlyPeriodChart) {
    console.warn("⚠️ Marine hourly period chart not initialized");
    return;
  }

  if (!apiData || !apiData.parameters) {
    console.warn("⚠️ No marine hourly period data available");
    return;
  }

  const wavePeriod = apiData.parameters.wave_period;
  const seaTemp = apiData.parameters.sea_temp;

  if (!wavePeriod || !seaTemp) {
    console.warn("⚠️ Missing wave period or temperature parameters");
    return;
  }

  // Format labels (hours)
  const labels = wavePeriod.times.map(formatHourLabel);

  marineHourlyPeriodChart.data.labels = labels;
  marineHourlyPeriodChart.data.datasets[0].data = wavePeriod.values;
  marineHourlyPeriodChart.data.datasets[1].data = seaTemp.values;

  marineHourlyPeriodChart.update();

  console.log("✅ Marine hourly period & temperature chart updated");
}
/**
 * Create marine wave height chart (LEGACY - for hourly data)
 * Keep this for backward compatibility
 */
function createMarineWaveChart(data) {
  console.log("📊 Creating marine wave chart (hourly)...");

  const ctx = document.getElementById("marineWaveChart");

  if (!ctx) {
    console.warn("⚠️ marineWaveChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (marineWaveChart) {
    marineWaveChart.destroy();
  }

  // Sample data (24 hours, every 3 hours)
  const labels = [
    "00:00",
    "03:00",
    "06:00",
    "09:00",
    "12:00",
    "15:00",
    "18:00",
    "21:00",
    "24:00",
  ];

  // Wave heights in meters
  const totalWaveHeight = [1.2, 1.4, 1.6, 1.8, 2.1, 2.3, 2.0, 1.7, 1.5];
  const swellWaveHeight = [0.8, 0.9, 1.0, 1.2, 1.4, 1.5, 1.3, 1.1, 1.0];
  const windWaveHeight = [0.4, 0.5, 0.6, 0.6, 0.7, 0.8, 0.7, 0.6, 0.5];

  marineWaveChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Total Wave Height (m)",
          data: totalWaveHeight,
          borderColor: "#0ea5e9",
          backgroundColor: "rgba(14, 165, 233, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 3,
        },
        {
          label: "Swell Wave Height (m)",
          data: swellWaveHeight,
          borderColor: "#6366f1",
          backgroundColor: "rgba(99, 102, 241, 0.1)",
          tension: 0.4,
          fill: true,
          borderDash: [5, 5],
        },
        {
          label: "Wind Wave Height (m)",
          data: windWaveHeight,
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: true,
          borderDash: [3, 3],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              // Add wave condition interpretation
              const value = context.parsed.y;
              if (context.datasetIndex === 0) {
                if (value < 0.5) return "Calm";
                if (value < 1.25) return "Smooth";
                if (value < 2.5) return "Slight";
                if (value < 4.0) return "Moderate";
                return "Rough";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 3,
          title: {
            display: true,
            text: "Wave Height (meters)",
          },
          ticks: {
            callback: function (value) {
              return value + " m";
            },
          },
        },
        x: {
          title: {
            display: true,
            text: "Time",
          },
        },
      },
    },
  });

  console.log("✅ Marine wave chart (hourly) created");
}

// ========================================
// SATELLITE RADIATION CHARTS
// ========================================

/**
 * Create satellite daily radiation components chart
 * Shows shortwave, direct, and diffuse radiation over days
 */
function createSatelliteDailyRadiationChart() {
  console.log("📊 Creating satellite daily radiation chart...");

  const ctx = document.getElementById("satelliteDailyRadiationChart");

  if (!ctx) {
    console.warn("⚠️ satelliteDailyRadiationChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (satelliteDailyRadiationChart) {
    satelliteDailyRadiationChart.destroy();
  }

  satelliteDailyRadiationChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Shortwave Radiation (W/m²)",
          data: [],
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.2)",
          tension: 0.4,
          fill: true,
          borderWidth: 3,
        },
        {
          label: "Direct Radiation (W/m²)",
          data: [],
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
        },
        {
          label: "Diffuse Radiation (W/m²)",
          data: [],
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6, 182, 212, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              const value = context.parsed.y;
              if (context.datasetIndex === 0) {
                // Shortwave radiation
                if (value > 700) return "☀️ Excellent solar conditions";
                if (value > 400) return "🌤️ Good solar output";
                if (value > 200) return "⛅ Moderate solar output";
                return "🌥️ Low solar output";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Solar Radiation (W/m²)",
          },
          ticks: {
            callback: function (value) {
              return value + " W/m²";
            },
          },
        },
        x: {
          title: {
            display: true,
            text: "Date",
          },
        },
      },
    },
  });

  console.log("✅ Satellite daily radiation chart created");
  return satelliteDailyRadiationChart;
}

/**
 * Update satellite daily radiation chart with API data
 */
function updateSatelliteDailyRadiationChart(apiData) {
  console.log("📊 Updating satellite daily radiation chart...");

  if (!satelliteDailyRadiationChart) {
    console.warn("⚠️ Satellite radiation chart not initialized");
    return;
  }

  if (!apiData || apiData.length === 0) {
    console.warn("⚠️ No satellite radiation data available");
    return;
  }

  const labels = [];
  const shortwaveRadiation = [];
  const directRadiation = [];
  const diffuseRadiation = [];

  // Sort by created_at (newest first)
  const sortedData = [...apiData].sort((a, b) => 
    new Date(a.created_at) - new Date(b.created_at)
  );

  sortedData.forEach((day) => {
    // Format date from created_at: "2025-11-11T05:00:06" → "Nov 11"
    const date = new Date(day.created_at);
    const label = date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone: "UTC"
    });
    labels.push(label);

    // Extract radiation data
    shortwaveRadiation.push(day.shortwave_radiation || 0);
    directRadiation.push(day.direct_radiation || 0);
    diffuseRadiation.push(day.diffuse_radiation || 0);
  });

  satelliteDailyRadiationChart.data.labels = labels;
  satelliteDailyRadiationChart.data.datasets[0].data = shortwaveRadiation;
  satelliteDailyRadiationChart.data.datasets[1].data = directRadiation;
  satelliteDailyRadiationChart.data.datasets[2].data = diffuseRadiation;

  satelliteDailyRadiationChart.update();

  console.log("✅ Satellite daily radiation chart updated");
}

/**
 * Create satellite daily irradiance chart
 * Shows DNI, GTI, and terrestrial radiation
 */
function createSatelliteDailyIrradianceChart() {
  console.log("📊 Creating satellite daily irradiance chart...");

  const ctx = document.getElementById("satelliteDailyIrradianceChart");

  if (!ctx) {
    console.warn("⚠️ satelliteDailyIrradianceChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (satelliteDailyIrradianceChart) {
    satelliteDailyIrradianceChart.destroy();
  }

  satelliteDailyIrradianceChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          type: "bar",
          label: "Direct Normal Irradiance (W/m²)",
          data: [],
          backgroundColor: "rgba(239, 68, 68, 0.7)",
          borderColor: "rgb(239, 68, 68)",
          borderWidth: 1,
          yAxisID: "y",
        },
        {
          type: "bar",
          label: "Global Tilted Irradiance (W/m²)",
          data: [],
          backgroundColor: "rgba(245, 158, 11, 0.7)",
          borderColor: "rgb(245, 158, 11)",
          borderWidth: 1,
          yAxisID: "y",
        },
        {
          type: "line",
          label: "Terrestrial Radiation (W/m²)",
          data: [],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 3,
          yAxisID: "y",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              if (context.datasetIndex === 0) {
                // DNI
                const value = context.parsed.y;
                if (value > 800) return "🌞 Excellent for solar panels";
                if (value > 500) return "☀️ Very good conditions";
                if (value > 300) return "🌤️ Good solar potential";
                return "⛅ Moderate conditions";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Irradiance (W/m²)",
          },
          ticks: {
            callback: function (value) {
              return value + " W/m²";
            },
          },
        },
        x: {
          title: {
            display: true,
            text: "Date",
          },
        },
      },
    },
  });

  console.log("✅ Satellite daily irradiance chart created");
  return satelliteDailyIrradianceChart;
}

/**
 * Update satellite daily irradiance chart with API data
 */
function updateSatelliteDailyIrradianceChart(apiData) {
  console.log("📊 Updating satellite daily irradiance chart...");

  if (!satelliteDailyIrradianceChart) {
    console.warn("⚠️ Satellite irradiance chart not initialized");
    return;
  }

  if (!apiData || apiData.length === 0) {
    console.warn("⚠️ No satellite irradiance data available");
    return;
  }

  const labels = [];
  const dni = [];
  const gti = [];
  const terrestrial = [];

  // Sort by created_at (newest first)
  const sortedData = [...apiData].sort((a, b) => 
    new Date(a.created_at) - new Date(b.created_at)
  );

  sortedData.forEach((day) => {
    // Format date from created_at: "2025-11-11T05:00:06" → "Nov 11"
    const date = new Date(day.created_at);
    const label = date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      timeZone: "UTC"
    });
    labels.push(label);

    // Extract irradiance data
    dni.push(day.direct_normal_irradiance || 0);
    gti.push(day.global_tilted_irradiance || 0);
    terrestrial.push(day.terrestrial_radiation || 0);
  });

  satelliteDailyIrradianceChart.data.labels = labels;
  satelliteDailyIrradianceChart.data.datasets[0].data = dni;
  satelliteDailyIrradianceChart.data.datasets[1].data = gti;
  satelliteDailyIrradianceChart.data.datasets[2].data = terrestrial;

  satelliteDailyIrradianceChart.update();

  console.log("✅ Satellite daily irradiance chart updated");
}

// ========================================
// CLIMATE PROJECTION CHARTS
// ========================================

/**
 * Create climate temperature trends chart (2022-2026)
 * Shows max, mean, and min temperatures over 5 years
 */
function createClimateTempTrendsChart() {
  console.log("📊 Creating climate temperature trends chart...");

  const ctx = document.getElementById("climateTempTrendsChart");

  if (!ctx) {
    console.warn("⚠️ climateTempTrendsChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (climateTempTrendsChart) {
    climateTempTrendsChart.destroy();
  }

  climateTempTrendsChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Max Temperature (°C)",
          data: [],
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.05)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
        },
        {
          label: "Mean Temperature (°C)",
          data: [],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 3,
          pointRadius: 0,
          pointHoverRadius: 4,
        },
        {
          label: "Min Temperature (°C)",
          data: [],
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59, 130, 246, 0.05)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            title: function(context) {
              return context[0].label;
            },
            afterLabel: function (context) {
              if (context.datasetIndex === 1) {
                const value = context.parsed.y;
                if (value < 10) return "🥶 Cold period";
                if (value < 15) return "😊 Cool period";
                if (value < 20) return "🌤️ Mild period";
                if (value < 25) return "🌞 Warm period";
                return "🔥 Hot period";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: false,
          title: {
            display: true,
            text: "Temperature (°C)",
          },
          ticks: {
            callback: function (value) {
              return value + "°C";
            },
          },
        },
        x: {
          title: {
            display: true,
            text: "Date (2022-2026)",
          },
          ticks: {
            maxTicksLimit: 20,
            maxRotation: 45,
            minRotation: 45,
          },
        },
      },
    },
  });

  console.log("✅ Climate temperature trends chart created");
  return climateTempTrendsChart;
}

/**
 * Update climate temperature trends chart with API data
 */
function updateClimateTempTrendsChart(apiData) {
  console.log("📊 Updating climate temperature trends chart...");

  if (!climateTempTrendsChart) {
    console.warn("⚠️ Climate temperature trends chart not initialized");
    return;
  }

  if (!apiData || !apiData.daily_data || apiData.daily_data.length === 0) {
    console.warn("⚠️ No climate temperature data available");
    return;
  }

  const labels = [];
  const maxTemps = [];
  const meanTemps = [];
  const minTemps = [];

  // Sample every 7 days to reduce data points (weekly average)
  const sampledData = apiData.daily_data.filter((_, index) => index % 7 === 0);

  sampledData.forEach((day) => {
    // Format date: "2022-01-01" → "Jan '22"
    const dateParts = day.valid_date.split('-');
    const year = parseInt(dateParts[0]);
    const month = parseInt(dateParts[1]) - 1;
    const dayNum = parseInt(dateParts[2]);

    const date = new Date(Date.UTC(year, month, dayNum));
    const label = date.toLocaleDateString("en-US", {
      month: "short",
      year: "2-digit",
      timeZone: "UTC"
    });
    labels.push(label);

    maxTemps.push(day.temperature_2m_max || null);
    meanTemps.push(day.temperature_2m_mean || null);
    minTemps.push(day.temperature_2m_min || null);
  });

  climateTempTrendsChart.data.labels = labels;
  climateTempTrendsChart.data.datasets[0].data = maxTemps;
  climateTempTrendsChart.data.datasets[1].data = meanTemps;
  climateTempTrendsChart.data.datasets[2].data = minTemps;

  climateTempTrendsChart.update();

  console.log(`✅ Climate temperature trends chart updated with ${sampledData.length} data points`);
}

/**
 * Create climate precipitation & humidity chart
 * Shows annual precipitation and humidity patterns
 */
function createClimatePrecipHumidityChart() {
  console.log("📊 Creating climate precipitation & humidity chart...");

  const ctx = document.getElementById("climatePrecipHumidityChart");

  if (!ctx) {
    console.warn("⚠️ climatePrecipHumidityChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (climatePrecipHumidityChart) {
    climatePrecipHumidityChart.destroy();
  }

  climatePrecipHumidityChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          type: "bar",
          label: "Precipitation (mm)",
          data: [],
          backgroundColor: "rgba(59, 130, 246, 0.7)",
          borderColor: "rgb(59, 130, 246)",
          borderWidth: 1,
          yAxisID: "y",
        },
        {
          type: "line",
          label: "Mean Humidity (%)",
          data: [],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          yAxisID: "y1",
          pointRadius: 0,
          pointHoverRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              if (context.datasetIndex === 0) {
                const value = context.parsed.y;
                if (value === 0) return "☀️ No precipitation";
                if (value < 5) return "🌤️ Light precipitation";
                if (value < 20) return "🌧️ Moderate precipitation";
                if (value < 50) return "⛈️ Heavy precipitation";
                return "🌊 Very heavy precipitation";
              }
              if (context.datasetIndex === 1) {
                const value = context.parsed.y;
                if (value < 40) return "🏜️ Dry";
                if (value < 60) return "👌 Comfortable";
                if (value < 80) return "💧 Humid";
                return "🌊 Very humid";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          beginAtZero: true,
          title: {
            display: true,
            text: "Precipitation (mm)",
          },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: "Humidity (%)",
          },
          grid: {
            drawOnChartArea: false,
          },
        },
        x: {
          title: {
            display: true,
            text: "Date (2022-2026)",
          },
          ticks: {
            maxTicksLimit: 20,
            maxRotation: 45,
            minRotation: 45,
          },
        },
      },
    },
  });

  console.log("✅ Climate precipitation & humidity chart created");
  return climatePrecipHumidityChart;
}

/**
 * Update climate precipitation & humidity chart with API data
 */
function updateClimatePrecipHumidityChart(apiData) {
  console.log("📊 Updating climate precipitation & humidity chart...");

  if (!climatePrecipHumidityChart) {
    console.warn("⚠️ Climate precipitation chart not initialized");
    return;
  }

  if (!apiData || !apiData.daily_data || apiData.daily_data.length === 0) {
    console.warn("⚠️ No climate precipitation data available");
    return;
  }

  const labels = [];
  const precipitation = [];
  const humidity = [];

  // Sample every 7 days to reduce data points
  const sampledData = apiData.daily_data.filter((_, index) => index % 7 === 0);

  sampledData.forEach((day) => {
    // Format date: "2022-01-01" → "Jan '22"
    const dateParts = day.valid_date.split('-');
    const year = parseInt(dateParts[0]);
    const month = parseInt(dateParts[1]) - 1;
    const dayNum = parseInt(dateParts[2]);

    const date = new Date(Date.UTC(year, month, dayNum));
    const label = date.toLocaleDateString("en-US", {
      month: "short",
      year: "2-digit",
      timeZone: "UTC"
    });
    labels.push(label);

    precipitation.push(day.precipitation_sum || 0);
    humidity.push(day.relative_humidity_2m_mean || null);
  });

  climatePrecipHumidityChart.data.labels = labels;
  climatePrecipHumidityChart.data.datasets[0].data = precipitation;
  climatePrecipHumidityChart.data.datasets[1].data = humidity;

  climatePrecipHumidityChart.update();

  console.log(`✅ Climate precipitation & humidity chart updated with ${sampledData.length} data points`);
}

/**
 * Create climate wind & radiation chart
 * Shows wind speed and solar radiation trends
 */
function createClimateWindRadiationChart() {
  console.log("📊 Creating climate wind & radiation chart...");

  const ctx = document.getElementById("climateWindRadiationChart");

  if (!ctx) {
    console.warn("⚠️ climateWindRadiationChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (climateWindRadiationChart) {
    climateWindRadiationChart.destroy();
  }

  climateWindRadiationChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Max Wind Speed (km/h)",
          data: [],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 2,
          yAxisID: "y",
          pointRadius: 0,
          pointHoverRadius: 4,
        },
        {
          label: "Solar Radiation (MJ/m²)",
          data: [],
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          yAxisID: "y1",
          pointRadius: 0,
          pointHoverRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            afterLabel: function (context) {
              if (context.datasetIndex === 0) {
                const value = context.parsed.y;
                if (value < 20) return "🍃 Light wind";
                if (value < 40) return "💨 Moderate wind";
                if (value < 60) return "🌬️ Strong wind";
                return "⚠️ Very strong wind";
              }
              if (context.datasetIndex === 1) {
                const value = context.parsed.y;
                if (value > 25) return "☀️ Excellent solar";
                if (value > 15) return "🌤️ Good solar";
                if (value > 10) return "⛅ Moderate solar";
                return "🌥️ Low solar";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          beginAtZero: true,
          title: {
            display: true,
            text: "Wind Speed (km/h)",
          },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          beginAtZero: true,
          title: {
            display: true,
            text: "Solar Radiation (MJ/m²)",
          },
          grid: {
            drawOnChartArea: false,
          },
        },
        x: {
          title: {
            display: true,
            text: "Date (2022-2026)",
          },
          ticks: {
            maxTicksLimit: 20,
            maxRotation: 45,
            minRotation: 45,
          },
        },
      },
    },
  });

  console.log("✅ Climate wind & radiation chart created");
  return climateWindRadiationChart;
}

/**
 * Update climate wind & radiation chart with API data
 */
function updateClimateWindRadiationChart(apiData) {
  console.log("📊 Updating climate wind & radiation chart...");

  if (!climateWindRadiationChart) {
    console.warn("⚠️ Climate wind chart not initialized");
    return;
  }

  if (!apiData || !apiData.daily_data || apiData.daily_data.length === 0) {
    console.warn("⚠️ No climate wind data available");
    return;
  }

  const labels = [];
  const windSpeed = [];
  const radiation = [];

  // Sample every 7 days to reduce data points
  const sampledData = apiData.daily_data.filter((_, index) => index % 7 === 0);

  sampledData.forEach((day) => {
    // Format date: "2022-01-01" → "Jan '22"
    const dateParts = day.valid_date.split('-');
    const year = parseInt(dateParts[0]);
    const month = parseInt(dateParts[1]) - 1;
    const dayNum = parseInt(dateParts[2]);

    const date = new Date(Date.UTC(year, month, dayNum));
    const label = date.toLocaleDateString("en-US", {
      month: "short",
      year: "2-digit",
      timeZone: "UTC"
    });
    labels.push(label);

    windSpeed.push(day.wind_speed_10m_max || null);
    // Convert from Wh/m² to MJ/m² (divide by ~277.778)
    const radiationMJ = day.shortwave_radiation_sum ? (day.shortwave_radiation_sum / 277.778).toFixed(2) : null;
    radiation.push(radiationMJ ? parseFloat(radiationMJ) : null);
  });

  climateWindRadiationChart.data.labels = labels;
  climateWindRadiationChart.data.datasets[0].data = windSpeed;
  climateWindRadiationChart.data.datasets[1].data = radiation;

  climateWindRadiationChart.update();

  console.log(`✅ Climate wind & radiation chart updated with ${sampledData.length} data points`);
}


// ========================================
// INITIALIZE CHARTS ON SECTION VIEW
// ========================================

/**
 * Initialize all weather charts
 *
 * Creates sample charts when dashboard loads
 * Later will fetch real data from backend
 */
function initializeWeatherCharts() {
  console.log("🎨 Initializing weather charts...");

  // Create weather forecast charts with sample data
  createWeatherDailyChart();
  createWeatherPrecipChart();
  createWeatherUvChart();
  createWeatherWindChart();
  createWeatherHourlyPrecipChart();
  createWeatherHourlyWindChart();
  createWeatherHourlyTempChart();
  createAirQualityAqiChart();
  createAirQualityPollutantsChart();
  createAirQualitySecondaryChart();
  createMarineDailyPeriodChart();
  createMarineDailyWaveChart();
  createMarineHourlyPeriodChart();
  createMarineHourlyWaveChart();

  createSatelliteDailyIrradianceChart();
  createSatelliteDailyRadiationChart();

  createClimatePrecipHumidityChart();
  createClimateTempTrendsChart();
  createClimateWindRadiationChart();

  console.log("✅ Weather charts initialized");
}
