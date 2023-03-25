# Generated by Django 4.1.7 on 2023-03-25 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0006_account_account_id_profile_indexing_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="bookmarks_count",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="account",
            name="favorites_count",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="account",
            name="followers_count",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="account",
            name="following_count",
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]