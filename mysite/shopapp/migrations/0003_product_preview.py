# Generated by Django 4.1.7 on 2023-03-02 11:31

from django.db import migrations, models
import shopapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('shopapp', '0002_order_receipt'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='preview',
            field=models.ImageField(blank=True, null=True, upload_to=shopapp.models.product_preview_directory_path),
        ),
    ]
