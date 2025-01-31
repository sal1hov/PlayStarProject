# main/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from main.models import CustomUser  # Импортируем кастомную модель пользователя
from bookings.models import Booking  # Предполагается, что модель бронирований находится в приложении bookings
from bookings.forms import BookingForm  # Импортируем форму для бронирований

def role_required(*group_names):
    """Декоратор для проверки групп."""
    def in_groups(user):
        if user.is_authenticated:
            if bool(user.groups.filter(name__in=group_names)) or user.is_superuser:
                return True
        return False
    return user_passes_test(in_groups)

@login_required
def profile_view(request):
    user = request.user
    bookings = Booking.objects.filter(user=user).order_by('-booking_date')  # Получаем все бронирования текущего пользователя
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = user
            booking.status = 'pending'  # Устанавливаем статус "ожидает утверждения"
            booking.save()
            messages.success(request, 'Бронирование успешно создано.')
            return redirect('profile')
    else:
        form = BookingForm()
    return render(request, 'accounts/profile.html', {'user': user, 'bookings': bookings, 'form': form})

@login_required
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)  # Проверяем, что бронирование принадлежит текущему пользователю
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Бронирование успешно отредактировано.')
            return redirect('profile')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'bookings/edit_booking.html', {'form': form, 'booking': booking})

@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)  # Проверяем, что бронирование принадлежит текущему пользователю
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
            print(f"User groups: {user.groups.values_list('name', flat=True)}")  # Отладочное сообщение
            print(f"Is superuser: {user.is_superuser}")  # Отладочное сообщение
            # Перенаправление в зависимости от роли пользователя
            if user.groups.filter(name='Admin').exists() or user.is_superuser:
                print("Redirecting to admin dashboard")  # Отладочное сообщение
                return redirect('admin_dashboard')
            elif user.groups.filter(name='Manager').exists():
                print("Redirecting to manager dashboard")  # Отладочное сообщение
                return redirect('manager_dashboard')
            elif user.groups.filter(name='Staff').exists():
                print("Redirecting to employee dashboard")  # Отладочное сообщение
                return redirect('employee_dashboard')  # Перенаправление для сотрудников
            else:
                print("Redirecting to profile")  # Отладочное сообщение
                return redirect('profile')  # Для клиентов и других ролей
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()
    return render(request, 'main/registration/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Вы успешно зарегистрированы!')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
@user_passes_test(role_required('Admin'))
def admin_dashboard(request):
    if request.user.groups.filter(name='Admin').exists() or request.user.is_superuser:
        users = CustomUser.objects.all()  # Используем кастомную модель пользователя
        paginator = Paginator(users, 5)  # Показывать по 5 пользователей на странице
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        bookings = Booking.objects.all()

        return render(request, 'staff/admin_dashboard.html', {'users': page_obj, 'bookings': bookings})
    return redirect('index')  # Перенаправление, если роль не подходит

@login_required
@user_passes_test(role_required('Manager', 'Admin'))
def manager_dashboard(request):
    if request.user.groups.filter(name='Manager').exists() or request.user.groups.filter(name='Admin').exists() or request.user.is_superuser:
        bookings = Booking.objects.all()
        return render(request, 'staff/manager_dashboard.html', {'bookings': bookings})
    return redirect('index')  # Перенаправление, если роль не подходит

@login_required
@user_passes_test(role_required('Staff'))
def employee_dashboard(request):
    if request.user.groups.filter(name='Staff').exists():
        # Здесь можно добавить логику для панели сотрудника
        return render(request, 'staff/employee_dashboard.html')
    return redirect('index')  # Перенаправление, если роль не подходит

def logout_view(request):
    logout(request)
    return redirect('index')  # Перенаправление на главную страницу после выхода