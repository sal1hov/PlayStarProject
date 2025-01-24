from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def profile(request):
    user = request.user
    return render(request, 'accounts/profile.html', {'user': user})