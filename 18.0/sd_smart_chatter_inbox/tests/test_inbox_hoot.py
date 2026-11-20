from odoo.tests import HttpCase, tagged


def _hoot_error_checker(message):
    return "[HOOT]" not in message


@tagged("post_install", "-at_install", "sci")
class TestInboxHoot(HttpCase):

    def test_inbox_unit_tests(self):
        self.browser_js(
            "/web/tests?headless&loglevel=2&preset=desktop&timeout=15000&filter=sd_smart_chatter_inbox",
            "", "", login="admin", timeout=900,
            success_signal="[HOOT] Test suite succeeded", error_checker=_hoot_error_checker)
