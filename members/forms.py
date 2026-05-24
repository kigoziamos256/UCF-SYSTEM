from django import forms
from .models import Event
from django.contrib.auth.models import User
from .models import Member
from .models import Duty
from .models import Announcement
from .models import Department
from django.contrib.auth.forms import UserCreationForm

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_date', 'location', 'department']
        widgets = {
            'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

class MemberRegistrationForm(forms.ModelForm):

    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Member
        fields = ['department']

    def save(self, commit=True):

        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )

        member = super().save(commit=False)
        member.user = user
        member.role = 'member'

        if commit:
            member.save()

        return member

class DutyForm(forms.ModelForm):

    class Meta:
        model = Duty

        fields = [
            'title',
            'description',
            'assigned_to',
            'duty_date'
        ]

        widgets = {
            'duty_date': forms.DateInput(attrs={'type': 'date'})
        }


class AnnouncementForm(forms.ModelForm):

    class Meta:
        model = Announcement

        fields = [
            'title',
            'message'
        ]

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={
                'accept': 'image/*',
                'capture': 'camera'  # enables camera capture on mobile
            }),
        }

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class MemberRegistrationForm(forms.ModelForm):

    class Meta:
        model = Member
        fields = ['department', 'profile_picture']