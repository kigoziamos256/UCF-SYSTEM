# members/migrations/0006_add_cover_image.py

from django.db import migrations
import imagekit.models.fields

class Migration(migrations.Migration):

    dependencies = [
        ('members', '0005_alter_announcement_options_alter_duty_options_and_more'),  # ← REPLACE with your actual last migration name
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='cover_image',
            field=imagekit.models.fields.ProcessedImageField(
                blank=True,
                null=True,
                upload_to='event_covers/',
                processors=[ResizeToFill(800, 400)],
                format='JPEG',
                options={'quality': 85}
            ),
        ),
    ]
