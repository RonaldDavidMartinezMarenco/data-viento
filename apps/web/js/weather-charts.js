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

let weatherDailyChart = null;
let weatherWindChart = null;
let airQualityChart = null;
let marineWaveChart = null;
let satelliteChart = null;
let climateTempChart = null;

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
    const date = new Date(day.valid_date);
    const label = date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
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
  console.log("📊 Creating weather wind chart...");

  const ctx = document.getElementById("weatherWindChart");

  if (!ctx) {
    console.warn("⚠️ weatherWindChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (weatherWindChart) {
    weatherWindChart.destroy();
  }

  // Sample data (24 hours)
  const labels = [
    "00:00",
    "02:00",
    "04:00",
    "06:00",
    "08:00",
    "10:00",
    "12:00",
    "14:00",
    "16:00",
    "18:00",
    "20:00",
    "22:00",
  ];
  const windSpeeds = [12, 10, 8, 9, 11, 15, 18, 20, 19, 16, 14, 13];

  weatherWindChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Wind Speed (km/h)",
          data: windSpeeds,
          backgroundColor: "rgba(34, 197, 94, 0.7)",
          borderColor: "rgb(34, 197, 94)",
          borderWidth: 1,
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
            text: "Time",
          },
        },
      },
    },
  });

  console.log("✅ Weather wind chart created");
}

// ========================================
// AIR QUALITY CHARTS
// ========================================

/**
 * Create air quality index chart
 *
 * Shows PM2.5, PM10, and overall AQI over 24 hours
 *
 * @param {Array} data - Air quality data from backend
 */
function createAirQualityChart() {
  console.log("📊 Creating air quality chart...");

  const ctx = document.getElementById("airQualityChart");

  if (!ctx) {
    console.warn("⚠️ airQualityChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (airQualityChart) {
    airQualityChart.destroy();
  }

  // Sample data (24 hours)
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

  // Air Quality Index values (0-500 scale)
  // 0-50: Good (Green)
  // 51-100: Moderate (Yellow)
  // 101-150: Unhealthy for Sensitive Groups (Orange)
  // 151-200: Unhealthy (Red)
  // 201+: Very Unhealthy (Purple)
  const aqiValues = [45, 52, 58, 65, 72, 68, 55, 48, 42];
  const pm25Values = [12, 15, 18, 22, 25, 23, 18, 15, 11];
  const pm10Values = [25, 28, 32, 38, 42, 40, 32, 28, 24];

  airQualityChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "AQI (Air Quality Index)",
          data: aqiValues,
          borderColor: "#8b5cf6",
          backgroundColor: "rgba(139, 92, 246, 0.1)",
          tension: 0.4,
          fill: true,
          yAxisID: "y",
        },
        {
          label: "PM2.5 (μg/m³)",
          data: pm25Values,
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          tension: 0.4,
          fill: true,
          yAxisID: "y1",
        },
        {
          label: "PM10 (μg/m³)",
          data: pm10Values,
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6, 182, 212, 0.1)",
          tension: 0.4,
          fill: true,
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
              // Add AQI interpretation to tooltip
              if (context.datasetIndex === 0) {
                const value = context.parsed.y;
                if (value <= 50) return "Good";
                if (value <= 100) return "Moderate";
                if (value <= 150) return "Unhealthy for Sensitive";
                if (value <= 200) return "Unhealthy";
                return "Very Unhealthy";
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
          max: 200,
          title: {
            display: true,
            text: "AQI Value",
          },
          // Add color bands for AQI levels
          ticks: {
            callback: function (value) {
              return value;
            },
          },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          beginAtZero: true,
          title: {
            display: true,
            text: "PM Concentration (μg/m³)",
          },
          grid: {
            drawOnChartArea: false,
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

  console.log("✅ Air quality chart created");
}

// ========================================
// MARINE WEATHER CHARTS
// ========================================

/**
 * Create marine wave height chart
 *
 * Shows wave height forecast, swell waves, and wind waves
 *
 * @param {Array} data - Marine data from backend
 */
function createMarineWaveChart(data) {
  console.log("📊 Creating marine wave chart...");

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

  console.log("✅ Marine wave chart created");
}
// ========================================
// SATELLITE RADIATION CHARTS
// ========================================

/**
 * Create satellite radiation chart
 *
 * Shows solar radiation components throughout the day
 * - Shortwave Radiation
 * - Direct Radiation
 * - Diffuse Radiation
 *
 * @param {Array} data - Satellite radiation data from backend
 */
function createSatelliteChart(data) {
  console.log("📊 Creating satellite radiation chart...");

  const ctx = document.getElementById("satelliteChart");

  if (!ctx) {
    console.warn("⚠️ satelliteChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (satelliteChart) {
    satelliteChart.destroy();
  }

  // Sample data (12 hours daylight, hourly)
  const labels = [
    "06:00",
    "07:00",
    "08:00",
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
    "18:00",
  ];

  // Radiation values in W/m² (Watts per square meter)
  const shortwaveRadiation = [
    50, 150, 300, 450, 600, 750, 850, 800, 700, 550, 400, 250, 100,
  ];
  const directRadiation = [
    30, 100, 200, 350, 480, 600, 680, 640, 560, 440, 320, 200, 80,
  ];
  const diffuseRadiation = [
    20, 50, 100, 100, 120, 150, 170, 160, 140, 110, 80, 50, 20,
  ];

  satelliteChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Shortwave Radiation (W/m²)",
          data: shortwaveRadiation,
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.2)",
          tension: 0.4,
          fill: true,
          borderWidth: 2,
        },
        {
          label: "Direct Radiation (W/m²)",
          data: directRadiation,
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
        },
        {
          label: "Diffuse Radiation (W/m²)",
          data: diffuseRadiation,
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
            label: function (context) {
              let label = context.dataset.label || "";
              if (label) {
                label += ": ";
              }
              if (context.parsed.y !== null) {
                label += context.parsed.y + " W/m²";
              }
              return label;
            },
            afterBody: function (context) {
              // Add solar panel efficiency note
              const value = context[0].parsed.y;
              if (value > 700) {
                return ["", "☀️ Excellent for solar panels"];
              } else if (value > 400) {
                return ["", "🌤️ Good solar conditions"];
              } else if (value > 200) {
                return ["", "⛅ Moderate solar output"];
              }
              return ["", "🌥️ Low solar output"];
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 1000,
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
            text: "Time of Day",
          },
        },
      },
    },
  });

  console.log("✅ Satellite radiation chart created");
}
// ========================================
// CLIMATE CHANGE CHARTS
// ========================================

/**
 * Create climate temperature trends chart
 *
 * Shows historical and projected temperature trends
 * - Mean Temperature
 * - Max Temperature
 * - Min Temperature
 *
 * @param {Array} data - Climate data from backend
 */
function createClimateTempChart(data) {
  console.log("📊 Creating climate temperature chart...");

  const ctx = document.getElementById("climateTempChart");

  if (!ctx) {
    console.warn("⚠️ climateTempChart canvas not found");
    return;
  }

  // Destroy existing chart if it exists
  if (climateTempChart) {
    climateTempChart.destroy();
  }

  // Sample data (12 months - annual trend)
  const labels = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];

  // Temperature values in Celsius
  const meanTemperature = [8, 10, 13, 16, 20, 24, 27, 26, 23, 18, 12, 9];
  const maxTemperature = [12, 14, 18, 22, 26, 30, 33, 32, 28, 23, 16, 13];
  const minTemperature = [4, 6, 8, 10, 14, 18, 21, 20, 18, 13, 8, 5];

  climateTempChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Mean Temperature (°C)",
          data: meanTemperature,
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: true,
          borderWidth: 3,
        },
        {
          label: "Max Temperature (°C)",
          data: maxTemperature,
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.05)",
          tension: 0.4,
          fill: false,
          borderWidth: 2,
          borderDash: [5, 5],
        },
        {
          label: "Min Temperature (°C)",
          data: minTemperature,
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59, 130, 246, 0.05)",
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
            label: function (context) {
              let label = context.dataset.label || "";
              if (label) {
                label += ": ";
              }
              if (context.parsed.y !== null) {
                label += context.parsed.y + "°C";
              }
              return label;
            },
            afterBody: function (context) {
              // Add seasonal context
              const monthIndex = context[0].dataIndex;
              if (monthIndex >= 0 && monthIndex <= 2) {
                return ["", "❄️ Winter Season"];
              } else if (monthIndex >= 3 && monthIndex <= 5) {
                return ["", "🌸 Spring Season"];
              } else if (monthIndex >= 6 && monthIndex <= 8) {
                return ["", "☀️ Summer Season"];
              } else {
                return ["", "🍂 Autumn Season"];
              }
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
            text: "Month",
          },
        },
      },
    },
  });

  console.log("✅ Climate temperature chart created");
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
  createWeatherWindChart();
  createAirQualityChart();
  createMarineWaveChart();
  createSatelliteChart();
  createClimateTempChart();

  console.log("✅ Weather charts initialized");
}
