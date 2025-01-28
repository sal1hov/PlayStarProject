from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import StaffProfile

# Декораторы для проверки ролей
def employee_required(view_func):
    return user_passes_test(lambda u: hasattr(u, 'staffprofile') and u.staffprofile.is_employee())(view_func)

def manager_required(view_func):
    return user_passes_test(lambda u: hasattr(u, 'staffprofile') and u.staffprofile.is_manager())(view_func)

def admin_required(view_func):
    return user_passes_test(lambda u: hasattr(u, 'staffprofile') and u.staffprofile.is_admin())(view_func)

@login_required
@employee_required
def employee_dashboard(request):
    return render(request, 'staff/employee_dashboard.html')

@login_required
@manager_required
def manager_dashboard(request):
    return render(request, 'staff/manager_dashboard.html')

@login_required
@admin_required
def admin_dashboard(request):
    return render(request, 'staff/admin_dashboard.html', {
        'users': User.objects.all()  # Пример: список всех пользователей для администратора
    })