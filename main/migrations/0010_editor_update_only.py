from django.db import migrations


def limit_editor_to_updates(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    database = schema_editor.connection.alias

    editor, _ = Group.objects.using(database).get_or_create(name="Editor")
    permissions = []
    for model in ("award", "experience"):
        content_type, _ = ContentType.objects.using(database).get_or_create(
            app_label="main", model=model
        )
        permission, _ = Permission.objects.using(database).get_or_create(
            content_type=content_type,
            codename=f"change_{model}",
            defaults={"name": f"Can change {model}"},
        )
        permissions.append(permission)

    editor.permissions.set(permissions)


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0009_editor_group"),
    ]

    operations = [
        migrations.RunPython(limit_editor_to_updates, migrations.RunPython.noop),
    ]
