# members/migrations/0006_add_finance_and_attendance.py

from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_add_cover_image_...'),  # ← REPLACE with your actual last migration name
    ]

    operations = [
        # 1. Update ROLE_CHOICES to include 'finance'
        migrations.AlterField(
            model_name='member',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Admin'),
                    ('leader', 'Leader'),
                    ('finance', 'Finance'),
                    ('member', 'Member')
                ],
                default='member',
                max_length=50
            ),
        ),
        
        # 2. Create Attendance model
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('present', 'Present'), ('absent', 'Absent'), ('excused', 'Excused'), ('late', 'Late')], default='present', max_length=20)),
                ('check_in_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True, null=True)),
                ('checked_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attendance_checked', to='auth.user')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='members.event')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='members.member')),
            ],
            options={
                'ordering': ['-check_in_time'],
                'unique_together': {('event', 'member')},
            },
        ),
    ]
