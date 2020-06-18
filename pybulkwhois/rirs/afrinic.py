import logging
import json

from .rir import RIR, FTPRIR


class AFRINIC(FTPRIR):

    BASE_URL = "ftp://ftp.afrinic.net/dbase"
    NAME = "afrinic"

    def get_raw(self, name=None):
        # Afrinic only has one file which contains all of their records
        full_name = "afrinic.db.gz"
        return super(AFRINIC, self).get_raw(full_name)

    def construct_intermediate_jsons(self, out_folder, types):
        # Overridden to call the one-file version of construct_intermediate_jsons.
        super(AFRINIC, self).construct_intermediate_jsons_one_file(out_folder, types)