# Generated by Django 4.2.1 on 2023-05-21 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0011_githubaccount"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="send_daily_digest",
            field=models.BooleanField(default=False),
        ),
    ]
