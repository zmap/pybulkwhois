import logging
import urllib.request as request
import shutil
import tempfile
import gzip
import json
from contextlib import closing

from ..file import BulkWHOISFile

ENCODING = 'utf-8'

class RIR(object):
    IGNORED_KEYS   = []
    IGNORED_VALUES = []

    # Overridden by an RIR if it has a different name for the typical types
    # (e.g. ARIN calls 'aut-num' 'ASHandle')
    TYPE_MAP = {}

    # Overridden by each RIR to translate its keys into a final standardized
    # representation
    STANDARD_KEY_MAP  = {}

    def get(self, name=None):
        return BulkWHOISFile(self.get_raw(name), self.IGNORED_KEYS, self.IGNORED_VALUES)

    def intm_json_path(self, out_folder, t):
        '''
        Return the intermediate json path for this type.
        '''
        return "%s/intm/%s_%s.json" % (out_folder, self.NAME, t)

    def construct_intermediate_jsons(self, out_folder, types):
        '''
        Fetch the db files from the RIR and parse them into well-structured json
        files in the out_folder. types specifies which files to grab. Constructs
        one json file per type in the types list.
        '''
        for t in types:
            t_file = self.get(t)
            out_path = self.intm_json_path(out_folder, t)
            with open(out_path, 'w+', encoding=ENCODING) as out:
                for entry in t_file:
                    # Only write out objects with matching types - some of the RIRs
                    # include dummy objects/other info in these files.
                    if entry.type == t or (t in self.TYPE_MAP and entry.type == self.TYPE_MAP[t]):
                        # Convert to standard form before writing out.
                        out_json = self.convert_to_standard_form(entry.labeled)
                        out.write(json.dumps(out_json, ensure_ascii = False) + "\n")
            logging.debug('Wrote out ' + t + ' objects to ' + out_path)

    def construct_intermediate_jsons_one_file(self, out_folder, types):
        '''
        Another version of construct_intermediate_jsons for the RIRs which put all
        of their records into a single file. Fetches the single db file and parses it into
        well-structured json files in the out_folder. Constructs one json file per type in
        the types list.
        '''
        out_files = {}
        for t in types:
            out_path = self.intm_json_path(out_folder, t)
            out_files[t] = open(out_path, 'w+', encoding=ENCODING)
        # afrinic and lacnic put all their data in one file, so we don't need to give it a specific type
        db_file = self.get()
        for entry in db_file:
            if entry.type in types:
                # convert to standard form
                out_json = self.convert_to_standard_form(entry.labeled)
                out_files[entry.type].write(json.dumps(out_json, ensure_ascii = False) + "\n")
        for t, f in out_files.items():
            f.close()

    def is_other_org_entry(self, in_json):
        '''
        Redefined inside of the specific RIR classes - evaluates whether this
        aut-num json is an entry from another RIR
        '''
        return False

    def convert_to_standard_form(self, in_json):
        '''
        Takes in one of the intermediate jsons and converts it to our standardized
        form using the RIR's specified STANDARD_KEY_MAP.
        '''
        out_json = {}

        # Translate the original key if necessary
        for k, v in in_json.items():
            # Second pass to filter ignored keys, in case they changed but
            # we don't want to rebuild all the intermediate jsons.
            if k in self.IGNORED_KEYS:
                continue

            # by default convert to lowercase
            new_k = k.lower()
            if k in self.STANDARD_KEY_MAP:
                new_k = self.STANDARD_KEY_MAP[k]

            out_json[new_k] = v

        # Handle some weird case nonsense
        if 'asn' in out_json:
            # If the "as" is lowercase, convert it to uppercase
            out_json['asn'] = out_json['asn'].upper()
            if not out_json['asn'].startswith('AS'):
            # Otherwise, if it isn't there add it on
                out_json['asn'] = 'AS' + out_json['asn']
                
        if 'source' in out_json:
            out_json['source'] = out_json['source'].upper()

        return out_json

    def add_to_full_db(self, out_folder, full_db, types):
        '''
        Iterate over the parsed jsons in RIR_aut-num.json and convert them to a
        standardized format, then append them (if they aren't duplicates) to the
        full db file.
        '''
        full_db_path = "%s/%s" % (out_folder, full_db)
        as_path = self.intm_json_path(out_folder, 'aut-num')

        # map from asns to their objects
        asn_objs = {}
        # map from org/contact handles to a list of asns that contain them
        handles_to_asns = {}

        with open(as_path, 'r', encoding=ENCODING) as ans:
            for l in ans:
                out_json = json.loads(l)

                # Make sure not to add duplicates.
                if self.is_other_org_entry(out_json):
                    continue

                # Check for contact / org object references
                for k, v in out_json.items():
                    if 'handle' in k or '-c' in k:
                        # There can be multiple contacts listed! They were joined
                        # by '\n' in the intake process
                        cs = v.split('\n')
                        for v in cs:
                            if not v in handles_to_asns:
                                handles_to_asns[v] = set()
                            handles_to_asns[v].add(out_json['asn'])

                # add space for the eventual contact/org objects
                out_json['handles'] = {}

                # add to our list to eventually write out
                asn_objs[out_json['asn']] = out_json

        # Now we'll loop over the other intermediate jsons for this RIR to see if
        # any of the orgs/contacts are relevant
        for t in types:
            # no need to process aut-num again
            if t == 'aut-num':
                continue
            int_path = self.intm_json_path(out_folder, t)
            with open(int_path, 'r', encoding=ENCODING) as ij:
                for l in ij:
                    out_json = json.loads(l)
                    org_pocs = set()

                    if t == 'organisation':
                        handle = out_json['orghandle']

                        # Check for contact / org object references in the orgs
                        # so that we can catch them when we go through the people/roles
                        for k, v in out_json.items():
                            if 'handle' in k or '-c' in k:
                                for v in v.split('\n'):
                                    org_pocs.add(v)

                    elif t == 'person' or t == 'role':
                        if 'pochandle' in out_json:
                            handle = out_json['pochandle']

                    # If we noted that we cared about this handle, then loop over
                    # all the asns it was relevant to and add this object to their set
                    # of handles.
                    if handle in handles_to_asns:
                        for asn in handles_to_asns[handle]:
                            asn_objs[asn]['handles'][handle] = out_json
                            # Add this asn to the to process list for any nested contacts we discovered
                            for p in org_pocs:
                                if p not in handles_to_asns:
                                    handles_to_asns[p] = set()
                                handles_to_asns[p].add(asn)

        # If any of these ASes represent blocks, duplicate them.
        for asn in list(asn_objs.keys()).copy():
            obj = asn_objs[asn]
            if 'asblock' in obj:
                parts = obj['asblock'].split('-')
                # If the asnumber was a range, duplicate this object for each as in the range
                # that we don't have a different entry for. 
                if len(parts) == 2:
                    as_range = ["AS" + str(i) for i in range(int(parts[0]), int(parts[1]) + 1)]
                    # If there are more than 10,000 ASes in this block, it's probably not a real 
                    # block of ASes. 
                    if len(as_range) > 10000:
                        continue
                    for new_asn in as_range:
                        if not new_asn in asn_objs:
                            asn_objs[new_asn] = obj.copy()
                            asn_objs[new_asn]["asn"] = new_asn

        # Finally, write out all of the asn objects to the full db file.
        with open(full_db_path, 'a+', encoding=ENCODING) as db:
            for out_json in asn_objs.values():
                db.write(json.dumps(out_json, ensure_ascii=False) + "\n")
        logging.debug("Added as#s to full db.")

class FTPRIR(RIR):
    BASE_URL        = None
    SUPPORTED_TYPES = set()

    # override parent's: these are only relevant to the FTP RIRs
    IGNORED_KEYS = ["export", "export-via", "import", "import-via", "default", \
                    "mnt-by", "member-of", "mp-export", "mp-import", "mnt-lower", \
                    "mnt-irt", "mnt-routes", "mnt-ref", "mp-default", "changed"]

    # Maps the labels used by the individual RIR to a final standardized representation
    STANDARD_KEY_MAP = {
        "aut-num": "asn",
        "as-name": "name",
        "org": "orghandle",
        "organisation": "orghandle",
        "sponsoring-org": "sponsoring-orghandle",
        "nic-hdl": "pochandle"
    }

    def __init__(self, base_url=None, uid=None, pwd=None):
        self._base_url = base_url or self.BASE_URL
        self._uid = uid
        self._pwd = pwd

    def make_path(self, name):
        return "%s/%s" % (self._base_url, name)

    def get_raw(self, name):
        retv = tempfile.NamedTemporaryFile(delete=False)
        gzipped = tempfile.NamedTemporaryFile(delete=False)
        path = self.make_path(name)

        # Some of the FTP RIR systems require a login, so we'll open them all through
        # a password manager
        pwd_mgr = request.HTTPPasswordMgrWithDefaultRealm()
        if self._uid:
            pwd_mgr.add_password(None, self._base_url, self._uid, self._pwd)
        handler = request.HTTPBasicAuthHandler(pwd_mgr)
        opener = request.build_opener(handler)
        opener.open(path)
        request.install_opener(opener)

        logging.debug("will attempt to download %s", path)
        with closing(request.urlopen(path)) as f:
            shutil.copyfileobj(f, gzipped)
        gzipped.close()
        logging.debug("gzipped content downloaded to %s", gzipped.name)
        with gzip.open(gzipped.name) as g:
            shutil.copyfileobj(g, retv)
        logging.debug("uncompressed content saved to %s", retv.name)
        return retv


