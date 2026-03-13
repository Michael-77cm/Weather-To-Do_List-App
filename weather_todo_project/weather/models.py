from django.db import models
from django.contrib.auth.models import User

class WeatherSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weather_searches')
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    temperature = models.FloatField()
    description = models.CharField(max_length=200)
    humidity = models.IntegerField()
    wind_speed = models.FloatField()
    icon = models.CharField(max_length=10)
    searched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-searched_at']
    
    def __str__(self):
        return f"{self.city} - {self.searched_at}"