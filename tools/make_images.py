"""Generate the original app icon and store banner (no third-party assets)."""
import sys
from PIL import Image, ImageDraw, ImageFont

out = sys.argv[1]
TEAL, TEAL_DARK, WHITE = (1, 126, 132), (0, 90, 96), (255, 255, 255)
COLORS = [(222, 63, 63), (230, 160, 30), (40, 160, 100), (60, 110, 200)]


def font(size, bold=True):
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_mark(d, x, y, s):
    """Speech bubble with a 4-colour status queue inside."""
    d.rounded_rectangle([x, y, x + s, y + s * 0.78], radius=s * 0.16, fill=WHITE)
    d.polygon([(x + s * 0.2, y + s * 0.74), (x + s * 0.2, y + s * 0.98), (x + s * 0.44, y + s * 0.76)], fill=WHITE)
    for i, color in enumerate(COLORS):
        top = y + s * (0.12 + i * 0.15)
        d.ellipse([x + s * 0.12, top, x + s * 0.22, top + s * 0.1], fill=color)
        d.rounded_rectangle([x + s * 0.28, top + s * 0.02, x + s * (0.88 - i * 0.1), top + s * 0.08],
                            radius=s * 0.03, fill=(200, 212, 214))


icon = Image.new("RGB", (256, 256), TEAL)
d = ImageDraw.Draw(icon)
d.rectangle([0, 200, 256, 256], fill=TEAL_DARK)
draw_mark(d, 40, 36, 176)
icon.save(f"{out}/icon.png")

banner = Image.new("RGB", (1200, 600), TEAL)
d = ImageDraw.Draw(banner)
d.rectangle([0, 470, 1200, 600], fill=TEAL_DARK)
draw_mark(d, 80, 120, 300)
d.text((440, 140), "Smart Chatter Inbox Pro", font=font(56), fill=WHITE)
d.text((440, 220), "Your CRM follow-up queue", font=font(36, False), fill=WHITE)
for i, (label, color) in enumerate(zip(["Needs Action", "Waiting", "Done", "Snoozed"], COLORS)):
    x = 440 + i * 180
    d.rounded_rectangle([x, 300, x + 165, 350], radius=25, fill=color)
    d.text((x + 82, 325), label, font=font(22), fill=WHITE, anchor="mm")
d.text((80, 510), "Owners - Snooze - Secure filters - Native chatter & activities", font=font(30, False), fill=WHITE)
d.text((1120, 535), "$19", font=font(48), fill=WHITE, anchor="rm")
banner.save(f"{out}/banner.png")
print("images written to", out)
