# staff/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard(request):
    if request.user.role == 'admin':
        return render(request, 'staff/admin_dashboard.html')
    return redirect('index')  # Перенаправление, если роль не подходит

@login_required
def manager_dashboard(request):
    if request.user.role == 'manager':
        return render(request, 'staff/manager_dashboard.html')
    return redirect('index')  # Перенаправление, если роль не подходит

@login_required
def employee_dashboard(request):
    if request.user.role == 'employee':
        return render(request, 'staff/employee_dashboard.html')
    return redirect('index')  # Перенаправление, если роль не подходит
