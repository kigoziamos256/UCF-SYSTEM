from django import forms
from .models import Event, Member, Duty, Announcement, Department, Attendance, FinancialTransaction
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import (
    FinancialTransaction, Budget, ExpenseRequisition, BankReconciliation,
    IncomeCategory, ExpenseCategory, Vendor, Currency
)


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_date', 'location', 'department', 'cover_image']
        widgets = {
            'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class MemberRegistrationForm(forms.ModelForm):
    # Only member-specific fields. User fields (username, email, password)
    # are handled by UserRegisterForm.
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = Member
        fields = ['department', 'profile_picture', 'phone_number']
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DutyForm(forms.ModelForm):
    class Meta:
        model = Duty
        fields = ['title', 'description', 'assigned_to', 'duty_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'duty_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'message', 'department']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'capture': 'camera'  # mobile camera access
            }),
        }


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class FinancialTransactionForm(forms.ModelForm):
    class Meta:
        model = FinancialTransaction
        fields = [
            'transaction_type', 'payment_method', 'amount', 'date',
            'payer_name', 'payer_phone', 'payer_email', 'payer_member',
            'description', 'reference_number', 'notes', 'receipt_image'
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'payer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'payer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'payer_member': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'receipt_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['department', 'income_category', 'expense_category', 'frequency', 'period_month', 'period_year', 'budgeted_amount']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-control'}),
            'income_category': forms.Select(attrs={'class': 'form-control'}),
            'expense_category': forms.Select(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'period_month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'period_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'budgeted_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ExpenseRequisitionForm(forms.ModelForm):
    class Meta:
        model = ExpenseRequisition
        fields = ['title', 'description', 'department', 'expense_category', 'estimated_amount', 'vendor']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'expense_category': forms.Select(attrs={'class': 'form-control'}),
            'estimated_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vendor': forms.Select(attrs={'class': 'form-control'}),
        }


class BankReconciliationForm(forms.ModelForm):
    class Meta:
        model = BankReconciliation
        fields = ['bank_name', 'account_number', 'statement_date', 'statement_balance', 'ledger_balance', 'notes']
        widgets = {
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'statement_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'statement_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ledger_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }



class FinanceFilterForm(forms.Form):
    transaction_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(FinancialTransaction.TRANSACTION_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    payment_method = forms.ChoiceField(
        choices=[('', 'All Methods')] + list(FinancialTransaction.PAYMENT_METHODS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
