from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from main.models import CustomUser
from bookings.models import Booking

class BookingsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(username='user', password='pass123')
        self.client.login(username='user', password='pass123')

    def test_booking_creation(self):
        response = self.client.post(reverse('bookings:create_booking'), {
            'booking_type': 'birthday',
            'event_date': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'children_count': 2,
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.status, 'pending')
