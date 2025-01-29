from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

def index(request):
    return render(request, 'main/index.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Убираем автоматический вход после регистрации
            # login(request, user)  # Закомментируйте эту строку
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('login')  # Перенаправляем на страницу входа
        else:
            messages.error(request, 'Что-то пошло не так. Проверьте введённые данные.')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def admin_dashboard(request):
    if request.user.staffprofile.role == 'admin':
        return redirect('/admin/')  # Перенаправить в стандартную админку Django
    else:
        return HttpResponseForbidden("У вас нет прав для доступа к этой странице.")

@login_required
def manager_dashboard(request):
    if request.user.staffprofile.role == 'manager':
        return render(request, 'staff/manager_dashboard.html')
    else:
        return HttpResponseForbidden("У вас нет прав для доступа к этой странице.")

@login_required
def employee_dashboard(request):
    if request.user.staffprofile.role == 'employee':
        return render(request, 'staff/employee_dashboard.html')
    else:
        return HttpResponseForbidden("У вас нет прав для доступа к этой странице.")
