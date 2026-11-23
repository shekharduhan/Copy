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
import time

KEY = os.environ.get("FAL_KEY", "proxy-injected")
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


def submit(model, inp):
    r = _curl(["-X", "POST", f"{Q}/{model}", "--data-binary", "@-"], json.dumps(inp))
    if "request_id" not in r:
        raise RuntimeError(f"{model}: {r}")
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
