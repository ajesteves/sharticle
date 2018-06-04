# Generated by Django 2.0.3 on 2018-06-03 21:51

import articles.models
from django.db import migrations, models
import djongo.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0005_auto_20180518_2019'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.CharField(max_length=64)),
            ],
        ),
        migrations.AddField(
            model_name='article',
            name='tags',
            field=djongo.models.fields.ArrayModelField(model_container=articles.models.Tag, model_form_class=articles.models.TagForm, null=True),
        ),
    ]
