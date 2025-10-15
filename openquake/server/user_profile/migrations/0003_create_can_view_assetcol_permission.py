from django.db import migrations


def create_can_view_assetcol_permission(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # You can attach the permission to any content type;
    # using 'auth.Permission' is fine for non-model resources
    content_type = ContentType.objects.get_for_model(Permission)

    Permission.objects.get_or_create(
        codename='can_view_assetcol',
        name='Can view assetcol',
        content_type=content_type,
    )


def delete_can_view_assetcol_permission(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    Permission.objects.filter(codename='can_view_assetcol').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('user_profile', '0002_create_can_view_exposure_permission'),
    ]

    operations = [
        migrations.RunPython(create_can_view_assetcol_permission,
                             delete_can_view_assetcol_permission),
    ]
