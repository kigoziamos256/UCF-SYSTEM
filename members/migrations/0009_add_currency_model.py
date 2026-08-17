# members/migrations/0009_add_currency_model.py
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('members', '0008_finance_models'),  # replace with your last migration
    ]

    operations = [
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='e.g., USD, UGX, EUR, GBP', max_length=10, unique=True)),
                ('symbol', models.CharField(help_text='e.g., $, UGX, €, £', max_length=10)),
                ('name', models.CharField(help_text='e.g., US Dollar, Uganda Shilling', max_length=50)),
                ('is_default', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Currencies',
                'ordering': ['code'],
            },
        ),
    ]
