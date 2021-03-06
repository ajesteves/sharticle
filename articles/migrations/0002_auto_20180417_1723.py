# Generated by Django 2.0.3 on 2018-04-17 16:23

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sharticleuser',
            name='date_last_modified',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sharticleuser',
            name='number_of_followees',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='sharticleuser',
            name='number_of_followers',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='sharticleuser',
            name='profileImagePath',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='sharticleuser',
            name='resume',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]
