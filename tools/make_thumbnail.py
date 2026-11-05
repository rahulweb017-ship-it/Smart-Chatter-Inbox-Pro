"""Generate the animated store thumbnail (banner.gif) and the static hero image.

Usage: python make_thumbnail.py <out_dir>
Everything is drawn here (no third-party artwork). The queue animation cycles a few
leads through Needs Action -> Waiting -> Done -> Snoozed, which is what the app does.
"""
import sys

from PIL import Image, ImageDraw, ImageFont

out = sys.argv[1]
W, H = 1200, 600
TEAL, TEAL_DARK, WHITE = (1, 126, 132), (0, 84, 90), (255, 255, 255)
INK, MUTED, LINE = (33, 37, 41), (108, 117, 125), (226, 232, 235)
STATES = {
    "needs_action": ("Needs Action", (222, 63, 63), (253, 234, 234)),
    "waiting": ("Waiting", (196, 128, 10), (255, 243, 214)),
    "done": ("Done", (32, 140, 84), (223, 245, 233)),
    "snoozed": ("Snoozed", (52, 100, 190), (226, 235, 252)),
}


def font(size, bold=True):
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def gradient():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(TEAL[i] * (1 - t) + TEAL_DARK[i] * t) for i in range(3)))
    # soft decorative circles
    d.ellipse([980, -140, 1320, 200], outline=(40, 160, 168), width=3)
    return img


def badge(d, x, y, state, size=18):
    label, fg, bg = STATES[state]
    f = font(size)
    w = d.textlength(label, font=f) + 26
    d.rounded_rectangle([x, y, x + w, y + size + 14], radius=(size + 14) // 2, fill=bg)
    d.text((x + w / 2, y + (size + 14) / 2), label, font=f, fill=fg, anchor="mm")
    return w


LEADS = [
    ("Website redesign request", "Northwind Studio"),
    ("ERP rollout - 40 users", "Bluefin Logistics"),
    ("Annual support renewal", "Kettle & Co"),
    ("Quote follow-up: 12 licenses", "Lumen Dental Group"),
]
# state of each lead per animation step, and which row is "being worked on"
STEPS = [
    (["needs_action", "needs_action", "needs_action", "needs_action"], 0),
    (["waiting", "needs_action", "needs_action", "needs_action"], 0),
    (["waiting", "done", "needs_action", "needs_action"], 1),
    (["waiting", "done", "snoozed", "needs_action"], 2),
    (["waiting", "done", "snoozed", "waiting"], 3),
    (["done", "done", "snoozed", "waiting"], 0),
]


def frame(states, active, pulse):
    img = gradient()
    d = ImageDraw.Draw(img)
    # left: pitch
    d.text((64, 70), "Smart Chatter", font=font(60), fill=WHITE)
    d.text((64, 140), "Inbox Pro", font=font(60), fill=WHITE)
    d.text((64, 228), "Your Odoo CRM follow-up queue", font=font(28, False), fill=(214, 240, 241))
    for i, line in enumerate(["Status for every lead", "Owners and snooze", "Native chatter & activities"]):
        y = 290 + i * 44
        d.ellipse([64, y + 6, 82, y + 24], fill=(120, 220, 170))
        d.text((96, y + 15), line, font=font(24, False), fill=WHITE, anchor="lm")
    d.rounded_rectangle([64, 452, 300, 524], radius=36, fill=WHITE)
    d.text((182, 488), "Only $19", font=font(34), fill=TEAL_DARK, anchor="mm")
    d.text((320, 488), "Odoo 19 & 20", font=font(24), fill=(214, 240, 241), anchor="lm")

    # right: mock inbox card
    x0, y0, x1, y1 = 600, 60, 1150, 540
    d.rounded_rectangle([x0 + 8, y0 + 12, x1 + 8, y1 + 12], radius=22, fill=(0, 60, 64))
    d.rounded_rectangle([x0, y0, x1, y1], radius=22, fill=WHITE)
    d.rounded_rectangle([x0, y0, x1, y0 + 64], radius=22, fill=(245, 248, 249))
    d.rectangle([x0, y0 + 40, x1, y0 + 64], fill=(245, 248, 249))
    d.text((x0 + 28, y0 + 33), "Smart Chatter Inbox", font=font(24), fill=INK, anchor="lm")
    counts = sum(s == "needs_action" for s in states)
    pill = STATES["needs_action"] if counts else STATES["done"]
    text = f"{counts} need{'s' if counts == 1 else ''} action" if counts else "All caught up"
    d.rounded_rectangle([x1 - 190, y0 + 16, x1 - 24, y0 + 50], radius=17, fill=pill[2])
    d.text((x1 - 107, y0 + 33), text, font=font(17), fill=pill[1], anchor="mm")
    row_h = 104
    for i, ((name, partner), state) in enumerate(zip(LEADS, states)):
        ry = y0 + 64 + i * row_h
        if i == active:
            d.rectangle([x0, ry, x1, ry + row_h], fill=(232, 246, 246))
            d.rectangle([x0, ry, x0 + 6, ry + row_h], fill=TEAL)
        if i:
            d.line([(x0 + 20, ry), (x1 - 20, ry)], fill=LINE, width=2)
        d.text((x0 + 28, ry + 34), name, font=font(23), fill=INK, anchor="lm")
        d.text((x0 + 28, ry + 70), partner, font=font(19, False), fill=MUTED, anchor="lm")
        label, fg, bg = STATES[state]
        bw = d.textlength(label, font=font(18)) + 26
        badge(d, x1 - 28 - bw, ry + 22, state)
        if i == active and pulse:
            cx, cy = x1 - 28 - bw / 2, ry + 38
            d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], outline=(1, 126, 132), width=3)
    return img


frames, durations = [], []
for states, active in STEPS:
    frames.append(frame(states, active, pulse=True))
    durations.append(450)
    frames.append(frame(states, active, pulse=False))
    durations.append(1150)
durations[-1] = 2200
frame(*STEPS[-1], pulse=False).save(f"{out}/banner.png")
frame(*STEPS[3], pulse=False).save(f"{out}/hero.png")
palette = frames[6].quantize(colors=96, method=Image.Quantize.MEDIANCUT)
q = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
q[0].save(f"{out}/banner.gif", save_all=True, append_images=q[1:], duration=durations, loop=0, optimize=True)
print("thumbnail written to", out)
