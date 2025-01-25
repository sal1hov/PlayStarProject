from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserUpdateForm, ProfileUpdateForm, ChildForm
from .models import Profile, Child

@login_required
def profile(request):
    user = request.user
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)
    return render(request, 'accounts/profile.html', {'user': user})

@login_required
def profile_edit(request):
    user = request.user
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, instance=user.profile)

        # Обработка формы добавления ребенка
        if 'add_child' in request.POST:
            child_form = ChildForm(request.POST)
            if child_form.is_valid():
                child = child_form.save(commit=False)
                child.profile = user.profile
                child.save()
                messages.success(request, 'Ребенок успешно добавлен!')
                return redirect('profile_edit')
        else:
            child_form = ChildForm()

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль успешно обновлен!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=user.profile)
        child_form = ChildForm()

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'child_form': child_form,
    }

    return render(request, 'accounts/profile_edit.html', context)