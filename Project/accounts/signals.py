from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from main.models import Profile

User = get_user_model()

# Соответствие ролей вашим существующим группам (с учетом регистра)
ROLE_GROUPS_MAPPING = {
    'CLIENT': None,  # Клиенты не входят в специальные группы
    'STAFF': 'Staff',  # Ваша существующая группа
    'MANAGER': 'Manager',  # Ваша существующая группа
    'ADMIN': 'Admin'  # Ваша существующая группа
}


@receiver(pre_save, sender=User)
def track_role_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            original_user = User.objects.get(pk=instance.pk)
            instance._original_role = original_user.role
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def handle_user_roles_and_groups(sender, instance, created, **kwargs):
    role_changed = hasattr(instance, '_original_role') and instance._original_role != instance.role

    if created or role_changed:
        for group in instance.groups.filter(name__in=['Admin', 'Manager', 'Staff']):
            instance.groups.remove(group)

        group_name = ROLE_GROUPS_MAPPING.get(instance.role)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                instance.groups.add(group)
            except Group.DoesNotExist:
                print(f'Группа {group_name} не найдена!')

    if created:
        Profile.objects.get_or_create(user=instance)
    elif hasattr(instance, 'profile'):
        instance.profile.save()

    if instance.role in ['STAFF', 'MANAGER', 'ADMIN']:
        from staff.models import StaffProfile
        StaffProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):  # Проверяем, существует ли профиль
        instance.profile.save()