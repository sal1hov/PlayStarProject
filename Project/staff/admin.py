from django.contrib import admin
from django.utils.html import format_html
from .models import Event, StaffProfile, SiteSettings, Shift, ShiftRequest


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'date', 'location', 'moderation_status', 'image_preview')
    list_filter = ('event_type', 'moderation_status')
    search_fields = ('name', 'description')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 100px;" />'
        return "Нет изображения"

    image_preview.allow_tags = True
    image_preview.short_description = "Превью"


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'user_role')
    list_filter = ('user__role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'position')
    raw_id_fields = ('user',)

    def user_role(self, obj):
        return obj.user.get_role_display()

    user_role.short_description = 'Роль'


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_title', 'meta_description_short')
    fieldsets = (
        ('Основные настройки', {
            'fields': ('site_title', 'meta_description', 'meta_keywords')
        }),
        ('Аналитика', {
            'fields': ('google_analytics',),
            'classes': ('collapse',)
        })
    )

    def meta_description_short(self, obj):
        return obj.meta_description[:50] + '...' if obj.meta_description else ''

    meta_description_short.short_description = 'Мета описание'

    def has_add_permission(self, request):
        return False if self.model.objects.count() > 0 else super().has_add_permission(request)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('date', 'shift_type_display', 'max_staff', 'approved_requests_count', 'pending_requests_count')
    list_filter = ('date', 'shift_type')
    search_fields = ('date',)
    ordering = ('-date',)

    def shift_type_display(self, obj):
        return obj.get_shift_type_display()

    shift_type_display.short_description = 'Тип смены'

    def approved_requests_count(self, obj):
        count = obj.shiftrequest_set.filter(status='approved').count()
        return format_html(
            '<span class="text-green-600">{}</span>',
            count
        )

    approved_requests_count.short_description = 'Утверждено'

    def pending_requests_count(self, obj):
        count = obj.shiftrequest_set.filter(status='pending').count()
        return format_html(
            '<span class="text-orange-500">{}</span>',
            count
        )

    pending_requests_count.short_description = 'На рассмотрении'


@admin.register(ShiftRequest)
class ShiftRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'shift_info', 'status', 'created_at', 'admin_actions')
    list_filter = ('status', 'shift__date', 'shift__shift_type')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name', 'shift__date')
    list_editable = ('status',)
    actions = ['approve_requests', 'reject_requests']
    raw_id_fields = ('employee', 'shift')

    def shift_info(self, obj):
        return f"{obj.shift.date} ({obj.shift.get_shift_type_display()})"

    shift_info.short_description = 'Смена'

    def admin_actions(self, obj):
        return format_html(
            '<div class="flex gap-2">'
            '<a class="px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm no-underline" href="approve/{}/">Утвердить</a>'
            '<a class="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm no-underline" href="reject/{}/">Отклонить</a>'
            '</div>',
            obj.id, obj.id
        )

    admin_actions.short_description = 'Действия'

    def approve_requests(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f"Утверждено {updated} заявок")

    approve_requests.short_description = "Утвердить выбранные заявки"

    def reject_requests(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f"Отклонено {updated} заявок")

    reject_requests.short_description = "Отклонить выбранные заявки"