APPS = (
    'auth',
    'contenttypes',
    'sessions',
    'sites',
    'admin',
)


class DefaultRouter(object):

    def db_for_read(self, model, **hints):
        if model._meta.app_label in APPS:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in APPS:
            return 'default'
        return None

    def allow_syncdb(self, db, model):
        if not db == 'default':
            return False
        return True
