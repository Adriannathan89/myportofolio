from django.db import migrations


EDITOR_PERMISSIONS = {
    "award": ("add_award", "delete_award"),
    "experience": ("add_experience", "change_experience", "delete_experience"),
}


def create_editor_group(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    database = schema_editor.connection.alias

    editor, _ = Group.objects.using(database).get_or_create(name="Editor")
    for model, codenames in EDITOR_PERMISSIONS.items():
        content_type, _ = ContentType.objects.using(database).get_or_create(
            app_label="main", model=model
        )
        for codename in codenames:
            permission, _ = Permission.objects.using(database).get_or_create(
                content_type=content_type,
                codename=codename,
                defaults={"name": f"Can {codename.split('_')[0]} {model}"},
            )
            editor.permissions.add(permission)


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0008_award_starred_by"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(create_editor_group, migrations.RunPython.noop),
    ]
