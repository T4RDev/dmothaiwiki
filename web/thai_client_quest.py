"""Jogress quests from the (already decrypted) Thai client in CrackDMO.

    python web/thai_client_quest.py      -> web/thai_jogress_quests.json

quest_str.bin  : u32 count, then per quest u32 id + 8 strings (u32 length + UTF-16LE)
                 [0] quest-line name, [1] title, [2] story, [3] objective, [4] tracker, [5] in-progress, [6] done, [7] -
quest.bin      : u32 count, then per quest  u32 id | u32 id | header ... u16 tamer level @16 ... u32 start NPC, u32 end NPC
                 | u32 n_pre  + n_pre * 9  (u8 type, u32 value, u32 extra)      0 = previous quest, 3 = level, 4 = Digimon
                 | u32 n_obj  + n_obj * 21 (u8 type, u32 target, u32 count, ..)  0 = have Digimon, 1 = defeat, 2 = item, 4 = talk
                 | u32 n_rew  + n_rew * 10 (u8, u8 type, u32 value, u32 count)    2 = item
"""
import bisect
import json
import re
import struct
from pathlib import Path

CRACK = Path(r"C:\Users\T4R\Desktop\AllWorks\CrackDMO")
HERE = Path(__file__).resolve().parent
OUT = HERE / "thai_jogress_quests.json"


def load_quest_str():
    b = (CRACK / "out_decrypted/data/bin/language/thailand/quest_str.bin").read_bytes()
    n, o, out = struct.unpack_from("<i", b, 0)[0], 4, {}
    for _ in range(n):
        qid = struct.unpack_from("<i", b, o)[0]
        o += 4
        strs = []
        for _ in range(8):
            ln = struct.unpack_from("<i", b, o)[0]
            o += 4
            strs.append(b[o:o + 2 * ln].decode("utf-16le", "replace"))
            o += 2 * ln
        out[qid] = strs
    return out


def parse_record(blk):
    for h in range(28, 60):
        o = h
        try:
            secs = []
            for size in (9, 21, 10):
                n = struct.unpack_from("<i", blk, o)[0]
                if not 0 <= n <= 30:
                    raise ValueError
                o += 4
                secs.append([blk[o + i * size:o + (i + 1) * size] for i in range(n)])
                o += n * size
            if o != len(blk):
                continue
        except (ValueError, struct.error):
            continue
        pre = [{"type": e[0], "value": struct.unpack_from("<i", e, 1)[0]} for e in secs[0]]
        obj = [{"type": e[0], "target": struct.unpack_from("<i", e, 1)[0], "count": struct.unpack_from("<i", e, 5)[0]}
               for e in secs[1]]
        rew = [{"type": e[1], "value": struct.unpack_from("<i", e, 2)[0], "count": struct.unpack_from("<i", e, 6)[0]}
               for e in secs[2]]
        return {"level": struct.unpack_from("<H", blk, 16)[0] if h > 18 else 0,
                "start_npc": struct.unpack_from("<i", blk, h - 13)[0], "end_npc": struct.unpack_from("<i", blk, h - 8)[0],
                "pre": pre, "obj": obj, "rew": rew}
    return None


def _sections(b, o):
    """parse the three sections starting at o -> (parsed, end) or None"""
    secs = []
    for size in (9, 21, 10):
        if o + 4 > len(b):
            return None
        n = struct.unpack_from("<i", b, o)[0]
        if not 0 <= n <= 30:
            return None
        o += 4
        secs.append([b[o + i * size:o + (i + 1) * size] for i in range(n)])
        o += n * size
    return secs, o


def _record_end_ok(b, end):
    return end == len(b) or (end + 8 <= len(b) and b[end:end + 4] == b[end + 4:end + 8]
                              and 0 < struct.unpack_from("<i", b, end)[0] < 100000)


def load_quests(ids=None):
    """Walk quest.bin record by record.

    header (36 + 9*n bytes): u32 id | u32 id | ... u16 tamer level @16 ... u8 @21 | u8 has start NPC @22
                             | u32 start NPC @23 | u32 end NPC @28 | u32 n @32 | n * 9 supply items given when the
                             quest is accepted (u8 type, u32 item, u32 count)
    then the three sections (prerequisites, objectives, rewards).
    """
    b = (CRACK / "out_decrypted/data/bin/table/quest.bin").read_bytes()
    count = struct.unpack_from("<i", b, 0)[0]
    out, p = {}, 4
    for _ in range(count):
        if p + 36 > len(b):
            break
        qid = struct.unpack_from("<i", b, p)[0]
        n_sup = struct.unpack_from("<i", b, p + 32)[0]
        hit = None
        guesses = ([36 + 9 * n_sup] if 0 <= n_sup <= 10 else []) + list(range(28, 80))
        for h in guesses:
            r = _sections(b, p + h)
            if r and _record_end_ok(b, r[1]):
                hit = (h, *r)
                break
        if not hit:
            break
        h, secs, end = hit
        sup = []
        if h >= 36:
            for i in range(min(max(n_sup, 0), (h - 36) // 9)):
                o = p + 36 + i * 9
                sup.append({"type": b[o], "item": struct.unpack_from("<i", b, o + 1)[0],
                            "count": struct.unpack_from("<i", b, o + 5)[0]})
        rec = {
            "level": struct.unpack_from("<H", b, p + 16)[0],
            "start_npc": struct.unpack_from("<i", b, p + 23)[0] if h >= 32 else 0,
            "end_npc": struct.unpack_from("<i", b, p + 28)[0] if h >= 32 else 0,
            "supply": sup,
            "pre": [{"type": e[0], "value": struct.unpack_from("<i", e, 1)[0]} for e in secs[0]],
            "obj": [{"type": e[0], "target": struct.unpack_from("<i", e, 1)[0], "count": struct.unpack_from("<i", e, 5)[0]}
                    for e in secs[1]],
            "rew": [{"type": e[1], "value": struct.unpack_from("<i", e, 2)[0], "count": struct.unpack_from("<i", e, 6)[0]}
                    for e in secs[2]],
        }
        if ids is None or qid in ids:
            out[qid] = rec
        p = end
    return out


def evolution_slots():
    """(base Digimon, slot) -> Digimon in that slot, and quest id -> Digimon whose slot that quest opens."""
    import thai_client_evo as E
    names = E.digimon_names()
    slots, opens = {}, {}
    for ln in E.parse_lines(set(names)):
        slots.setdefault((ln["parent"], ln["slot"]), ln["type"])
        slots.setdefault((ln["parent"], 1), ln["parent"])
        if ln["quest"]:
            opens.setdefault(ln["quest"], ln["type"])
    return slots, opens


JOG = re.compile(r"โจเกรส|jogress|jogrss|jogres|quset", re.I)


def _clean(s):
    s = re.sub(r"%q[se]|%c[cm]\d*|%mc\d*|@<[^>]*>|%\w+", "", s or "")
    s = re.sub(r"[ \t]+", " ", s.replace("\r", ""))
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def _dn(s):
    return re.sub(r"\s+", " ", re.sub(r"ดิจิมอนใหม่", "", s or "")).strip()


def _obj_summary(o):
    if o["kind"] == "defeat":
        return f"กำจัด{o['target']} ×{o['count']}"
    if o["kind"] == "collect":
        return f"รวบรวม{o['target']}" + (f" ×{o['count']}" if o.get("count", 1) > 1 else "")
    if o["kind"] == "talk":
        return f"คุยกับ{o['target']}"
    return o.get("target") or ""


def build():
    import thai_client_evo as E
    strs = load_quest_str()
    recs = load_quests()
    names = E.digimon_names()
    its = E.items()
    lang = CRACK / "out_json" / "language"
    npc = {x["id"]: x["fields"] for x in json.loads((lang / "npc_str.json").read_text(encoding="utf-8"))}
    mon = {x["id"]: x["fields"][0] for x in json.loads((lang / "monstername_str.json").read_text(encoding="utf-8"))}
    evo = json.loads(E.OUT.read_text(encoding="utf-8")) if E.OUT.exists() else {}
    item_names = {x["id"]: (x.get("fields") or [""])[0] for x in json.loads((lang / "item_str.json").read_text(encoding="utf-8"))}
    slots, slot_quest = evolution_slots()
    # unlock item id -> Digimon (client ids) it opens
    item_to_digi = {}
    for cid, r in evo.items():
        for x in (r.get("items") or []) + ([{"item": r["item"]}] if r.get("item") else []):
            item_to_digi.setdefault(x["item"]["id"], set()).add(int(cid))

    def item(iid, count=1):
        it = its.get(iid)
        if not it:  # quest items are named in item_str but missing from itemdata
            nm = re.sub(r"\s+", " ", item_names.get(iid, "")).strip()
            ok = E.save_icon(iid, None) if nm else False
            return {"id": iid, "name_th": nm or f"ไอเทม #{iid}", "icon": f"/images/client_items/{iid}.png" if ok else "",
                    "count": count, "unlocks": sorted(item_to_digi.get(iid, []))}
        ok = E.save_icon(iid, it.get("icon_id"))
        return {"id": iid, "name_th": re.sub(r"\s+", " ", it["name"]).strip(), "icon": f"/images/client_items/{iid}.png" if ok else "",
                "count": count, "unlocks": sorted(item_to_digi.get(iid, []))}

    def npc_of(i):
        f = npc.get(i)
        return {"id": i, "name": f[1], "title": f[0].strip("<>")} if f else None

    def digi(i):
        return {"client_id": i, "name_th": re.sub(r"ดิจิมอนใหม่\s*", "", names.get(i, "")).strip()} if i in names else None

    # quest lines that hand out an unlock item of a Jogress Digimon (one item per partner) count too,
    # even when the line is not named "โจเกรส" (e.g. "ราเฟลเรซีมอน", "[เควสคาออสมอน]")
    jog_items = {iid for iid, ds in item_to_digi.items()
                 if any(len(evo[str(c)].get("items") or []) > 1 for c in ds if str(c) in evo)}
    extra_cats = {strs[q][0].strip() for q, r in recs.items() if q in strs
                  and any(w["type"] == 2 and w["value"] in jog_items for w in r["rew"])}
    lines, seen_sig = {}, set()
    for qid, s in strs.items():
        if qid not in recs or not (JOG.search(s[0] + " " + s[1]) or s[0].strip() in extra_cats):
            continue
        r = recs[qid]
        cat = s[0].strip() or "<โจเกรส>"
        pre = {}
        for p in r["pre"]:
            pre.setdefault(p["type"], []).append(p["value"])
        # the tracker text names every objective in order: "%qs1ดิจิคอร์[จินลอนมอน]%qe %cc1/%mc1 %qs2..."
        labels = [_clean(x) for x in re.findall(r"%qs\d+(.*?)%qe", s[4] or "")]
        objectives = []
        for i, o in enumerate(r["obj"]):
            lab = labels[i] if i < len(labels) else ""
            if o["type"] == 0:
                objectives.append({"kind": "defeat", "target": mon.get(o["target"], lab or f"มอนสเตอร์ #{o['target']}"),
                                   "count": o["count"]})
            elif o["type"] == 1:
                it = item(o["target"], o["count"]) if (o["target"] in its or o["target"] in item_names) else None
                objectives.append({"kind": "collect", "target": re.sub(r"^(รวบรวม|ครอบครอง)\s*", "", lab) or
                                   (it or {}).get("name_th", f"ไอเทม #{o['target']}"), "count": o["count"],
                                   "icon": (it or {}).get("icon", "")})
            elif o["type"] == 4:
                n = npc_of(o["target"])
                objectives.append({"kind": "talk", "target": n["name"] if n else (lab or f"NPC #{o['target']}"),
                                   "title": n["title"] if n else ""})
            elif o["type"] == 8 and o["target"] in item_names:  # use a quest item at a spot
                it = item(o["target"], o["count"])
                objectives.append({"kind": "other", "target": lab or (_clean(s[4]) if len(r["obj"]) == 1 else "")
                                   or f"ใช้{it['name_th']}", "count": o["count"], "icon": it.get("icon", "")})
            elif o["type"] == 2 and o["count"] in item_names:  # finish the Jogress -> title item
                objectives.append({"kind": "other", "target": lab or f"โจเกรสสำเร็จ (ได้รับ {item(o['count'])['name_th']})",
                                   "count": 1})
            else:
                objectives.append({"kind": "other", "target": lab or (_clean(s[4]) if len(r["obj"]) == 1 else "")
                                   or f"เงื่อนไข #{o['type']}", "count": o["count"]})
        rewards = []
        for w in r["rew"]:
            if w["type"] == 2:
                same = next((x for x in rewards if x["kind"] == "item" and x["item"]["id"] == w["value"]), None)
                if same:  # the same item listed twice = more of it
                    same["item"]["count"] += w["count"] or 1
                    continue
                rewards.append({"kind": "item", "item": item(w["value"], w["count"] or 1)})
            elif w["type"] == 0 and w["value"]:
                rewards.append({"kind": "exp", "value": w["value"]})
            elif w["type"] == 1 and w["value"]:
                rewards.append({"kind": "money", "value": w["value"]})
        title, objective_text = _clean(s[1]), _clean(s[3])
        tag_title = bool(re.fullmatch(r"<[^<>]*>|\[[^\[\]]*\]", title)) or title == cat
        if objective_text == title:
            objective_text = ""
        if tag_title or not title:  # "<โอเมกามอน-อากูมอน 1>" is only a tag: name it after what it asks for
            title = " / ".join(_obj_summary(o) for o in objectives) or title
        need_ids = pre.get(4, []) + pre.get(8, [])
        forms = []
        for slot in pre.get(6, []):  # the partner must currently be in this evolution slot
            for d in need_ids or [None]:
                f = slots.get((d, slot)) if d else None
                forms.append({"slot": slot, "client_id": f, "name_th": _dn(names.get(f, "")) if f else ""})
        opens = []
        for slot in pre.get(7, []):  # the Jogress slot this quest line opens
            for d in need_ids:
                f = slots.get((d, slot))
                if f:
                    opens.append({"client_id": f, "name_th": _dn(names.get(f, ""))})
        if qid in slot_quest:
            f = slot_quest[qid]
            if not any(o["client_id"] == f for o in opens):
                opens.append({"client_id": f, "name_th": _dn(names.get(f, ""))})
        q = {
            "id": qid, "title": title, "tag": _clean(s[1]) if tag_title else "", "story": _clean(s[2]),
            "objective": objective_text,
            "done_text": _clean(s[6]),
            "start_npc": npc_of(r["start_npc"]), "end_npc": npc_of(r["end_npc"]),
            "prev": pre.get(0, []), "tamer_level": max(pre.get(1, [0])), "digimon_level": max(pre.get(3, [0])),
            "need_digimon": [d for d in (digi(x) for x in need_ids) if d],
            "need_form": [f for f in forms if f["name_th"]],
            "need_items": [item(x) for x in pre.get(2, [])],
            "opens": opens,
            "supply": [item(x["item"], x["count"] or 1) for x in r.get("supply", []) if x["item"]],
            "auto_start": not r["start_npc"],
            "objectives": objectives, "rewards": rewards,
        }
        sig = (cat, q["title"], tuple(need_ids), json.dumps(q["objectives"], ensure_ascii=False),
               json.dumps(q["rewards"], ensure_ascii=False))
        if sig in seen_sig:  # the client keeps old + new copies of some quests
            continue
        seen_sig.add(sig)
        lines.setdefault(cat, []).append(q)

    out = []
    for cat, qs in lines.items():
        qs.sort(key=lambda q: q["id"])
        targets = set()
        for q in qs:
            for w in q["rewards"]:
                if w["kind"] == "item":
                    targets |= set(w["item"].get("unlocks") or [])
        # quest-line name "โจเกรส[มิลเลนเนียมมอน]" / "<โจเกรส - เอ็กซามอน 2>" / "เควสโจเกรส(ชิลฟีมอน)"
        m = re.search(r"[\[(]\s*(.+?)\s*[\])]|[-–]\s*([^>\d]+?)\s*\d*>?$", cat)
        named = (m.group(1) or m.group(2) or "").strip() if m else ""
        named = re.sub(r"^โจเกรส\s*", "", named)
        name_hits = [cid for cid, n in names.items()
                     if named and re.sub(r"\s", "", n.replace("ดิจิมอนใหม่", "")) == re.sub(r"\s", "", named)]
        out.append({"line": cat, "named": named, "targets": sorted(targets), "named_ids": name_hits,
                    "quests": qs, "start_level": min((q["tamer_level"] or q["digimon_level"] or 0) for q in qs)})
    out.sort(key=lambda x: (x["named"] or x["line"]))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[quest] {len(out)} jogress quest lines, {sum(len(x['quests']) for x in out)} quests -> {OUT.name}")
    return out


if __name__ == "__main__":
    build()
