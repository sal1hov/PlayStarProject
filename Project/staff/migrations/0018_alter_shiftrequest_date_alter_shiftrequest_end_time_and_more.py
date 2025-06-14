# Generated by Django 5.1.5 on 2025-05-31 23:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0017_alter_shiftrequest_unique_together_shiftrequest_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shiftrequest',
            name='date',
            field=models.DateField(verbose_name='Дата смены'),
        ),
        migrations.AlterField(
            model_name='shiftrequest',
            name='end_time',
            field=models.TimeField(verbose_name='Конец смены'),
        ),
        migrations.AlterField(
            model_name='shiftrequest',
            name='role',
            field=models.CharField(choices=[('animator', 'Детский городок'), ('additional', 'Доп. сотрудник'), ('vr_operator', 'VR сотрудник'), ('cashier', 'Кассир (Администратор)')], max_length=20, verbose_name='Роль'),
        ),
        migrations.AlterField(
            model_name='shiftrequest',
            name='start_time',
            field=models.TimeField(verbose_name='Начало смены'),
        ),
    ]
