import albums.models
import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalog', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('state', models.CharField(choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('in_production', 'In production'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('expired', 'Expired')], default='draft', max_length=20)),
                ('photo_limit', models.PositiveIntegerField(default=albums.models.default_photo_limit, validators=[django.core.validators.MinValueValidator(1)])),
                ('expires_at', models.DateTimeField(default=albums.models.draft_expiry)),
                ('version', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('default_print_product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='catalog.printproduct')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at', '-created_at', 'id'],
                'indexes': [models.Index(fields=['owner', '-updated_at'], name='albums_albu_owner_i_e424f7_idx')],
                'constraints': [models.CheckConstraint(condition=models.Q(('photo_limit__gt', 0)), name='album_positive_limit'), models.CheckConstraint(condition=models.Q(('version__gt', 0)), name='album_positive_version')],
            },
        ),
    ]
