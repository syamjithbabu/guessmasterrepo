# Generated by Django 4.2.5 on 2023-10-17 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agent', '0006_remove_agentbill_data'),
    ]

    operations = [
        migrations.RenameField(
            model_name='agentbill',
            old_name='total_amount',
            new_name='total_c_amount',
        ),
        migrations.AddField(
            model_name='agentbill',
            name='total_count',
            field=models.DecimalField(decimal_places=0, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='agentbill',
            name='total_d_amount',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
    ]
