"""Create the two guest users the frontend uses for its guest login."""
from django.contrib.auth.hashers import make_password
from django.db import migrations

GUEST_USERS = [
    {"username": "andrey", "password": "asdasd", "type": "customer"},
    {"username": "kevin", "password": "asdasd24", "type": "business"},
]


def create_guest_users(apps, schema_editor):
    """Add both guest users with profiles; existing ones stay unchanged."""
    user_model = apps.get_model("auth", "User")
    profile_model = apps.get_model("auth_app", "UserProfile")
    for guest in GUEST_USERS:
        user, _ = user_model.objects.get_or_create(
            username=guest["username"],
            defaults={"password": make_password(guest["password"])},
        )
        profile_model.objects.get_or_create(
            user=user, defaults={"type": guest["type"]}
        )


def remove_guest_users(apps, schema_editor):
    """Delete the guest users (and their profiles) on reverse."""
    user_model = apps.get_model("auth", "User")
    usernames = [guest["username"] for guest in GUEST_USERS]
    user_model.objects.filter(username__in=usernames).delete()


class Migration(migrations.Migration):
    """Data migration: guest users for the frontend's guest login."""

    dependencies = [
        ("auth_app", "0001_initial"),
        ("authtoken", "0004_alter_tokenproxy_options"),
    ]

    operations = [
        migrations.RunPython(create_guest_users, remove_guest_users),
    ]
