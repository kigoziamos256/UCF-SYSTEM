from django.contrib.auth import login, logout
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib import messages

from .models import Event, Member, Duty, Announcement, Notification, Attendance, Department, FinancialTransaction
from .forms import (
    EventForm, MemberRegistrationForm, DutyForm, AnnouncementForm,
    DepartmentForm, ProfilePictureForm, UserRegisterForm, AttendanceForm, FinancialTransactionForm  # ✅ Fixed typo here
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
@admin_required
def finance_dashboard(request):
    """Admin view for finance department"""
    finance_staff = Member.objects.filter(role='finance').select_related('user', 'department')
    all_members = Member.objects.count()
    total_events = Event.objects.count()

    context = {
        'finance_staff': finance_staff,
        'all_members': all_members,
        'total_events': total_events,
        'section': 'finance'
    }
    return render(request, 'admin/finance_dashboard.html', context)


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

    # Attendance stats
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

    # Check if user has already marked attendance
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
# FINANCE
# -------------------------

@login_required
@admin_required
def finance_dashboard(request):
    """Admin view for finance department with summary"""
    finance_staff = Member.objects.filter(role='finance').select_related('user', 'department')
    all_members = Member.objects.count()
    total_events = Event.objects.count()
    
    # Get all transactions
    transactions = FinancialTransaction.objects.all().order_by('-date', '-recorded_at')[:50]
    
    # Calculate totals by type
    totals = {
        'tithe': FinancialTransaction.objects.filter(transaction_type='tithe').aggregate(Sum('amount'))['amount__sum'] or 0,
        'offertory': FinancialTransaction.objects.filter(transaction_type='offertory').aggregate(Sum('amount'))['amount__sum'] or 0,
        'donation': FinancialTransaction.objects.filter(transaction_type='donation').aggregate(Sum('amount'))['amount__sum'] or 0,
        'mobile_money': FinancialTransaction.objects.filter(transaction_type='mobile_money').aggregate(Sum('amount'))['amount__sum'] or 0,
        'bank_transfer': FinancialTransaction.objects.filter(transaction_type='bank_transfer').aggregate(Sum('amount'))['amount__sum'] or 0,
        'offering': FinancialTransaction.objects.filter(transaction_type='offering').aggregate(Sum('amount'))['amount__sum'] or 0,
        'special': FinancialTransaction.objects.filter(transaction_type='special').aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    
    # Today's transactions
    today = timezone.now().date()
    today_transactions = FinancialTransaction.objects.filter(date=today).order_by('-recorded_at')
    
    # Total amount
    total_amount = FinancialTransaction.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Last 30 days
    thirty_days_ago = today - timezone.timedelta(days=30)
    recent_transactions = FinancialTransaction.objects.filter(
        date__gte=thirty_days_ago
    ).order_by('-date', '-recorded_at')
    
    context = {
        'finance_staff': finance_staff,
        'all_members': all_members,
        'total_events': total_events,
        'transactions': transactions,
        'today_transactions': today_transactions,
        'recent_transactions': recent_transactions,
        'totals': totals,
        'total_amount': total_amount,
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
    
    # Filtering
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
    
    # Calculate total
    total = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'transactions': transactions,
        'form': form,
        'total': total,
        'section': 'finance'
    }
    return render(request, 'admin/finance_transactions.html', context)


@login_required
@admin_required
def finance_summary(request):
    """Financial summary by month/year with charts"""
    from django.db.models import Sum
    from datetime import datetime
    
    # Get current year
    current_year = datetime.now().year
    
    # Monthly summary for current year
    monthly_data = []
    for month in range(1, 13):
        monthly_total = FinancialTransaction.objects.filter(
            date__year=current_year,
            date__month=month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Get breakdown by type for this month
        tithe = FinancialTransaction.objects.filter(
            date__year=current_year,
            date__month=month,
            transaction_type='tithe'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        offertory = FinancialTransaction.objects.filter(
            date__year=current_year,
            date__month=month,
            transaction_type='offertory'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        donation = FinancialTransaction.objects.filter(
            date__year=current_year,
            date__month=month,
            transaction_type='donation'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        monthly_data.append({
            'month': month,
            'month_name': timezone.datetime(current_year, month, 1).strftime('%B'),
            'total': monthly_total,
            'tithe': tithe,
            'offertory': offertory,
            'donation': donation,
        })
    
    # Yearly totals
    yearly_totals = {
        'tithe': FinancialTransaction.objects.filter(transaction_type='tithe', date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0,
        'offertory': FinancialTransaction.objects.filter(transaction_type='offertory', date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0,
        'donation': FinancialTransaction.objects.filter(transaction_type='donation', date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0,
        'mobile_money': FinancialTransaction.objects.filter(transaction_type='mobile_money', date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0,
        'bank_transfer': FinancialTransaction.objects.filter(transaction_type='bank_transfer', date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0,
        'offering': FinancialTransaction.objects.filter(transaction_type='offering', date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0,
        'special': FinancialTransaction.objects.filter(transaction_type='special', date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    yearly_total = sum(yearly_totals.values())
    
    # Daily summary (today)
    today = timezone.now().date()
    today_total = FinancialTransaction.objects.filter(date=today).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'monthly_data': monthly_data,
        'yearly_totals': yearly_totals,
        'yearly_total': yearly_total,
        'current_year': current_year,
        'today_total': today_total,
        'section': 'finance'
    }
    return render(request, 'admin/finance_summary.html', context)
