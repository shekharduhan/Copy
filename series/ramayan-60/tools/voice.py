"""Narrate one episode in the cloned voice: one fal MiniMax speech-02-hd call per beat, joined with short pauses.

  python3 voice.py 1          -> ep01/audio/beat_XX.wav, ep01/audio/narration.wav, ep01/audio/timing.json
"""
import concurrent.futures as cf, hashlib, json, pathlib, sys
import numpy as np, soundfile as sf
import fal

ROOT = pathlib.Path(__file__).resolve().parent.parent
VOICE_ID = json.loads((ROOT / "voice_minimax.json").read_text())["custom_voice_id"]   # cloned from voice_ref_clean.wav
SPEED = 0.9
GAP, LEAD, TAIL = 0.5, 0.6, 1.2


def beat_audio(text, dst):
    if dst.exists():
        return dst
    r = fal.run("fal-ai/minimax/speech-02-hd", {"text": text, "output_format": "url",
                "voice_setting": {"voice_id": VOICE_ID, "speed": SPEED, "vol": 1, "pitch": 0, "emotion": "neutral"}})
    mp3 = dst.with_suffix(".mp3"); fal.download(r["audio"]["url"], mp3)
    import subprocess
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100", str(dst)], check=True); mp3.unlink()
    return dst


def trim(x, sr, thr=0.01):
    idx = np.where(np.abs(x) > thr * np.abs(x).max())[0]
    return x[max(0, idx[0] - int(0.03 * sr)): idx[-1] + int(0.08 * sr)] if len(idx) else x


def main(ep):
    eps = {e["ep"]: e for e in json.loads((ROOT / "episodes_60s.json").read_text())}
    e = eps[ep]; d = ROOT / f"ep{ep:02d}" / "audio"; d.mkdir(parents=True, exist_ok=True)
    paths = [d / f"beat_{i+1:02d}_{hashlib.sha1(('mm' + b['text']).encode()).hexdigest()[:8]}.wav" for i, b in enumerate(e["beats"])]   # re-voice only changed text
    with cf.ThreadPoolExecutor(4) as ex:
        list(ex.map(beat_audio, [b["text"] for b in e["beats"]], paths))
    parts, t, timing, sr0 = [], LEAD, [], None
    for i, p in enumerate(paths):
        x, sr = sf.read(p); x = x if x.ndim == 1 else x.mean(1); sr0 = sr0 or sr
        x = trim(x, sr)
        if not parts: parts.append(np.zeros(int(LEAD * sr)))
        parts.append(x); dur = len(x) / sr
        timing.append({"beat": i + 1, "start": round(t, 3), "end": round(t + dur, 3), "text": e["beats"][i]["text"]})
        t += dur + GAP; parts.append(np.zeros(int(GAP * sr)))
    parts.append(np.zeros(int(TAIL * sr0)))
    y = np.concatenate(parts).astype(np.float32); sf.write(d / "narration.wav", y, sr0)
    total = round(len(y) / sr0, 2)
    (d / "timing.json").write_text(json.dumps({"ep": ep, "duration": total, "beats": timing}, indent=1))
    print(f"ep{ep:02d}: {total}s narration, {len(timing)} beats")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        main(int(a))
