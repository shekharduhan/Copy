"""Parse scripts/*.txt into episodes_60s.json and report word counts and estimated length.

Format per episode:
  ## <n> | <title> | <on-screen closing line>
  src: <where the story comes from>
  [visual] narration...
"""
import json, pathlib, re, sys
HERE = pathlib.Path(__file__).parent
WPS = 2.75          # words per second incl. pauses (Kokoro onyx measured 3.0 speech-only); re-measured on the final voice
eps = []
for f in sorted((HERE / "scripts").glob("*.txt")):
    for block in re.split(r"^## ", f.read_text(), flags=re.M)[1:]:
        head, *lines = block.strip().split("\n")
        n, title, onscreen = [x.strip() for x in head.split("|")]
        src = ""; beats = []
        for ln in lines:
            ln = ln.strip()
            if ln.startswith("src:"): src = ln[4:].strip()
            elif ln.startswith("["):
                v, t = re.match(r"\[([^\]]+)\]\s*(.+)", ln).groups(); beats.append({"visual": v, "text": t})
        words = sum(len(b["text"].split()) for b in beats)
        eps.append({"ep": int(n), "title": title, "onscreen": onscreen, "source": src, "beats": beats,
                    "words": words, "est_seconds": round(words / WPS + 2, 1)})
eps.sort(key=lambda e: e["ep"])
(HERE / "episodes_60s.json").write_text(json.dumps(eps, ensure_ascii=False, indent=1) + "\n")
for e in eps:
    flag = "" if 54 <= e["est_seconds"] <= 64 else "  <-- adjust"
    print(f"{e['ep']:>2} {e['title'][:28]:28} {e['words']:>3} words  ~{e['est_seconds']}s  {len(e['beats'])} beats{flag}")
