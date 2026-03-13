from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .utils import get_weather_data, get_weather_forecast, get_weather_animation, get_all_cities
from .models import WeatherSearch
from datetime import datetime

@login_required
def weather_dashboard(request):
    """Main weather dashboard view"""
    context = {
        'cities': get_all_cities(),
    }
    
    # Get weather for default city or user's last searched
    last_search = WeatherSearch.objects.filter(user=request.user).first()
    if last_search:
        context['last_city'] = last_search.city
    
    return render(request, 'weather_dashboard.html', context)

@login_required
@require_GET
def get_weather(request):
    """AJAX endpoint to get weather data"""
    city = request.GET.get('city', '')
    
    if not city:
        return JsonResponse({'error': 'City is required'}, status=400)
    
    weather_data = get_weather_data(city)
    
    if weather_data and weather_data.get('cod') == 200:
        # Save search to history
        WeatherSearch.objects.create(
            user=request.user,
            city=weather_data['name'],
            country=weather_data['sys']['country'],
            temperature=weather_data['main']['temp'],
            description=weather_data['weather'][0]['description'],
            humidity=weather_data['main']['humidity'],
            wind_speed=weather_data['wind']['speed'],
            icon=weather_data['weather'][0]['icon']
        )
        
        # Get animation class
        animation = get_weather_animation(weather_data['weather'][0]['main'])
        
        response_data = {
            'success': True,
            'city': weather_data['name'],
            'country': weather_data['sys']['country'],
            'temperature': round(weather_data['main']['temp']),
            'feels_like': round(weather_data['main']['feels_like']),
            'description': weather_data['weather'][0]['description'].title(),
            'humidity': weather_data['main']['humidity'],
            'wind_speed': weather_data['wind']['speed'],
            'pressure': weather_data['main']['pressure'],
            'icon': weather_data['weather'][0]['icon'],
            'animation': animation,
            'sunrise': datetime.fromtimestamp(weather_data['sys']['sunrise']).strftime('%H:%M'),
            'sunset': datetime.fromtimestamp(weather_data['sys']['sunset']).strftime('%H:%M'),
        }
        
        # Get forecast data
        forecast_data = get_weather_forecast(city)
        if forecast_data:
            response_data['forecast'] = process_forecast(forecast_data)
        
        return JsonResponse(response_data)
    else:
        return JsonResponse({'error': 'City not found'}, status=404)

def process_forecast(forecast_data):
    """Process forecast data for display"""
    forecast_list = []
    for item in forecast_data['list'][:8]:  # Next 24 hours
        forecast_list.append({
            'time': datetime.fromtimestamp(item['dt']).strftime('%H:%M'),
            'temp': round(item['main']['temp']),
            'icon': item['weather'][0]['icon'],
            'description': item['weather'][0]['description']
        })
    return forecast_list

@login_required
def search_history(request):
    """View weather search history"""
    searches = WeatherSearch.objects.filter(user=request.user)[:20]
    return JsonResponse({
        'searches': [
            {
                'city': s.city,
                'country': s.country,
                'temperature': s.temperature,
                'searched_at': s.searched_at.strftime('%Y-%m-%d %H:%M')
            }
            for s in searches
        ]
    })