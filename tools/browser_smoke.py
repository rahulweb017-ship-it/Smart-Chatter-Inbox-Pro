"""Cross-browser smoke test of the real inbox UI.

Usage: python tools/browser_smoke.py <base_url> <chromium|firefox> [login] [password]
Exits non-zero on the first failed check.
"""
import sys

from playwright.sync_api import expect, sync_playwright

BASE, ENGINE = sys.argv[1], sys.argv[2]
LOGIN = sys.argv[3] if len(sys.argv) > 3 else "admin"
PASSWORD = sys.argv[4] if len(sys.argv) > 4 else "admin"
INBOX = f"{BASE}/odoo/action-sd_smart_chatter_inbox.action_sci_inbox"
errors = []


def login(page):
    page.goto(f"{BASE}/web/login")
    page.fill("input[name=login]", LOGIN)
    page.fill("input[name=password]", PASSWORD)
    page.click("button[type=submit]")
    page.wait_for_url("**/odoo**", timeout=120_000)  # first hit on a new DB builds assets


def check(label, fn):
    try:
        fn()
        print(f"  ok   {label}")
    except Exception as exc:  # noqa: BLE001
        print(f"  FAIL {label}: {str(exc).splitlines()[0][:200]}")
        errors.append(label)


with sync_playwright() as p:
    launcher = p.chromium.launch(channel="chrome") if ENGINE == "chromium" else p.firefox.launch()
    page = launcher.new_page(viewport={"width": 1440, "height": 900})
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    login(page)
    page.evaluate("sessionStorage.clear()")
    page.goto(INBOX)

    check("styles applied (3-pane grid)", lambda: expect(page.locator(".o_sci_body")).to_have_css("display", "grid"))
    page.click(".o_sci_quick_btn[data-quick=all]")
    rows = page.locator(".o_sci_row")
    check("rows listed", lambda: expect(rows.first).to_be_visible())
    first_name = rows.first.locator(".o_sci_row_name").inner_text()
    rows.first.click()
    check("detail pane loads", lambda: expect(page.locator(".o_sci_detail_name")).to_have_text(first_name))
    page.select_option("#o_sci_state", "waiting")
    page.click(".o_sci_save")
    check("save notifies", lambda: expect(page.locator(".o_notification").filter(has_text="Inbox status saved")).to_be_visible())
    page.click(".o_sci_quick_btn[data-quick=waiting]")
    check("item appears under Waiting", lambda: expect(
        page.locator(".o_sci_row").filter(has_text=first_name).locator(".o_sci_badge_waiting")).to_be_visible())
    page.select_option("#o_sci_state", "snoozed")
    check("snooze input shown with time zone", lambda: (
        expect(page.locator("#o_sci_snooze")).to_be_visible(),
        expect(page.locator("label[for=o_sci_snooze]")).to_contain_text("GMT")))
    page.select_option("#o_sci_state", "waiting")
    page.click(".o_sci_schedule")
    check("activity dialog opens", lambda: expect(page.locator(".modal .o_form_view")).to_be_visible())
    page.click(".modal-header .btn-close")
    check("keyboard navigation", lambda: (
        page.locator(".o_sci_rows").focus(), page.keyboard.press("ArrowDown"),
        expect(page.locator(".o_sci_row.o_sci_selected")).to_have_count(1)))
    page.click(".o_sci_open_chatter")
    check("Open Chatter shows native chatter", lambda: expect(page.locator(".o-mail-Chatter")).to_be_visible())
    page.go_back()
    check("filters preserved after Back", lambda: expect(
        page.locator(".o_sci_quick_btn.active")).to_have_attribute("data-quick", "waiting"))

    mobile = launcher.new_page(viewport={"width": 390, "height": 844})
    login(mobile)
    mobile.goto(INBOX)
    check("phone: list shown, detail hidden", lambda: (
        expect(mobile.locator(".o_sci_row").first).to_be_visible(),
        expect(mobile.locator(".o_sci_detail")).to_be_hidden()))
    mobile.locator(".o_sci_row").first.click()
    check("phone: detail replaces list, back works", lambda: (
        expect(mobile.locator(".o_sci_detail_name")).to_be_visible(),
        expect(mobile.locator(".o_sci_list")).to_be_hidden(),
        mobile.click(".o_sci_back"),
        expect(mobile.locator(".o_sci_list")).to_be_visible()))
    check("phone: no horizontal overflow", lambda: (
        mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1") or (_ for _ in ()).throw(
            AssertionError("page scrolls horizontally"))))
    launcher.close()

page_errors = [e for e in errors if e.startswith("pageerror")]
print(f"{ENGINE}: {'PASS' if not errors else 'FAIL'} ({len(errors)} problem(s)) {page_errors[:3]}")
sys.exit(1 if errors else 0)
