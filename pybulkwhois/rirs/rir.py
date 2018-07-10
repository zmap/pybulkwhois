import logging
import urllib2
import shutil
import tempfile
import gzip

from contextlib import closing

from ..file import BulkWHOISFile

class RIR(object):

    def get(self, name=None):
        return BulkWHOISFile(self.get_raw(name))


class FTPRIR(RIR):

    BASE_URL = None
    SUPPORTED_TYPES = set()

    def __init__(self, base_url=None, uid=None, pwd=None):
        self._base_url = base_url or self.BASE_URL
        self._uid = uid
        self._pwd = pwd

    def make_path(self, name):
        if self._uid:
            return "%s:%s@%s/%s" % (self._uid, self._pwd, self._base_url, name)
        return "%s/%s" % (self._base_url, name)

    def get_raw(self, name):
        retv = tempfile.NamedTemporaryFile(delete=False)
        gzipped = tempfile.NamedTemporaryFile(delete=False)
        path = self.make_path(name)
        logging.debug("will attempt to download %s", path)
        with closing(urllib2.urlopen(path)) as f:
            shutil.copyfileobj(f, gzipped)
        gzipped.close()
        logging.debug("gzipped content downloaded to %s", gzipped.name)
        with gzip.open(gzipped.name) as g:
            shutil.copyfileobj(g, retv)
        logging.debug("uncompressed content saved to %s", retv.name)
        return retv



