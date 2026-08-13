from django.db import migrations, models
import django.utils.timezone
import imagekit.models.fields

class Migration(migrations.Migration):

    dependencies = [
        ('members', '0007_add_finance_and_attendance'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinancialTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('tithe', 'Tithe'), ('offertory', 'Offertory'), ('mobile_money', 'Mobile Money'), ('bank_transfer', 'Bank Transfer'), ('donation', 'Donation'), ('offering', 'Offering'), ('special', 'Special Offering')], max_length=50)),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('mobile_money', 'Mobile Money'), ('bank_transfer', 'Bank Transfer'), ('cheque', 'Cheque'), ('card', 'Card')], default='cash', max_length=50)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('payer_name', models.CharField(max_length=200)),
                ('payer_phone', models.CharField(blank=True, max_length=20)),
                ('payer_email', models.EmailField(blank=True, max_length=254)),
                ('description', models.TextField(blank=True)),
                ('reference_number', models.CharField(blank=True, help_text='Transaction reference or receipt number', max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('receipt_image', imagekit.models.fields.ProcessedImageField(blank=True, null=True, upload_to='finance/receipts/', processors=[ResizeToFill(800, 600)], format='JPEG', options={'quality': 85})),
                ('payer_member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='members.member')),
                ('recorded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_transactions', to='auth.user')),
            ],
            options={
                'verbose_name': 'Financial Transaction',
                'verbose_name_plural': 'Financial Transactions',
                'ordering': ['-date', '-recorded_at'],
            },
        ),
        migrations.CreateModel(
            name='FinanceSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('month', models.IntegerField(blank=True, null=True)),
                ('total_tithe', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_offertory', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_donations', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_mobile_money', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_bank_transfer', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_offering', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_special', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-year', '-month'],
                'unique_together': {('year', 'month')},
            },
        ),
    ]
