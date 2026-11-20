from odoo.addons.web.tests.test_js import qunit_error_checker
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install", "sci")
class TestInboxQUnit(HttpCase):
    """Odoo 17 has no Hoot: run the inbox UI unit tests (static/tests/inbox.test.js) with QUnit."""

    def test_inbox_unit_tests(self):
        self.browser_js(
            "/web/tests?module=sd_smart_chatter_inbox", "", "", login="admin", timeout=900,
            error_checker=qunit_error_checker)
