from main.models import CustomUser, Profile, Child
from bookings.models import Booking
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Avg, F, Q
from django.db.models.functions import TruncMonth
from django.template.loader import render_to_string
from .models import (
    Event, Shift, ShiftRequest,
    ChildCityItem, ArcadeMachineItem, VRArenaItem,
    BirthdayPackage, VRPackage, StandardPackage,
    PlayStationSlot, VRRide
)
from .forms import EventForm, ShiftRequestForm, ShiftForm
from datetime import datetime
from django.utils import timezone
from decimal import Decimal
from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
import traceback
from django.conf import settings
from django.db import transaction
from django.urls import reverse

logger = logging.getLogger(__name__)


def role_required(*group_names):
    """
    Декоратор: пользователь должен быть в одной из групп group_names или superuser.
    """
    def in_groups(user):
        if user.is_authenticated:
            if bool(user.groups.filter(name__in=group_names)) or user.is_superuser:
                return True
        return False

    return lambda u: user_passes_test(in_groups)(u)


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
    bookings_qs = Booking.objects.all()
    booking_search = request.GET.get('booking_search')

    if booking_search:
        bookings_qs = bookings_qs.filter(event_name__icontains=booking_search)

    booking_status = request.GET.get('booking_status')
    if booking_status:
        bookings_qs = bookings_qs.filter(status=booking_status)

    total_bookings = bookings_qs.count()
    pending_bookings = bookings_qs.filter(status='pending').count()

    paginator = Paginator(users, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # ===== НОВЫЙ КОД ДЛЯ ПАНЕЛЕЙ =====
    today = timezone.now().date()
    shifts_today = Shift.objects.filter(date=today).prefetch_related('staff')
    staff_working = []
    for shift in shifts_today:
        for staff_member in shift.staff.all():
            staff_working.append({
                'staff': staff_member,
                'role': shift.get_role_display(),
                'shift_type': shift.get_shift_type_display(),
                'time_range': f"{shift.start_time} - {shift.end_time}"
            })

    bookings_today = Booking.objects.filter(
        event_date__date=today,
        status='approved'
    ).select_related('user')
    # ===== КОНЕЦ НОВОГО КОДА =====

    return render(request, 'staff/admin/dashboard.html', {
        'users': page_obj,
        'bookings': bookings_qs,
        'total_users': total_users,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        # ===== НОВЫЕ ПЕРЕМЕННЫЕ =====
        'staff_working': staff_working,
        'bookings_today': bookings_today,
        'today': today.strftime("%d.%m.%Y")
        # ===== КОНЕЦ НОВЫХ ПЕРЕМЕННЫХ =====
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
            user_to_edit.professional_role = request.POST.get('professional_role', 'none')
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
        'professional_roles': CustomUser.PROFESSIONAL_ROLES
    })


@login_required
@role_required('Admin', 'Manager')
def delete_user(request, user_id):
    if request.method == 'POST':
        try:
            user_to_delete = get_object_or_404(CustomUser, id=user_id)
            username = user_to_delete.username
            user_to_delete.delete()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Пользователь {username} успешно удалён'
                })

            messages.success(request, 'Пользователь успешно удален.')
            return redirect('staff:admin-dashboard')

        except Exception as e:
            error_msg = f'Ошибка при удалении пользователя: {str(e)}'
            logger.error(error_msg)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=500)

            messages.error(request, error_msg)
            return redirect('staff:admin-dashboard')

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
@role_required('Admin', 'Manager')
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Мероприятие успешно создано.'})
            return redirect('staff:events')
        else:
            errors = form.errors.as_json()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Ошибка валидации формы.', 'errors': errors}, status=400)
            return render(request, 'staff/admin/events.html', {'form': form})
    else:
        form = EventForm()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('staff/common/partials/edit_event_form.html', {'form': form}, request=request)
        return JsonResponse({'html': html})
    else:
        return render(request, 'staff/admin/events.html', {'form': form})


@login_required
@role_required('Admin', 'Manager')
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'GET':
        form = EventForm(instance=event)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('staff/common/partials/edit_event_form.html',
                                    {'form': form, 'event': event},
                                    request=request)
            return JsonResponse({'html': html})

        return render(request, 'staff/admin/edit_event.html', {
            'form': form,
            'event': event
        })

    elif request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Мероприятие успешно обновлено.'})

            messages.success(request, 'Мероприятие успешно обновлено.')
            return redirect('staff:events')

        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

            return render(request, 'staff/admin/edit_event.html', {
                'form': form,
                'event': event
            })


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
        )['total'] or 0.00

        avg_income = bookings.aggregate(
            avg=Avg(F('prepayment') + F('cashier_payment') + F('paid_amount'))
        )['avg'] or 0.00

        total_prepayments = bookings.aggregate(
            total=Sum('prepayment')
        )['total'] or 0.00

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
                        'status_display': b.get_status_display()
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
            prepayment_flag = request.POST.get('prepayment') == 'true'
            paid_amount = Decimal(request.POST.get('paid_amount', '0'))

            if prepayment_flag:
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
        total_prepayments = bookings.filter(prepayment=True).aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
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
        for b in bookings_data:
            b['status_display'] = dict(Booking.STATUS_CHOICES).get(b['status'], b['status'])

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

        date_filter = self.request.GET.get('date')
        status_filter = self.request.GET.get('status')
        date_req_filter = self.request.GET.get('date_req')

        shifts = Shift.objects.all().order_by('date')
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                shifts = shifts.filter(date=filter_date)
            except ValueError:
                pass
        context['shifts'] = shifts

        requests = ShiftRequest.objects.select_related('employee').order_by('-created_at')
        if status_filter:
            requests = requests.filter(status=status_filter)
        if date_req_filter:
            requests = requests.filter(date=date_req_filter)

        context['requests'] = requests
        context['approved_requests_count'] = ShiftRequest.objects.filter(status='approved').count()
        context['pending_requests_count'] = ShiftRequest.objects.filter(status='pending').count()

        context['current_filters'] = {
            'date': date_filter,
            'status': status_filter,
            'date_req': date_req_filter
        }

        return context


class ShiftListView(ListView):
    model = Shift
    template_name = 'staff/admin/shift_list.html'
    context_object_name = 'shifts'
    paginate_by = 10

    def get_queryset(self):
        queryset = Shift.objects.filter(date__gte=timezone.now().date()).order_by('date')
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

            dates = request.POST.getlist('dates[]')
            staff_data = {}

            for key in request.POST:
                if key.startswith('staff['):
                    parts = key.split('[')
                    day_index = int(parts[1].split(']')[0])
                    staff_index = int(parts[2].split(']')[0])

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

    shift, created = Shift.objects.get_or_create(
        date=shift_request.date,
        role=shift_request.role,
        defaults={
            'shift_type': shift_request.get_shift_type_from_times(),
            'max_staff': 1
        }
    )

    if shift_request.employee not in shift.staff.all():
        shift.staff.add(shift_request.employee)

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
    profile, _ = Profile.objects.get_or_create(user=user)
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


@ensure_csrf_cookie
@login_required
@role_required('Admin', 'Manager')
def delete_booking_admin(request, booking_id):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Требуется AJAX запрос'}, status=400)

    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)

    try:
        booking = Booking.objects.get(id=booking_id)
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
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

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
            return redirect('staff:shift-list')
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
        return redirect('staff:shift-list')

    return render(request, 'staff/admin/edit_shift.html', {'shift': shift})


@login_required
@role_required('Admin', 'Manager')
def delete_shift(request, pk):
    shift = get_object_or_404(Shift, pk=pk)

    existing_requests = ShiftRequest.objects.filter(
        date=shift.date,
        role=shift.role,
        start_time=shift.start_time,
        end_time=shift.end_time
    )

    if existing_requests.exists():
        error_msg = 'Нельзя удалить смену с активными заявками.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        messages.error(request, error_msg)
        return redirect('staff:shift-management')

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            shift.delete()
            return JsonResponse({
                'success': True,
                'message': 'Смена успешно удалена'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    shift.delete()
    messages.success(request, 'Смена успешно удалена')
    return redirect('staff:shift-management')


@login_required
def get_shift_types(request):
    role = request.GET.get('role')
    role_to_shift_types = {
        'animator': [('full', 'Полная смена'), ('morning', 'Утренняя'), ('evening', 'Вечерняя')],
        'additional': [('full', 'Полная смена'), ('additional_evening', 'Доп. вечерняя')],
        'vr_operator': [('full', 'Полная смена'), ('vr_evening', 'VR вечерняя')],
        'cashier': [('full', 'Полная смена')],
    }
    types = role_to_shift_types.get(role, [])
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


@login_required
@role_required('Admin', 'Manager')
def edit_day_shifts(request):
    selected_date = request.GET.get('date')
    if not selected_date:
        return HttpResponse("Дата не указана", status=400)

    shifts = Shift.objects.filter(date=selected_date).prefetch_related('staff')

    if request.method == 'POST':
        for shift in shifts:
            form = ShiftForm(request.POST, instance=shift, prefix=f'shift_{shift.pk}')
            if form.is_valid():
                form.save()
        messages.success(request, 'Смены успешно обновлены')
        return redirect('staff:shift-management')

    forms = []
    for shift in shifts:
        form = ShiftForm(instance=shift, prefix=f'shift_{shift.pk}')
        forms.append((shift, form))

    return render(request, 'staff/admin/edit_day_shifts.html', {
        'date': selected_date,
        'forms': forms
    })


@login_required
@role_required('Admin', 'Manager')
def duplicate_shift(request, pk):
    if request.method == 'POST':
        try:
            original = get_object_or_404(Shift, pk=pk)
            new_shift = Shift.objects.create(
                date=original.date,
                role=original.role,
                shift_type=original.shift_type,
                max_staff=original.max_staff
            )
            new_shift.staff.set(original.staff.all())

            form = ShiftForm(instance=new_shift, prefix=f'shift_{new_shift.pk}')
            html = render_to_string('staff/common/partials/shift_card.html', {
                'shift': new_shift,
                'form': form
            }, request=request)

            return JsonResponse({
                'success': True,
                'new_shift_html': html
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Метод не разрешен'}, status=405)


@login_required
def edit_day_shifts_view(request):
    date_str = request.GET.get('date')
    if not date_str:
        return render(request, 'staff/admin/edit_day_shifts.html', {
            'forms': [],
            'date': None
        })

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        target_date = timezone.now().date()

    shifts = Shift.objects.filter(date=target_date)

    if request.method == 'POST':
        forms = []
        all_valid = True
        for shift in shifts:
            form = ShiftForm(request.POST, instance=shift, prefix=f'shift_{shift.id}')
            forms.append((shift, form))
            if not form.is_valid():
                all_valid = False
        if all_valid:
            for _, form in forms:
                form.save()
            return render(request, 'staff/admin/edit_day_shifts.html', {
                'forms': forms,
                'date': target_date,
                'success': True
            })
    else:
        forms = [(shift, ShiftForm(instance=shift, prefix=f'shift_{shift.id}')) for shift in shifts]

    return render(request, 'staff/admin/edit_day_shifts.html', {
        'forms': forms,
        'date': target_date
    })


@login_required
@role_required('Admin', 'Manager')
def users_view(request):
    users = CustomUser.objects.all().order_by('-date_joined')

    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)

    is_active_filter = request.GET.get('is_active')
    if is_active_filter:
        users = users.filter(is_active=bool(int(is_active_filter)))

    paginator = Paginator(users, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'staff/admin/users.html', {
        'users': page_obj
    })


@login_required
@role_required('Admin', 'Manager')
def create_user(request):
    if request.method == 'POST':
        try:
            user = CustomUser.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password1'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                phone_number=request.POST.get('phone_number'),
                role=request.POST.get('role', 'CLIENT'),
                professional_role=request.POST.get('professional_role', 'none'),
                is_active='is_active' in request.POST
            )

            profile = Profile.objects.create(
                user=user,
                bonuses=request.POST.get('bonuses', 0)
            )

            messages.success(request, f'Пользователь {user.username} успешно создан!')
            return redirect('staff:users')

        except Exception as e:
            messages.error(request, f'Ошибка при создании пользователя: {str(e)}')

    return render(request, 'staff/admin/create_user.html', {
        'role_choices': CustomUser.ROLE_CHOICES,
        'professional_roles': CustomUser.PROFESSIONAL_ROLES
    })


# ------------------------------------------------------------
# Ниже идут view-функции для «Price Settings»
# ------------------------------------------------------------

@login_required
@role_required('Admin', 'Manager')
def price_settings(request):
    """
    Загружает все объекты из моделей цены и отдаёт их в шаблон для редактирования.
    Преобразовывает QuerySet в списки словарей, чтобы они были JSON-сериализуемы.
    """
    # Преобразуем каждый QuerySet в список словарей
    child_city_items = list(
        ChildCityItem.objects.all().values(
            'id', 'name',
            'weekday_before_17',
            'weekday_after_17_weekends',
            'description'
        )
    )
    arcade_machines_items = list(
        ArcadeMachineItem.objects.all().values(
            'id', 'name',
            'weekday_before_17',
            'weekday_after_17_weekends',
            'description'
        )
    )
    vr_arena_items = list(
        VRArenaItem.objects.all().values(
            'id', 'duration',
            'weekday_before_17',
            'weekday_after_17_weekends',
            'description'
        )
    )
    birthday_packages_items = list(
        BirthdayPackage.objects.all().values(
            'id', 'name',
            'price_mon_thu',
            'price_fri_sun',
            'extra_person',
            'description'
        )
    )
    vr_packages_items = list(
        VRPackage.objects.all().values(
            'id', 'name',
            'price_mon_thu',
            'price_fri_sun',
            'extra_person',
            'description'
        )
    )
    standard_packages_items = list(
        StandardPackage.objects.all().values(
            'id', 'name',
            'price_mon_thu',
            'price_fri_sun',
            'extra_person',
            'description'
        )
    )
    playstation_items = list(
        PlayStationSlot.objects.all().values(
            'id', 'duration',
            'weekday_before_17',
            'weekday_after_17_weekends',
            'description'
        )
    )
    vr_rides_items = list(
        VRRide.objects.all().values(
            'id', 'name',
            'weekday_before_17',
            'weekday_after_17_weekends',
            'description'
        )
    )

    context = {
        'child_city_items': child_city_items,
        'arcade_machines_items': arcade_machines_items,
        'vr_arena_items': vr_arena_items,
        'birthday_packages_items': birthday_packages_items,
        'vr_packages_items': vr_packages_items,
        'standard_packages_items': standard_packages_items,
        'playstation_items': playstation_items,
        'vr_rides_items': vr_rides_items,
    }
    return render(request, 'staff/admin/price_settings.html', context)


@login_required
@role_required('Admin', 'Manager')
def save_child_city_prices(request):
    """
    Обработка POST-запроса из вкладки 'Детский городок'.
    Если AJAX, возвращаем JSON с обновленным списком.
    """
    if request.method == 'POST':
        for item in ChildCityItem.objects.all():
            prefix = f'child_city_{item.id}_'
            before_17 = request.POST.get(prefix + 'before_17')
            after_17 = request.POST.get(prefix + 'after_17')
            desc = request.POST.get(prefix + 'desc', '').strip()

            try:
                item.weekday_before_17 = int(before_17)
            except (TypeError, ValueError):
                item.weekday_before_17 = 0
            try:
                item.weekday_after_17_weekends = int(after_17)
            except (TypeError, ValueError):
                item.weekday_after_17_weekends = 0
            item.description = desc
            item.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            updated = list(
                ChildCityItem.objects.all().values(
                    'id', 'name',
                    'weekday_before_17',
                    'weekday_after_17_weekends',
                    'description'
                )
            )
            return JsonResponse({'success': True, 'updated': updated})

        messages.success(request, 'Цены Детского городка обновлены.')
        return redirect(request.META.get('HTTP_REFERER', 'staff:price-settings'))

    return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def save_arcade_prices(request):
    """
    Обработка POST-запроса из вкладки 'Игровые автоматы (жетоны)'.
    Если AJAX, возвращаем JSON с обновленным списком.
    """
    if request.method == 'POST':
        for machine in ArcadeMachineItem.objects.all():
            prefix = f'arcade_{machine.id}_'
            before_17 = request.POST.get(prefix + 'before_17')
            after_17 = request.POST.get(prefix + 'after_17')
            desc = request.POST.get(prefix + 'desc', '').strip()

            try:
                machine.weekday_before_17 = int(before_17)
            except (TypeError, ValueError):
                machine.weekday_before_17 = 0
            try:
                machine.weekday_after_17_weekends = int(after_17)
            except (TypeError, ValueError):
                machine.weekday_after_17_weekends = 0
            machine.description = desc
            machine.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            updated = list(
                ArcadeMachineItem.objects.all().values(
                    'id', 'name',
                    'weekday_before_17',
                    'weekday_after_17_weekends',
                    'description'
                )
            )
            return JsonResponse({'success': True, 'updated': updated})

        messages.success(request, 'Цены Игровых автоматов обновлены.')
        return redirect(request.META.get('HTTP_REFERER', 'staff:price-settings'))

    return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def save_vr_arena_prices(request):
    """
    Обработка POST-запроса из вкладки 'VR-арена'.
    Если AJAX, возвращаем JSON с обновленным списком.
    """
    if request.method == 'POST':
        for session in VRArenaItem.objects.all():
            prefix = f'vr_arena_{session.id}_'
            before_17 = request.POST.get(prefix + 'before_17')
            after_17 = request.POST.get(prefix + 'after_17')
            desc = request.POST.get(prefix + 'desc', '').strip()

            try:
                session.weekday_before_17 = int(before_17)
            except (TypeError, ValueError):
                session.weekday_before_17 = 0
            try:
                session.weekday_after_17_weekends = int(after_17)
            except (TypeError, ValueError):
                session.weekday_after_17_weekends = 0
            session.description = desc
            session.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            updated = list(
                VRArenaItem.objects.all().values(
                    'id', 'duration',
                    'weekday_before_17',
                    'weekday_after_17_weekends',
                    'description'
                )
            )
            return JsonResponse({'success': True, 'updated': updated})

        messages.success(request, 'Цены VR-арены обновлены.')
        return redirect(request.META.get('HTTP_REFERER', 'staff:price-settings'))

    return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def save_birthday_packages(request):
    """
    Обработка POST-запроса из вкладки 'Пакеты ко Дню Рождения'.
    Если AJAX, возвращаем JSON с обновленным списком.
    """
    if request.method == 'POST':
        for pkg in BirthdayPackage.objects.all():
            prefix = f'birthday_pkg_{pkg.id}_'
            price_mon_thu = request.POST.get(prefix + 'price_mon_thu')
            price_fri_sun = request.POST.get(prefix + 'price_fri_sun')
            extra = request.POST.get(prefix + 'extra_person')
            desc = request.POST.get(prefix + 'desc', '').strip()

            try:
                pkg.price_mon_thu = int(price_mon_thu)
            except (TypeError, ValueError):
                pkg.price_mon_thu = 0
            try:
                pkg.price_fri_sun = int(price_fri_sun)
            except (TypeError, ValueError):
                pkg.price_fri_sun = 0
            try:
                pkg.extra_person = int(extra)
            except (TypeError, ValueError):
                pkg.extra_person = 0
            pkg.description = desc
            pkg.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            updated = list(
                BirthdayPackage.objects.all().values(
                    'id', 'name',
                    'price_mon_thu',
                    'price_fri_sun',
                    'extra_person',
                    'description'
                )
            )
            return JsonResponse({'success': True, 'updated': updated})

        messages.success(request, 'Коэффициенты и цены пакетов ДР обновлены.')
        return redirect(request.META.get('HTTP_REFERER', 'staff:price-settings'))

    return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def save_vr_packages(request):
    """
    Обработка POST-запроса из вкладки 'Пакеты VR'.
    Если AJAX, возвращаем JSON с обновленным списком.
    """
    if request.method == 'POST':
        for pkg in VRPackage.objects.all():
            prefix = f'vr_pkg_{pkg.id}_'
            price_mon_thu = request.POST.get(prefix + 'price_mon_thu')
            price_fri_sun = request.POST.get(prefix + 'price_fri_sun')
            extra = request.POST.get(prefix + 'extra_person')
            desc = request.POST.get(prefix + 'desc', '').strip()

            try:
                pkg.price_mon_thu = int(price_mon_thu)
            except (TypeError, ValueError):
                pkg.price_mon_thu = 0
            try:
                pkg.price_fri_sun = int(price_fri_sun)
            except (TypeError, ValueError):
                pkg.price_fri_sun = 0
            try:
                pkg.extra_person = int(extra)
            except (TypeError, ValueError):
                pkg.extra_person = 0
            pkg.description = desc
            pkg.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            updated = list(
                VRPackage.objects.all().values(
                    'id', 'name',
                    'price_mon_thu',
                    'price_fri_sun',
                    'extra_person',
                    'description'
                )
            )
            return JsonResponse({'success': True, 'updated': updated})

        messages.success(request, 'Цены пакетов VR обновлены.')
        return redirect(request.META.get('HTTP_REFERER', 'staff:price-settings'))

    return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def save_standard_packages(request):
    """
    Обработка POST-запроса из вкладки 'Обычные пакеты услуг'.
    Если AJAX, возвращаем JSON с обновленным списком.
    """
    if request.method == 'POST':
        for pkg in StandardPackage.objects.all():
            prefix = f'std_pkg_{pkg.id}_'
            price_mon_thu = request.POST.get(prefix + 'price_mon_thu')
            price_fri_sun = request.POST.get(prefix + 'price_fri_sun')
            extra = request.POST.get(prefix + 'extra_person')
            desc = request.POST.get(prefix + 'desc', '').strip()

            try:
                pkg.price_mon_thu = int(price_mon_thu)
            except (TypeError, ValueError):
                pkg.price_mon_thu = 0
            try:
                pkg.price_fri_sun = int(price_fri_sun)
            except (TypeError, ValueError):
                pkg.price_fri_sun = 0
            try:
                pkg.extra_person = int(extra)
            except (TypeError, ValueError):
                pkg.extra_person = 0
            pkg.description = desc
            pkg.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            updated = list(
                StandardPackage.objects.all().values(
                    'id', 'name',
                    'price_mon_thu',
                    'price_fri_sun',
                    'extra_person',
                    'description'
                )
            )
            return JsonResponse({'success': True, 'updated': updated})

        messages.success(request, 'Цены обычных пакетов обновлены.')
        return redirect(request.META.get('HTTP_REFERER', 'staff:price-settings'))

    return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def save_playstation_prices(request):
    """
    Обработка POST-запроса из вкладки 'Зона PlayStation'.
    Если AJAX, возвращаем JSON с обновленным списком.
    """
    if request.method == 'POST':
        for slot in PlayStationSlot.objects.all():
            prefix = f'ps_{slot.id}_'
            before_17 = request.POST.get(prefix + 'before_17')
            after_17 = request.POST.get(prefix + 'after_17')
            desc = request.POST.get(prefix + 'desc', '').strip()

            try:
                slot.weekday_before_17 = int(before_17)
            except (TypeError, ValueError):
                slot.weekday_before_17 = 0
            try:
                slot.weekday_after_17_weekends = int(after_17)
            except (TypeError, ValueError):
                slot.weekday_after_17_weekends = 0
            slot.description = desc
            slot.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            updated = list(
                PlayStationSlot.objects.all().values(
                    'id', 'duration',
                    'weekday_before_17',
                    'weekday_after_17_weekends',
                    'description'
                )
            )
            return JsonResponse({'success': True, 'updated': updated})

        messages.success(request, 'Цены зоны PlayStation обновлены.')
        return redirect(request.META.get('HTTP_REFERER', 'staff:price-settings'))

    return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def save_vr_rides(request):
    """
    Обработка POST-запроса из вкладки 'VR-аттракционы'.
    Если AJAX, возвращаем JSON с обновленным списком.
    """
    if request.method == 'POST':
        for ride in VRRide.objects.all():
            prefix = f'vr_ride_{ride.id}_'
            before_17 = request.POST.get(prefix + 'before_17')
            after_17 = request.POST.get(prefix + 'after_17')
            desc = request.POST.get(prefix + 'desc', '').strip()

            try:
                ride.weekday_before_17 = int(before_17)
            except (TypeError, ValueError):
                ride.weekday_before_17 = 0
            try:
                ride.weekday_after_17_weekends = int(after_17)
            except (TypeError, ValueError):
                ride.weekday_after_17_weekends = 0
            ride.description = desc
            ride.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            updated = list(
                VRRide.objects.all().values(
                    'id', 'name',
                    'weekday_before_17',
                    'weekday_after_17_weekends',
                    'description'
                )
            )
            return JsonResponse({'success': True, 'updated': updated})

        messages.success(request, 'Цены VR-аттракционов обновлены.')
        return redirect(request.META.get('HTTP_REFERER', 'staff:price-settings'))

    return redirect('staff:price-settings')


# --------------------------------------------
# Добавленные view-функции «Добавить/Удалить»
# --------------------------------------------

@login_required
@role_required('Admin', 'Manager')
def add_child_city_item(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        before_17 = request.POST.get('weekday_before_17', '').strip()
        after_17 = request.POST.get('weekday_after_17_weekends', '').strip()
        description = request.POST.get('description', '').strip()

        if name:
            try:
                weekday_before_17 = int(before_17) if before_17 else 0
            except ValueError:
                weekday_before_17 = 0

            try:
                weekday_after_17_weekends = int(after_17) if after_17 else 0
            except ValueError:
                weekday_after_17_weekends = 0

            item = ChildCityItem.objects.create(
                name=name,
                weekday_before_17=weekday_before_17,
                weekday_after_17_weekends=weekday_after_17_weekends,
                description=description
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                item_data = {
                    'id': item.id,
                    'name': item.name,
                    'weekday_before_17': item.weekday_before_17,
                    'weekday_after_17_weekends': item.weekday_after_17_weekends,
                    'description': item.description
                }
                return JsonResponse({'success': True, 'item': item_data})

            messages.success(request, 'Услуга «Детский городок» добавлена.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Название услуги обязательно!'}, status=400)
            messages.error(request, 'Название услуги обязательно!')

        return redirect('staff:price-settings')

    html = render_to_string('staff/common/partials/add_child_city_item_form.html', {}, request)
    return JsonResponse({'html': html})


@login_required
@role_required('Admin', 'Manager')
def delete_child_city_item(request, pk):
    try:
        item = get_object_or_404(ChildCityItem, pk=pk)
        item_name = item.name
        item.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Услуга «{item_name}» удалена.'
            })

        messages.success(request, f'Услуга «{item_name}» удалена.')
        return redirect('staff:price-settings')

    except Exception as e:
        error_msg = f'Ошибка удаления: {str(e)}'
        logger.error(error_msg)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)

        messages.error(request, error_msg)
        return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def delete_arcade_machine_item(request, pk):
    try:
        machine = get_object_or_404(ArcadeMachineItem, pk=pk)
        machine_name = machine.name
        machine.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Автомат «{machine_name}» удалён.'
            })

        messages.success(request, f'Автомат «{machine_name}» удалён.')
        return redirect('staff:price-settings')

    except Exception as e:
        error_msg = f'Ошибка удаления: {str(e)}'
        logger.error(error_msg)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)

        messages.error(request, error_msg)
        return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def delete_vr_arena_item(request, pk):
    try:
        session = get_object_or_404(VRArenaItem, pk=pk)
        session_duration = session.get_duration_display()
        session.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Сеанс {session_duration} удалён.'
            })

        messages.success(request, f'Сеанс {session_duration} удалён.')
        return redirect('staff:price-settings')

    except Exception as e:
        error_msg = f'Ошибка удаления: {str(e)}'
        logger.error(error_msg)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)

        messages.error(request, error_msg)
        return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def delete_birthday_package(request, pk):
    try:
        pkg = get_object_or_404(BirthdayPackage, pk=pk)
        pkg_name = pkg.name
        pkg.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Пакет «{pkg_name}» удалён.'
            })

        messages.success(request, f'Пакет «{pkg_name}» удалён.')
        return redirect('staff:price-settings')

    except Exception as e:
        error_msg = f'Ошибка удаления: {str(e)}'
        logger.error(error_msg)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)

        messages.error(request, error_msg)
        return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def delete_vr_package(request, pk):
    try:
        pkg = get_object_or_404(VRPackage, pk=pk)
        pkg_name = pkg.name
        pkg.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Пакет «{pkg_name}» удалён.'
            })

        messages.success(request, f'Пакет «{pkg_name}» удалён.')
        return redirect('staff:price-settings')

    except Exception as e:
        error_msg = f'Ошибка удаления: {str(e)}'
        logger.error(error_msg)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)

        messages.error(request, error_msg)
        return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def delete_standard_package(request, pk):
    try:
        pkg = get_object_or_404(StandardPackage, pk=pk)
        pkg_name = pkg.name
        pkg.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Пакет «{pkg_name}» удалён.'
            })

        messages.success(request, f'Пакет «{pkg_name}» удалён.')
        return redirect('staff:price-settings')

    except Exception as e:
        error_msg = f'Ошибка удаления: {str(e)}'
        logger.error(error_msg)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)

        messages.error(request, error_msg)
        return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def delete_playstation_slot(request, pk):
    try:
        slot = get_object_or_404(PlayStationSlot, pk=pk)
        slot_duration = slot.get_duration_display()
        slot.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Слот {slot_duration} удалён.'
            })

        messages.success(request, f'Слот {slot_duration} удалён.')
        return redirect('staff:price-settings')

    except Exception as e:
        error_msg = f'Ошибка удаления: {str(e)}'
        logger.error(error_msg)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)

        messages.error(request, error_msg)
        return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def delete_vr_ride(request, pk):
    try:
        ride = get_object_or_404(VRRide, pk=pk)
        ride_name = ride.name
        ride.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Аттракцион «{ride_name}» удалён.'
            })

        messages.success(request, f'Аттракцион «{ride_name}» удалён.')
        return redirect('staff:price-settings')

    except Exception as e:
        error_msg = f'Ошибка удаления: {str(e)}'
        logger.error(error_msg)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)

        messages.error(request, error_msg)
        return redirect('staff:price-settings')


@login_required
@role_required('Admin', 'Manager')
def add_arcade_machine_item(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        before_17 = request.POST.get('weekday_before_17', '').strip()
        after_17 = request.POST.get('weekday_after_17_weekends', '').strip()
        description = request.POST.get('description', '').strip()

        if name:
            try:
                weekday_before_17 = int(before_17) if before_17 else 0
            except ValueError:
                weekday_before_17 = 0

            try:
                weekday_after_17_weekends = int(after_17) if after_17 else 0
            except ValueError:
                weekday_after_17_weekends = 0

            machine = ArcadeMachineItem.objects.create(
                name=name,
                weekday_before_17=weekday_before_17,
                weekday_after_17_weekends=weekday_after_17_weekends,
                description=description
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                machine_data = {
                    'id': machine.id,
                    'name': machine.name,
                    'weekday_before_17': machine.weekday_before_17,
                    'weekday_after_17_weekends': machine.weekday_after_17_weekends,
                    'description': machine.description
                }
                return JsonResponse({'success': True, 'item': machine_data})

            messages.success(request, 'Игровой автомат добавлен.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Название автомата обязательно!'}, status=400)
            messages.error(request, 'Название автомата обязательно!')

        return redirect('staff:price-settings')

    html = render_to_string('staff/common/partials/add_arcade_machine_item_form.html', {}, request)
    return JsonResponse({'html': html})


@login_required
@role_required('Admin', 'Manager')
def add_vr_arena_item(request):
    if request.method == 'POST':
        duration = request.POST.get('duration', '').strip()
        before_17 = request.POST.get('weekday_before_17', '').strip()
        after_17 = request.POST.get('weekday_after_17_weekends', '').strip()
        description = request.POST.get('description', '').strip()

        if duration:
            try:
                weekday_before_17 = int(before_17) if before_17 else 0
            except ValueError:
                weekday_before_17 = 0

            try:
                weekday_after_17_weekends = int(after_17) if after_17 else 0
            except ValueError:
                weekday_after_17_weekends = 0

            session = VRArenaItem.objects.create(
                duration=int(duration),
                weekday_before_17=weekday_before_17,
                weekday_after_17_weekends=weekday_after_17_weekends,
                description=description
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                session_data = {
                    'id': session.id,
                    'duration': session.duration,
                    'weekday_before_17': session.weekday_before_17,
                    'weekday_after_17_weekends': session.weekday_after_17_weekends,
                    'description': session.description
                }
                return JsonResponse({'success': True, 'item': session_data})

            messages.success(request, 'Сеанс VR-арены добавлен.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Продолжительность сеанса обязательна!'}, status=400)
            messages.error(request, 'Продолжительность сеанса обязательна!')

        return redirect('staff:price-settings')

    html = render_to_string('staff/common/partials/add_vr_arena_item_form.html', {}, request)
    return JsonResponse({'html': html})


@login_required
@role_required('Admin', 'Manager')
def add_birthday_package(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        price_mon_thu = request.POST.get('price_mon_thu', '').strip()
        price_fri_sun = request.POST.get('price_fri_sun', '').strip()
        extra_person = request.POST.get('extra_person', '').strip()
        description = request.POST.get('description', '').strip()

        if name:
            try:
                mon_thu_price = int(price_mon_thu) if price_mon_thu else 0
            except ValueError:
                mon_thu_price = 0

            try:
                fri_sun_price = int(price_fri_sun) if price_fri_sun else 0
            except ValueError:
                fri_sun_price = 0

            try:
                extra_price = int(extra_person) if extra_person else 0
            except ValueError:
                extra_price = 0

            pkg = BirthdayPackage.objects.create(
                name=name,
                price_mon_thu=mon_thu_price,
                price_fri_sun=fri_sun_price,
                extra_person=extra_price,
                description=description
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                pkg_data = {
                    'id': pkg.id,
                    'name': pkg.name,
                    'price_mon_thu': pkg.price_mon_thu,
                    'price_fri_sun': pkg.price_fri_sun,
                    'extra_person': pkg.extra_person,
                    'description': pkg.description
                }
                return JsonResponse({'success': True, 'item': pkg_data})

            messages.success(request, 'Пакет ко Дню Рождения добавлен.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Название пакета обязательно!'}, status=400)
            messages.error(request, 'Название пакета обязательно!')

        return redirect('staff:price-settings')

    html = render_to_string('staff/common/partials/add_birthday_package_form.html', {}, request)
    return JsonResponse({'html': html})


@login_required
@role_required('Admin', 'Manager')
def add_vr_package(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        price_mon_thu = request.POST.get('price_mon_thu', '').strip()
        price_fri_sun = request.POST.get('price_fri_sun', '').strip()
        extra_person = request.POST.get('extra_person', '').strip()
        description = request.POST.get('description', '').strip()

        if name:
            try:
                mon_thu_price = int(price_mon_thu) if price_mon_thu else 0
            except ValueError:
                mon_thu_price = 0

            try:
                fri_sun_price = int(price_fri_sun) if price_fri_sun else 0
            except ValueError:
                fri_sun_price = 0

            try:
                extra_price = int(extra_person) if extra_person else 0
            except ValueError:
                extra_price = 0

            pkg = VRPackage.objects.create(
                name=name,
                price_mon_thu=mon_thu_price,
                price_fri_sun=fri_sun_price,
                extra_person=extra_price,
                description=description
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                pkg_data = {
                    'id': pkg.id,
                    'name': pkg.name,
                    'price_mon_thu': pkg.price_mon_thu,
                    'price_fri_sun': pkg.price_fri_sun,
                    'extra_person': pkg.extra_person,
                    'description': pkg.description
                }
                return JsonResponse({'success': True, 'item': pkg_data})

            messages.success(request, 'VR пакет добавлен.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Название пакета обязательно!'}, status=400)
            messages.error(request, 'Название пакета обязательно!')

        return redirect('staff:price-settings')

    html = render_to_string('staff/common/partials/add_vr_package_form.html', {}, request)
    return JsonResponse({'html': html})


@login_required
@role_required('Admin', 'Manager')
def add_standard_package(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        price_mon_thu = request.POST.get('price_mon_thu', '').strip()
        price_fri_sun = request.POST.get('price_fri_sun', '').strip()
        extra_person = request.POST.get('extra_person', '').strip()
        description = request.POST.get('description', '').strip()

        if name:
            try:
                mon_thu_price = int(price_mon_thu) if price_mon_thu else 0
            except ValueError:
                mon_thu_price = 0

            try:
                fri_sun_price = int(price_fri_sun) if price_fri_sun else 0
            except ValueError:
                fri_sun_price = 0

            try:
                extra_price = int(extra_person) if extra_person else 0
            except ValueError:
                extra_price = 0

            pkg = StandardPackage.objects.create(
                name=name,
                price_mon_thu=mon_thu_price,
                price_fri_sun=fri_sun_price,
                extra_person=extra_price,
                description=description
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                pkg_data = {
                    'id': pkg.id,
                    'name': pkg.name,
                    'price_mon_thu': pkg.price_mon_thu,
                    'price_fri_sun': pkg.price_fri_sun,
                    'extra_person': pkg.extra_person,
                    'description': pkg.description
                }
                return JsonResponse({'success': True, 'item': pkg_data})

            messages.success(request, 'Стандартный пакет добавлен.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Название пакета обязательно!'}, status=400)
            messages.error(request, 'Название пакета обязательно!')

        return redirect('staff:price-settings')

    html = render_to_string('staff/common/partials/add_standard_package_form.html', {}, request)
    return JsonResponse({'html': html})


@login_required
@role_required('Admin', 'Manager')
def add_playstation_slot(request):
    if request.method == 'POST':
        duration = request.POST.get('duration', '').strip()
        before_17 = request.POST.get('weekday_before_17', '').strip()
        after_17 = request.POST.get('weekday_after_17_weekends', '').strip()
        description = request.POST.get('description', '').strip()

        # проверяем, что duration не пустая строка
        if not duration:
            # если AJAX-запрос — вернем JSON-ошибку
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'Продолжительность слота обязательна!'},
                    status=400
                )
            # иначе редиректим с сообщением
            messages.error(request, 'Продолжительность слота обязательна!')
            return redirect('staff:price-settings')

        # пытаемся преобразовать duration в int
        try:
            duration_int = int(duration)
        except ValueError:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': 'Неверный формат длительности (должно быть число).'},
                    status=400
                )
            messages.error(request, 'Неверный формат длительности (должно быть число).')
            return redirect('staff:price-settings')

        # разбираем цены (если не число — делаем 0)
        try:
            weekday_before_17 = int(before_17) if before_17 else 0
        except ValueError:
            weekday_before_17 = 0

        try:
            weekday_after_17_weekends = int(after_17) if after_17 else 0
        except ValueError:
            weekday_after_17_weekends = 0

        # создаем запись
        slot = PlayStationSlot.objects.create(
            duration=duration_int,
            weekday_before_17=weekday_before_17,
            weekday_after_17_weekends=weekday_after_17_weekends,
            description=description
        )

        # если AJAX — возвращаем весь JSON, который ждет JS
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            slot_data = {
                'id': slot.id,
                # вместо “duration” отдаем “duration_display”, чтобы клиент мог сразу показать текст
                'duration_display': slot.get_duration_display(),
                'weekday_before_17': slot.weekday_before_17,
                'weekday_after_17_weekends': slot.weekday_after_17_weekends,
                'description': slot.description,
                # ссылка для удаления (JS берет data-url из item.delete_url)
                'delete_url': reverse('staff:delete_playstation_slot', args=[slot.id]),
            }
            return JsonResponse({
                'success': True,
                'category': 'playstation',      # обязательно указываем, к какой категории относится
                'item': slot_data
            })

        # если это не AJAX, просто редирект с сообщением
        messages.success(request, 'Слот PlayStation добавлен.')
        return redirect('staff:price-settings')

    # на GET возвращаем JSON с HTML-формой (не используем сейчас, но оставляем на всякий)
    html = render_to_string('staff/common/partials/add_playstation_slot_form.html', {}, request)
    return JsonResponse({'html': html})


@login_required
@role_required('Admin', 'Manager')
def add_vr_ride(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        before_17 = request.POST.get('weekday_before_17', '').strip()
        after_17 = request.POST.get('weekday_after_17_weekends', '').strip()
        description = request.POST.get('description', '').strip()

        if name:
            try:
                weekday_before_17 = int(before_17) if before_17 else 0
            except ValueError:
                weekday_before_17 = 0

            try:
                weekday_after_17_weekends = int(after_17) if after_17 else 0
            except ValueError:
                weekday_after_17_weekends = 0

            ride = VRRide.objects.create(
                name=name,
                weekday_before_17=weekday_before_17,
                weekday_after_17_weekends=weekday_after_17_weekends,
                description=description
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                ride_data = {
                    'id': ride.id,
                    'name': ride.name,
                    'weekday_before_17': ride.weekday_before_17,
                    'weekday_after_17_weekends': ride.weekday_after_17_weekends,
                    'description': ride.description
                }
                return JsonResponse({'success': True, 'item': ride_data})

            messages.success(request, 'VR аттракцион добавлен.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Название аттракциона обязательно!'}, status=400)
            messages.error(request, 'Название аттракциона обязательно!')

        return redirect('staff:price-settings')

    html = render_to_string('staff/common/partials/add_vr_ride_form.html', {}, request)
    return JsonResponse({'html': html})
