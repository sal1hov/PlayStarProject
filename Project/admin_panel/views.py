from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard(request):
    if request.user.role == 'admin':
        return render(request, 'admin_panel/admin_dashboard.html')
    return HttpResponseForbidden("Доступ запрещен")