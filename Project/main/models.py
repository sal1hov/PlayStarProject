# main/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('CLIENT', 'Клиент'),
        ('STAFF', 'Сотрудник'),
        ('MANAGER', 'Менеджер'),
        ('ADMIN', 'Администратор'),
    ]

    # ПРОФЕССИОНАЛЬНЫЕ РОЛИ (должности)
    PROFESSIONAL_ROLES = [
        ('none', 'Не назначена'),
        ('animator', 'Детский городок'),
        ('additional', 'Доп. сотрудник'),
        ('vr_operator', 'VR сотрудник'),
        ('cashier', 'Кассир (Администратор)'),
    ]

    phone_number = models.CharField(max_length=15, unique=True, verbose_name="Номер телефона")
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='CLIENT',
        verbose_name='Роль'
    )
    professional_role = models.CharField(
        max_length=20,
        choices=PROFESSIONAL_ROLES,
        default='none',
        verbose_name='Профессиональная роль'
    )
    email = models.EmailField(unique=True, verbose_name="Email")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_staff_member(self):
        return self.role in ['STAFF', 'MANAGER', 'ADMIN']

    def is_manager_or_higher(self):
        return self.role in ['MANAGER', 'ADMIN']

    # ДОБАВЛЕНО: Метод для отображения профессиональной роли
    def get_professional_role_display(self):
        return dict(self.PROFESSIONAL_ROLES).get(
            self.professional_role,
            self.professional_role
        )

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username


    @property
    def telegram_account(self):
        """Получить привязанный Telegram аккаунт"""
        return self.socialaccount_set.filter(provider='telegram').first()

    @property
    def has_telegram(self):
        """Проверить наличие привязанного Telegram"""
        return self.socialaccount_set.filter(provider='telegram').exists()


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"Профиль {self.user.username}"


class Child(models.Model):
    GENDER_CHOICES = [
        ('M', 'Мальчик'),
        ('F', 'Девочка'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='children')
    name = models.CharField(max_length=100, verbose_name="Имя ребенка")
    age = models.PositiveIntegerField(verbose_name="Возраст ребенка")
    birthdate = models.DateField(verbose_name="Дата рождения", blank=True, null=True)
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        verbose_name="Пол",
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.name} ({self.age} лет)"

    class Meta:
        verbose_name = "Ребенок"
        verbose_name_plural = "Дети"