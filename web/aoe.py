"""Which skills of a Digimon hit an area (AoE), taken only from what dmowiki states explicitly:
- sentences on the Digimon page ("The third skill is an area of effect hitting every enemy around ...",
  "F4 is a linear AOE", "Very wide F3, F4 skills Area of Effect", ...)
- skill descriptions / skill-effect fields that say "Area of Effect" / "AoE"
- the "Area of Effect Skills" table page (effective area + range per skill name)
Result: {slot(int 1-based): {"shape": "self|target|line|", "size": "Small|Wide|Maximum|Medium|"}}"""
import re

ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6}
AOE_RE = re.compile(r"area of effect|\baoe\b", re.I)
SKIP = re.compile(r"Area of Effect Skills Armor|raid|Skill \d+ =|Memory Skills|Ruler of Space|Family [Bb]uff", re.I)
F_RUN = re.compile(r"F(\d)(?:\s*(?:,|and|&|/)\s*F(\d))?(?:\s*(?:,|and|&|/)\s*F(\d))?")
ORD_RUN = re.compile(r"\b(first|second|third|fourth|fifth|sixth)\b(?:\s*(?:,|and)\s*(first|second|third|fourth|fifth|sixth))?", re.I)


def _shape(s):
    s = s.lower()
    if re.search(r"straight line|linear|vertical", s):
        return "line"
    if "around the target" in s or "target enemy" in s:
        return "target"
    if re.search(r"around (the user|your|it|him|her)|around [A-Z]|every enemy around|surrounding|within \d+ meters", s, re.I):
        return "self"
    return ""


def _size(s):
    s = s.lower()
    if "maximum range" in s:
        return "Maximum"
    if "medium-range" in s or "medium range" in s:
        return "Medium"
    if re.search(r"\bwide\b", s):
        return "Wide"
    return ""


def _norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def load_table(rows):
    """rows of the 'Area of Effect Skills' table -> {skill name lower: (shape, size)}"""
    out = {}
    for r in rows:
        if len(r) < 5 or r[0] == "Evolution":
            continue
        area = r[3].lower()
        shape = "line" if "straight" in area else "target" if "target" in area else "self" if "user" in area else ""
        size = r[4] if r[4] in ("Small", "Wide", "Maximum") else ""
        out[(_norm(r[1]), r[2].strip().lower())] = (shape, size)
    return out


def parse_aoe(text, skills, skill_effects, table, title=""):
    found = {}

    def mark(slot, shape="", size=""):
        if not 1 <= slot <= max(len(skills), 1):
            return
        cur = found.setdefault(slot, {"shape": "", "size": ""})
        cur["shape"] = cur["shape"] or shape
        cur["size"] = cur["size"] or size

    flat = re.sub(r"\s*\n\s*", " ", text)
    for sent in re.split(r"(?<=[.!])\s+|Pros:|Cons:", flat):
        if not AOE_RE.search(sent):
            continue
        m = AOE_RE.search(sent)
        sent = sent[max(0, m.start() - 160):m.end() + 200]
        if SKIP.search(sent):
            continue
        m = AOE_RE.search(sent)
        before, after = sent[:m.start()], sent[m.start():]
        slots = []
        fr = list(F_RUN.finditer(before))
        orr = list(ORD_RUN.finditer(before))
        cands = []
        if fr:
            cands.append((fr[-1].end(), [int(g) for g in fr[-1].groups() if g]))
        if orr and "skill" in sent.lower():
            cands.append((orr[-1].end(), [ORD[g.lower()] for g in orr[-1].groups() if g]))
        cands = [cd for cd in cands if len(before) - cd[0] <= 70]
        if cands:
            slots = max(cands)[1]
        else:
            fa = F_RUN.search(after)
            if fa and fa.start() < 40:
                slots = [int(g) for g in fa.groups() if g]
        for s in slots:
            mark(s, _shape(sent), _size(sent))

    for i, sk in enumerate(skills, 1):
        if AOE_RE.search(sk.get("description", "")):
            mark(i, _shape(sk["description"]), _size(sk["description"]))
        t = table.get((_norm(title), sk.get("name", "").strip().lower()))
        if t:
            mark(i, *t)
            found[i]["shape"], found[i]["size"] = t[0] or found[i]["shape"], t[1] or found[i]["size"]
    for e in skill_effects:
        try:
            slot = int(str(e.get("slot", "")).lstrip("F"))
        except ValueError:
            continue
        if any(AOE_RE.search(f[1]) for f in e.get("fields", [])):
            mark(slot, _shape(" ".join(f[1] for f in e["fields"])))
    return found
