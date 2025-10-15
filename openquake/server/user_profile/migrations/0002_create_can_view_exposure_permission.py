from django.db import migrations


def create_can_view_exposure_permission(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # You can attach the permission to any content type;
    # using 'auth.Permission' is fine for non-model resources
    content_type = ContentType.objects.get_for_model(Permission)

    Permission.objects.get_or_create(
        codename='can_view_exposure',
        name='Can view exposure',
        content_type=content_type,
    )


def delete_can_view_exposure_permission(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    Permission.objects.filter(codename='can_view_exposure').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('user_profile', '0001_create_user_profiles'),
    ]

    operations = [
        migrations.RunPython(create_can_view_exposure_permission,
                             delete_can_view_exposure_permission),
    ]
