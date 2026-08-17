from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill


# ==================== DEPARTMENT ====================
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# ==================== MEMBER ====================
class Member(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('leader', 'Leader'),
        ('finance', 'Finance'),
        ('member', 'Member'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='member')

    profile_picture = ProcessedImageField(
        upload_to='profile_pics/',
        processors=[ResizeToFill(300, 300)],
        format='JPEG',
        options={'quality': 90},
        null=True,
        blank=True
    )

    profile_picture_updated_at = models.DateTimeField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url') and self.profile_picture.name:
            return self.profile_picture.url
        initials = self.get_initials()
        return f"https://ui-avatars.com/api/?name={initials}&size=300&background=random&color=fff&length=2&font-size=0.5"

    def get_initials(self):
        full_name = self.user.get_full_name()
        if full_name:
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                return f"{name_parts[0][0]}{name_parts[-1][0]}".upper()
            return name_parts[0][:2].upper()
        else:
            return self.user.username[:2].upper()


# ==================== EVENT ====================
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events_created")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, related_name="events")
    location = models.CharField(max_length=200)
    attendees = models.ManyToManyField(User, blank=True, related_name="events_joined")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cover_image = ProcessedImageField(
        upload_to='event_covers/',
        processors=[ResizeToFill(800, 400)],
        format='JPEG',
        options={'quality': 85},
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['event_date']

    def __str__(self):
        return self.title

    def get_attendee_count(self):
        return self.attendees.count()


# ==================== ATTENDANCE ====================
class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('excused', 'Excused'),
        ('late', 'Late'),
    )

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendance_records')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    check_in_time = models.DateTimeField(default=timezone.now)
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_checked')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['event', 'member']
        ordering = ['-check_in_time']

    def __str__(self):
        return f"{self.member.user.username} - {self.event.title} - {self.status}"


# ==================== CURRENCY ====================
class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True, help_text="e.g., USD, UGX, EUR, GBP")
    symbol = models.CharField(max_length=10, help_text="e.g., $, UGX, €, £")
    name = models.CharField(max_length=50, help_text="e.g., US Dollar, Uganda Shilling")
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Currencies"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} ({self.symbol})"

    def save(self, *args, **kwargs):
        if self.is_default:
            Currency.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# ==================== FINANCE MODELS ====================

class IncomeCategory(models.Model):
    """Income categories for budgeting and tracking"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=20, unique=True, help_text="e.g., INC-001")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Income Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class ExpenseCategory(models.Model):
    """Expense categories for budgeting and tracking"""
    CATEGORY_TYPES = (
        ('direct', 'Direct Cost'),
        ('overhead', 'Shared Overhead'),
        ('capital', 'Capital Expenditure'),
        ('operational', 'Operational'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, default='operational')
    code = models.CharField(max_length=20, unique=True, help_text="e.g., EXP-001")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Vendor(models.Model):
    """Vendor/Supplier management"""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True, help_text="Tax/VAT registration number")
    payment_terms = models.CharField(max_length=50, blank=True, help_text="e.g., Net 30")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class FinancialTransaction(models.Model):
    """Main transaction model for all income and expenses (full version)"""
    TRANSACTION_TYPES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    )

    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('card', 'Card'),
        ('mpesa', 'M-Pesa'),
        ('airtel_money', 'Airtel Money'),
    )

    INCOME_SUB_TYPES = (
        ('tithe', 'Tithe'),
        ('offertory', 'Offertory'),
        ('donation', 'Donation'),
        ('offering', 'Offering'),
        ('special', 'Special Offering'),
        ('facility_rent', 'Facility Rent'),
        ('cafe_sales', 'Cafe Sales'),
        ('gym_membership', 'Gym Membership'),
        ('gym_day_pass', 'Gym Day Pass'),
        ('gym_training', 'Gym Training/Classes'),
        ('catering', 'Catering'),
        ('other_income', 'Other Income'),
    )

    EXPENSE_SUB_TYPES = (
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('salaries', 'Salaries/Wages'),
        ('equipment', 'Equipment'),
        ('maintenance', 'Maintenance'),
        ('travel', 'Travel'),
        ('supplies', 'Supplies'),
        ('marketing', 'Marketing'),
        ('insurance', 'Insurance'),
        ('taxes', 'Taxes'),
        ('cafe_supplies', 'Cafe Supplies'),
        ('gym_equipment', 'Gym Equipment'),
        ('other_expense', 'Other Expense'),
    )

    # Transaction core
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    income_sub_type = models.CharField(max_length=50, choices=INCOME_SUB_TYPES, blank=True, null=True)
    expense_sub_type = models.CharField(max_length=50, choices=EXPENSE_SUB_TYPES, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)

    # For income transactions
    payer_name = models.CharField(max_length=200, blank=True)
    payer_phone = models.CharField(max_length=20, blank=True)
    payer_email = models.EmailField(blank=True)
    payer_member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='income_transactions')

    # For expense transactions
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    invoice_number = models.CharField(max_length=100, blank=True, help_text="Vendor invoice number")
    purchase_order_number = models.CharField(max_length=100, blank=True)
    due_date = models.DateField(null=True, blank=True, help_text="Payment due date")
    paid_date = models.DateField(null=True, blank=True, help_text="Date payment was made")
    is_paid = models.BooleanField(default=False)

    # Payment details
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='cash')
    reference_number = models.CharField(max_length=100, blank=True, help_text="Transaction reference or receipt number")
    bank_reference = models.CharField(max_length=100, blank=True, help_text="Bank transaction reference")

    # Categorization
    income_category = models.ForeignKey(IncomeCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    expense_category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='finance_transactions')

    # Additional fields
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    receipt_image = ProcessedImageField(
        upload_to='finance/receipts/',
        processors=[ResizeToFill(800, 600)],
        format='JPEG',
        options={'quality': 85},
        null=True,
        blank=True
    )

    # Approval and audit
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_transactions')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_transactions')
    approved_at = models.DateTimeField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-recorded_at']
        verbose_name = "Financial Transaction"
        verbose_name_plural = "Financial Transactions"

    def __str__(self):
        if self.transaction_type == 'income':
            return f"{self.get_income_sub_type_display()} - {self.payer_name} - {self.amount}"
        else:
            return f"{self.get_expense_sub_type_display()} - {self.vendor} - {self.amount}"

    def get_sub_type_display(self):
        if self.transaction_type == 'income':
            return self.get_income_sub_type_display()
        return self.get_expense_sub_type_display()


class FinanceSummary(models.Model):
    """Monthly/Yearly financial summary"""
    year = models.IntegerField()
    month = models.IntegerField(null=True, blank=True)
    total_tithe = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_offertory = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_donations = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_mobile_money = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_bank_transfer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_offering = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_special = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['year', 'month']
        ordering = ['-year', '-month']

    def __str__(self):
        if self.month:
            return f"{self.year} - {self.month} Summary"
        return f"{self.year} Summary"


class Budget(models.Model):
    """Budget management with department, category, and period"""
    DEPARTMENT_CHOICES = (
        ('church', 'Church'),
        ('cafe', 'Cafe'),
        ('gym', 'Gym'),
        ('shared', 'Shared Overhead'),
    )

    FREQUENCY_CHOICES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    )

    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    income_category = models.ForeignKey(IncomeCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='budgets')
    expense_category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='budgets')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    period_month = models.IntegerField(null=True, blank=True, help_text="1-12 for monthly")
    period_year = models.IntegerField()
    budgeted_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-period_year', 'period_month']
        unique_together = ['department', 'income_category', 'expense_category', 'period_month', 'period_year']

    def __str__(self):
        return f"{self.department} - {self.category_name()} - {self.get_period_display()}"

    def category_name(self):
        if self.income_category:
            return self.income_category.name
        if self.expense_category:
            return self.expense_category.name
        return "General"

    def get_period_display(self):
        if self.frequency == 'annual':
            return str(self.period_year)
        return f"{timezone.datetime(self.period_year, self.period_month or 1, 1).strftime('%B')} {self.period_year}"

    def get_actual_amount(self):
        """Get actual amount spent/received for this budget period"""
        from django.db.models import Sum
        if self.income_category:
            actual = FinancialTransaction.objects.filter(
                income_category=self.income_category,
                transaction_type='income',
                date__year=self.period_year
            )
            if self.frequency == 'monthly' and self.period_month:
                actual = actual.filter(date__month=self.period_month)
            return actual.aggregate(Sum('amount'))['amount__sum'] or 0
        elif self.expense_category:
            actual = FinancialTransaction.objects.filter(
                expense_category=self.expense_category,
                transaction_type='expense',
                date__year=self.period_year
            )
            if self.frequency == 'monthly' and self.period_month:
                actual = actual.filter(date__month=self.period_month)
            return actual.aggregate(Sum('amount'))['amount__sum'] or 0
        return 0

    def get_variance(self):
        """Calculate variance between actual and budgeted"""
        actual = self.get_actual_amount()
        if self.income_category:
            return actual - self.budgeted_amount  # Positive = good
        return self.budgeted_amount - actual      # Positive = good (under budget)

    def get_status(self):
        """Get status color based on variance"""
        variance = self.get_variance()
        if self.income_category:
            if variance >= 0:
                return 'green'
            elif variance >= -self.budgeted_amount * 0.1:
                return 'yellow'
            else:
                return 'red'
        else:
            if variance >= 0:
                return 'green'
            elif variance >= -self.budgeted_amount * 0.1:
                return 'yellow'
            else:
                return 'red'


class ExpenseRequisition(models.Model):
    """Purchase requisition and approval workflow"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('purchased', 'Purchased'),
        ('paid', 'Paid'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisitions')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='requisitions')
    expense_category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, related_name='requisitions')
    estimated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='requisitions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requisitions')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.requested_by.username} - {self.get_status_display()}"


class BankReconciliation(models.Model):
    """Bank and cash reconciliation records"""
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50, blank=True)
    statement_date = models.DateField()
    statement_balance = models.DecimalField(max_digits=12, decimal_places=2)
    ledger_balance = models.DecimalField(max_digits=12, decimal_places=2)
    difference = models.DecimalField(max_digits=12, decimal_places=2, help_text="Statement - Ledger")
    reconciled_at = models.DateTimeField(auto_now_add=True)
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reconciliations')
    notes = models.TextField(blank=True)
    is_reconciled = models.BooleanField(default=False)

    class Meta:
        ordering = ['-statement_date']

    def __str__(self):
        return f"{self.bank_name} - {self.statement_date}"


# ==================== DUTY ====================
class Duty(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name="duties")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="duties")
    duty_date = models.DateField()
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="duties_created")

    class Meta:
        ordering = ['duty_date', 'title']
        verbose_name_plural = "Duties"

    def __str__(self):
        return self.title

    def mark_completed(self):
        self.completed = True
        self.completed_at = timezone.now()
        self.save()


# ==================== ANNOUNCEMENT ====================
class Announcement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, related_name="announcements")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="announcements")
    is_important = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_posted']

    def __str__(self):
        return self.title

    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


# ==================== NOTIFICATION ====================
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('event', 'Event'),
        ('duty', 'Duty'),
        ('announcement', 'Announcement'),
        ('general', 'General'),
    )

    recipient = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    title = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    duty = models.ForeignKey(Duty, on_delete=models.SET_NULL, null=True, blank=True)
    announcement = models.ForeignKey(Announcement, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.user.username}: {self.message[:50]}"

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()


# ==================== SIGNALS ====================

@receiver(post_save, sender=User)
def create_member_profile(sender, instance, created, **kwargs):
    if created:
        Member.objects.create(user=instance)
    else:
        Member.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_member_profile(sender, instance, **kwargs):
    if hasattr(instance, 'member'):
        instance.member.save()


@receiver(post_save, sender=Member)
def update_profile_picture_timestamp(sender, instance, **kwargs):
    if instance.profile_picture and not instance.profile_picture_updated_at:
        instance.profile_picture_updated_at = timezone.now()
        Member.objects.filter(pk=instance.pk).update(profile_picture_updated_at=timezone.now())


@receiver(post_save, sender=Event)
def notify_new_event(sender, instance, created, **kwargs):
    if created:
        if instance.department:
            recipients = Member.objects.filter(department=instance.department, is_active=True)
        else:
            recipients = Member.objects.filter(is_active=True)

        for recipient in recipients:
            Notification.objects.create(
                recipient=recipient,
                notification_type='event',
                title=f"New Event: {instance.title}",
                message=f"A new event '{instance.title}' has been scheduled for {instance.event_date.strftime('%B %d, %Y at %I:%M %p')}.",
                event=instance
            )


@receiver(post_save, sender=Duty)
def notify_new_duty(sender, instance, created, **kwargs):
    if created:
        try:
            recipient = Member.objects.get(user=instance.assigned_to)
            Notification.objects.create(
                recipient=recipient,
                notification_type='duty',
                title=f"New Duty: {instance.title}",
                message=f"You have been assigned a new duty: '{instance.title}' due on {instance.duty_date.strftime('%B %d, %Y')}.",
                duty=instance
            )
        except Member.DoesNotExist:
            pass


@receiver(post_save, sender=Announcement)
def notify_new_announcement(sender, instance, created, **kwargs):
    if created:
        if instance.department:
            recipients = Member.objects.filter(department=instance.department, is_active=True)
        else:
            recipients = Member.objects.filter(is_active=True)

        for recipient in recipients:
            Notification.objects.create(
                recipient=recipient,
                notification_type='announcement',
                title=f"New Announcement: {instance.title}",
                message=f"A new announcement has been posted: '{instance.title}'",
                announcement=instance
            )


@receiver(post_save, sender=Duty)
def check_duty_completion(sender, instance, **kwargs):
    if instance.completed and not instance.completed_at:
        instance.completed_at = timezone.now()
        Duty.objects.filter(pk=instance.pk).update(completed_at=timezone.now())

        try:
            if instance.created_by:
                recipient = Member.objects.get(user=instance.created_by)
                Notification.objects.create(
                    recipient=recipient,
                    notification_type='duty',
                    title=f"Duty Completed: {instance.title}",
                    message=f"{instance.assigned_to.get_full_name() or instance.assigned_to.username} has completed the duty: '{instance.title}'",
                    duty=instance
                )
        except (Member.DoesNotExist, AttributeError):
            pass
