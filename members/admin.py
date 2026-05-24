from django.contrib import admin
from .models import Member, Department
from .models import Event
from .models import Announcement

admin.site.register(Member)
admin.site.register(Department)
admin.site.register(Event)
admin.site.register(Announcement)