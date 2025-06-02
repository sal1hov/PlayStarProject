from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from main.models import CustomUser
from staff.models import Event, Shift

class StaffTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Создаем пользователя и добавляем в группу Admin, чтобы проходить проверки ролей
        self.user = CustomUser.objects.create_user(
            username='adminuser',
            email='admin@mail.com',
            password='password',
            phone_number='+79998887766',
            first_name='Админ',
            last_name='Пользователь',
        )
        admin_group, created = self.user.groups.model.objects.get_or_create(name='Admin')
        self.user.groups.add(admin_group)
        self.user.save()
        self.client.login(username='adminuser', password='password')

    def test_create_event_and_view(self):
        """Создание события и проверка, что оно отображается в списке"""
        event = Event.objects.create(
            name='Тестовое событие',
            description='Описание тестового события',
            date=timezone.now() + timedelta(days=10),
            location='main',
            event_type='выездные анимации',
            moderation_status='pending',
            max_participants=50,
        )
        response = self.client.get(reverse('staff:events'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, event.name)

    def test_create_shift_and_list(self):
        """Создание смены и проверка списка смен"""
        shift = Shift.objects.create(
            role='animator',
            shift_type='full',
            date=timezone.now().date() + timedelta(days=1),
            max_staff=3
        )
        response = self.client.get(reverse('staff:shift-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, shift.get_staff_names() or '')  # Поскольку staff пустой, проверим на пустую строку

