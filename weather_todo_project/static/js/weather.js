// Weather Module
class WeatherManager {
    constructor() {
        this.apiUrl = weatherApiUrl;
        this.historyUrl = historyApiUrl;
        this.initEventListeners();
        this.loadSearchHistory();
    }

    initEventListeners() {
        $('#searchWeather').on('click', () => this.searchWeather());
        $('#cityInput').on('keypress', (e) => {
            if (e.which === 13) this.searchWeather();
        });
        $('#getLocation').on('click', () => this.getLocationWeather());
    }

    searchWeather() {
        const city = $('#cityInput').val().trim();
        if (!city) {
            this.showNotification('Please enter a city name', 'warning');
            return;
        }

        this.showLoading(true);
        
        $.ajax({
            url: this.apiUrl,
            method: 'GET',
            data: { city: city },
            success: (response) => {
                this.displayWeather(response);
                this.showLoading(false);
                this.loadSearchHistory(); // Reload history
            },
            error: (xhr) => {
                this.showLoading(false);
                const error = xhr.responseJSON?.error || 'City not found';
                this.showNotification(error, 'danger');
            }
        });
    }

    getLocationWeather() {
        if (!navigator.geolocation) {
            this.showNotification('Geolocation is not supported by your browser', 'warning');
            return;
        }

        this.showLoading(true);
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                this.getWeatherByCoords(position.coords.latitude, position.coords.longitude);
            },
            (error) => {
                this.showLoading(false);
                this.showNotification('Unable to get your location', 'danger');
            }
        );
    }

    getWeatherByCoords(lat, lon) {
        // Using OpenWeatherMap API directly with coordinates
        $.ajax({
            url: 'https://api.openweathermap.org/data/2.5/weather',
            method: 'GET',
            data: {
                lat: lat,
                lon: lon,
                appid: '{{ WEATHER_API_KEY }}', // This will be replaced by Django template
                units: 'metric'
            },
            success: (response) => {
                $('#cityInput').val(response.name);
                this.searchWeather();
            },
            error: () => {
                this.showLoading(false);
                this.showNotification('Unable to get weather for your location', 'danger');
            }
        });
    }

    displayWeather(data) {
        const weatherHtml = `
            <div class="weather-card fade-in">
                <div class="row align-items-center">
                    <div class="col-md-6">
                        <h2>${data.city}, ${data.country}</h2>
                        <div class="weather-temp">${data.temperature}°C</div>
                        <p class="lead">${data.description}</p>
                    </div>
                    <div class="col-md-6 text-center">
                        <img src="https://openweathermap.org/img/wn/${data.icon}@4x.png" 
                             alt="${data.description}" class="weather-icon">
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-3 col-6">
                        <div class="weather-detail-item">
                            <i class="fas fa-thermometer-half"></i>
                            <div>Feels Like</div>
                            <strong>${data.feels_like}°C</strong>
                        </div>
                    </div>
                    <div class="col-md-3 col-6">
                        <div class="weather-detail-item">
                            <i class="fas fa-tint"></i>
                            <div>Humidity</div>
                            <strong>${data.humidity}%</strong>
                        </div>
                    </div>
                    <div class="col-md-3 col-6">
                        <div class="weather-detail-item">
                            <i class="fas fa-wind"></i>
                            <div>Wind</div>
                            <strong>${data.wind_speed} m/s</strong>
                        </div>
                    </div>
                    <div class="col-md-3 col-6">
                        <div class="weather-detail-item">
                            <i class="fas fa-compress"></i>
                            <div>Pressure</div>
                            <strong>${data.pressure} hPa</strong>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-3">
                    <div class="col-md-6">
                        <div class="weather-detail-item">
                            <i class="fas fa-sun"></i>
                            <div>Sunrise</div>
                            <strong>${data.sunrise}</strong>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="weather-detail-item">
                            <i class="fas fa-moon"></i>
                            <div>Sunset</div>
                            <strong>${data.sunset}</strong>
                        </div>
                    </div>
                </div>
                
                ${this.renderForecast(data.forecast)}
            </div>
        `;

        $('#weatherResult').html(weatherHtml).removeClass('d-none');
        
        // Add animation
        $('#weatherAnimation').attr('class', `weather-animation-container ${data.animation}`);
    }

    renderForecast(forecast) {
        if (!forecast || forecast.length === 0) return '';

        let forecastHtml = '<div class="row mt-4"><h5 class="mb-3">Hourly Forecast</h5>';
        
        forecast.forEach(item => {
            forecastHtml += `
                <div class="col-md-3 col-6 mb-2">
                    <div class="weather-detail-item">
                        <div>${item.time}</div>
                        <img src="https://openweathermap.org/img/wn/${item.icon}.png" alt="${item.description}">
                        <div><strong>${item.temp}°C</strong></div>
                    </div>
                </div>
            `;
        });

        forecastHtml += '</div>';
        return forecastHtml;
    }

    loadSearchHistory() {
        $.ajax({
            url: this.historyUrl,
            method: 'GET',
            success: (response) => {
                this.displaySearchHistory(response.searches);
            }
        });
    }

    displaySearchHistory(searches) {
        let historyHtml = '';
        
        if (searches.length === 0) {
            historyHtml = '<p class="text-muted">No search history yet</p>';
        } else {
            searches.forEach(search => {
                historyHtml += `
                    <a href="#" class="list-group-item list-group-item-action history-item" 
                       onclick="$('#cityInput').val('${search.city}'); weatherManager.searchWeather(); return false;">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${search.city}, ${search.country}</strong>
                                <div class="text-muted">${search.temperature}°C</div>
                            </div>
                            <small class="text-muted">${search.searched_at}</small>
                        </div>
                    </a>
                `;
            });
        }

        $('#searchHistory').html(historyHtml);
    }

    showLoading(show) {
        if (show) {
            $('#loadingSpinner').removeClass('d-none');
            $('#weatherResult').addClass('d-none');
        } else {
            $('#loadingSpinner').addClass('d-none');
        }
    }

    showNotification(message, type) {
        const types = {
            'success': 'success',
            'danger': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        
        const toastClass = types[type] || 'info';
        
        const toast = $(`
            <div class="toast toast-${toastClass}" role="alert">
                <div class="toast-header">
                    <strong class="me-auto">
                        <i class="fas fa-${type === 'success' ? 'check-circle' : 
                                          type === 'danger' ? 'exclamation-circle' :
                                          type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
                        Notification
                    </strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `);

        $('.toast-container').append(toast);
        
        // Initialize and show toast
        const bsToast = new bootstrap.Toast(toast[0], { delay: 3000 });
        bsToast.show();

        // Remove from DOM after hiding
        toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    }
}

// Initialize weather manager when document is ready
$(document).ready(function() {
    window.weatherManager = new WeatherManager();
});