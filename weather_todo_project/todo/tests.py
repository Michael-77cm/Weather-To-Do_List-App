from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Task, TaskCategory


class TodoSmokeTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='owner', password='StrongPass123!')
		self.category = TaskCategory.objects.create(name='work')

	def test_task_list_requires_authentication(self):
		response = self.client.get(reverse('todo:task_list'))
		self.assertEqual(response.status_code, 302)

	def test_task_crud_and_completion_flow(self):
		self.client.login(username='owner', password='StrongPass123!')

		create_response = self.client.post(
			reverse('todo:task_create'),
			{
				'title': 'Smoke Task',
				'description': 'Task created by test',
				'category': self.category.id,
				'priority': 'medium',
				'due_date': '2026-03-20',
				'due_time': '09:30',
				'assigned_to': [],
			},
		)
		self.assertEqual(create_response.status_code, 302)

		task = Task.objects.get(title='Smoke Task')

		update_response = self.client.post(
			reverse('todo:task_update', args=[task.pk]),
			{
				'title': 'Smoke Task Updated',
				'description': 'Updated description',
				'category': self.category.id,
				'priority': 'high',
				'due_date': '2026-03-21',
				'due_time': '10:30',
				'assigned_to': [],
			},
		)
		self.assertEqual(update_response.status_code, 302)

		toggle_response = self.client.post(reverse('todo:task_mark_completed', args=[task.pk]))
		self.assertEqual(toggle_response.status_code, 200)

		task.refresh_from_db()
		self.assertEqual(task.status, 'completed')

		delete_response = self.client.post(reverse('todo:task_delete', args=[task.pk]))
		self.assertEqual(delete_response.status_code, 302)
		self.assertFalse(Task.objects.filter(pk=task.pk).exists())
