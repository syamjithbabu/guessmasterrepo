# Generated by Django 4.2.5 on 2023-10-18 08:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('agent', '0007_rename_total_amount_agentbill_total_c_amount_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('total_c_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_d_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_count', models.DecimalField(decimal_places=0, max_digits=10)),
                ('time_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='adminapp.playtime')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='AgentBill',
        ),
    ]