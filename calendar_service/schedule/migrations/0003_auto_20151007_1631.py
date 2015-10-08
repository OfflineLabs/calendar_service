# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0002_auto_20151005_1616'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='rule_params',
            field=jsonfield.fields.JSONField(null=True, verbose_name='repeat params', blank=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='rule',
            field=models.ForeignKey(blank=True, to='schedule.Rule', help_text="Select '----' for a one time only event.", null=True, verbose_name='Repeats'),
        ),
    ]
