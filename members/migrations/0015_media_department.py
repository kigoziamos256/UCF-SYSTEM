import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('members', '0014_department_profiles'),  # 👈 Check this name matches your last migration!
    ]

    operations = [
        migrations.CreateModel(
            name='EquipmentCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={'verbose_name_plural': 'Equipment Categories'},
        ),
        migrations.CreateModel(
            name='ExternalEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('event_date', models.DateField()),
                ('location', models.CharField(max_length=200)),
                ('services_offered', models.CharField(help_text='e.g., Sound, Lighting, Video', max_length=200)),
                ('contact_person', models.CharField(max_length=100)),
                ('contact_phone', models.CharField(max_length=20)),
                ('is_completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-event_date']},
        ),
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('serial_number', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('status', models.CharField(choices=[('available', 'Available'), ('lent', 'Lent Out'), ('maintenance', 'Under Maintenance')], default='available', max_length=20)),
                ('purchase_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='equipment', to='members.equipmentcategory')),
            ],
            options={'ordering': ['category__name', 'name']},
        ),
        migrations.CreateModel(
            name='EquipmentLoan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('borrower_name', models.CharField(max_length=100)),
                ('borrower_phone', models.CharField(max_length=20)),
                ('date_lent', models.DateTimeField(default=django.utils.timezone.now)),
                ('expected_return', models.DateTimeField()),
                ('actual_return', models.DateTimeField(blank=True, null=True)),
                ('authorized_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authorized_loans', to=settings.AUTH_USER_MODEL)),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loans', to='members.equipment')),
            ],
            options={'ordering': ['-date_lent']},
        ),
    ]
