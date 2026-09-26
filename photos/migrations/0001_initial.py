import django.db.models.deletion
import photos.models
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('albums', '0002_album_photo_count_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('original_filename', models.CharField(max_length=255)),
                ('state', models.CharField(choices=[('processing', 'Processing'), ('ready', 'Ready'), ('failed', 'Failed')], default='processing', max_length=20)),
                ('width', models.PositiveIntegerField()),
                ('height', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('album', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='albums.album')),
            ],
            options={
                'ordering': ['display_order', 'created_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='PhotoAsset',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('kind', models.CharField(choices=[('original', 'Original'), ('preview', 'Preview'), ('ai_improved', 'AI improved')], max_length=20)),
                ('file', models.FileField(max_length=500, upload_to=photos.models.private_asset_path)),
                ('checksum', models.CharField(max_length=64)),
                ('media_type', models.CharField(max_length=80)),
                ('width', models.PositiveIntegerField()),
                ('height', models.PositiveIntegerField()),
                ('byte_size', models.PositiveBigIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='photos.photo')),
            ],
            options={
                'ordering': ['created_at', 'id'],
            },
        ),
        migrations.AddIndex(
            model_name='photo',
            index=models.Index(fields=['album', 'display_order'], name='photos_phot_album_i_e8c750_idx'),
        ),
        migrations.AddConstraint(
            model_name='photoasset',
            constraint=models.UniqueConstraint(condition=models.Q(('kind', 'original')), fields=('photo',), name='one_original_asset_per_photo'),
        ),
        migrations.AddConstraint(
            model_name='photoasset',
            constraint=models.UniqueConstraint(condition=models.Q(('kind', 'preview')), fields=('photo',), name='one_preview_asset_per_photo'),
        ),
    ]
