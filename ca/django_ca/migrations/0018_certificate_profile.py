# Generated by Django 3.0.2 on 2020-01-19 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_ca', '0017_auto_20200112_1657'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificate',
            name='profile',
            field=models.CharField(blank=True, default='', help_text='Profile that was used to generate this certificate.', max_length=32),
        ),
    ]
