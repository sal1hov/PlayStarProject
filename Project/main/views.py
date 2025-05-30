from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from main.models import CustomUser
from bookings.models import Booking
from bookings.forms import BookingForm
from django.shortcuts import render
from staff.models import Event
from django.core.paginator import Paginator
import logging

logger = logging.getLogger(__name__)


def role_required(*group_names):
    def in_groups(user):
        if user.is_authenticated:
            if bool(user.groups.filter(name__in=group_names)) or user.is_superuser:
                return True
        return False

    return user_passes_test(in_groups)


@login_required
def profile_view(request):
    user = request.user
    bookings = Booking.objects.filter(user=user).order_by('-event_date')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = user
            booking.status = 'pending'
            booking.save()
            messages.success(request, 'Бронирование успешно создано.')
            return redirect('profile')
    else:
        form = BookingForm()

    return render(request, 'accounts/profile.html', {
        'user': user,
        'bookings': bookings,
        'form': form
    })


@login_required
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Бронирование успешно отредактировано.')
            return redirect('profile')
    else:
        form = BookingForm(instance=booking)

    return render(request, 'bookings/edit_booking.html', {
        'form': form,
        'booking': booking
    })


@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    booking.delete()
    messages.success(request, 'Бронирование успешно удалено.')
    return redirect('profile')


def index(request):
    return render(request, 'main/index.html')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Вы успешно вошли в систему.')

            # Перенаправление в зависимости от роли
            if user.groups.filter(name='Admin').exists() or user.is_superuser:
                return redirect('admin_dashboard')
            elif user.groups.filter(name='Manager').exists():
                return redirect('manager_dashboard')
            elif user.groups.filter(name='Staff').exists():
                return redirect('employee_dashboard')
            else:
                return redirect('profile')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()

    return render(request, 'main/registration/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, 'Вы успешно зарегистрированы!')
                return redirect('login')
            except Exception as e:
                logger.error(f"Ошибка при регистрации: {str(e)}")
                messages.error(request, 'Произошла ошибка при регистрации. Пожалуйста, попробуйте снова.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Ошибка в поле '{form[field].label}': {error}")
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
@user_passes_test(role_required('Admin'))
def admin_dashboard(request):
    users = CustomUser.objects.all()
    paginator = Paginator(users, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    bookings = Booking.objects.all()

    return render(request, 'staff/admin_dashboard.html', {
        'users': page_obj,
        'bookings': bookings
    })


@login_required
@user_passes_test(role_required('Manager', 'Admin'))
def manager_dashboard(request):
    bookings = Booking.objects.all()
    return render(request, 'staff/manager_dashboard.html', {'bookings': bookings})


@login_required
@user_passes_test(role_required('Staff'))
def employee_dashboard(request):
    return render(request, 'staff/employee_dashboard.html')


def logout_view(request):
    logout(request)
    return redirect('index')


def events_list(request):
    events = Event.objects.filter(moderation_status='approved').order_by('date')
    return render(request, 'main/events.html', {'events': events})