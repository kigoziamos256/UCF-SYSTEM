from django import forms
from .models import Event, Member, Duty, Announcement, Department
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_date', 'location', 'department', 'cover_image']  # added cover_image
        widgets = {
            'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class MemberRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = Member
        fields = ['department', 'profile_picture']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )
        
        # Set first and last name if provided
        if self.cleaned_data.get('first_name'):
            user.first_name = self.cleaned_data['first_name']
        if self.cleaned_data.get('last_name'):
            user.last_name = self.cleaned_data['last_name']
        user.save()

        member = super().save(commit=False)
        member.user = user
        member.role = 'member'
        
        if self.cleaned_data.get('phone_number'):
            member.phone_number = self.cleaned_data['phone_number']

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
            'duty_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            'title',
            'message',
            'department'
        ]
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
                'capture': 'camera'  # enables camera capture on mobile
            }),
        }


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
