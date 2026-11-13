"""DigiEgg (Digitama) catalogue built from dmowiki pages.

One egg = one hatchable Digimon + evolution line (e.g. "Salamon (Mikemon)").
Sources:
- Digimon infobox: "Can be hatched", "Data needed / amount" (per line when the egg has several lines)
- "Mercenary DigiEgg Drop Locations": which wild Digimon drop the egg, map, levels
- Cash-shop / event egg boxes (Riddle DigiEgg Lv.5, Reinforced Lv.4-5, Mystery Mercenary (Lv.3) ...):
  which eggs each box gives and at which hatch level (3 / 4 / 5)
"""
import json
import re

DATA_TH = {"Beast": "สัตว์", "Dragon": "มังกร", "Bird": "นก", "Aquatic": "สัตว์น้ำ", "Insectoid": "แมลง",
           "Plant": "พืช", "Devil": "ปีศาจ", "Rock": "หิน", "Fire": "ไฟ", "Mutant": "กลายพันธุ์"}

# names used by the cash-shop boxes / KDMO  ->  name used by the dex (base Digimon)
BASE_ALIAS = {
    "piyomon": "biyomon", "vmon": "veemon", "exvmon": "veemon", "armadimon": "armadillomon",
    "agumonblack": "blackagumon", "gabumonblack": "blackgabumon", "agumon": "agumonclassic",
    "ryuudamon": "ryudamon", "qinglongmon": "azulongmonchampion", "azulongmon": "azulongmonchampion",
    "xuanwumon": "ebonwumonchampion", "ebonwumon": "ebonwumonchampion",
    "zhuqiaomon": "zhuqiaomonchampion", "baihumon": "baihumonchampion", "raremon": "raremonchampion",
    "arkadimon": "arkadimonrookie", "toyagumon": "toyagumonrookie", "commandramon": "commandramon",
}
# Champion-named eggs are the Rookie egg of that line
LINE_ALIAS = {
    "woodmon": ("palmon", "woodmon"), "togemon": ("palmon", "togemon"),
    "myotismon": ("demidevimon", "myotismon"), "soulmon": ("demidevimon", "soulmon"),
    "bakemon": ("demidevimon", "bakemon"), "mechanorimon": ("hagurumon", "mechanorimon"),
    "gardromon": ("hagurumon", "guardromon"), "guardromon": ("hagurumon", "guardromon"),
    "dorugamon": ("dorumon", "dorugamon"), "dexdorugamon": ("dorumon", "dexdorugamon"),
    "musyamon": ("kotemon", "musyamon"), "gladimon": ("kotemon", "gladimon"),
    "blackgatomon": ("salamon", "blackgatomon"), "exvmon": ("veemon", "exveemon"),
    "kokuwamon": ("kokuwamon", ""), "veedramon": ("veemon", "veedramon"),
}
LINE_SYN = {"exvmon": "exveemon", "vdramon": "veedramon", "daemon": "demon", "millenniummon": "millenniumon",
            "moonmillenniummon": "moonmillenniumon", "raptordramon": "reptiledramon", "gardromon": "guardromon",
            "dukemon": "gallantmon", "typeblue": "blue", "typegreen": "green", "jogress": "jogress",
            "coredramonblue": "blue", "coredramongreen": "green",
            "exveemon": "exveemon", "imperialdramon": "imperialdramon"}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


JOGRESS_OF = {"patamon": "shakkoumon", "armadillomon": "shakkoumon", "hawkmon": "silphymon",
              "salamon": "silphymon", "veemon": "imperialdramon", "wormmon": "imperialdramon"}
INFOBOX_JOG = {("patamon", "angemonjogress"): "shakkoumon", ("wormmon", "paildramonjogress"): "imperialdramon"}


def line_key(s, base=""):
    k, b = norm(s), norm(base)
    if (b, k) in INFOBOX_JOG:
        return INFOBOX_JOG[(b, k)]
    if k.endswith("jogress") and k != "jogress":
        k = k[:-7]
    if k == "jogress":
        return JOGRESS_OF.get(b, k)
    return LINE_SYN.get(k, k)


def split_name(raw):
    """'Salamon(Lilithmon)' / 'Dracomon[Type:Blue]' / 'Agumon(Black)[BlitzGreymon]' -> (base, line)"""
    raw = raw.replace("–", "-").strip()
    parts = re.findall(r"[\(\[]([^\)\]]*)[\)\]]", raw)
    base = re.sub(r"[\(\[][^\)\]]*[\)\]]", "", raw).strip(" -")
    if parts and parts[0].strip().lower() == "black":  # Agumon(Black) -> BlackAgumon
        base = base + " black"
        parts = parts[1:]
    if parts and parts[0].strip().lower() in ("classic",):
        base = base + " classic"
        parts = parts[1:]
    line = parts[0].replace("Type:", "").strip() if parts else ""
    line = re.sub(r"\(.*$", "", line).strip() or line   # "Shakkoumon(Jogress" -> "Shakkoumon"
    return base, line


def levels_of(text, default):
    t = text.replace("~", "-")
    m = re.search(r"(?:Lv\.?|Level|\[Lv\.?)\s*(\d)\s*-\s*(\d)", t, re.I)
    if m:
        return list(range(int(m.group(1)), int(m.group(2)) + 1))
    m = re.search(r"(?:Lv\.?\s*|Level\s*|\bLv\s+)(\d)\b", t, re.I)
    if m:
        return [int(m.group(1))]
    return list(default)


# box page slug -> (default levels when an entry does not say, kind)
BOX_DEFAULT = [
    (r"^Riddle_DigiEgg_Lv\.5", (5,), "mall"),
    (r"^Rare_(BM|Jogress)_Random_DigiEgg_Lv\.5", (5,), "mall"),
    (r"^Jogress_Random_Reinforced_Digiegg_Lv5", (5,), "mall"),
    (r"^Random_Reinforced_DigiEgg_Lv\.5", (5,), "mall"),
    (r"^Awesome_May_Special_Digiegg_Lv\.5", (5,), "event"),
    (r"^Mysterious_Mercenary_DigiEgg_Lv\.5", (5,), "mall"),
    (r"Lv\.4-5", (4, 5), "mall"),
    (r"^Burst_Mode_Random_DigiEgg", (4, 5), "mall"),
    (r"^Jogress_Mercenary_DigiEgg_Triple", (3,), "mall"),
    (r"^Mystery_Mercenary_DigiEgg", (3,), "event"),
    (r"^Mystery_Extra_Mercenary_Digi-Egg", (3,), "event"),
    (r"^Random_Reinforced_Mercenary_DigiEgg", (3, 4, 5), "event"),
    (r"_Hatch_Package", (3,), "mall"),
]


def _box_entries(slug, text):
    """-> list of raw egg names found in a box page"""
    body = text.split("From Digimon Masters Online Wiki - DMO Wiki", 1)[-1]
    body = body.split("Retrieved from", 1)[0]
    body = re.split(r"\n(?:See also|\[Bonus|Category)\b", body)[0]
    lines = [l.strip() for l in body.split("\n") if l.strip()]
    out = []
    if slug.startswith("Random_Reinforced_Mercenary_DigiEgg"):
        flat = " ".join(lines)
        for seg in re.findall(r"these digimons:(.*?)(?:Random Reinforced Mercenary DigiEgg - Beta|$)", flat)[:2]:
            for tok in re.split(r"\s*,\s*|\s+and\s+|\s+or\s+", seg):
                tok = re.sub(r"\s*\(\s*", "(", tok).replace(" )", ")").replace("line", "").strip(" .")
                if tok and len(tok) < 40:
                    out.append((tok, ""))
        return out
    for l in lines:
        if re.search(r"(?i)may be obtained|scannable|component|refund|scanning cost|kind|class|hatch backup|data\b|"
                     r"fortune cookie|character bound|^contents|^this |item is|quest|^you can get|ea$|^\d|^-", l) \
                and not re.search(r"(?i)digiegg|digi-egg|mercenary", l):
            continue
        if re.search(r"(?i)hatch backup|DATA \d|DATA$|Fortune Cookie|El Evangelio|Bucephalus", l):
            continue
        m = re.match(r"(?:Reinforced Mercenary DigiEgg(?: \(Cash\))?\s*[-–]\s*|Reinforced Mercenary DigiEgg\s*\[|"
                     r"Mystery DigiEgg\s+)?(.+?)\s*(?:\]\s*)?(?:Digi-?egg|DigiEgg|Lv \d|Lv\.?\s?\d|$)(.*)$", l, re.I)
        if not m:
            continue
        name = m.group(1).strip(" -–[]")
        name = re.sub(r"\s*-\s*\d+%$", "", name).strip()
        if not name or len(name) > 45 or re.search(r"(?i)digimons|items|possibly|phase|any reinforced", name):
            continue
        out.append((name, l))
    return out


def build_eggs(dex, conn):
    rows = {r[0]: (r[1], json.loads(r[2])) for r in conn.execute(
        "SELECT slug, title, data_json FROM pages WHERE slug NOT LIKE 'File:%' AND slug NOT LIKE 'Special:%' "
        "AND slug NOT LIKE 'Talk:%' AND slug != 'index.php'")}

    def find_dex(base):
        k = norm(base)
        k = BASE_ALIAS.get(k, k)
        d = dex.by_key.get(k)
        if not d:
            d = dex.by_key.get(k + "rookie") or dex.by_key.get(k + "champion")
        return d

    eggs = {}

    def egg_for(d, line):
        lk = line_key(line, re.sub(r"\s*\(.*$", "", d["title"]))
        key = d["slug"] + ("|" + lk if lk else "")
        e = eggs.get(key)
        if not e:
            e = eggs[key] = {"key": key, "slug": d["slug"], "line": line, "line_key": lk,
                             "drops": [], "boxes": [], "data_type": "", "data_amount": "", "hatchable": False}
        elif line and not e["line"]:
            e["line"] = line
        return e

    def resolve(raw):
        base, line = split_name(raw)
        nb = norm(base)
        if nb in LINE_ALIAS and not line:
            b2, l2 = LINE_ALIAS[nb]
            base, line = b2, l2
        d = find_dex(base)
        return d, line

    # 1) infobox: hatchable + data per line
    for d in dex.digimon:
        if not str(d.get("can_hatch", "")).lower().startswith("y"):
            continue
        raw = [x for x in d.get("hatch_data_raw", []) if x.strip() != ":"]
        pairs, cur = [], None
        for x in raw:
            m = re.match(r"^\s*([A-Za-z]+)\s*/\s*(\d+)\s*$", x)
            if m:
                pairs.append((cur or "", m.group(1), m.group(2)))
                cur = None
            else:
                cur = x.strip().rstrip(":")
        if not pairs:
            e = egg_for(d, "")
            e["hatchable"] = True
            continue
        multi = len(pairs) > 1
        for line, typ, amt in pairs:
            e = egg_for(d, line if multi else "")
            e.update(hatchable=True, data_type=typ, data_amount=amt)

    # 2) map drops
    page = rows.get("Mercenary_DigiEgg_Drop_Locations")
    if page:
        lines = [l.strip() for l in page[1]["text"].split("\n")]
        # the page repeats its headings (contents list + body): keep the longest block per egg
        blocks, cur = [], None
        for l in lines:
            m = re.match(r"^(.+?)\s*Mercenary Egg:$", l)
            if m:
                cur = [m.group(1).strip(), []]
                blocks.append(cur)
            elif l.startswith("Retrieved from"):
                break
            elif cur is not None and l:
                cur[1].append(l)
        best = {}
        for name, buf in blocks:
            vals = [x for x in buf if x not in ("Digimon", "Where found", "Levels")]
            rows3 = []
            for i in range(0, len(vals) - 2, 3):
                if not vals[i + 2].startswith("Levels"):
                    break
                rows3.append({"monster": vals[i], "map": vals[i + 1],
                              "levels": vals[i + 2].replace("Levels:", "").strip()})
            if len(rows3) > len(best.get(name, [])):
                best[name] = rows3
        for name, rows3 in best.items():
            if name.startswith("Random"):
                continue
            d, line = resolve(name)
            if d:
                egg_for(d, line)["drops"].extend(rows3)

    # 3) cash-shop / event boxes
    for slug, (title, data) in rows.items():
        rule = next((r for r in BOX_DEFAULT if re.search(r[0], slug)), None)
        if not rule:
            continue
        img = dex.icon_for(title, [], ("",)) or dex.icon_for(slug.replace("_", " "), [], ("",))
        for raw, full in _box_entries(slug, data.get("text", "")):
            d, line = resolve(raw)
            if not d:
                continue
            e = egg_for(d, line)
            lv = levels_of(full, rule[1]) if full else list(rule[1])
            if any(b["box"] == title for b in e["boxes"]):
                b = next(b for b in e["boxes"] if b["box"] == title)
                b["levels"] = sorted(set(b["levels"]) | set(lv))
                continue
            e["boxes"].append({"box": title, "slug": slug, "levels": lv, "kind": rule[2], "image": img})

    # Hyper Spirits are not "hatchable" in their infobox but are unlocked at Bokomon like the other Spirits
    for d in dex.digimon:
        if d["title"] in HYPER_SPIRITS:
            egg_for(d, "")["hatchable"] = True

    # a plain "Gabumon DigiEgg" is the default (first) line of an egg that lists several lines in its infobox
    for d in dex.digimon:
        lines = [x.strip().rstrip(":") for x in d.get("hatch_data_raw", [])
                 if x.strip() != ":" and not re.match(r"^\s*[A-Za-z]+\s*/\s*\d+\s*$", x)]
        plain = eggs.get(d["slug"])
        if not lines or not plain:
            continue
        tgt = eggs.get(d["slug"] + "|" + line_key(lines[0], re.sub(r"\s*\(.*$", "", d["title"])))
        if not tgt:
            continue
        tgt["drops"] += plain["drops"]
        for b in plain["boxes"]:
            ob = next((x for x in tgt["boxes"] if x["box"] == b["box"]), None)
            if ob:
                ob["levels"] = sorted(set(ob["levels"]) | set(b["levels"]))
            else:
                tgt["boxes"].append(b)
        del eggs[d["slug"]]

    # line labels + the dex page of the line, needed to find the egg's real line in the client
    for e in eggs.values():
        if e["line_key"] in JOGRESS_OF.values():
            e["line"] = {"shakkoumon": "Shakkoumon", "silphymon": "Silphymon",
                         "imperialdramon": "Imperialdramon"}[e["line_key"]] + " (Jogress)"
        elif e["line_key"] in ("blue", "green"):
            e["line"] = e["line_key"].title()
        e["_line_d"] = None
        if e["line"]:
            ln = re.sub(r"\s*\(Jogress\)$", "", e["line"])
            e["_line_d"] = dex.by_key.get(norm(ln)) or dex.by_key.get(norm(ln + " (Jogress)"))
        e["_line_slug"] = e["_line_d"]["slug"] if e["_line_d"] else ""

    # The Thai client's egg table (evodigitama) is the list of eggs: one egg per base id
    # (Gabumon = "กาบูมอน" 31138 + "กาบูมอน[เครสการูรูมอน]" 33082). dmowiki's eggs only add drops, mall boxes and
    # screenshots to the client egg they belong to.
    try:
        from egg_client import ClientLines, egg_table, egg_label
        CL = ClientLines(dex)
        table = egg_table(CL)
    except Exception as ex:
        print("[WARN] client egg table unavailable:", ex)
        CL, table = None, {}
    if CL and table:
        client = {}                      # slug -> [base ids]
        for base in sorted(table):
            if not CL.bases.get(base):   # placeholder rows with no evolution line
                continue
            d = CL.find(base)
            if d:
                client.setdefault(d["slug"], []).append(base)
        wiki_by_slug = {}
        for e in eggs.values():
            wiki_by_slug.setdefault(e["slug"], []).append(e)
        new = {}
        for slug, bases in client.items():
            d = next((x for x in dex.digimon if x["slug"] == slug), None)
            base_name = CL._base_name(bases[0])
            # label = what the egg item says ("กาบูมอน[เครสการูรูมอน]"), else the bracket in the client's
            # Digimon name ("สึไกมอน[บาร์บามอน]")
            labels = {b: egg_label(table[b]["name"], base_name) or egg_label(CL.names.get(b, "") + " ดิจิทามะ", base_name)
                      for b in bases}
            plain = next((b for b in bases if not labels[b]), None) if len(bases) > 1 else bases[0]
            # other eggs with no label (two "พัลมอน ดิจิทามะ", Hawkmon's Silphymon egg): name them after the first
            # Digimon of their line that the plain egg's line does not have (a Jogress form first)
            if len(bases) > 1:
                pc = {m["slug"] or m["name"] for m in CL.chain(plain)} if plain else set()
                for b in bases:
                    if b != plain and not labels[b] and CL.chain(b):
                        ch = [m for m in CL.chain(b) if (m["slug"] or m["name"]) not in pc] or CL.chain(b)
                        labels[b] = ch[0]["cname"]
            wiki = wiki_by_slug.pop(slug, [])
            # which wiki egg is which client egg
            asg = {}
            if len(bases) == 1:
                asg = {w["key"]: bases[0] for w in wiki}
            else:
                for w in wiki:
                    best = max(bases, key=lambda b: (CL.score(b, w), -b))
                    if CL.score(best, w) <= 0 or not w["line"]:
                        best = plain or bases[0]
                    asg[w["key"]] = best
            for base in bases:
                t = table[base]
                chain = CL.chain(base)
                lab = "" if base == plain else labels[base]
                mine = [w for w in wiki if asg.get(w["key"]) == base]
                # English line name: the chain member the Thai label names, else the wiki egg's line
                line = ""
                if lab:
                    k = lab.replace(" ", "")
                    hit = next((m for m in chain if k and (k in m["cname"].replace(" ", "") or
                                                           k in m["name"].replace(" ", ""))), None)
                    line = re.sub(r"\s*\((?:Jogress|Champion|Ultimate|Mega)\)", "", hit["title"]).strip() if hit else ""
                    if not line:
                        line = {"ฟ้า": "Blue", "เขียว": "Green", "ออริจินัล": "Original",
                                "อาโพคารีมอน": "Apocalymon"}.get(lab.replace(" ", ""), "")
                    if not line:
                        line = next((w["line"] for w in mine if w["line"]), "") or (chain[0]["title"] if chain else lab)
                key = slug + ("|" + norm(line or lab) if (lab and len(bases) > 1) else "")
                if key in new:
                    key += f"-{base}"
                e = {"key": key, "slug": slug, "line": line, "line_key": norm(line), "line_label_th": lab,
                     "drops": [], "boxes": [], "data_type": t["data_type"], "data_amount": str(t["amount"] or ""),
                     "hatchable": True, "_base": base, "_aka": [], "egg_item_th": t["name"]}
                for w in sorted(mine, key=lambda w: -len(w["drops"])):
                    e["drops"] += [x for x in w["drops"] if x not in e["drops"]]
                    for bx in w["boxes"]:
                        ob = next((x for x in e["boxes"] if x["box"] == bx["box"]), None)
                        if ob:
                            ob["levels"] = sorted(set(ob["levels"]) | set(bx["levels"]))
                        else:
                            e["boxes"].append(bx)
                    if w["line"] and norm(w["line"]) != norm(line):
                        e["_aka"].append(w["line"])
                    if not e["data_type"]:
                        e["data_type"], e["data_amount"] = w["data_type"], w["data_amount"]
                e["_line_d"] = None
                if line:
                    e["_line_d"] = next((dex.by_key.get(norm(x)) for x in
                                         (line, line + " (Jogress)", line + " (Champion)", line + " (Ultimate)")
                                         if dex.by_key.get(norm(x))), None)
                    if e["_line_d"] and line != "Apocalymon" and not any(m["slug"] == e["_line_d"]["slug"] for m in chain):
                        e["_line_d"] = None
                    if not e["_line_d"] and chain:
                        e["_line_d"] = next((x for x in dex.digimon if x["slug"] == next(
                            (m["slug"] for m in chain if norm(line) in norm(m["title"])), chain[0]["slug"])), None)
                e["_line_slug"] = e["_line_d"]["slug"] if e["_line_d"] else ""
                new[key] = e
        # eggs the Thai client cannot hatch are dropped, except Spirits (not eggs in the client)
        dropped = []
        for slug, ws in wiki_by_slug.items():
            dd = next((x for x in dex.digimon if x["slug"] == slug), None)
            if dd and ("hybrid" in (dd.get("form") or "").lower() or dd["title"] in HYPER_SPIRITS):
                for w in ws:
                    new[w["key"]] = w
            else:
                dropped += [w["key"] for w in ws]
        if dropped:
            print(f"[EGGS] not hatchable in the Thai client, hidden: {', '.join(sorted(dropped))}")
        eggs = new
    type_icon = {}
    if CL:
        type_icon = CL.type_icons([(e["data_type"], e["_base"]) for e in eggs.values() if e.get("_base")])

    # finish: fill data from sibling line / base egg, Thai labels, icons, tags
    by_slug = {}
    for e in eggs.values():
        by_slug.setdefault(e["slug"], []).append(e)
    out = []
    for e in eggs.values():
        d = dex.by_key.get(norm(e["slug"])) or next((x for x in dex.digimon if x["slug"] == e["slug"]), None)
        if not d or not d.get("in_thai", True):
            continue
        sib = by_slug[e["slug"]]
        if not e["data_type"]:
            src = next((s for s in sib if s["data_type"] and s["line_key"] == e["line_key"]), None) \
                or next((s for s in sib if s["data_type"]), None)
            if src:
                e["data_type"], e["data_amount"] = src["data_type"], src["data_amount"]
            e["hatchable"] = e["hatchable"] or any(s["hatchable"] for s in sib)
        typ = e["data_type"]
        line_d = e.get("_line_d")
        chain = CL.chain(e["_base"]) if (CL and e.get("_base")) else []
        levels = sorted({lv for b in e["boxes"] for lv in b["levels"]})
        spirit = "hybrid" in (d.get("form") or "").lower()

        # ตรวจสอบว่าเป็นสายโจเกรสหรือไม่
        line_raw = (e.get('line') or '').lower()
        title_raw = (d.get('title') or '').lower()
        lk_val = e.get('line_key') or ''
        jog = False
        if not spirit and chain:
            # the game's own evolution table decides: a line that reaches a Jogress Digimon is a Jogress egg
            jog = any(m["jogress"] for m in chain) or "jogress" in ((line_d or {}).get("form") or "").lower()
        elif not spirit:
            if 'jogress' in line_raw or lk_val in JOGRESS_OF.values():
                jog = True
            elif title_raw in ('agumon (classic)', 'gabumon') and not line_raw:
                jog = True
            elif 'alter-s' in line_raw or 'blitzgreymon' in line_raw or 'cresgarurumon' in line_raw:
                jog = True
            elif title_raw == 'ryudamon':
                jog = True
            elif 'dorumon' in title_raw and (not line_raw or 'alpha' in line_raw or 'raptor' in line_raw or 'dorugamon' in line_raw):
                jog = True
            elif 'dracomon' in title_raw:
                jog = True
            elif 'veemon' in title_raw and ('imperial' in line_raw or 'ex-veemon' in line_raw or not line_raw):
                jog = True
            elif 'wormmon' in title_raw and ('imperial' in line_raw or 'sting' in line_raw or not line_raw):
                jog = True
            elif 'hawkmon' in title_raw and ('silphy' in line_raw or 'aquila' in line_raw or not line_raw):
                jog = True
            elif 'salamon' in title_raw and ('silphy' in line_raw or 'blackgatomon' in line_raw):
                jog = True
            elif 'patamon' in title_raw and ('shakkou' in line_raw or 'ange' in line_raw or not line_raw):
                jog = True
            elif 'armadillomon' in title_raw and ('shakkou' in line_raw or 'ankyl' in line_raw or not line_raw):
                jog = True
            elif 'millennium' in line_raw:
                jog = True
            elif any(title_raw.startswith(b) for b in ('azulongmon', 'baihumon', 'ebonwumon', 'zhuqiaomon')):
                jog = True
            elif 'meicoomon' in title_raw:
                jog = True
            elif any(title_raw.startswith(b) for b in ('shoutmon', 'ballistamon', 'mailbirdramon', 'greymon (c)')):
                jog = True

        # สร้างข้อมูลไข่มอลล์ / อีเวนต์ (เซิร์ฟเวอร์ไทย CrackDMO)
        fam = {"aquatic": "water", "insectoid": "insect", "rock": "universal"}.get((typ or "").lower(), (typ or "universal").lower())
        if fam not in ('dragon', 'beast', 'devil', 'bird', 'plant', 'fire', 'insect', 'water', 'mutant', 'universal'):
            fam = "universal"
        # the client's own egg icons: plain / Lv.3 = icon, Lv.4 = icon + 16, Lv.5 = icon + 32
        tic = type_icon.get(typ)
        lv_icon = {3: (CL.icon_file(tic) if tic else "") or f"/images/client_items/egg_reinforced_lv3_{fam}.png",
                   4: (CL.icon_file(tic + 16) if tic else "") or f"/images/client_items/egg_reinforced_lv4_{fam}.png",
                   5: (CL.icon_file(tic + 32) if tic else "") or f"/images/client_items/egg_reinforced_lv5_{fam}.png"}
        digi_name_th = d.get("thai_name") or d["title"]

        mall_eggs = []
        if not spirit:
            if jog:
                mall_eggs = [
                    {
                        "level": 4,
                        "name_th": f"ไข่ดิจิมอนโจเกรสเสริมพลัง ระดับ 4 [{digi_name_th}]",
                        "name_en": f"Jogress Reinforced Mercenary DigiEgg Lv.4 [{d['title']}]",
                        "icon": "/images/client_items/egg_jogress_lv4_large.png",
                        "tag": "Lv.4 โจเกรส",
                        "tag_class": "jogress lv4",
                        "desc": "ไข่ดิจิมอนสายโจเกรส ใส่ดาต้าสำเร็จ 4 ขั้น การันตีฟักสำเร็จ 100% (ขนาดตัว ~110% - 125%)",
                        "is_jogress": True,
                    },
                    {
                        "level": 5,
                        "name_th": f"ไข่ดิจิมอนโจเกรสเสริมพลัง ระดับ 5 [{digi_name_th}]",
                        "name_en": f"Jogress Reinforced Mercenary DigiEgg Lv.5 [{d['title']}]",
                        "icon": "/images/client_items/egg_jogress_lv5_large.png",
                        "tag": "Lv.5 โจเกรส",
                        "tag_class": "jogress lv5",
                        "desc": "ไข่ดิจิมอนสายโจเกรส ใส่ดาต้าสำเร็จ 5 ขั้น การันตีฟักสำเร็จ 100% (ขนาดตัว 125% ขึ้นไป · ขนาดใหญ่สุด)",
                        "is_jogress": True,
                    },
                    {
                        "level": 45,
                        "name_th": "ไข่สุ่มดิจิทามะโจเกรสลึกลับ [ระดับ 4-5]",
                        "name_en": "Mystery Jogress Reinforced DigiEgg [Lv.4-5]",
                        "icon": "/images/client_items/egg_jogress_lv4.png",
                        "tag": "สุ่ม 4-5 โจเกรส",
                        "tag_class": "jogress lv45",
                        "desc": "สุ่มรับไข่ดิจิมอนโจเกรสเสริมพลัง ระดับ 4 หรือ ระดับ 5 แบบสุ่มตัว",
                        "is_jogress": True,
                    },
                ]
            else:
                mall_eggs = [
                    {
                        "level": 3,
                        "name_th": f"ไข่ดิจิมอนเสริมพลัง ระดับ 3 [{digi_name_th}]",
                        "name_en": f"Reinforced Mercenary DigiEgg Lv.3 [{d['title']}]",
                        "icon": lv_icon[3],
                        "tag": "Lv.3 (3/5)",
                        "tag_class": "lv3",
                        "desc": "ใส่ดาต้าสำเร็จ 3 ขั้น การันตีฟักสำเร็จ 100% (ขนาดตัว ~85% - 100%)",
                        "is_jogress": False,
                    },
                    {
                        "level": 4,
                        "name_th": f"ไข่ดิจิมอนเสริมพลัง ระดับ 4 [{digi_name_th}]",
                        "name_en": f"Reinforced Mercenary DigiEgg Lv.4 [{d['title']}]",
                        "icon": lv_icon[4],
                        "tag": "Lv.4 (4/5)",
                        "tag_class": "lv4",
                        "desc": "ใส่ดาต้าสำเร็จ 4 ขั้น การันตีฟักสำเร็จ 100% (ขนาดตัว ~110% - 125%)",
                        "is_jogress": False,
                    },
                    {
                        "level": 5,
                        "name_th": f"ไข่ดิจิมอนเสริมพลัง ระดับ 5 [{digi_name_th}]",
                        "name_en": f"Reinforced Mercenary DigiEgg Lv.5 [{d['title']}]",
                        "icon": lv_icon[5],
                        "tag": "Lv.5 (5/5)",
                        "tag_class": "lv5",
                        "desc": "ใส่ดาต้าสำเร็จ 5 ขั้น การันตีฟักสำเร็จ 100% (ขนาดตัว 125% ขึ้นไป · ขนาดใหญ่สุด)",
                        "is_jogress": False,
                    },
                ]

        tags = []
        if e["drops"]:
            tags.append("drop")
        else:
            tags.append("nodrop")
        if mall_eggs:
            tags.append("mall")
        if jog:
            tags.append("jogress")
            tags += ["lv4", "lv5"]
        else:
            tags += ["lv3", "lv4", "lv5"]
        tags += [f"lv{lv}" for lv in levels]
        si = spirit_info(dex, d) if spirit else None
        # the line shown for the egg: its named line, else (Dracomon "Blue") the first step of the client line
        first = chain[0] if chain else None
        if line_d:
            lm = next((m for m in chain if m["slug"] == line_d["slug"]), None)
            line_info = {"th": line_d.get("thai_name") or "", "slug": line_d["slug"],
                         "icon": line_d.get("icon") or (lm or {}).get("icon", "")}
        elif e["line"] and first and first["slug"]:
            line_info = {"th": first["name"], "slug": first["slug"], "icon": first["icon"]}
        else:
            line_info = {"th": "", "slug": "", "icon": ""}
        if spirit:
            tags.append("spirit")
            if si and si.get("hyper"):
                tags.append("spirit-high")
            else:
                tags.append("spirit-norm")
        out.append({
            **{k: e[k] for k in ("key", "slug", "line", "drops", "boxes", "data_type", "data_amount")},
            "title": d["title"], "thai_name": d.get("thai_name", ""), "form": d.get("form", ""),
            "form_th": d.get("form_th", ""), "icon": d.get("icon", ""), "image": d.get("image", ""),
            "attribute": d.get("attribute", ""), "attribute_icon": d.get("attribute_icon", ""),
            "element": d.get("element", ""), "element_icon": d.get("element_icon", ""),
            "line_th": line_info["th"], "line_slug": line_info["slug"], "line_icon": line_info["icon"],
            "chain": [{k: m[k] for k in ("slug", "name", "title", "icon", "jogress")} for m in chain],
            "aka": [x for x in e.get("_aka", []) if x],
            "client_name": CL._base_name(e["_base"]) if (CL and e.get("_base")) else "",
            "egg_item_th": e.get("egg_item_th", ""), "line_label_th": e.get("line_label_th", ""),
            "egg_name": ((si["item_th"] if si else f"{d['title']} Spirit") if spirit else f"{d['title']}{' (' + e['line'] + ')' if e['line'] else ''} DigiEgg"),
            "egg_icon": ((si["item_icon"] if (spirit and si) else "") or (CL.icon_file(tic) if (CL and tic) else "")
                         or dex.icon_for(f"{typ} Mercenary DigiEgg", [], ("",)) or dex.icon_for(f"{typ} DigiEgg", [], ("",))
                         or dex.icon_for(f"{typ} DigiEgg Low Class", [], ("",))) if typ else "",
            "data_th": DATA_TH.get(typ, typ),
            "data_item": f"{typ} Low Class DATA" if typ else "",
            "data_icon": (dex.icon_for(f"{typ} Low Class Data", [], ("",)) if typ else ""),
            "hatch_shot": _line_shot(dex, d["title"], [e["line"]] + e.get("_aka", [])),
            "levels": levels, "tags": tags, "spirit": spirit,
            "spirit_info": si,
            "is_jogress": jog,
            "mall_eggs": mall_eggs,
            "hatchable": e["hatchable"] or bool(e["drops"]) or bool(e["boxes"]) or bool(mall_eggs),
            "drops": [{**x, "monster_slug": (dex.by_key.get(norm(x["monster"])) or {}).get("slug", ""),
                       "monster_th": dex.thai_of_digimon(x["monster"]),
                       "map_th": dex.vocab.get("location", {}).get(x["map"], "")} for x in e["drops"]],
        })
    # one hatching screenshot per line: when several lines of a Digimon got the same picture, keep it on the
    # line it names (else the plain, non-Jogress line) - the others show their own evolution strip instead
    shots = {}
    for x in out:
        if x["hatch_shot"] and not x["spirit"]:
            shots.setdefault((x["slug"], x["hatch_shot"]), []).append(x)
    for (_, shot), xs in shots.items():
        if len(xs) < 2:
            continue
        fn = norm(shot.rsplit("/", 1)[-1])
        def rank(x):
            names = [norm(x["line"])] + [norm(a) for a in x["aka"]] + [norm(m["title"]) for m in x["chain"][:1]]
            return (any(n and n in fn for n in names), len(x["drops"]), not x["is_jogress"])
        keep = max(xs, key=rank)
        for x in xs:
            if x is not keep:
                x["hatch_shot"] = ""
    out.sort(key=lambda x: (x["title"].lower(), x["line"].lower()))
    return out


SPIRIT_ELEM = {"Pitch Black": "Darkness", "Land": "Earth"}
ELEM_KARAOKE = {"Fire": "ไฟร์", "Wind": "วินด์", "Ice": "ไอซ์", "Wood": "วู้ด", "Earth": "เอิร์ธ", "Light": "ไลท์",
                "Thunder": "ธันเดอร์", "Water": "วอเตอร์", "Darkness": "ดาร์กเนส", "Steel": "สตีล"}


# ข้อมูลสปิริต 20 ตัวธรรมดา (กรอบสีฟ้า) อิงจากไฟล์แคตตาล็อกไอเทมเซิร์ฟไทย (CrackDMO: item_catalog.json)
NORMAL_SPIRITS_DATA = {
    # title: (item_id, item_th, elem_th, shining_id, shining_th)
    "Agnimon": (99101, "ฮิวแมนสปิริตแห่งไฟ", "ไฟ", 99121, "ฮิวแมนสปิริตแห่งไฟขั้นสูง"),
    "BurningGreymon": (99102, "บีสต์สปิริตแห่งไฟ", "ไฟ", 99122, "บีสต์สปิริตแห่งไฟขั้นสูง"),
    "Kazemon": (99103, "ฮิวแมนสปิริตแห่งลม", "ลม", 99123, "ฮิวแมนสปิริตแห่งลมขั้นสูง"),
    "Zephyrmon": (99104, "บีสต์สปิริตแห่งลม", "ลม", 99124, "บีสต์สปิริตแห่งลมขั้นสูง"),
    "Kumamon": (99105, "ฮิวแมนสปิริตแห่งน้ำแข็ง", "น้ำแข็ง", 99125, "ฮิวแมนสปิริตแห่งน้ำแข็งขั้นสูง"),
    "Korikakumon": (99106, "บีสต์สปิริตแห่งน้ำแข็ง", "น้ำแข็ง", 99126, "บีสต์สปิริตแห่งน้ำแข็งขั้นสูง"),
    "Arbormon": (99107, "ฮิวแมนสปิริตแห่งไม้", "ไม้", 99127, "ฮิวแมนสปิริตแห่งไม้ขั้นสูง"),
    "Petaldramon": (99108, "บีสสปิริตแห่งไม้", "ไม้", 99128, "บีสสปิริตแห่งไม้ขั้นสูง"),
    "Grumblemon": (99109, "ฮิวแมนสปิริตแห่งดิน", "ดิน", 99129, "ฮิวแมนสปิริตแห่งดินขั้นสูง"),
    "Gigasmon": (99110, "บีสต์สปิริตแห่งดิน", "ดิน", 99130, "บีสต์สปิริตแห่งดินขั้นสูง"),
    "Wolfmon": (99111, "ฮิวแมนสปิริตแห่งแสง", "แสง", 99131, "ฮิวแมนสปิริตแห่งแสงขั้นสูง"),
    "Garmmon": (99112, "บีสต์สปิริตแห่งแสง", "แสง", 99132, "บีสต์สปิริตแห่งแสงขั้นสูง"),
    "Blitzmon": (99113, "ฮิวแมนสปิริตแห่งสายฟ้า", "สายฟ้า", 99133, "ฮิวแมนสปิริตแห่งสายฟ้าขั้นสูง"),
    "Bolgmon": (99114, "บีสต์สปิริตแห่งสายฟ้า", "สายฟ้า", 99134, "บีสต์สปิริตแห่งสายฟ้าขั้นสูง"),
    "Ranamon": (99115, "ฮิวแมนสปิริตแห่งน้ำ", "น้ำ", 99135, "ฮิวแมนสปิริตแห่งน้ำชั้นสูง"),
    "Calmaramon": (99116, "บีสต์สปิริตแห่งน้ำ", "น้ำ", 99136, "บีสต์สปิริตแห่งน้ำชั้นสูง"),
    "Löwemon": (99117, "ฮิวแมนสปิริตแห่งความมืด", "ความมืด", 99137, "ฮิวแมนสปิริตแห่งความมืดขั้นสูง"),
    "KaiserLeomon": (99118, "บีสต์สปิริตแห่งความมืด", "ความมืด", 99138, "บีสต์สปิริตแห่งความมืดขั้นสูง"),
    "Mercuremon": (99119, "ฮิวแมนสปิริตแห่งเหล็ก", "เหล็ก", 99139, "ฮิวแมนสปิริตแห่งเหล็กขั้นสูง"),
    "Mercurymon": (99119, "ฮิวแมนสปิริตแห่งเหล็ก", "เหล็ก", 99139, "ฮิวแมนสปิริตแห่งเหล็กขั้นสูง"),
    "Sefirotmon": (99120, "บีสต์สปิริตแห่งเหล็ก", "เหล็ก", 99140, "บีสต์สปิริตแห่งเหล็กขั้นสูง"),
}

# สปิริตขั้นสูง (H - กรอบสีม่วง) 10 ชิ้น สำหรับ ไคเซอร์เกรย์มอน (ธาตุ ไฟ, ลม, น้ำแข็ง, ไม้, ดิน)
KAISER_SHININGS = [
    (99121, "ฮิวแมนสปิริตแห่งไฟขั้นสูง (H)", "ไฟ"),
    (99122, "บีสต์สปิริตแห่งไฟขั้นสูง (H)", "ไฟ"),
    (99123, "ฮิวแมนสปิริตแห่งลมขั้นสูง (H)", "ลม"),
    (99124, "บีสต์สปิริตแห่งลมขั้นสูง (H)", "ลม"),
    (99125, "ฮิวแมนสปิริตแห่งน้ำแข็งขั้นสูง (H)", "น้ำแข็ง"),
    (99126, "บีสต์สปิริตแห่งน้ำแข็งขั้นสูง (H)", "น้ำแข็ง"),
    (99127, "ฮิวแมนสปิริตแห่งไม้ขั้นสูง (H)", "ไม้"),
    (99128, "บีสสปิริตแห่งไม้ขั้นสูง (H)", "ไม้"),
    (99129, "ฮิวแมนสปิริตแห่งดินขั้นสูง (H)", "ดิน"),
    (99130, "บีสต์สปิริตแห่งดินขั้นสูง (H)", "ดิน"),
]

# สปิริตขั้นสูง (H - กรอบสีม่วง) 10 ชิ้น สำหรับ แมคนาการูรูมอน (ธาตุ แสง, สายฟ้า, น้ำ, ความมืด, เหล็ก)
MAGNA_SHININGS = [
    (99131, "ฮิวแมนสปิริตแห่งแสงขั้นสูง (H)", "แสง"),
    (99132, "บีสต์สปิริตแห่งแสงขั้นสูง (H)", "แสง"),
    (99133, "ฮิวแมนสปิริตแห่งสายฟ้าขั้นสูง (H)", "สายฟ้า"),
    (99134, "บีสต์สปิริตแห่งสายฟ้าขั้นสูง (H)", "สายฟ้า"),
    (99135, "ฮิวแมนสปิริตแห่งน้ำชั้นสูง (H)", "น้ำ"),
    (99136, "บีสต์สปิริตแห่งน้ำชั้นสูง (H)", "น้ำ"),
    (99137, "ฮิวแมนสปิริตแห่งความมืดขั้นสูง (H)", "ความมืด"),
    (99138, "บีสต์สปิริตแห่งความมืดขั้นสูง (H)", "ความมืด"),
    (99139, "ฮิวแมนสปิริตแห่งเหล็กขั้นสูง (H)", "เหล็ก"),
    (99140, "บีสต์สปิริตแห่งเหล็กขั้นสูง (H)", "เหล็ก"),
]

HYPER_SPIRITS = ["KaiserGreymon", "MagnaGarurumon"]


def hyper_spirit_info(dex, d):
    """KaiserGreymon / MagnaGarurumon: ปลดที่โบโคมอน ด้วยสปิริตขั้นสูง (H) ครบ 10 ชิ้น + สารานุกรมโบโคมอน + เงิน 1 T"""
    title = d.get("title")
    is_kaiser = (title == "KaiserGreymon")
    raw = KAISER_SHININGS if is_kaiser else MAGNA_SHININGS
    shinings = [{
        "item_id": s_id,
        "item": s_name,
        "item_th": s_name,
        "icon": f"/images/client_items/{s_id}.png",
        "elem_th": s_elem,
        "frame_color": "purple",
        "rank_type": "H"
    } for s_id, s_name, s_elem in raw]

    elems_th = ["ไฟ", "ลม", "น้ำแข็ง", "ไม้", "ดิน"] if is_kaiser else ["แสง", "สายฟ้า", "น้ำ", "ความมืด", "เหล็ก"]
    return {
        "hyper": True,
        "shinings": shinings,
        "item": "สปิริตขั้นสูง (H) ×10",
        "item_th": "สปิริตขั้นสูง (H) 10 ชิ้น",
        "item_icon": shinings[0]["icon"],
        "rank_type": "H",
        "type_th": "สปิริตขั้นสูง (H)",
        "frame_color": "purple",
        "book": "สารานุกรมโบโคมอน",
        "book_th": "สารานุกรมโบโคมอน",
        "book_icon": "/images/client_items/99100.png",
        "npc": "Bokomon",
        "npc_th": "โบโคมอน",
        "npc_icon": dex.icon_for("Bokomon Icon", [], ("",)) or "/images/Bokomon_Icon.png",
        "npc_map_th": "ศูนย์บัญชาการ DATS",
        "money_cost": "1 T",
        "money_th": "1 T (1,000 M)",
        "money_icon": "/images/client_items/money_tera.png",
        "money_total_th": "6 T (ค่าแลกสปิริต 10 ชิ้น 5 T + ค่าปลด 1 T)",
        "elem": d.get("element", ""),
        "elem_th": dex.vocab.get("element", {}).get(d.get("element"), ""),
        "elems_th": elems_th,
    }


def spirit_info(dex, d):
    """สปิริตทั้ง 20 ตัว ฟักที่ NPC โบโคมอน โดยใช้สปิริตธรรมดา ไม่ใช้แบบ H"""
    title = d.get("title")
    if title in HYPER_SPIRITS:
        return hyper_spirit_info(dex, d)

    entry = NORMAL_SPIRITS_DATA.get(title)
    if not entry:
        m = re.match(r"^([HB])-Hybrid$", d.get("form") or "")
        if not m:
            return None
        elem = SPIRIT_ELEM.get(d.get("element"), d.get("element"))
        return {
            "hyper": False,
            "item_id": 99101,
            "item": f"ฮิวแมนสปิริตแห่ง{elem}",
            "item_th": f"ฮิวแมนสปิริตแห่ง{elem}",
            "item_icon": "/images/client_items/99101.png",
            "rank_type": "ธรรมดา",
            "type_th": "สปิริตธรรมดา",
            "frame_color": "blue",
            "shining_id": 99121,
            "shining": f"ฮิวแมนสปิริตแห่ง{elem}ขั้นสูง (H)",
            "shining_icon": "/images/client_items/99121.png",
            "book": "สารานุกรมโบโคมอน",
            "book_th": "สารานุกรมโบโคมอน",
            "book_icon": "/images/client_items/99100.png",
            "card": "Spirit Summon Card",
            "card_th": "สปิริต ซัมมอน การ์ด",
            "card_icon": dex.icon_for("Spirit Summon Card", [], ("",)) or "/images/Spirit_summon_card.jpg",
            "npc": "Bokomon",
            "npc_th": "โบโคมอน",
            "npc_icon": dex.icon_for("Bokomon Icon", [], ("",)) or "/images/Bokomon_Icon.png",
            "npc_map_th": "ศูนย์บัญชาการ DATS",
            "money_cost": "0",
            "money_th": "",
            "money_icon": "",
            "elem": elem,
            "elem_th": dex.vocab.get("element", {}).get(d.get("element"), ""),
        }

    item_id, item_th, elem_th, shining_id, shining_th = entry
    return {
        "hyper": False,
        "item_id": item_id,
        "item": item_th,
        "item_th": item_th,
        "item_icon": f"/images/client_items/{item_id}.png",
        "rank_type": "ธรรมดา",
        "type_th": "สปิริตธรรมดา",
        "frame_color": "blue",
        "shining_id": shining_id,
        "shining": f"{shining_th} (H)",
        "shining_icon": f"/images/client_items/{shining_id}.png",
        "book": "สารานุกรมโบโคมอน",
        "book_th": "สารานุกรมโบโคมอน",
        "book_icon": "/images/client_items/99100.png",
        "card": "Spirit Summon Card",
        "card_th": "สปิริต ซัมมอน การ์ด",
        "card_icon": dex.icon_for("Spirit Summon Card", [], ("",)) or "/images/Spirit_summon_card.jpg",
        "npc": "Bokomon",
        "npc_th": "โบโคมอน",
        "npc_icon": dex.icon_for("Bokomon Icon", [], ("",)) or "/images/Bokomon_Icon.png",
        "npc_map_th": "ศูนย์บัญชาการ DATS",
        "money_cost": "0",
        "money_th": "",
        "money_icon": "",
        "elem": d.get("element", ""),
        "elem_th": elem_th,
    }


def _line_shot(dex, title, lines):
    """screenshot for an egg known under several line names: one whose file names a line wins"""
    first = ""
    for ln in lines:
        p = _hatch_shot(dex, title, ln)
        if p and ln and norm(ln) in norm(p.rsplit("/", 1)[-1]):
            return p
        first = first or p
    return first


def _hatch_shot(dex, title, line):
    cands = []
    if line:
        cands += [
            f"{title} ({line}) Hatch",
            f"{title} ({line}) Hatching Screen",
            f"{title} ({line}) Hatching Screenshot",
        ]
    cands += [
        f"{title} Hatch",
        f"{title} Hatching Screen",
        f"{title} hatching screen",
        f"{title} hatched",
    ]

    base = re.sub(r"\s*\(.*?\)", "", title).strip()
    if base != title:
        if line:
            cands += [f"{base} ({line}) Hatch", f"{base} ({line}) Hatching Screen"]
        cands += [f"{base} Hatch", f"{base} Hatching Screen", f"{base} hatching screen"]

    ln = (line or "").lower()
    t_lower = title.lower()

    if "veemon" in t_lower:
        if "ex" in ln:
            cands.insert(0, "ExV-mon Hatching Screen")
        elif "veedramon" in ln:
            cands.insert(0, "Veedramon Hatching Screen")
        else:
            cands.insert(0, "V-mon Jogress Hatching Screen")
            cands.append("ExV-mon Hatching Screen")
    elif "dorumon" in t_lower:
        if "alpha" in ln or "reptile" in ln:
            cands.insert(0, "Dorumon (Reptile) Hatch")
        elif "dex" in ln or "greymon" in ln:
            cands.insert(0, "Dorumon (DexDorugamon) Hatching Screen")
        else:
            cands.insert(0, "Dorumon (Dorugamon) Hatch")
            cands.append("Dorumon (Reptile) Hatch")
    elif "demidevimon" in t_lower:
        if "soul" in ln or "bake" in ln:
            cands.insert(0, "Demidevimon (Bakemon) Hatch")
        else:
            cands.insert(0, "Demidevimon (Myotismon) Hatching Screen")
            cands.append("Demidevimon (Bakemon) Hatch")
    elif "salamon" in t_lower:
        if "black" in ln or "mike" in ln:
            cands.insert(0, "Salamon (Mikemon) Hatch")
        else:
            cands.insert(0, "Salamon (Gatomon) Hatching Screen")
            cands.append("Salamon (Mikemon) Hatch")
    elif "tsukaimon" in t_lower:
        if "daemon" in ln or "murm" in ln:
            cands.insert(0, "Tsukaimon (Murmukusmon) Hatch")
        else:
            cands.insert(0, "Tsukaimon (Barbamon) Hatching Screen")
            cands.append("Tsukaimon (Murmukusmon) Hatch")
    elif "kotemon" in t_lower:
        cands.insert(0, "Kotemon (Gladimon) Hatch")
    elif "toyagumon" in t_lower or "toy agumon" in t_lower:
        cands.insert(0, "ToyAgumon Hatch")
    elif "queenchessmon" in t_lower:
        cands.insert(0, "Pawnchessmon Black Hatching Screen")
    elif "starmon" in t_lower:
        cands.insert(0, "Starmon Hatching Screen")
    elif "dorulumon" in t_lower:
        cands.insert(0, "Dorulumon NewHatch")
    elif "psychemon" in t_lower:
        cands.insert(0, "Psyche hatching screen")
    elif "raremon" in t_lower:
        cands.insert(0, "Raremon Hatch")
    elif "arkadimon" in t_lower:
        cands.insert(0, "Arkadimon Hatching Screen")
    elif "azulongmon" in t_lower:
        cands.insert(0, "Azulongmon Hatching Screen")
    elif "baihumon" in t_lower:
        cands.insert(0, "Baihumon Hatching Screen")
    elif "ebonwumon" in t_lower:
        cands.insert(0, "Ebonwumon Hatching Screen")
    elif "zhuqiaomon" in t_lower:
        cands.insert(0, "Zhuqiaomon Hatching Screen")

    for cand in cands:
        p = dex.icon_for(cand, [], ("",))
        if p:
            return p
    return ""
