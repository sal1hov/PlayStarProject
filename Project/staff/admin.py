from django.contrib import admin
from .models import Event, StaffProfile, SiteSettings, Shift, ShiftRequest

admin.site.register(Event)
admin.site.register(StaffProfile)
admin.site.register(SiteSettings)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('date', 'shift_type', 'max_staff', 'get_approved_requests')
    list_filter = ('date', 'shift_type')
    search_fields = ('date',)
    ordering = ('-date',)

    def get_approved_requests(self, obj):
        return obj.shiftrequest_set.filter(status='approved').count()

    get_approved_requests.short_description = 'Утвержденные заявки'


@admin.register(ShiftRequest)
class ShiftRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'shift', 'status', 'created_at')
    list_filter = ('status', 'shift__date', 'shift__shift_type')
    search_fields = ('employee__username', 'shift__date')
    list_editable = ('status',)
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        queryset.update(status='approved')

    approve_requests.short_description = "Утвердить выбранные заявки"

    def reject_requests(self, request, queryset):
        queryset.update(status='rejected')

    reject_requests.short_description = "Отклонить выбранные заявки"