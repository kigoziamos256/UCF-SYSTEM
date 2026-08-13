from django.contrib import admin
from .models import Member, Department, Event, Duty, Announcement, Notification, FinancialTransaction


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_date', 'location', 'department', 'get_attendee_count', 'cover_image_preview')
    list_filter = ('event_date', 'department')
    search_fields = ('title', 'description', 'location')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'description', 'event_date', 'location', 'department', 'created_by')
        }),
        ('Cover Image', {
            'fields': ('cover_image',),
            'classes': ('collapse',),  # Collapsible section
        }),
        ('Attendees', {
            'fields': ('attendees',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def cover_image_preview(self, obj):
        """Show a thumbnail preview of the cover image in admin list"""
        if obj.cover_image and obj.cover_image.name:
            return f'<img src="{obj.cover_image.url}" style="width: 100px; height: 60px; object-fit: cover; border-radius: 4px;" />'
        return '<span style="color: #999;">No Image</span>'
    cover_image_preview.allow_tags = True
    cover_image_preview.short_description = 'Cover Preview'
    
    def get_attendee_count(self, obj):
        """Return the number of attendees for the event"""
        return obj.attendees.count()
    get_attendee_count.short_description = 'Attendees'


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'phone_number', 'is_active', 'profile_picture_preview')
    list_filter = ('role', 'department', 'is_active')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number')
    readonly_fields = ('date_joined', 'profile_picture_updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'department')
        }),
        ('Contact Details', {
            'fields': ('phone_number', 'address')
        }),
        ('Profile Picture', {
            'fields': ('profile_picture',),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('is_active', 'date_joined', 'profile_picture_updated_at')
        }),
    )
    
    def profile_picture_preview(self, obj):
        """Show a thumbnail preview of the profile picture in admin list"""
        if obj.profile_picture and obj.profile_picture.name:
            return f'<img src="{obj.profile_picture.url}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />'
        return '<span style="color: #999;">No Photo</span>'
    profile_picture_preview.allow_tags = True
    profile_picture_preview.short_description = 'Photo'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'member_count')
    search_fields = ('name', 'description')
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(Duty)
class DutyAdmin(admin.ModelAdmin):
    list_display = ('title', 'assigned_to', 'department', 'duty_date', 'completed', 'status_badge')
    list_filter = ('completed', 'duty_date', 'department')
    search_fields = ('title', 'description', 'assigned_to__username')
    readonly_fields = ('created_at', 'completed_at')
    
    fieldsets = (
        ('Duty Information', {
            'fields': ('title', 'description', 'department')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'duty_date', 'completed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',),
        }),
    )
    
    def status_badge(self, obj):
        if obj.completed:
            return '<span style="background: #28a745; color: white; padding: 2px 10px; border-radius: 12px; font-size: 12px;">Completed</span>'
        return '<span style="background: #ffc107; color: #000; padding: 2px 10px; border-radius: 12px; font-size: 12px;">Pending</span>'
    status_badge.allow_tags = True
    status_badge.short_description = 'Status'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_posted', 'created_by', 'department', 'is_important')
    list_filter = ('date_posted', 'department', 'is_important')
    search_fields = ('title', 'message', 'content')
    readonly_fields = ('date_posted',)
    
    fieldsets = (
        ('Announcement Information', {
            'fields': ('title', 'message', 'content', 'department')
        }),
        ('Settings', {
            'fields': ('is_important', 'expires_at')
        }),
        ('Metadata', {
            'fields': ('created_by', 'date_posted'),
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__user__username')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('recipient', 'notification_type', 'title', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'created_at')
        }),
        ('Related Content', {
            'fields': ('event', 'duty', 'announcement'),
            'classes': ('collapse',),
        }),
    )

@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'payer_name', 'amount', 'date', 'payment_method', 'recorded_by', 'recorded_at')
    list_filter = ('transaction_type', 'payment_method', 'date')
    search_fields = ('payer_name', 'payer_phone', 'reference_number', 'description')
    readonly_fields = ('recorded_at',)
    date_hierarchy = 'date'
