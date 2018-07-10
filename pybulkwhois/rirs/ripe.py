import logging

from .rir import RIR, FTPRIR


class RIPE(FTPRIR):

    BASE_URL = "https://ftp.ripe.net/ripe/dbase/split"

    SUPPORTED_TYPES = {
        "as-block",
        "as-set",
        "aut-num",
        "domain",
        "filter-set",
        "inet-rtr",
        "inet6num",
        "inetnumz",
        "irt",
        "key-cert",
        "mntner",
        "organisation",
        "peering-set",
        "person",
        "poem",
        "poetic-form",
        "role",
        "route-set",
        "route",
        "route6",
        "rtr-set",
    }

    def get_raw(self, name):
        if name not in self.SUPPORTED_TYPES:
            raise Exception("invalid file type requested")
        full_name = "ripe.db.%s.gz" % name
        return super(RIPE, self).get_raw(full_name)


