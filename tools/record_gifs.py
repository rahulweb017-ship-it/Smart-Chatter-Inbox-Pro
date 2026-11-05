"""Record animated GIF demos of the real inbox for the store page.

Usage: python record_gifs.py <base_url> <out_dir> [gif names...]
Run tools/seed_demo.py on the database first so the demo leads are in their starting state.
"""
import io
import sys
import time
import urllib.request

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

BASE, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3:]  # optional subset: triage snooze filters chatter mobile
INBOX = f"{BASE}/odoo/action-sd_smart_chatter_inbox.action_sci_inbox"
WIDTH = 1000  # output GIF width
CAPTION_H = 54
TEAL = (1, 126, 132)

CURSOR_JS = """
() => {
  if (document.getElementById('sci-demo-cursor')) return;
  const c = document.createElement('div');
  c.id = 'sci-demo-cursor';
  c.style.cssText = 'position:fixed;z-index:99999;left:-50px;top:-50px;width:22px;height:22px;' +
    'border-radius:50%;background:rgba(230,60,60,.35);border:3px solid #e33c3c;pointer-events:none;' +
    'transform:translate(-50%,-50%);transition:none;box-shadow:0 0 0 0 rgba(230,60,60,.4)';
  document.body.appendChild(c);
}
"""

for _ in range(90):
    try:
        urllib.request.urlopen(f"{BASE}/web/login", timeout=5)
        break
    except Exception:
        time.sleep(2)


def font(size, bold=True):
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


class Recorder:
    def __init__(self, page, width=WIDTH):
        self.page, self.width = page, width
        self.frames, self.durations = [], []
        self.caption = ""
        self.cursor = (-50, -50)

    def _cursor(self, x, y, pressed=False):
        self.page.evaluate(CURSOR_JS)
        self.page.evaluate(
            """([x, y, p]) => { const c = document.getElementById('sci-demo-cursor');
               c.style.left = x + 'px'; c.style.top = y + 'px';
               c.style.boxShadow = p ? '0 0 0 12px rgba(230,60,60,.25)' : 'none'; }""",
            [x, y, pressed])
        self.cursor = (x, y)

    def shot(self, ms=700):
        img = Image.open(io.BytesIO(self.page.screenshot())).convert("RGB")
        img = img.resize((self.width, round(img.height * self.width / img.width)), Image.LANCZOS)
        if self.caption:
            canvas = Image.new("RGB", (img.width, img.height + CAPTION_H), TEAL)
            canvas.paste(img, (0, CAPTION_H))
            d = ImageDraw.Draw(canvas)
            d.text((20, CAPTION_H // 2), self.caption, font=font(24 if self.width > 600 else 20),
                   fill=(255, 255, 255), anchor="lm")
            img = canvas
        self.frames.append(img)
        self.durations.append(ms)

    def move_to(self, selector, steps=4):
        box = self.page.locator(selector).first.bounding_box()
        tx, ty = box["x"] + min(box["width"] / 2, 60), box["y"] + box["height"] / 2
        sx, sy = self.cursor if self.cursor[0] >= 0 else (tx - 200, ty + 120)
        for i in range(1, steps + 1):
            self._cursor(sx + (tx - sx) * i / steps, sy + (ty - sy) * i / steps)
            self.shot(90)
        return selector

    def click(self, selector, hold=700):
        self.move_to(selector)
        self._cursor(*self.cursor, pressed=True)
        self.shot(200)
        self.page.locator(selector).first.click()
        self.page.wait_for_timeout(450)
        self._cursor(*self.cursor, pressed=False)
        self.shot(hold)

    def select(self, selector, value, hold=700):
        self.move_to(selector)
        self._cursor(*self.cursor, pressed=True)
        self.shot(200)
        self.page.select_option(selector, value)
        self.page.wait_for_timeout(300)
        self._cursor(*self.cursor, pressed=False)
        self.shot(hold)

    def type(self, selector, text, hold=700):
        self.move_to(selector)
        self.page.locator(selector).first.click()
        for i in range(0, len(text), 2):
            self.page.keyboard.type(text[i:i + 2])
            self.shot(120)
        self.page.wait_for_timeout(700)
        self.shot(hold)

    def save(self, name):
        self.durations[-1] = 2200  # pause on the last frame before looping
        palette_src = self.frames[len(self.frames) // 2]
        palette = palette_src.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
        frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in self.frames]
        frames[0].save(f"{OUT}/{name}", save_all=True, append_images=frames[1:],
                       duration=self.durations, loop=0, optimize=True, disposal=1)
        print(name, len(frames), "frames")


def login(page):
    page.goto(f"{BASE}/web/login")
    page.fill("input[name=login]", "admin")
    page.fill("input[name=password]", "admin")
    page.click("button[type=submit]")
    page.wait_for_url("**/odoo**", timeout=120_000)


def open_inbox(page, quick="all"):
    page.goto(INBOX)
    page.wait_for_selector(".o_sci_quick_btn")
    page.click(f".o_sci_quick_btn[data-quick={quick}]")
    page.wait_for_selector(".o_sci_row")
    page.wait_for_timeout(600)


def want(name):
    return not ONLY or name in ONLY


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    page = browser.new_page(viewport={"width": 1280, "height": 760})
    login(page)
    page.evaluate("sessionStorage.clear()")

    # 1. Triage: pick a lead, set Waiting + owner, save, find it under Waiting.
    if want("triage"):
        open_inbox(page, "needs_action")
        r = Recorder(page)
        r.caption = "1. Pick a lead from your follow-up queue"
        r.shot(1200)
        r.click(".o_sci_row:has-text('Website redesign')", 1200)
        r.caption = "2. Set the status and a follow-up owner"
        r.select("#o_sci_state", "waiting", 900)
        r.select("#o_sci_owner_select", str(page.locator("#o_sci_owner_select option:has-text('Maya')").get_attribute("value")), 900)
        r.caption = "3. Save: it leaves Needs Action and waits for the customer"
        r.click(".o_sci_save", 1300)
        r.click(".o_sci_quick_btn[data-quick=waiting]", 1600)
        r.save("gif_triage.gif")

    # 2. Snooze to an exact date, see it under Snoozed.
    if want("snooze"):
        open_inbox(page, "needs_action")
        r = Recorder(page)
        r.caption = "Snooze a lead until the day you need it back"
        r.click(".o_sci_row:has-text('Annual support renewal')", 1000)
        r.select("#o_sci_state", "snoozed", 800)
        r.move_to("#o_sci_snooze")
        page.fill("#o_sci_snooze", "2026-11-20T09:30")
        page.wait_for_timeout(200)
        r.shot(1000)
        r.click(".o_sci_save", 1200)
        r.caption = "It disappears from Needs Action and comes back by itself"
        r.click(".o_sci_quick_btn[data-quick=snoozed]", 1800)
        r.save("gif_snooze.gif")

    # 3. Search and filters.
    if want("filters"):
        open_inbox(page, "all")
        r = Recorder(page)
        r.caption = "Search by lead or customer, filter by owner, team or type"
        r.shot(900)
        r.type("#o_sci_search_input", "Harbor", 1200)
        page.fill("#o_sci_search_input", "")
        page.dispatch_event("#o_sci_search_input", "input")
        page.wait_for_timeout(800)
        r.shot(600)
        leo = page.locator("#o_sci_owner option:has-text('Leo')").get_attribute("value")
        r.select("#o_sci_owner", str(leo), 1300)
        r.select("#o_sci_type", "opportunity", 1100)
        r.click(".o_sci_reset", 1300)
        r.save("gif_filters.gif")

    # 4. Native follow-up: schedule activity + open chatter.
    if want("chatter"):
        open_inbox(page, "all")
        r = Recorder(page)
        r.caption = "Schedule a follow-up with Odoo's own activity dialog"
        r.click(".o_sci_row:has-text('ERP rollout')", 900)
        r.click(".o_sci_schedule", 1800)
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)
        r.caption = "Open Chatter: reply in the lead's normal chatter"
        r.shot(500)
        r.click(".o_sci_open_chatter", 600)
        page.wait_for_selector(".o-mail-Chatter")
        page.wait_for_timeout(900)
        r.shot(900)
        page.locator(".o-mail-Chatter").first.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        r.shot(700)
        r.click(".o-mail-Chatter button:has-text('Send message')", 2000)
        r.save("gif_chatter.gif")

    # 5. Phone layout.
    if want("mobile"):
        mobile = browser.new_page(viewport={"width": 390, "height": 760}, is_mobile=True, device_scale_factor=2)
        login(mobile)
        mobile.goto(INBOX)
        mobile.wait_for_selector(".o_sci_row")
        mobile.wait_for_timeout(600)
        r = Recorder(mobile, width=390)
        r.caption = "Works on phones"
        r.shot(1200)
        r.click(".o_sci_filters_toggle", 1300)
        r.click(".o_sci_quick_btn[data-quick=all]", 900)
        r.click(".o_sci_row:has-text('Quote follow-up')", 1600)
        mobile.mouse.wheel(0, 400)
        mobile.wait_for_timeout(400)
        r.shot(1400)
        r.click(".o_sci_back", 1400)
        r.save("gif_mobile.gif")
    browser.close()
print("gifs written to", OUT)
