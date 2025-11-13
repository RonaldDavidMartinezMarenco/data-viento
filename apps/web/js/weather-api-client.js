/**
 * DataViento - Weather API Client
 *
 * Simple API client for fetching weather data from backend
 * Uses existing authentication patterns from auth.js
 */

/**
 * Weather API Client
 */
class WeatherApiClient {
    constructor() {
        this.baseUrl = getApiUrl('');
    }

    /**
     * Fetch daily weather forecast for a location
     *
     * @param {number} locationId - Location ID
     * @returns {Promise<Object>} API response with daily forecast data
     * @throws {Error} When API call fails
     */


    async fetchDailyForecast(locationId) {
        return await this.fetchData(`/weather/daily/${locationId}`)
    }

    async fetchCurrentData(locationId) {
        return await this.fetchData(`/weather/current/${locationId}`)
    }

    async fetchHourlyData(locationId) {
        return await this.fetchData(`/weather/hourly/${locationId}`)
    }

    async fetchAirQualityCurrentData(locationId) {
        return await this.fetchData(`/air-quality/current/${locationId}`)
    }

    async fetchAirQualityHourlyData(locationId) {
        return await this.fetchData(`/air-quality/hourly/${locationId}`)
    }

    async fetchMarineCurrentData(locationId) {
        return await this.fetchData(`/marine/current/${locationId}`)
    }

    async fetchMarineHourlyData(locationId) {
        return await this.fetchData(`/marine/hourly/${locationId}`)
    }
    
    async fetchMarineDailyData(locationId) {
        return await this.fetchData(`/marine/daily/${locationId}`)
    }

    async fetchSatelliteDailyData(locationId) {
        return await this.fetchData(`/satellite/daily/${locationId}`)
    }

    async fetchClimateProjection(locationId) {
        return await this.fetchData(`/climate/projection/${locationId}`)
    }

    async fetchData(endpoint) {
        const token = localStorage.getItem("access_token");

        if (!token) {
            throw new Error("No authentication token found");
        }

        const apiUrl = getApiUrl(endpoint);

        try {
            const response = await fetch(apiUrl, {
                method: "GET",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // Token expired or invalid - clear tokens and redirect to login
                    localStorage.removeItem("access_token");
                    localStorage.removeItem("refresh_token");
                    window.location.href = "/login.html";
                    throw new Error("Authentication failed");
                }

                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.detail || "API returned unsuccessful response");
            }

            return data;

        } catch (error) {
            console.error("Error fetching current forecast:", error);
            throw error;
        }
    
    }
}

// Create global instance
window.weatherApiClient = new WeatherApiClient();