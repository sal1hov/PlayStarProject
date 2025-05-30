# Generated by Django 5.1.5 on 2025-03-20 23:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0005_alter_booking_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Сумма'),
        ),
        migrations.AddField(
            model_name='booking',
            name='booking_type',
            field=models.CharField(choices=[('online', 'Онлайн'), ('offline', 'Оффлайн')], default='online', max_length=10, verbose_name='Тип бронирования'),
        ),
    ]
