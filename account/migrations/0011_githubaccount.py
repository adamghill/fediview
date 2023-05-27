# Generated by Django 4.2 on 2023-05-14 12:24

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0010_profile_generate_recommendations"),
    ]

    operations = [
        migrations.CreateModel(
            name="GitHubAccount",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("access_token", models.CharField(max_length=1024)),
                ("username", models.CharField(max_length=1024)),
                (
                    "account",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="github_account",
                        to="account.account",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]