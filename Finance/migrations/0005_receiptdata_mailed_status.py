# Generated by Django 2.1.7 on 2019-03-02 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Finance', '0004_auto_20190302_1042'),
    ]

    operations = [
        migrations.AddField(
            model_name='receiptdata',
            name='mailed_status',
            field=models.BooleanField(default=False),
        ),
    ]
