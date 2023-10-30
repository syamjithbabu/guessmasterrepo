# Generated by Django 4.2.5 on 2023-10-30 09:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0005_monitor'),
    ]

    operations = [
        migrations.CreateModel(
            name='CombinedGame',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('LSK', models.CharField(max_length=100)),
                ('number', models.CharField(max_length=100)),
                ('count', models.IntegerField()),
                ('user', models.CharField(max_length=100)),
                ('remaining_limit', models.IntegerField(blank=True, null=True)),
                ('combined', models.BooleanField()),
                ('time', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='adminapp.playtime')),
            ],
        ),
    ]
