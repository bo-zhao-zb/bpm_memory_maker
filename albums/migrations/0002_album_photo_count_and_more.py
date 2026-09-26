from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('albums', '0001_initial'),
        ('catalog', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='album',
            name='photo_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddConstraint(
            model_name='album',
            constraint=models.CheckConstraint(condition=models.Q(('photo_count__lte', models.F('photo_limit'))), name='album_photo_count_within_limit'),
        ),
    ]
