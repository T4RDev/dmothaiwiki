"""Evolution unlock items from the (already decrypted) Thai client tables in CrackDMO.

    python web/thai_client_evo.py            # writes web/thai_evo_unlock.json + copies item icons

Sources (made by the user's own tools, read-only here):
    CrackDMO/out_decrypted/data/bin/table/devolutionlist.bin   evolution slots (who evolves into what, level, unlock item)
    CrackDMO/out_decrypted/data/bin/table/itemdata.bin         item -> section (item category) + icon
    CrackDMO/out_json/language/item_str.json                   item Thai names
    CrackDMO/out_json/language/digimonname_str.json            Digimon Thai names (type id -> name)
    CrackDMO/out_item_icons/<item_id>.png                      item icons
"""
import json
import re
import shutil
import struct
from pathlib import Path

CRACK = Path(r"C:\Users\T4R\Desktop\AllWorks\CrackDMO")
HERE = Path(__file__).resolve().parent
OUT = HERE / "thai_evo_unlock.json"
ICON_OUT = HERE.parent / "output" / "images" / "client_items"


def u16(b, i):
    return struct.unpack_from("<H", b, i)[0]


def u32(b, i):
    return struct.unpack_from("<i", b, i)[0]


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def digimon_names():
    return {x["id"]: x["text"] for x in load_json(CRACK / "out_json/language/digimonname_str.json")}


def items():
    """item_id -> {name, kind, desc, section, icon}"""
    names = {}
    for x in load_json(CRACK / "out_json/language/item_str.json"):
        f = x.get("fields") or []
        names[x["id"]] = {"name": f[0] if f else "", "kind": f[1] if len(f) > 1 else "", "desc": f[2] if len(f) > 2 else ""}
    b = (CRACK / "out_decrypted/data/bin/table/itemdata.bin").read_bytes()
    # one pass: every record starts with the item id written twice
    first = {}
    for m in re.finditer(rb"(?s)(?=(.{4})\1)", b):
        v = struct.unpack_from("<i", b, m.start())[0]
        if v in names and v not in first:
            first[v] = m.start()
    out = {}
    for iid, i in first.items():
        out[iid] = {**names[iid], "section": u32(b, i + 28), "icon_id": u32(b, i + 8)}
    return out


def parse_lines(valid):
    """Scan devolutionlist.bin for evolution-slot headers:
       u16 slot | u32 type | u16 slot_level | u32 n | n * (u32 stage, u32 target) |
       u16 a | u16 b | u32 parent | u16 c | u8 d | u16 unlock_level | u32 quest | u32 item_section | u16 amount
    """
    b = (CRACK / "out_decrypted/data/bin/table/devolutionlist.bin").read_bytes()
    lines = []
    i = 4
    end = len(b) - 40
    while i < end:
        slot, typ, lvl, n = u16(b, i), u32(b, i + 2), u16(b, i + 6), u32(b, i + 8)
        if 1 <= slot <= 20 and typ in valid and 0 <= n <= 12 and 1 <= lvl <= 20:
            j = i + 12
            ok = True
            targets = []
            for _ in range(n):
                st, tg = u32(b, j), u32(b, j + 4)
                if tg not in valid or not 0 <= st <= 30:
                    ok = False
                    break
                targets.append(tg)
                j += 8
            if ok:
                parent = u32(b, j + 4)
                if parent in valid or parent == typ:
                    lines.append({
                        "offset": i, "slot": slot, "type": typ, "slot_level": lvl, "to": targets, "parent": parent,
                        "unlock_level": u16(b, j + 11), "quest": u32(b, j + 13),
                        "item_section": u32(b, j + 17), "amount": u16(b, j + 21),
                    })
                    i = j + 24
                    continue
        i += 1
    return lines


_ATLAS = {}


def save_icon(iid, icon_id):
    """Copy the pre-sliced icon, or cut it from the client's icon atlas (32 px cells)."""
    dest = ICON_OUT / f"{iid}.png"
    if dest.exists() and dest.stat().st_size:
        return True
    src = CRACK / "out_item_icons" / f"{iid}.png"
    if src.exists():
        shutil.copyfile(src, dest)
        return True
    if not icon_id:
        return False
    try:
        from PIL import Image
    except ImportError:
        return False
    n, idx = icon_id // 1000, icon_id % 1000
    if n not in _ATLAS:
        f = CRACK / "out_images" / "data" / "interface" / "icon" / f"icon{n:02d}.png"
        _ATLAS[n] = Image.open(f).convert("RGBA") if f.exists() else None
    atl = _ATLAS[n]
    if atl is None:
        return False
    cols = atl.width // 32
    r, c = divmod(idx, cols)
    if (r + 1) * 32 > atl.height:
        return False
    cell = atl.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32))
    if not cell.getbbox():  # empty cell
        return False
    cell.save(dest)
    return True


GENERIC = ("อีโวลูเตอร์", "แอคเซเรเตอร์", "อีโวลูชั่นลิมิต")
STAGE_HINT = {"ร่างสุดยอด": "67", "เมก้า": "67", "ร่างสมบูรณ์": "5", "อัลติเมท": "5",
              "ร่างเจริญวัย": "4", "แชมเปี้ยน": "4"}
DESC_PATTERNS = [
    r"ขยายช่องวิวัฒนาการ(?:ขั้นสุดท้าย)?ของ.+?สำหรับ\s*(?P<t>[^.\n@]+)",
    r"ขยายช่องวิวัฒนาการสำหรับ\s*(?P<t>.+?)ของ",
    r"ขยายช่องวิวัฒนาการ(?!ของ|ขั้นสุดท้าย|สำหรับ)\s*(?P<t>[^.\n@]+)",
    r"ปลดร่างสายวิวัฒนาการ\s*(?P<t>.+?)ของ",
    r"(?:ใช้|ใช้เพื่อ)\s*ปลดร่าง(?:โจเกรส)?\s*(?P<t>.+?)\s*ของ",
]


def _nkey(s):
    s = re.sub(r"ดิจิมอนใหม่|โจเกรส", "", s or "")
    return re.sub(r"[\s\-–:()\[\]·.,'\"!]+", "", s).replace("์", "")


def apply_descriptions(result, names, its):
    """Item descriptions name the Digimon they unlock ("ขยายช่องวิวัฒนาการจินลอนมอน (ร่างสุดยอด)").
    That beats the evolution table where it still lists a generic item (Evoluter/Accelerator) or none."""
    by_name, by_loose = {}, {}
    loose = lambda k: re.sub(r"[่้๊๋็ีืูัิุึาะำ]", "", k)
    for cid, n in names.items():
        by_name.setdefault(_nkey(n), []).append(cid)
        by_loose.setdefault(loose(_nkey(n)), []).append(cid)
    changed = []
    for iid, it in sorted(its.items()):
        if "[" in it["name"] or not it["name"].strip() or "ขับขี่" in it["desc"]:
            continue
        desc = re.sub(r"@<[^>]*>|\n", " ", it["desc"])
        tgt = None
        for p in DESC_PATTERNS:
            m = re.search(p, desc)
            if m:
                tgt = m.group("t").strip()
                break
        if tgt:
            tgt = re.split(r"\s{2,}|ไอเทม|สามารถ|หาได้", tgt)[0].strip(" .")
        if not tgt or "ดิจิมอนครอสวอร์ส" in tgt:
            continue
        hint = next((v for k, v in STAGE_HINT.items() if f"({k})" in tgt), None)
        tgt = re.sub(r"\((?:%s)\)" % "|".join(STAGE_HINT), "", tgt)
        cids = by_name.get(_nkey(tgt), []) or by_loose.get(loose(_nkey(tgt)), [])
        if hint:
            cids = [c for c in cids if str(c)[0] in hint]
        in_tree = [c for c in cids if c in result]
        # only slots that still show a generic item (or none) can take the named one
        is_generic = lambda c: not (result[c].get("item") or {}).get("name_th") or             any(g in result[c]["item"]["name_th"] for g in GENERIC)
        if any((result[c].get("item") or {}).get("name_th", "").strip() == it["name"].strip() for c in in_tree):
            continue  # that Digimon already shows this exact item
        if len(in_tree) == 1:
            open_slots = [c for c in in_tree if is_generic(c)]
        else:  # several forms share the name: only replace a generic item, never fill an empty slot
            open_slots = [c for c in in_tree if (result[c].get("item") or {}).get("name_th") and is_generic(c)]
        if len(open_slots) != 1:
            continue
        in_tree = open_slots
        rec = result[in_tree[0]]
        cur = (rec.get("item") or {}).get("name_th", "")
        has_icon = save_icon(iid, it.get("icon_id"))
        rec["item"] = {"id": iid, "name_th": it["name"], "icon": f"/images/client_items/{iid}.png" if has_icon else "",
                       "variants": [], "from": "description"}
        rec["amount"] = 1
        rec["items"] = [{"item": rec["item"], "amount": 1, "parent_th": rec.get("parent_th", "")}]
        changed.append((in_tree[0], names[in_tree[0]], cur or "-", it["name"]))
    for c in changed:
        print("  [desc]", c)
    print(f"[evo] {len(changed)} unlock items taken from item descriptions")


def build():
    names = digimon_names()
    valid = set(names)
    its = items()
    by_section = {}
    for iid, it in its.items():
        if it["section"]:
            by_section.setdefault(it["section"], []).append(iid)
    lines = parse_lines(valid)
    ICON_OUT.mkdir(parents=True, exist_ok=True)
    result = {}
    for ln in lines:
        sec = ln["item_section"]
        cand = sorted(by_section.get(sec, []))
        # prefer the normal item over "[กิจกรรม]" / event copies
        main = [c for c in cand if "[" not in its[c]["name"]] or cand
        item = None
        if main:
            iid = main[0]
            has_icon = save_icon(iid, its[iid].get("icon_id"))
            item = {"id": iid, "name_th": its[iid]["name"], "icon": f"/images/client_items/{iid}.png" if has_icon else "",
                    "variants": [{"id": c, "name_th": its[c]["name"]} for c in cand if c != iid]}
        rec = {"type": ln["type"], "name_th": names.get(ln["type"], ""), "parent": ln["parent"],
               "parent_th": names.get(ln["parent"], ""), "unlock_level": ln["unlock_level"],
               "item_section": sec, "amount": ln["amount"], "item": item, "items": []}
        # a Digimon can sit in several trees; keep the entry that actually needs an item
        prev = result.get(ln["type"])
        if not prev or (not prev["item"] and item):
            if prev:
                rec["items"] = prev["items"]
            result[ln["type"]] = rec
        # Jogress forms sit in every partner's tree, each with its own item: keep them all
        cur = result[ln["type"]]
        if item and all(x["item"]["id"] != item["id"] for x in cur["items"]):
            cur["items"].append({"item": item, "amount": ln["amount"] or 1, "parent_th": names.get(ln["parent"], "")})
    apply_descriptions(result, names, its)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    with_item = sum(1 for r in result.values() if r["item"])
    print(f"[evo] {len(lines)} slots, {len(result)} Digimon, {with_item} need an unlock item -> {OUT.name}")
    return result


if __name__ == "__main__":
    build()
