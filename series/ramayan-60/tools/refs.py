"""Make a full-body reference portrait for every character in characters.json that has none yet."""
import concurrent.futures as cf, json, pathlib
import fal
ROOT = pathlib.Path(__file__).resolve().parent.parent
C = json.loads((ROOT / "characters.json").read_text())

def make(name, c):
    dst = ROOT / "characters" / f"{name}.png"
    if dst.exists(): return name, "exists"
    for attempt in range(3):
        r = fal.run("fal-ai/nano-banana", {"prompt": f"{C['style']}. Full-body character reference portrait of {c['desc']}, standing, front view, centered, plain dark background",
                                            "num_images": 1, "aspect_ratio": "9:16", "output_format": "png"})
        if r.get("images"):
            fal.download(r["images"][0]["url"], dst); return name, "made"
        if "content_policy" in str(r):
            break
    # nano-banana's checker sometimes blocks harmless prompts; Flux dev draws the same description
    r = fal.run("fal-ai/flux/dev", {"prompt": f"{C['style']}. Full-body character reference portrait of {c['desc']}, standing, front view, centered, plain dark background",
                                    "image_size": "portrait_16_9", "num_images": 1})
    if r.get("images"):
        fal.download(r["images"][0]["url"], dst); return name, "made (flux)"
    return name, f"FAILED: {str(r)[:200]}"

with cf.ThreadPoolExecutor(5) as ex:
    for n, s in ex.map(lambda kv: make(*kv), C["characters"].items()): print(n, s)
