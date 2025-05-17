import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from main.models import CustomUser, Profile, Child
from bookings.models import Booking
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Avg, F
from django.db.models.functions import TruncMonth, TruncDay
from django.template.loader import render_to_string
from .models import Event
from .forms import EventForm
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Shift, ShiftRequest
from .forms import ShiftRequestForm
from django.contrib.auth import update_session_auth_hash


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

    return render(request, 'staff/edit_user.html', {
        'user': user_to_edit,
        'profile': profile,
        'children': children,
        'role_choices': CustomUser.ROLE_CHOICES
    })

@login_required
@role_required('Admin', 'Manager')
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(CustomUser, id=user_id)
    user_to_delete.delete()
    messages.success(request, 'Пользователь успешно удален.')
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
    return render(request, 'staff/employee_dashboard.html')

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
                return JsonResponse({'error': 'Неверный формат даты. Используйте ДД.ММ.ГГ'}, status=400)

            bookings = Booking.objects.filter(
                booking_date__gte=start_date,
                booking_date__lte=end_date
            )
            users = CustomUser.objects.filter(
                date_joined__gte=start_date,
                date_joined__lte=end_date
            )
        else:
            bookings = Booking.objects.all()
            users = CustomUser.objects.all()

        users_by_month = users.annotate(
            month=TruncMonth('date_joined')
        ).values('month').annotate(count=Count('id')).order_by('month')
        users_by_month = list(users_by_month)
        for item in users_by_month:
            if item['month']:
                item['month'] = item['month'].strftime('%Y-%m')

        bookings_by_status = bookings.values('status').annotate(count=Count('id')).order_by('status')
        status_translation = {
            'pending': 'На модерации',
            'approved': 'Подтверждено',
            'rejected': 'Отклонено',
            'completed': 'Завершено'
        }
        for item in bookings_by_status:
            item['status'] = status_translation.get(item['status'], item['status'])

        online_bookings_count = 0
        total_earnings = bookings.aggregate(total=Sum('paid_amount'))['total'] or 0

        earnings_by_month = bookings.annotate(
            month=TruncMonth('booking_date')
        ).values('month').annotate(total=Sum('paid_amount')).order_by('month')
        earnings_by_month = list(earnings_by_month)
        for item in earnings_by_month:
            if item['month']:
                item['month'] = item['month'].strftime('%Y-%m')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'users_by_month': users_by_month,
                'bookings_by_status': list(bookings_by_status),
                'online_bookings_count': online_bookings_count,
                'total_earnings': total_earnings,
                'earnings_by_month': earnings_by_month,
            })

        return render(request, 'staff/admin/statistics.html', {
            'users_by_month': users_by_month,
            'bookings_by_status': list(bookings_by_status),
            'online_bookings_count': online_bookings_count,
            'total_earnings': total_earnings,
            'earnings_by_month': earnings_by_month,
        })
    except Exception as e:
        logger.error(f"Ошибка в statistics_view: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Произошла ошибка на сервере'}, status=500)
        else:
            raise

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

    return render(request, 'staff/events.html', {
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
                return redirect('staff:events')
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
@role_required('Admin', 'Manager')
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
        html = render_to_string('staff/partials/view_booking.html',
                               {'booking': booking},
                               request=request)
        return JsonResponse({'html': html})
    return JsonResponse({'error': 'This endpoint is only accessible via AJAX.'}, status=400)

@login_required
@role_required('Admin', 'Manager')
def income_management(request):
    try:
        total_income = Booking.objects.aggregate(
            total=Sum(F('prepayment_amount') + F('paid_amount'))
        )['total'] or Decimal('0.00')

        thirty_days_ago = timezone.now() - timedelta(days=30)
        average_income = Booking.objects.filter(
            booking_date__gte=thirty_days_ago
        ).aggregate(
            avg=Avg(F('prepayment_amount') + F('paid_amount'))
        )['avg'] or Decimal('0.00')

        total_prepayments = Booking.objects.filter(
            prepayment=True
        ).aggregate(
            total=Sum('prepayment_amount')
        )['total'] or Decimal('0.00')

        earnings_by_month = Booking.objects.annotate(
            month=TruncMonth('booking_date')
        ).values('month').annotate(
            total=Sum(F('prepayment_amount') + F('paid_amount'))
        ).order_by('month')

        return render(request, 'staff/income_management.html', {
            'total_income': total_income,
            'average_income': average_income,
            'total_prepayments': total_prepayments,
            'earnings_by_month': earnings_by_month,
            'bookings': Booking.objects.all().order_by('-booking_date')
        })
    except Exception as e:
        logger.error(f"Ошибка в income_management: {e}")
        return render(request, 'staff/admin/income_management.html', {
            'total_income': Decimal('0.00'),
            'average_income': Decimal('0.00'),
            'total_prepayments': Decimal('0.00'),
            'earnings_by_month': [],
            'bookings': []
        })

@csrf_exempt
@login_required
@role_required('Admin', 'Manager')
def add_income(request):
    if request.method == 'POST':
        try:
            booking_id = request.POST.get('booking_id')
            amount = request.POST.get('amount')

            if not booking_id or not amount:
                return JsonResponse({'success': False, 'error': 'Необходимо указать ID бронирования и сумму.'})

            try:
                amount_decimal = Decimal(amount)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Сумма должна быть числом.'})

            booking = Booking.objects.get(id=booking_id)
            booking.amount += amount_decimal
            booking.save()

            return JsonResponse({'success': True, 'message': 'Доход успешно добавлен.'})
        except Booking.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Бронирование не найдено.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Недопустимый метод запроса.'})

@csrf_exempt
@login_required
def edit_income_and_prepayment(request):
    if request.method == 'POST':
        try:
            booking = Booking.objects.get(id=request.POST.get('booking_id'))
            is_prepayment = request.POST.get('is_prepayment') == 'on'

            booking.prepayment = is_prepayment
            paid_amount = Decimal(request.POST.get('paid_amount', 0))

            if is_prepayment:
                booking.paid_amount = max(paid_amount, Decimal('0'))
            else:
                booking.paid_amount = paid_amount

            booking.save()

            total_prepayments = Booking.objects.filter(prepayment=True).aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')

            return JsonResponse({
                'success': True,
                'new_paid_amount': float(booking.paid_amount),
                'new_prepayment': booking.prepayment,
                'total_prepayments': float(total_prepayments)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

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
                booking_date__date__gte=start_date,
                booking_date__date__lte=end_date
            )

        total_income = bookings.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
        avg_income = bookings.aggregate(avg=Avg('paid_amount'))['avg'] or Decimal('0.00')
        total_prepayments = bookings.filter(prepayment=True).aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
        total_earnings = bookings.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')

        earnings_by_month = bookings.annotate(
            month=TruncMonth('booking_date')
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

        bookings_data = list(bookings.order_by('-booking_date').values(
            'id',
            'event_name',
            'booking_date',
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

class ShiftListView(ListView):
    model = Shift
    template_name = 'staff/shift_list.html'
    context_object_name = 'shifts'
    paginate_by = 10

    def get_queryset(self):
        return Shift.objects.filter(date__gte=timezone.now().date()).order_by('date')

class MyShiftRequestsView(ListView):
    model = ShiftRequest
    template_name = 'staff/my_shift_requests.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return ShiftRequest.objects.filter(employee=self.request.user).order_by('-created_at')

class CreateShiftRequestView(CreateView):
    model = ShiftRequest
    form_class = ShiftRequestForm
    template_name = 'staff/shift_request_form.html'
    success_url = reverse_lazy('staff:my-shift-requests')

    def form_valid(self, form):
        form.instance.employee = self.request.user
        return super().form_valid(form)

class AdminShiftApprovalView(ListView):
    model = ShiftRequest
    template_name = 'staff/admin_shift_approval.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        return ShiftRequest.objects.filter(status='pending').order_by('shift__date')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('staff:employee-dashboard')
        return super().dispatch(request, *args, **kwargs)

@login_required
def approve_shift_request(request, pk):
    shift_request = get_object_or_404(ShiftRequest, pk=pk)
    if request.user.is_staff:
        shift_request.status = 'approved'
        shift_request.save()
        messages.success(request, 'Заявка утверждена')
    return redirect('staff:admin_shift_approval')

@login_required
def reject_shift_request(request, pk):
    shift_request = get_object_or_404(ShiftRequest, pk=pk)
    if request.user.is_staff:
        shift_request.status = 'rejected'
        shift_request.save()
        messages.success(request, 'Заявка отклонена')
    return redirect('staff:admin_shift_approval')

@login_required
@role_required('Admin', 'Manager')
def shift_request_details(request, pk):
    shift_request = get_object_or_404(ShiftRequest, pk=pk)
    return render(request, 'staff/partials/shift_request_details.html', {
        'request': shift_request
    })

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

    return render(request, 'staff/manage_user_children.html', {
        'user': user,
        'profile': profile,
        'children': children
    })