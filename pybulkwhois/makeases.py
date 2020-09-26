import logging
import json
import os
import sys

from .rirs.ripe     import RIPE
from .rirs.apnic    import APNIC
from .rirs.afrinic  import AFRINIC
from .rirs.lacnic   import LACNIC
from .rirs.arin     import ARIN

from .file import BulkWHOISFile

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Make sure all the relevant environment keys are present
    rirs_with_logins = ["APNIC", "LACNIC", "ARIN"]
    logins = json.load(open('logins.json', 'r'))
    have_all_logins = True
    for rir in rirs_with_logins:
        if not (rir + "_UID" in logins.keys() and rir + "_PWD" in logins.keys()):
            have_all_logins = False
            logging.debug(f"Missing uid/pwd for {rir} in logins.json.")
    if not have_all_logins:
        logging.debug("Exiting.")
        exit()

    # Configure output directory
    if (len(sys.argv) > 1):
        out_folder = sys.argv[1]
    else:
        out_folder = "out" # default

    logging.debug(f"Using {out_folder} as output directory.")
    if not os.path.isdir(out_folder):
        logging.debug(f'Making directory {out_folder}.')
        os.mkdir(out_folder)

    intermediate_folder = out_folder + "/intm"
    if not os.path.isdir(intermediate_folder):
        os.mkdir(intermediate_folder)


    # full_db is where we'll eventually write out all of the processed entries
    full_db = 'full_db.json'
    # If the file already exists, clear it
    with open(out_folder + '/' + full_db, 'w+') as out:
        out.write("")

    # These are the types relevant to the full database
    types = ['aut-num', 'organisation', 'person', 'role']

    # RIPE
    logging.debug("----- Processing RIPE -----")
    ripe = RIPE()
    ripe.construct_intermediate_jsons(out_folder, types)
    ripe.add_to_full_db(out_folder, full_db, types)

    # APNIC
    logging.debug("----- Processing APNIC -----")
    apnic = APNIC(uid=os.environ["APNIC_UID"], pwd=os.environ["APNIC_PWD"])
    apnic.construct_intermediate_jsons(out_folder, types)
    apnic.add_to_full_db(out_folder, full_db, types)

    # AFRINIC
    logging.debug("----- Processing AFRINIC -----")
    afrinic = AFRINIC()
    afrinic.construct_intermediate_jsons(out_folder, types)
    afrinic.add_to_full_db(out_folder, full_db, types)

    # LACNIC
    logging.debug("----- Processing LACNIC -----")
    lacnic = LACNIC(os.environ["LACNIC_UID"], os.environ["LACNIC_PWD"])
    lacnic.construct_intermediate_jsons(out_folder, types)
    lacnic.add_to_full_db(out_folder, full_db, types)

    # ARIN
    logging.debug("----- Processing ARIN -----")
    types = ['aut-num', 'organisation', 'person'] # ARIN wraps roles into person
    arin = ARIN(os.environ["ARIN_UID"], os.environ["ARIN_PWD"])
    arin.construct_intermediate_jsons(out_folder, types)
    arin.add_to_full_db(out_folder, full_db, types)

    logging.debug(f"All AS objects written out to {out_folder}/{full_db}.")