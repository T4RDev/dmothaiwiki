"""Tie every DigiEgg to its real evolution line in the Thai client (devolutionlist.bin).

The client keeps one base id per egg line: Wormmon 31142 = Stingmon > JewelBeemon > GrandisKuwagamon,
Wormmon 33075 = Stingmon > Paildramon > Imperialdramon ... So the line decides
  - the evolution strip shown for the egg (different per line),
  - whether the egg is a Jogress egg (its line reaches a Jogress Digimon) or a normal Lv.3/4/5 one,
  - the egg icon (from the client's own "<Digimon> ดิจิทามะ" items; Lv.4 = icon + 16, Lv.5 = icon + 32).
"""
import re
from collections import Counter, defaultdict

from thai_client_match import ClientMatcher

SYN = {"exvmon": "exveemon", "vdramon": "veedramon", "daemon": "demon", "millenniummon": "millenniumon",
       "raptordramon": "reptiledramon", "gardromon": "guardromon", "dukemon": "gallantmon",
       "mechanorimon": "mechanorimon", "musyamon": "musyamon", "coredramonblue": "blue", "coredramongreen": "green"}


def _norm(s):
    k = re.sub(r"[^a-z0-9]", "", (s or "").lower())
    return SYN.get(k, k)


def _clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("ดิจิมอนใหม่", "")).strip()


class ClientLines:
    def __init__(self, dex):
        import thai_client_evo as E
        from thai_client_apply import ClientEvo
        self.E = E
        self.names = E.digimon_names()
        self.matcher = ClientMatcher(dex)
        self._pic = ClientEvo.client_picture
        slots = defaultdict(dict)
        for ln in E.parse_lines(set(self.names)):
            slots[ln["parent"]].setdefault(ln["slot"], ln["type"])
        self.bases = {}      # base id -> [client ids along the line]
        for b, sl in slots.items():
            if 76000 <= b < 77000:      # "jumping" event copies of a line
                continue
            self.bases[b] = [sl[s] for s in sorted(sl) if sl[s] != b]
        self._dex = {}
        self.by_slug = defaultdict(list)
        plain = {}   # Thai base name -> dex entry, from the bases the matcher places
        for b in self.bases:
            d = self.find(b)
            if d:
                plain.setdefault(self._base_name(b), d)
        for b in sorted(self.bases):
            d = self.find(b)
            if not d:   # "แบล็คอากูมอน[มิลเลนเนียม]", a second "วอร์มมอน": same Digimon, another line
                d = plain.get(self._base_name(b)) or self.matcher.find(31999, self._base_name(b))
                self._dex[b] = d
            if d:
                self.by_slug[d["slug"]].append(b)
        self._items = None

    def _base_name(self, cid):
        return re.sub(r"\s*[\[(].*$", "", _clean(self.names.get(cid, ""))).strip()

    def find(self, cid):
        if cid not in self._dex:
            self._dex[cid] = self.matcher.find(cid, self.names.get(cid, ""))
        return self._dex[cid]

    def member(self, cid):
        d = self.find(cid)
        nm = _clean(self.names.get(cid, ""))
        if not d:
            return {"slug": "", "name": nm, "title": "", "icon": self._pic(cid), "jogress": False}
        return {"slug": d["slug"], "name": d.get("thai_name") or nm or d["title"], "title": d["title"],
                "icon": d.get("icon") or self._pic(cid) or d.get("image", ""),
                "jogress": "jogress" in (d.get("form") or "").lower() or "(jogress)" in d["title"].lower()}

    def chain(self, base):
        """evolution line of an egg, each Digimon once (the client repeats forms in later branches)"""
        out, seen = [], set()
        for c in self.bases.get(base, []):
            m = self.member(c)
            k = m["slug"] or m["name"]
            if k in seen:
                continue
            seen.add(k)
            m["cname"] = _clean(self.names.get(c, ""))
            out.append(m)
        return out

    # ---- matching an egg line to a client base -------------------------------------------------
    def _score(self, base, line, line_key, line_slug):
        ch = self.chain(base)
        if not line:
            return 1
        jog_names = {"shakkoumon", "silphymon", "imperialdramon"}
        if line_key in jog_names:
            return 200 if any(m["jogress"] and line_key in _norm(m["title"]) for m in ch) else -1
        want = _norm(re.sub(r"\s*\(Jogress\)$", "", line))
        for i, m in enumerate(ch):
            t = _norm(re.sub(r"\s*\(.*$", "", m["title"]))
            full = _norm(m["title"])
            if (line_slug and m["slug"] == line_slug) or want in (t, full) or line_key in (t, full):
                return 100 - i
        return -1

    def score(self, base, e):
        return self._score(base, e.get("line") or "", e.get("line_key") or "", e.get("_line_slug") or "")

    def assign(self, eggs):
        """eggs: raw egg dicts of ONE Digimon (same slug). -> {egg key: base id}; eggs that fall on a base
        already taken by a better match are the same egg under another name."""
        cands = self.by_slug.get(eggs[0]["slug"], [])
        if not cands:
            return {}
        scored = []
        for e in eggs:
            for b in cands:
                s = self._score(b, e.get("line") or "", e.get("line_key") or "", e.get("_line_slug") or "")
                if s > 0:
                    scored.append((s, -b, e["key"], b))
        scored.sort(reverse=True)
        out, used = {}, set()
        plain = {e["key"] for e in eggs if not e.get("line")}
        for k in plain:
            out[k] = min(cands)
        for s, _, k, b in scored:            # best matches first, one egg per base
            if k not in out and b not in used:
                out[k] = b
                used.add(b)
        for s, _, k, b in scored:            # the rest share a base (duplicate names of one egg)
            out.setdefault(k, b)
        return out

    # ---- egg icons ------------------------------------------------------------------------------
    def egg_icons(self):
        """client Digimon name -> icon id of its plain hatchable egg"""
        if self._items is None:
            self._items = {}
            for iid, it in self.E.items().items():
                if it["kind"] != "ไข่ที่ฟักได้":
                    continue
                n = _clean(it["name"])
                m = re.match(r"^(.+?)\s*ดิจิทามะ(?:\s*\(เมอร์เชนารี\))?$", n)
                if m and 2000 <= it["icon_id"] < 2016:
                    self._items.setdefault(re.sub(r"\s", "", m.group(1)), it["icon_id"])
        return self._items

    def icon_file(self, icon_id):
        """cut one icon out of the client atlas -> /images/client_items/icon_<id>.png"""
        key = f"icon_{icon_id}"
        return f"/images/client_items/{key}.png" if self.E.save_icon(key, icon_id) else ""

    def type_icons(self, eggs_typed):
        """eggs_typed: [(data_type, base id)] -> {data_type: icon id} by majority of the eggs the client names"""
        table = self.egg_icons()
        votes = defaultdict(Counter)
        for typ, base in eggs_typed:
            ic = table.get(re.sub(r"\s", "", _clean(self.names.get(base, ""))))
            if typ and ic:
                votes[typ][ic] += 1
        return {t: c.most_common(1)[0][0] for t, c in votes.items()}


# evodigitama.bin: the game's own list of hatchable eggs. Row (int16 pairs): u32 egg item | u32 Digimon base
# | ... | u32 data type marker @6 | byte amount @8 high byte | ...
EGG_TYPE = {2073856: "Beast", 2074112: "Rock", 2074368: "Devil", 2074624: "Bird", 2074880: "Dragon",
            2075136: "Plant", 2075392: "Fire", 2075648: "Insectoid", 2075904: "Aquatic"}
_NOT_PLAIN = re.compile(r"ระดับ|ไข่มอลล์|เมอร์เช|เมอร์เซ|สุ่ม|กิจกรรม|จัมปิ้ง|Mercenary|DigiEgg|^-$")


def _u32(a, b):
    return (a & 0xFFFF) | ((b & 0xFFFF) << 16)


def egg_table(lines):
    """-> {base id: {"item", "name", "data_type", "amount"}} for every egg line the Thai client can hatch"""
    import json
    import thai_client_evo as E
    p = E.CRACK / "out_json" / "table" / "evodigitama.json"
    if not p.exists():
        return {}
    rows = json.loads(p.read_text(encoding="utf-8"))["rows"]
    item_names = {x["id"]: (x.get("fields") or [""])[0]
                  for x in json.loads((E.CRACK / "out_json/language/item_str.json").read_text(encoding="utf-8"))}
    out = {}
    for r in rows:
        iid, base = _u32(r[0], r[1]), _u32(r[2], r[3])
        if 76000 <= base < 77000:          # "ไข่จัมปิ้ง" event copies of an existing line
            continue
        e = out.setdefault(base, {"item": 0, "name": "", "data_type": EGG_TYPE.get(_u32(r[6], r[7]), ""),
                                  "amount": (r[8] >> 8) & 0xFF})
        nm = _clean(item_names.get(iid, ""))
        if not e["name"] and nm and re.search(r"[\u0e00-\u0e7f]", nm) and not _NOT_PLAIN.search(nm):
            e["item"], e["name"] = iid, nm
    # one line listed twice under two ids (same Digimon, same evolution chain): keep the lower id
    seen = {}
    for b in sorted(out):
        sig = (_clean(lines.names.get(b, "")), tuple(lines.bases.get(b, [])))
        if sig in seen and sig[1]:
            del out[b]
        else:
            seen[sig] = b
    return out


def egg_label(item_name, base_name):
    """'กาบูมอน[เครสการูรูมอน]ดิจิทามะ' -> 'เครสการูรูมอน'; 'อังคิโลมอน ดิจิทามะ' (Armadillomon) -> 'อังคิโลมอน'"""
    s = re.sub(r"^\[[^\]]*\]", "", item_name or "")
    s = re.sub(r"\s*ดิจิทามะ.*$", "", s).strip()
    m = re.search(r"[\[(]\s*([^\])]+?)\s*[\])]", s)
    if m:
        return m.group(1).strip()
    lead = re.sub(r"\s", "", s)
    return "" if (not lead or lead == re.sub(r"\s", "", base_name)) else s.strip()
