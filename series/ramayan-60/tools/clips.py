"""Animate each still into a 5 s image-to-video clip (Kling 2.1 standard on fal).

  python3 clips.py 1 [beat ...]     -> ep01/clips/beat_XX.mp4
"""
import concurrent.futures as cf, json, pathlib, sys, tempfile
from PIL import Image
import fal
ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL = "fal-ai/kling-video/v2.1/standard/image-to-video"
NEG = "text, subtitles, letters, watermark, blur, distortion, deformed faces, extra limbs, morphing, low quality"


def motion(beat):
    return (f"{beat['visual']}. Gentle cinematic anime motion: slow camera push-in, characters breathe and move naturally, "
            "hair and cloth sway in the breeze, firelight and lamps flicker, dust and light particles drift. Keep faces and art style consistent.")


def clip(img, beat, dst):
    if dst.exists():
        return dst.name, "exists"
    with tempfile.NamedTemporaryFile(suffix=".jpg") as t:
        Image.open(img).convert("RGB").save(t.name, quality=92)
        r = fal.run(MODEL, {"prompt": motion(beat), "image_url": fal.data_uri(t.name), "duration": "5",
                            "negative_prompt": NEG, "cfg_scale": 0.5})
    url = (r.get("video") or {}).get("url")
    if not url:
        return dst.name, f"FAILED {str(r)[:200]}"
    fal.download(url, dst); return dst.name, "made"


def main(n, only=None):
    ep = {e["ep"]: e for e in json.loads((ROOT / "episodes_60s.json").read_text())}[n]
    d = ROOT / f"ep{n:02d}"; (d / "clips").mkdir(parents=True, exist_ok=True)
    jobs = [(d / "images" / f"beat_{i+1:02d}.png", b, d / "clips" / f"beat_{i+1:02d}.mp4")
            for i, b in enumerate(ep["beats"]) if not only or i + 1 in only]
    with cf.ThreadPoolExecutor(5) as ex:
        for name, how in ex.map(lambda j: clip(*j), jobs):
            print(name, how)


if __name__ == "__main__":
    main(int(sys.argv[1]), [int(x) for x in sys.argv[2:]] or None)
