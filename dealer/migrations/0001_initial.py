# Generated by Django 4.2.5 on 2023-10-22 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DealerGame',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('LSK', models.CharField(max_length=100)),
                ('number', models.CharField(max_length=100)),
                ('count', models.IntegerField()),
                ('d_amount', models.FloatField()),
                ('c_amount', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='DealerGameTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('LSK', models.CharField(max_length=100)),
                ('number', models.CharField(max_length=100)),
                ('count', models.IntegerField()),
                ('d_amount', models.FloatField()),
                ('c_amount', models.FloatField()),
            ],
        ),
    ]
