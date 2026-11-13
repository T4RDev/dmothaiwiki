"""
Seal Master catalog builder backed by CrackDMO decrypted client tables,
Thai client language strings, and official DMO Wiki Seal Master cross-references.
"""
import json
import math
import os
import re
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from seal_models import build_all_seal_models
except ImportError:
    from web.seal_models import build_all_seal_models

BASE_DIR = Path(__file__).resolve().parent.parent
CRACKDMO_DIR = Path(os.environ.get("CRACKDMO_DIR", r"C:\Users\T4R\Desktop\AllWorks\CrackDMO"))
TBL_DIR = CRACKDMO_DIR / "out_decrypted" / "data" / "bin" / "table"
LANG_DIR = CRACKDMO_DIR / "out_json" / "language"
SEAL_IMG_DISK = BASE_DIR / "output" / "images" / "sealmaster" / "sealimage"
WIKI_SEAL_PAGE = BASE_DIR / "output" / "pages" / "Seal_Master.json"

# Verified against sealcard.bin stat_type + Thai item_str descriptions
STAT_DEFS: Dict[int, Dict[str, Any]] = {
    5:  {"key": "AT", "order": 1, "name_en": "Attack",        "name_th": "พลังโจมตี",       "is_pct": False},
    9:  {"key": "CT", "order": 2, "name_en": "Critical Rate", "name_th": "คริติคอล",         "is_pct": True},
    11: {"key": "HT", "order": 3, "name_en": "Hit Rate",      "name_th": "ความแม่นยำ",      "is_pct": False},
    1:  {"key": "HP", "order": 4, "name_en": "Health Points", "name_th": "พลังชีวิต (HP)",    "is_pct": False},
    3:  {"key": "DS", "order": 5, "name_en": "Digi-Soul",     "name_th": "ดิจิโซล (DS)",     "is_pct": False},
    13: {"key": "DE", "order": 6, "name_en": "Defense",       "name_th": "พลังป้องกัน",      "is_pct": False},
    15: {"key": "BL", "order": 7, "name_en": "Block Rate",    "name_th": "อัตราบล็อก",       "is_pct": True},
    17: {"key": "EV", "order": 8, "name_en": "Evade Rate",    "name_th": "การหลบหลีก",       "is_pct": True},
}

TIER_META = [
    {"tier": 0, "code": "normal",   "name_en": "Normal",   "name_th": "ธรรมดา",    "bg": "/images/sealmaster/sealback/sealmaster_bg_normal.png",   "color": "#94a3b8"},
    {"tier": 1, "code": "bronze",   "name_en": "Bronze",   "name_th": "บรอนซ์",    "bg": "/images/sealmaster/sealback/sealmaster_bg_bronze.png",   "color": "#cd7f32"},
    {"tier": 2, "code": "silver",   "name_en": "Silver",   "name_th": "ซิลเวอร์",   "bg": "/images/sealmaster/sealback/sealmaster_bg_silver.png",   "color": "#cbd5e1"},
    {"tier": 3, "code": "gold",     "name_en": "Gold",     "name_th": "โกลด์",      "bg": "/images/sealmaster/sealback/sealmaster_bg_master.png",   "color": "#f59e0b"},
    {"tier": 4, "code": "platinum", "name_en": "Platinum", "name_th": "แพลทินัม",   "bg": "/images/sealmaster/sealback/sealmaster_bg_platinum.png", "color": "#38bdf8"},
    {"tier": 5, "code": "master",   "name_en": "Master",   "name_th": "มาสเตอร์",   "bg": "/images/sealmaster/sealback/sealmaster_bg_master2.png",  "color": "#c084fc"},
]

NATURE_ICONS: Dict[int, Tuple[str, str]] = {
    16: ("น้ำแข็ง",    "/images/sealmaster/elemental/sealmaster_elemental_ice.png"),
    17: ("น้ำ",        "/images/sealmaster/elemental/sealmaster_elemental_water.png"),
    18: ("ไฟ",         "/images/sealmaster/elemental/sealmaster_elemental_fire.png"),
    19: ("ดิน",        "/images/sealmaster/elemental/sealmaster_elemental_earth.png"),
    20: ("ลม",         "/images/sealmaster/elemental/sealmaster_elemental_wind.png"),
    21: ("ไม้",        "/images/sealmaster/elemental/sealmaster_elemental_tree.png"),
    22: ("แสง",        "/images/sealmaster/elemental/sealmaster_elemental_light.png"),
    23: ("ความมืด",    "/images/sealmaster/elemental/sealmaster_elemental_dark.png"),
    24: ("สายฟ้า",     "/images/sealmaster/elemental/sealmaster_elemental_elec.png"),
    25: ("เหล็ก",      "/images/sealmaster/elemental/sealmaster_elemental_iron.png"),
    26: ("ไร้ธาตุ",    "/images/sealmaster/elemental/sealmaster_elemental_non.png"),
}

# Non-hunting hub / pack map IDs in sealfilter.bin (still included in map filter like Thai DMO,
# but distinguished from field-kill drops for source_categories)
SPECIAL_MAP_IDS = {
    3:    "ศูนย์บัญชาการ DATS",
    1312: "การทำลายล้างและการฟื้นฟู",
}

WORLD_NAMES_CLEAN = {
    10: "Xros Wars",
    15: "สมรภูมิชี้ชะตา (Decisive Battle)",
    21: "ดิจิมอน ฟรอนเทียร์",
}

SEALS_PER_OPENER = 50
SEALS_PER_CLOSER = 50


def _strip_color_tags(txt: str) -> str:
    txt = re.sub(r"@<tc:[^>]*>", "", txt or "")
    txt = txt.replace("@</tc>", "").replace("\r", "")
    # Drop shift-right-click inventory helper boilerplate to keep clean flavor text
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    kept = []
    for l in lines:
        if "กด Shift + คลิกขวา" in l or "[เมื่อถึงระดับซีลมาสเตอร์]" in l:
            continue
        kept.append(l)
    return "\n".join(kept)


def _format_stat(val: int, is_pct: bool) -> str:
    if is_pct:
        pct = f"{val / 100:.2f}".rstrip("0").rstrip(".")
        return f"+{pct}%"
    return f"+{val:,}"


def _norm_key(s: str) -> str:
    s = re.sub(r"\(.*?\)", "", (s or "").lower())
    return re.sub(r"[^a-z0-9\u0e00-\u0e7f]+", "", s)


def _slugify(name: str) -> str:
    s = (name or "").strip().lower()
    s = re.sub(r"[\s_/\\]+", "-", s)
    s = re.sub(r"[^a-z0-9\u0e00-\u0e7f\-]+", "", s)
    return re.sub(r"-{2,}", "-", s).strip("-") or "seal"


def _load_lang_dict(filename: str) -> Dict[int, Any]:
    p = LANG_DIR / filename
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        rows = json.load(f)
    out: Dict[int, Any] = {}
    if isinstance(rows, list):
        for r in rows:
            if isinstance(r, dict) and "id" in r:
                out[int(r["id"])] = r.get("fields") if "fields" in r else r.get("text")
    return out


def _parse_sealdigimonimage() -> Dict[int, str]:
    p = TBL_DIR / "sealdigimonimage.bin"
    if not p.exists():
        return {}
    data = p.read_bytes()
    cnt = struct.unpack_from("<I", data, 0)[0]
    pos = 4
    out: Dict[int, str] = {}
    for _ in range(cnt):
        did, slen = struct.unpack_from("<II", data, pos)
        pos += 8
        out[did] = data[pos : pos + slen].decode("ascii", "replace")
        pos += slen
    return out


def _parse_sealleader() -> Dict[int, int]:
    p = TBL_DIR / "sealleader.bin"
    if not p.exists():
        return {}
    data = p.read_bytes()
    cnt = struct.unpack_from("<I", data, 0)[0]
    out: Dict[int, int] = {}
    for i in range(cnt):
        idx, mon_id, _ = struct.unpack_from("<HHH", data, 4 + i * 6)
        out[idx] = mon_id
    return out


def _parse_sealfilter(
    wnames: Dict[int, Any], mnames: Dict[int, Any], anames: Dict[int, Any]
) -> Dict[int, List[Dict[str, Any]]]:
    p = TBL_DIR / "sealfilter.bin"
    if not p.exists():
        return {}
    data = p.read_bytes()
    cnt = struct.unpack_from("<I", data, 0)[0]
    pos = 4
    out: Dict[int, List[Dict[str, Any]]] = {}
    for wi in range(cnt):
        cat_id, sub_cnt = struct.unpack_from("<HI", data, pos)
        pos += 6
        w_raw = wnames.get(cat_id)
        wname = WORLD_NAMES_CLEAN.get(cat_id) or (
            w_raw[0].replace("\n", " ").strip() if isinstance(w_raw, list) and w_raw else f"พื้นที่ #{cat_id}"
        )
        for mi in range(sub_cnt):
            sub_id, card_cnt = struct.unpack_from("<II", data, pos)
            pos += 8
            items = list(struct.unpack_from(f"<{card_cnt}I", data, pos))
            pos += 4 * card_cnt
            raw_mname = (
                mnames.get(sub_id)
                or (anames.get(sub_id)[0] if isinstance(anames.get(sub_id), list) and anames.get(sub_id) else None)
                or ""
            )
            raw_mname = raw_mname.replace("\n", " ").strip()
            has_named_map = bool(raw_mname)
            display_map = raw_mname or f"แหล่งกิจกรรม/แลกเปลี่ยน ({wname})"
            is_field_map = has_named_map and sub_id not in SPECIAL_MAP_IDS
            for iid in items:
                out.setdefault(iid, []).append({
                    "world_id": cat_id,
                    "world_name": wname,
                    "world_order": wi,
                    "map_id": sub_id,
                    "map_name": display_map,
                    "map_order": mi,
                    "raw_map_name": raw_mname,
                    "is_hunting_map": has_named_map,
                    "is_field_map": is_field_map,
                })
    return out


def _parse_digimon_elements() -> Dict[int, Tuple[str, str]]:
    p = TBL_DIR / "digimonlistdata.bin"
    if not p.exists():
        return {}
    data = p.read_bytes()
    out: Dict[int, Tuple[str, str]] = {}
    pos = 4
    # Scan safely for records where u32 at off matches off+24 and off+28
    # (verified across Tsunomon..Alphamon Ouryuken)
    for off in range(4, len(data) - 72, 2):
        mid = struct.unpack_from("<I", data, off)[0]
        if 10000 <= mid <= 99999 and mid not in out:
            if struct.unpack_from("<II", data, off + 24) == (mid, mid):
                elem_id = struct.unpack_from("<H", data, off + 62)[0]
                if elem_id in NATURE_ICONS:
                    out[mid] = NATURE_ICONS[elem_id]
    return out


def _parse_itemcreation_for_seals(
    seal_ids: set, istr: Dict[int, Any], nstr: Dict[int, Any]
) -> Dict[int, List[Dict[str, Any]]]:
    p = TBL_DIR / "itemcreation.bin"
    if not p.exists():
        return {}
    ic = p.read_bytes()

    # Locate NPC group header offsets: repeated <npc_id, npc_id> where id in npc_str
    npc_anchors: List[Tuple[int, str]] = []
    for off in range(4, len(ic) - 8, 2):
        a, b = struct.unpack_from("<II", ic, off)
        if a == b and 90000 <= a <= 99999 and a in nstr:
            if not npc_anchors or off - npc_anchors[-1][0] > 16:
                nf = nstr[a]
                if isinstance(nf, list) and len(nf) >= 2:
                    title = nf[0].strip()
                    name = nf[1].strip()
                    label = f"{name} {title}".strip() if title and title != name else name
                else:
                    label = f"NPC #{a}"
                npc_anchors.append((off, label))

    def find_npc(offset: int) -> str:
        owner = "NPC คราฟต์ไอเทม"
        for a_off, a_name in npc_anchors:
            if a_off <= offset:
                owner = a_name
            else:
                break
        return owner

    recipes: Dict[int, List[Dict[str, Any]]] = {}
    seen_keys = set()
    for iid in sorted(seal_ids):
        pat = struct.pack("<I", iid)
        start = 0
        while True:
            idx = ic.find(pat, start)
            if idx == -1:
                break
            start = idx + 1
            if idx < 4 or idx + 28 > len(ic):
                continue
            out_id, out_qty, prob, cost, mat_cnt = struct.unpack_from("<IIIII", ic, idx)
            if out_id != iid or not (1 <= out_qty <= 500) or not (1 <= prob <= 10000) or not (1 <= mat_cnt <= 6):
                continue
            mats = []
            off = idx + 20
            valid = True
            for _ in range(mat_cnt):
                if off + 8 > len(ic):
                    valid = False
                    break
                mid, mq = struct.unpack_from("<II", ic, off)
                if mid not in istr or not (1 <= mq <= 10000):
                    valid = False
                    break
                mname = istr[mid][0].replace("\n", " ").strip() if isinstance(istr[mid], list) else str(mid)
                mats.append({"item_id": mid, "name": mname, "qty": mq})
                off += 8
            if not valid or not mats:
                continue
            npc_name = find_npc(idx)
            dedup = (iid, npc_name, out_qty, cost, tuple((m["item_id"], m["qty"]) for m in mats))
            if dedup in seen_keys:
                continue
            seen_keys.add(dedup)
            recipes.setdefault(iid, []).append({
                "npc": npc_name,
                "out_qty": out_qty,
                "cost_bit": cost,
                "rate_pct": round(prob / 100, 1),
                "materials": mats,
            })
    return recipes


def _load_wiki_drop_lookup() -> Dict[Tuple[str, str], Dict[str, Any]]:
    if not WIKI_SEAL_PAGE.exists():
        return {}
    with WIKI_SEAL_PAGE.open("r", encoding="utf-8") as f:
        smj = json.load(f)
    stat_keys = ["AT", "CT", "HT", "HP", "DS", "DE", "BL", "EV"]
    lookup: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for idx, tbl in enumerate(smj.get("tables", [])[1:9]):
        sk = stat_keys[idx]
        for row in tbl.get("rows", []):
            if len(row) < 12 or row[0] == "Unopened":
                continue
            dname = row[8].strip()
            exch = row[9].strip()
            drops = row[10].strip()
            lookup[(_norm_key(dname), sk)] = {
                "name_en": dname,
                "exchange_text": exch,
                "drop_text": drops,
            }
            lookup.setdefault((_norm_key(dname), "*"), {
                "name_en": dname,
                "exchange_text": exch,
                "drop_text": drops,
            })
    return lookup


def _extract_name_en(img_path_str: str, fallback_th: str) -> str:
    fn = os.path.splitext(os.path.basename(img_path_str.replace("\\", "/")))[0]
    fn = re.sub(r"^sealmaster_img_", "", fn, flags=re.IGNORECASE)
    fn = re.sub(r"_+", " ", fn).strip()
    fn = re.sub(r"\s{2,}", " ", fn)
    if not fn:
        return fallback_th
    # Title-case pure lowercase tokens like 'kudamon', keep CamelCase intact
    if fn.islower():
        return fn.title()
    return fn


def _translate_wiki_drop_notes(drop_text: str) -> List[str]:
    if not drop_text or drop_text == "-":
        return []
    notes = []
    mc = re.findall(r"Monster Card Lv\.?\s*([0-9\-]+)", drop_text, flags=re.IGNORECASE)
    for m in mc:
        notes.append(f"การ์ดมอนสเตอร์ Lv.{m}")
    if "Not Droppable" in drop_text:
        notes.append("ไม่ดรอปจากมอนสเตอร์ทั่วไป (หาจากการแลก/กล่อง/แพ็ก)")
    if "Event" in drop_text:
        notes.append("กิจกรรมพิเศษ (Event)")
    if "Royal Base" in drop_text:
        notes.append("ดันเจี้ยน Royal Base")
    if "Destruction and Regeneration" in drop_text:
        notes.append("แพ็กสุ่มซีล Destruction and Regeneration")
    if "Seal Master Package" in drop_text or "Random Pack" in drop_text:
        notes.append("แพ็กสุ่มซีล (Seal Master Random Pack)")
    return list(dict.fromkeys(notes))


def build_seals() -> Dict[str, Any]:
    """Build complete Seal Master dataset from CrackDMO binaries + Thai strings + wiki notes."""
    istr = _load_lang_dict("item_str.json")
    nstr = _load_lang_dict("npc_str.json")
    wnames = _load_lang_dict("worldmapinfo_str.json")
    anames = _load_lang_dict("areamapinfo_str.json")
    mnames = _load_lang_dict("mapname_str.json")

    img_map = _parse_sealdigimonimage()
    leader_map = _parse_sealleader()
    filter_sources = _parse_sealfilter(wnames, mnames, anames)
    elem_map = _parse_digimon_elements()
    wiki_drops = _load_wiki_drop_lookup()

    leader_3d_cidx: Dict[str, int] = {}
    leader_3d_models: Dict[str, Any] = {}
    if build_all_seal_models is not None:
        try:
            sm_res = build_all_seal_models(force=False)
            leader_3d_cidx = {str(k): int(v) for k, v in (sm_res.get("cidx_to_leader") or {}).items()}
            leader_3d_models = sm_res.get("models") or {}
        except Exception as mex:
            print("[WARN] Seal leader 3D models skipped:", mex)

    disk_imgs: Dict[str, str] = {}
    if SEAL_IMG_DISK.exists():
        for fn in os.listdir(SEAL_IMG_DISK):
            disk_imgs[fn.lower()] = fn

    sc_path = TBL_DIR / "sealcard.bin"
    if not sc_path.exists():
        return {"seals": [], "stat_totals": [], "worlds": [], "maps": [], "source_types": [], "opener_closer": {}}

    data = sc_path.read_bytes()
    cnt = struct.unpack_from("<I", data, 0)[0]
    recs = [data[4 + i * 96 : 4 + (i + 1) * 96] for i in range(cnt)]
    seal_ids = {struct.unpack_from("<I", r, 0)[0] for r in recs}
    recipes = _parse_itemcreation_for_seals(seal_ids, istr, nstr)

    seals: List[Dict[str, Any]] = []
    slug_counts: Dict[str, int] = {}
    stat_totals_raw: Dict[str, Dict[str, Any]] = {}
    worlds_map: Dict[int, Dict[str, Any]] = {}
    maps_map: Dict[int, Dict[str, Any]] = {}

    for rec_idx, r in enumerate(recs):
        iid = struct.unpack_from("<I", r, 0)[0]
        cidx = struct.unpack_from("<H", r, 4)[0]
        mon_id = struct.unpack_from("<I", r, 6)[0]
        tcnt = struct.unpack_from("<I", r, 14)[0]
        raw_tiers = [struct.unpack_from("<BHHHHI", r, 18 + t * 13) for t in range(tcnt)]
        if not raw_tiers:
            continue

        st_type = raw_tiers[0][3]
        sdef = STAT_DEFS.get(st_type, {"key": f"STAT{st_type}", "order": 99, "name_en": f"Stat {st_type}", "name_th": f"สเตตัส #{st_type}", "is_pct": False})
        stat_key = sdef["key"]
        is_pct = bool(sdef["is_pct"])

        item_fields = istr.get(iid)
        name_th = (
            item_fields[0].replace("\n", " ").strip()
            if isinstance(item_fields, list) and item_fields
            else f"ซีล #{iid}"
        )
        short_th = re.sub(r"\s*ซีล$", "", name_th).strip() or name_th
        desc_th = _strip_color_tags(item_fields[2]) if isinstance(item_fields, list) and len(item_fields) > 2 else ""

        rel_img_raw = img_map.get(mon_id) or img_map.get(leader_map.get(cidx, 0), "")
        fn_png = os.path.splitext(os.path.basename(rel_img_raw.replace("\\", "/")))[0].lower() + ".png"
        actual_fn = disk_imgs.get(fn_png)
        image_url = f"/images/sealmaster/sealimage/{actual_fn}" if actual_fn else "/images/Seal_Icon.png"
        name_en = _extract_name_en(rel_img_raw, short_th)

        # Element badge from digimonlistdata
        elem_info = elem_map.get(mon_id) or elem_map.get(leader_map.get(cidx, 0))
        element_name = elem_info[0] if elem_info else ""
        element_icon = elem_info[1] if elem_info else ""

        # Build 6-tier progression
        tiers_out: List[Dict[str, Any]] = []
        for t_i, (_, _, req, _, st_val, _) in enumerate(raw_tiers):
            meta = TIER_META[t_i] if t_i < len(TIER_META) else TIER_META[-1]
            next_req = raw_tiers[t_i + 1][2] if t_i + 1 < len(raw_tiers) else None
            prev_req = raw_tiers[t_i - 1][2] if t_i > 0 else 0
            prev_val = raw_tiers[t_i - 1][4] if t_i > 0 else 0

            range_text = f"{req:,}" if next_req is None else (f"{req:,}" if next_req - 1 == req else f"{req:,} ~ {next_req - 1:,}")
            openers_cum = math.ceil(req / SEALS_PER_OPENER)
            seals_delta = req - prev_req
            # Incremental openers if you open exact delta to reach this tier cleanly in batches
            openers_delta = math.ceil(seals_delta / SEALS_PER_OPENER) if seals_delta > 0 else 0
            closers_at_tier = math.ceil(req / SEALS_PER_CLOSER)

            tiers_out.append({
                "tier": meta["tier"],
                "code": meta["code"],
                "name_en": meta["name_en"],
                "name_th": meta["name_th"],
                "bg_image": meta["bg"],
                "color": meta["color"],
                "min_seals": req,
                "max_seals_in_tier": (next_req - 1) if next_req is not None else req,
                "range_text": range_text,
                "seals_delta": seals_delta,
                "stat_value": st_val,
                "stat_display": _format_stat(st_val, is_pct),
                "stat_delta": st_val - prev_val,
                "stat_delta_display": _format_stat(st_val - prev_val, is_pct),
                "openers_total_direct": openers_cum,
                "openers_step_batch": openers_delta,
                "closers_to_unequip": closers_at_tier,
                "seals_returned_on_close": req,
            })

        master_tier = tiers_out[-1]
        master_seals = master_tier["min_seals"]
        master_openers = master_tier["openers_total_direct"]
        master_closers = master_tier["closers_to_unequip"]

        # Map & source enrichment
        f_entries = filter_sources.get(iid, [])
        hunting_maps = []
        hub_sources = []
        seen_maps = set()
        field_drop_maps = []
        for fe in f_entries:
            mid_key = (fe["world_id"], fe["map_id"])
            if mid_key in seen_maps:
                continue
            seen_maps.add(mid_key)
            if fe["is_hunting_map"]:
                hunting_maps.append({"world_id": fe["world_id"], "world_name": fe["world_name"], "map_id": fe["map_id"], "map_name": fe["map_name"]})
                worlds_map.setdefault(fe["world_id"], {"world_id": fe["world_id"], "world_name": fe["world_name"], "world_order": fe["world_order"], "count": 0})
                worlds_map[fe["world_id"]]["count"] += 1
                maps_map.setdefault(fe["map_id"], {"map_id": fe["map_id"], "map_name": fe["map_name"], "world_id": fe["world_id"], "world_name": fe["world_name"], "world_order": fe["world_order"], "map_order": fe["map_order"], "count": 0})
                maps_map[fe["map_id"]]["count"] += 1
                if fe.get("is_field_map"):
                    field_drop_maps.append(fe["map_id"])
            else:
                hub_sources.append({"world_id": fe["world_id"], "world_name": fe["world_name"], "map_id": fe["map_id"], "map_name": fe["map_name"]})

        craft_list = recipes.get(iid, [])
        wiki_hit = wiki_drops.get((_norm_key(name_en), stat_key)) or wiki_drops.get((_norm_key(name_en), "*"))
        extra_notes = _translate_wiki_drop_notes(wiki_hit["drop_text"]) if wiki_hit else []
        if "กิจกรรม" in name_th or "Event" in name_en:
            if "กิจกรรมพิเศษ (Event)" not in extra_notes:
                extra_notes.append("ซีลกิจกรรม (Event)")

        source_categories = []
        if field_drop_maps or "เมื่อจัดการ" in desc_th:
            source_categories.append("drop")
        if craft_list:
            source_categories.append("exchange")
        if any("การ์ดมอนสเตอร์" in n for n in extra_notes):
            source_categories.append("card")
        if any(fe["map_id"] in (1312, 1700) for fe in f_entries) or any("แพ็ก" in n for n in extra_notes):
            source_categories.append("pack")
        if "กิจกรรม" in name_th or any("Event" in n or "กิจกรรม" in n for n in extra_notes):
            source_categories.append("event")
        if not source_categories:
            source_categories.append("special")

        # Unique readable slug without raw IDs unless duplicate name
        base_slug = _slugify(name_th)
        slug_counts[base_slug] = slug_counts.get(base_slug, 0) + 1
        slug = base_slug if slug_counts[base_slug] == 1 else f"{base_slug}-{stat_key.lower()}-{slug_counts[base_slug]}"

        # Aggregate stat summary
        st_sum = stat_totals_raw.setdefault(stat_key, {
            "key": stat_key,
            "order": sdef["order"],
            "name_en": sdef["name_en"],
            "name_th": sdef["name_th"],
            "is_pct": is_pct,
            "count": 0,
            "max_total": 0,
            "total_master_seals": 0,
            "total_master_openers": 0,
        })
        st_sum["count"] += 1
        st_sum["max_total"] += master_tier["stat_value"]
        st_sum["total_master_seals"] += master_seals
        st_sum["total_master_openers"] += master_openers

        lmon_id = leader_3d_cidx.get(str(cidx)) or leader_map.get(cidx, mon_id)
        lmodel_meta = leader_3d_models.get(str(lmon_id)) or leader_3d_models.get(str(mon_id)) or {}
        lmodel_url = lmodel_meta.get("url", "")
        lmodel_nif = lmodel_meta.get("nif", "")

        seals.append({
            "id": iid,
            "card_index": cidx,
            "mon_id": mon_id,
            "leader_mon_id": lmon_id,
            "leader_model_url": lmodel_url,
            "leader_model_nif": lmodel_nif,
            "leader_preview_type": "digimon_3d" if lmodel_url else "card_3d",
            "slug": slug,
            "name_th": name_th,
            "short_th": short_th,
            "name_en": name_en,
            "description_th": desc_th,
            "stat_key": stat_key,
            "stat_name_th": sdef["name_th"],
            "stat_name_en": sdef["name_en"],
            "is_pct": is_pct,
            "image": image_url,
            "element_name": element_name,
            "element_icon": element_icon,
            "tiers": tiers_out,
            "master_seals": master_seals,
            "master_stat_value": master_tier["stat_value"],
            "master_stat_display": master_tier["stat_display"],
            "master_openers": master_openers,
            "master_closers": master_closers,
            "seals_per_opener": SEALS_PER_OPENER,
            "seals_per_closer": SEALS_PER_CLOSER,
            "hunting_maps": hunting_maps,
            "hub_sources": hub_sources,
            "crafts": craft_list,
            "extra_notes": extra_notes,
            "wiki_drop_en": wiki_hit["drop_text"] if wiki_hit else "",
            "source_categories": source_categories,
            "is_event": "event" in source_categories,
        })

    # Sort seals cleanly: Stat order -> Master stat desc -> Master seals desc -> Name TH
    stat_order_map = {v["key"]: v["order"] for v in STAT_DEFS.values()}
    seals.sort(key=lambda s: (stat_order_map.get(s["stat_key"], 99), -s["master_stat_value"], -s["master_seals"], s["name_th"]))

    stat_totals = sorted(stat_totals_raw.values(), key=lambda x: x["order"])
    for st in stat_totals:
        st["max_total_display"] = _format_stat(st["max_total"], st["is_pct"])

    worlds = sorted(worlds_map.values(), key=lambda w: (w["world_order"], w["world_id"]))
    maps = sorted(maps_map.values(), key=lambda m: (m["world_order"], m["map_order"], m["map_id"]))

    return {
        "total": len(seals),
        "seals": seals,
        "stat_totals": stat_totals,
        "worlds": worlds,
        "maps": maps,
        "tier_meta": TIER_META,
        "opener_closer_rules": {
            "opener_name_th": "การ์ดเปิดผนึก",
            "opener_name_en": "Seal Opener",
            "opener_icon": "/images/Seal_Opener_Icon.png",
            "seals_per_opener": SEALS_PER_OPENER,
            "closer_name_th": "การ์ดปิดผนึก",
            "closer_name_en": "Seal Closer",
            "closer_icon": "/images/Seal_Closer_Icon.png",
            "seals_per_closer": SEALS_PER_CLOSER,
            "ticket_icon": "/images/Seal_Exchange_Ticket.png",
            "opener_rule_th": "การ์ดเปิดผนึก 1 ใบ เปิดใช้งานซีลได้สูงสุด 50 ใบ (หากเปิดน้อยกว่า 50 ใบต่อครั้ง จะใช้ขั้นต่ำ 1 ใบ; สูตรคำนวณ = ปัดเศษขึ้นของ จำนวนซีล ÷ 50)",
            "closer_rule_th": "การ์ดปิดผนึก 1 ใบ ปิดผนึกซีลที่เปิดใช้งานไว้ได้สูงสุด 50 ใบ เพื่อนำซีลการ์ดกลับมาเป็นไอเทมที่แลกเปลี่ยนได้ โดยจะได้รับซีลการ์ดกลับคืนเต็มจำนวน 1:1 ตามจำนวนซีลที่เลือกปิดผนึก (เช่น ปิดผนึก 3,000 ใบ ใช้การ์ดปิดผนึก 60 ใบ → ได้รับซีลกลับ 3,000 ใบ)",
        },
    }


if __name__ == "__main__":
    data = build_seals()
    print(f"Total seals: {data['total']}")
    print("Stat totals:", [(x["key"], x["count"], x["max_total_display"]) for x in data["stat_totals"]])
    print("Hunting worlds:", len(data["worlds"]), "Hunting maps:", len(data["maps"]))
    # Verify unique slugs
    slugs = [s["slug"] for s in data["seals"]]
    assert len(slugs) == len(set(slugs)), "Duplicate slugs!"
    print("Sample seal:", json.dumps(data["seals"][0], ensure_ascii=False, indent=2)[:800])

