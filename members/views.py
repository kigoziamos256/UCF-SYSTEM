import os
import base64
from io import BytesIO
from PIL import Image, ImageFilter
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.templatetags.static import static
from xhtml2pdf import pisa
from io import BytesIO

import qrcode
import io
import secrets
import requests
from datetime import time

from .utils import send_ucf_email
from .models import (
    Event, Member, Duty, Announcement, Notification, Attendance, Department,
    FinancialTransaction, Budget, ExpenseRequisition, BankReconciliation,
    Vendor, IncomeCategory, ExpenseCategory, Currency, ServiceSchedule, 
    ServiceFlyer, ServiceAttendance, GuestAttendance, DepartmentPhoto,
    build_member_qr_payload, parse_member_qr_payload,
    ChatRoom, Message, Sermon, ServiceGallery,
    EquipmentCategory, Equipment, EquipmentLoan, ExternalEvent
)

from .forms import (
    EventForm, MemberRegistrationForm, DutyForm, AnnouncementForm,
    DepartmentForm, ProfilePictureForm, UserRegisterForm, AttendanceForm,
    FinancialTransactionForm, BudgetForm, ExpenseRequisitionForm,
    BankReconciliationForm, FinanceFilterForm, ServiceFlyerForm,
    CompleteProfileForm, DepartmentProfileForm, DepartmentPhotoFormSet,
    SermonForm, ServiceGalleryForm, GalleryPhotoFormSet,
    EquipmentForm, EquipmentLoanForm, ExternalEventForm
)


# ============================================================
# DECORATORS
# ============================================================

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

def media_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'member'):
            member = request.user.member
            if member.role == 'admin':
                return view_func(request, *args, **kwargs)
            if member.role == 'leader' and member.department and 'media' in member.department.name.lower():
                return view_func(request, *args, **kwargs)
        raise PermissionDenied("You do not have access to the Media Hub.")
    return wrapper


# ============================================================
# HOME & AUTH
# ============================================================

def home(request):
    return render(request, "home.html")

def custom_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

def make_admin(request):
    if User.objects.filter(is_superuser=True).exists():
        messages.info(request, "Superuser already exists.")
    else:
        User.objects.create_superuser('admin', 'admin@church.com', 'admin123')
        messages.success(request, "Superuser created! Username: admin, Password: admin123")
    return redirect('/admin/')

def create_superuser_temp(request):
    if User.objects.filter(is_superuser=True).exists():
        messages.info(request, "Superuser already exists.")
    else:
        User.objects.create_superuser('admin', 'admin@church.com', 'admin123')
        messages.success(request, "Superuser created! You can now log in at /admin")
    return redirect('home')

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

def custom_csrf_failure(request, reason=""):
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(
        f"CSRF failure: {reason} | "
        f"UA: {request.META.get('HTTP_USER_AGENT', 'unknown')} | "
        f"Referer: {request.META.get('HTTP_REFERER', 'none')} | "
        f"Host: {request.META.get('HTTP_HOST', 'none')}"
    )
    return render(request, 'csrf_failure.html', {'reason': reason}, status=403)

def help_view(request):
    return render(request, 'help.html')

@login_required
def complete_profile_view(request):
    member = request.user.member

    if member.department and request.method == 'GET':
        return redirect('dashboard')

    if request.method == 'POST':
        form = CompleteProfileForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            m = form.save(commit=False)
            if not m.profile_picture and m.avatar_url:
                try:
                    r = requests.get(m.avatar_url, timeout=10)
                    if r.status_code == 200:
                        m.profile_picture.save(f"google_{request.user.id}.jpg", ContentFile(r.content), save=False)
                except Exception:
                    pass
            m.save()
            messages.success(request, "Profile completed. Welcome to UCF!")
            return redirect('dashboard')
    else:
        form = CompleteProfileForm(instance=member)

    return render(request, 'members/complete_profile.html', {'form': form, 'member': member})


# ============================================================
# MEMBER MANAGEMENT
# ============================================================

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
            return render(request, "members/register.html", {"user_form": user_form, "member_form": member_form})
    else:
        user_form = UserRegisterForm()
        member_form = MemberRegistrationForm()

    return render(request, "members/register.html", {"user_form": user_form, "member_form": member_form})

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
    member = get_object_or_404(Member.objects.select_related("user", "department"), id=id)
    upcoming_events = Event.objects.filter(attendees=member.user, event_date__gte=timezone.now()).order_by("event_date")[:5]
    duties = Duty.objects.filter(assigned_to=member.user).order_by("duty_date")[:5]

    context = {"member": member, "upcoming_events": upcoming_events, "duties": duties}
    return render(request, "members/member_detail.html", context)


# ============================================================
# DASHBOARD
# ============================================================

@login_required
def dashboard_view(request):
    user = request.user
    member = user.member
    notifications = member.notifications.filter(is_read=False).order_by('-created_at')

    if member.role == "admin":
        upcoming_events = Event.objects.filter(event_date__gte=timezone.now()).order_by("event_date")[:5]
        announcements = Announcement.objects.all().order_by("-date_posted")[:5]
    elif member.role == "leader":
        upcoming_events = Event.objects.filter(department=member.department, event_date__gte=timezone.now()).order_by("event_date")[:5]
        announcements = Announcement.objects.filter(department=member.department).order_by("-date_posted")[:5]
    else:
        upcoming_events = Event.objects.filter(event_date__gte=timezone.now()).order_by("event_date")[:5]
        announcements = Announcement.objects.all().order_by("-date_posted")[:5]

    pending_duties = Duty.objects.filter(assigned_to=user, completed=False).order_by("duty_date")[:5]

    attendance_present = Attendance.objects.filter(member=member, status='present').count()
    attendance_late = Attendance.objects.filter(member=member, status='late').count()
    attendance_absent = Attendance.objects.filter(member=member, status='absent').count()

    departments = Department.objects.all()[:4]

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
        "departments": departments,
    }
    return render(request, "dashboard.html", context)


# ============================================================
# NOTIFICATIONS & DUTIES
# ============================================================

@login_required
def notifications_api(request):
    member = request.user.member
    qs = member.notifications.filter(is_read=False).order_by('-created_at')
    total = qs.count()
    latest = qs[:10]

    data = {
        'count': total,
        'notifications': [
            {
                'id': n.id,
                'type': n.notification_type,
                'title': n.title or 'New notification',
                'message': n.message,
                'created_at': n.created_at.strftime('%b %d, %H:%M'),
                'url': reverse('mark_notification_read', args=[n.id]),
            }
            for n in latest
        ],
    }
    return JsonResponse(data)

@login_required
@require_POST
def mark_all_notifications_read(request):
    member = request.user.member
    member.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'ok': True})

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user.member)
    notification.is_read = True
    notification.save()
    return redirect('dashboard')

@login_required
@leader_required
def assign_duty(request):
    if request.method == "POST":
        form = DutyForm(request.POST)
        if form.is_valid():
            duty = form.save(commit=False)
            duty.created_by = request.user

            if not duty.department_id:
                try:
                    member = Member.objects.get(user=duty.assigned_to)
                    if member.department_id:
                        duty.department = member.department
                except Member.DoesNotExist:
                    pass

                if not duty.department_id:
                    creator_member = getattr(request.user, 'member', None)
                    if creator_member and creator_member.department_id:
                        duty.department = creator_member.department

                if not duty.department_id:
                    first_dept = Department.objects.first()
                    if first_dept:
                        duty.department = first_dept

                if not duty.department_id:
                    messages.error(request, "Cannot assign duty: no department exists yet. Please create a department first.")
                    return render(request, 'members/assign_duty.html', {'form': form})

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
@require_POST
def mark_duty_complete(request, duty_id):
    duty = get_object_or_404(Duty, id=duty_id)
    is_assignee = (duty.assigned_to == request.user)
    is_admin = hasattr(request.user, 'member') and request.user.member.role == 'admin'

    if not (is_assignee or is_admin):
        messages.error(request, "You can only mark your own duties as complete.")
        return redirect('dashboard')

    if duty.completed:
        messages.info(request, "This duty was already marked complete.")
        return redirect('dashboard')

    duty.completed = True
    duty.completed_at = timezone.now()
    duty.save()

    messages.success(request, f"Duty '{duty.title}' marked as complete. The assigner has been notified.")
    return redirect('dashboard')

@login_required
def duty_detail_view(request, duty_id):
    duty = get_object_or_404(Duty, id=duty_id)
    return render(request, "duty_detail.html", {"duty": duty})


# ============================================================
# EVENTS & ANNOUNCEMENTS
# ============================================================

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

@login_required
def announcements_list(request):
    announcements = Announcement.objects.select_related('created_by', 'department').order_by('-date_posted')

    query = request.GET.get('q', '').strip()
    if query:
        announcements = announcements.filter(
            Q(title__icontains=query) | Q(message__icontains=query) | Q(content__icontains=query)
        )

    dept_id = request.GET.get('department', '').strip()
    if dept_id:
        announcements = announcements.filter(department_id=dept_id)

    important = request.GET.get('important', '').strip()
    if important == '1':
        announcements = announcements.filter(is_important=True)

    paginator = Paginator(announcements, 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'announcements': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'query': query,
        'selected_department': dept_id,
        'important_only': important,
        'departments': Department.objects.all().order_by('name'),
        'total_count': paginator.count,
    }
    return render(request, 'announcements.html', context)

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


# ============================================================
# DEPARTMENT PROFILES
# ============================================================

def department_list_view(request):
    departments = Department.objects.all()
    return render(request, 'departments/list.html', {'departments': departments})

def department_detail_view(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)
    photos = department.photos.all()
    
    can_edit = False
    if request.user.is_authenticated:
        member = request.user.member
        if member.role == 'admin':
            can_edit = True
        elif member.role == 'leader' and member.department == department:
            can_edit = True

    return render(request, 'departments/detail.html', {
        'department': department,
        'photos': photos,
        'can_edit': can_edit
    })

@login_required
def department_edit_view(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)
    member = request.user.member

    if member.role == 'admin':
        pass
    elif member.role == 'leader' and member.department == department:
        pass
    else:
        raise PermissionDenied("You don't have permission to edit this department.")

    if request.method == 'POST':
        form = DepartmentProfileForm(request.POST, request.FILES, instance=department)
        formset = DepartmentPhotoFormSet(request.POST, request.FILES, instance=department)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f"{department.name} profile updated successfully!")
            return redirect('department_detail', dept_id=department.id)
    else:
        form = DepartmentProfileForm(instance=department)
        formset = DepartmentPhotoFormSet(instance=department)

    return render(request, 'departments/edit.html', {
        'department': department,
        'form': form,
        'formset': formset
    })

@login_required
@admin_required
def create_department(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created successfully!")
            return redirect('department_list_view')
    else:
        form = DepartmentForm()

    return render(request, 'members/create_department.html', {'form': form})

@login_required
@admin_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'members/department_list.html', {'departments': departments})


# ============================================================
# PROFILE
# ============================================================

@login_required
def profile_view(request):
    member = request.user.member

    events_attended = request.user.events_joined.count()
    duties_completed = Duty.objects.filter(assigned_to=request.user, completed=True).count()
    announcements_count = Announcement.objects.filter(created_by=request.user).count()

    upcoming_events = Event.objects.filter(attendees=request.user, event_date__gte=timezone.now()).order_by("event_date")[:5]
    pending_duties = Duty.objects.filter(assigned_to=request.user, completed=False).order_by("duty_date")[:5]

    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile picture updated successfully!")
            return redirect('profile')
    else:
        form = ProfilePictureForm(instance=member)

    notifications = Notification.objects.filter(recipient=member, is_read=False).order_by('-created_at')

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


# ============================================================
# FINANCE VIEWS
# ============================================================

@login_required
@admin_required
def finance_dashboard(request):
    total_income = FinancialTransaction.objects.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = FinancialTransaction.objects.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance = total_income - total_expense
    
    income_by_type = {}
    for sub_type, label in FinancialTransaction.INCOME_SUB_TYPES:
        amount = FinancialTransaction.objects.filter(transaction_type='income', income_sub_type=sub_type).aggregate(Sum('amount'))['amount__sum'] or 0
        income_by_type[sub_type] = {'label': label, 'amount': amount}
    
    expense_by_type = {}
    for sub_type, label in FinancialTransaction.EXPENSE_SUB_TYPES:
        amount = FinancialTransaction.objects.filter(transaction_type='expense', expense_sub_type=sub_type).aggregate(Sum('amount'))['amount__sum'] or 0
        expense_by_type[sub_type] = {'label': label, 'amount': amount}
    
    today = timezone.now().date()
    today_income = FinancialTransaction.objects.filter(date=today, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    today_expense = FinancialTransaction.objects.filter(date=today, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    today_transactions = FinancialTransaction.objects.filter(date=today).order_by('-recorded_at')
    today_total = today_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    
    thirty_days_ago = today - timezone.timedelta(days=30)
    recent_transactions = FinancialTransaction.objects.filter(date__gte=thirty_days_ago).order_by('-date', '-recorded_at')
    
    pending_invoices = FinancialTransaction.objects.filter(transaction_type='expense', is_paid=False, due_date__isnull=False, due_date__gte=today).count()
    overdue_invoices = FinancialTransaction.objects.filter(transaction_type='expense', is_paid=False, due_date__lt=today).count()
    
    ar_0_30 = FinancialTransaction.objects.filter(transaction_type='income', is_paid=False).filter(date__gte=today - timezone.timedelta(days=30)).aggregate(Sum('amount'))['amount__sum'] or 0
    ar_31_60 = FinancialTransaction.objects.filter(transaction_type='income', is_paid=False).filter(date__lt=today - timezone.timedelta(days=30), date__gte=today - timezone.timedelta(days=60)).aggregate(Sum('amount'))['amount__sum'] or 0
    ar_60_plus = FinancialTransaction.objects.filter(transaction_type='income', is_paid=False).filter(date__lt=today - timezone.timedelta(days=60)).aggregate(Sum('amount'))['amount__sum'] or 0
    
    budgets = Budget.objects.filter(is_active=True, period_year=today.year)
    budget_alerts = []
    for budget in budgets:
        variance = budget.get_variance()
        if budget.income_category and variance < -budget.budgeted_amount * 0.1:
            budget_alerts.append({'budget': budget, 'message': f"Income {budget.category_name()} is below target by {abs(variance):.2f}", 'status': 'danger'})
        elif budget.expense_category and variance < -budget.budgeted_amount * 0.1:
            budget_alerts.append({'budget': budget, 'message': f"Expense {budget.category_name()} is over budget by {abs(variance):.2f}", 'status': 'danger'})
    
    context = {
        'total_income': total_income, 'total_expense': total_expense, 'net_balance': net_balance,
        'income_by_type': income_by_type, 'expense_by_type': expense_by_type,
        'today_income': today_income, 'today_expense': today_expense,
        'today_transactions': today_transactions, 'today_total': today_total,
        'recent_transactions': recent_transactions,
        'pending_invoices': pending_invoices, 'overdue_invoices': overdue_invoices,
        'ar_0_30': ar_0_30, 'ar_31_60': ar_31_60, 'ar_60_plus': ar_60_plus,
        'budget_alerts': budget_alerts, 'section': 'finance'
    }
    return render(request, 'admin/finance_dashboard.html', context)

@login_required
@admin_required
def finance_add_transaction(request):
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
    transactions = FinancialTransaction.objects.all().order_by('-date', '-recorded_at')
    form = FinanceFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('transaction_type'): transactions = transactions.filter(transaction_type=form.cleaned_data['transaction_type'])
        if form.cleaned_data.get('payment_method'): transactions = transactions.filter(payment_method=form.cleaned_data['payment_method'])
        if form.cleaned_data.get('date_from'): transactions = transactions.filter(date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'): transactions = transactions.filter(date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data.get('department'): transactions = transactions.filter(department=form.cleaned_data['department'])
    
    total_income = transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {'transactions': transactions, 'form': form, 'total_income': total_income, 'total_expense': total_expense, 'net_total': total_income - total_expense, 'section': 'finance'}
    return render(request, 'admin/finance_transactions.html', context)

@login_required
@admin_required
def finance_summary(request):
    current_year = timezone.now().year
    monthly_data = []
    for month in range(1, 13):
        income = FinancialTransaction.objects.filter(date__year=current_year, date__month=month, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        expense = FinancialTransaction.objects.filter(date__year=current_year, date__month=month, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        budget_income = Budget.objects.filter(period_year=current_year, period_month=month, income_category__isnull=False).aggregate(Sum('budgeted_amount'))['budgeted_amount__sum'] or 0
        budget_expense = Budget.objects.filter(period_year=current_year, period_month=month, expense_category__isnull=False).aggregate(Sum('budgeted_amount'))['budgeted_amount__sum'] or 0
        
        monthly_data.append({
            'month': month, 'month_name': timezone.datetime(current_year, month, 1).strftime('%B'),
            'income': income, 'expense': expense, 'net': income - expense,
            'budget_income': budget_income, 'budget_expense': budget_expense,
            'income_variance': income - budget_income, 'expense_variance': budget_expense - expense,
        })
    
    budgets = Budget.objects.filter(is_active=True, period_year=current_year)
    budget_analysis = [{'budget': b, 'actual': b.get_actual_amount(), 'variance': b.get_variance(), 'status': b.get_status(), 'department_display': b.get_department_display(), 'category_name': b.category_name()} for b in budgets]
    
    yearly_income = FinancialTransaction.objects.filter(transaction_type='income', date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0
    yearly_expense = FinancialTransaction.objects.filter(transaction_type='expense', date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {'monthly_data': monthly_data, 'budget_analysis': budget_analysis, 'yearly_income': yearly_income, 'yearly_expense': yearly_expense, 'yearly_net': yearly_income - yearly_expense, 'current_year': current_year, 'section': 'finance'}
    return render(request, 'admin/finance_summary.html', context)

@login_required
@admin_required
def finance_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Budget created successfully!")
            return redirect('finance_budget')
    else:
        form = BudgetForm()
    budgets = Budget.objects.all().order_by('-period_year', 'department')
    return render(request, 'admin/finance_budget.html', {'budgets': budgets, 'form': form, 'section': 'finance'})

@login_required
@admin_required
def finance_requisition(request):
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
    return render(request, 'admin/finance_requisition.html', {'requisitions': requisitions, 'form': form, 'section': 'finance'})

@login_required
@admin_required
def finance_requisition_approve(request, req_id):
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
    return render(request, 'admin/finance_requisition_approve.html', {'requisition': requisition, 'section': 'finance'})

@login_required
@admin_required
def finance_reconciliation(request):
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
    return render(request, 'admin/finance_reconciliation.html', {'reconciliations': reconciliations, 'form': form, 'section': 'finance'})


# ============================================================
# SERVICES & QR ATTENDANCE
# ============================================================

def _current_service_and_session():
    now = timezone.localtime()
    weekday = now.strftime('%A')
    current_time = now.time()

    if weekday == 'Sunday':
        first = ServiceSchedule.objects.filter(service_type='sunday_first', is_active=True).first()
        second = ServiceSchedule.objects.filter(service_type='sunday_second', is_active=True).first()
        if first and first.start_time <= current_time <= first.end_time: return first, 'first'
        if second and second.start_time <= current_time <= second.end_time: return second, 'second'
        if current_time < time(10, 30): return first, 'first'
        return second, 'second'

    if weekday == 'Wednesday':
        return ServiceSchedule.objects.filter(service_type='midweek', is_active=True).first(), 'midweek'

    return None, None

def sunday_service_view(request):
    first = ServiceSchedule.objects.filter(service_type='sunday_first', is_active=True).first()
    second = ServiceSchedule.objects.filter(service_type='sunday_second', is_active=True).first()
    today = timezone.localdate()
    flyer_first = ServiceFlyer.objects.filter(service=first, service_date=today, is_active=True).first() if first else None
    flyer_second = ServiceFlyer.objects.filter(service=second, service_date=today, is_active=True).first() if second else None
    if not flyer_first and first: flyer_first = ServiceFlyer.objects.filter(service=first, is_active=True).first()
    if not flyer_second and second: flyer_second = ServiceFlyer.objects.filter(service=second, is_active=True).first()
    return render(request, 'services/sunday_service.html', {'first': first, 'second': second, 'flyer_first': flyer_first, 'flyer_second': flyer_second, 'today': today})

def midweek_service_view(request):
    mid = ServiceSchedule.objects.filter(service_type='midweek', is_active=True).first()
    flyer = ServiceFlyer.objects.filter(service=mid, is_active=True).first() if mid else None
    return render(request, 'services/midweek_service.html', {'service': mid, 'flyer': flyer})

@login_required
def scanner_view(request):
    service, session = _current_service_and_session()
    return render(request, 'services/scanner.html', {'service': service, 'session': session, 'today': timezone.localdate()})

@login_required
@require_POST
def scan_attendance_api(request):
    import json
    try:
        payload = json.loads(request.body).get('payload', '')
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid request'}, status=400)

    if payload.startswith('UCF-GUEST-'):
        service_type = payload.replace('UCF-GUEST-', '')
        return JsonResponse({'ok': True, 'guest': True, 'redirect': f"/members/services/guest/?service={service_type}"})

    member_id = parse_member_qr_payload(payload)
    if not member_id:
        return JsonResponse({'ok': False, 'error': 'Unknown QR code'}, status=400)

    try:
        member = Member.objects.get(id=member_id)
    except Member.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Member not found'}, status=404)

    service, session = _current_service_and_session()
    if not service:
        return JsonResponse({'ok': False, 'error': 'No active service right now'}, status=400)

    today = timezone.localdate()
    obj, created = ServiceAttendance.objects.get_or_create(service=service, service_date=today, session=session, member=member, defaults={'checked_by': request.user})
    
    return JsonResponse({
        'ok': True, 'created': created,
        'name': member.user.get_full_name() or member.user.username,
        'status': 'Already marked' if not created else 'Marked present',
        'photo': member.get_profile_picture_url(),
    })

def guest_attendance_view(request):
    service_type = request.GET.get('service', 'sunday_first')
    service = ServiceSchedule.objects.filter(service_type=service_type, is_active=True).first()
    if not service:
        messages.error(request, "That service is not currently active.")
        return redirect('sunday_service')

    _, session = _current_service_and_session()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip().lower()

        if not name:
            messages.error(request, "Please enter your name.")
        else:
            user = User.objects.filter(email__iexact=email).first() if email else None
            if not user:
                base = (email.split('@')[0] if email else name.lower().replace(' ', '.'))[:20]
                username = base
                i = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base}{i}"
                    i += 1

                temp_pass = secrets.token_urlsafe(8)
                user = User.objects.create_user(username=username, email=email or f"{username}@guest.ucf", password=temp_pass, first_name=name.split()[0][:30], last_name=(" ".join(name.split()[1:])[:30] if len(name.split()) > 1 else ""))
                user.member.phone_number = phone
                user.member.save()

            ServiceAttendance.objects.get_or_create(service=service, service_date=timezone.localdate(), session=session, member=user.member)
            GuestAttendance.objects.create(name=name, phone=phone, email=email, service=service, service_date=timezone.localdate(), session=session, converted_to_member=True)

            messages.success(request, f"Welcome, {name}! Your attendance is recorded.")
            return redirect('sunday_service' if 'sunday' in service_type else 'midweek_service')

    return render(request, 'services/guest_attendance.html', {'service': service, 'session': session})

@login_required
def member_qr_view(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    img = qrcode.make(build_member_qr_payload(member))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return HttpResponse(buf.getvalue(), content_type='image/png')

@login_required
def my_qr_view(request):
    return render(request, 'services/my_qr.html', {'member': request.user.member})

@login_required
@admin_required
def upload_flyer(request):
    if request.method == 'POST':
        form = ServiceFlyerForm(request.POST, request.FILES)
        if form.is_valid():
            flyer = form.save(commit=False)
            flyer.created_by = request.user
            flyer.save()
            messages.success(request, "Flyer published!")
            return redirect('sunday_service' if 'sunday' in flyer.service.service_type else 'midweek_service')
    else:
        form = ServiceFlyerForm()
    return render(request, 'services/upload_flyer.html', {'form': form})

@login_required
@admin_required
def entrance_qr_view(request):
    schedules = ServiceSchedule.objects.filter(is_active=True)
    return render(request, 'services/entrance_qr.html', {'schedules': schedules, 'base_url': request.build_absolute_uri('/').rstrip('/')})

@login_required
@admin_required
def entrance_qr_image(request, service_type):
    service = ServiceSchedule.objects.filter(service_type=service_type, is_active=True).first()
    if not service:
        return HttpResponse("Service not found", status=404)

    guest_path = reverse('guest_attendance') + f"?service={service_type}"
    full_url = request.build_absolute_uri(guest_path)

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=12, border=2)
    qr.add_data(full_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#6B1F2E", back_color="white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type="image/png")

@login_required
@admin_required
def attendance_report_view(request):
    from_date = request.GET.get('from')
    to_date = request.GET.get('to')
    service_id = request.GET.get('service')
    session = request.GET.get('session')

    qs = ServiceAttendance.objects.select_related('member__user', 'service', 'checked_by').order_by('-service_date', 'session', 'member__user__first_name')

    if from_date: qs = qs.filter(service_date__gte=from_date)
    if to_date: qs = qs.filter(service_date__lte=to_date)
    if service_id: qs = qs.filter(service_id=service_id)
    if session: qs = qs.filter(session=session)

    summary = {
        'total': qs.count(),
        'unique_members': qs.values('member').distinct().count(),
        'first': qs.filter(session='first').count(),
        'second': qs.filter(session='second').count(),
        'midweek': qs.filter(session='midweek').count(),
    }

    context = {
        'attendances': qs[:500], 'summary': summary,
        'schedules': ServiceSchedule.objects.filter(is_active=True),
        'from_date': from_date or '', 'to_date': to_date or '',
        'selected_service': service_id or '', 'selected_session': session or '',
    }
    return render(request, 'services/attendance_report.html', context)

@login_required
@admin_required
def attendance_export_csv(request):
    import csv
    from_date = request.GET.get('from')
    to_date = request.GET.get('to')
    service_id = request.GET.get('service')
    session = request.GET.get('session')

    qs = ServiceAttendance.objects.select_related('member__user', 'service').order_by('-service_date', 'session', 'member__user__first_name')

    if from_date: qs = qs.filter(service_date__gte=from_date)
    if to_date: qs = qs.filter(service_date__lte=to_date)
    if service_id: qs = qs.filter(service_id=service_id)
    if session: qs = qs.filter(session=session)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{timezone.localdate()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Service', 'Session', 'Member Name', 'Email', 'Phone', 'Check-in Time', 'Recorded By'])
    for a in qs:
        writer.writerow([
            a.service_date, a.service.label, a.get_session_display() if hasattr(a, 'get_session_display') else a.session,
            a.member.user.get_full_name() or a.member.user.username, a.member.user.email, a.member.phone_number,
            a.check_in_time.strftime('%Y-%m-%d %H:%M'),
            (a.checked_by.get_full_name() or a.checked_by.username) if a.checked_by else '—',
        ])
    return response

# ============================================================
# PDF GENERATION
# ============================================================

@login_required
@admin_required
def download_attendance_pdf(request):
    from io import BytesIO

    from_date = request.GET.get('from')
    to_date = request.GET.get('to')
    service_id = request.GET.get('service')
    session = request.GET.get('session')

    qs = ServiceAttendance.objects.select_related('member__user', 'service').order_by('member__user__first_name')

    if from_date: qs = qs.filter(service_date__gte=from_date)
    if to_date: qs = qs.filter(service_date__lte=to_date)
    if service_id: qs = qs.filter(service_id=service_id)
    if session: qs = qs.filter(session=session)

    summary = {
        'total': qs.count(),
        'unique_members': qs.values('member').distinct().count(),
        'first': qs.filter(session='first').count(),
        'second': qs.filter(session='second').count(),
        'midweek': qs.filter(session='midweek').count(),
    }

    logo_url = request.build_absolute_uri(static('images/ucf-logo.png'))

    # 👇 Generate a faded, blurred watermark (in-memory, no file saved)
    watermark_uri = None
    try:
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'ucf-logo.png')
        with Image.open(logo_path).convert("RGBA") as logo:
            # Reduce opacity to ~6% so it's a soft ghost
            alpha = logo.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.03))
            logo.putalpha(alpha)

            # Apply a gentle blur
            logo = logo.filter(ImageFilter.GaussianBlur(radius=6))

            # Encode as base64 data URI
            buf = BytesIO()
            logo.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            watermark_uri = f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"⚠️ Watermark generation failed: {e}")

    context = {
        'attendances': qs,
        'summary': summary,
        'logo_url': logo_url,
        'watermark_uri': watermark_uri,   # 👈 new
        'generated_on': timezone.now(),
        'from_date': from_date,
        'to_date': to_date,
        'generated_by': request.user.get_full_name() or request.user.username,
    }

    html_string = render_to_string('services/attendance_pdf.html', context, request=request)

    result = BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=result)

    if result.getbuffer().nbytes == 0:
        messages.error(request, "There was a problem generating the PDF. Please try again.")
        return redirect('attendance_report')

    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    filename = f"UCF_Attendance_{timezone.localdate()}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ============================================================
# EMAIL REPORTS
# ============================================================

@login_required
def email_attendance_report(request):
    if not (request.user.member.role in ['admin', 'leader']):
        raise PermissionDenied
        
    today = timezone.localdate()
    attendance = ServiceAttendance.objects.filter(service_date=today)
    
    if not attendance.exists():
        messages.warning(request, "No attendance recorded today yet.")
        return redirect('dashboard')

    total = attendance.count()
    unique = attendance.values('member').distinct().count()
    first = attendance.filter(session='first').count()
    second = attendance.filter(session='second').count()
    midweek = attendance.filter(session='midweek').count()

    report_text = (
        f"UCF Attendance Report for {today.strftime('%B %d, %Y')}\n\n"
        f"Total Check-ins: {total}\n"
        f"Unique Members: {unique}\n\n"
        f"First Service: {first}\n"
        f"Second Service: {second}\n"
        f"Mid-Week: {midweek}\n\n"
        f"Please log in to the app for the full detailed list."
    )

    recipients = list(Member.objects.filter(role='admin').values_list('user__email', flat=True))
    usher_dept = Department.objects.filter(name__icontains='usher').first()
    if usher_dept:
        usher_leaders = usher_dept.members.filter(role__in=['leader', 'admin']).values_list('user__email', flat=True)
        recipients.extend(usher_leaders)

    recipients = [email for email in set(recipients) if email]
    if recipients:
        send_ucf_email(f"Attendance Report - {today}", report_text, recipients)
        messages.success(request, f"Attendance report emailed to {len(recipients)} recipients.")
    else:
        messages.error(request, "No valid email addresses found for Admins or Usher Leaders.")

    return redirect('dashboard')


# ============================================================
# CHAT SYSTEM
# ============================================================

@login_required
def chat_dashboard(request):
    user = request.user
    member = user.member

    direct_rooms = ChatRoom.objects.filter(room_type='direct', participants=user).order_by('-created_at')

    dept_room = None
    if member.department:
        dept_room, _ = ChatRoom.objects.get_or_create(
            room_type='department',
            department=member.department,
            defaults={'name': f"{member.department.name} Chat"}
        )

    leaders_room = None
    if member.role in ['admin', 'leader']:
        leaders_room, _ = ChatRoom.objects.get_or_create(
            room_type='leaders',
            defaults={'name': "All Leaders Chat"}
        )

    admins_room = None
    if member.role == 'admin':
        admins_room, _ = ChatRoom.objects.get_or_create(
            room_type='admins',
            defaults={'name': "Admins Only Chat"}
        )

    return render(request, 'chat/dashboard.html', {
        'direct_rooms': direct_rooms,
        'dept_room': dept_room,
        'leaders_room': leaders_room,
        'admins_room': admins_room,
    })

@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    user = request.user
    member = user.member

    if room.room_type == 'direct' and user not in room.participants.all():
        raise PermissionDenied
    elif room.room_type == 'department' and member.department != room.department:
        raise PermissionDenied
    elif room.room_type == 'leaders' and member.role not in ['admin', 'leader']:
        raise PermissionDenied
    elif room.room_type == 'admins' and member.role != 'admin':
        raise PermissionDenied

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            msg = Message.objects.create(room=room, sender=user, content=content)
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': msg.content,
                    'sender_id': user.id,
                    'sender_name': user.get_full_name() or user.username,
                    'time': msg.timestamp.strftime('%H:%M')
                })
            
            return redirect('chat_room', room_id=room.id)

    messages_list = room.messages.all().order_by('timestamp')
    return render(request, 'chat/room.html', {'room': room, 'messages': messages_list})

@login_required
def start_direct_chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    if other_user == request.user:
        messages.error(request, "You cannot message yourself.")
        return redirect('member_list')

    room = ChatRoom.objects.filter(room_type='direct', participants=request.user).filter(participants=other_user).first()
    
    if not room:
        room = ChatRoom.objects.create(
            room_type='direct',
            name=f"{request.user.username} & {other_user.username}"
        )
        room.participants.add(request.user, other_user)

    return redirect('chat_room', room_id=room.id)


# ============================================================
# MEDIA DEPARTMENT (Equipment & Events)
# ============================================================

@login_required
@media_required
def media_dashboard(request):
    categories = EquipmentCategory.objects.all()
    total_equipment = Equipment.objects.count()
    lent_equipment = Equipment.objects.filter(status='lent').count()
    
    active_loans = EquipmentLoan.objects.filter(actual_return__isnull=True).order_by('expected_return')
    
    today = timezone.now().date()
    upcoming_events = ExternalEvent.objects.filter(event_date__gte=today, is_completed=False).order_by('event_date')

    return render(request, 'media/dashboard.html', {
        'categories': categories,
        'total_equipment': total_equipment,
        'lent_equipment': lent_equipment,
        'active_loans': active_loans,
        'upcoming_events': upcoming_events,
    })

@login_required
@media_required
def equipment_list(request):
    categories = EquipmentCategory.objects.prefetch_related('equipment').all()
    return render(request, 'media/equipment_list.html', {'categories': categories})

@login_required
@media_required
def equipment_add(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Equipment added successfully.")
            return redirect('equipment_list')
    else:
        form = EquipmentForm()
    return render(request, 'media/equipment_form.html', {'form': form, 'title': 'Add New Equipment'})

@login_required
@media_required
def lend_equipment(request):
    if request.method == 'POST':
        form = EquipmentLoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.authorized_by = request.user
            loan.save()
            
            loan.equipment.status = 'lent'
            loan.equipment.save()
            
            messages.success(request, f"{loan.equipment.name} lent to {loan.borrower_name}.")
            return redirect('media_dashboard')
    else:
        form = EquipmentLoanForm()
    return render(request, 'media/equipment_form.html', {'form': form, 'title': 'Lend Equipment'})

@login_required
@media_required
@require_POST
def return_equipment(request, loan_id):
    loan = get_object_or_404(EquipmentLoan, id=loan_id)
    if not loan.actual_return:
        loan.actual_return = timezone.now()
        loan.save()
        
        loan.equipment.status = 'available'
        loan.equipment.save()
        messages.success(request, f"{loan.equipment.name} returned successfully.")
    return redirect('media_dashboard')

@login_required
@media_required
def external_events_list(request):
    events = ExternalEvent.objects.all().order_by('-event_date')
    return render(request, 'media/external_events.html', {'events': events})

@login_required
@media_required
def add_external_event(request):
    if request.method == 'POST':
        form = ExternalEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, "External event registered.")
            return redirect('external_events_list')
    else:
        form = ExternalEventForm()
    return render(request, 'media/equipment_form.html', {'form': form, 'title': 'Register External Event'})


# ============================================================
# SERMONS & GALLERY
# ============================================================

def sermon_list(request):
    sermons = Sermon.objects.all()
    return render(request, 'media/sermon_list.html', {'sermons': sermons})

def sermon_detail(request, sermon_id):
    sermon = get_object_or_404(Sermon, id=sermon_id)
    return render(request, 'media/sermon_detail.html', {'sermon': sermon})

@login_required
@admin_required
def add_sermon(request):
    if request.method == 'POST':
        form = SermonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sermon uploaded!")
            return redirect('sermon_list')
    else:
        form = SermonForm()
    return render(request, 'media/add_sermon.html', {'form': form})

def gallery_list(request):
    galleries = ServiceGallery.objects.prefetch_related('photos').all()
    return render(request, 'media/gallery_list.html', {'galleries': galleries})

def gallery_detail(request, gallery_id):
    gallery = get_object_or_404(ServiceGallery, id=gallery_id)
    return render(request, 'media/gallery_detail.html', {'gallery': gallery})

@login_required
@admin_required
def add_gallery(request):
    if request.method == 'POST':
        form = ServiceGalleryForm(request.POST)
        formset = GalleryPhotoFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            gallery = form.save()
            formset.instance = gallery
            formset.save()
            messages.success(request, "Gallery created!")
            return redirect('gallery_list')
    else:
        form = ServiceGalleryForm()
        formset = GalleryPhotoFormSet()
    return render(request, 'media/add_gallery.html', {'form': form, 'formset': formset})
