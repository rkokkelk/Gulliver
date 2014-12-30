import libtorrent
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component

def _set_session_settings(self, session, settings):
    settings_obj = session.settings()
    for k in dir(settings_obj):
        if k.startswith("_"):
            continue
        if k in settings:
            val_type = type(getattr(settings_obj, k))
            v = val_type(settings[k])
            setattr(settings_obj, k, v)

def _set_session_settings(self, session, settings):
    settings_obj = session.settings()
    for k in dir(settings_obj):
        if k.startswith("_"):
            continue
        if k in settings:
            val_type = type(getattr(settings_obj, k))
            v = val_type(settings[k])
            setattr(settings_obj, k, v)
            session.set_settings(settings_obj)

def _apply_settings(self, settings):
    for k, v in settings.iteritems():
        if isinstance(v, unicode):
            try:
                settings[k] = str(v)
            except UnicodeEncodeError:
                del settings[k]
                self._set_session_settings(self._session, settings)


def _convert_from_libtorrent_settings(self, settings_obj):
    settings = {}
    for k in dir(settings_obj):
        if k.startswith("_") or k == "peer_tos":
            continue
        try:
            v = getattr(settings_obj, k)
        except TypeError:
            continue
        val_type = type(v)
        if val_type.__module__ == "libtorrent":
            try:
                v = int(v)
            except ValueError:
                continue
            settings[k] = v
            return settings

_session = libtorrent.session()
print _session.pause()

if hasattr(libtorrent, "high_performance_seed"):
    settings_obj = libtorrent.high_performance_seed()
    print "Has atribute"
