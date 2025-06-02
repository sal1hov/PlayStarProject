from django.test import TestCase, Client
from django.urls import reverse
from main.models import CustomUser
from staff.models import Shift, ShiftRequest
from datetime import date, time

class StaffTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.employee = CustomUser.objects.create_user(username='emp', password='emp123', role='Employee')
        self.admin = CustomUser.objects.create_user(username='admin', password='admin123', role='Admin')
        self.shift = Shift.objects.create(
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(18, 0),
            max_staff=3
        )
        self.client.login(username='emp', password='emp123')

    def test_create_shift_request(self):
        response = self.client.post(reverse('staff:create_shift_request'), {
            'shift': self.shift.id,
            'date': self.shift.date,
            'start_time': self.shift.start_time,
            'end_time': self.shift.end_time,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ShiftRequest.objects.filter(user=self.employee).count(), 1)

    def test_admin_can_see_shift_list(self):
        self.client.logout()
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('staff:shift_list'))
        self.assertEqual(response.status_code, 200)
