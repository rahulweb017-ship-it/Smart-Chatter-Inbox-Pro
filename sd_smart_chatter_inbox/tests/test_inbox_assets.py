from pathlib import Path

import sass

from odoo.tests import BaseCase, tagged


@tagged("post_install", "-at_install", "sci")
class TestInboxAssets(BaseCase):

    def test_scss_compiles(self):
        """A SCSS error does not fail the install: Odoo silently falls back to unstyled pages."""
        scss_dir = Path(__file__).parent.parent / "static" / "src" / "scss"
        for path in scss_dir.glob("*.scss"):
            with self.subTest(path=path.name):
                sass.compile(string=path.read_text(encoding="utf-8"))
