from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import RegisterForm

def index(request):
    return render(request, 'main/index.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Убираем автоматический вход после регистрации
            # login(request, user)  # Закомментируйте эту строку
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('login')  # Перенаправляем на страницу входа
        else:
            messages.error(request, 'Что-то пошло не так. Проверьте введённые данные.')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})