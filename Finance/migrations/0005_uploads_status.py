# Generated by Django 2.1 on 2019-03-02 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Finance', '0004_auto_20190302_1042'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploads',
            name='status',
            field=models.BooleanField(default=False),
        ),
    ]
