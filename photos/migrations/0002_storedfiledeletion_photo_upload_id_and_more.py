import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('albums', '0002_album_photo_count_and_more'),
        ('photos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoredFileDeletion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('storage_key', models.CharField(max_length=500, unique=True)),
                ('state', models.CharField(choices=[('pending', 'Pending'), ('failed', 'Failed'), ('deleted', 'Deleted')], default='pending', max_length=20)),
                ('attempt_count', models.PositiveIntegerField(default=0)),
                ('last_error', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['created_at', 'id'],
            },
        ),
        migrations.AddField(
            model_name='photo',
            name='upload_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name='photo',
            constraint=models.UniqueConstraint(condition=models.Q(('upload_id__isnull', False)), fields=('album', 'upload_id'), name='unique_photo_upload_id_per_album'),
        ),
    ]
