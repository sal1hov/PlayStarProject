from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

def role_required(*roles):
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if request.user.role in roles:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Доступ запрещен")
        return wrapped_view
    return decorator

@login_required
@role_required('client')
def client_dashboard(request):
    return render(request, 'bookings/client_dashboard.html')

@login_required
@role_required('employee')
def employee_dashboard(request):
    return render(request, 'bookings/employee_dashboard.html')

@login_required
@role_required('manager')
def manager_dashboard(request):
    return render(request, 'bookings/manager_dashboard.html')

@login_required
@role_required('admin')
def admin_dashboard(request):
    return render(request, 'bookings/admin_dashboard.html')