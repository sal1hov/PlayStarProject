from django.urls import path
from accounts.views import (
    profile, profile_edit, add_child, delete_child, change_password,
    change_email, social_accounts, disconnect_social_account,
    verify_telegram_code, telegram_login, login_view, start_telegram_login
)

app_name = 'accounts'

urlpatterns = [
    path('login/', login_view, name='login'),
    path('profile/', profile, name='profile'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('profile/add_child/', add_child, name='add_child'),
    path('profile/delete_child/<int:child_id>/', delete_child, name='delete_child'),
    path('change-password/', change_password, name='change_password'),
    path('change-email/', change_email, name='change_email'),
    path('profile/social/', social_accounts, name='social_accounts'),
    path('profile/social/disconnect/', disconnect_social_account, name='disconnect_social_account'),
    path('verify-telegram-code/', verify_telegram_code, name='verify_telegram_code'),
    path('telegram-login/', telegram_login, name='telegram_login'),
    path('start-telegram-login/', start_telegram_login, name='start_telegram_login'),
]