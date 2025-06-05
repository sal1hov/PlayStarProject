# staff/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.utils import timezone

# Если у вас CustomUser лежит в main.models
from main.models import CustomUser


# ------------------------------------------------------------
# Существующие модели для StaffProfile, SiteSettings, Event, Shift, ShiftRequest
# ------------------------------------------------------------

class StaffProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    position = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.user.username} - {self.position}'


class SiteSettings(models.Model):
    site_title = models.CharField(max_length=255, verbose_name="Заголовок сайта")
    meta_description = models.TextField(blank=True, null=True, verbose_name="Мета описание")
    meta_keywords = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ключевые слова")
    google_analytics = models.TextField(blank=True, null=True, verbose_name="Код Google Analytics")

    def __str__(self):
        return "Настройки сайта"

    class Meta:
        verbose_name = "Настройка сайта"
        verbose_name_plural = "Настройки сайта"


# Константы для выбора типа и статуса модерации
EVENT_TYPES = (
    ('выездные анимации', 'Выездные анимации'),
    ('открытые анимации', 'Открытые анимации'),
    ('панорамик', 'Панорамик'),
    ('другое', 'Другое'),
)

MODERATION_STATUS = (
    ('approved', 'Принято'),
    ('rejected', 'Отказано'),
    ('unavailable', 'Недоступно'),
    ('pending', 'На модерации'),
)


class Event(models.Model):
    LOCATION_CHOICES = [
        ('main', 'Основная площадка'),
        ('secondary', 'Дополнительная площадка')
    ]

    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    date = models.DateTimeField(verbose_name="Дата и время")
    location = models.CharField(
        max_length=100,
        choices=LOCATION_CHOICES,
        default='main',
        verbose_name="Место проведения"
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        verbose_name="Тип мероприятия"
    )
    moderation_status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS,
        default='pending',
        verbose_name="Статус модерации"
    )
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Бронирование"
    )
    image = models.ImageField(
        upload_to='events/',
        null=True,
        blank=True,
        verbose_name="Изображение"
    )
    max_participants = models.PositiveIntegerField(
        default=10,
        verbose_name='Максимальное количество участников'
    )

    def __str__(self):
        return self.name

    def get_event_type_display(self):
        return dict(EVENT_TYPES).get(self.event_type, self.event_type)

    def get_moderation_status_display(self):
        return dict(MODERATION_STATUS).get(self.moderation_status, self.moderation_status)

    def get_location_display(self):
        return dict(self.LOCATION_CHOICES).get(self.location, self.location)

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
        ordering = ['date']


class Shift(models.Model):
    ROLE_CHOICES = [
        ('animator', 'Детский городок'),
        ('additional', 'Доп. сотрудник'),
        ('vr_operator', 'VR сотрудник'),
        ('cashier', 'Кассир (Администратор)'),
    ]

    SHIFT_TYPES = [
        ('full', 'Полный день (9:30-22:00)'),
        ('morning', 'Утро (9:30-16:00)'),
        ('evening', 'Вечер (16:00-22:00)'),
        ('additional_evening', 'Вечер доп. сотрудника (15:00-22:00)'),
        ('vr_evening', 'Вечер VR сотрудника (15:00-22:00)'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='animator',
        verbose_name="Роль сотрудника"
    )
    shift_type = models.CharField(
        max_length=20,
        choices=SHIFT_TYPES,
        verbose_name="Тип смены"
    )
    date = models.DateField(verbose_name="Дата смены")
    max_staff = models.PositiveIntegerField(default=1, verbose_name="Макс. сотрудников")
    staff = models.ManyToManyField(
        CustomUser,
        related_name='shifts',
        blank=True,
        verbose_name="Сотрудники"
    )

    def __str__(self):
        role_display = dict(self.ROLE_CHOICES).get(self.role, self.role)
        shift_display = dict(self.SHIFT_TYPES).get(self.shift_type, self.shift_type)
        return f"{role_display} - {shift_display} - {self.date.strftime('%d.%m.%Y')}"

    def get_staff_names(self):
        return ", ".join([staff.get_full_name() for staff in self.staff.all()])

    def clean(self):
        # Кассир может работать только полный день
        if self.role == 'cashier' and self.shift_type != 'full':
            raise ValidationError("Кассиры могут работать только полный день")

        valid_combinations = {
            'animator': ['full', 'morning', 'evening'],
            'additional': ['full', 'additional_evening'],
            'vr_operator': ['full', 'vr_evening'],
            'cashier': ['full']
        }
        if self.shift_type not in valid_combinations.get(self.role, []):
            raise ValidationError(f"Недопустимый тип смены для роли {self.get_role_display()}")

    @property
    def start_time(self):
        times = {
            'full': '09:30',
            'morning': '09:30',
            'evening': '16:00',
            'additional_evening': '15:00',
            'vr_evening': '15:00',
        }
        return times.get(self.shift_type, '')

    @property
    def end_time(self):
        times = {
            'full': '22:00',
            'morning': '16:00',
            'evening': '22:00',
            'additional_evening': '22:00',
            'vr_evening': '22:00',
        }
        return times.get(self.shift_type, '')

    @property
    def duration(self):
        durations = {
            'full': 12.5,
            'morning': 6.5,
            'evening': 6,
            'additional_evening': 7,
            'vr_evening': 7,
        }
        return durations.get(self.shift_type, 0)


class ShiftRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'На рассмотрении'),
        ('approved', 'Утверждено'),
        ('rejected', 'Отклонено'),
    )

    ROLE_CHOICES = [
        ('animator', 'Детский городок'),
        ('additional', 'Доп. сотрудник'),
        ('vr_operator', 'VR сотрудник'),
        ('cashier', 'Кассир (Администратор)'),
    ]

    employee = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='shift_requests')
    date = models.DateField(verbose_name="Дата смены")
    start_time = models.TimeField(verbose_name="Начало смены")
    end_time = models.TimeField(verbose_name="Конец смены")
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name="Роль"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_comment = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий сотрудника')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.username} - {self.date} ({self.get_status_display()})"

    def get_shift_type_from_times(self):
        """Определяем тип смены на основе времени"""
        start_hour = self.start_time.hour
        end_hour = self.end_time.hour

        if start_hour == 9 and end_hour == 22:
            return 'full'
        elif start_hour == 9 and end_hour == 16:
            return 'morning'
        elif start_hour == 16 and end_hour == 22:
            return 'evening'
        elif start_hour == 15 and end_hour == 22:
            if self.role == 'additional':
                return 'additional_evening'
            elif self.role == 'vr_operator':
                return 'vr_evening'
        return 'full'

    def duration(self):
        """Рассчитать продолжительность смены в часах"""
        start = timezone.datetime.combine(self.date, self.start_time)
        end = timezone.datetime.combine(self.date, self.end_time)
        return (end - start).total_seconds() / 3600


@receiver(post_migrate)
def verify_groups_exist(sender, **kwargs):
    required_groups = ['Admin', 'Manager', 'Staff']
    for group_name in required_groups:
        if not Group.objects.filter(name=group_name).exists():
            print(f'Внимание: требуемая группа "{group_name}" не найдена! Создайте её в админке.')


# ------------------------------------------------------------
# Ниже – модели для раздела «Price Settings»
# ------------------------------------------------------------

# 1) Детский городок
class ChildCityItem(models.Model):
    name = models.CharField("Услуга", max_length=100)
    weekday_before_17 = models.PositiveIntegerField("Цена (будни до 17:00)", default=0)
    weekday_after_17_weekends = models.PositiveIntegerField("Цена (будни после 17:00 и выходные)", default=0)
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "Услуга Детского городка"
        verbose_name_plural = "Услуги Детского городка"

    def __str__(self):
        return self.name


# 2) Игровые автоматы (жетоны)
class ArcadeMachineItem(models.Model):
    name = models.CharField("Автомат/Зона", max_length=100)
    weekday_before_17 = models.PositiveIntegerField("Цена (будни до 17:00)", default=0)
    weekday_after_17_weekends = models.PositiveIntegerField("Цена (будни после 17:00 и выходные)", default=0)
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "Игровой автомат (жетон)"
        verbose_name_plural = "Игровые автоматы (жетоны)"

    def __str__(self):
        return self.name


# 3) VR-арена (сеансы)
class VRArenaItem(models.Model):
    DURATION_CHOICES = [
        (30, "30 минут"),
        (60, "60 минут"),
    ]
    duration = models.PositiveSmallIntegerField("Длительность (в мин.)", choices=DURATION_CHOICES)
    weekday_before_17 = models.PositiveIntegerField("Цена (будни до 17:00)", default=0)
    weekday_after_17_weekends = models.PositiveIntegerField("Цена (будни после 17:00 и выходные)", default=0)
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "Сеанс VR-арены"
        verbose_name_plural = "Сеансы VR-арены"

    def __str__(self):
        return f"{self.get_duration_display()}"


# 4) Пакеты ко Дню Рождения
class BirthdayPackage(models.Model):
    name = models.CharField("Название пакета", max_length=100)
    price_mon_thu = models.PositiveIntegerField("Цена (Пн–Чт)", default=0)
    price_fri_sun = models.PositiveIntegerField("Цена (Пт–Вс)", default=0)
    extra_person = models.PositiveIntegerField("Доп. игрок / ребёнок (₽)", default=0)
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "Пакет ко Дню Рождения"
        verbose_name_plural = "Пакеты ко Дню Рождения"

    def __str__(self):
        return self.name


# 5) Пакеты VR
class VRPackage(models.Model):
    name = models.CharField("Название пакета", max_length=100)
    price_mon_thu = models.PositiveIntegerField("Цена (Пн–Чт)", default=0)
    price_fri_sun = models.PositiveIntegerField("Цена (Пт–Вс)", default=0)
    extra_person = models.PositiveIntegerField("Доп. игрок / ребёнок (₽)", default=0)
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "Пакет VR"
        verbose_name_plural = "Пакеты VR"

    def __str__(self):
        return self.name


# 6) Обычные пакеты услуг
class StandardPackage(models.Model):
    name = models.CharField("Название пакета", max_length=100)
    price_mon_thu = models.PositiveIntegerField("Цена (Пн–Чт)", default=0)
    price_fri_sun = models.PositiveIntegerField("Цена (Пт–Вс)", default=0)
    extra_person = models.PositiveIntegerField("Доп. игрок / ребёнок (₽)", default=0)
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "Обычный пакет услуг"
        verbose_name_plural = "Обычные пакеты услуг"

    def __str__(self):
        return self.name


# 7) Зона PlayStation (слоты по времени)
class PlayStationSlot(models.Model):
    DURATION_CHOICES = [
        (30, "30 минут"),
        (60, "60 минут"),
    ]
    duration = models.PositiveSmallIntegerField("Длительность (в мин.)", choices=DURATION_CHOICES)
    weekday_before_17 = models.PositiveIntegerField("Цена (будни до 17:00)", default=0)
    weekday_after_17_weekends = models.PositiveIntegerField("Цена (будни после 17:00 и выходные)", default=0)
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "Слот PlayStation"
        verbose_name_plural = "Слоты PlayStation"

    def __str__(self):
        return f"{self.get_duration_display()}"


# 8) VR-аттракционы
class VRRide(models.Model):
    name = models.CharField("Название аттракциона", max_length=100)
    weekday_before_17 = models.PositiveIntegerField("Цена (будни до 17:00)", default=0)
    weekday_after_17_weekends = models.PositiveIntegerField("Цена (будни после 17:00 и выходные)", default=0)
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "VR-аттракцион"
        verbose_name_plural = "VR-аттракционы"

    def __str__(self):
        return self.name
