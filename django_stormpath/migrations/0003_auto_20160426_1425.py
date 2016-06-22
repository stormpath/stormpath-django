# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_stormpath', '0002_auto_20150826_1154'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stormpathuser',
            name='email',
            field=models.EmailField(db_index=True, max_length=255, unique=True, verbose_name='email address'),
        ),
    ]
