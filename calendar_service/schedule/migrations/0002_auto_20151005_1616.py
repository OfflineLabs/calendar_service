# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='creator',
        ),
        migrations.AlterUniqueTogether(
            name='occurrence',
            unique_together=set([('event', 'start')]),
        ),
        migrations.RemoveField(
            model_name='occurrence',
            name='description',
        ),
        migrations.RemoveField(
            model_name='occurrence',
            name='title',
        ),
    ]
