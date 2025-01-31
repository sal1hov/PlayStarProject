# accounts/migrations/0002_create_groups.py
from django.db import migrations
from django.contrib.auth.models import Group

def create_groups(apps, schema_editor):
    Group.objects.get_or_create(name='Admin')
    Group.objects.get_or_create(name='Manager')
    Group.objects.get_or_create(name='Staff')

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),  # Зависит от предыдущей миграции вашего приложения accounts
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]