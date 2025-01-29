# staff/views.py
from django.shortcuts import render

def employee_dashboard(request):
    return render(request, 'staff/employee_dashboard.html')

def manager_dashboard(request):
    return render(request, 'staff/manager_dashboard.html')

def admin_dashboard(request):
    return render(request, 'staff/admin_dashboard.html')
