

class OQRouter(object):

    def db_for_read(self, model, **hints):
        raise NotImplementedError

    def db_for_write(self, model, **hints):
        raise NotImplementedError
