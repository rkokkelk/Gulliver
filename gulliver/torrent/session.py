import logging
import libtorrent as lt

log = logging.getLogger('gulliver.scanner')

class Session():

    lt_session = None

    def __init__(self):
        log.debug("Init")
        self.lt_session = lt.session()
        log.info("Libtorrent session started")
