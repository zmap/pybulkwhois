import logging

from .rirs.ripe import RIPE

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    ripe = RIPE()
    x = ripe.get("aut-num")
    print x
    for l in x:
        asv = {
                "asn":l.labeled["aut-num"][0],
                "name":l.labeled["as-name"][0]
        }
        if "org" in l.labeled:
            asv["orghandle"] = l.labeled["org"][0]
        if "descr" in l.labeled:
            asv["descr"] = " ".join(l.labeled.get("descr", []))
        print asv
