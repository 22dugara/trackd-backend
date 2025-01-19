# Generated by Django 5.1.5 on 2025-01-19 05:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_album_spotify_uri_artist_spotify_uri_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='album',
            name='cover_art',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='artist',
            name='image',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='song',
            name='image',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
