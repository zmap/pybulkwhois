from .entry import BulkWHOISEntry

class BulkWHOISFile(object):

    def __init__(self, path):
        if type(path) == basestring:
            self.f = open(path, 'r')
        else:
            self.f = path

    def __iter__(self):
        lines = []
        self.f.seek(0)
        for l in self.f:
            tl = l.strip()
            if tl and tl[0] in ("#", "%"):
                continue
            if lines and not tl:
                yield BulkWHOISEntry(lines)
                lines = []
                continue
            lines.append(l.rstrip())
        if lines:
            yield BulkWHOISEntry(lines)
