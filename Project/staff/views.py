# staff/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group

@login_required
def admin_dashboard(request):
    if request.user.groups.filter(name='Admin').exists() or request.user.is_superuser:
        return render(request, 'staff/admin_dashboard.html')
    return redirect('index')  # Перенаправление, если роль не подходит

@login_required
def manager_dashboard(request):
    if request.user.groups.filter(name='Manager').exists() or request.user.groups.filter(name='Admin').exists() or request.user.is_superuser:
        return render(request, 'staff/manager_dashboard.html')
    return redirect('index')  # Перенаправление, если роль не подходит

@login_required
def employee_dashboard(request):
    if request.user.groups.filter(name='Staff').exists():
        return render(request, 'staff/employee_dashboard.html')
    return redirect('index')  # Перенаправление, если роль не подходит