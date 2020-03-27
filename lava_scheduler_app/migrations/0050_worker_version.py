# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-03-26 08:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("lava_scheduler_app", "0049_add_worker_auth")]

    operations = [
        migrations.AddField(
            model_name="worker",
            name="version",
            field=models.CharField(
                blank=True,
                default=None,
                max_length=50,
                null=True,
                verbose_name="Dispatcher version",
            ),
        )
    ]
