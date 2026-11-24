import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W, H = 1280, 720
F = "../ramayan-60/fonts/Montserrat-ExtraBold.ttf"
im = Image.open("images/" + __import__("sys").argv[1]).convert("RGB")
a = np.asarray(im.convert("L")); dark = a.mean(1) < 10
t, b = int(np.argmax(~dark)), int(np.argmax(~dark[::-1]))
im = im.crop((0, t + 2, im.width, im.height - b - 2))
s = H * 1.08 / im.height; im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
c = Image.new("RGB", (W, H), (20, 12, 4))
c.paste(im, (W - im.width + 230, (H - im.height) // 2))
# warm dark fade on the left for text
g = np.zeros((H, W), np.float32); x = np.linspace(0, 1, W)
g[:] = np.clip(1.05 - x / 0.62, 0, 0.93)
shade = Image.new("RGB", (W, H), (18, 9, 2))
c = Image.composite(shade, c, Image.fromarray((g * 255).astype("uint8")))
d = ImageDraw.Draw(c)
def text(xy, s, size, fill, stroke=6, glow=None):
    f = ImageFont.truetype(F, size)
    if glow:
        l = Image.new("RGBA", (W, H)); ImageDraw.Draw(l).text(xy, s, font=f, fill=glow)
        c.paste(l.filter(ImageFilter.GaussianBlur(18)), (0, 0), l.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(c).text(xy, s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(10, 5, 0))
text((48, 60), "THE", 54, (255, 255, 255))
text((40, 118), "IKSHVAKU", 138, (255, 200, 70), 8, glow=(255, 150, 0, 200))
text((46, 268), "DYNASTY", 112, (255, 255, 255), 8)
# red pill
d = ImageDraw.Draw(c); f = ImageFont.truetype(F, 46); s = "THE COMPLETE LINEAGE"
w = d.textlength(s, font=f)
d.rounded_rectangle((44, 420, 44 + w + 44, 494), 14, fill=(205, 20, 20))
d.text((66, 428), s, font=f, fill=(255, 255, 255))
f = ImageFont.truetype(F, 40)
d.text((48, 530), "BRAHMA  →  RAMA  →  SUMITRA", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38), fill=(255, 225, 150), stroke_width=4, stroke_fill=(10, 5, 0))
c.save("out/Ikshvaku_Thumbnail.jpg", quality=92)
