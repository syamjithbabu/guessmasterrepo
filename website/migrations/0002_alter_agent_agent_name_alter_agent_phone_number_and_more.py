# Generated by Django 4.2.6 on 2023-11-02 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agent',
            name='agent_name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='agent',
            name='phone_number',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='dealer',
            name='dealer_name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='dealer',
            name='phone_number',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
