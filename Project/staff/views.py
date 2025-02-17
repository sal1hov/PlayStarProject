from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponse, JsonResponse
import csv
from main.models import CustomUser
from bookings.models import Booking
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.template.loader import render_to_string
from .models import Event
import io
import pandas as pd  # для импорта из Excel
from .forms import EventForm

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
    writer.writerow(['ID', 'User', 'Date', 'Status'])
    for booking in Booking.objects.all():
        writer.writerow([booking.id, booking.user.username, booking.booking_date, booking.status])
    return response

def statistics_view(request):
    users_by_month = CustomUser.objects.annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(count=Count('id')).order_by('month')
    users_by_month = list(users_by_month)
    for item in users_by_month:
        if item['month']:
            item['month'] = item['month'].strftime('%Y-%m')

    bookings_by_status = Booking.objects.values('status').annotate(count=Count('id')).order_by('status')

    return render(request, 'staff/statistics.html', {
        'users_by_month': users_by_month,
        'bookings_by_status': list(bookings_by_status),
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
    # Получаем бронирование, где название мероприятия совпадает с именем события
    booking = Booking.objects.filter(event_name=event.name).first()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('staff/partials/view_event.html', {'event': event, 'booking': booking}, request=request)
        return JsonResponse({'html': html})
    else:
        return JsonResponse({'error': 'This endpoint is only accessible via AJAX.'}, status=400)

@login_required
@role_required('Admin')
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            # Создаем мероприятие, не сохраняя сразу, чтобы добавить данные пользователя
            event = form.save(commit=False)
            # Предполагается, что в модели Event есть поля client_name и client_login
            event.client_name = request.user.get_full_name() or request.user.username
            event.client_login = request.user.username
            event.save()
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
@role_required('Admin')
def import_events(request):
    """
    Импорт мероприятий из файлов .csv, .xls или .xlsx.
    Ожидается, что в файле будут столбцы: name, description, date, location, event_type.
    Все импортированные мероприятия получают статус модерации "pending".
    """
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                messages.error(request, "Неподдерживаемый формат файла.")
                return redirect('events')

            df.columns = [col.strip().lower() for col in df.columns]

            if 'name' not in df.columns:
                messages.error(request, "Файл не содержит столбца 'name'.")
                return redirect('events')

            for index, row in df.iterrows():
                if not row.get('name'):
                    messages.error(request, f"Ошибка: строка {index+1} не содержит имя мероприятия.")
                    continue

                etype = row.get('event_type', 'other')
                if isinstance(etype, str):
                    etype = etype.strip().lower()
                    if etype in ['праздник', 'holiday']:
                        etype = 'holiday'
                    elif etype in ['концерт', 'concert']:
                        etype = 'concert'
                    elif etype in ['семинар', 'seminar']:
                        etype = 'seminar'
                    else:
                        etype = 'other'
                else:
                    etype = 'other'

                event = Event(
                    name=row.get('name'),
                    description=row.get('description'),
                    date=row.get('date'),
                    location=row.get('location'),
                    event_type=etype,
                    moderation_status='pending'
                )
                event.save()

            messages.success(request, "Мероприятия успешно импортированы.")
        except Exception as e:
            messages.error(request, f"Ошибка при импорте: {e}")
    else:
        messages.error(request, "Пожалуйста, загрузите файл для импорта.")
    return redirect('events')

@login_required
@role_required('Admin')
def export_events_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="events.csv"'
    writer = csv.writer(response)
    writer.writerow(
        ['ID', 'Название', 'Дата и время', 'Описание', 'Местоположение', 'Тип мероприятия', 'Статус модерации']
    )

    events = Event.objects.all()
    for event in events:
        writer.writerow([event.id, event.name, event.date, event.description, event.location, event.event_type,
                         event.moderation_status])
    return response

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Требуем, чтобы доступ к этому эндпоинту был только через AJAX
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

    # Если мероприятие связано с бронированием, обновляем его статус
    if event.booking:
        event.booking.status = 'Подтверждено'
        event.booking.save()
        messages.success(request, f'Мероприятие "{event.name}" и связанное бронирование подтверждены.')
    else:
        messages.success(request, f'Мероприятие "{event.name}" подтверждено.')
    return redirect('events')

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def reject_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.moderation_status = 'rejected'
    event.save()

    # Если мероприятие связано с бронированием, обновляем его статус
    if event.booking:
        event.booking.status = 'Отклонено'
        event.booking.save()
        messages.success(request, f'Мероприятие "{event.name}" и связанное бронирование отклонены.')
    else:
        messages.success(request, f'Мероприятие "{event.name}" отклонено.')
    return redirect('events')

@login_required
@user_passes_test(role_required('Admin', 'Manager'))
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    messages.success(request, 'Мероприятие успешно удалено.')
    return redirect('events')

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
