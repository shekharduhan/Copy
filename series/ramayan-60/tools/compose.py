"""Assemble one finished 9:16 episode: AI clips cut to the narration, channel-style captions, title, end line, music.

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


def main(n):
    ep = {e["ep"]: e for e in json.loads((ROOT / "episodes_60s.json").read_text())}[n]
    d = ROOT / f"ep{n:02d}"; out = d / "out"; out.mkdir(exist_ok=True); tmp = out / "tmp"; tmp.mkdir(exist_ok=True)
    timing = json.loads((d / "audio" / "timing.json").read_text())
    beats = timing["beats"]; total = beats[-1]["end"] + 0.35 + END_HOLD
    # 1. one segment per beat, cut at the next beat's start (first beat from 0, last until the end)
    segs = []
    for i, b in enumerate(beats):
        t0 = 0 if i == 0 else b["start"] - 0.15
        t1 = total if i == len(beats) - 1 else beats[i + 1]["start"] - 0.15
        need = t1 - t0; clip = d / "clips" / f"beat_{i+1:02d}.mp4"
        src = dur(clip); f = min(need / src, 1.6) if need > src else 1.0
        hold = max(0.0, need - src * f)
        vf = (f"setpts={f:.4f}*PTS,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
              f"tpad=stop_mode=clone:stop_duration={hold + 0.2:.3f},trim=duration={need:.3f},setpts=PTS-STARTPTS,"
              f"eq=saturation=1.06:contrast=1.04,vignette=PI/5")
        seg = tmp / f"seg_{i+1:02d}.mp4"
        sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(clip), "-an", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", str(seg)])
        segs.append(seg)
    lst = tmp / "list.txt"; lst.write_text("".join(f"file '{s.name}'\n" for s in segs))
    video = tmp / "video.mp4"
    sh(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(video)])
    # 2. captions
    ass = tmp / "captions.ass"; captions(ep, timing, total, ass)
    # 3. music bed ducked under the voice
    music = d / "audio" / "music.wav"
    mood = MOODS.get(n, "calm")
    sh(["python3", str(ROOT / "tools" / "music.py"), f"{total + 0.5:.2f}", str(music), "--seed", str(n), "--mood", mood])
    final = out / f"Ramayan_Ep{n:02d}.mp4"
    fc = ("[1:a]aresample=44100,pan=stereo|c0=c0|c1=c0,loudnorm=I=-16:TP=-1.5:LRA=11,apad,asplit=2[v1][v2];"
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
