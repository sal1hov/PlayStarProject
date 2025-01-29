# core/views.py
from django.shortcuts import redirect

def get_user_role_redirect(user):
    if user.role == 'admin':
        return '/staff/admin-dashboard/'
    elif user.role == 'manager':
        return '/staff/manager-dashboard/'
    elif user.role == 'employee':
        return '/staff/employee-dashboard/'
    return '/'
