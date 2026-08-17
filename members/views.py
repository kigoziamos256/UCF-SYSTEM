from django.contrib.auth import login, logout
from django.core.exceptions import PermissionDenied
from decimal import Decimal
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib import messages

from .models import (
    Event, Member, Duty, Announcement, Notification, Attendance, Department,
    FinancialTransaction, Budget, ExpenseRequisition, BankReconciliation,
    Vendor, IncomeCategory, ExpenseCategory, Currency
)
from .forms import (
    EventForm, MemberRegistrationForm, DutyForm, AnnouncementForm,
    DepartmentForm, ProfilePictureForm, UserRegisterForm, AttendanceForm,
    FinancialTransactionForm, BudgetForm, ExpenseRequisitionForm,
    BankReconciliationForm, FinanceFilterForm
)


# -------------------------
# DECORATORS
# -------------------------

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'member') and request.user.member.role == "admin":
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper

def leader_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'member') and request.user.member.role in ["admin", "leader"]:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


# -------------------------
# LOGOUT
# -------------------------

def custom_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


# -------------------------
# HOME
# -------------------------

def home(request):
    return render(request, "home.html")


# -------------------------
# TEMPORARY ADMIN CREATORS
# -------------------------

def make_admin(request):
    """Temporary view – visit /members/make-admin/ to create a superuser."""
    if User.objects.filter(is_superuser=True).exists():
        messages.info(request, "Superuser already exists.")
    else:
        User.objects.create_superuser('admin', 'admin@church.com', 'admin123')
        messages.success(request, "Superuser created! Username: admin, Password: admin123")
    return redirect('/admin/')


def create_superuser_temp(request):
    """Alternative temporary view – visit /members/create-superuser/."""
    if User.objects.filter(is_superuser=True).exists():
        messages.info(request, "Superuser already exists.")
    else:
        User.objects.create_superuser('admin', 'admin@church.com', 'admin123')
        messages.success(request, "Superuser created! You can now log in at /admin")
    return redirect('home')


# -------------------------
# MEMBER MANAGEMENT
# -------------------------

@login_required
def promote_to_admin(request):
    if request.user.is_superuser:
        member = request.user.member
        member.role = 'admin'
        member.save()
        messages.success(request, "Your member role has been updated to Admin!")
    else:
        messages.error(request, "You need to be a superuser to do this.")
    return redirect('dashboard')


@login_required
@admin_required
def manage_members(request):
    members = Member.objects.all()
    return render(request, "members/manage_members.html", {"members": members})


def register_member(request):
    if request.method == "POST":
        user_form = UserRegisterForm(request.POST)
        member_form = MemberRegistrationForm(request.POST, request.FILES)

        if user_form.is_valid() and member_form.is_valid():
            user = user_form.save()
            member = user.member
            member.department = member_form.cleaned_data.get('department')
            if member_form.cleaned_data.get('profile_picture'):
                member.profile_picture = member_form.cleaned_data['profile_picture']
            if member_form.cleaned_data.get('phone_number'):
                member.phone_number = member_form.cleaned_data['phone_number']
            member.save()

            login(request, user)
            messages.success(request, "Registration successful! Welcome.")
            return redirect('dashboard')
        else:
            return render(request, "members/register.html", {
                "user_form": user_form,
                "member_form": member_form
            })
    else:
        user_form = UserRegisterForm()
        member_form = MemberRegistrationForm()

    return render(request, "members/register.html", {
        "user_form": user_form,
        "member_form": member_form
    })


@login_required
def member_list(request):
    query = request.GET.get("q")
    members = Member.objects.select_related("user", "department").all()

    if query:
        members = members.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(department__name__icontains=query)
        )

    return render(request, "members/member_list.html", {"members": members})


@login_required
def member_detail(request, id):
    member = get_object_or_404(
        Member.objects.select_related("user", "department"),
        id=id
    )

    upcoming_events = Event.objects.filter(
        attendees=member.user,
        event_date__gte=timezone.now()
    ).order_by("event_date")[:5]

    duties = Duty.objects.filter(assigned_to=member.user).order_by("duty_date")[:5]

    context = {
        "member": member,
        "upcoming_events": upcoming_events,
        "duties": duties,
    }
    return render(request, "members/member_detail.html", context)


# -------------------------
# DASHBOARD
# -------------------------

@login_required
def dashboard_view(request):
    user = request.user
    member = user.member
    notifications = member.notifications.filter(is_read=False).order_by('-created_at')

    if member.role == "admin":
        upcoming_events = Event.objects.filter(
            event_date__gte=timezone.now()
        ).order_by("event_date")[:5]
    elif member.role == "leader":
        upcoming_events = Event.objects.filter(
            department=member.department,
            event_date__gte=timezone.now()
        ).order_by("event_date")[:5]
    else:
        upcoming_events = Event.objects.filter(
            event_date__gte=timezone.now()
        ).order_by("event_date")[:5]

    pending_duties = Duty.objects.filter(
        assigned_to=user,
        completed=False
    ).order_by("duty_date")[:5]

    if member.role == "admin":
        announcements = Announcement.objects.all().order_by("-date_posted")[:5]
    elif member.role == "leader" and member.department:
        announcements = Announcement.objects.filter(
            department=member.department
        ).order_by("-date_posted")[:5]
    else:
        announcements = Announcement.objects.all().order_by("-date_posted")[:5]

    attendance_present = Attendance.objects.filter(member=member, status='present').count()
    attendance_late = Attendance.objects.filter(member=member, status='late').count()
    attendance_absent = Attendance.objects.filter(member=member, status='absent').count()

    context = {
        "user": user,
        "upcoming_events": upcoming_events,
        "pending_duties": pending_duties,
        "announcements": announcements,
        "total_members": Member.objects.count(),
        "total_events": Event.objects.count(),
        "total_duties": Duty.objects.count(),
        "notifications": notifications,
        "attendance_present": attendance_present,
        "attendance_late": attendance_late,
        "attendance_absent": attendance_absent,
    }
    return render(request, "dashboard.html", context)


# -------------------------
# EVENTS
# -------------------------

@login_required
@admin_required
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()

            for member in Member.objects.all():
                Notification.objects.create(
                    recipient=member,
                    notification_type='event',
                    title=f"New Event: {event.title}",
                    message=f"New event '{event.title}' has been scheduled for {event.event_date.strftime('%B %d, %Y at %I:%M %p')}.",
                    event=event
                )

            messages.success(request, f"Event '{event.title}' created and all members notified!")
            return redirect('calendar')
    else:
        form = EventForm()

    return render(request, 'members/create_event.html', {'form': form})


@login_required
def calendar_view(request):
    events = Event.objects.filter(event_date__gte=timezone.now()).order_by("event_date")
    return render(request, "calendar.html", {"upcoming_events": events})


@login_required
def event_detail_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user_member = request.user.member

    attendance = None
    try:
        attendance = Attendance.objects.get(event=event, member=user_member)
    except Attendance.DoesNotExist:
        pass

    if request.method == "POST":
        if 'join' in request.POST:
            if request.user not in event.attendees.all():
                event.attendees.add(request.user)
                messages.success(request, "You have joined the event!")
        elif 'unjoin' in request.POST:
            if request.user in event.attendees.all():
                event.attendees.remove(request.user)
                messages.success(request, "You have left the event!")
        elif 'mark_attendance' in request.POST:
            form = AttendanceForm(request.POST)
            if form.is_valid():
                attendance = form.save(commit=False)
                attendance.event = event
                attendance.member = user_member
                attendance.checked_by = request.user
                attendance.save()
                messages.success(request, f"Attendance marked as {attendance.get_status_display()}!")
                return redirect('event_detail', event_id=event.id)
        return redirect('event_detail', event_id=event.id)

    attendance_stats = {
        'present': Attendance.objects.filter(event=event, status='present').count(),
        'absent': Attendance.objects.filter(event=event, status='absent').count(),
        'excused': Attendance.objects.filter(event=event, status='excused').count(),
        'late': Attendance.objects.filter(event=event, status='late').count(),
        'total': Attendance.objects.filter(event=event).count(),
    }

    context = {
        'event': event,
        'attendance': attendance,
        'attendance_stats': attendance_stats,
        'attendance_form': AttendanceForm() if not attendance else None,
    }
    return render(request, "event_detail.html", context)


# -------------------------
# DUTIES
# -------------------------

@login_required
@leader_required
def assign_duty(request):
    if request.method == "POST":
        form = DutyForm(request.POST)
        if form.is_valid():
            duty = form.save(commit=False)
            duty.created_by = request.user
            duty.save()

            try:
                recipient = Member.objects.get(user=duty.assigned_to)
                Notification.objects.create(
                    recipient=recipient,
                    notification_type='duty',
                    title=f"New Duty: {duty.title}",
                    message=f"You have been assigned a new duty: '{duty.title}' due on {duty.duty_date.strftime('%B %d, %Y')}.",
                    duty=duty
                )
                messages.success(request, f"Duty assigned to {duty.assigned_to.get_full_name() or duty.assigned_to.username}!")
            except Member.DoesNotExist:
                messages.warning(request, "Duty assigned but notification could not be sent.")

            return redirect('dashboard')
    else:
        form = DutyForm()

    return render(request, 'members/assign_duty.html', {'form': form})


@login_required
def duty_detail_view(request, duty_id):
    duty = get_object_or_404(Duty, id=duty_id)
    return render(request, "duty_detail.html", {"duty": duty})


# -------------------------
# ANNOUNCEMENTS
# -------------------------

@login_required
def announcements_list(request):
    announcements = Announcement.objects.all().order_by("-date_posted")
    return render(request, "announcements.html", {"announcements": announcements})


@login_required
@leader_required
def create_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()

            if announcement.department:
                members = Member.objects.filter(department=announcement.department)
            else:
                members = Member.objects.all()

            for member in members:
                Notification.objects.create(
                    recipient=member,
                    notification_type='announcement',
                    title=f"New Announcement: {announcement.title}",
                    message=f"New announcement: '{announcement.title}'",
                    announcement=announcement
                )

            messages.success(request, f"Announcement '{announcement.title}' posted!")
            return redirect('dashboard')
    else:
        form = AnnouncementForm()

    return render(request, 'members/create_announcement.html', {'form': form})


@login_required
def announcement_detail_view(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    return render(request, "announcement_detail.html", {"announcement": announcement})


# -------------------------
# DEPARTMENTS
# -------------------------

@login_required
@admin_required
def create_department(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created successfully!")
            return redirect('department_list')
    else:
        form = DepartmentForm()

    return render(request, 'members/create_department.html', {'form': form})


@login_required
@admin_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'members/department_list.html', {'departments': departments})


# -------------------------
# PROFILE
# -------------------------

@login_required
def profile_view(request):
    member = request.user.member

    events_attended = request.user.events_joined.count()
    duties_completed = Duty.objects.filter(assigned_to=request.user, completed=True).count()
    announcements_count = Announcement.objects.filter(created_by=request.user).count()

    upcoming_events = Event.objects.filter(
        attendees=request.user,
        event_date__gte=timezone.now()
    ).order_by("event_date")[:5]

    pending_duties = Duty.objects.filter(
        assigned_to=request.user,
        completed=False
    ).order_by("duty_date")[:5]

    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile picture updated successfully!")
            return redirect('profile')
    else:
        form = ProfilePictureForm(instance=member)

    notifications = Notification.objects.filter(
        recipient=member,
        is_read=False
    ).order_by('-created_at')

    context = {
        'member': member,
        'form': form,
        'notifications': notifications,
        'events_attended': events_attended,
        'duties_completed': duties_completed,
        'announcements_count': announcements_count,
        'upcoming_events': upcoming_events,
        'pending_duties': pending_duties,
    }
    return render(request, 'profile.html', context)


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user.member)
    notification.is_read = True
    notification.save()
    return redirect('dashboard')


# -------------------------
# FINANCE VIEWS
# -------------------------

@login_required
@admin_required
def finance_dashboard(request):
    """Admin view for finance department with summary"""
    # Income vs Expense totals
    total_income = FinancialTransaction.objects.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = FinancialTransaction.objects.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance = total_income - total_expense
    
    # Income by sub-type
    income_by_type = {}
    for sub_type, label in FinancialTransaction.INCOME_SUB_TYPES:
        amount = FinancialTransaction.objects.filter(
            transaction_type='income',
            income_sub_type=sub_type
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        income_by_type[sub_type] = {
            'label': label,
            'amount': amount
        }
    
    # Expense by sub-type
    expense_by_type = {}
    for sub_type, label in FinancialTransaction.EXPENSE_SUB_TYPES:
        amount = FinancialTransaction.objects.filter(
            transaction_type='expense',
            expense_sub_type=sub_type
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        expense_by_type[sub_type] = {
            'label': label,
            'amount': amount
        }
    
    # Today's transactions
    today = timezone.now().date()
    today_income = FinancialTransaction.objects.filter(date=today, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    today_expense = FinancialTransaction.objects.filter(date=today, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    today_transactions = FinancialTransaction.objects.filter(date=today).order_by('-recorded_at')
    today_total = today_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Recent transactions (last 30 days)
    thirty_days_ago = today - timezone.timedelta(days=30)
    recent_transactions = FinancialTransaction.objects.filter(
        date__gte=thirty_days_ago
    ).order_by('-date', '-recorded_at')
    
    # Pending invoices (expenses with due date)
    pending_invoices = FinancialTransaction.objects.filter(
        transaction_type='expense',
        is_paid=False,
        due_date__isnull=False,
        due_date__gte=today
    ).count()
    
    overdue_invoices = FinancialTransaction.objects.filter(
        transaction_type='expense',
        is_paid=False,
        due_date__lt=today
    ).count()
    
    # Aging Accounts Receivable (for income)
    ar_0_30 = FinancialTransaction.objects.filter(
        transaction_type='income',
        is_paid=False
    ).filter(date__gte=today - timezone.timedelta(days=30)).aggregate(Sum('amount'))['amount__sum'] or 0
    
    ar_31_60 = FinancialTransaction.objects.filter(
        transaction_type='income',
        is_paid=False
    ).filter(date__lt=today - timezone.timedelta(days=30), date__gte=today - timezone.timedelta(days=60)).aggregate(Sum('amount'))['amount__sum'] or 0
    
    ar_60_plus = FinancialTransaction.objects.filter(
        transaction_type='income',
        is_paid=False
    ).filter(date__lt=today - timezone.timedelta(days=60)).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Budget alerts
    budgets = Budget.objects.filter(is_active=True, period_year=today.year)
    budget_alerts = []
    for budget in budgets:
        variance = budget.get_variance()
        if budget.income_category:
            if variance < -budget.budgeted_amount * 0.1:
                budget_alerts.append({
                    'budget': budget,
                    'message': f"Income {budget.category_name()} is below target by {abs(variance):.2f}",
                    'status': 'danger'
                })
        else:
            if variance < -budget.budgeted_amount * 0.1:
                budget_alerts.append({
                    'budget': budget,
                    'message': f"Expense {budget.category_name()} is over budget by {abs(variance):.2f}",
                    'status': 'danger'
                })
    
    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'income_by_type': income_by_type,
        'expense_by_type': expense_by_type,
        'today_income': today_income,
        'today_expense': today_expense,
        'today_transactions': today_transactions,
        'today_total': today_total,
        'recent_transactions': recent_transactions,
        'pending_invoices': pending_invoices,
        'overdue_invoices': overdue_invoices,
        'ar_0_30': ar_0_30,
        'ar_31_60': ar_31_60,
        'ar_60_plus': ar_60_plus,
        'budget_alerts': budget_alerts,
        'section': 'finance'
    }
    return render(request, 'admin/finance_dashboard.html', context)


@login_required
@admin_required
def finance_add_transaction(request):
    """Add a new financial transaction"""
    if request.method == 'POST':
        form = FinancialTransactionForm(request.POST, request.FILES)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.recorded_by = request.user
            
            if transaction.transaction_type == 'income':
                transaction.is_paid = True
                transaction.paid_date = transaction.date
            
            transaction.save()
            messages.success(request, f"Transaction of {transaction.get_transaction_type_display()} for {transaction.amount} recorded!")
            return redirect('finance_dashboard')
    else:
        form = FinancialTransactionForm()
    
    return render(request, 'admin/finance_add_transaction.html', {'form': form})


@login_required
@admin_required
def finance_transactions(request):
    """View all financial transactions with filtering"""
    transactions = FinancialTransaction.objects.all().order_by('-date', '-recorded_at')
    
    form = FinanceFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('transaction_type'):
            transactions = transactions.filter(transaction_type=form.cleaned_data['transaction_type'])
        if form.cleaned_data.get('payment_method'):
            transactions = transactions.filter(payment_method=form.cleaned_data['payment_method'])
        if form.cleaned_data.get('date_from'):
            transactions = transactions.filter(date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            transactions = transactions.filter(date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data.get('department'):
            transactions = transactions.filter(department=form.cleaned_data['department'])
    
    total_income = transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'transactions': transactions,
        'form': form,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_total': total_income - total_expense,
        'section': 'finance'
    }
    return render(request, 'admin/finance_transactions.html', context)


@login_required
@admin_required
def finance_summary(request):
    """Financial summary with budget vs actual analysis"""
    current_year = timezone.now().year
    
    # Monthly income/expense for current year
    monthly_data = []
    for month in range(1, 13):
        income = FinancialTransaction.objects.filter(
            date__year=current_year,
            date__month=month,
            transaction_type='income'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        expense = FinancialTransaction.objects.filter(
            date__year=current_year,
            date__month=month,
            transaction_type='expense'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Get budget for this month (if exists)
        budget_income = Budget.objects.filter(
            period_year=current_year,
            period_month=month,
            income_category__isnull=False
        ).aggregate(Sum('budgeted_amount'))['budgeted_amount__sum'] or 0
        
        budget_expense = Budget.objects.filter(
            period_year=current_year,
            period_month=month,
            expense_category__isnull=False
        ).aggregate(Sum('budgeted_amount'))['budgeted_amount__sum'] or 0
        
        monthly_data.append({
            'month': month,
            'month_name': timezone.datetime(current_year, month, 1).strftime('%B'),
            'income': income,
            'expense': expense,
            'net': income - expense,
            'budget_income': budget_income,
            'budget_expense': budget_expense,
            'income_variance': income - budget_income,
            'expense_variance': budget_expense - expense,
        })
    
    # Budget vs Actual by category
    budgets = Budget.objects.filter(is_active=True, period_year=current_year)
    budget_analysis = []
    for budget in budgets:
        actual = budget.get_actual_amount()
        variance = budget.get_variance()
        status = budget.get_status()
        budget_analysis.append({
            'budget': budget,
            'actual': actual,
            'variance': variance,
            'status': status,
            'department_display': budget.get_department_display(),
            'category_name': budget.category_name(),
        })
    
    yearly_income = FinancialTransaction.objects.filter(
        transaction_type='income',
        date__year=current_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    yearly_expense = FinancialTransaction.objects.filter(
        transaction_type='expense',
        date__year=current_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'monthly_data': monthly_data,
        'budget_analysis': budget_analysis,
        'yearly_income': yearly_income,
        'yearly_expense': yearly_expense,
        'yearly_net': yearly_income - yearly_expense,
        'current_year': current_year,
        'section': 'finance'
    }
    return render(request, 'admin/finance_summary.html', context)


@login_required
@admin_required
def finance_budget(request):
    """Manage budgets"""
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Budget created successfully!")
            return redirect('finance_budget')
    else:
        form = BudgetForm()
    
    budgets = Budget.objects.all().order_by('-period_year', 'department')
    context = {
        'budgets': budgets,
        'form': form,
        'section': 'finance'
    }
    return render(request, 'admin/finance_budget.html', context)


@login_required
@admin_required
def finance_requisition(request):
    """Expense requisition management"""
    if request.method == 'POST':
        form = ExpenseRequisitionForm(request.POST)
        if form.is_valid():
            requisition = form.save(commit=False)
            requisition.requested_by = request.user
            requisition.status = 'pending'
            requisition.save()
            messages.success(request, "Requisition submitted for approval!")
            return redirect('finance_requisition')
    else:
        form = ExpenseRequisitionForm()
    
    requisitions = ExpenseRequisition.objects.all().order_by('-created_at')
    context = {
        'requisitions': requisitions,
        'form': form,
        'section': 'finance'
    }
    return render(request, 'admin/finance_requisition.html', context)


@login_required
@admin_required
def finance_requisition_approve(request, req_id):
    """Approve or reject a requisition"""
    requisition = get_object_or_404(ExpenseRequisition, id=req_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            requisition.status = 'approved'
            requisition.approved_by = request.user
            requisition.approved_at = timezone.now()
            messages.success(request, f"Requisition '{requisition.title}' approved!")
        elif action == 'reject':
            requisition.status = 'rejected'
            requisition.rejected_reason = request.POST.get('reason', '')
            messages.warning(request, f"Requisition '{requisition.title}' rejected.")
        requisition.save()
        return redirect('finance_requisition')
    
    context = {
        'requisition': requisition,
        'section': 'finance'
    }
    return render(request, 'admin/finance_requisition_approve.html', context)


@login_required
@admin_required
def finance_reconciliation(request):
    """Bank reconciliation management"""
    if request.method == 'POST':
        form = BankReconciliationForm(request.POST)
        if form.is_valid():
            reconciliation = form.save(commit=False)
            reconciliation.reconciled_by = request.user
            reconciliation.difference = reconciliation.statement_balance - reconciliation.ledger_balance
            reconciliation.is_reconciled = True
            reconciliation.save()
            messages.success(request, "Bank reconciliation completed!")
            return redirect('finance_reconciliation')
    else:
        form = BankReconciliationForm()
    
    reconciliations = BankReconciliation.objects.all().order_by('-statement_date')
    context = {
        'reconciliations': reconciliations,
        'form': form,
        'section': 'finance'
    }
    return render(request, 'admin/finance_reconciliation.html', context)
