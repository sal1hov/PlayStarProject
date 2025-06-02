from django.test import TestCase, Client
from django.urls import reverse
from main.models import CustomUser, Profile, Child
import json

class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='tester',
            email='tester@mail.com',
            password='password',
            first_name='Имя',
            last_name='Фамилия',
            phone_number='+70000000000',
        )
        Profile.objects.get_or_create(user=self.user)
        self.client.login(username='tester', password='password')

    def test_profile_update(self):
        response = self.client.post(reverse('accounts:profile_edit'), {
            'first_name': 'Тест',
            'last_name': 'Тестович',
            'email': 'tester@mail.com',
            'username': 'tester',
            'phone_number': '+79991112233',
        })
        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '+79991112233')

    def test_add_child(self):
        response = self.client.post(reverse('accounts:add_child'), {
            'name': 'Аня',
            'birthdate': '2018-06-01',
            'age': 6,
            'gender': 'F',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        if response.status_code != 200:
            print("Add child errors:", response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Child.objects.filter(profile=self.user.profile).count(), 1)
        json_response = json.loads(response.content)
        self.assertTrue(json_response.get('success'))
