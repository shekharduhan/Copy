"""Two 9:16 anime stills per beat (a wide shot and a closer shot), drawn with the reference portraits of the characters named in the beat's visual.

  python3 images.py 1      -> ep01/images/beat_XX.png
"""
import concurrent.futures as cf, hashlib, json, pathlib, re, sys
import fal
ROOT = pathlib.Path(__file__).resolve().parent.parent
C = json.loads((ROOT / "characters.json").read_text())
REF_CACHE = {}


def in_eps(c, n):
    rng = [c.get("eps", [1, 999])] + ([c["also_eps"]] if "also_eps" in c else [])
    return any(lo <= n <= hi for lo, hi in rng)


CHILD = re.compile(r"\b(baby|babies|boy|boys|child|children|young Rama|girl|infant|cradle)\b", re.I)


def cast(visual, n=1):
    if CHILD.search(visual):           # adult reference portraits would turn children into adults
        return []
    found = []
    for name, c in C["characters"].items():
        if in_eps(c, n) and any(re.search(r"\b" + re.escape(m) + r"\b", visual, re.I) for m in c["match"]) and (ROOT / "characters" / f"{name}.png").exists():
            found.append(name)
    return found[:4]


SHOTS = {"a": "Cinematic medium-wide shot with the main figures clearly visible."}   # the close-up is cropped from this image
MAX_REF_SHOTS = 4      # consistent-character (paid) images per episode; the rest use Flux Schnell


def shot_path(d, beat, shot):
    """Images are named by their scene description, so editing a script never mismatches images and beats."""
    return d / f"{hashlib.sha1(beat['visual'].encode()).hexdigest()[:10]}_{shot}.png"


def prompt_for(ep, beat, names, shot="a"):
    who = "; ".join(C["characters"][n]["desc"] for n in names)
    framing = SHOTS[shot] if (names or shot == "a") else "Closer detail shot of the same place and its ordinary people; no princes, queens or heroes."
    p = (f"{C['style']}. Vertical 9:16 cinematic frame from the Ramayana. Scene: {beat['visual']}. {framing} "
         )   # the narration is left out on purpose: models paint it onto the image as text
    if names:
        p += f"Characters (keep their faces, clothes and colors exactly as in the reference images): {who}. "
    if CHILD.search(beat["visual"]):
        p += "The children are small, clearly young kids. "
    return p + "Ancient India, epic and emotional, characters fully clothed. No signboards, banners or writing; absolutely no text, captions, letters or subtitles anywhere in the image."


def still(ep, beat, shot, dst, use_refs=True):
    if dst.exists():
        return dst.name, "exists"
    names = cast(beat["visual"], ep["ep"])
    p = prompt_for(ep, beat, names, shot)
    tries = []
    if names and not use_refs:          # over the per-episode cap: describe the characters in words only
        tries.append(("fal-ai/flux/schnell", {"prompt": p, "image_size": {"width": 768, "height": 1344}, "num_images": 1, "num_inference_steps": 4}))
    elif names:
        refs = [REF_CACHE.setdefault(n, fal.data_uri(ROOT / "characters" / f"{n}.png")) for n in names]
        tries.append(("fal-ai/nano-banana/edit", {"prompt": p, "image_urls": refs, "num_images": 1, "aspect_ratio": "9:16", "output_format": "png"}))
    if names and use_refs:
        tries.append(("fal-ai/nano-banana", {"prompt": p, "num_images": 1, "aspect_ratio": "9:16", "output_format": "png"}))
    tries.append(("fal-ai/flux/schnell", {"prompt": p, "image_size": {"width": 768, "height": 1344}, "num_images": 1, "num_inference_steps": 4}))
    for model, inp in tries:
        try:
            r = fal.run(model, inp)
        except fal.BudgetExceeded:
            raise
        except Exception as e:
            r = {"error": str(e)}
        if r.get("images"):
            fal.download(r["images"][0]["url"], dst)
            return dst.name, f"{model} {names}"
    return dst.name, f"FAILED {str(r)[:160]}"


def upscale(src):
    """Free local 2x upscale (Lanczos + light unsharp mask) so slow zooms on 1080x1920 stay crisp."""
    from PIL import Image, ImageFilter
    dst = src.with_name(src.stem + "_up.png")
    if dst.exists() or not src.exists():
        return dst
    im = Image.open(src).convert("RGB"); im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2)).save(dst)
    return dst


def main(n):
    ep = {e["ep"]: e for e in json.loads((ROOT / "episodes_60s.json").read_text())}[n]
    d = ROOT / f"ep{n:02d}" / "images"; d.mkdir(parents=True, exist_ok=True)
    jobs, used = [], 0
    for b in ep["beats"]:
        ref = bool(cast(b["visual"], n)) and used < MAX_REF_SHOTS
        used += ref
        jobs.append((ep, b, "a", shot_path(d, b, "a"), ref))
    with cf.ThreadPoolExecutor(5) as ex:
        for name, how in ex.map(lambda j: still(*j), jobs):
            print(name, how)
        list(ex.map(upscale, [j[3] for j in jobs]))
    print(f"ep{n:02d}: {len(jobs)} stills, upscaled, estimated spend so far ${fal._spend():.2f}")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        main(int(a))
