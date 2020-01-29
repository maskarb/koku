# Generated by Django 2.2.8 on 2020-01-28 21:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_providerstatus_squashed_0042_auto_20200116_2048'),
    ]

    operations = [
        migrations.RunSQL(
            """
            UPDATE public.api_provider
                SET type = 'Azure'
            WHERE type = 'AZURE'
            ;

            UPDATE public.api_providerinfrastructuremap
                SET infrastructure_type = 'Azure'
            WHERE infrastructure_type = 'AZURE'
            ;
            """
        )
    ]
