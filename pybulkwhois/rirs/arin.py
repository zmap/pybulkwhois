import os
import re
import requests
import shutil
import urllib.request as request
import tempfile
import logging
import json

from contextlib import closing
from bs4 import BeautifulSoup

from .rir import RIR

class ARIN(RIR):

    LOGIN_URL = "https://accountws.arin.net/public/seam/resource/rest/auth/login"
    BASE_URL = "https://accountws.arin.net/public/secure/downloads/bulkwhois"
    NAME = "arin"

    IGNORED_KEYS = ['ASNumber', 'CanAllocate']

    # Map the standard types to the ARIN filenames
    SUPPORTED_TYPES = {
        "aut-num": "asns.txt",
        "organisation": "orgs.txt",
        "person": "pocs.txt"
    }

    # Map the standard types to ARIN's special names for them
    TYPE_MAP = {
        "aut-num": "ASHandle",
        "organisation": "OrgID",
        "person": "POCHandle"
    }

    # Maps the labels used by the individual RIR to a final standardized representation
    STANDARD_KEY_MAP = {
        # These are starts of objects
        "ASHandle": "asn",
        "POCHandle": "pochandle",
        "OrgID": "orghandle",
        # Assorted
        "ASName": "name",
        "OrgName": "org-name",
        "Source": "source",
        "RegDate": "created",
        "Updated": "last-modified",
        "Comment": "remarks",
        # These are all inner contact links
        "TechHandle": "tech-c",
        "OrgTechHandle": "tech-c",
        "AbuseHandle": "abuse-c",
        "OrgAbuseHandle": "abuse-c",
        "OrgAdminHandle": "admin-c",
        "NOCHandle": "noc-c",
        "OrgNOCHandle": "noc-c",
        "OrgRoutingHandle": "routing-c",
        "OrgDNSHandle": "dns-c",
    }

    def __init__(self, uid=None, pwd=None):
        self.uid = uid
        self.pwd = pwd

    def get_raw(self, name=None):
        if name not in self.SUPPORTED_TYPES:
            raise Exception("invalid file type requested")
        path = self.BASE_URL + "/" + self.SUPPORTED_TYPES[name]

        # First log in to get the relevant cookie.
        session = requests.session()
        headers = {"Content-Type": "application/json"}
        logged_in_raw = session.post(self.LOGIN_URL, headers=headers, data=json.dumps({
            "username":self.uid,
            "password":self.pwd
        }))
        cookie = list(logged_in_raw.cookies.get_dict().items())[0]
        cookie_val = cookie[0] + "=" + cookie[1]

        retv = tempfile.NamedTemporaryFile(delete=False)

        logging.debug("will attempt to download %s", path)
        req = request.Request(path)
        req.add_header("Cookie", cookie_val)
        with closing(request.urlopen(req)) as f:
            shutil.copyfileobj(f, retv)
        logging.debug("uncompressed content saved to %s", retv.name)
        retv.seek(0)
        return retv


    def is_other_org_entry(self, in_json):
        '''
        This AS entry is from another org if the comment denotes it as such
        '''
        OTHER_RIR_COMMENTS = [
            "This AS is under LACNIC responsibility",
            "This AS is under LACNIC responsibility",
            "This AS number block is under AFRINIC responsibility",
            "These AS numbers are not registered in the ARIN database",
            "These ASNs have been further assigned to users in the RIPE NCC region",
            "This AS number is not registered in the ARIN database",
            "These addresses have been further assigned to users in",
            "These ASNs have been further assigned to users in",
        ]

        if 'Comment' in in_json:
            for c in OTHER_RIR_COMMENTS:
                if c in in_json['Comment']:
                    return True
        if 'RIPE-ASNBLOCK' in in_json['ASName']:
            return True
        return False

        return 'Comment' in in_json and in_json['Comment'] in OTHER_RIR_COMMENTS

if __name__ == '__main__':
    print("Running arin.py")
    l = ARIN(os.environ["ARIN_UID"], os.environ["ARIN_PWD"])
    print(l.get_raw())
