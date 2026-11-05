"""Capture store screenshots of the real inbox. Usage: python screenshots.py <base_url> <out_dir>"""
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

BASE, OUT = sys.argv[1], sys.argv[2]
INBOX = f"{BASE}/odoo/action-sd_smart_chatter_inbox.action_sci_inbox"

for _ in range(90):
    try:
        urllib.request.urlopen(f"{BASE}/web/login", timeout=5)
        break
    except Exception:
        time.sleep(2)


def login(page):
    page.goto(f"{BASE}/web/login")
    page.fill("input[name=login]", "admin")
    page.fill("input[name=password]", "admin")
    page.click("button[type=submit]")
    page.wait_for_url("**/odoo**", timeout=120_000)  # first hit on a new DB builds assets


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    page = browser.new_page(viewport={"width": 1440, "height": 860})
    login(page)
    page.evaluate("sessionStorage.clear()")

    page.goto(INBOX)
    page.click(".o_sci_quick_btn[data-quick=all]")
    page.wait_for_selector(".o_sci_row:has-text('ERP rollout')")
    page.click(".o_sci_row:has-text('ERP rollout')")
    page.wait_for_selector(".o_sci_detail_name:has-text('ERP rollout')")
    page.wait_for_timeout(500)
    page.screenshot(path=f"{OUT}/screenshot_inbox.png")

    page.click(".o_sci_quick_btn[data-quick=needs_action]")
    page.wait_for_selector(".o_sci_row:has-text('Website redesign')")
    page.click(".o_sci_row:has-text('Website redesign')")
    page.wait_for_selector(".o_sci_detail_name:has-text('Website redesign')")
    page.select_option("#o_sci_state", "snoozed")
    page.fill("#o_sci_snooze", "2026-11-13T10:00")
    page.wait_for_timeout(300)
    page.screenshot(path=f"{OUT}/screenshot_snooze.png")

    page.click(".o_sci_open_chatter")
    page.wait_for_selector(".o-mail-Chatter")
    page.wait_for_timeout(800)
    page.screenshot(path=f"{OUT}/screenshot_chatter.png")

    mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, device_scale_factor=2)
    login(mobile)
    mobile.goto(INBOX)
    mobile.wait_for_selector(".o_sci_row")
    mobile.wait_for_timeout(500)
    mobile.screenshot(path=f"{OUT}/screenshot_mobile.png")
    browser.close()
print("screenshots written to", OUT)
