# Generated by Django 4.0.10 on 2023-04-19 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_rename_recipes_favouriterecipes_recipe'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='favouriterecipes',
            name='recipe_user_unique',
        ),
        migrations.AddConstraint(
            model_name='favouriterecipes',
            constraint=models.UniqueConstraint(fields=('recipe', 'user'), name='recipe_user_unique'),
        ),
    ]
