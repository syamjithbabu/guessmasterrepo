# Generated by Django 4.2.5 on 2023-10-27 09:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0001_initial'),
        ('adminapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectionReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('from_or_to', models.CharField(max_length=100)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('agent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='website.agent')),
                ('time', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='adminapp.playtime')),
            ],
        ),
    ]
