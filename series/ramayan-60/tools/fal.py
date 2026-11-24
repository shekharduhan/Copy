"""Minimal fal.ai queue client (submit, poll, fetch result, download outputs).

The API key is never read here: the session's network proxy adds the Authorization header for
queue.fal.run, so requests send a placeholder. Outside this environment set FAL_KEY instead.

  python3 fal.py <model> '<json input>' [--out dir]
"""
import base64
import json
import mimetypes
import os
import pathlib
import subprocess
import sys
import threading
import time

KEY = os.environ.get("FAL_KEY", "proxy-injected")
LEDGER = pathlib.Path(__file__).resolve().parent.parent / "spend.json"
BUDGET = float(os.environ.get("FAL_BUDGET", "15.5"))      # dollars; the user has $18 left and asked to stay under $16
PRICE = {                                                    # estimates from fal.ai's listed prices
    "fal-ai/nano-banana": 0.039, "fal-ai/nano-banana/edit": 0.039,
    "fal-ai/flux/schnell": 0.004, "fal-ai/flux/dev": 0.025, "fal-ai/esrgan": 0.003,
}


def estimate(model, inp):
    if model.startswith("fal-ai/minimax/speech"):
        return 0.10 * len(inp.get("text", "")) / 1000
    return PRICE.get(model, 0.05)


_LOCK = threading.Lock()


def _spend(add=0.0):
    """Read (and optionally add to) the estimated spend; file-locked so parallel batches share one total."""
    import fcntl
    with _LOCK, open(LEDGER.with_suffix(".lock"), "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        led = json.loads(LEDGER.read_text()) if LEDGER.exists() else {"total": 0.0, "calls": 0}
        if add:
            led["total"] = round(led["total"] + add, 4); led["calls"] += 1; LEDGER.write_text(json.dumps(led, indent=1))
        return led["total"]
Q = "https://queue.fal.run"


def _curl(args, data=None):
    cmd = ["curl", "-sS", "--retry", "3", "-H", f"Authorization: Key {KEY}", "-H", "Content-Type: application/json"] + args
    r = subprocess.run(cmd, input=data, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip())
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(r.stdout[:500])


def data_uri(path):
    p = pathlib.Path(path)
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


class BudgetExceeded(RuntimeError):
    pass


def submit(model, inp):
    cost = estimate(model, inp)
    if _spend() + cost > BUDGET:
        raise BudgetExceeded(f"stopping: estimated spend ${_spend():.2f} + ${cost:.3f} would pass the ${BUDGET:.2f} budget")
    r = _curl(["-X", "POST", f"{Q}/{model}", "--data-binary", "@-"], json.dumps(inp))
    if "request_id" not in r:
        raise RuntimeError(f"{model}: {r}")
    _spend(cost)
    return r


def wait(sub, every=3, timeout=1800):
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = _curl([sub["status_url"]])
        if s.get("status") == "COMPLETED":
            return _curl([sub["response_url"]])
        if s.get("status") not in ("IN_QUEUE", "IN_PROGRESS"):
            raise RuntimeError(f"job ended: {s}")
        time.sleep(every)
    raise TimeoutError(sub["request_id"])


def run(model, inp):
    return wait(submit(model, inp))


def download(url, dst):
    dst = pathlib.Path(dst); dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-sSL", "--retry", "3", "--fail", "-o", str(dst), url], check=True)
    return dst


if __name__ == "__main__":
    model, inp = sys.argv[1], json.loads(sys.argv[2])
    print(json.dumps(run(model, inp), indent=1)[:3000])
