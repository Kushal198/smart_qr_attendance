# Generated by Django 3.2.5 on 2022-01-06 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20220106_1215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendanceclass',
            name='created_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]