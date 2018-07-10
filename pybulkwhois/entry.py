
class BulkWHOISEntry(object):

    def __init__(self, lines):
        self.entries = list(self._iter_labeled_entries(lines))
        self.labeled = {}
        for (k,v) in self.entries:
            if k not in self.labeled:
                self.labeled[k] = []
            self.labeled[k].append(v)

    def _iter_labeled_entries(self, entries):
        for entry in self._iter_joined_entries(entries):
            k, v = entry.split(":", 1)
            yield k.strip(), v.strip()

    def _iter_joined_entries(self, lines):
        for entry in self._iter_raw_entries(lines):
            retv = "\n".join(entry)
            assert retv[0] != " "
            yield retv

    def _iter_raw_entries(self, lines):
        previous = []
        for line in lines:
            if not line:
                continue
            if line[0] in (" ", "+"):
                previous.append(line.strip())
                continue
            if previous:
                yield previous
                previous = []
            previous.append(line.strip())
            assert previous[0][0] != " "
        if previous:
            yield previous

    @property
    def type(self):
        return self.entries[0].split(":")[0].strip()

