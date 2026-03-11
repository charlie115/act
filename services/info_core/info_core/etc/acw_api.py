from _acw_common import ensure_acw_common_on_path

ensure_acw_common_on_path()

from acw_common.clients.acw_api import AcwApi as SharedAcwApi


class AcwApi(SharedAcwApi):
    def __init__(self, acw_url, node, prod):
        super().__init__(acw_url, node, prod, message_content_mode="inline")
