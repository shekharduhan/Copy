"""One 9:16 anime still per beat, drawn with the reference portraits of the characters named in the beat's visual.

  python3 images.py 1      -> ep01/images/beat_XX.png
"""
import concurrent.futures as cf, json, pathlib, re, sys
import fal
ROOT = pathlib.Path(__file__).resolve().parent.parent
C = json.loads((ROOT / "characters.json").read_text())
REF_CACHE = {}


def cast(visual):
    found = []
    for name, c in C["characters"].items():
        if any(re.search(r"\b" + re.escape(m) + r"\b", visual, re.I) for m in c["match"]) and (ROOT / "characters" / f"{name}.png").exists():
            found.append(name)
    return found[:4]


def prompt_for(ep, beat, names):
    who = "; ".join(C["characters"][n]["desc"] for n in names)
    p = (f"{C['style']}. Vertical 9:16 cinematic frame from the Ramayana, episode '{ep['title']}'. Scene: {beat['visual']}. "
         )   # the narration is left out on purpose: models paint it onto the image as text
    if names:
        p += f"Characters (keep their faces, clothes and colors exactly as in the reference images): {who}. "
    return p + "Ancient India, epic and emotional, characters fully clothed. Absolutely no text, captions, letters or subtitles anywhere in the image."


def still(ep, i, beat, dst):
    if dst.exists():
        return dst.name, "exists"
    names = cast(beat["visual"])
    p = prompt_for(ep, beat, names)
    tries = []
    if names:
        refs = [REF_CACHE.setdefault(n, fal.data_uri(ROOT / "characters" / f"{n}.png")) for n in names]
        tries.append(("fal-ai/nano-banana/edit", {"prompt": p, "image_urls": refs, "num_images": 1, "aspect_ratio": "9:16", "output_format": "png"}))
    tries.append(("fal-ai/nano-banana", {"prompt": p, "num_images": 1, "aspect_ratio": "9:16", "output_format": "png"}))
    tries.append(("fal-ai/flux/dev", {"prompt": p, "image_size": "portrait_16_9", "num_images": 1}))
    for model, inp in tries:
        try:
            r = fal.run(model, inp)
        except Exception as e:
            r = {"error": str(e)}
        if r.get("images"):
            fal.download(r["images"][0]["url"], dst)
            return dst.name, f"{model} {names}"
    return dst.name, f"FAILED {str(r)[:160]}"


def main(n):
    ep = {e["ep"]: e for e in json.loads((ROOT / "episodes_60s.json").read_text())}[n]
    d = ROOT / f"ep{n:02d}" / "images"; d.mkdir(parents=True, exist_ok=True)
    jobs = [(ep, i, b, d / f"beat_{i+1:02d}.png") for i, b in enumerate(ep["beats"])]
    with cf.ThreadPoolExecutor(5) as ex:
        for name, how in ex.map(lambda j: still(*j), jobs):
            print(name, how)


if __name__ == "__main__":
    for a in sys.argv[1:]:
        main(int(a))
