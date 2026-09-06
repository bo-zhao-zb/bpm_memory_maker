from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PrintProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(unique=True)),
                ('name', models.CharField(max_length=80)),
                ('width_mm', models.DecimalField(decimal_places=2, max_digits=7)),
                ('height_mm', models.DecimalField(decimal_places=2, max_digits=7)),
                ('active', models.BooleanField(default=True)),
                ('display_order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['display_order', 'name'],
                'constraints': [models.CheckConstraint(condition=models.Q(('height_mm__gt', 0), ('width_mm__gt', 0)), name='print_product_positive_dimensions')],
            },
        ),
    ]
