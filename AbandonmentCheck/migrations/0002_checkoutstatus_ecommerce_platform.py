# Generated by Django 5.0.7 on 2024-07-15 17:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AbandonmentCheck', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkoutstatus',
            name='ecommerce_platform',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='AbandonmentCheck.ecommerceplatform'),
        ),
    ]