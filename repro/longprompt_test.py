#!/usr/bin/env python3
"""Step 7b long-context drift / hallucination / vision test against an OpenAI-compatible server.

Per size: one long document with
  - 10 recall facts (gen.FACTS) spread 5%..95%
  - 3 facts stated early and CORRECTED late (must answer the corrected value)
  - 3 near-duplicate distractors (a similar entity with a different value)
  - 5 questions whose answer is NOT in the document (must say "not in document")
  - an image before the document, asked about at the end (vision across the whole context)
Then a cached follow-up turn (short question) to measure generation speed at depth.
Usage: longprompt_test.py <label> <base_url> <model> <size> [size ...]   -> results/ctx-<label>.jsonl
"""
import base64, io, json, random, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gen

UPDATES = [  # (early statement, late correction, question, accepted, rejected)
    ("The on-call rotation for team Granite is led by Marcus Bell.",
     "CORRECTION: the on-call rotation for team Granite is now led by Hana Ito, replacing Marcus Bell.",
     "Who currently leads the on-call rotation for team Granite?", ["ito"], ["bell"]),
    ("The Osprey cluster runs kernel version 6.1.44.",
     "CORRECTION: the Osprey cluster was upgraded and now runs kernel version 6.8.12.",
     "Which kernel version does the Osprey cluster run now?", ["6.8.12"], ["6.1.44"]),
    ("Cold storage pool Delta-North has a capacity of 640 TB.",
     "CORRECTION: cold storage pool Delta-North was expanded to a capacity of 910 TB.",
     "What is the current capacity of cold storage pool Delta-North?", ["910"], ["640"]),
]
DISTRACT = [  # near-duplicates of gen.FACTS entities, placed near the real fact
    "The maintenance window for cluster Orion-6 is Monday at 01:10.",
    "The Graywater-B VPN uses UDP port 49152.",
    "Build runner Saffron-2 has exactly 64 GB of RAM.",
]
ABSENT = [  # plausible but never stated
    "What is the maintenance window for cluster Orion-9?",
    "Who is the emergency contact for the Kestrel datacenter?",
    "Which TCP port does the Graywater VPN admin console use?",
    "How many days does the archive bucket kestrel-cold-22 retain objects?",
    "What is the rollback code word for the Solstice release?",
]
ABSENT_OK = ["not in", "not mentioned", "not stated", "not found", "no information", "does not", "doesn't",
             "not specified", "not provided", "unknown", "n/a", "not present", "no mention", "not available"]

def image_b64():
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (640, 360), "white"); d = ImageDraw.Draw(im)
    try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
    except Exception: f = ImageFont.load_default()
    d.text((40, 40), "7342", fill="black", font=f)
    d.ellipse((430, 200, 590, 340), fill="red")
    d.rectangle((40, 220, 200, 330), fill="blue")
    b = io.BytesIO(); im.save(b, "PNG"); return base64.b64encode(b.getvalue()).decode()

def build(size):
    doc, qa = gen.make_doc(size, seed=11)
    paras = doc.split("\n\n")
    n = len(paras); rng = random.Random(size)
    def ins(frac, text):
        i = min(n - 1, max(0, int(n * frac))); paras[i] += " " + text
    for k, (early, late, *_ ) in enumerate(UPDATES):
        ins(0.08 + 0.1 * k, early); ins(0.62 + 0.1 * k, late)
    for k, t in enumerate(DISTRACT):
        ins((0.05, 0.5, 0.35)[k] + 0.01, t)   # right after the matching real fact's position
    return "\n\n".join(paras), qa

def post(base, model, msgs, max_tokens=8192):
    body = {"model": model, "messages": msgs, "max_tokens": max_tokens, "stream": True,
            "stream_options": {"include_usage": True}, "temperature": 0.6, "top_p": 0.95}
    req = urllib.request.Request(base + "/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
    t0 = time.time(); first = None; out = []; usage = {}; timings = {}; finish = None
    with urllib.request.urlopen(req, timeout=7200) as r:
        for raw in r:
            line = raw.decode().strip()
            if not line.startswith("data:") or line == "data: [DONE]": continue
            j = json.loads(line[5:])
            usage = j.get("usage") or usage; timings = j.get("timings") or timings
            for ch in j.get("choices", []):
                dl = ch.get("delta", {}); finish = ch.get("finish_reason") or finish
                if (dl.get("content") or dl.get("reasoning_content")) and first is None: first = time.time()
                out.append(dl.get("content") or "")
    end = time.time()
    return "".join(out), {"prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                          "ttft_s": round((first or end) - t0, 1), "total_s": round(end - t0, 1),
                          "pp_tok_s": round(timings.get("prompt_per_second", 0), 1), "gen_tok_s": round(timings.get("predicted_per_second", 0), 1),
                          "finish": finish}

def vram():
    import subprocess
    o = subprocess.run(["rocm-smi", "--showmeminfo", "vram"], capture_output=True, text=True).stdout
    for l in o.splitlines():
        if "Used" in l: return round(int(l.split(":")[-1]) / 2**30, 2)

def run(label, base, model, size):
    doc, qa = build(size)
    qs = [q for q, _ in qa] + [u[2] for u in UPDATES] + ABSENT + [
        "In the image shown before the document: what 4-digit number is written, and what color is the circle?"]
    numbered = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(qs))
    user = [{"type": "image_url", "image_url": {"url": "data:image/png;base64," + image_b64()}},
            {"type": "text", "text": f"<document>\n{doc}\n</document>\n\nAnswer every question below using ONLY the "
             f"document (and the image for the last one). If the document does not contain the answer, reply exactly "
             f"\"not in document\" for that question. Where a value was later corrected, give the current value. "
             f"Reply with only a JSON object mapping the question number (\"1\"..\"{len(qs)}\") to a short answer.\n\n{numbered}"}]
    msgs = [{"role": "system", "content": "You answer questions about documents precisely and never guess."},
            {"role": "user", "content": user}]
    rec = {"label": label, "size": size}
    try:
        txt, m = post(base, model, msgs); rec.update(m)
    except Exception as e:
        rec["error"] = repr(e)[:300]; rec["vram_gb"] = vram(); return rec
    rec["vram_gb"] = vram()
    try:
        a = json.loads(txt[txt.index("{"): txt.rindex("}") + 1]); rec["format_ok"] = True
    except Exception:
        a = {}; rec["format_ok"] = False
    g = lambda i: str(a.get(str(i), "")).lower()
    rec["recall"] = sum(any(x in g(i + 1) for x in acc) for i, (_, acc) in enumerate(qa))
    o = len(qa)
    rec["updates"] = sum(any(x in g(o + k + 1) for x in u[3]) and not any(x in g(o + k + 1) for x in u[4])
                         for k, u in enumerate(UPDATES))
    rec["distractor_confusions"] = sum(bad in g(i) for i, bad in ((1, "01:10"), (6, "49152"), (4, "64")))
    o2 = o + len(UPDATES)
    halluc = [k for k in range(len(ABSENT)) if not any(x in g(o2 + k + 1) for x in ABSENT_OK)]
    rec["hallucinated"] = len(halluc); rec["hallucinated_answers"] = [g(o2 + k + 1)[:60] for k in halluc]
    vi = g(len(qs)); rec["vision"] = int("7342" in vi) + int("red" in vi)
    rec["answers_tail"] = txt[-400:]
    # cached follow-up: generation speed at depth
    try:
        msgs2 = msgs + [{"role": "assistant", "content": txt},
                        {"role": "user", "content": "In 3 sentences, what kinds of maintenance work does this log describe most often?"}]
        _, m2 = post(base, model, msgs2, max_tokens=2048)
        rec["followup"] = {k: m2[k] for k in ("ttft_s", "gen_tok_s", "total_s", "prompt_tokens")}
    except Exception as e:
        rec["followup"] = {"error": repr(e)[:200]}
    return rec

if __name__ == "__main__":
    label, base, model = sys.argv[1:4]
    out = Path(__file__).parent / "results" / f"ctx-{label}.jsonl"; out.parent.mkdir(exist_ok=True)
    for s in sys.argv[4:]:
        r = run(label, base, model, int(s))
        with open(out, "a") as f: f.write(json.dumps(r) + "\n")
        print("CTX " + json.dumps({k: r.get(k) for k in ("label", "size", "prompt_tokens", "ttft_s", "pp_tok_s", "gen_tok_s",
              "recall", "updates", "distractor_confusions", "hallucinated", "vision", "format_ok", "finish", "vram_gb",
              "followup", "error")}), flush=True)
