# Generated by Django 4.2.7 on 2023-12-09 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0006_combinedgame_cleared'),
    ]

    operations = [
        migrations.AlterField(
            model_name='combinedgame',
            name='cleared',
            field=models.IntegerField(default=0),
        ),
    ]
