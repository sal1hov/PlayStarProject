from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import RegisterForm  # Импортируем кастомную форму для регистрации

def index(request):
    return render(request, 'main/index.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматический вход после регистрации
            messages.success(request, 'Регистрация прошла успешно!')  # Уведомление об успехе
            return redirect('index')  # Перенаправление на главную страницу
        else:
            messages.error(request, 'Что-то пошло не так. Проверьте введённые данные.')  # Уведомление об ошибке
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})