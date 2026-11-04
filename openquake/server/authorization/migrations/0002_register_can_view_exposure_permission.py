from django.db import migrations


def create_permission(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    content_type = ContentType.objects.get_for_model(Permission)
    Permission.objects.get_or_create(
        codename='can_view_exposure',
        name='Can view exposure',
        content_type=content_type,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('authorization', '0001_create_can_share_own_jobs_permission'),
    ]

    # The legacy UserProfile migration also creates this permission; don't
    # remove it when rolling back this migration.
    operations = [
        migrations.RunPython(create_permission, migrations.RunPython.noop),
    ]
