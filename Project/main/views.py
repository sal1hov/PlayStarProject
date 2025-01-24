from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .forms import RegisterForm  # Импортируем кастомную форму для регистрации
from django.contrib import messages  # Импортируем messages

def index(request):
    return render(request, 'main/index.html')

import logging

logger = logging.getLogger(__name__)
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('index')
        else:
            # Логируем ошибки формы
            logger.error(f"Ошибки формы: {form.errors}")
            messages.error(request, 'Что-то пошло не так. Проверьте введённые данные.')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})