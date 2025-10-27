import os
import re
import requests
import shutil
import urllib.request as request
import tempfile
import logging
import json
import zipfile


from contextlib import closing
from bs4 import BeautifulSoup

from .rir import RIR

class ARIN(RIR):

    def get_url(self, name=None):
        if name is not None:
            return f"https://accountws.arin.net/public/rest/downloads/bulkwhois/{name}.zip?apikey={self.api_key}"
        else:
            return f"https://accountws.arin.net/public/rest/downloads/bulkwhois?apikey={self.api_key}"
        

    NAME = "arin"

    IGNORED_KEYS = ['CanAllocate']

    # Map the standard types to the ARIN filenames
    SUPPORTED_TYPES = {
        "aut-num": "asns.txt",
        "organisation": "orgs.txt",
        "person": "pocs.txt"
    }

    # Map the standard types to the ARIN record to request
    TYPE_TO_ARIN_RECORD = {
        "aut-num": "asns",
        "organisation": "orgs",
        "person": "pocs"
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
        "ASNumber": "asblock",
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
        "Mailbox": "e-mail",
        "OfficePhone": "phone",
    }

    def __init__(self, api_key=None):
        self.api_key = api_key

    def get_raw(self, name=None):
        if name not in self.SUPPORTED_TYPES:
            raise Exception("invalid file type requested")
         # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "arin_bulkwhois.zip")

        url = self.get_url(self.TYPE_TO_ARIN_RECORD[name])
        print(f"Downloading from {url} ...")
        response = requests.get(url)
        response.raise_for_status()  # raise exception if download failed

        with open(zip_path, "wb") as f:
            f.write(response.content)
        # we'll need to download the zip file for the type, then extract it, and return the arin_db.txt
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        extracted_path = os.path.join(temp_dir, "arin_db.txt")
        renamed_path = os.path.join(temp_dir, f"{self.TYPE_TO_ARIN_RECORD[name]}.txt")

        # Rename the extracted file
        if os.path.exists(extracted_path):
            os.rename(extracted_path, renamed_path)
            print(f"Extracted and renamed file saved at: {renamed_path}")
        else:
            raise FileNotFoundError("arin_db.txt not found in the downloaded ZIP file")

        retv = tempfile.NamedTemporaryFile(delete=False)
        with open(renamed_path, "rb") as f:
            shutil.copyfileobj(f, retv)
            retv.seek(0)
        return retv


    def is_other_org_entry(self, in_json):
        '''
        This AS entry is from another org if the comment denotes it as such.
        This function should only be called after an object is converted to standard form.
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

        if 'remarks' in in_json:
            for c in OTHER_RIR_COMMENTS:
                if c in in_json['remarks']:
                    return True
        if 'RIPE-ASNBLOCK' in in_json['name']:
            return True
        return False

if __name__ == '__main__':
    print("Running arin.py")
    l = ARIN(os.environ["ARIN_API"])
    print(l.get_raw())
