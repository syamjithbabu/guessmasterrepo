# Generated by Django 4.2.7 on 2023-11-30 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agent', '0008_alter_bill_total_c_amount_admin_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='customer',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
