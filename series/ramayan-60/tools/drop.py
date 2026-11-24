"""Remove beats from episodes: drop.py '2:3,7,8' '4:7,8' ...  (beat numbers as listed by build_scripts.py)."""
import pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
drops = {int(a.split(":")[0]): {int(x) for x in a.split(":")[1].split(",")} for a in sys.argv[1:]}
for f in sorted((ROOT / "scripts").glob("*.txt")):
    s = f.read_text()
    for ep, idx in drops.items():
        m = re.search(rf"^## {ep} \|.*?(?=^## |\Z)", s, flags=re.M | re.S)
        if not m: continue
        lines = m.group(0).rstrip("\n").split("\n"); k = 0; out = []
        for l in lines:
            if l.startswith("["):
                k += 1
                if k in idx: continue
            out.append(l)
        s = s[:m.start()] + "\n".join(out) + "\n\n" + s[m.end():].lstrip("\n")
    f.write_text(s)
