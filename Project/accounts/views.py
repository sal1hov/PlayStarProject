# Project/accounts/views.py

from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from core.views import get_user_role_redirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import (
    UserUpdateForm, ProfileUpdateForm, ChildForm, EmailChangeForm,
    CustomPasswordChangeForm, SocialAccountDisconnectForm
)
from main.models import Profile, Child
from bookings.models import Booking
from staff.models import Event, BirthdayPackage
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import SocialAccount
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from django.contrib.auth import get_user_model
from .utils import generate_telegram_code, get_code_expiration

# Добавили недостающий импорт:
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)
User = get_user_model()


@login_required
def profile(request):
    user = request.user
    Profile.objects.get_or_create(user=user)

    # Получаем все пакеты "День рождения" для модального окна
    birthday_packages = BirthdayPackage.objects.all()

    # Текущая дата/время, чтобы поле <input type="datetime-local"> не позволило выбрать прошедшую дату
    today = timezone.now().strftime('%Y-%m-%dT%H:%M')

    context = {
        'user': user,
        'bookings': Booking.objects.filter(user=user).order_by('-created_at')[:5],
        'user_events': Event.objects.filter(booking__user=user)
                           .select_related('booking')
                           .order_by('-date')[:5],
        'birthday_packages': birthday_packages,
        'today': today,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    children = profile.children.all()

    telegram_account = SocialAccount.objects.filter(user=user, provider='telegram').first()

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Профиль успешно обновлен!'))
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'child_form': ChildForm(),
        'password_form': CustomPasswordChangeForm(user=request.user),
        'children': children,
        'telegram_bot_name': getattr(settings, 'TELEGRAM_BOT_NAME', ''),
        'telegram_account': telegram_account,
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


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(get_user_role_redirect(user))
        else:
            messages.error(request, 'Неверные данные для входа')
            return render(request, 'registration/login.html', {
                'telegram_bot_name': settings.TELEGRAM_BOT_NAME,
                'error': 'Неверные данные'
            })

    return render(request, 'registration/login.html', {
        'telegram_bot_name': settings.TELEGRAM_BOT_NAME
    })


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


@login_required
def social_accounts(request):
    # Генерация кода привязки Telegram-аккаунта
    if request.method == 'POST' and 'generate_telegram_token' in request.POST:
        code = generate_telegram_code()
        expires_at = get_code_expiration()

        # Сохраняем код и время истечения в сессии
        request.session['telegram_auth'] = {
            'code': code,
            'expires_at': expires_at.isoformat()
        }

        messages.success(
            request,
            f"Код для привязки: {code} (действителен до {expires_at.strftime('%H:%M')})"
        )
        return redirect('accounts:social_accounts')


@login_required
@require_POST
def disconnect_social_account(request):
    form = SocialAccountDisconnectForm(request.user, request.POST)
    if form.is_valid():
        account = form.cleaned_data['account_id']
        if account.provider == 'telegram':
            account.delete()
            return JsonResponse({
                'success': True,
                'message': 'Telegram аккаунт успешно отвязан',
                'telegram_connected': False
            })
        return JsonResponse({
            'success': False,
            'error': 'Неизвестный провайдер аккаунта'
        }, status=400)
    return JsonResponse({
        'success': False,
        'error': 'Ошибка при отвязке аккаунта'
    }, status=400)


@login_required
@require_POST
def verify_telegram_code(request):
    code = request.POST.get('code', '').strip()

    try:
        account = SocialAccount.objects.get(
            provider='telegram_pending',
            user__isnull=True,
            extra_data__code=code
        )

        expires_at = datetime.fromisoformat(account.extra_data['expires_at'])
        if timezone.now() > expires_at:
            account.delete()
            return JsonResponse({
                'success': False,
                'error': 'Срок действия кода истек'
            }, status=400)

        if SocialAccount.objects.filter(
                provider='telegram',
                uid=f"telegram_{account.extra_data['telegram_id']}"
        ).exists():
            account.delete()
            return JsonResponse({
                'success': False,
                'error': 'Этот Telegram аккаунт уже привязан'
            }, status=400)

        account.user = request.user
        account.provider = 'telegram'
        account.uid = f"telegram_{account.extra_data['telegram_id']}"
        account.extra_data['verified'] = True
        account.save()

        return JsonResponse({
            'success': True,
            'message': 'Telegram успешно привязан!'
        })

    except SocialAccount.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Неверный код подтверждения'
        }, status=400)
    except Exception as e:
        logger.error(f"Ошибка при проверке кода: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Произошла ошибка при обработке кода'
        }, status=500)


def generate_telegram_code():
    """Генерация 6-значного кода"""
    import secrets, string
    return ''.join(secrets.choice(string.digits) for _ in range(6))


@csrf_exempt
def telegram_login(request):
    # Вход через Telegram-код (POST JSON с полем "code")
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            code = data.get('code')

            # Ищем временный аккаунт с этим кодом
            try:
                account = SocialAccount.objects.get(
                    provider='telegram_pending',
                    extra_data__code=code,
                    extra_data__purpose='login'
                )
            except SocialAccount.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Неверный код подтверждения'
                }, status=400)

            # Проверяем срок действия
            expires_at = datetime.fromisoformat(account.extra_data['expires_at'])
            if timezone.now() > expires_at:
                account.delete()
                return JsonResponse({
                    'success': False,
                    'error': 'Срок действия кода истек'
                }, status=400)

            # Если аккаунт уже привязан к пользователю
            if account.user:
                user = account.user
                login(request, user)

                # Превращаем временную запись в постоянную
                telegram_id = account.extra_data['telegram_id']
                account.provider = 'telegram'
                account.uid = f"telegram_{telegram_id}"
                account.extra_data['verified'] = True
                account.save()

                return JsonResponse({
                    'success': True,
                    'redirect': get_user_role_redirect(user)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Аккаунт Telegram не привязан к пользователю'
                }, status=400)

        except Exception as e:
            logger.error(f"Ошибка при входе через Telegram: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка'
            }, status=500)

    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'}, status=405)


def start_telegram_login(request):
    # Генерация кода для логина через Telegram (возвращается JSON с code и expires_at)
    if request.method == 'POST':
        try:
            code = generate_telegram_code()
            expires_at = timezone.now() + timedelta(minutes=5)

            # Сохраняем в сессии
            request.session['telegram_login'] = {
                'code': code,
                'expires_at': expires_at.isoformat()
            }

            return JsonResponse({
                'success': True,
                'code': code,
                'expires_at': expires_at.isoformat()
            })
        except Exception as e:
            logger.error(f"Ошибка при генерации кода: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка'
            }, status=500)
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'}, status=405)
