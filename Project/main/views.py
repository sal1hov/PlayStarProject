# main/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group

def role_required(*group_names):
    """Декоратор для проверки групп."""
    def in_groups(user):
        if user.is_authenticated:
            if bool(user.groups.filter(name__in=group_names)) or user.is_superuser:
                return True
        return False
    return user_passes_test(in_groups)

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
                print("Redirecting to index")  # Отладочное сообщение
                return redirect('index')  # Для клиентов и других ролей
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
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

# Панели управления
@login_required
@role_required('Admin')
def admin_dashboard(request):
    return render(request, 'staff/admin_dashboard.html')

@login_required
@role_required('Manager', 'Admin')
def manager_dashboard(request):
    return render(request, 'staff/manager_dashboard.html')

@login_required
@role_required('Staff')
def employee_dashboard(request):
    return render(request, 'staff/employee_dashboard.html')