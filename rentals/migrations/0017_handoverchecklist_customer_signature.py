# Generated by Django 5.2.1 on 2025-07-01 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rentals', '0016_handoverchecklist_handoverphoto'),
    ]

    operations = [
        migrations.AddField(
            model_name='handoverchecklist',
            name='customer_signature',
            field=models.ImageField(blank=True, null=True, upload_to='signatures/'),
        ),
    ]
