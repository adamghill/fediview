# Generated by Django 4.1.4 on 2023-01-31 12:55

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
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
                ("hours", models.IntegerField()),
                ("scorer", models.CharField(max_length=255)),
                ("threshold", models.CharField(max_length=255)),
                ("timeline", models.CharField(max_length=255)),
                (
                    "account",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="account.account",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]