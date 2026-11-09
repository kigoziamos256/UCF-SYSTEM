from django.db import migrations, models
import imagekit.models.fields
from imagekit.processors import ResizeToFill

class Migration(migrations.Migration):

    dependencies = [
        ('members', '0013_member_avatar_urls.py'),  # 👈 CHANGE THIS to your actual last migration name!
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='leadership_structure',
            field=models.TextField(blank=True, help_text='Names of leaders and units'),
        ),
        migrations.AddField(
            model_name='department',
            name='profile_writeup',
            field=models.TextField(blank=True, help_text='Introduction, purpose, and responsibilities'),
        ),
        migrations.AddField(
            model_name='department',
            name='stories_and_experiences',
            field=models.TextField(blank=True, help_text='Testimonies and stories'),
        ),
        migrations.AddField(
            model_name='department',
            name='cover_image',
            field=imagekit.models.fields.ProcessedImageField(blank=True, null=True, upload_to='department_covers/', processors=[ResizeToFill(800, 400)], format='JPEG', options={'quality': 85}),
        ),
        migrations.AddField(
            model_name='department',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.CreateModel(
            name='DepartmentPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', imagekit.models.fields.ProcessedImageField(upload_to='department_gallery/', processors=[ResizeToFill(800, 600)], format='JPEG', options={'quality': 85})),
                ('caption', models.CharField(blank=True, help_text="e.g., 'Youth Camp 2026'", max_length=200)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='members.department')),
            ],
        ),
    ]
