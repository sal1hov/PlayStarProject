# staff/migrations/0020_shift_role_and_more.py
from django.db import migrations, models

def set_default_role(apps, schema_editor):
    Shift = apps.get_model('staff', 'Shift')
    for shift in Shift.objects.all():
        shift.role = 'animator'  # Установка значения по умолчанию
        shift.save()

class Migration(migrations.Migration):

    dependencies = [
        # Зависит от последней реальной миграции в вашем проекте
        ('staff', '0014_shiftrequest_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='role',
            field=models.CharField(
                choices=[
                    ('animator', 'Детский городок'),
                    ('additional', 'Доп. сотрудник'),
                    ('vr_operator', 'VR сотрудник'),
                    ('cashier', 'Кассир (Администратор)')
                ],
                default='animator',
                max_length=20,
                verbose_name='Роль сотрудника'
            ),
        ),
        migrations.RunPython(set_default_role),
        migrations.AlterField(
            model_name='shift',
            name='shift_type',
            field=models.CharField(
                choices=[
                    ('full', 'Полный день (9:30-22:00)'),
                    ('morning', 'Утро (9:30-16:00)'),
                    ('evening', 'Вечер (16:00-22:00)'),
                    ('additional_evening', 'Вечер доп. сотрудника (15:00-22:00)'),
                    ('vr_evening', 'Вечер VR сотрудника (15:00-22:00)')
                ],
                max_length=20,
                verbose_name='Тип смены'
            ),
        ),
    ]