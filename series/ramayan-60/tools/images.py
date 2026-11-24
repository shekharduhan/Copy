"""9:16 anime stills for an episode, on a small budget.

Scenes with people: at most MAX_REF_SHOTS paid images (nano-banana), drawn with the reference portraits of the
characters named in the visual; the episode's first people image is also passed as a reference to the later
ones, so one-off characters (Shabari, Guha...) stay the same within the episode. People scenes past the cap get
no image: compose.py reuses the nearest one, cropped differently. Pure scenery uses Flux Schnell (cheap).

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
MAX_REF_SHOTS = 3      # consistent-character (paid) images per episode; the rest use Flux Schnell


PEOPLE = re.compile(r"\b(sage|sages|king|kings|queen|queens|woman|women|man|men|demon|demons|demoness|demonesses|monkey|monkeys|"
                    r"bear|army|armies|warrior|warriors|brother|brothers|prince|princes|princess|hermit|devotee|vulture|bird|"
                    r"serpent|figure|figures|crowd|maid|boatman|giant|guard|guards|priest|people|citizens|villager|messenger|"
                    r"messengers|couple|couples|bride|brides|son|sons|daughter|daughters|wife|husband|mother|father|being|"
                    r"he|she|him|her|his|they|them|baby|boy|boys|girl|child|children)\b", re.I)


def has_people(visual):
    return bool(PEOPLE.search(visual) or re.search(r"\b[A-Z][a-z]+", visual))   # any capitalised name


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


def still(ep, beat, shot, dst, paid=True, anchor=None):
    """paid: a people scene inside the cap (nano-banana). Otherwise scenery (Flux Schnell)."""
    if dst.exists():
        return dst.name, "exists"
    names = cast(beat["visual"], ep["ep"]) if paid else []
    p = prompt_for(ep, beat, names, shot)
    refs = [REF_CACHE.setdefault(n, fal.data_uri(ROOT / "characters" / f"{n}.png")) for n in names]
    if anchor is not None and anchor.exists() and not CHILD.search(beat["visual"]):
        refs.append(fal.data_uri(anchor))
        p += "Keep any people who also appear in the last reference image looking exactly the same. "
    tries = []
    if paid and refs:
        tries.append(("fal-ai/nano-banana/edit", {"prompt": p, "image_urls": refs[:4], "num_images": 1, "aspect_ratio": "9:16", "output_format": "png"}))
    if paid:
        tries.append(("fal-ai/nano-banana", {"prompt": p, "num_images": 1, "aspect_ratio": "9:16", "output_format": "png"}))
    else:
        tries.append(("fal-ai/flux/schnell", {"prompt": p, "image_size": {"width": 768, "height": 1344}, "num_images": 1, "num_inference_steps": 4}))
    r = {}
    for model, inp in tries:
        try:
            r = fal.run(model, inp)
        except fal.BudgetExceeded:
            raise
        except Exception as e:
            r = {"error": str(e)}
        if r.get("images"):
            fal.download(r["images"][0]["url"], dst)
            return dst.name, f"{model} {names}{' +anchor' if anchor else ''}"
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
    people = [b for b in ep["beats"] if has_people(b["visual"])]
    # spread the paid images across the episode's people scenes (first, middle, last ...)
    done = [b for b in people if shot_path(d, b, "a").exists()]          # already paid for: they count toward the cap
    rest = [b for b in people if b not in done]
    k = max(0, min(MAX_REF_SHOTS - len(done), len(rest)))
    pick = sorted({round(i * (len(rest) - 1) / max(1, k - 1)) for i in range(k)}) if k else []
    paid = done[:1] + [rest[i] for i in pick] + done[1:]
    scenery = [b for b in ep["beats"] if not has_people(b["visual"])]
    anchor = None
    if paid:                                   # the first people image is generated alone, then anchors the rest
        first = paid[0]; anchor = shot_path(d, first, "a")
        print(*still(ep, first, "a", anchor, True))
    jobs = [(ep, b, "a", shot_path(d, b, "a"), True, anchor) for b in paid[1:]] + \
           [(ep, b, "a", shot_path(d, b, "a"), False, None) for b in scenery]
    with cf.ThreadPoolExecutor(5) as ex:
        for name, how in ex.map(lambda j: still(*j), jobs):
            print(name, how)
        made = [shot_path(d, b, "a") for b in ep["beats"]]
        list(ex.map(upscale, made))
    skipped = len(people) - len(paid)
    print(f"ep{n:02d}: {len(paid)} paid + {len(scenery)} scenery stills, {skipped} scenes reuse an image; estimated spend so far ${fal._spend():.2f}")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        main(int(a))
