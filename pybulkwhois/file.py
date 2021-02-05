from .entry import BulkWHOISEntry

class BulkWHOISFile(object):
    def __init__(self, path, ignored_keys=[], ignored_values=[]):
        self.f = path
        self.ignored_keys   = ignored_keys
        self.ignored_values = ignored_values

    def __iter__(self):
        lines = []
        self.f.seek(0)
        for l in self.f:
            # For Lacnic and Apnic Latin American data bases, letters do not fit w/in utf-8 encoding
            if type(l) != str:
                l = l.decode('latin-1')
            if l.startswith("#") or l.startswith("%") or l.startswith("Query rate limit"):
                continue
            if l == "\n" and lines:
                yield BulkWHOISEntry(lines, self.ignored_keys, self.ignored_values)
                lines = []
            if l.strip():
                lines.append(l)

    def iter_filtered(self, etype):
        for entry in self:
            if entry.type == etype:
                yield entry
