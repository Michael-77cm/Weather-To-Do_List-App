from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import WeatherSearch


class WeatherSmokeTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='weatheruser', password='StrongPass123!')

	def test_dashboard_requires_authentication(self):
		response = self.client.get(reverse('weather:dashboard'))
		self.assertEqual(response.status_code, 302)

	def test_dashboard_loads_for_authenticated_user(self):
		self.client.login(username='weatheruser', password='StrongPass123!')
		response = self.client.get(reverse('weather:dashboard'))
		self.assertEqual(response.status_code, 200)

	def test_search_history_returns_recent_searches(self):
		self.client.login(username='weatheruser', password='StrongPass123!')
		WeatherSearch.objects.create(
			user=self.user,
			city='London',
			country='GB',
			temperature=12.3,
			description='Cloudy',
			humidity=80,
			wind_speed=4.2,
			icon='03d',
		)

		response = self.client.get(reverse('weather:search_history'))
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertIn('searches', payload)
		self.assertEqual(payload['searches'][0]['city'], 'London')
