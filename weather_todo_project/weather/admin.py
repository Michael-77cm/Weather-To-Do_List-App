from django.contrib import admin
from .models import WeatherSearch

@admin.register(WeatherSearch)
class WeatherSearchAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'country', 'temperature', 'searched_at')
    list_filter = ('user', 'country', 'searched_at')
    search_fields = ('city', 'country', 'user__username')
    date_hierarchy = 'searched_at'