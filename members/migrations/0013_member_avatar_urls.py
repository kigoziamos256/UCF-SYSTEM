from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0012_services'),   # 👈 your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='avatar_url',
            field=models.URLField(blank=True, help_text='Temporary Google avatar URL'),
        ),
    ]
