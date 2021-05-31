import logging

from .rir import RIR, FTPRIR


class APNIC(FTPRIR):

    BASE_URL = "https://ftp.apnic.net/whois-data/APNIC/split"
    NAME = "apnic"

    SUPPORTED_TYPES = {
        "as-block",
        "as-set",
        "aut-num",
        "domain",
        "filter-set",
        "inet-rtr",
        "inet6num",
        "inetnum",
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
        full_name = "%s.db.%s.gz" % (self.NAME, name)
        return super(APNIC, self).get_raw(full_name)


