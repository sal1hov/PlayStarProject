from main.models import CustomUser, Profile, Child
from bookings.models import Booking
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Avg, F, Q
from django.db.models.functions import TruncMonth, TruncDay
from django.template.loader import render_to_string
from .models import Event, Shift, ShiftRequest
from .forms import EventForm, ShiftRequestForm
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
import traceback
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import ShiftForm
from django.views import View
from django.db import transaction


logger = logging.getLogger(__name__)


def role_required(*group_names):
    def in_groups(user):
        if user.is_authenticated:
            if bool(user.groups.filter(name__in=group_names)) or user.is_superuser:
                return True
        return False

    return user_passes_test(in_groups)


@login_required
@role_required('Admin', 'Manager')
def admin_dashboard(request):
    all_users = CustomUser.objects.all()
    users = CustomUser.objects.all().order_by('-date_joined')
    search_query = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '').strip().upper()
    bookings = Booking.objects.select_related('user').all().order_by('-created_at')

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

    return render(request, 'staff/admin/dashboard.html', {
        'users': page_obj,
        'bookings': bookings,
        'total_users': total_users,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings
    })


@login_required
@role_required('Admin', 'Manager')
def edit_user(request, user_id):
    user_to_edit = get_object_or_404(CustomUser, id=user_id)
    profile, created = Profile.objects.get_or_create(user=user_to_edit)
    children = Child.objects.filter(profile=profile)

    if request.method == 'POST':
        try:
            user_to_edit.role = request.POST.get('role')
            user_to_edit.professional_role = request.POST.get('professional_role', 'none')  # Добавлено
            user_to_edit.first_name = request.POST.get('first_name')
            user_to_edit.last_name = request.POST.get('last_name')
            user_to_edit.email = request.POST.get('email')
            user_to_edit.phone_number = request.POST.get('phone_number')
            user_to_edit.is_active = 'is_active' in request.POST

            if request.POST.get('password'):
                user_to_edit.set_password(request.POST.get('password'))
                update_session_auth_hash(request, user_to_edit)

            profile.bonuses = request.POST.get('bonuses', 0)
            profile.save()

            user_to_edit.save()
            messages.success(request, 'Данные пользователя успешно обновлены.')
            return redirect('staff:admin-dashboard')

        except Exception as e:
            messages.error(request, f'Ошибка при обновлении пользователя: {str(e)}')
            logger.error(f"Error updating user {user_id}: {str(e)}")

    return render(request, 'staff/admin/edit_user.html', {
        'user': user_to_edit,
        'profile': profile,
        'children': children,
        'role_choices': CustomUser.ROLE_CHOICES,
        'professional_roles': CustomUser.PROFESSIONAL_ROLES  # Добавлено
    })


@login_required
@role_required('Admin', 'Manager')
def delete_user(request, user_id):
    if request.method == 'POST':
        try:
            user_to_delete = get_object_or_404(CustomUser, id=user_id)
            username = user_to_delete.username
            user_to_delete.delete()

            # Для AJAX-запросов возвращаем JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Пользователь {username} успешно удалён'
                })

            # Для обычных запросов сохраняем сообщение и редиректим
            messages.success(request, 'Пользователь успешно удален.')
            return redirect('staff:admin-dashboard')

        except Exception as e:
            error_msg = f'Ошибка при удалении пользователя: {str(e)}'
            logger.error(error_msg)

            # Для AJAX-запросов возвращаем ошибку
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=500)

            # Для обычных запросов сохраняем ошибку и редиректим
            messages.error(request, error_msg)
            return redirect('staff:admin-dashboard')

    # Блокируем GET-запросы к этому эндпоинту
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'Метод не разрешен'
        }, status=405)

    return redirect('staff:admin-dashboard')


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
    return redirect('staff:admin-dashboard')


@login_required
@role_required('Admin', 'Manager')
def manager_dashboard(request):
    bookings = Booking.objects.all()
    return render(request, 'staff/manager_dashboard.html', {'bookings': bookings})


@login_required
@role_required('Staff')
def employee_dashboard(request):
    # Исправленный путь к шаблону
    return render(request, 'staff/employee/dashboard.html')


@login_required
@role_required('Admin', 'Manager')
def statistics_view(request):
    try:
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        start_date = None
        end_date = None

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%d.%m.%y').date()
                end_date = datetime.strptime(end_date_str, '%d.%m.%y').date()
                start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
                end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
            except ValueError as e:
                logger.error(f"Ошибка формата даты: {e}")
                return JsonResponse({'error': 'Неверный формат даты. Используйте ДД.ММ.ГГ'}, status=400)

        users_query = CustomUser.objects.all()
        bookings_query = Booking.objects.all()
        earnings_query = Booking.objects.filter(status='approved')

        if start_date and end_date:
            users_query = users_query.filter(date_joined__range=(start_date, end_date))
            bookings_query = bookings_query.filter(created_at__range=(start_date, end_date))
            earnings_query = earnings_query.filter(created_at__range=(start_date, end_date))

        users_by_month = users_query.annotate(
            month=TruncMonth('date_joined')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        bookings_by_status = bookings_query.values('status').annotate(
            count=Count('id')
        ).order_by('status')

        earnings_by_month = earnings_query.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total=Sum(F('prepayment') + F('paid_amount'))
        ).order_by('month')

        users_data = []
        for item in users_by_month:
            users_data.append({
                'month': item['month'].strftime('%Y-%m') if item['month'] else '',
                'count': item['count']
            })

        earnings_data = []
        for item in earnings_by_month:
            earnings_data.append({
                'month': item['month'].strftime('%Y-%m') if item['month'] else '',
                'total': float(item['total']) if item['total'] else 0.0
            })

        status_mapping = dict(Booking.STATUS_CHOICES)
        bookings_data = []
        for item in bookings_by_status:
            bookings_data.append({
                'status': status_mapping.get(item['status'], item['status']),
                'count': item['count']
            })

        total_earnings = earnings_query.aggregate(
            total=Sum(F('prepayment') + F('paid_amount'))
        ).get('total') or 0.0

        online_bookings_count = bookings_query.filter(
            booking_type__in=['birthday', 'vr', 'animation']
        ).count()

        context = {
            'users_by_month': users_data,
            'bookings_by_status': bookings_data,
            'earnings_by_month': earnings_data,
            'total_earnings': float(total_earnings),
            'online_bookings_count': online_bookings_count,
        }

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(context)

        return render(request, 'staff/admin/statistics.html', context)

    except Exception as e:
        logger.error(f"Critical error in statistics_view: {str(e)}", exc_info=True)
        error_message = 'Произошла ошибка на сервере' if not settings.DEBUG else str(e)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': error_message}, status=500)

        return render(request, 'staff/admin/statistics.html', {
            'error': error_message,
            'traceback': traceback.format_exc() if settings.DEBUG else None
        })


@login_required
@role_required('Admin', 'Manager')
def events_view(request):
    events = Event.objects.filter(booking__isnull=True)

    filter_by_type = request.GET.get('type')
    if filter_by_type:
        events = events.filter(event_type=filter_by_type)

    event_date = request.GET.get('event_date')
    if event_date:
        events = events.filter(date__date=event_date)

    moderation_status = request.GET.get('moderation_status')
    if moderation_status:
        events = events.filter(moderation_status=moderation_status)

    sort_by = request.GET.get('sort_by', '')
    if sort_by == 'date':
        events = events.order_by('date')
    elif sort_by == 'name':
        events = events.order_by('name')

    paginator = Paginator(events, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    no_events = events.count() == 0

    return render(request, 'staff/admin/events.html', {
        'events': page_obj,
        'event_date': event_date,
        'moderation_status': moderation_status,
        'sort_by': sort_by,
        'no_events': no_events,
    })


@login_required
@role_required('Admin', 'Manager')
def event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('staff/common/partials/view_event.html', {'event': event}, request=request)
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
                return redirect('staff:events')
        else:
            messages.error(request, 'Ошибка при создании мероприятия.')
    else:
        form = EventForm()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('staff/common/partials/edit_event_form.html', {'form': form}, request=request)
        return JsonResponse({'html': html})
    else:
        return render(request, 'staff/common/partials/edit_event_form.html', {'form': form})


@login_required
@role_required('Admin', 'Manager')
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'This endpoint is only accessible via AJAX.'}, status=400)

    if request.method == 'GET':
        form = EventForm(instance=event)
        html = render_to_string('staff/common/partials/edit_event_form.html', {'form': form, 'event': event},
                                request=request)
        return JsonResponse({'html': html})
    elif request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Мероприятие успешно обновлено.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
@role_required('Admin', 'Manager')
def approve_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.moderation_status = 'approved'
    event.save()
    messages.success(request, f'Мероприятие "{event.name}" подтверждено.')
    return redirect('staff:events')


@login_required
@role_required('Admin', 'Manager')
def reject_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.moderation_status = 'rejected'
    event.save()
    messages.success(request, f'Мероприятие "{event.name}" отклонено.')
    return redirect('staff:events')


@login_required
@role_required('Admin', 'Manager')
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    messages.success(request, 'Мероприятие успешно удалено.')
    return redirect('staff:events')


@login_required
@role_required('Admin', 'Manager')
def view_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('staff/common/partials/view_booking.html',
                                {'booking': booking},
                                request=request)
        return JsonResponse({'html': html})
    return JsonResponse({'error': 'This endpoint is only accessible via AJAX.'}, status=400)


@login_required
@role_required('Admin', 'Manager')
def income_management(request):
    try:
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        start_date = None
        end_date = None

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%d.%m.%Y').date()
                end_date = datetime.strptime(end_date_str, '%d.%m.%Y').date()
            except ValueError:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Неверный формат даты'}, status=400)
                else:
                    messages.error(request, 'Неверный формат даты')
                    return redirect('staff:income-management')

        bookings = Booking.objects.all().order_by('-created_at')

        if start_date and end_date:
            bookings = bookings.filter(
                created_at__date__range=(start_date, end_date)
            )

        total_income = bookings.aggregate(
            total=Sum(F('prepayment') + F('cashier_payment') + F('paid_amount'))
        )['total'] or Decimal('0.00')

        avg_income = bookings.aggregate(
            avg=Avg(F('prepayment') + F('cashier_payment') + F('paid_amount'))
        )['avg'] or Decimal('0.00')

        total_prepayments = bookings.aggregate(
            total=Sum('prepayment')
        )['total'] or Decimal('0.00')

        earnings_by_month = (
            bookings.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum(
                F('prepayment') + F('cashier_payment') + F('paid_amount')
            ))
            .order_by('month')
        )

        chart_data = [
            {
                'month': item['month'].strftime('%Y-%m') if item['month'] else '',
                'total': float(item['total']) if item['total'] else 0.0
            }
            for item in earnings_by_month
        ]

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'total_income': float(total_income),
                'average_income': float(avg_income),
                'total_prepayments': float(total_prepayments),
                'bookings': [
                    {
                        'id': b.id,
                        'event_name': b.event_name,
                        'created_at': b.created_at.isoformat(),
                        'total_payment': float(b.total_payment),
                        'prepayment': float(b.prepayment),
                        'status': b.status,
                        'status_display': b.status_display
                    }
                    for b in bookings
                ],
                'earnings_by_month': chart_data
            })

        return render(request, 'staff/admin/income_management.html', {
            'bookings': bookings,
            'total_income': total_income,
            'average_income': avg_income,
            'total_prepayments': total_prepayments,
            'earnings_by_month': chart_data,
            'start_date': start_date,
            'end_date': end_date
        })

    except Exception as e:
        logger.error(f"Ошибка в income_management: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
        else:
            raise


@csrf_exempt
@login_required
@role_required('Admin', 'Manager')
def edit_income(request):
    if request.method == 'POST':
        try:
            booking = Booking.objects.get(id=request.POST.get('booking_id'))
            prepayment = request.POST.get('prepayment') == 'true'
            paid_amount = Decimal(request.POST.get('paid_amount', '0'))

            if prepayment:
                booking.prepayment = max(paid_amount, Decimal('1000.00'))
                booking.paid_amount = Decimal('0.00')
            else:
                booking.paid_amount = paid_amount
                booking.prepayment = Decimal('0.00')

            booking.save()

            return JsonResponse({
                'success': True,
                'new_prepayment': float(booking.prepayment),
                'new_paid_amount': float(booking.paid_amount),
                'new_total': float(booking.total_payment)
            })

        except Booking.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Бронирование не найдено'}, status=404)
        except Exception as e:
            logger.error(f"Ошибка обновления оплаты: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Метод не разрешен'}, status=405)


@login_required
@role_required('Admin', 'Manager')
def income_management_data(request):
    try:
        date_range = request.GET.get('date_range', '')
        start_date = end_date = None

        if date_range:
            try:
                dates = date_range.split(' to ')
                start_date = datetime.strptime(dates[0], '%d.%m.%Y').date()
                end_date = datetime.strptime(dates[-1], '%d.%m.%Y').date() if len(dates) > 1 else start_date
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Неверный формат даты: {e}'})

        bookings = Booking.objects.all()
        if start_date and end_date:
            bookings = bookings.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )

        total_income = bookings.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
        avg_income = bookings.aggregate(avg=Avg('paid_amount'))['avg'] or Decimal('0.00')
        total_prepayments = bookings.filter(prepayment=True).aggregate(total=Sum('paid_amount'))['total'] or Decimal(
            '0.00')
        total_earnings = bookings.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')

        earnings_by_month = bookings.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total=Sum('paid_amount')
        ).order_by('month')

        chart_data = {
            'labels': [],
            'data': []
        }
        for item in earnings_by_month:
            if item['month']:
                chart_data['labels'].append(item['month'].strftime('%Y-%m'))
                chart_data['data'].append(float(item['total']))

        bookings_data = list(bookings.order_by('-created_at').values(
            'id',
            'event_name',
            'created_at',
            'paid_amount',
            'prepayment',
            'status'
        ))
        for booking in bookings_data:
            booking['status_display'] = dict(Booking.STATUS_CHOICES).get(booking['status'], booking['status'])

        return JsonResponse({
            'success': True,
            'total_income': float(total_income),
            'average_income': float(avg_income),
            'total_prepayments': float(total_prepayments),
            'chart_data': chart_data,
            'bookings': bookings_data,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


class ShiftManagementView(TemplateView):
    template_name = 'staff/admin/shift_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Фильтрация смен
        shifts = Shift.objects.filter(date__gte=timezone.now().date()).order_by('date')
        date_filter = self.request.GET.get('date')
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                shifts = shifts.filter(date=filter_date)
            except ValueError:
                pass
        context['shifts'] = shifts

        # Фильтрация заявок
        requests = ShiftRequest.objects.select_related('employee').order_by('-created_at')
        status = self.request.GET.get('status')
        if status:
            requests = requests.filter(status=status)

        date_req = self.request.GET.get('date_req')
        if date_req:
            requests = requests.filter(date=date_req)

        context['requests'] = requests
        context['approved_requests_count'] = ShiftRequest.objects.filter(status='approved').count()
        context['pending_requests_count'] = ShiftRequest.objects.filter(status='pending').count()

        return context

class ShiftListView(ListView):
    model = Shift
    template_name = 'staff/admin/shift_list.html'
    context_object_name = 'shifts'
    paginate_by = 10

    def get_queryset(self):
        queryset = Shift.objects.filter(date__gte=timezone.now().date()).order_by('date')

        # Фильтрация по дате
        date_filter = self.request.GET.get('date')
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                queryset = queryset.filter(date=filter_date)
            except ValueError:
                pass

        return queryset


class CreateShiftView(View):
    template_name = 'staff/admin/create_shift.html'
    success_url = reverse_lazy('staff:shift-management')

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        try:
            week_start = request.POST.get('week_start')
            if not week_start:
                messages.error(request, "Не указана дата начала недели")
                return render(request, self.template_name)

            # Собираем данные по дням
            dates = request.POST.getlist('dates[]')
            staff_data = {}

            # Собираем данные по сотрудникам
            for key in request.POST:
                if key.startswith('staff['):
                    # Формат ключа: staff[day_index][staff_index]
                    parts = key.split('[')
                    day_index = int(parts[1].split(']')[0])
                    staff_index = int(parts[2].split(']')[0])

                    # Получаем связанные данные
                    role = request.POST.get(f'role[{day_index}][{staff_index}]')
                    shift_type = request.POST.get(f'shift_type[{day_index}][{staff_index}]')
                    staff_id = request.POST.get(key)

                    if not all([role, shift_type, staff_id]):
                        continue

                    if day_index not in staff_data:
                        staff_data[day_index] = []

                    staff_data[day_index].append({
                        'role': role,
                        'shift_type': shift_type,
                        'staff_id': staff_id
                    })

            # Создаем смены
            created_shifts = 0
            for day_index, staff_list in staff_data.items():
                if day_index >= len(dates):
                    continue

                try:
                    date = datetime.strptime(dates[day_index], '%Y-%m-%d').date()
                except ValueError:
                    continue

                for staff_info in staff_list:
                    try:
                        staff_member = CustomUser.objects.get(id=staff_info['staff_id'])
                    except CustomUser.DoesNotExist:
                        continue

                    # Создаем смену
                    shift = Shift.objects.create(
                        date=date,
                        role=staff_info['role'],
                        shift_type=staff_info['shift_type'],
                        max_staff=1
                    )
                    shift.staff.add(staff_member)
                    created_shifts += 1

            messages.success(request, f"Успешно создано {created_shifts} смен!")
            return redirect(self.success_url)

        except Exception as e:
            logger.error(f"Ошибка при создании смен: {str(e)}", exc_info=True)
            messages.error(request, f"Ошибка при создании смен: {str(e)}")
            return render(request, self.template_name)

class UpdateShiftView(UpdateView):
    model = Shift
    form_class = ShiftForm
    template_name = 'staff/admin/edit_shift.html'
    success_url = reverse_lazy('staff:shift-management')

    def form_valid(self, form):
        messages.success(self.request, 'Смена успешно обновлена')
        return super().form_valid(form)

class MyShiftRequestsView(ListView):
    model = ShiftRequest
    template_name = 'staff/employee/shifts/my_shift_requests.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return ShiftRequest.objects.filter(employee=self.request.user).order_by('-date')

class CreateShiftRequestView(CreateView):
    model = ShiftRequest
    form_class = ShiftRequestForm
    template_name = 'staff/employee/shifts/shift_request_form.html'
    success_url = reverse_lazy('staff:my-shift-requests')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.employee = self.request.user
        messages.success(self.request, 'Заявка на смену успешно создана!')
        return super().form_valid(form)

class UpdateShiftRequestView(UpdateView):
    model = ShiftRequest
    form_class = ShiftRequestForm
    template_name = 'staff/employee/shifts/shift_request_form.html'
    success_url = reverse_lazy('staff:my-shift-requests')

    def get_queryset(self):
        return ShiftRequest.objects.filter(employee=self.request.user, status='pending')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context['is_weekend'] = today.weekday() in [5, 6]
        context['user_role'] = self.request.user.get_role_display()
        context['professional_role'] = self.request.user.professional_role
        context['professional_role_display'] = self.request.user.get_professional_role_display()
        return context


class AdminShiftApprovalView(ListView):
    template_name = "staff/admin/shift_approval.html"
    model = ShiftRequest
    context_object_name = "requests"
    paginate_by = 10

    def get_queryset(self):
        queryset = ShiftRequest.objects.select_related('employee').order_by('-created_at')

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        date = self.request.GET.get('date')
        if date:
            queryset = queryset.filter(date=date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['approved_requests_count'] = ShiftRequest.objects.filter(status='approved').count()
        context['pending_requests_count'] = ShiftRequest.objects.filter(status='pending').count()
        return context


class ShiftRequestDetailView(DetailView):
    model = ShiftRequest
    context_object_name = 'request'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not (request.user == obj.employee or
                request.user.role in ['ADMIN', 'MANAGER']):
            return HttpResponseForbidden("У вас нет доступа к этой странице")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if self.request.user.role in ['ADMIN', 'MANAGER']:
            return ['staff/admin/shift_request_details.html']
        else:
            return ['staff/employee/shifts/shift_request_details.html']


@login_required
@role_required('Admin', 'Manager')
@transaction.atomic
def approve_shift_request(request, pk):
    shift_request = get_object_or_404(ShiftRequest, pk=pk)

    # Проверяем, существует ли уже смена на эту дату и роль
    shift, created = Shift.objects.get_or_create(
        date=shift_request.date,
        role=shift_request.role,
        defaults={
            'shift_type': shift_request.get_shift_type_from_times(),
            'max_staff': 1
        }
    )

    # Добавляем сотрудника в смену
    if shift_request.employee not in shift.staff.all():
        shift.staff.add(shift_request.employee)

    # Обновляем статус заявки
    shift_request.status = 'approved'
    shift_request.save()

    messages.success(request, 'Заявка утверждена и сотрудник добавлен в смену')
    return redirect('staff:shift-management')


@login_required
@role_required('Admin', 'Manager')
def reject_shift_request(request, pk):
    shift_request = get_object_or_404(ShiftRequest, pk=pk)

    if request.method == 'POST':
        shift_request.admin_comment = request.POST.get('admin_comment', '')

    shift_request.status = 'rejected'
    shift_request.save()
    messages.success(request, 'Заявка отклонена')
    return redirect('staff:shift-management')


@login_required
@role_required('Admin', 'Manager')
def delete_shift_request(request, pk):
    shift_request = get_object_or_404(ShiftRequest, pk=pk)
    shift_request.delete()
    messages.success(request, 'Заявка на смену успешно удалена.')
    return redirect('staff:shift-management')


@login_required
@role_required('Admin', 'Manager')
def manage_user_children(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    profile = Profile.objects.get_or_create(user=user)[0]
    children = Child.objects.filter(profile=profile)

    if request.method == 'POST':
        if 'add_child' in request.POST:
            name = request.POST.get('child_name')
            age = request.POST.get('child_age')
            birthdate = request.POST.get('child_birthdate')
            gender = request.POST.get('child_gender')

            if name and age:
                Child.objects.create(
                    profile=profile,
                    name=name,
                    age=age,
                    birthdate=birthdate if birthdate else None,
                    gender=gender if gender else None
                )
                messages.success(request, 'Ребенок успешно добавлен')
                return redirect('staff:manage-user-children', user_id=user_id)
            else:
                messages.error(request, 'Имя и возраст обязательны для заполнения')

        elif 'delete_child' in request.POST:
            child_id = request.POST.get('child_id')
            if child_id:
                child = get_object_or_404(Child, id=child_id, profile=profile)
                child.delete()
                messages.success(request, 'Ребенок успешно удален')
                return redirect('staff:manage-user-children', user_id=user_id)

    return render(request, 'staff/admin/manage_user_children.html', {
        'user': user,
        'profile': profile,
        'children': children
    })


@login_required
@role_required('Admin', 'Manager')
@ensure_csrf_cookie
def delete_booking_admin(request, booking_id):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Требуется AJAX запрос'}, status=400)

    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)

    try:
        booking = Booking.objects.get(id=booking_id)
        Event.objects.filter(booking=booking).delete()
        booking.delete()

        return JsonResponse({
            'success': True,
            'message': 'Бронирование успешно удалено'
        })

    except Booking.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Бронирование не найдено'
        }, status=404)

    except Exception as e:
        logger.error(f"Ошибка при удалении: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }, status=500)


@login_required
@role_required('Admin', 'Manager')
def filter_users(request):
    search_query = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '').strip().upper()
    page_number = request.GET.get('page', 1)

    users = CustomUser.objects.all().order_by('-date_joined')

    if search_query:
        users = users.filter(username__icontains=search_query)

    if role_filter:
        users = users.filter(role=role_filter)

    paginator = Paginator(users, 5)
    page_obj = paginator.get_page(page_number)

    html = render_to_string(
        'staff/common/partials/user_table.html',
        {'users': page_obj},
        request=request
    )

    return JsonResponse({'html': html})


@login_required
@role_required('Admin', 'Manager')
def create_shift(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        try:
            Shift.objects.create(
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            messages.success(request, 'Смена успешно создана')
            return redirect('staff:shift_list')
        except Exception as e:
            messages.error(request, f'Ошибка при создании смены: {str(e)}')

    return render(request, 'staff/admin/create_shift.html')


@login_required
@role_required('Admin', 'Manager')
def edit_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)

    if request.method == 'POST':
        shift.date = request.POST.get('date')
        shift.start_time = request.POST.get('start_time')
        shift.end_time = request.POST.get('end_time')
        shift.save()
        messages.success(request, 'Смена успешно обновлена')
        return redirect('staff:shift_list')

    return render(request, 'staff/admin/edit_shift.html', {'shift': shift})


@login_required
@role_required('Admin', 'Manager')
def delete_shift(request, pk):
    shift = get_object_or_404(Shift, pk=pk)

    if shift.shiftrequest_set.exists():
        messages.error(request, 'Нельзя удалить смену с активными заявками')
        return redirect('staff:shift-management')

    shift.delete()
    messages.success(request, 'Смена успешно удалена')
    return redirect('staff:shift-management')


@login_required
def get_shift_types(request):
    role = request.GET.get('role')
    form = ShiftForm()
    types = form.get_shift_type_choices(role)
    return JsonResponse({'types': types})


@login_required
def get_staff(request):
    role = request.GET.get('role')
    staff = CustomUser.objects.filter(
        professional_role=role,
        role__in=['STAFF', 'MANAGER', 'ADMIN']
    ).values('id', 'first_name', 'last_name', 'professional_role')

    staff_data = []
    for user in staff:
        staff_data.append({
            'id': user['id'],
            'full_name': f"{user['first_name']} {user['last_name']}",
            'professional_role': dict(CustomUser.PROFESSIONAL_ROLES).get(
                user['professional_role'], user['professional_role']
            )
        })

    return JsonResponse({'staff': staff_data})