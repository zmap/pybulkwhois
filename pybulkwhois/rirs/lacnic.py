import os
import re
import requests
import shutil
import urllib.request as urllib2
import tempfile

from contextlib import closing
from bs4 import BeautifulSoup

from .rir import RIR

class LACNIC(RIR):

    BASE_URL = "https://lacnic.net/cgi-bin/lacnic/stini"
    NAME = "lacnic"

    STANDARD_KEY_MAP = {
        "aut-num": "asn",
        "owner": "name",
        "changed": "last-modified",
    }

    def __init__(self, uid=None, pwd=None):
        self.uid = uid
        self.pwd = pwd

    def get_raw(self, name=None):
        # we need a session
        session = requests.session()
        raw_login_page = session.get(self.BASE_URL)
        parsed_login_page = BeautifulSoup(raw_login_page.text, "html.parser")
        action = parsed_login_page.find('form').get('action')
        full_action = "https://lacnic.net" + action
        logged_in_raw = session.post(full_action, data={
            "handle":self.uid,
            "passwd":self.pwd
        })
        logged_in_parsed = BeautifulSoup(logged_in_raw.text, "html.parser")
        dl_url = logged_in_parsed(text=re.compile('Bulk Whois'))[0].parent.get("href")
        full_dl_url = "https://lacnic.net" + dl_url
        retv = tempfile.NamedTemporaryFile(delete=False)
        with closing(urllib2.urlopen(full_dl_url)) as f:
            shutil.copyfileobj(f, retv)
        retv.seek(0)
        return retv

    def construct_intermediate_jsons(self, out_folder, types):
        # Overridden to call the one-file version of construct_intermediate_jsons.
        super(LACNIC, self).construct_intermediate_jsons_one_file(out_folder, types)

if __name__ == '__main__':
    print("Running lacnic.py")
    l = LACNIC(os.environ["LACNIC_UID"], os.environ["LACNIC_PWD"])
    print(l.get_raw())
