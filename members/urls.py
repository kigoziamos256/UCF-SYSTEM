from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
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
]