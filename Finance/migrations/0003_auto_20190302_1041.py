# Generated by Django 2.0 on 2019-03-02 05:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Finance', '0002_auto_20190302_1037'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receiptdata',
            name='amount',
            field=models.CharField(max_length=10),
        ),
    ]
