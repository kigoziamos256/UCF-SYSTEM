from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    path('members/', views.member_list, name='member_list'),
    path('members/<int:id>/', views.member_detail, name='member_detail'),
    path('manage-members/', views.manage_members, name='manage_members'),
    
    path('calendar/', views.calendar_view, name='calendar'),
    path('announcements/', views.announcements_list, name='announcements'),
    path('create-announcement/', views.create_announcement, name='create_announcement'),
    
    path('create-event/', views.create_event, name='create_event'),
    path('assign-duty/', views.assign_duty, name='assign_duty'),
    
    path('event/<int:event_id>/', views.event_detail_view, name='event_detail'),
    path('duty/<int:duty_id>/', views.duty_detail_view, name='duty_detail'),
    path('announcement/<int:announcement_id>/', views.announcement_detail_view, name='announcement_detail'),
    
    path('register/', views.register_member, name='register'),
    path('notification/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    
    path('create-department/', views.create_department, name='create_department'),
    path('departments/', views.department_list, name='department_list'),

    path('create-superuser/', views.create_superuser_temp, name='create_superuser'),
    
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    # 👇 ADD THIS LINE - Temporary admin creator
    path('make-admin/', views.make_admin, name='make_admin'),
    path('promote-to-admin/', views.promote_to_admin, name='promote_to_admin'),

    # Finance
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    path('finance/add/', views.finance_add_transaction, name='finance_add_transaction'),
    path('finance/transactions/', views.finance_transactions, name='finance_transactions'),
    path('finance/summary/', views.finance_summary, name='finance_summary'),
    path('finance/budget/', views.finance_budget, name='finance_budget'),
    path('finance/requisition/', views.finance_requisition, name='finance_requisition'),
    path('finance/requisition/<int:req_id>/approve/', views.finance_requisition_approve, name='finance_requisition_approve'),
    path('finance/reconciliation/', views.finance_reconciliation, name='finance_reconciliation'),
]
