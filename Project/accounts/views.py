from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import UserUpdateForm, ProfileUpdateForm, ChildForm
from main.models import Profile, Child  # Импортируем модели из main
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse
from main.models import Profile  # Исправляем импорт
from bookings.models import Booking  # Импортируем модель Booking из приложения bookings
from django.contrib.auth import authenticate, login
from core.views import get_user_role_redirect

@login_required
def profile(request):
    user = request.user

    # Создаем профиль, если его нет
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)

    # Получаем последние 5 бронирований пользователя
    bookings = Booking.objects.filter(user=user).order_by('-booking_date')[:5]

    # Передаем данные в шаблон
    context = {
        'user': user,
        'bookings': bookings,  # Добавляем бронирования в контекст
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def profile_edit(request):
    user = request.user
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, instance=user.profile)
        child_form = ChildForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль успешно обновлен!')
            return redirect('profile')

        if child_form.is_valid():
            child = child_form.save(commit=False)
            child.profile = user.profile
            child.save()
            messages.success(request, 'Ребенок успешно добавлен!')
            return redirect('profile_edit')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=user.profile)
        child_form = ChildForm()

    # Добавляем форму смены пароля в контекст
    password_form = PasswordChangeForm(user=request.user)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'child_form': child_form,
        'password_form': password_form,  # Добавлено
    }

    return render(request, 'accounts/profile_edit.html', context)

@login_required
def add_child(request):
    if request.method == 'POST':
        child_form = ChildForm(request.POST)
        if child_form.is_valid():
            child = child_form.save(commit=False)
            child.profile = request.user.profile
            child.save()
            messages.success(request, 'Ребенок успешно добавлен!')
            return redirect('profile')
    else:
        child_form = ChildForm()

    return render(request, 'accounts/profile_edit.html', {
        'user_form': UserUpdateForm(instance=request.user),
        'profile_form': ProfileUpdateForm(instance=request.user.profile),
        'child_form': child_form,
    })

@login_required
def delete_child(request, child_id):
    child = get_object_or_404(Child, id=child_id, profile=request.user.profile)
    child.delete()
    messages.success(request, 'Ребенок успешно удален!')
    return redirect('profile')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            old_password = form.cleaned_data.get('old_password')
            new_password1 = form.cleaned_data.get('new_password1')
            new_password2 = form.cleaned_data.get('new_password2')

            # Проверка, что новый пароль не совпадает со старым
            if old_password == new_password1:
                return JsonResponse({
                    'success': False,
                    'message': 'Новый пароль не должен совпадать со старым.',
                })

            # Проверка, что новый пароль и его подтверждение совпадают
            if new_password1 != new_password2:
                return JsonResponse({
                    'success': False,
                    'message': 'Новый пароль и его подтверждение не совпадают.',
                })

            # Если все проверки пройдены, сохраняем новый пароль
            user = form.save()
            update_session_auth_hash(request, user)  # Обновляем сессию, чтобы пользователь не вышел из системы
            return JsonResponse({
                'success': True,
                'message': 'Пароль успешно изменен!',
            })
        else:
            # Если форма не валидна, выводим первую ошибку
            for field, errors in form.errors.items():
                for error in errors:
                    return JsonResponse({
                        'success': False,
                        'message': error,
                    })
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})

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


