# Generated by Django 4.2.5 on 2023-10-17 13:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('agent', '0005_rename_time_agentbill_time_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='agentbill',
            name='data',
        ),
    ]