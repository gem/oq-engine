from django.db import migrations


def create_permission(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    content_type = ContentType.objects.get_for_model(Permission)
    Permission.objects.get_or_create(
        codename='can_share_own_jobs',
        name='Can share own jobs',
        content_type=content_type,
    )


def delete_permission(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    content_type = ContentType.objects.get_for_model(Permission)
    Permission.objects.filter(
        codename='can_share_own_jobs', content_type=content_type).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(create_permission, delete_permission),
    ]
