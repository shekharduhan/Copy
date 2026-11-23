"""Two 9:16 anime stills per beat (a wide shot and a closer shot), drawn with the reference portraits of the characters named in the beat's visual.

  python3 images.py 1      -> ep01/images/beat_XX.png
"""
import concurrent.futures as cf, hashlib, json, pathlib, re, sys
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


SHOTS = {"a": "Wide establishing shot.", "b": "Closer shot from a different camera angle, focusing on faces, hands and expressions."}


def shot_path(d, beat, shot):
    """Images are named by their scene description, so editing a script never mismatches images and beats."""
    return d / f"{hashlib.sha1(beat['visual'].encode()).hexdigest()[:10]}_{shot}.png"


def prompt_for(ep, beat, names, shot="a"):
    who = "; ".join(C["characters"][n]["desc"] for n in names)
    framing = SHOTS[shot] if (names or shot == "a") else "Closer detail shot of the same place and its ordinary people; no princes, queens or heroes."
    p = (f"{C['style']}. Vertical 9:16 cinematic frame from the Ramayana, episode '{ep['title']}'. Scene: {beat['visual']}. {framing} "
         )   # the narration is left out on purpose: models paint it onto the image as text
    if names:
        p += f"Characters (keep their faces, clothes and colors exactly as in the reference images): {who}. "
    return p + "Ancient India, epic and emotional, characters fully clothed. Absolutely no text, captions, letters or subtitles anywhere in the image."


def still(ep, beat, shot, dst):
    if dst.exists():
        return dst.name, "exists"
    names = cast(beat["visual"])
    p = prompt_for(ep, beat, names, shot)
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


def upscale(src):
    """2x anime upscale (Real-ESRGAN) so slow zooms on a 1080x1920 frame stay sharp."""
    dst = src.with_name(src.stem + "_up.png")
    if dst.exists() or not src.exists():
        return dst
    r = fal.run("fal-ai/esrgan", {"image_url": fal.data_uri(src), "scale": 2, "model": "RealESRGAN_x4plus_anime_6B", "output_format": "png"})
    return fal.download(r["image"]["url"], dst)


def main(n):
    ep = {e["ep"]: e for e in json.loads((ROOT / "episodes_60s.json").read_text())}[n]
    d = ROOT / f"ep{n:02d}" / "images"; d.mkdir(parents=True, exist_ok=True)
    jobs = [(ep, b, sh, shot_path(d, b, sh)) for b in ep["beats"] for sh in SHOTS]
    with cf.ThreadPoolExecutor(5) as ex:
        for name, how in ex.map(lambda j: still(*j), jobs):
            print(name, how)
        list(ex.map(upscale, [j[3] for j in jobs]))
    print(f"ep{n:02d}: {len(jobs)} stills, upscaled")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        main(int(a))
