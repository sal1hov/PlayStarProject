from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),

    # Управление пользователями
    path('user/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('user/<int:user_id>/delete/', views.delete_user, name='delete_user'),

    # Управление бронированиями
    path('booking/<int:booking_id>/<str:action>/', views.manage_booking, name='manage_booking'),

    # Статистика и отчеты
    path('statistics/', views.statistics_view, name='statistics'),

    # Управление мероприятиями
    path('events/', views.events_view, name='events'),
    path('events/create/', views.create_event, name='create_event'),
    path('events/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('events/<int:event_id>/approve/', views.approve_event, name='approve_event'),
    path('events/<int:event_id>/reject/', views.reject_event, name='reject_event'),
    path('events/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    path('events/<int:event_id>/view/', views.event_view, name='event_view'),
    path('events/<int:event_id>/view_booking/', views.view_booking, name='view_booking'),

    # Управление доходами
    path('income-management/', views.income_management, name='income_management'),
    path('income-management/data/', views.income_management_data, name='income_management_data'),
    path('edit-income-and-prepayment/', views.edit_income_and_prepayment, name='edit_income_and_prepayment'),
    # Управление графиком
    path('shifts/', views.ShiftListView.as_view(), name='shift_list'),
    path('my-shifts/', views.MyShiftRequestsView.as_view(), name='my_shift_requests'),
    path('shift-request/create/', views.CreateShiftRequestView.as_view(), name='create_shift_request'),
    path('admin/shift-approval/', views.AdminShiftApprovalView.as_view(), name='admin_shift_approval'),
    path('admin/shift-approval/<int:pk>/approve/', views.approve_shift_request, name='approve_shift_request'),
    path('admin/shift-approval/<int:pk>/reject/', views.reject_shift_request, name='reject_shift_request'),
    path('shift-request/<int:pk>/details/', views.shift_request_details, name='shift_request_details'),
    path('user/<int:user_id>/children/', views.manage_user_children, name='manage_user_children'),
]