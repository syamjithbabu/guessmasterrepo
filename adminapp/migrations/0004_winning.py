# Generated by Django 4.2.5 on 2023-10-24 12:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0001_initial'),
        ('adminapp', '0003_result'),
    ]

    operations = [
        migrations.CreateModel(
            name='Winning',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('number', models.CharField(max_length=3)),
                ('LSK', models.CharField(max_length=100)),
                ('count', models.DecimalField(decimal_places=2, max_digits=10)),
                ('position', models.CharField(max_length=10)),
                ('prize', models.DecimalField(decimal_places=2, max_digits=10)),
                ('commission', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('agent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='website.agent')),
                ('dealer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='website.dealer')),
                ('time', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='adminapp.playtime')),
            ],
        ),
    ]
