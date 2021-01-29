from pkg_resources import resource_filename

from functools import lru_cache


class ReactUIService:
    def __init__(self, mode="dev", dev_prefix="http://localhost:3000"):
        self._mode = mode
        self._dev_prefix = dev_prefix
        self._ui_root = resource_filename("checkmate", "static/static/ui")


    def _parse_html(self):
        index_html = self._ui_root + "/index.html"



    def js(self):
        if self._mode == "dev":
            for tail in ("/static/js/bundle.js", "/static/js/0.chunk.js", "/static/js/main.chunk.js"):
                yield self._dev_prefix + tail
            return




    def css(self):
        if self._mode == "dev":
            return