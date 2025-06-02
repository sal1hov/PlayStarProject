from django.test import TestCase, Client
from django.urls import reverse
from main.models import CustomUser
from bookings.models import Booking
import json
from datetime import datetime, timedelta
from django.utils import timezone

class BookingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='user1',
            email='user1@mail.com',
            password='password',
            first_name='Имя',
            last_name='Фамилия',
            phone_number='+79999999999',
        )
        self.client.login(username='user1', password='password')

    def test_create_booking(self):
        future_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(reverse('bookings:create_booking'), data={
            'event_name': 'Test Event',
            'booking_type': 'birthday',
            'event_date': future_date,
            'children_count': 3,
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get('success'))
        self.assertIn('redirect_url', data)



    def test_edit_booking(self):
        booking = Booking.objects.create(
            user=self.user,
            event_name='Old Event',
            booking_type='birthday',
            event_date=timezone.now() + timedelta(days=5),
            children_count=2
        )
        new_date = (timezone.now() + timedelta(days=15)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(reverse('bookings:edit_booking', args=[booking.id]), data={
            'event_name': 'Updated Event',
            'booking_type': 'birthday',
            'event_date': new_date,
            'children_count': 2,
        })

        self.assertEqual(response.status_code, 302)  # Редирект при успешном обновлении

        booking.refresh_from_db()
        self.assertEqual(booking.event_name, 'Updated Event')

    def test_manage_booking_approve(self):
        booking = Booking.objects.create(
            user=self.user,
            event_name='Some Event',
            booking_type='birthday',
            event_date=datetime.now() + timedelta(days=5),
            children_count=1,
            status='pending'
        )
        admin_group, created = self.user.groups.model.objects.get_or_create(name='Admin')
        self.user.groups.add(admin_group)
        self.user.save()

        response = self.client.get(reverse('bookings:manage_booking', args=[booking.id, 'approve']))

        self.assertEqual(response.status_code, 302)

        booking.refresh_from_db()
        self.assertEqual(booking.status, 'approved')

    def test_delete_booking(self):
        booking = Booking.objects.create(
            user=self.user,
            event_name='To Delete',
            booking_type='birthday',
            event_date=datetime.now() + timedelta(days=5),
            children_count=1,
            status='pending'
        )

        response = self.client.post(reverse('bookings:delete_booking', args=[booking.id]),
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get('success'))
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())
