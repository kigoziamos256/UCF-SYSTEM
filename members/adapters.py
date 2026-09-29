from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from .models import Member


class UCFSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter that:
    1. Populates User.first_name / last_name from Google.
    2. Copies the Google profile picture URL into Member.
    3. Leaves department blank so the user can pick it later.
    """

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        # Fallback: some Google accounts only return 'name', not first/last
        if not user.first_name and 'name' in data:
            parts = data['name'].split(' ', 1)
            user.first_name = parts[0][:30]
            if len(parts) > 1:
                user.last_name = parts[1][:30]

        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)

        # Ensure Member exists (signal normally creates it)
        member, _ = Member.objects.get_or_create(user=user)

        # Grab the Google picture URL from extra_data
        extra = sociallogin.account.extra_data or {}
        picture_url = extra.get('picture', '')

        # Save it as a temporary avatar URL (as a string note for the profile form)
        # We don't download the image yet — we wait for the user to confirm.
        if picture_url and not member.profile_picture:
            member.avatar_url = picture_url   # see step 6 for model field
            member.save()

        return user
