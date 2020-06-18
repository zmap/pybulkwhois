import copy
import json
import sys
# from future.utils import iteritems

class BulkWHOISEntry(object):

    def __init__(self, lines, ignored_keys, ignored_values):
        self._type = None
        self.ignored_keys   = ignored_keys
        self.ignored_values = ignored_values
        self._type, self.labeled = self._make_labeled(lines)

    def _remove_cruft(self, retv):
        """RIPE likes to add verbose comments as well dummy values. This strips
        an ASN record of these superfluous values. Additionally, removes any values with keys
        that we don't care about."""

        # python doesn't let you modify a dict you're iterating over
        for k, v in copy.copy(retv).items():
            if k in self.ignored_keys or v in self.ignored_values:
                del retv[k]
            # if one of the ignored values is inside the actual value (happens a lot for remarks),
            # splice out only the part we want to ignore
            else:
                for iv in self.ignored_values:
                    if iv in v:
                        iv_start = v.index(iv)
                        spliced = v[0:iv_start] + v[iv_start + len(iv):]
                        retv[k] = spliced.strip()
        return retv

    def _make_labeled(self, lines):
        """Takes an ordered set of raw lines that describe a single entity and
        parse them into a sane dict that represents the object"""
        retv = {}
        top_type = None
        def append(t, v):
            if t in retv:
                retv[t] = "\n".join([retv[t], v])
            else:
                retv[t] = v
        last_type = None
        last_value = None
        for l in lines:
            if l[0] == " ":
                append(last_type, l.strip())
            # It looks like RIPE uses a '+' to indicate a newline within a
            # record since actual empty newlines delimit records themselves
            elif l[0] == "+":
                append(last_type, "\n")
            else:
                if (l.find(":", 0)) == -1:
                    value = last_value + " " + l.strip()
                    del(retv[last_type])
                    append(last_type, value)
                else:
                    type_, value = map(lambda x: x.strip(), l.split(":", 1))
                    append(type_, value)
                    last_type = type_
                    last_value = value
                    if not top_type:
                        top_type = type_

        self._remove_cruft(retv)
        return top_type, retv

    @property
    def type(self):
        return self._type

