import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('members', '0015_media_department'),  # 👈 Depends on the file we just created above
    ]

    operations = [
        migrations.CreateModel(
            name='ChatRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('room_type', models.CharField(choices=[('direct', 'Direct Message'), ('department', 'Department Group'), ('leaders', 'All Leaders'), ('admins', 'All Admins')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='members.department')),
                ('participants', models.ManyToManyField(blank=True, related_name='chat_rooms', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='members.chatroom')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
    ]
