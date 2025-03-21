from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponse, JsonResponse
import csv
from main.models import CustomUser
from bookings.models import Booking
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.template.loader import render_to_string
from .models import Event
import io
import pandas as pd  # для импорта из Excel
from .forms import EventForm
from datetime import datetime

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
    all_users = CustomUser.objects.all()
    users = CustomUser.objects.all()
    search_query = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '').strip().upper()

    if search_query:
        users = users.filter(username__icontains=search_query)

    if role_filter:
        users = users.filter(role=role_filter)

    total_users = all_users.count()

    bookings = Booking.objects.all()

    booking_search = request.GET.get('booking_search')
    if booking_search:
        bookings = bookings.filter(event_name__icontains=booking_search)

    booking_status = request.GET.get('booking_status')
    if booking_status:
        bookings = bookings.filter(status=booking_status)

    total_bookings = bookings.count()
    pending_bookings = bookings.filter(status='pending').count()

    paginator = Paginator(users, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'staff/admin_dashboard.html', {
        'users': page_obj,
        'bookings': bookings,
        'total_users': total_users,
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
def statistics_view(request):
    # Фильтр по диапазону дат
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        # Преобразуем даты из формата дд.мм.гг в datetime
        start_date = datetime.strptime(start_date, '%d.%m.%y')
        end_date = datetime.strptime(end_date, '%d.%m.%y')
        bookings = Booking.objects.filter(booking_date__range=(start_date, end_date))
    else:
        bookings = Booking.objects.all()

    # Статистика пользователей по месяцам
    users_by_month = CustomUser.objects.annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(count=Count('id')).order_by('month')
    users_by_month = list(users_by_month)
    for item in users_by_month:
        if item['month']:
            item['month'] = item['month'].strftime('%Y-%m')

    # Статистика бронирований по статусам
    bookings_by_status = bookings.values('status').annotate(count=Count('id')).order_by('status')

    # Новая статистика
    online_bookings_count = bookings.filter(booking_type='online').count()
    total_earnings = bookings.aggregate(total=Sum('amount'))['total'] or 0

    # График доходов по месяцам
    earnings_by_month = bookings.annotate(
        month=TruncMonth('booking_date')
    ).values('month').annotate(total=Sum('amount')).order_by('month')
    earnings_by_month = list(earnings_by_month)
    for item in earnings_by_month:
        if item['month']:
            item['month'] = item['month'].strftime('%Y-%m')

    # Если запрос AJAX, возвращаем JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'users_by_month': users_by_month,
            'bookings_by_status': list(bookings_by_status),
            'online_bookings_count': online_bookings_count,
            'total_earnings': total_earnings,
            'earnings_by_month': earnings_by_month,
        })

    return render(request, 'staff/statistics.html', {
        'users_by_month': users_by_month,
        'bookings_by_status': list(bookings_by_status),
        'online_bookings_count': online_bookings_count,
        'total_earnings': total_earnings,
        'earnings_by_month': earnings_by_month,
    })

def events_view(request):
    events = Event.objects.all()

    # Фильтрация по типу события (если выбран)
    filter_by_type = request.GET.get('type')
    if filter_by_type:
        events = events.filter(event_type=filter_by_type)

    # Фильтрация по дате
    event_date = request.GET.get('event_date')
    if event_date:
        events = events.filter(date__date=event_date)

    # Фильтрация по статусу
    moderation_status = request.GET.get('moderation_status')
    if moderation_status:
        events = events.filter(moderation_status=moderation_status)

    # Сортировка
    sort_by = request.GET.get('sort_by', '')
    if sort_by == 'date':
        events = events.order_by('date')
    elif sort_by == 'name':
        events = events.order_by('name')

    # Пагинация
    paginator = Paginator(events, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Проверяем, есть ли мероприятия по заданным фильтрам
    no_events = events.count() == 0

    return render(request, 'staff/events.html', {
        'events': page_obj,
        'event_date': event_date,
        'moderation_status': moderation_status,
        'sort_by': sort_by,
        'no_events': no_events,
    })

# Новое представление для просмотра информации о мероприятии через AJAX
@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('staff/partials/view_event.html', {'event': event}, request=request)
        return JsonResponse({'html': html})
    else:
        return JsonResponse({'error': 'This endpoint is only accessible via AJAX.'}, status=400)

@login_required
@role_required('Admin')
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            messages.success(request, 'Мероприятие успешно создано и отправлено на модерацию.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Мероприятие успешно создано.'})
            else:
                return redirect('events')
        else:
            messages.error(request, 'Ошибка при создании мероприятия.')
    else:
        form = EventForm()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('staff/partials/edit_event_form.html', {'form': form}, request=request)
        return JsonResponse({'html': html})
    else:
        return render(request, 'staff/partials/edit_event_form.html', {'form': form})

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'This endpoint is only accessible via AJAX.'}, status=400)

    if request.method == 'GET':
        form = EventForm(instance=event)
        html = render_to_string('staff/partials/edit_event_form.html', {'form': form, 'event': event}, request=request)
        return JsonResponse({'html': html})
    elif request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Мероприятие успешно обновлено.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def approve_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.moderation_status = 'approved'
    event.save()
    messages.success(request, f'Мероприятие "{event.name}" подтверждено.')
    return redirect('events')

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def reject_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.moderation_status = 'rejected'
    event.save()
    messages.success(request, f'Мероприятие "{event.name}" отклонено.')
    return redirect('events')

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    messages.success(request, 'Мероприятие успешно удалено.')
    return redirect('events')

# Добавляем недостающую функцию view_booking
@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def view_booking(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Ищем бронирование, где название мероприятия совпадает с именем события
    booking = Booking.objects.filter(event_name=event.name).first()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('staff/partials/view_booking.html', {'booking': booking}, request=request)
        return JsonResponse({'html': html})
    else:
        return JsonResponse({'error': 'This endpoint is only accessible via AJAX.'}, status=400)