class LACNIC(RIR):

    def __init__(self, st_key=None):
        self.st_key = st_key or os.environ["LACNIC_ST_KEY"]
