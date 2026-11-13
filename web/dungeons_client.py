"""Dungeons of the Thai server, read from the (already decrypted) client in CrackDMO.

dungeon id = map id * 100 + difficulty (200101 -> map 2001 "เขาวงกตดิจิมอนแห่งความมืด")

dungeonlist.bin          u32 count | id u32, u16 ?, u16 max players, u32 len + image path, 6 bytes
dungeonqualification.bin u32 count | 20 bytes: id, ticket item, ticket count, 2 x u32
dungeonreward.bin        u32 count | id, u32 ?, u8 ?, u32 n, n x (item, count)            clear reward
dungeonobtainable.bin    u32 count | id, u32 n, n x item                                  "items you can get"
dungeonstepinfo.bin      u32 count | id, u32 stages | stage: u8 no, u32 n, n x 18 bytes (u32 key, u32, u8, u8 kind, u32 target, u32 count)
                         kind 1 = defeat monster <target> x count, kind 2 = reach area
monster.bin              u32 count | 70-byte records: id @0, level u16 @12, exp u32 @14, HP u32 @20
mapmonster.bin           u32 count | map, n, n x (monster, points, points x 16 bytes)     fixed spawns
mapnpc.bin               u32 count | map, n, n x (npc, x, y, rot)
npcinfo.bin              id, id, map, u8 type @12 ... type 0x19 = dungeon guide: n @23, dungeon ids from @31
itemcreation.bin         NPC exchange lists: npc, npc, n tabs | tab: type, type, n groups | group: g, g, n recipes |
                         recipe: id, item, count, rate (x100), cost, n mats, n x (item, count), 12 bytes
"""
import json
import re
import struct
from collections import defaultdict

FIELD_MAPS = [11, 12, 13, 89, 1201, 1202, 1203, 1204, 1205, 1206, 1307]
EXCHANGES = {}   # npc id -> every trade of that NPC (filled by build())
TIERS = [("early", "ต้นเกม", 0, 59), ("mid", "กลางเกม", 60, 109), ("late", "เลทเกม", 110, 999)]


def _clean(s):
    s = re.sub(r"@<[^>]*>|@</?\w+>", "", s or "")
    return re.sub(r"[ \t\r]+", " ", s.replace("\\n", "\n")).strip()


class Reader:
    def __init__(self, b):
        self.b, self.o = b, 0

    def u8(self):
        v = self.b[self.o]
        self.o += 1
        return v

    def u16(self):
        v = struct.unpack_from("<H", self.b, self.o)[0]
        self.o += 2
        return v

    def i32(self):
        v = struct.unpack_from("<i", self.b, self.o)[0]
        self.o += 4
        return v


def build():
    import thai_client_evo as E
    T = E.CRACK / "out_decrypted" / "data" / "bin" / "table"
    L = E.CRACK / "out_json" / "language"
    if not (T / "dungeonlist.bin").exists():
        return {"dungeons": [], "npcs": {}}
    lj = lambda n: json.loads((L / n).read_text(encoding="utf-8"))
    dstr = {x["id"]: x["fields"] for x in lj("dungeon_str.json")}
    mapname = {x["id"]: _clean(x["text"]) for x in lj("mapname_str.json")}
    monname = {x["id"]: x["fields"] for x in lj("monstername_str.json")}
    npcstr = {x["id"]: x["fields"] for x in lj("npc_str.json")}
    item_names = {x["id"]: _clean((x.get("fields") or [""])[0]) for x in lj("item_str.json")}
    its = E.items()

    def item(iid, count=1):
        it = its.get(iid)
        ok = E.save_icon(iid, it.get("icon_id") if it else None)
        return {"id": iid, "name": item_names.get(iid) or "ไอเทม", "count": count,
                "icon": f"/images/client_items/{iid}.png" if ok else ""}

    # ---- monsters (level / HP) --------------------------------------------------------------
    b = (T / "monster.bin").read_bytes()
    mon = {}
    for i in range(struct.unpack_from("<i", b, 0)[0]):
        o = 4 + i * 70
        mid = struct.unpack_from("<i", b, o)[0]
        mon[mid] = {"level": struct.unpack_from("<H", b, o + 12)[0], "exp": struct.unpack_from("<I", b, o + 14)[0],
                    "hp": struct.unpack_from("<I", b, o + 20)[0], "model": struct.unpack_from("<i", b, o + 8)[0]}

    from thai_client_apply import ClientEvo
    _pics = {}

    def pic(model):
        if model and model not in _pics:
            _pics[model] = ClientEvo.client_picture(model)
        return _pics.get(model, "")

    # monsters whose model has no picture file (boss-only models): use a client Digimon with the same name
    def loose(s):
        s = re.sub(r"\s+|ดิจิมอนใหม่", "", s or "")
        return re.sub(r"[่้๊๋์]", "", s).replace("ร", "ล")      # tone marks, ร/ล spellings
    _by_name = {}
    for cid, nm in E.digimon_names().items():
        _by_name.setdefault(loose(nm), []).append(cid)

    def pic_by_name(name):
        for cid in sorted(_by_name.get(loose(name), []), reverse=True):
            u = pic(cid)
            if u:
                return u
        return ""

    def monster(mid, count=0):
        f = monname.get(mid) or ["", ""]
        m = mon.get(mid, {})
        mname = _clean(f[0]) or ""
        if mname.startswith("กำจัดวาจิร"):
            mname = "วาจิรามอน"
        return {"id": mid, "name": mname, "title": _clean(f[1]).strip("<>") if len(f) > 1 else "",
                "level": m.get("level", 0), "hp": m.get("hp", 0), "count": count, "model": m.get("model", 0),
                "icon": pic(m.get("model", 0)) or pic_by_name(mname)}

    # ---- map spawns ----------------------------------------------------------------------
    r = Reader((T / "mapmonster.bin").read_bytes())
    spawns = {}
    for _ in range(r.i32()):
        mp, n = r.i32(), r.i32()
        g = []
        for _ in range(n):
            m, c = r.i32(), r.i32()
            r.o += 16 * c
            g.append((m, c))
        spawns[mp] = g

    # ---- NPC positions + dungeon guides ------------------------------------------------------
    r = Reader((T / "mapnpc.bin").read_bytes())
    npc_map = {}
    for _ in range(r.i32()):
        mp, n = r.i32(), r.i32()
        for _ in range(n):
            nid, x, y = r.i32(), r.i32(), r.i32()
            r.o += 4
            npc_map.setdefault(nid, (mp, x, y))
    nb = (T / "npcinfo.bin").read_bytes()
    guides = defaultdict(list)                     # dungeon id -> [npc ids]
    for nid in npcstr:
        key = struct.pack("<ii", nid, nid)
        i = nb.find(key)
        while i >= 0:
            if nb[i + 12] == 0x19:
                n = struct.unpack_from("<i", nb, i + 23)[0]
                if 0 < n < 60:
                    for k in range(n):
                        guides[struct.unpack_from("<i", nb, i + 31 + 4 * k)[0]].append(nid)
                break
            i = nb.find(key, i + 1)

    # NPC pictures: out_images/data/npc/<name>/0<model 6 digits>_<name>l.png; the model id sits at +19 of the
    # npcinfo record (the NPC itself, or a Digimon id -> the Digimon's own picture)
    import shutil
    npc_pics = {}
    root = E.CRACK / "out_images" / "data" / "npc"
    if root.exists():
        for f in sorted(root.glob("*/*.png")):
            m = re.match(r"0(\d{6})_.*l\.png$", f.name, re.I)
            if m:
                npc_pics.setdefault(int(m.group(1)), f)
    pic_out = E.ICON_OUT.parent / "client_npc"
    pic_out.mkdir(parents=True, exist_ok=True)
    npc_icon_cache = {}

    def npc_icon(nid):
        if nid in npc_icon_cache:
            return npc_icon_cache[nid]
        model = 0
        i = nb.find(struct.pack("<ii", nid, nid))
        if i >= 0 and i + 23 <= len(nb):
            model = struct.unpack_from("<i", nb, i + 19)[0]
        # the model the NPC record points at wins: the Thai server reuses NPC ids, so the picture filed under
        # the NPC id can be an old NPC (90080 = Guilmon guide, but npc/elecmon/0090080_*.png is Elecmon)
        url = ""
        src = npc_pics.get(model) if model and model != nid else None
        if not src and model and model != nid:
            url = pic(model)            # a Digimon model (Guilmon guide -> Digimon 31005)
        if not url:
            src = src or npc_pics.get(nid)
            if src:
                dest = pic_out / f"{nid}.png"
                if not dest.exists() or dest.stat().st_size != src.stat().st_size:
                    shutil.copyfile(src, dest)
                url = f"/images/client_npc/{nid}.png"
        npc_icon_cache[nid] = url
        return url

    def npc(nid):
        f = npcstr.get(nid) or ["", ""]
        mp = npc_map.get(nid)
        return {"id": nid, "name": _clean(f[1]) if len(f) > 1 else "", "title": _clean(f[0]).strip("<>"),
                "map": mapname.get(mp[0], "") if mp else "", "map_id": mp[0] if mp else 0, "icon": npc_icon(nid)}

    # ---- NPC exchange lists ----------------------------------------------------------------
    r = Reader((T / "itemcreation.bin").read_bytes())
    exchange = {}
    for _ in range(r.i32()):
        nid = r.i32()
        r.i32()
        recs = []
        for _ in range(r.i32()):
            r.i32(), r.i32()
            for _ in range(r.i32()):
                r.i32(), r.i32()
                for _ in range(r.i32()):
                    _rid, it_, cnt, rate, cost, nm = (r.i32() for _ in range(6))
                    mats = [(r.i32(), r.i32()) for _ in range(nm)]
                    r.o += 12
                    recs.append({"item": it_, "count": cnt, "rate": rate / 100, "cost": cost, "mats": mats})
        exchange[nid] = recs

    # ---- dungeon tables ---------------------------------------------------------------------
    r = Reader((T / "dungeonlist.bin").read_bytes())
    dlist = {}
    for _ in range(r.i32()):
        did, _a, players = r.i32(), r.u16(), r.u16()
        ln = r.i32()
        r.o += ln + 6
        dlist[did] = {"players": players}
    r = Reader((T / "dungeonqualification.bin").read_bytes())
    ticket = {}
    for _ in range(r.i32()):
        did, iid, cnt, _x, _y = (r.i32() for _ in range(5))
        if iid:
            ticket[did] = (iid, cnt)
    r = Reader((T / "dungeonreward.bin").read_bytes())
    reward = defaultdict(list)
    for _ in range(r.i32()):
        did, _a, _b, n = r.i32(), r.i32(), r.u8(), r.i32()
        reward[did] += [(r.i32(), r.i32()) for _ in range(n)]
    r = Reader((T / "dungeonobtainable.bin").read_bytes())
    obtain = {}
    for _ in range(r.i32()):
        did, n = r.i32(), r.i32()
        obtain[did] = [r.i32() for _ in range(n)]
    r = Reader((T / "dungeonstepinfo.bin").read_bytes())
    steps = {}
    for _ in range(r.i32()):
        did, n = r.i32(), r.i32()
        st = []
        for _ in range(n):                 # stage: u8 number, u32 n, n x 18-byte goals
            no, k = r.u8(), r.i32()
            for _ in range(k):
                _key, _b, _c, kind, target, cnt = r.i32(), r.i32(), r.u8(), r.u8(), r.i32(), r.i32()
                st.append({"no": no, "kind": kind, "target": target, "count": cnt})
        steps[did] = st

    # ---- quests that send you to kill these monsters ------------------------------------------
    import thai_client_quest as Q
    qstr, qrec = Q.load_quest_str(), Q.load_quests()
    by_mon = defaultdict(list)
    for qid, rec in qrec.items():
        if qid not in qstr:
            continue
        for o in rec["obj"]:
            if o["type"] == 0:
                by_mon[o["target"]].append(qid)

    def quest(qid):
        s, rec = qstr[qid], qrec[qid]
        rew = []
        for w in rec["rew"]:
            if w["type"] == 2:
                rew.append(item(w["value"], w["count"] or 1))
            elif w["type"] == 0 and w["value"]:
                rew.append({"exp": w["value"]})
            elif w["type"] == 1 and w["value"]:
                rew.append({"money": w["value"]})
        objs = [monster(o["target"], o["count"]) for o in rec["obj"] if o["type"] == 0]
        st = rec.get("start_npc") or 0
        return {"id": qid, "title": _clean(s[1]), "line": _clean(s[0]), "objective": _clean(s[3]),
                "start_npc": npc(st) if st in npcstr else None, "level": rec.get("level", 0),
                "defeat": objs, "rewards": rew}

    # ---- assemble -----------------------------------------------------------------------------
    def make(key, name, desc, map_id, mons_ids, did=None):
        mons = {}
        for mid, cnt, src in mons_ids:
            if mid not in monname:
                continue
            m = mons.setdefault(mid, {**monster(mid), "count": 0, "boss": False})
            m["count"] = max(m["count"], cnt)
        lst = sorted(mons.values(), key=lambda m: (m["level"], m["hp"]))
        if lst:
            # Pick boss intelligently:
            chosen = None
            if did in (41101, 41201):  # พื้นที่ของไกเซอร์ (Kaiser Territory)
                chosen = next((m for m in mons.values() if "วารุมอนซาเอมอน" in m["name"]), None)
            elif "นาโนมอน" in name:  # ทางวงกตของนาโนมอน (Datamon Maze)
                chosen = next((m for m in mons.values() if "นาโนมอน" in m["name"]), None)

            if not chosen:
                name_matches = [m for m in mons.values() if m["name"] and (m["name"] in name or name in m["name"])]
                if name_matches:
                    chosen = max(name_matches, key=lambda m: (m["level"], m["hp"]))
            if not chosen:
                st = [s for s in steps.get(did, []) if s.get("kind") == 1]
                if st:
                    max_stage = max(s["no"] for s in st)
                    final_targets = [s["target"] for s in st if s["no"] == max_stage]
                    final_mobs = [mons[tid] for tid in final_targets if tid in mons]
                    if final_mobs:
                        chosen = max(final_mobs, key=lambda m: (m["level"], m["hp"]))
            if not chosen:
                chosen = max(lst, key=lambda m: (m["level"], m["hp"]))
            if chosen:
                chosen["boss"] = True
        mon_ids = set(mons)
        names = {m["name"] for m in lst}
        quests = []
        for mid in mon_ids:
            for qid in by_mon.get(mid, []):
                if qid not in [q["id"] for q in quests]:
                    q = quest(qid)
                    if q["rewards"]:
                        quests.append(q)
        quests.sort(key=lambda q: q["id"])

        # Exchange NPCs: only those trading actual exclusive dungeon materials (exclude generic materials)
        GENERIC_MATS = (
            'หินเปลี่ยนค่าออฟชั่น', 'เครื่องปรับแต่งค่าออฟชั่น', 'หินปรับค่าออฟชั่น',
            'กล่องชิปเซ็ท', 'กล่องอัพเกรดชิพ', 'ชิปเซ็ท', 'ชิปก้าวข้ามขีดจำกัด',
            'กล้วย', 'ชุดไก่', 'EP', 'เหรียญแลกเปลี่ยนชิป', 'ดิจิคอร์',
            'เมมโมรี่ชิป', 'เมมโมรีสกิล', 'บัตรผ่าน', 'ตั๋ว', 'การ์ดคริสมาสต์',
            'ดิจิทามะ', 'แบคอัพ', 'แบ็คอัพ', 'คริสตัลวิวัฒนาการ', 'แก่นแท้ของวิวัฒนาการ',
            'ชิ้นส่วน X - แอนติบอดี้ - ดาต้า', 'พลังงานลบ :', 'ชิ้นส่วนดิจิโค๊ด'
        )
        loot = {i for i in set(obtain.get(did, [])) | {i for i, _ in reward.get(did, [])} if loot_count[i] <= 4}
        exch = []
        for nid, recs in exchange.items():
            if nid in (91054, 90289) and did not in (40101, 40201, 40701):
                continue
            if nid in (10037, 94086, 93114) and did in (21001, 21101, 161401, 170101, 170401, 131201):
                continue
            hits = []
            for i, x in enumerate(recs):
                target_nm = (item_names.get(x["item"]) or "").lower()
                if any(k in target_nm for k in ['บัตรผ่าน', 'ตั๋ว', 'กล้วย', 'กล่องชิปเซ็ท']):
                    continue
                has_dungeon_loot = False
                for m, _ in x["mats"]:
                    if m in loot:
                        mnm = item_names.get(m, "")
                        if not any(bad in mnm for bad in GENERIC_MATS):
                            has_dungeon_loot = True
                            break
                if has_dungeon_loot:
                    hits.append(i)
            if hits:
                if nid not in EXCHANGES:
                    EXCHANGES[nid] = [{"item": item(x["item"], x["count"]), "rate": x["rate"], "cost": x["cost"],
                                       "mats": [item(m, c) for m, c in x["mats"]]} for x in recs]
                exch.append({**npc(nid), "trade_ids": hits, "total": len(hits),
                             "preview": [EXCHANGES[nid][i] for i in hits[:3]]})
        m = re.search(r"เลเวล(?:ดิจิมอน)?ที่เหมาะสม\s*:\s*(\d+)", desc or "")
        lv = sorted(x["level"] for x in lst if x["level"])
        level = lv[len(lv) // 2] if lv else (int(m.group(1)) if m else 0)   # median monster level
        tier = next(t for t in TIERS if t[2] <= level <= t[3])
        return {
            "key": str(key), "id": did, "name": name, "map_id": map_id, "map": mapname.get(map_id, ""),
            "desc": desc, "instance": did is not None, "players": dlist.get(did, {}).get("players", 0) if did else 0,
            "level": level, "tier": tier[0], "tier_th": tier[1],
            "level_range": [lv[0], lv[-1]] if lv else [], "level_hint": int(m.group(1)) if m else 0,
            "entry_npcs": [npc(n) for n in dict.fromkeys(guides.get(did, []))] if did else [],
            "ticket": item(*ticket[did]) if did in ticket else None,
            "monsters": lst, "steps": steps.get(did, []),
            "obtainable": [item(i) for i in obtain.get(did, [])],
            "clear_reward": [item(i, c) for i, c in reward.get(did, [])],
            "quests": quests, "exchange_npcs": exch,
        }

    loot_count = defaultdict(int)
    for did in dstr:
        for i in set(obtain.get(did, [])) | {i for i, _ in reward.get(did, [])}:
            loot_count[i] += 1
    out = []
    for did, f in dstr.items():
        name = _clean(f[0])
        if not name or name in ("???",):
            continue
        mp = did // 100
        st = steps.get(did, [])
        ids = [(s["target"], s["count"], "step") for s in st if s["kind"] == 1]
        ids += [(m, c, "spawn") for m, c in spawns.get(mp, [])]
        desc = _clean(f[1]) if len(f) > 1 else ""
        if re.search(r"[가-힣]", desc):      # untranslated Korean notes
            desc = ""
        out.append(make(did, name, desc, mp, ids, did))
    for mp in FIELD_MAPS:
        if mp in mapname and spawns.get(mp):
            out.append(make(f"map{mp}", mapname[mp], "", mp, [(m, c, "spawn") for m, c in spawns[mp]]))
    # same name more than once ("ดันเจี้ยนมังกร" x3): tell them apart
    # Thai server wording: the description ("[ระดับง่าย]"), else the (Easy)/(Normal)/(Hard) the game puts in
    # the names of the quests only that copy has; one copy left over takes the remaining level. No clue -> no label.
    from collections import Counter
    LV = {"easy": "ระดับง่าย", "normal": "ระดับธรรมดา", "hard": "ระดับยาก"}

    def quest_levels(d):
        return {LV[x.lower()] for q in d["quests"] for x in re.findall(r"(?i)[(\[]\s*(easy|normal|hard)\s*[)\]]", q["title"])}

    groups = defaultdict(list)
    for d in out:
        groups[d["name"]].append(d)
    for name, same in groups.items():
        if len(same) < 2:
            continue
        found = {}
        for d in same:
            m = re.search(r"\[(ระดับ[^\]]+)\]|\((ระดับ[^)]+)\)", d["desc"])
            if m:
                found[id(d)] = m.group(1) or m.group(2)
        if len(found) < len(same):
            levels = {id(d): quest_levels(d) for d in same}
            for d in same:
                if id(d) in found:
                    continue
                others = set().union(*(levels[id(o)] for o in same if o is not d))
                own = levels[id(d)] - others
                if len(own) == 1:
                    found[id(d)] = own.pop()
            left = [d for d in same if id(d) not in found]
            used = set(found.values())
            pool = [v for v in LV.values() if v not in used]
            if len(left) == 1 and found and len(pool) >= 1:
                # the copy with no own label: the level its siblings do not use (lowest first)
                order = [v for v in LV.values() if v in pool]
                found[id(left[0])] = order[0]
        for d in same:
            if id(d) in found:
                d["variant"] = found[id(d)]
    for d in out:
        for st in d["steps"]:
            st["monster"] = monster(st["target"]) if st["kind"] == 1 else None
    seen_slugs = set()
    for d in out:
        raw_name = f"{d['name']}-{d['variant']}" if d.get("variant") else d["name"]
        base = re.sub(r"[\s/\\?#%&]+", "-", raw_name).strip("-") or str(d["key"])
        slug = base
        if slug in seen_slugs:
            n = 2
            while f"{base}-{n}" in seen_slugs:
                n += 1
            slug = f"{base}-{n}"
        seen_slugs.add(slug)
        d["slug"] = slug
    out.sort(key=lambda d: (d["level"], d["name"]))
    return out
