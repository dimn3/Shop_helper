# Generated by Django 4.0.10 on 2023-04-19 10:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shoppinglist',
            name='recipes',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cart', to='api.recipe', verbose_name='Список покупок'),
        ),
        migrations.AlterField(
            model_name='shoppinglist',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cart', to=settings.AUTH_USER_MODEL, verbose_name='Автор списка покупок'),
        ),
    ]
