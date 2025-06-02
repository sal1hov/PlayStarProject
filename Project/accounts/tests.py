from django.test import TestCase, Client
from django.urls import reverse
from main.models import CustomUser, Profile, Child

class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(username='tester', email='tester@mail.com', password='password')
        Profile.objects.create(user=self.user, phone_number='88005553535')
        self.client.login(username='tester', password='password')

    def test_profile_update(self):
        response = self.client.post(reverse('accounts:update_profile'), {
            'phone_number': '89991112233',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.phone_number, '89991112233')

    def test_add_child(self):
        response = self.client.post(reverse('accounts:add_child'), {
            'name': 'Аня',
            'birthdate': '2018-06-01',
            'gender': 'female',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Child.objects.filter(user=self.user).count(), 1)
