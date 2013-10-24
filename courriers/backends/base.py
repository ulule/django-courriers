class BaseBackend(object):

    def register(self, email, lang=None, user=None):
        raise NotImplemented

    def unregister(self, email, user=None):
        raise NotImplemented

    def exists(self, email, user=None):
        raise NotImplemented

    def send_mails(self, newsletter):
        raise NotImplemented