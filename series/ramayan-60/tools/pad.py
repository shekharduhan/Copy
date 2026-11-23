"""Insert extra beats into episodes: pad.py <file with '## <ep>' blocks of '[visual] text' lines>.
Each block's beats go in just before that episode's last beat (or after beat N with '## <ep> after <N>')."""
import pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
adds = {}
for blk in re.split(r"^## ", pathlib.Path(sys.argv[1]).read_text(), flags=re.M)[1:]:
    head, *lines = blk.strip().split("\n")
    m = re.match(r"(\d+)(?:\s+after\s+(\d+))?", head.strip()); ep, after = int(m.group(1)), m.group(2)
    adds[ep] = (int(after) if after else None, [l.strip() for l in lines if l.strip().startswith("[")])
for f in sorted((ROOT / "scripts").glob("*.txt")):
    s = f.read_text(); changed = False
    for ep, (after, lines) in adds.items():
        m = re.search(rf"^## {ep} \|.*?(?=^## |\Z)", s, flags=re.M | re.S)
        if not m: continue
        block = m.group(0).rstrip("\n").split("\n")
        beat_idx = [i for i, l in enumerate(block) if l.startswith("[")]
        pos = beat_idx[after - 1] + 1 if after else beat_idx[-1]
        block[pos:pos] = lines
        s = s[:m.start()] + "\n".join(block) + "\n\n" + s[m.end():].lstrip("\n"); changed = True
    if changed: f.write_text(s)
