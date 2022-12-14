# Generated by Django 4.1.2 on 2022-11-30 11:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import media.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta', models.JSONField(blank=True, null=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('db_status', models.IntegerField(choices=[(-1, 'Deleted'), (0, 'Pending'), (1, 'Active')], default=1)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('id_string', models.CharField(db_index=True, max_length=200)),
                ('tg_id', models.CharField(db_index=True, max_length=100)),
                ('tg_username', models.CharField(blank=True, max_length=256, null=True)),
                ('tg_name', models.CharField(blank=True, max_length=256, null=True)),
                ('photo', models.FileField(max_length=500, upload_to=media.models.path_and_rename, validators=[media.models.validate_file_size])),
                ('raw', models.JSONField(blank=True, null=True)),
                ('joined', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='accounts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta', models.JSONField(blank=True, null=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('db_status', models.IntegerField(choices=[(-1, 'Deleted'), (0, 'Pending'), (1, 'Active')], default=1)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('id_string', models.CharField(db_index=True, max_length=200)),
                ('desc', models.CharField(blank=True, max_length=600, null=True)),
                ('taxonomy', models.CharField(default='category', max_length=10)),
            ],
            options={
                'unique_together': {('id_string', 'taxonomy')},
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta', models.JSONField(blank=True, null=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('db_status', models.IntegerField(choices=[(-1, 'Deleted'), (0, 'Pending'), (1, 'Active')], default=1)),
                ('tg_id', models.CharField(db_index=True, max_length=100)),
                ('batch', models.IntegerField(default=1)),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('id_string', models.CharField(db_index=True, max_length=200, unique=True)),
                ('desc', models.TextField(blank=True, max_length=500, null=True)),
                ('statistics', models.JSONField(blank=True, null=True)),
                ('members', models.IntegerField(default=0)),
                ('online', models.IntegerField(default=0)),
                ('views', models.IntegerField(default=0)),
                ('messages', models.IntegerField(default=0)),
                ('is_group', models.BooleanField(blank=True, null=True)),
                ('photo', models.FileField(max_length=500, upload_to=media.models.path_and_rename, validators=[media.models.validate_file_size])),
                ('last_post_id', models.IntegerField(blank=True, null=True)),
                ('last_crawl', models.DateTimeField(blank=True, null=True)),
                ('associate', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='associated_rooms', to='main.room')),
                ('properties', models.ManyToManyField(blank=True, related_name='rooms', to='main.property')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='rooms', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Sticker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta', models.JSONField(blank=True, null=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('db_status', models.IntegerField(choices=[(-1, 'Deleted'), (0, 'Pending'), (1, 'Active')], default=1)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('id_string', models.CharField(db_index=True, max_length=200)),
                ('tg_id', models.CharField(db_index=True, max_length=100)),
                ('desc', models.CharField(blank=True, max_length=600, null=True)),
                ('count', models.IntegerField(default=0)),
                ('is_archived', models.BooleanField(default=False)),
                ('is_official', models.BooleanField(default=False)),
                ('is_animated', models.BooleanField(default=False)),
                ('is_video', models.BooleanField(default=False)),
                ('tags', models.ManyToManyField(blank=True, related_name='stickers', to='main.property')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stickers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StickerItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta', models.JSONField(blank=True, null=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('db_status', models.IntegerField(choices=[(-1, 'Deleted'), (0, 'Pending'), (1, 'Active')], default=1)),
                ('tg_id', models.CharField(db_index=True, max_length=100)),
                ('path', models.FileField(max_length=500, upload_to=media.models.path_and_rename, validators=[media.models.validate_file_size])),
                ('sticker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sticker_items', to='main.sticker')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Snapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta', models.JSONField(blank=True, null=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('db_status', models.IntegerField(choices=[(-1, 'Deleted'), (0, 'Pending'), (1, 'Active')], default=1)),
                ('post_id', models.IntegerField(blank=True, null=True)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_range', models.CharField(default='1h', max_length=3)),
                ('members', models.IntegerField(default=0)),
                ('online', models.IntegerField(default=0)),
                ('views', models.IntegerField(default=0)),
                ('messages', models.IntegerField(default=0)),
                ('replies', models.IntegerField(default=0)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='snapshots', to='main.room')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta', models.JSONField(blank=True, null=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('db_status', models.IntegerField(choices=[(-1, 'Deleted'), (0, 'Pending'), (1, 'Active')], default=1)),
                ('body', models.TextField(blank=True, max_length=500, null=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to='main.room')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta', models.JSONField(blank=True, null=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('db_status', models.IntegerField(choices=[(-1, 'Deleted'), (0, 'Pending'), (1, 'Active')], default=1)),
                ('is_admin', models.BooleanField(default=False)),
                ('rank', models.CharField(blank=True, default='member', max_length=50, null=True)),
                ('roles', models.JSONField(blank=True, null=True)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='main.account')),
                ('inviter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inviter_participants', to='main.account')),
                ('promoter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='promoter_participants', to='main.account')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='main.room')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
