from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .forms import RegisterForm  # Импортируем кастомную форму для регистрации

def index(request):
    return render(request, 'main/index.html')
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)  # Используем кастомную форму
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматический вход после регистрации
            return redirect('index')  # Перенаправление на главную страницу
    else:
        form = RegisterForm()  # Используем кастомную форму
    return render(request, 'registration/register.html', {'form': form})


