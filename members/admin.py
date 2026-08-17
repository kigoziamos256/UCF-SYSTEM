from django.contrib import admin
from .models import (
    Member, Department, Event, Duty, Announcement, Notification,
    Attendance, Currency, IncomeCategory, ExpenseCategory, Vendor,
    FinancialTransaction, FinanceSummary, Budget, ExpenseRequisition,
    BankReconciliation
)


# ==================== EVENT ====================
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
            'classes': ('collapse',),
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
        if obj.cover_image and obj.cover_image.name:
            return f'<img src="{obj.cover_image.url}" style="width: 100px; height: 60px; object-fit: cover; border-radius: 4px;" />'
        return '<span style="color: #999;">No Image</span>'
    cover_image_preview.allow_tags = True
    cover_image_preview.short_description = 'Cover Preview'
    
    def get_attendee_count(self, obj):
        return obj.attendees.count()
    get_attendee_count.short_description = 'Attendees'


# ==================== MEMBER ====================
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
        if obj.profile_picture and obj.profile_picture.name:
            return f'<img src="{obj.profile_picture.url}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />'
        return '<span style="color: #999;">No Photo</span>'
    profile_picture_preview.allow_tags = True
    profile_picture_preview.short_description = 'Photo'


# ==================== DEPARTMENT ====================
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'member_count')
    search_fields = ('name', 'description')
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


# ==================== DUTY ====================
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


# ==================== ANNOUNCEMENT ====================
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


# ==================== NOTIFICATION ====================
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


# ==================== ATTENDANCE ====================
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('event', 'member', 'status', 'check_in_time')
    list_filter = ('status', 'event')
    search_fields = ('member__user__username', 'event__title')


# ==================== CURRENCY ====================
@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'symbol', 'name', 'is_default', 'is_active')
    list_editable = ('is_default', 'is_active')
    search_fields = ('code', 'name')
    actions = ['set_as_default']

    def set_as_default(self, request, queryset):
        if queryset.count() == 1:
            currency = queryset.first()
            Currency.objects.filter(is_default=True).update(is_default=False)
            currency.is_default = True
            currency.save()
            self.message_user(request, f"{currency.code} is now the default currency.")
        else:
            self.message_user(request, "Please select exactly one currency to set as default.", level='error')
    set_as_default.short_description = "Set selected currency as default"


# ==================== FINANCE MODELS ====================

@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category_type', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('category_type', 'is_active')


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'is_active')
    search_fields = ('name', 'contact_person', 'phone')
    list_filter = ('is_active',)


@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'get_sub_type', 'amount', 'date', 'payment_method', 'is_paid', 'recorded_by')
    list_filter = ('transaction_type', 'payment_method', 'date', 'is_paid')
    search_fields = ('payer_name', 'description', 'reference_number', 'invoice_number')
    readonly_fields = ('recorded_at', 'updated_at')
    date_hierarchy = 'date'
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_type', 'income_sub_type', 'expense_sub_type', 'amount', 'date')
        }),
        ('Payer/Vendor Information', {
            'fields': ('payer_name', 'payer_phone', 'payer_email', 'payer_member', 'vendor')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'reference_number', 'bank_reference')
        }),
        ('Categorization', {
            'fields': ('income_category', 'expense_category', 'department')
        }),
        ('Status', {
            'fields': ('is_paid', 'paid_date', 'due_date', 'invoice_number', 'purchase_order_number')
        }),
        ('Additional Info', {
            'fields': ('description', 'notes', 'receipt_image')
        }),
        ('Audit', {
            'fields': ('recorded_by', 'approved_by', 'approved_at', 'is_approved')
        }),
    )

    def get_sub_type(self, obj):
        return obj.get_sub_type_display()
    get_sub_type.short_description = 'Sub Type'


@admin.register(FinanceSummary)
class FinanceSummaryAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'total_amount', 'total_tithe', 'total_offertory', 'total_donations')
    list_filter = ('year', 'month')
    search_fields = ('year',)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('department', 'category_name', 'budgeted_amount', 'period_year', 'period_month', 'is_active')
    list_filter = ('department', 'frequency', 'period_year', 'is_active')
    search_fields = ('department', 'income_category__name', 'expense_category__name')
    actions = ['duplicate_budget']

    def category_name(self, obj):
        return obj.category_name()
    category_name.short_description = 'Category'

    def duplicate_budget(self, request, queryset):
        for budget in queryset:
            budget.pk = None
            budget.is_active = True
            budget.save()
        self.message_user(request, f"{queryset.count()} budget(s) duplicated successfully.")
    duplicate_budget.short_description = "Duplicate selected budgets"


@admin.register(ExpenseRequisition)
class ExpenseRequisitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'requested_by', 'estimated_amount', 'status', 'created_at')
    list_filter = ('status', 'department')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_requisitions', 'reject_requisitions']

    def approve_requisitions(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} requisition(s) approved.")
    approve_requisitions.short_description = "Approve selected requisitions"

    def reject_requisitions(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} requisition(s) rejected.")
    reject_requisitions.short_description = "Reject selected requisitions"


@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'statement_date', 'statement_balance', 'ledger_balance', 'difference', 'is_reconciled')
    list_filter = ('bank_name', 'statement_date', 'is_reconciled')
    search_fields = ('bank_name', 'account_number')
    readonly_fields = ('reconciled_at', 'reconciled_by')
    actions = ['mark_as_reconciled']

    def mark_as_reconciled(self, request, queryset):
        queryset.update(is_reconciled=True)
        self.message_user(request, f"{queryset.count()} reconciliation(s) marked as reconciled.")
    mark_as_reconciled.short_description = "Mark selected as reconciled"
