# Generated by Django 2.0 on 2019-03-02 12:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Finance', '0006_auto_20190302_1814'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='id',
        ),
        migrations.AlterField(
            model_name='company',
            name='name',
            field=models.CharField(max_length=50, primary_key=True, serialize=False),
        ),
    ]
