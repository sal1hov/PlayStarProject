from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from core.views import get_user_role_redirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserUpdateForm, ProfileUpdateForm, ChildForm, EmailChangeForm, CustomPasswordChangeForm
from main.models import Profile, Child
from bookings.models import Booking
from bookings.forms import BookingForm
from staff.models import Event  # Добавляем импорт модели Event
from main.models import Child
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST, require_http_methods


@login_required
def profile(request):
    user = request.user
    Profile.objects.get_or_create(user=user)

    context = {
        'user': user,
        'bookings': Booking.objects.filter(user=user).order_by('-booking_date')[:5],
        'user_events': Event.objects.filter(booking__user=user)
                       .select_related('booking')
                       .order_by('-date')[:5],
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def profile_edit(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    children = profile.children.all()

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Профиль успешно обновлен!'))
            return redirect('profile_edit')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'child_form': ChildForm(),
        'password_form': CustomPasswordChangeForm(user=request.user),
        'children': children,
    }
    return render(request, 'accounts/profile_edit.html', context)

@login_required
@require_POST
def add_child(request):
    form = ChildForm(request.POST)
    if form.is_valid():
        child = form.save(commit=False)
        child.profile = request.user.profile
        child.save()
        messages.success(request, _('Ребенок успешно добавлен!'))
        return JsonResponse({'success': True})
    return JsonResponse({
        'success': False,
        'errors': form.errors.as_json()
    }, status=400)

@login_required
@require_POST
def delete_child(request, child_id):
    child = get_object_or_404(Child, id=child_id, profile=request.user.profile)
    child.delete()
    messages.success(request, _('Ребенок успешно удален!'))
    return JsonResponse({'success': True})

@login_required
@require_POST
def change_password(request):
    form = CustomPasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, _('Пароль успешно изменен!'))
        return JsonResponse({'success': True})
    return JsonResponse({
        'success': False,
        'errors': form.errors.as_json()
    }, status=400)

# Сотрудники

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(get_user_role_redirect(user))  # Перенаправление по роли
        else:
            return render(request, 'registration/login.html', {'error': 'Неверные данные'})
    return render(request, 'registration/login.html')

@login_required
@require_POST
def change_email(request):
    form = EmailChangeForm(request.user, request.POST)
    if form.is_valid():
        request.user.email = form.cleaned_data['new_email']
        request.user.save()
        messages.success(request, _('Email успешно изменен!'))
        return JsonResponse({'success': True})
    return JsonResponse({
        'success': False,
        'errors': form.errors.as_json()
    }, status=400)
