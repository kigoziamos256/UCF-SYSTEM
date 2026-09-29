from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import imagekit.models.fields
from imagekit.processors import ResizeToFill


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0011_add_finance_columns'),   # 👈 replace with your LAST migration
        migrations.swappable_dependency('auth.user'),
    ]

    operations = [

        # ========== ServiceSchedule ==========
        migrations.CreateModel(
            name='ServiceSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_type', models.CharField(choices=[
                    ('sunday_first',  'Sunday First Service (8:30 AM – 10:00 AM)'),
                    ('sunday_second', 'Sunday Second Service (11:00 AM – 1:00 PM)'),
                    ('midweek',       'Mid-Week Service (Wednesday 6:00 PM – 8:00 PM)'),
                ], max_length=30, unique=True)),
                ('label', models.CharField(max_length=100)),
                ('day_of_week', models.CharField(max_length=10)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['day_of_week', 'start_time']},
        ),

        # ========== ServiceFlyer ==========
        migrations.CreateModel(
            name='ServiceFlyer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('flyer_image', imagekit.models.fields.ProcessedImageField(
                    blank=True, null=True, upload_to='service_flyers/',
                    processors=[ResizeToFill(1200, 1500)],
                    format='JPEG', options={'quality': 85, 'optimize': True}
                )),
                ('youtube_live_url', models.URLField(blank=True)),
                ('service_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_flyers', to='auth.user'
                )),
                ('service', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='flyers', to='members.serviceschedule'
                )),
            ],
            options={
                'ordering': ['-service_date'],
                'unique_together': {('service', 'service_date')},
            },
        ),

        # ========== ServiceAttendance ==========
        migrations.CreateModel(
            name='ServiceAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_date', models.DateField()),
                ('session', models.CharField(blank=True, choices=[
                    ('first',  'First Service'),
                    ('second', 'Second Service'),
                    ('midweek','Mid-Week Service'),
                ], max_length=10)),
                ('check_in_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True)),
                ('checked_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='checked_service_attendances', to='auth.user'
                )),
                ('member', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='service_attendances', to='members.member'
                )),
                ('service', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attendances', to='members.serviceschedule'
                )),
            ],
            options={
                'ordering': ['-check_in_time'],
                'unique_together': {('service', 'service_date', 'session', 'member')},
            },
        ),

        # ========== GuestAttendance ==========
        migrations.CreateModel(
            name='GuestAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('email', models.EmailField(blank=True)),
                ('service_date', models.DateField()),
                ('session', models.CharField(blank=True, choices=[
                    ('first',  'First Service'),
                    ('second', 'Second Service'),
                    ('midweek','Mid-Week Service'),
                ], max_length=10)),
                ('check_in_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('converted_to_member', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('service', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='guest_attendances', to='members.serviceschedule'
                )),
            ],
            options={'ordering': ['-check_in_time']},
        ),

    ]
