# Generated by Django 4.2.7 on 2023-11-27 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agent', '0006_remove_bill_dealer_game_admin'),
        ('dealer', '0005_remove_dealergameadmin_dealer_game_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dealergametestadmin',
            name='agent',
        ),
        migrations.RemoveField(
            model_name='dealergametestadmin',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='dealergametestadmin',
            name='dealer',
        ),
        migrations.RemoveField(
            model_name='dealergametestadmin',
            name='time',
        ),
        migrations.AddField(
            model_name='dealergame',
            name='c_amount_admin',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dealergame',
            name='count_admin',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dealergame',
            name='d_amount_admin',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dealergametest',
            name='c_amount_admin',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dealergametest',
            name='count_admin',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dealergametest',
            name='d_amount_admin',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='DealerGameAdmin',
        ),
        migrations.DeleteModel(
            name='DealerGameTestAdmin',
        ),
    ]