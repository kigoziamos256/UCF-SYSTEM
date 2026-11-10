import django.db.models.deletion
from django.db import migrations, models
import imagekit.models.fields
from imagekit.processors import ResizeToFill

class Migration(migrations.Migration):

    dependencies = [
        ('members', '0016_chat_system'), # 👈 Check this matches your last migration
    ]

    operations = [
        migrations.CreateModel(
            name='Sermon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('preacher', models.CharField(max_length=100)),
                ('date_preached', models.DateField()),
                ('youtube_url', models.URLField(help_text='Paste the full YouTube video link')),
                ('notes', models.TextField(blank=True, help_text='Sermon outline or main points')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-date_preached']},
        ),
        migrations.CreateModel(
            name='ServiceGallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('service_date', models.DateField()),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-service_date'],
                'verbose_name_plural': 'Service Galleries',
            },
        ),
        migrations.CreateModel(
            name='GalleryPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', imagekit.models.fields.ProcessedImageField(upload_to='service_gallery/', processors=[ResizeToFill(1000, 1000)], format='JPEG', options={'quality': 85})),
                ('caption', models.CharField(blank=True, max_length=200)),
                ('gallery', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='members.servicegallery')),
            ],
        ),
    ]
