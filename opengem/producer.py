# vim: tabstop=4 shiftwidth=4 softtabstop=4


class FileProducer(object):
    def __init__(self):
        self.finished = event.Event()

    def __iter__(self):
        try:
            rv = self._parse_one()
            while rv:
                yield rv
                rv = self._parse_one()
        except Exception, e:
            self.finished.send_exception(e)
        
        self.finished.send(True)

    def filter(self, constraint):
        for next in self:
            if constraint.match(next):
                yield next
