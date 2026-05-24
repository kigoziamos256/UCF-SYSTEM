from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Member(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('leader', 'Leader'),
        ('member', 'Member'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='member')
    
    # Single profile picture field with ImageKit processing
    profile_picture = ProcessedImageField(
        upload_to='profile_pics/',
        processors=[ResizeToFill(300, 300)],  # crops to 300x300 square
        format='JPEG',
        options={'quality': 90},
        null=True,
        blank=True
    )
    
    # Track when profile picture was last updated
    profile_picture_updated_at = models.DateTimeField(null=True, blank=True)
    
    # Additional profile fields you might want
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_profile_picture_url(self):
        """Returns profile picture URL or default avatar with initials"""
        if self.profile_picture and hasattr(self.profile_picture, 'url') and self.profile_picture.name:
            return self.profile_picture.url
        
        # Generate avatar with initials using UI Avatars service
        initials = self.get_initials()
        return f"https://ui-avatars.com/api/?name={initials}&size=300&background=random&color=fff&length=2&font-size=0.5"
    
    def get_initials(self):
        """Get user initials for avatar"""
        full_name = self.user.get_full_name()
        if full_name:
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                return f"{name_parts[0][0]}{name_parts[-1][0]}".upper()
            return name_parts[0][:2].upper()
        else:
            # Use username if no full name
            username = self.user.username
            return username[:2].upper()


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateTimeField()  # Changed to DateTimeField for better precision
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events_created")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, related_name="events")
    location = models.CharField(max_length=200)
    attendees = models.ManyToManyField(User, blank=True, related_name="events_joined")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['event_date']

    def __str__(self):
        return self.title
    
    def get_attendee_count(self):
        return self.attendees.count()


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


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    content = models.TextField()  # You might want to consolidate message and content
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
    
    # Optional link to related object
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


# Signal to automatically create Member profile when User is created
@receiver(post_save, sender=User)
def create_member_profile(sender, instance, created, **kwargs):
    """Create a Member instance whenever a new User is created"""
    if created:
        Member.objects.create(user=instance)
    else:
        # Ensure member exists for existing users (in case signal was missed)
        Member.objects.get_or_create(user=instance)


# Signal to save Member when User is saved
@receiver(post_save, sender=User)
def save_member_profile(sender, instance, **kwargs):
    """Save the Member instance when the User is saved"""
    if hasattr(instance, 'member'):
        instance.member.save()


# Signal to update profile_picture_updated_at when profile picture changes
@receiver(post_save, sender=Member)
def update_profile_picture_timestamp(sender, instance, **kwargs):
    """Update the timestamp when profile picture changes"""
    if instance.profile_picture and not instance.profile_picture_updated_at:
        instance.profile_picture_updated_at = timezone.now()
        # Avoid recursion by using update() instead of save()
        Member.objects.filter(pk=instance.pk).update(profile_picture_updated_at=timezone.now())


# Signal to create notification for new events
@receiver(post_save, sender=Event)
def notify_new_event(sender, instance, created, **kwargs):
    """Send notification to relevant members when new event is created"""
    if created:
        # Determine recipients based on event department
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


# Signal to create notification for new duties
@receiver(post_save, sender=Duty)
def notify_new_duty(sender, instance, created, **kwargs):
    """Send notification when new duty is assigned"""
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
            pass  # Handle case where user doesn't have a member profile


# Signal to create notification for new announcements
@receiver(post_save, sender=Announcement)
def notify_new_announcement(sender, instance, created, **kwargs):
    """Send notification when new announcement is posted"""
    if created:
        # Determine recipients based on announcement department
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


# Signal to mark duty as completed
@receiver(post_save, sender=Duty)
def check_duty_completion(sender, instance, **kwargs):
    """Send notification when duty is marked as completed"""
    if instance.completed and not instance.completed_at:
        instance.completed_at = timezone.now()
        Duty.objects.filter(pk=instance.pk).update(completed_at=timezone.now())
        
        # Notify the assigner or admin that duty is completed
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
            pass  # Handle if created_by doesn't exist or has no member profile