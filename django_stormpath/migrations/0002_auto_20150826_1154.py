# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_stormpath.models


class Migration(migrations.Migration):

    dependencies = [
        ('django_stormpath', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stormpathuser',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='stormpathuser',
            name='groups',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups'),
        ),
        migrations.AlterField(
            model_name='stormpathuser',
            name='is_active',
            field=models.BooleanField(default=django_stormpath.models.get_default_is_active),
        ),
        migrations.AlterField(
            model_name='stormpathuser',
            name='last_login',
            field=models.DateTimeField(null=True, verbose_name='last login', blank=True),
        ),
    ]
