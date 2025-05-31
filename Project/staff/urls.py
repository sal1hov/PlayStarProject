from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager-dashboard'),
    path('employee-dashboard/', views.employee_dashboard, name='employee-dashboard'),
    path('user/<int:user_id>/edit/', views.edit_user, name='edit-user'),
    path('user/<int:user_id>/delete/', views.delete_user, name='delete-user'),
    path('booking/<int:booking_id>/delete/', views.delete_booking_admin, name='delete-booking-admin'),
    path('booking/<int:booking_id>/<str:action>/', views.manage_booking, name='manage-booking'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('events/', views.events_view, name='events'),
    path('events/create/', views.create_event, name='create-event'),
    path('events/<int:event_id>/edit/', views.edit_event, name='edit-event'),
    path('events/<int:event_id>/approve/', views.approve_event, name='approve-event'),
    path('events/<int:event_id>/reject/', views.reject_event, name='reject-event'),
    path('events/<int:event_id>/delete/', views.delete_event, name='delete-event'),
    path('events/<int:event_id>/view/', views.event_view, name='view-event'),
    path('events/<int:event_id>/view-booking/', views.view_booking, name='view-booking'),

    path('income-management/', views.income_management, name='income-management'),
    path('income-management/data/', views.income_management_data, name='income-management-data'),
    path('income-management/edit/', views.edit_income, name='edit-income'),

    path('shifts/', views.ShiftListView.as_view(), name='shift-list'),
    path('my-shifts/', views.MyShiftRequestsView.as_view(), name='my-shift-requests'),
    path('shift-request/create/', views.CreateShiftRequestView.as_view(), name='shift-request-create'),
    path('shift-request/<int:pk>/update/', views.UpdateShiftRequestView.as_view(), name='shift-request-update'),
    path('shift-request/<int:pk>/details/', views.shift_request_details, name='shift-request-details'),
    path('admin/shift-approval/', views.AdminShiftApprovalView.as_view(), name='admin_shift_approval'),
    path('admin/shift-approval/<int:pk>/approve/', views.approve_shift_request, name='approve-shift-request'),
    path('admin/shift-approval/<int:pk>/reject/', views.reject_shift_request, name='reject-shift-request'),
    path('shift-request/<int:pk>/details/', views.shift_request_details, name='shift-request-details'),
    path('user/<int:user_id>/children/', views.manage_user_children, name='manage-user-children'),
    path('filter-users/', views.filter_users, name='filter_users'),
]