from django.contrib import admin
from .models import Event, StaffProfile, SiteSettings

admin.site.register(Event)
admin.site.register(StaffProfile)
admin.site.register(SiteSettings)
