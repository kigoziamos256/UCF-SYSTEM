from django.db import migrations

def create_default_currency(apps, schema_editor):
    Currency = apps.get_model('members', 'Currency')
    if not Currency.objects.filter(is_default=True).exists():
        Currency.objects.create(
            code='UGX',
            symbol='UGX',
            name='Uganda Shilling',
            is_default=True,
            is_active=True
        )

def reverse_default_currency(apps, schema_editor):
    Currency = apps.get_model('members', 'Currency')
    Currency.objects.filter(code='UGX', is_default=True).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('members', '0009_add_currency_model'),
    ]

    operations = [
        migrations.RunPython(create_default_currency, reverse_default_currency),
    ]
