# staff/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponse
import csv
from main.models import CustomUser  # Используем кастомную модель пользователя
from bookings.models import Booking  # Модель бронирований из приложения bookings
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from .models import Notification

def role_required(*group_names):
    """Декоратор для проверки групп."""
    def in_groups(user):
        if user.is_authenticated:
            if bool(user.groups.filter(name__in=group_names)) or user.is_superuser:
                return True
        return False
    return user_passes_test(in_groups)


@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def admin_dashboard(request):
    # Получаем всех пользователей без фильтров для статистики
    all_users = CustomUser.objects.all()

    # Применяем фильтры для отображения списка пользователей
    users = CustomUser.objects.all()
    search_query = request.GET.get('search', '').strip()  # Получаем параметр поиска
    role_filter = request.GET.get('role', '').strip().upper()  # Приводим к верхнему регистру

    if search_query:
        users = users.filter(username__icontains=search_query)  # Фильтруем по username

    if role_filter:
        users = users.filter(role=role_filter)  # Фильтруем по роли

    # Общее количество пользователей (без фильтров)
    total_users = all_users.count()

    # Бронирования
    bookings = Booking.objects.all()

    # Фильтрация бронирований
    booking_search = request.GET.get('booking_search')
    if booking_search:
        bookings = bookings.filter(event_name__icontains=booking_search)

    booking_status = request.GET.get('booking_status')
    if booking_status:
        bookings = bookings.filter(status=booking_status)

    # Общее количество бронирований
    total_bookings = bookings.count()
    pending_bookings = bookings.filter(status='pending').count()

    # Пагинация для отфильтрованного списка пользователей
    paginator = Paginator(users, 5)  # Пагинация
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'staff/admin_dashboard.html', {
        'users': page_obj,
        'bookings': bookings,
        'total_users': total_users,  # Общее количество пользователей без фильтров
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings
    })

@login_required
@role_required('Admin')
def edit_user(request, user_id):
    user_to_edit = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        user_to_edit.username = request.POST.get('username')
        user_to_edit.first_name = request.POST.get('first_name')
        user_to_edit.last_name = request.POST.get('last_name')
        user_to_edit.children = request.POST.get('children')
        user_to_edit.phone = request.POST.get('phone')
        password = request.POST.get('password')
        if password:
            user_to_edit.set_password(password)
            update_session_auth_hash(request, user_to_edit)
        user_to_edit.save()
        messages.success(request, 'Пользователь успешно обновлен.')
        return redirect('admin_dashboard')
    return render(request, 'staff/edit_user.html', {'user': user_to_edit})

@login_required
@role_required('Admin')
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(CustomUser, id=user_id)
    user_to_delete.delete()
    messages.success(request, 'Пользователь успешно удален.')
    return redirect('admin_dashboard')

@login_required
@role_required('Admin', 'Manager')
def manage_booking(request, booking_id, action):
    booking = get_object_or_404(Booking, id=booking_id)
    if action == 'approve':
        booking.status = 'approved'
    elif action == 'reject':
        booking.status = 'rejected'
    booking.save()
    messages.success(request, f'Бронирование успешно {"утверждено" if action == "approve" else "отклонено"}.')
    return redirect('admin_dashboard')

@login_required
@role_required('Admin', 'Manager')
def manager_dashboard(request):
    bookings = Booking.objects.all()
    return render(request, 'staff/manager_dashboard.html', {'bookings': bookings})

@login_required
@role_required('Staff')
def employee_dashboard(request):
    return render(request, 'staff/employee_dashboard.html')

@login_required
@role_required('Admin')
def export_users_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'First Name', 'Last Name', 'Email'])
    for user in CustomUser.objects.all():
        writer.writerow([user.id, user.username, user.first_name, user.last_name, user.email])
    return response

@login_required
@role_required('Admin')
def export_bookings_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bookings.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'User', 'Date', 'Status', ])
    for booking in Booking.objects.all():
        writer.writerow([booking.id, booking.user.username, booking.booking_date, booking.status])
    return response

def statistics_view(request):
    # Статистика пользователей по месяцам
    users_by_month = CustomUser.objects.annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(count=Count('id')).order_by('month')

    # Статистика бронирований по статусам
    bookings_by_status = Booking.objects.values('status').annotate(count=Count('id')).order_by('status')

    return render(request, 'staff/statistics.html', {
        'users_by_month': list(users_by_month),
        'bookings_by_status': list(bookings_by_status),
    })
def events_view(request):
    events = Event.objects.all()
    return render(request, 'staff/events.html', {'events': events})

def filter_users(request):
    users = CustomUser.objects.all()
    search_query = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '').strip().upper()

    if search_query:
        users = users.filter(username__icontains=search_query)
    if role_filter:
        users = users.filter(role=role_filter)

    html = render_to_string('staff/users_table.html', {'users': users})
    return JsonResponse({'html': html})

def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'staff/notifications.html', {'notifications': notifications})