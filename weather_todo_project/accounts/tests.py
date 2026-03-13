from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountsSmokeTests(TestCase):
	def test_login_page_loads(self):
		response = self.client.get(reverse('accounts:login'))
		self.assertEqual(response.status_code, 200)

	def test_signup_creates_user_and_logs_user_in(self):
		response = self.client.post(
			reverse('accounts:signup'),
			{
				'username': 'newuser',
				'first_name': 'New',
				'last_name': 'User',
				'email': 'newuser@example.com',
				'password1': 'StrongPass123!',
				'password2': 'StrongPass123!',
			},
		)

		self.assertEqual(response.status_code, 302)
		self.assertTrue(User.objects.filter(username='newuser').exists())
		self.assertIn('_auth_user_id', self.client.session)

	def test_profile_requires_authentication(self):
		response = self.client.get(reverse('accounts:profile'))
		self.assertEqual(response.status_code, 302)

	def test_profile_loads_for_authenticated_user(self):
		user = User.objects.create_user(username='jane', password='StrongPass123!')
		self.client.login(username='jane', password='StrongPass123!')

		response = self.client.get(reverse('accounts:profile'))
		self.assertEqual(response.status_code, 200)
