const searchInput = document.querySelector('[data-city-search]');
const resultsContainer = document.querySelector('[data-city-results]');
const weatherPanel = document.querySelector('[data-weather-panel]');
const weatherScene = document.querySelector('[data-weather-scene]');
const weatherLocation = document.querySelector('[data-weather-location]');
const weatherDescription = document.querySelector('[data-weather-description]');
const weatherTemp = document.querySelector('[data-weather-temp]');
const weatherFeels = document.querySelector('[data-weather-feels]');
const weatherHumidity = document.querySelector('[data-weather-humidity]');
const weatherWind = document.querySelector('[data-weather-wind]');
const forecastStrip = document.querySelector('[data-weather-forecast]');

let searchDebounce;

function clearSuggestions() {
    if (resultsContainer) {
        resultsContainer.innerHTML = '';
    }
}

function createParticles(className, count) {
    const fragment = document.createDocumentFragment();
    for (let index = 0; index < count; index += 1) {
        const particle = document.createElement('span');
        particle.className = className;
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.animationDelay = `${Math.random() * 2}s`;
        particle.style.animationDuration = `${1.2 + Math.random() * 1.8}s`;
        fragment.appendChild(particle);
    }
    return fragment;
}

function createCloud(sizeClass) {
    const cloud = document.createElement('div');
    cloud.className = `cloud ${sizeClass}`;
    return cloud;
}

function renderScene(condition, isDay) {
    if (!weatherScene || !weatherPanel) {
        return;
    }

    weatherScene.innerHTML = '';
    weatherPanel.dataset.condition = condition;
    weatherScene.dataset.mode = isDay ? 'day' : 'night';

    switch (condition) {
        case 'clear': {
            const sun = document.createElement('div');
            sun.className = isDay ? 'sun' : 'moon';
            weatherScene.appendChild(sun);
            weatherScene.appendChild(createParticles('sparkle', 18));
            break;
        }
        case 'cloudy': {
            weatherScene.appendChild(createCloud('large'));
            weatherScene.appendChild(createCloud('medium'));
            weatherScene.appendChild(createParticles('sparkle faint', 12));
            break;
        }
        case 'rain': {
            weatherScene.appendChild(createCloud('large'));
            weatherScene.appendChild(createCloud('small'));
            weatherScene.appendChild(createParticles('raindrop', 34));
            break;
        }
        case 'snow': {
            weatherScene.appendChild(createCloud('large'));
            weatherScene.appendChild(createParticles('snowflake', 28));
            break;
        }
        case 'storm': {
            weatherScene.appendChild(createCloud('large'));
            weatherScene.appendChild(createCloud('medium'));
            const flash = document.createElement('div');
            flash.className = 'lightning';
            weatherScene.appendChild(flash);
            weatherScene.appendChild(createParticles('raindrop heavy', 28));
            break;
        }
        default: {
            weatherScene.appendChild(createCloud('large'));
            weatherScene.appendChild(createParticles('fog', 10));
            break;
        }
    }
}

function renderForecast(items) {
    if (!forecastStrip) {
        return;
    }
    forecastStrip.innerHTML = '';

    items.forEach((item) => {
        const card = document.createElement('article');
        card.className = `forecast-card ${item.condition}`;
        card.innerHTML = `
            <p>${new Date(item.date).toLocaleDateString(undefined, { weekday: 'short' })}</p>
            <strong>${item.description}</strong>
            <span>${Math.round(item.high)}° / ${Math.round(item.low)}°</span>
        `;
        forecastStrip.appendChild(card);
    });
}

function renderWeather(data) {
    if (!weatherLocation) {
        return;
    }

    const locationBits = [data.city, data.country].filter(Boolean).join(', ');
    weatherLocation.textContent = locationBits || 'Selected city';
    weatherDescription.textContent = data.description;
    weatherTemp.textContent = data.temperature == null ? '--' : Math.round(data.temperature);
    weatherFeels.textContent = data.feels_like == null ? '--' : `${Math.round(data.feels_like)}°C`;
    weatherHumidity.textContent = data.humidity == null ? '--' : `${Math.round(data.humidity)}%`;
    weatherWind.textContent = data.wind_speed == null ? '--' : `${Math.round(data.wind_speed)} km/h`;
    renderForecast(data.forecast || []);
    renderScene(data.condition, data.is_day);
}

async function fetchWeather(city) {
    const params = new URLSearchParams({
        lat: city.latitude,
        lon: city.longitude,
        name: city.name,
        country: city.country || '',
    });
    const response = await fetch(`/api/weather/?${params.toString()}`);
    if (!response.ok) {
        throw new Error('Weather lookup failed');
    }
    const payload = await response.json();
    renderWeather(payload);
}

function chooseCity(city) {
    if (searchInput) {
        searchInput.value = city.label;
    }
    clearSuggestions();
    fetchWeather(city).catch(() => {
        weatherDescription.textContent = 'Weather data is unavailable right now.';
    });
}

function renderSuggestions(items) {
    clearSuggestions();
    if (!resultsContainer || items.length === 0) {
        return;
    }

    items.forEach((item) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'suggestion-item';
        button.textContent = item.label;
        button.addEventListener('click', () => chooseCity(item));
        resultsContainer.appendChild(button);
    });
}

async function fetchCities(query) {
    const response = await fetch(`/api/cities/?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
        throw new Error('City search failed');
    }
    const payload = await response.json();
    renderSuggestions(payload.results || []);
}

if (searchInput) {
    searchInput.addEventListener('input', (event) => {
        const query = event.target.value.trim();
        clearTimeout(searchDebounce);
        if (query.length < 2) {
            clearSuggestions();
            return;
        }

        searchDebounce = setTimeout(() => {
            fetchCities(query).catch(clearSuggestions);
        }, 220);
    });

    document.addEventListener('click', (event) => {
        if (!resultsContainer?.contains(event.target) && event.target !== searchInput) {
            clearSuggestions();
        }
    });

    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
            ({ coords }) => {
                fetchWeather({
                    latitude: coords.latitude,
                    longitude: coords.longitude,
                    name: 'Your location',
                    country: '',
                }).catch(() => null);
            },
            () => null,
            { timeout: 10000 }
        );
    }
}