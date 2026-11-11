from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ==================== PUBLIC ====================
    path('', views.home, name='home'),

    # ==================== AUTH ====================
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('register/', views.register_member, name='register'),
    path('complete-profile/', views.complete_profile_view, name='complete_profile'),

    # ==================== DASHBOARD ====================
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),

    # ==================== MEMBERS ====================
    path('members/', views.member_list, name='member_list'),
    path('members/<int:id>/', views.member_detail, name='member_detail'),
    path('manage-members/', views.manage_members, name='manage_members'),

    # ==================== EVENTS & CALENDAR ====================
    path('calendar/', views.calendar_view, name='calendar'),
    path('create-event/', views.create_event, name='create_event'),
    path('event/<int:event_id>/', views.event_detail_view, name='event_detail'),

    # ==================== DUTIES ====================
    path('assign-duty/', views.assign_duty, name='assign_duty'),
    path('duty/<int:duty_id>/', views.duty_detail_view, name='duty_detail'),

    # ==================== ANNOUNCEMENTS ====================
    path('announcements/', views.announcements_list, name='announcements'),
    path('create-announcement/', views.create_announcement, name='create_announcement'),
    path('announcement/<int:announcement_id>/', views.announcement_detail_view, name='announcement_detail'),

    # ==================== NOTIFICATIONS ====================
    path('notification/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),

    # ==================== DEPARTMENTS ====================
    path('create-department/', views.create_department, name='create_department'),
    path('departments/', views.department_list, name='department_list'),

    # ==================== ADMIN BOOTSTRAP (temporary) ====================
    path('create-superuser/', views.create_superuser_temp, name='create_superuser'),
    path('make-admin/', views.make_admin, name='make_admin'),
    path('promote-to-admin/', views.promote_to_admin, name='promote_to_admin'),

    # ==================== FINANCE ====================
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    path('finance/add/', views.finance_add_transaction, name='finance_add_transaction'),
    path('finance/transactions/', views.finance_transactions, name='finance_transactions'),
    path('finance/summary/', views.finance_summary, name='finance_summary'),
    path('finance/budget/', views.finance_budget, name='finance_budget'),
    path('finance/requisition/', views.finance_requisition, name='finance_requisition'),
    path('finance/requisition/<int:req_id>/approve/', views.finance_requisition_approve, name='finance_requisition_approve'),
    path('finance/reconciliation/', views.finance_reconciliation, name='finance_reconciliation'),

    # ==================== SERVICES ====================
    path('services/sunday/', views.sunday_service_view, name='sunday_service'),
    path('services/midweek/', views.midweek_service_view, name='midweek_service'),
    path('services/upload-flyer/', views.upload_flyer, name='upload_flyer'),

    # QR attendance
    path('services/scanner/', views.scanner_view, name='scanner'),
    path('services/scan/api/', views.scan_attendance_api, name='scan_attendance_api'),
    path('services/guest/', views.guest_attendance_view, name='guest_attendance'),
    path('services/my-qr/', views.my_qr_view, name='my_qr'),
    path('services/qr/<int:member_id>/', views.member_qr_view, name='member_qr'),

    # Entrance QR (admin)
    path('services/entrance-qr/', views.entrance_qr_view, name='entrance_qr'),
    path('services/entrance-qr/<str:service_type>/image.png', views.entrance_qr_image, name='entrance_qr_image'),

    # Attendance report (admin)
    path('services/attendance-report/', views.attendance_report_view, name='attendance_report'),
    path('services/attendance-report/export/', views.attendance_export_csv, name='attendance_export_csv'),
    # ==================== HELP ====================
    path('help/', views.help_view, name='help'),

    # ==================== NOTIFICATIONS API ====================
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/notifications/mark-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Duty completion
    path('duty/<int:duty_id>/complete/', views.mark_duty_complete, name='mark_duty_complete'),

    # ==================== DEPARTMENT PROFILES ====================
    path('departments/', views.department_list_view, name='department_list_view'),
    path('departments/<int:dept_id>/', views.department_detail_view, name='department_detail'),
    path('departments/<int:dept_id>/edit/', views.department_edit_view, name='department_edit'),
    # ==================== MEDIA HUB ====================
    path('media/', views.media_dashboard, name='media_dashboard'),
    path('media/equipment/', views.equipment_list, name='equipment_list'),
    path('media/equipment/add/', views.equipment_add, name='equipment_add'),
    path('media/lend/', views.lend_equipment, name='lend_equipment'),
    path('media/return/<int:loan_id>/', views.return_equipment, name='return_equipment'),
    path('media/external-events/', views.external_events_list, name='external_events_list'),
    path('media/external-events/add/', views.add_external_event, name='add_external_event'),
    path('attendance/email-report/', views.email_attendance_report, name='email_attendance_report'),

    # ==================== CHAT SYSTEM ====================
    path('chat/', views.chat_dashboard, name='chat_dashboard'),
    path('chat/<int:room_id>/', views.chat_room, name='chat_room'),
    path('chat/start/<int:user_id>/', views.start_direct_chat, name='start_direct_chat'),

    # Sermons & Gallery
    path('sermons/', views.sermon_list, name='sermon_list'),
    path('sermons/<int:sermon_id>/', views.sermon_detail, name='sermon_detail'),
    path('sermons/add/', views.add_sermon, name='add_sermon'),
    path('gallery/', views.gallery_list, name='gallery_list'),
    path('gallery/<int:gallery_id>/', views.gallery_detail, name='gallery_detail'),
    path('gallery/add/', views.add_gallery, name='add_gallery'),
    path('services/attendance-report/pdf/', views.download_attendance_pdf, name='download_attendance_pdf'),

]
