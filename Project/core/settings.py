import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-su7ynx19wj4qeduhfan&p$om4ruq*1#zz9r8_^p2u9()csd@&g'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'playstar.onrender.com',
    'localhost',  # Для локальной разработки
    '127.0.0.1',  # Для локальной разработки
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
    'accounts',
    'bookings',
    'staff',
    'telegram_bot',
    'social_django',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    # Убрана несуществующая папка static
    BASE_DIR / 'staff' / 'static',
    BASE_DIR / 'main' / 'static',
    BASE_DIR / 'accounts' / 'static',
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Кастомная модель пользователя
AUTH_USER_MODEL = 'main.CustomUser'

# Настройки перенаправления после входа и выхода
LOGIN_REDIRECT_URL = '/profile/'  # Перенаправление на страницу профиля после входа
LOGOUT_REDIRECT_URL = '/'  # Перенаправление на главную страницу после выхода

# Обработка ошибок для AJAX
def bad_request(request, exception=None):
    return JsonResponse({'error': 'Bad Request'}, status=400)

def permission_denied(request, exception=None):
    return JsonResponse({'error': 'Permission Denied'}, status=403)

def page_not_found(request, exception=None):
    return JsonResponse({'error': 'Page Not Found'}, status=404)

def server_error(request):
    return JsonResponse({'error': 'Server Error'}, status=500)

# Добавьте в конец файла:
handler400 = 'core.views.bad_request'
handler403 = 'core.views.permission_denied'
handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = '7583679391:AAF2mlP0JLsli1SsCpmjZZ6b2_JnKSLuKOU'
TELEGRAM_BOT_NAME = 'PlayStarAlmet_Bot'  # Без @
TELEGRAM_AUTH_TIMEOUT = 300  # 5 минут в секундах

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

CELERY_BEAT_SCHEDULE = {
    'cleanup_telegram_codes': {
        'task': 'accounts.tasks.cleanup_expired_codes',
        'schedule': timedelta(minutes=30),  # Запускать каждые 30 минут
    },
}

# Настройки CSRF
CSRF_COOKIE_HTTPONLY = False  # Разрешить доступ к CSRF из JS
CSRF_COOKIE_SECURE = False    # Для разработки, на проде должно быть True
CSRF_COOKIE_SAMESITE = 'Lax'

# Настройки CORS (если нужно)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True

# Для обработки JSON
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
SESSION_COOKIE_HTTPONLY = False