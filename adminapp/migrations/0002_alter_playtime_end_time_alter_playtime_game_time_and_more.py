# Generated by Django 4.2.5 on 2023-10-26 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='playtime',
            name='end_time',
            field=models.TimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='playtime',
            name='game_time',
            field=models.TimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='playtime',
            name='start_time',
            field=models.TimeField(auto_now=True),
        ),
    ]
