import logging
import time
import libtorrent as lt
from configobj import ConfigObj

log = logging.getLogger('gulliver.session')

class Session():

    lt_session = None

    def __init__(self):
        log.debug("Init")
        self.lt_session = lt.session()
        log.info("Libtorrent session started")

    def session_status(self):
        status = {}
        sess_status = self.lt_session.status()
        info_keys = ['num_peers','payload_upload_rate','payload_upload_rate']

        return "C: {0} D: {1} U: {2}".format(getattr(sess_status,'num_peers'),getattr(sess_status,'payload_download_rate'),getattr(sess_status,'payload_upload_rate'))

    def torrent_add(self,tor_file, in_save_path):

        e = lt.bdecode(open(tor_file,'rb').read())
        info = lt.torrent_info(e)

        params = { 'save_path': './', 'ti': info }
        self.lt_session.add_torrent(params)

    def load_settings(self, in_file):

        config = ConfigObj(in_file)
        settings = self.lt_session.get_settings()

        for k in settings:
            v = config[k]
            settings[k] = v

        self.lt_session.set_settings(settings)
        log.debug("New torrent settings saved")

    def display_libtor_settings(self, ui):

        settings = self.lt_session.get_settings()

        for k in settings:
            v = settings[k]

            if k is None:
                k = ""

            if v is None:
                v = ""

            status = "{0} = {1}".format(k,v)
            ui.update_log(status)

    def save_settings(self, out_file):

        config = ConfigObj()
        config.filename=out_file

        settings = self.lt_session.get_settings()

        for k in settings:
            v = settings[k]
            config[k] = settings[k]
            #v = getattr(settings, k)
            #config[k] = v

        config.write()
        log.debug("Torrent settings have been written")

    def get_settings(self):
        return self.lt_session.get_settings()

    def set_libtor_settings(self, settings):
        pass

