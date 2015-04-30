# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='StormpathPermissionsMixin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StormpathUser',
            fields=[
                ('stormpathpermissionsmixin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='django_stormpath.StormpathPermissionsMixin')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('href', models.CharField(max_length=255, null=True, blank=True)),
                ('username', models.CharField(unique=True, max_length=255)),
                ('given_name', models.CharField(max_length=255)),
                ('surname', models.CharField(max_length=255)),
                ('middle_name', models.CharField(max_length=255, null=True, blank=True)),
                ('email', models.EmailField(unique=True, max_length=255, verbose_name=b'email address', db_index=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_admin', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('django_stormpath.stormpathpermissionsmixin', models.Model),
        ),
        migrations.AddField(
            model_name='stormpathpermissionsmixin',
            name='groups',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='stormpathpermissionsmixin',
            name='user_permissions',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions'),
        ),
    ]
