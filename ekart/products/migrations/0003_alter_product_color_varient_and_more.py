# Generated by Django 5.0.3 on 2024-04-09 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_colorvarient_sizevarient_product_color_varient_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='color_varient',
            field=models.ManyToManyField(blank=True, to='products.colorvarient'),
        ),
        migrations.AlterField(
            model_name='product',
            name='size_varient',
            field=models.ManyToManyField(blank=True, to='products.sizevarient'),
        ),
    ]
