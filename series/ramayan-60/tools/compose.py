"""Assemble one finished 9:16 episode: two stills per beat with slow camera moves and crossfades, cut to the narration, channel-style captions, title, end line, music.

  python3 compose.py 1          -> ep01/out/Ramayan_Ep01.mp4

Captions follow the channel: two or three words at a time in the middle of the frame, bold white caps with
a black outline; the spoken word turns red and pops. Word times come from each beat's audio span,
shared out by letters (the voice model gives no word timestamps).
"""
import json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
END_HOLD = 2.6                         # seconds after the narration for the on-screen line
MOODS = {}                             # per-episode music mood overrides, e.g. {13: "grief"}


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-1500:])
    return r.stdout


def dur(p):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def ass_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def esc(s):
    return s.replace("{", "(").replace("}", ")")


def captions(ep, timing, total, path):
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat ExtraBold,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,7,3,5,60,60,0,1
Style: Title,Montserrat ExtraBold,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,6,3,8,70,70,190,1
Style: Kicker,Montserrat ExtraBold,40,&H0046C8F0,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,4,0,1,4,2,8,70,70,140,1
Style: End,Montserrat ExtraBold,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,7,3,5,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    ev.append(f"Dialogue: 1,{ass_time(0.15)},{ass_time(3.4)},Kicker,,0,0,0,,{{\\fad(250,300)}}EPISODE {ep['ep']}")
    ev.append(f"Dialogue: 1,{ass_time(0.25)},{ass_time(3.4)},Title,,0,0,0,,{{\\fad(250,300)\\fscx85\\fscy85\\t(0,250,\\fscx100\\fscy100)}}{esc(ep['title'].upper())}")
    RED = "&H002A2AE6&"
    for b in timing["beats"]:
        words = b["text"].replace("—", " ").split()
        letters = [max(1, len(re.sub(r"[^A-Za-z]", "", w))) + 1.5 for w in words]   # +1.5: a short beat per word
        span = b["end"] - b["start"]; tot = sum(letters); t = b["start"]; wt = []
        for w, l in zip(words, letters):
            wt.append((w, t, t + span * l / tot)); t += span * l / tot
        chunks, cur = [], []
        for item in wt:                                    # 2 words per card, 3 when the words are short
            cur.append(item)
            n = sum(len(x[0]) for x in cur)
            if len(cur) == 3 or (len(cur) == 2 and n > 9) or re.search(r"[.,!?;:]$", item[0]):
                chunks.append(cur); cur = []
        if cur: chunks.append(cur)
        for ci, ch in enumerate(chunks):
            c_end = chunks[ci + 1][0][1] if ci + 1 < len(chunks) else ch[-1][2] + 0.25
            for wi, (w, ws, we) in enumerate(ch):
                s, e = ws, (ch[wi + 1][1] if wi + 1 < len(ch) else c_end)
                parts = []
                for wj, (w2, _, _) in enumerate(ch):
                    txt = esc(re.sub(r"[“”\"]", "", w2).upper())
                    parts.append(f"{{\\c{RED}\\fscx112\\fscy112\\t(0,90,\\fscx100\\fscy100)}}{txt}{{\\c&H00FFFFFF&}}" if wj == wi else txt)
                pop = "\\fscx70\\fscy70\\t(0,110,\\fscx100\\fscy100)" if wi == 0 else ""
                ev.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Cap,,0,0,0,,{{\\pos({W//2},{int(H*0.60)}){pop}}}" + " ".join(parts))
    end_t = timing["beats"][-1]["end"] + 0.35
    ev.append(f"Dialogue: 2,{ass_time(end_t)},{ass_time(total)},End,,0,0,0,,{{\\fad(400,0)\\pos({W//2},{int(H*0.5)})\\fscx90\\fscy90\\t(0,400,\\fscx100\\fscy100)\\c&H0046C8F0&}}{esc(ep['onscreen'].upper())}")
    path.write_text(hdr + "\n".join(ev) + "\n")


XFADE = 0.5
MOVES = ["in", "out", "up", "down", "in", "left", "out", "right"]


def shot_list(ep, beats, total, img_dir):
    sys.path.insert(0, str(ROOT / "tools")); from images import shot_path
    shots = []
    for i, (b, beat) in enumerate(zip(beats, ep["beats"])):
        t0 = 0.0 if i == 0 else b["start"] - 0.2
        t1 = total if i == len(beats) - 1 else beats[i + 1]["start"] - 0.2
        mid = t0 + (t1 - t0) * 0.5
        for sh, (a, z) in (("a", (t0, mid)), ("b", (mid, t1))):
            f = shot_path(img_dir, beat, sh); up = f.with_name(f.stem + "_up.png")
            shots.append(((up if up.exists() else f), a, z))
    return shots


def frame_at(img, move, u):
    """Crop window for progress u in [0,1]: ease in/out, zoom 1.0-1.10, or a 7% drift at zoom 1.08."""
    import numpy as np
    from PIL import Image
    e = u * u * (3 - 2 * u)
    iw, ih = img.size; base = max(W / iw, H / ih)
    if move in ("in", "out"):
        z = 1.0 + 0.10 * (e if move == "in" else 1 - e); dx = dy = 0.0
    else:
        z = 1.08; k = (e - 0.5) * 0.07
        dx = k * iw if move in ("left", "right") else 0.0; dy = k * ih if move in ("up", "down") else 0.0
        if move in ("left", "up"): dx, dy = -dx, -dy
    s = base * z; cw, ch = W / s, H / s
    cx, cy = iw / 2 + dx * 0.5, ih / 2 + dy * 0.5
    cx = min(max(cx, cw / 2), iw - cw / 2); cy = min(max(cy, ch / 2), ih - ch / 2)
    x0, y0 = cx - cw / 2, cy - ch / 2
    return img.transform((W, H), Image.AFFINE, (cw / W, 0, x0, 0, ch / H, y0), resample=Image.BICUBIC)


def render_stills(ep, beats, total, img_dir, out):
    import numpy as np
    from PIL import Image
    shots = shot_list(ep, beats, total, img_dir)
    imgs = [Image.open(f).convert("RGB") for f, _, _ in shots]
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-vf", "eq=saturation=1.05:contrast=1.03,vignette=PI/6", "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "16", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    n = int(round(total * FPS))
    for k in range(n):
        t = k / FPS
        i = max(j for j, (_, a, _) in enumerate(shots) if a <= t + 1e-6)
        def render(j):
            _, a, z = shots[j]; a2 = a - (XFADE if j else 0); u = min(max((t - a2) / (z - a2 + XFADE), 0), 1)
            return np.asarray(frame_at(imgs[j], MOVES[j % len(MOVES)], u), dtype=np.float32)
        fr = render(i)
        if i + 1 < len(shots) and t > shots[i + 1][1] - XFADE:            # crossfade into the next shot
            w = (t - (shots[i + 1][1] - XFADE)) / XFADE; w = w * w * (3 - 2 * w)
            fr = fr * (1 - w) + render(i + 1) * w
        enc.stdin.write(fr.clip(0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()


def main(n):
    ep = {e["ep"]: e for e in json.loads((ROOT / "episodes_60s.json").read_text())}[n]
    d = ROOT / f"ep{n:02d}"; out = d / "out"; out.mkdir(exist_ok=True); tmp = out / "tmp"; tmp.mkdir(exist_ok=True)
    timing = json.loads((d / "audio" / "timing.json").read_text())
    beats = timing["beats"]; total = beats[-1]["end"] + 0.35 + END_HOLD
    # 1. picture: two stills per beat (wide, then close), slow sub-pixel camera moves, soft crossfades
    video = tmp / "video.mp4"
    render_stills(ep, beats, total, d / "images", video)
    # 2. captions
    ass = tmp / "captions.ass"; captions(ep, timing, total, ass)
    # 3. music bed ducked under the voice
    music = d / "audio" / "music.wav"
    mood = MOODS.get(n, "calm")
    sh(["python3", str(ROOT / "tools" / "music.py"), f"{total + 0.5:.2f}", str(music), "--seed", str(n), "--mood", mood, "--solo"])
    final = out / f"Ramayan_Ep{n:02d}.mp4"
    fc = ("[1:a]aresample=44100,highpass=f=60,pan=stereo|c0=c0|c1=c0,loudnorm=I=-16:TP=-1.5:LRA=11,apad,asplit=2[v1][v2];"
          "[2:a]volume=0.09[m];[m][v1]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=400[md];"
          "[v2][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1:LRA=11,atrim=0:" + f"{total:.3f}" + "[a];"
          f"[0:v]subtitles='{ass}':fontsdir='{ROOT / 'fonts'}'[vv]")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(d / "audio" / "narration.wav"), "-i", str(music),
        "-filter_complex", fc, "-map", "[vv]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", str(final)])
    print(f"{final}  ({total:.1f}s)")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        main(int(a))
