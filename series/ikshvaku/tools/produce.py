"""Long-form 16:9 documentary: "The Ikshvaku Dynasty". Reuses the Ramayan series tools (spend ledger, voice, music,
sub-pixel Ken Burns) and adds the family-tree graphic and long-form captions.

  python3 produce.py plan       # word count, image count, cost estimate against the budget
  python3 produce.py voice      # narration (MiniMax Deep_Voice_Man), one call per beat, cached by text
  python3 produce.py images     # 16:9 stills for kind=image beats, most important first, until the budget is used
  python3 produce.py trees      # family-tree frames (free, drawn in code)
  python3 produce.py compose    # out/Ikshvaku_Dynasty.mp4

script.json (from the research workflow): {title, chapters:[{title, beats:[{text, visual, kind, tree_focus}]}], lineage, sources}
"""
import concurrent.futures as cf
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SERIES = ROOT.parent / "ramayan-60"
sys.path.insert(0, str(SERIES / "tools"))
os.environ.setdefault("FAL_BUDGET", "18.70")          # ledger was $14.87 when the user said $4 was left
import fal                                            # noqa: E402  (shared ledger in ramayan-60/spend.json)

W, H, FPS = 1920, 1080, 30
VOICE = "Deep_Voice_Man"
STYLE = json.loads((SERIES / "characters.json").read_text())["style"]
GAP, LEAD, TAIL = 0.55, 1.0, 3.0
IMG_PRICE, VOICE_PER_1K = 0.039, 0.10


def load():
    s = json.loads((ROOT / "script.json").read_text())
    beats = []
    for ci, ch in enumerate(s["chapters"]):
        for bi, b in enumerate(ch["beats"]):
            beats.append({**b, "chapter": ci, "chapter_title": ch["title"], "first": bi == 0})
    return s, beats


def key(text):
    return hashlib.sha1((VOICE + text).encode()).hexdigest()[:10]


def img_path(b):
    return ROOT / "images" / f"{hashlib.sha1(b['visual'].encode()).hexdigest()[:10]}.png"


# ---------------------------------------------------------------- plan
def plan():
    s, beats = load()
    words = sum(len(b["text"].split()) for b in beats)
    chars = sum(len(b["text"]) for b in beats)
    kinds = {k: sum(b["kind"] == k for b in beats) for k in ("image", "tree", "reuse")}
    voiced = (ROOT / "audio" / "narration.wav").exists()
    voice_cost = 0.0 if voiced else VOICE_PER_1K * chars / 1000      # already paid once the narration exists
    left = fal.BUDGET - fal._spend()
    n_img = int(max(0, left - voice_cost - 0.05) // IMG_PRICE)
    print(f"{len(s['chapters'])} chapters, {len(beats)} beats, {words} words (~{words / 2.5 / 60:.1f} min speech)")
    print(f"kinds {kinds}; voice ~${voice_cost:.2f}; budget left ${left:.2f} -> {n_img} images affordable")
    return n_img


# ---------------------------------------------------------------- voice
def voice_one(text):
    dst = ROOT / "audio" / f"b_{key(text)}.wav"
    if dst.exists():
        return dst
    r = fal.run("fal-ai/minimax/speech-02-hd", {"text": text, "output_format": "url",
                "voice_setting": {"voice_id": VOICE, "speed": 0.9, "vol": 1, "pitch": 0, "emotion": "neutral"}})
    if not (r.get("audio") or {}).get("url"):
        raise RuntimeError(("CONTENT BLOCKED: " if "content_policy" in str(r) else "no audio: ") + text)
    mp3 = dst.with_suffix(".mp3"); fal.download(r["audio"]["url"], mp3)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100", str(dst)], check=True)
    mp3.unlink(); return dst


def voice():
    import numpy as np, soundfile as sf
    s, beats = load(); (ROOT / "audio").mkdir(exist_ok=True)
    blocked = []
    def go(b):
        try: return voice_one(b["text"])
        except RuntimeError as e:
            blocked.append(str(e)); return None
    with cf.ThreadPoolExecutor(4) as ex:
        paths = list(ex.map(go, beats))
    if blocked:
        print("\n".join(blocked)); sys.exit(f"{len(blocked)} beat(s) blocked; reword them in script.json and run again")
    parts, t, timing = [np.zeros(int(LEAD * 44100))], LEAD, []
    for b, p in zip(beats, paths):
        x, sr = sf.read(p); x = x if x.ndim == 1 else x.mean(1)
        idx = np.where(np.abs(x) > 0.01 * np.abs(x).max())[0]; x = x[max(0, idx[0] - 1300): idx[-1] + 3500]
        pause = GAP + (0.9 if b["first"] and timing else 0)          # a longer breath before each chapter
        if b["first"] and timing:
            parts.append(np.zeros(int(0.9 * sr))); t += 0.9
        timing.append({"start": round(t, 3), "end": round(t + len(x) / sr, 3)})
        parts += [x, np.zeros(int(GAP * sr))]; t += len(x) / sr + GAP
    parts.append(np.zeros(int(TAIL * 44100)))
    y = np.concatenate(parts).astype(np.float32); sf.write(ROOT / "audio" / "narration.wav", y, 44100)
    (ROOT / "audio" / "timing.json").write_text(json.dumps({"duration": round(len(y) / 44100, 2), "beats": timing}, indent=1))
    print(f"narration {len(y) / 44100 / 60:.1f} min, {len(beats)} beats; estimated spend ${fal._spend():.2f}")


# ---------------------------------------------------------------- images
CHARS = json.loads((SERIES / "characters.json").read_text())["characters"]


def refs_for(visual):
    out = []
    for name in ("rama_forest" if False else "rama", "dasharatha", "vasishtha", "vishwamitra", "sita", "lakshmana", "hanuman", "janaka"):
        c = CHARS.get(name)
        if c and any(re.search(r"\b" + m + r"\b", visual) for m in c["match"] if m[0].isupper()):
            out.append(name)
    return out[:3]


def image_one(b):
    dst = img_path(b)
    if dst.exists():
        return "exists"
    names = refs_for(b["visual"])
    p = (f"{STYLE}. Full-bleed 16:9 picture filling the whole frame (no black bars), from Indian epic history (the Ikshvaku dynasty). Scene: {b['visual']}. "
         + (f"Characters (match the reference images): {'; '.join(CHARS[n]['desc'] for n in names)}. " if names else "")
         + "Ancient India, majestic and calm, characters fully clothed. No signboards or writing; absolutely no text, letters or captions.")
    tries = []
    if names:
        tries.append(("fal-ai/nano-banana/edit", {"prompt": p, "image_urls": [fal.data_uri(SERIES / "characters" / f"{n}.png") for n in names],
                                                  "num_images": 1, "aspect_ratio": "16:9", "output_format": "png"}))
    tries.append(("fal-ai/nano-banana", {"prompt": p, "num_images": 1, "aspect_ratio": "16:9", "output_format": "png"}))
    for model, inp in tries:
        try:
            r = fal.run(model, inp)
        except fal.BudgetExceeded:
            raise
        except Exception as e:
            r = {"error": str(e)}
        if r.get("images"):
            fal.download(r["images"][0]["url"], dst); return model
    return f"FAILED {str(r)[:120]}"


def images():
    s, beats = load(); (ROOT / "images").mkdir(exist_ok=True)
    want = [b for b in beats if b["kind"] == "image" and not img_path(b).exists()]
    n = plan()
    # if the budget cannot cover every image beat, keep an even spread (chapter openers first)
    if n < len(want):
        firsts = [b for b in want if b["first"]]; rest = [b for b in want if not b["first"]]
        k = max(0, n - len(firsts)); step = len(rest) / k if k else 1
        want = firsts + [rest[int(i * step)] for i in range(k)]
        print(f"budget covers {n} of the image beats; the others re-show nearby pictures")
    def go(b):
        try: return image_one(b)
        except fal.BudgetExceeded as e: return f"BUDGET {e}"
    with cf.ThreadPoolExecutor(5) as ex:
        res = list(ex.map(go, want))
    print({r.split()[0]: res.count(r) for r in set(res)}, f"estimated spend ${fal._spend():.2f}")


# ---------------------------------------------------------------- family tree (free)
def tree_frame(lineage, focus, dst):
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    F = lambda s, b=True: ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if b else ''}.ttf", s)
    serif = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", s)
    S = 2                                                   # drawn at 2x, so camera moves stay sharp
    im = Image.new("RGB", (W * S, H * S), (22, 17, 12)); d = ImageDraw.Draw(im)
    for y in range(H * S):                                   # warm vertical gradient
        c = int(18 + 14 * (1 - abs(y / (H * S) - 0.45)))
        d.line([(0, y), (W * S, y)], fill=(c + 8, c, c - 6))
    names = [n for n in lineage]
    focus_set = {f.strip().lower() for f in focus.split(",") if f.strip()}
    fi = [i for i, n in enumerate(names) if n.lower() in focus_set] or [0]
    centre = sum(fi) / len(fi)
    span = 4.6                                               # rows visible above and below the focus
    cx = W * S * 0.62; row = H * S / (2 * span + 1.2)
    gold, cream, dim = (236, 190, 92), (226, 214, 190), (120, 104, 84)
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    for i, n in enumerate(names):
        y = H * S / 2 + (i - centre) * row
        if y < -row or y > H * S + row:
            continue
        on = i in fi; seen = i < min(fi)
        if i + 1 < len(names) and names[i + 1] != "..." and n != "...":
            d.line([(cx, y + 26 * S), (cx, y + row - 26 * S)], fill=gold if seen or on else dim, width=4 * S)
        if n == "...":
            d.text((cx, y), "· · ·", font=F(30 * S), fill=dim, anchor="mm"); continue
        r = (22 if on else 13) * S
        if on:
            g.ellipse([cx - 90 * S, y - 90 * S, cx + 90 * S, y + 90 * S], fill=(236, 190, 92, 70))
        d.ellipse([cx - r, y - r, cx + r, y + r], fill=gold if on else ((180, 150, 90) if seen else (60, 50, 40)),
                  outline=gold if (on or seen) else dim, width=3 * S)
        d.text((cx + (44 if on else 34) * S, y), n.upper() if on else n, font=(serif(52 * S) if on else F(30 * S, False)),
               fill=gold if on else (cream if seen else dim), anchor="lm")
        d.text((cx - 40 * S, y), str(i + 1) if names[0] != "..." else "", font=F(20 * S, False), fill=dim, anchor="rm")
    im.paste(Image.alpha_composite(im.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(40 * S))).convert("RGB"))
    d = ImageDraw.Draw(im)
    d.text((110 * S, H * S * 0.40), "THE IKSHVAKU LINE", font=F(40 * S), fill=(200, 160, 80), anchor="lm")
    d.text((110 * S, H * S * 0.40 + 62 * S), "The Solar Dynasty of Ayodhya", font=F(28 * S, False), fill=cream, anchor="lm")
    gen = names.index(names[fi[0]]) + 1
    d.text((110 * S, H * S * 0.40 + 120 * S), f"Generation {gen} from Brahma", font=F(24 * S, False), fill=dim, anchor="lm")
    im.save(dst)


def trees():
    s, beats = load(); d = ROOT / "trees"; d.mkdir(exist_ok=True)
    for b in beats:
        if b["kind"] == "tree":
            f = d / f"{hashlib.sha1(b.get('tree_focus', '').encode()).hexdigest()[:10]}.png"
            if not f.exists():
                tree_frame(s["lineage"], b.get("tree_focus", ""), f)
    print(f"{len(list(d.glob('*.png')))} tree frames")


# ---------------------------------------------------------------- compose
def compose():
    import numpy as np
    from PIL import Image
    import compose as C                                       # the series compositor: frame_at (sub-pixel Ken Burns), sh
    C.W, C.H = W, H
    s, beats = load(); tm = json.loads((ROOT / "audio" / "timing.json").read_text())
    total = tm["duration"]; T = tm["beats"]
    out = ROOT / "out"; out.mkdir(exist_ok=True); tmp = out / "tmp"; tmp.mkdir(exist_ok=True)
    # pick a picture for every beat
    last_img, pics = None, []
    for b in beats:
        if b["kind"] == "tree":
            pics.append((ROOT / "trees" / f"{hashlib.sha1(b.get('tree_focus', '').encode()).hexdigest()[:10]}.png", "tree"))
            continue
        f = img_path(b)
        if f.exists():
            last_img = f; pics.append((f, "img"))
        else:
            pics.append((last_img, "reuse"))
    first_img = next((p for p, k in pics if k == "img"), None)
    pics = [(p or first_img, k) for p, k in pics]
    shots = []                                                # (file, t0, t1, crop)
    for i, (b, (f, k)) in enumerate(zip(beats, pics)):
        t0 = 0.0 if i == 0 else T[i]["start"] - 0.25
        t1 = total if i == len(beats) - 1 else T[i + 1]["start"] - 0.25
        if k == "tree":
            shots.append((f, t0, t1, "wide"))
        elif k == "reuse":
            shots.append((f, t0, t1, "left" if i % 2 else "right"))
        elif t1 - t0 > 9:
            m = (t0 + t1) / 2; shots += [(f, t0, m, "wide"), (f, m, t1, "close")]
        else:
            shots.append((f, t0, t1, "wide"))
    cache = {}
    def img(f):
        if f not in cache:
            if len(cache) > 6: cache.pop(next(iter(cache)))
            im = Image.open(f).convert("RGB")
            a = np.asarray(im.convert("L")); dark = a.mean(1) < 10      # trim letterbox bars the model painted in
            top = int(np.argmax(~dark)); bot = int(np.argmax(~dark[::-1]))
            if top > 6 or bot > 6:
                im = im.crop((0, top + 2, im.width, im.height - bot - 2))
            if im.width < W * 1.6: im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
            cache[f] = im
        return cache[f]
    video = tmp / "video.mp4"
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-vf", "eq=saturation=1.05:contrast=1.03,vignette=PI/6", "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "18", "-pix_fmt", "yuv420p", str(video)], stdin=subprocess.PIPE)
    XF = 0.7; MOVES = ["in", "right", "out", "up", "in", "left", "out", "down"]
    for k in range(int(round(total * FPS))):
        t = k / FPS
        i = max(j for j, sh in enumerate(shots) if sh[1] <= t + 1e-6)
        def render(j):
            f, a, z, crop = shots[j]; a2 = a - (XF if j else 0); u = min(max((t - a2) / (z - a2 + XF), 0), 1)
            mv = "in" if crop == "tree" else MOVES[j % len(MOVES)]
            return np.asarray(C.frame_at(img(f), mv, u, crop if crop != "tree" else "wide"), dtype=np.float32)
        fr = render(i)
        if i + 1 < len(shots) and t > shots[i + 1][1] - XF:
            w = (t - (shots[i + 1][1] - XF)) / XF; w = w * w * (3 - 2 * w); fr = fr * (1 - w) + render(i + 1) * w
        enc.stdin.write(fr.clip(0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    # captions: sentence chunks at the bottom; chapter titles as lower-third cards
    def at(t):
        h = int(t // 3600); m = int(t % 3600 // 60); return f"{h}:{m:02d}:{t % 60:05.2f}"
    ev = []
    for i, (b, tb) in enumerate(zip(beats, T)):
        words = b["text"].split(); span = tb["end"] - tb["start"]; n = len(words)
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 8 or (len(cur) >= 4 and re.search(r"[.,;:!?]$", w)):
                chunks.append(cur); cur = []
        if cur: chunks.append(cur)
        t = tb["start"]
        for c in chunks:
            d = span * len(c) / n
            ev.append(f"Dialogue: 0,{at(t)},{at(t + d)},Sub,,0,0,0,,{' '.join(c)}"); t += d
        if b["first"]:
            ev.append(f"Dialogue: 1,{at(tb['start'] - 0.3)},{at(tb['start'] + 4.2)},Chap,,0,0,0,,{{\\fad(400,500)}}{b['chapter_title'].upper()}")
    ev.append(f"Dialogue: 1,{at(0.3)},{at(6.5)},Title,,0,0,0,,{{\\fad(600,700)}}{s['title'].upper()}")
    ass = tmp / "captions.ass"
    ass.write_text(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Montserrat ExtraBold,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0.5,0,1,4,2,2,160,160,64,1
Style: Chap,Montserrat ExtraBold,58,&H005CBEEC,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,3,0,1,5,2,7,110,110,90,1
Style: Title,Montserrat ExtraBold,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,2,0,1,6,3,5,120,120,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n")
    music = ROOT / "audio" / "music.wav"
    subprocess.run(["python3", str(SERIES / "tools" / "music.py"), f"{total + 1:.1f}", str(music), "--seed", "108", "--solo"], check=True)
    final = out / "Ikshvaku_Dynasty.mp4"
    fc = ("[1:a]aresample=44100,highpass=f=60,pan=stereo|c0=c0|c1=c0,loudnorm=I=-16:TP=-1.5:LRA=11,apad,asplit=2[v1][v2];"
          "[2:a]volume=0.09[m];[m][v1]sidechaincompress=threshold=0.04:ratio=4:attack=30:release=600[md];"
          f"[v2][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1:LRA=11,atrim=0:{total:.3f}[a];"
          f"[0:v]subtitles='{ass}':fontsdir='{SERIES / 'fonts'}'[vv]")
    C.sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(ROOT / "audio" / "narration.wav"), "-i", str(music),
          "-filter_complex", fc, "-map", "[vv]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", str(final)])
    print(f"{final}  ({total / 60:.1f} min)")


if __name__ == "__main__":
    {"plan": plan, "voice": voice, "images": images, "trees": trees, "compose": compose}[sys.argv[1]]()
