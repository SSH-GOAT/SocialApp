# Generated by Django 5.1.1 on 2024-09-28 06:40

import django.db.models.deletion
import django.utils.timezone
import network.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=254, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("name", models.CharField(max_length=40)),
                ("password", models.CharField(max_length=32)),
                (
                    "date_joined",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("blocked_user", models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ("friends", models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            managers=[
                ("objects", network.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Friend_Request",
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
                    "request_sent_on",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "request_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="request_sent",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "request_to",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="request_received",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
