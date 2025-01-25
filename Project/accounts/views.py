from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserUpdateForm, ProfileUpdateForm
from .models import Profile

@login_required
def profile(request):
    user = request.user
    # Создаем профиль, если его нет
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)
    return render(request, 'accounts/profile.html', {'user': user})

@login_required
def profile_edit(request):
    user = request.user
    # Создаем профиль, если его нет
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, instance=user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль успешно обновлен!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }

    return render(request, 'accounts/profile_edit.html', context)