"""Match Thai-client Digimon ids to dex entries.

Signals, strongest first:
  1. web/thai_client_map.json        manual  {client_id: "English dmowiki title"}
  2. Thai name (client digimonname_str) vs dex Thai names, with the dex stage suffix "(เมก้า)" etc. removed
  3. client id stage digit (3 rookie, 4 champion, 5 ultimate, 6 mega, 7 burst/jogress/special) vs dex form
  4. client model folder "<name>_re"  -> the "(ชิน)"/Awaken form
  5. client model file name (English) vs dex title
"""
import json
import os
import re
from collections import defaultdict
from pathlib import Path

try:
    from dex_builder import awaken_th
except ImportError:
    from web.dex_builder import awaken_th

CRACK = Path(__file__).resolve().parent.parent.parent / "CrackDMO"
if not (CRACK / "out_decrypted").exists():
    CRACK = Path(__file__).resolve().parent.parent / "CrackDMO"
if not (CRACK / "out_decrypted").exists():
    CRACK = Path(r"C:\Users\T4R\Desktop\AllWorks\CrackDMO")
HERE = Path(__file__).resolve().parent

STAGE_SUFFIX = r"\s*\((?:เมก้า|แชมเปี้ยน|อัลติเมท|รุคกี้|ร่างเด็ก|ทารก|เบบี้|อินเทรนนิ่ง|ร่างสุดยอด|ร่างสมบูรณ์|ร่างเจริญวัย)\)"


def clean_client_name(s):
    s = (s or "").replace("ดิจิมอนใหม่", "").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"^\[(.+?)\]\s*(.+)$", r"\2 (\1)", s)
    s = re.sub(r"^(.+?)\s*\[(.+?)\]$", r"\1 (\2)", s)
    return awaken_th(s)


def key(s):
    s = clean_client_name(s)
    s = re.sub(STAGE_SUFFIX, "", s).lower()
    s = s.replace("ฺ", "").replace("์", "").replace("©", "c")
    s = re.sub(r"\(?\s*x\s*-?\s*แอนติบอดี้\s*\)?", "x", s)
    s = s.replace("เบิร์สทโหมด", "เบิร์สโหมด").replace("เบิร์ส โหมด", "เบิร์สโหมด")
    return re.sub(r"[\s\-–:()\[\]·.,'\"!]+", "", s)


def tone_free(k):
    return re.sub(r"[่้๊๋็]", "", k)


def ekey(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def stage_ok(client_id, form):
    cs = str(client_id)
    f = (form or "").lower()
    if cs.startswith("75"):          # X-Antibody / armor forms of every stage
        return True
    if cs.startswith("67"):          # Awaken ("ชิน") Megas
        return "mega" in f or "burst" in f
    d = int(cs[0])
    if d == 3:
        return "rookie" in f or "armor" in f
    if d == 4:
        return "champion" in f or "armor" in f or "hybrid" in f
    if d == 5:
        return "ultimate" in f or "perfect" in f
    if d == 6:
        return "mega" in f or "hybrid" in f
    if d == 7:
        return not any(x in f for x in ("rookie", "champion", "in-training", "baby"))
    return True


def model_names():
    out = defaultdict(set)
    root = CRACK / "out_pack01" / "data" / "digimon"
    if not root.exists():
        return out
    for r, _ds, fs in os.walk(root):
        folder = os.path.basename(r)
        for f in fs:
            m = re.match(r"^0*(\d{4,6})_(.+?)\.\w+$", f)
            if m:
                cid = int(m.group(1))
                out[cid].add(folder)
                out[cid].add(re.sub(r"(?i)(_?evo|_?anim|[LS])$", "", m.group(2)))
    return out


class ClientMatcher:
    def __init__(self, dex):
        self.dex = dex
        mp = HERE / "thai_client_map.json"
        self.manual = {k: v for k, v in json.loads(mp.read_text(encoding="utf-8")).items() if not k.startswith("_")} \
            if mp.exists() else {}
        names = dex.vocab.get("names", {}) if hasattr(dex, "vocab") else {}
        self.by_th = defaultdict(list)
        self.by_th_loose = defaultdict(list)
        for d in dex.digimon:
            for t in {d.get("thai_name"), names.get(d["title"])}:
                if t:
                    self.by_th[key(t)].append(d)
                    self.by_th_loose[tone_free(key(t))].append(d)
        self.models = model_names()

    def _by_title(self, title):
        return self.dex.by_key.get(ekey(title))

    def find(self, client_id, client_name):
        cid = int(client_id)
        if str(cid) in self.manual:
            return self._by_title(self.manual[str(cid)])
        models = self.models.get(cid, set())
        is_re = any(re.search(r"(?i)_re$", m) for m in models) or str(cid).startswith("67")
        k = key(client_name)
        explicit = re.search(r"ชิน|เอ็กซ์ตรีม|x$|โจเกรส|เบิร์สโหมด", k)
        cands = [d for d in self.by_th.get(k, []) or self.by_th_loose.get(tone_free(k), [])
                 if stage_ok(cid, d.get("form"))]
        if is_re and not explicit:
            ak = key(clean_client_name(client_name) + " (ชิน)")
            aw = self.by_th.get(ak) or self.by_th_loose.get(tone_free(ak))
            if aw:
                return aw[0]
        if len({id(d) for d in cands}) == 1:
            return cands[0]
        # English model names
        for m in sorted(models, key=len):
            base = ekey(re.sub(r"(?i)_re$", "", m))
            tries = [base + "awaken"] if is_re else []
            if base.endswith("x"):
                tries += [base[:-1] + "xantibodysystem", base[:-1] + "x"]
            tries += [base, base + ("mega" if str(cid)[0] in "67" else "champion")]
            for t in tries:
                d = self.dex.by_key.get(t)
                if d and stage_ok(cid, d.get("form")):
                    return d
        if cands:  # several dex entries share the Thai name: take the one the stage digit agrees with best
            return cands[0]
        return None
