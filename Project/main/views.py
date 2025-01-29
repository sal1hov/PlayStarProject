# main/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, 'main/index.html')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Вы успешно вошли в систему.')

            # Перенаправление в зависимости от роли пользователя
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'staff':
                return redirect('employee_dashboard')
            elif user.role == 'client':
                return redirect('index')
            else:
                return redirect('index')
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
    return render(request, 'main/registration/register.html', {'form': form})


# Панели управления
@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('index')
    return HttpResponse("Административная панель")


@login_required
def manager_dashboard(request):
    if request.user.role != 'admin' and request.user.role != 'manager':
        return redirect('index')
    return HttpResponse("Панель менеджера")


@login_required
def employee_dashboard(request):
    if request.user.role != 'staff':
        return redirect('index')
    return HttpResponse("Панель сотрудника")
