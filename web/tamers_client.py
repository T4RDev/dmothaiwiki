"""Tamer profiles, Lv.1..180 stats, skills, and unlock items from the Thai DMO client (CrackDMO).

Sources (read-only):
    CrackDMO/out_json/language/tamer_str.json
    CrackDMO/out_json/language/skill_str.json
    CrackDMO/out_json/language/buff_str.json
    CrackDMO/out_json/language/item_str.json
    CrackDMO/out_decrypted/data/bin/table/createlist_tamer.bin
    CrackDMO/out_decrypted/data/bin/table/tamerstats.bin
    CrackDMO/out_decrypted/data/bin/table/tamerskill.bin
    CrackDMO/out_images/data/tamer/<folder>/*
    CrackDMO/pack01_filelist.txt
"""
import json
import re
import shutil
import struct
from pathlib import Path

import thai_client_evo as E

CRACK = E.CRACK
BASE_DIR = Path(__file__).resolve().parent.parent
TAMER_IMG_OUT = BASE_DIR / "output" / "images" / "tamers"
CACHE_FILE = Path(__file__).resolve().parent / "tamers_cache.json"

SERIES_TH = {
    "เซฟเวอร์ส": "เซฟเวอร์ส",
    "แอดเวนเจอร์": "แอดเวนเจอร์",
    "พาวเวอร์ดิจิมอน": "พาวเวอร์ดิจิมอน",
    "테이머즈": "เทมเมอร์ส",
    "고스트게임": "โกสต์เกม",
}
SERIES_EN = {
    "เซฟเวอร์ส": "Digimon Savers",
    "แอดเวนเจอร์": "Digimon Adventure",
    "พาวเวอร์ดิจิมอน": "Digimon Adventure 02",
    "เทมเมอร์ส": "Digimon Tamers",
    "โกสต์เกม": "Digimon Ghost Game",
}
GENDER_TH = {
    "ชาย": "ชาย",
    "หญิง": "หญิง",
    "남자": "ชาย",
    "여자": "หญิง",
}

# English display names & metadata matching the 21 client Tamer IDs
TAMER_META = {
    80001: ("Marcus Damon (Masaru)", "มาซารุ", "Agumon (Savers)"),
    80002: ("Thomas H. Norstein (Tohma)", "โทม่า", "Gaomon"),
    80003: ("Yoshino Fujieda", "โยชิโนะ", "Lalamon"),
    80004: ("Keenan Crier (Ikuto)", "อิคุโตะ", "Falcomon (Savers)"),
    80005: ("Tai Kamiya (Taichi)", "ไทจิ", "Agumon (Adventure)"),
    80006: ("Mimi Tachikawa", "มีมี่", "Palmon"),
    80007: ("Matt Ishida (Yamato)", "ยามาโตะ", "Gabumon"),
    80008: ("T.K. Takaishi (Takeru)", "ทาเครุ", "Patamon"),
    80009: ("Kari Kamiya (Hikari)", "ฮิคาริ", "Salamon / Gatomon"),
    80010: ("Sora Takenouchi", "โซระ", "Biyomon"),
    80011: ("Takato Matsuki", "ทาคาโตะ", "Guilmon"),
    80012: ("Rika Nonaka (Ruki)", "รูคิ", "Renamon"),
    80013: ("Henry Wong (Lee Jyenrya)", "เจินเรีย", "Terriermon"),
    80014: ("Izzy Izumi (Koushiro)", "โคจิโร่", "Tentomon"),
    80015: ("Joe Kido", "โจ", "Gomamon"),
    80016: ("Jeri Katou (Juri)", "จูริ", "Leomon"),
    80017: ("Ryo Akiyama", "เรียว", "Monodramon / Cyberdramon"),
    80018: ("Hiro Amanokawa", "ฮิโระ", "Gammamon"),
    80019: ("Ruli Tsukiyono", "รูริ", "Angoramon"),
    80020: ("Kiyoshiro Higashimitarai", "คิโยชิโร่", "Jellymon"),
    80021: ("Digimon Kaiser (Ken Ichijouji)", "ดิจิมอนไกเซอร์", "Wormmon / Chimairamon"),
}

# Tamer ID -> skill prefix in tamerskill.bin / skill_str.json
# (Koushiro 80014 & Joe 80015 sit ahead of Tamers/Ghost Game in skill IDs)
SKILL_PREFIX = {
    80001: 80001, 80002: 80002, 80003: 80003, 80004: 80004,
    80005: 80005, 80006: 80006, 80007: 80007, 80008: 80008,
    80009: 80009, 80010: 80010,
    80011: 80016, 80012: 80017, 80013: 80018,
    80014: 80014, 80015: 80015,
    80016: 80019, 80017: 80020,
    80018: 80021, 80019: 80022, 80020: 80023,
}

# Pack01 model folder per tamer ID
PACK_FOLDERS = {
    80001: "masaru", 80002: "tohma", 80003: "yoshino", 80004: "ikuto",
    80005: "taichi", 80006: "mimi", 80007: "yamato", 80008: "takeru",
    80009: "hikari", 80010: "sora", 80011: "takato", 80012: "ruki",
    80013: "jyenrya", 80014: "izmi", 80015: "joe", 80016: "katojury",
    80017: "akiyamaryo", 80018: "hiro", 80019: "ruli",
    80020: "higashimitaraikiyoshiro", 80021: "digimonemperor",
}

# Signature skill base name -> representative skill item ID (for icon extraction from iconXX atlases)
SKILL_ICON_ITEM = {
    "บ้าเลือด": 35348,
    "เชียร์": 35354,
    "กำแพงเหล็ก": 35358,
    "อวยพร": 35350,
    "ปกป้อง": 35344,
    "ให้กำลังใจ": 35356,
    "รวมพลัง": 35364,
    "ล็อคเป้า": 35366,
    "ป้องกัน": 35368,
    "วิเคราะห์": 35360,
    "หลบหลีก": 35362,
    "ความไร้เดียงสา": 35370,
    "เข้าชาร์จ": 35372,
    "จิตวิญญาณ": 35352,
    "หยั่งรู้": 35342,
    "ช็อค": 35346,
    "กำลังใจ": 35356,
    "ความใสซื่อ": 35370,
}

# Thai Patch 25300 revamped Tamer Skill pool (usable by ANY Tamer via Satsuma / Gekomon)
REVAMP_ACTIVE_SKILLS = [
    (35342, "หยั่งรู้", "คริติคอลเพิ่มขึ้น 100% เป็นเวลา 30 วินาที", "โทม่า"),
    (35344, "ปกป้อง", "สร้างบาเรียคอยป้องกันทำให้ไม่ได้รับความเสียหายเป็นเวลา 3 วินาที", "โยชิโนะ"),
    (35346, "ช็อค", "พลังโจมตีคริติคอลเพิ่มขึ้น 100% เป็นเวลา 30 วินาที", "อิคุโตะ"),
    (35348, "บ้าเลือด", "พลังโจมตีเพิ่มขึ้น 50% เป็นเวลา 30 วินาที", "ไทจิ"),
    (35350, "อวยพร", "ฟื้นฟู HP 40% ให้กับดิจิมอนของตัวเองและสมาชิกในปาร์ตี้", "มีมี่"),
    (35352, "จิตวิญญาณ", "พลังโจมตีเพิ่มขึ้น 30% เป็นเวลา 30 วินาที", "ยามาโตะ / คิโยชิโร่"),
    (35354, "เชียร์", "HP และ DS ของดิจิมอนเพิ่มขึ้น 100%", "ทาเครุ"),
    (35356, "ให้กำลังใจ", "เพิ่มค่า HP 30% ให้กับดิจิมอนของตัวเองและของทุกคนในปาร์ตี้ เป็นเวลา 180 วินาที", "ฮิคาริ / ฮิโระ"),
    (35358, "กำแพงเหล็ก", "ค่าความเสียหายที่ได้รับจากการโจมตีทั้งหมดลดลง 30% เป็นระยะเวลา 15 วินาที", "โซระ"),
    (35360, "วิเคราะห์", "พลังโจมตีคริติคอลเพิ่มขึ้น 150% เป็นระยะเวลา 8 วินาที", "โคจิโร่"),
    (35362, "หลบหลีก", "การหลบหลีกของดิจิมอนเพิ่มขึ้น 70% เป็นระยะเวลา 10 วินาที", "คิโด โจ"),
    (35366, "ล็อคเป้า", "ความแม่นยำในการโจมตีเพิ่มขึ้น 300% เป็นระยะเวลา 10 วินาที", "รูคิ"),
    (35364, "รวมพลัง", "พลังโจมตีสกิลของตัวเองและสมาชิกในปาร์ตี้เพิ่มขึ้น 10% เป็นระยะเวลา 30 วินาที", "ทาคาโตะ"),
    (35368, "ป้องกัน", "ความเสียหายทั้งหมดที่ตัวเองและสมาชิกในปาร์ตี้ได้รับลดลง 30% เป็นระยะเวลา 8 วินาที", "ลี เจินเรีย"),
    (35370, "ความไร้เดียงสา", "พลังป้องกันดิจิมอนของตัวเองเพิ่มขึ้น 500 และ HP เพิ่มขึ้น 15% เป็นระยะเวลา 180 วินาที", "จูริ / รูริ"),
    (35372, "เข้าชาร์จ", "พลังโจมตีของดิจิมอนเพิ่มขึ้น 100% และพลังโจมตีสกิลเพิ่มขึ้น 60% เป็นระยะเวลา 10 วินาที", "อาคิยามะ เรียว"),
]

REVAMP_PASSIVE_SKILLS = [
    (35374, "ความกล้าหาญของเทเมอร์ (Va)", "Va", "พลังโจมตีของดิจิมอนประเภทวัคซีนเพิ่มขึ้น 5%"),
    (35376, "ความกล้าหาญของเทเมอร์ (Da)", "Da", "พลังโจมตีของดิจิมอนประเภทดาต้าเพิ่มขึ้น 5%"),
    (35378, "ความกล้าหาญของเทเมอร์ (Vi)", "Vi", "พลังโจมตีของดิจิมอนประเภทไวรัสเพิ่มขึ้น 5%"),
    (35380, "ความกล้าหาญของเทเมอร์ (Un)", "Un", "พลังโจมตีของดิจิมอนไม่ปรากฏประเภทเพิ่มขึ้น 5%"),
    (35382, "สายสัมพันธ์ของเทเมอร์ (Va)", "Va", "HP ของดิจิมอนประเภทวัคซีนเพิ่มขึ้น 10%"),
    (35384, "สายสัมพันธ์ของเทเมอร์ (Da)", "Da", "HP ของดิจิมอนประเภทดาต้าเพิ่มขึ้น 10%"),
    (35386, "สายสัมพันธ์ของเทเมอร์ (Vi)", "Vi", "HP ของดิจิมอนประเภทไวรัสเพิ่มขึ้น 10%"),
    (35388, "สายสัมพันธ์ของเทเมอร์ (Un)", "Un", "HP ของดิจิมอนไม่ปรากฏประเภทเพิ่มขึ้น 10%"),
]


def _clean(text: str) -> str:
    text = re.sub(r"@<[^>]*>", "", text or "")
    text = re.sub(r"\r\n?", "\n", text)
    return text.strip().strip("'").strip()


def _parse_createlist():
    """Return tamer_id -> {starter: bool, flags: [a,b,c], order: int, costumes: [item_id...]}."""
    b = (CRACK / "out_decrypted/data/bin/table/createlist_tamer.bin").read_bytes()
    tids = list(range(80001, 80022))
    offs = sorted((b.find(struct.pack("<I", tid)), tid) for tid in tids if b.find(struct.pack("<I", tid)) >= 0)
    out = {}
    for idx, (pos, tid) in enumerate(offs):
        end = offs[idx + 1][0] if idx + 1 < len(offs) else len(b)
        chunk = b[pos:end]
        # Layout: u32 tid | u16 f1 | u16 f2 | u32 z1 | u32 order | u32 cost_cnt | cost_cnt * u32
        f1, f2 = struct.unpack_from("<HH", chunk, 4)
        order, cnt = struct.unpack_from("<II", chunk, 14) if len(chunk) >= 22 else (0, 0)
        costumes = []
        for k in range(min(cnt, 8)):
            if 22 + (k + 1) * 4 <= len(chunk):
                costumes.append(struct.unpack_from("<I", chunk, 22 + k * 4)[0])
        # First 4 Savers tamers have (f1, f2) == (257, 1) -> selectable in Character Creation
        is_starter = (f1 == 257 and f2 == 1)
        out[tid] = {"starter": is_starter, "order": order, "costumes": costumes}
    return out


def _parse_stats():
    """Return tamer_id -> list of 180 [lv, hp, ds, ms, de, at] rows."""
    b = (CRACK / "out_decrypted/data/bin/table/tamerstats.bin").read_bytes()
    cnt = struct.unpack_from("<I", b, 0)[0]
    out = {}
    for i in range(cnt):
        base = 4 + i * 5048
        tid, n_lv = struct.unpack_from("<II", b, base)
        rows = []
        for lv_idx in range(min(n_lv, 180)):
            lv, hp, ds, ms, de, at, _u = struct.unpack_from("<7I", b, base + 8 + lv_idx * 28)
            rows.append([lv, hp, ds, ms, de, at])
        out[tid] = rows
    return out


def _parse_tamerskills(skill_str, buff_str):
    """Return (by_prefix_skills, cash_upgrades_by_base)."""
    b = (CRACK / "out_decrypted/data/bin/table/tamerskill.bin").read_bytes()
    cnt = struct.unpack_from("<I", b, 0)[0]
    by_prefix = {}
    upgrades = {}
    for idx in range(cnt):
        rec = b[4 + idx * 42 : 4 + (idx + 1) * 42]
        seq = struct.unpack_from("<H", rec, 0)[0]
        code = struct.unpack_from("<I", rec, 6)[0]
        kind = struct.unpack_from("<H", rec, 16)[0]
        buff_id = struct.unpack_from("<I", rec, 22)[0]
        s_fields = skill_str.get(code) or []
        b_fields = buff_str.get(buff_id) or []
        name = _clean(s_fields[0] if s_fields else "") or _clean(b_fields[0] if b_fields else "")
        desc = _clean(s_fields[1] if len(s_fields) > 1 else "") or _clean(b_fields[1] if len(b_fields) > 1 else "")
        if not name or name in ("_", "0") or "test" in name.lower():
            continue
        pref = code // 100
        entry = {
            "seq": seq,
            "code": code,
            "kind": "passive" if kind == 4 else "active",
            "name": name,
            "desc": desc,
            "buff_id": buff_id,
        }
        if pref == 80012:
            # Shared/Upgraded cash tamer skill (ขั้นสูง / ขั้นสุดยอด / สายสัมพันธ์ / ความกล้าหาญ)
            base_name = re.sub(r"ขั้น(?:สูง|สุดยอด)$", "", name).strip()
            upgrades.setdefault(base_name, []).append(entry)
        else:
            by_prefix.setdefault(pref, []).append(entry)
    return by_prefix, upgrades


def _find_tamer_images():
    """Map tamer_id -> {portrait_lg, portrait_sm, extras} and copy PNGs into output/images/tamers/."""
    TAMER_IMG_OUT.mkdir(parents=True, exist_ok=True)
    src_root = CRACK / "out_images/data/tamer"
    out = {}
    if not src_root.exists():
        return out
    for p in src_root.rglob("*.png"):
        m = re.match(r"^00(800\d{2})_(.+?)(l|s)\.png$", p.name, re.I)
        if m:
            tid = int(m.group(1))
            size_kind = m.group(3).lower()
            dest_name = f"{tid}_{size_kind}.png"
            dest = TAMER_IMG_OUT / dest_name
            if not dest.exists() or dest.stat().st_size != p.stat().st_size:
                shutil.copyfile(p, dest)
            rec = out.setdefault(tid, {"portrait_lg": "", "portrait_sm": "", "extras": []})
            url = f"/images/tamers/{dest_name}"
            if size_kind == "l":
                rec["portrait_lg"] = url
            else:
                rec["portrait_sm"] = url
    return out


def _pack01_counts():
    """Return lowercased tamer folder -> file count inside Thai client pack01.pf."""
    p = CRACK / "pack01_filelist.txt"
    counts = {}
    if not p.exists():
        return counts
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        low = line.lower()
        if "\\tamer\\" in low:
            parts = low.split("\\")
            if len(parts) >= 3:
                counts[parts[2]] = counts.get(parts[2], 0) + 1
    return counts


def _role_tag(lv180):
    """Derive a clean stat specialization label from Lv.180 base stats [lv, hp, ds, ms, de, at]."""
    _lv, hp, ds, ms, de, at = lv180
    if at >= 250 and de >= 50:
        return "สมดุล AT / DE"
    if at >= 250:
        return "โจมตี AT สูง"
    if hp >= 2500:
        return "พลังชีวิต HP สูง"
    if ds >= 2500:
        return "ค่าพลังงาน DS สูง"
    if ms >= 580:
        return "คล่องตัว MS สูง"
    return "สายสมดุล"


def _copy_crack_asset(rel_src: str, dest_name: str) -> str:
    """Copy a PNG asset from CrackDMO/out_images into output/images/tamers/ and return its web URL."""
    TAMER_IMG_OUT.mkdir(parents=True, exist_ok=True)
    src = CRACK / "out_images" / rel_src
    if not src.exists():
        return ""
    dest = TAMER_IMG_OUT / dest_name
    if not dest.exists() or dest.stat().st_size != src.stat().st_size:
        shutil.copyfile(src, dest)
    return f"/images/tamers/{dest_name}"


def _build_skill_system(its):
    """Build the Thai Patch 25300 unified Tamer Skill System (NPC Satsuma quest + Gekomon exchange + 16 Active + 8 Passive)."""
    def item_icon(iid):
        it = its.get(iid)
        if it and E.save_icon(iid, it["icon_id"]):
            return f"/images/client_items/{iid}.png"
        return ""

    satsuma_img = _copy_crack_asset("data/npc/satsuma/0090018_satsumal.png", "npc_satsuma.png")
    gekomon_img = _copy_crack_asset("data/digimon/gekomon/0045161_gekomonl.png", "npc_gekomon.png")

    active_pool = [
        {
            "item_id": iid,
            "name": name,
            "desc": desc,
            "former_tamer": former,
            "icon": item_icon(iid),
        }
        for iid, name, desc, former in REVAMP_ACTIVE_SKILLS
    ]
    passive_pool = [
        {
            "item_id": iid,
            "name": name,
            "attr": attr,
            "group": "ความกล้าหาญของเทเมอร์ (AT +5%)" if "ความกล้าหาญ" in name else "สายสัมพันธ์ของเทมเมอร์ (HP +10%)",
            "desc": desc,
            "icon": item_icon(iid),
        }
        for iid, name, attr, desc in REVAMP_PASSIVE_SKILLS
    ]

    return {
        "patch_id": "25300",
        "patch_url": "/patch/25300",
        "title": "เทมเมอร์ทุกตัวใช้สกิลไหนก็ได้ (รับจากซาสึมะ)",
        "summary": "อัปเดตแพตช์ล่าสุดถอดข้อจำกัดสกิลเฉพาะตัวของเทมเมอร์ออกทั้งหมด สามารถรับเควส \"เลือกสกิลเทมเมอร์!\" จาก NPC ซาสึมะ ที่ศูนย์บัญชาการ DATS เพื่อเลือกสกิลแอคทีฟ 1 ชนิด และพาสซีฟ 2 ชนิด ไปใส่ให้เทมเมอร์ตัวใดก็ได้",
        "rules": [
            "เลือกสกิลแอคทีฟเฉพาะได้สูงสุด 1 สกิล (จากทั้งหมด 16 สกิล) โดยไม่จำกัดว่าเป็นเทมเมอร์คนใด",
            "เลือกสกิลพาสซีฟเฉพาะได้สูงสุด 2 สกิล (เพิ่มพลังโจมตี +5% หรือ HP +10% ตามคุณสมบัติ Va / Da / Vi / Un)",
            "สกิลเฉพาะเดิมที่ติดตัวเทมเมอร์แต่ละคนถูกลบออก (ส่วนสกิลขั้นสูงสุด และสกิลที่ได้รับการเสริมประสิทธิภาพยังคงอยู่)",
            "พาสซีฟเพิ่มความเร็วในการเคลื่อนที่ (MS) เป็นสกิลติดตัวพื้นฐานของเทมเมอร์ทุกตัว",
            "ทุกสกิลเป็นแบบถาวร ไม่สามารถเรียนซ้ำได้ แต่สามารถกดปุ่ม × ลบออกเพื่อเปลี่ยนสกิลใหม่ได้",
        ],
        "satsuma": {
            "name": "NPC ซาสึมะ",
            "role": "<หัวหน้าหน่วย / ดูแลภารกิจ> ศูนย์บัญชาการ DATS",
            "quest": "เควส: \"เลือกสกิลเทมเมอร์!\"",
            "image": satsuma_img,
            "rewards": [
                {"id": 36000, "name": "กล่องเลือกสกิลแอคทีฟเฉพาะของเทมเมอร์", "qty": 1, "icon": item_icon(36000)},
                {"id": 36002, "name": "กล่องเลือกสกิลพาสซีฟเฉพาะของเทมเมอร์", "qty": 2, "icon": item_icon(36002)},
            ],
        },
        "gekomon": {
            "name": "NPC เกโคมอน",
            "role": "<รับแลกเปลี่ยน> ศูนย์บัญชาการ DATS (ซื้อเปลี่ยน/เพิ่มเติม)",
            "image": gekomon_img,
            "shop": [
                {"id": 36001, "name": "กล่องเลือกสกิลแอคทีฟเฉพาะของเทมเมอร์ [กิจกรรม]", "cost": "10 T", "icon": item_icon(36001)},
                {"id": 36003, "name": "กล่องเลือกสกิลพาสซีฟเฉพาะของเทมเมอร์ [กิจกรรม]", "cost": "6 T", "icon": item_icon(36003)},
                {"id": 36005, "name": "กล่องสุ่มสกิลแอคทีฟเฉพาะของเทมเมอร์ [กิจกรรม]", "cost": "1 T", "icon": item_icon(36005)},
                {"id": 36007, "name": "กล่องสุ่มสกิลพาสซีฟเฉพาะของเทมเมอร์ [กิจกรรม]", "cost": "1 T", "icon": item_icon(36007)},
            ],
        },
        "base_passive": {
            "name": "เพิ่มความเร็วในการเคลื่อนที่",
            "desc": "พาสซีฟพื้นฐานของเทมเมอร์ทุกตัว (แยกต่างหากจากช่องสกิลเฉพาะ)",
            "icon": item_icon(6940),
        },
        "active_skills": active_pool,
        "passive_skills": passive_pool,
    }


def _build_tamer_status(its):
    """Build interactive Thai DMO Tamer Status & 17-Slot Equipment + Chipset guide from CrackDMO."""
    buf_path = CRACK / "out_decrypted/data/bin/table/itemdata.bin"
    itemdata_buf = buf_path.read_bytes() if buf_path.exists() else b""

    # Load item_str.json directly for accurate Thai categories & counts (covers 2-byte aligned items too)
    str_raw = E.load_json(CRACK / "out_json/language/item_str.json")
    cat_counts = {}
    str_map = {}
    for x in str_raw:
        f = x.get("fields", [])
        nm = _clean(f[0] if len(f) > 0 else "").replace("\n", " ")
        cat = f[1] if len(f) > 1 else ""
        desc = _clean(f[2] if len(f) > 2 else "").replace("\n", " ")
        str_map[x["id"]] = {"name": re.sub(r"\s+", " ", nm).strip(), "cat": cat, "desc": desc}
        if cat:
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    def resolve_icon(iid: int) -> str:
        it = its.get(iid)
        if it and it.get("icon_id") and E.save_icon(iid, it["icon_id"]):
            return f"/images/client_items/{iid}.png"
        if itemdata_buf:
            pat = struct.pack("<II", iid, iid)
            pos = itemdata_buf.find(pat)
            while pos != -1:
                if pos + 12 <= len(itemdata_buf):
                    ic = struct.unpack_from("<I", itemdata_buf, pos + 8)[0]
                    if ic and E.save_icon(iid, ic):
                        return f"/images/client_items/{iid}.png"
                pos = itemdata_buf.find(pat, pos + 2)
        return ""

    def mk_items(id_list):
        out = []
        for iid in id_list:
            meta = str_map.get(iid)
            if not meta or not meta["name"]:
                continue
            out.append({
                "id": iid,
                "name": meta["name"],
                "icon": resolve_icon(iid),
            })
        return out

    win_images = {
        "win1": _copy_crack_asset("data/interface/tamerstatus_new/tamerstatus_win_01.png", "status_win_01.png"),
        "win2": _copy_crack_asset("data/interface/tamerstatus_new/tamerstatus_win_02.png", "status_win_02.png"),
        "win3": _copy_crack_asset("data/interface/tamerstatus_new/tamerstatus_win_03.png", "status_win_03.png"),
        "win4": _copy_crack_asset("data/interface/tamerstatus_new/tamerstatus_win_04.png", "status_win_04.png"),
        "preset_bg": _copy_crack_asset("data/interface/Preset/Preset_EquipSlot_bg.png", "preset_equip_bg.png"),
    }

    stone_groups = {
        "hp": {
            "title": "หินเสริมคุณลักษณะ — เสื้อ (HP)",
            "badge": "เจาะรู & ตีบวกค่า HP",
            "examples": mk_items([102, 104, 152547]),
        },
        "df": {
            "title": "หินเสริมคุณลักษณะ — กางเกง (DF/DE)",
            "badge": "เจาะรู & ตีบวกค่า DF",
            "examples": mk_items([501, 503, 152562]),
        },
        "ap": {
            "title": "หินเสริมคุณลักษณะ — ถุงมือ (AP/AT)",
            "badge": "เจาะรู & ตีบวกค่าโจมตี AT/AP",
            "examples": mk_items([302, 304, 152557]),
        },
        "ms": {
            "title": "หินเสริมคุณลักษณะ — รองเท้า (MS)",
            "badge": "เจาะรู & ตีบวกความเร็วเดิน",
            "examples": mk_items([401, 1003, 11020]),
        },
        "ds": {
            "title": "หินเสริมคุณลักษณะ — เครื่องประดับ (DS)",
            "badge": "เจาะรู & ตีบวกค่า DS",
            "examples": mk_items([203, 205, 152552]),
        },
        "acc": {
            "title": "หินปรับแต่งเครื่องประดับ (พลังดิจิทารี่ 200% & สุ่มออฟชั่น)",
            "badge": "4 ช่องหลัก (แหวน / สร้อย / ต่างหู / กำไล)",
            "examples": mk_items([45000, 120007, 45001, 45002, 45003]),
        },
    }

    # Exact pixel boxes (x, y, w, h) verified on 406x676 tamerstatus_win_01.png
    slots = [
        {
            "key": "head",
            "num": 1,
            "tab": 1,
            "rect": [30, 138, 40, 40],
            "side": "ซ้าย (แถว 1)",
            "type_id": 21,
            "preset_label": "หัว",
            "category": "ส่วนหัว",
            "name_th": "หมวก / ส่วนหัว (Head)",
            "name_en": "Headgear",
            "color": "#38bdf8",
            "summary": "หมวกหรือเครื่องสวมศีรษะแฟชั่น เพิ่ม HP / DS / ออฟชั่นเฉพาะชุด",
            "details": "ช่องสวมใส่ส่วนหัวของเทมเมอร์ เช่น หมวกกิจกรรม หมวกอารีน่าคุณสมบัติ หรือหมวกเกราะสปิริต แสดงผลบนตัวละครเมื่อไม่ซ่อนส่วนหัว (แยกจากช่องแว่นนิรภัยด้านขวา)",
            "stats_note": "HP / DS / DE / MS หรือโบนัสพิเศษจากชุดเซ็ต",
            "stone_key": None,
            "total_items": cat_counts.get("ส่วนหัว", 0),
            "examples": mk_items([152211, 151529, 47658, 1601]),
        },
        {
            "key": "goggle",
            "num": 2,
            "tab": 1,
            "rect": [77, 138, 40, 40],
            "side": "ซ้าย (ช่องในแถว 1)",
            "type_id": 36,
            "preset_label": "หมวก (Goggle)",
            "category": "Hat accessory",
            "name_th": "แว่นตา / แว่นนิรภัย (Goggles)",
            "name_en": "Hat Accessory / Goggles",
            "color": "#a855f7",
            "summary": "ช่องเฉพาะสำหรับ แว่นนิรภัยแอดเวนเจอร์ / แว่นตาดิจิมอนไกเซอร์ บวกดาเมจให้เทมเมอร์และดิจิมอน",
            "details": "ช่องพิเศษด้านในแถวบน ใช้ใส่แว่นกอกเกิลหรือแว่นตาดิจิมอนไกเซอร์โดยตรง สามารถอัปเกรดเลเวลและสุ่ม/เปลี่ยนธาตุ [AT/CT/HP/DE] เพื่อส่งผลให้ดิจิมอนคู่หูแข็งแกร่งขึ้นมาก",
            "stats_note": "AT / CT / HP / Skill Damage / EXP (ส่งต่อให้ดิจิมอน)",
            "stone_key": None,
            "total_items": cat_counts.get("Hat accessory", 0),
            "examples": mk_items([47625, 47622, 10545, 10542]),
        },
        {
            "key": "face_acc",
            "num": 3,
            "tab": 1,
            "rect": [30, 184, 40, 40],
            "side": "ซ้าย (แถว 2)",
            "type_id": 27,
            "preset_label": "เครื่องประดับ",
            "category": "เครื่องประดับ",
            "name_th": "เครื่องประดับใบหน้า / หูฟัง / ผ้าคลุม",
            "name_en": "Face / Headphone / Cape Accessory",
            "color": "#34d399",
            "summary": "อุปกรณ์ตกแต่งส่วนหน้า-หลัง เช่น หูฟัง กระเป๋า เสื้อคลุมอารีน่า — ใส่หินเสริม DS ได้",
            "details": "เป็น 1 ใน 5 ชิ้นส่วนชุดอุปกรณ์หลักที่สามารถเสริม 'หินเสริมคุณลักษณะ DS' เพื่อเพิ่มค่า DigiSoul สูงสุดให้เทมเมอร์ มีทั้งแบบแฟชั่นทั่วไปและแบบอารีน่า/กิจกรรมที่มีออฟชั่นสเตตัส",
            "stats_note": "DS (หินคุณลักษณะ) / DE / EXP / HP",
            "stone_key": "ds",
            "total_items": cat_counts.get("เครื่องประดับ", 0),
            "examples": mk_items([152212, 151530, 47360, 61102]),
        },
        {
            "key": "top",
            "num": 4,
            "tab": 1,
            "rect": [30, 230, 40, 40],
            "side": "ซ้าย (แถว 3)",
            "type_id": 22,
            "preset_label": "เสื้อ",
            "category": "เสื้อ",
            "name_th": "เสื้อ (Top / Jacket)",
            "name_en": "Shirt / Jacket",
            "color": "#22c55e",
            "summary": "เสื้อเกราะ/เสื้อแฟชั่นของเทมเมอร์ — ใส่หินเสริมคุณลักษณะ HP ได้",
            "details": "ชิ้นส่วนหลักสำหรับเติมค่าเลือด (HP) ให้ดิจิมอนและเทมเมอร์ผ่านการเจาะรูและตี 'หินเสริมคุณลักษณะ HP ระดับ A/B/C/D' รวมถึงเสื้อฮู้ดอารีน่าคุณสมบัติและเสื้อสมาชิก DATS",
            "stats_note": "HP สูงสุด (หินคุณลักษณะ HP)",
            "stone_key": "hp",
            "total_items": cat_counts.get("เสื้อ", 0),
            "examples": mk_items([152213, 151531, 12041, 2001]),
        },
        {
            "key": "pants",
            "num": 5,
            "tab": 1,
            "rect": [30, 276, 40, 40],
            "side": "ซ้าย (แถว 4)",
            "type_id": 24,
            "preset_label": "กางเกง",
            "category": "กางเกง",
            "name_th": "กางเกง (Bottom / Pants)",
            "name_en": "Pants",
            "color": "#10b981",
            "summary": "กางเกงของเทมเมอร์ — ใส่หินเสริมคุณลักษณะ DF (พลังป้องกัน) ได้",
            "details": "ชิ้นส่วนหลักสำหรับเพิ่มค่าพลังป้องกัน (DF / DE) ให้คู่หูผ่าน 'หินเสริมคุณลักษณะ DF' ช่วยลดดาเมจที่ได้รับในดันเจี้ยนระดับสูง",
            "stats_note": "DF / DE (หินคุณลักษณะ DF)",
            "stone_key": "df",
            "total_items": cat_counts.get("กางเกง", 0),
            "examples": mk_items([152214, 151532, 63004, 3001]),
        },
        {
            "key": "gloves",
            "num": 6,
            "tab": 1,
            "rect": [30, 322, 40, 40],
            "side": "ซ้าย (แถว 5)",
            "type_id": 23,
            "preset_label": "มือ",
            "category": "ถุงมือ",
            "name_th": "ถุงมือ (Gloves)",
            "name_en": "Gloves",
            "color": "#ef4444",
            "summary": "ถุงมือของเทมเมอร์ — ช่องสำคัญที่สุดใน 5 ชิ้นหลักเพราะใส่หินเสริมพลังโจมตี (AP/AT) ได้",
            "details": "ชิ้นส่วนทำดาเมจหลักฝั่งซ้าย! สามารถใส่ 'หินเสริมคุณลักษณะ AP/AT' เพื่อบวกพลังโจมตีพื้นฐานโดยตรงให้ดิจิมอน นอกจากนี้ยังมีถุงมือแรร์อย่างถุงมืออารีน่าหรือถุงมือไบฟูมอนที่บวกสเตตัสสูงมาก",
            "stats_note": "AT / AP (หินคุณลักษณะ AT/AP) + โบนัสถุงมือ",
            "stone_key": "ap",
            "total_items": cat_counts.get("ถุงมือ", 0),
            "examples": mk_items([152216, 75698, 151534, 4101]),
        },
        {
            "key": "shoes",
            "num": 7,
            "tab": 1,
            "rect": [30, 368, 40, 40],
            "side": "ซ้าย (แถว 6)",
            "type_id": 25,
            "preset_label": "รองเท้า",
            "category": "รองเท้า",
            "name_th": "รองเท้า (Shoes)",
            "name_en": "Shoes",
            "color": "#06b6d4",
            "summary": "รองเท้าของเทมเมอร์ — ใส่หินเสริมคุณลักษณะ MS (ความเร็วเคลื่อนที่) ได้",
            "details": "ใช้สวมรองเท้าทั่วไปหรือรองเท้าอารีน่า/สมาชิก DATS โดยเป็นช่องเดียวในชุดเครื่องแต่งกายที่รองรับ 'หินเสริมคุณลักษณะ MS' (+30% ความเร็วเคลื่อนที่จากห้องแล็ป/ทะเลทราย/LvMax)",
            "stats_note": "MS (ความเร็วเคลื่อนที่) / HP",
            "stone_key": "ms",
            "total_items": cat_counts.get("รองเท้า", 0),
            "examples": mk_items([152215, 151533, 4501, 15021]),
        },
        {
            "key": "costume",
            "num": 8,
            "tab": 1,
            "rect": [30, 414, 40, 40],
            "side": "ซ้าย (แถว 7 ล่างสุด)",
            "type_id": 26,
            "preset_label": "คอสตูม",
            "category": "ชุดคอสทูม",
            "name_th": "ชุดคอสตูม (Costume Set)",
            "name_en": "Full Costume",
            "color": "#ec4899",
            "summary": "ชุดแฟชั่นเต็มตัว (ครอบทับรูปลักษณ์เสื้อ/กางเกง/รองเท้า) พร้อมออฟชั่น AT / HP / SCD",
            "details": "ช่องใส่ชุดคอสตูมแบบเต็มตัว เช่น ชุดไกเซอร์ ชุดตัวละครเฉพาะ หรือชุดเทศกาล หลายชุดมีค่าสถานะพิเศษติดตัว เช่น AT +200~300, HP +1000 หรือลดคูลดาวน์สกิล (SCD) และความเร็ววิ่ง (MS)",
            "stats_note": "MS / AT / HP / EXP / Skill Cooldown (SCD)",
            "stone_key": None,
            "total_items": cat_counts.get("ชุดคอสทูม", 0),
            "examples": mk_items([181201, 181199, 180018, 180489]),
        },
        {
            "key": "nameplate",
            "num": 9,
            "tab": 1,
            "rect": [77, 414, 40, 40],
            "side": "ซ้าย (ช่องในแถว 7)",
            "type_id": 34,
            "preset_label": "ไอเทมป้ายชื่อ",
            "category": "NamePlate Item",
            "name_th": "ป้ายชื่อ / แมกเนติก ID Card",
            "name_en": "Magnetic ID Card / NamePlate",
            "color": "#f472b6",
            "summary": "บัตรประจำตัวเทมเมอร์ แสดงกรอบชื่อบนหัวในเมือง พร้อมบัฟ AT / HP / HT / CT / EXP",
            "details": "ช่องสำหรับ 'แมกเนติก ID Card' หรือ 'ID Card ระดับไฮโซ' เปลี่ยนกรอบป้ายชื่อและสัญลักษณ์ข้างชื่อเทมเมอร์ อีกทั้งการ์ดระดับสูงมักแถมค่าสถานะ [AT] / [HP] / [CT] / [HT] หรือ [EXP] เพิ่มให้ดิจิมอนตลอดเวลาที่สวมใส่",
            "stats_note": "AT / HP / HT / CT / EXP + กรอบป้ายชื่อเฉพาะตัว",
            "stone_key": None,
            "total_items": cat_counts.get("NamePlate Item", 0),
            "examples": mk_items([181181, 180977, 180518, 39296]),
        },
        {
            "key": "earring",
            "num": 10,
            "tab": 1,
            "rect": [336, 138, 40, 40],
            "side": "ขวา (แถว 1)",
            "type_id": 30,
            "preset_label": "ต่างหู (ไฟล์เกมเขียนผิดเป็น 'สร้อยคอ')",
            "category": "ต่างหู",
            "name_th": "ต่างหู (Earring)",
            "name_en": "Earring",
            "color": "#f59e0b",
            "summary": "เครื่องประดับหลัก 1 ใน 4 ชิ้น (ใส่ได้สูงสุด 4 ออฟชั่น เช่น CD / HT / AT / HP)",
            "details": "เครื่องประดับสำคัญระดับ Endgame เช่น ต่างหูควอดคอร์ ต่างหูแห่งปาฏิหาริย์ หรือต่างหูศักดิ์สิทธิ์ของฟานลองมอน สามารถใช้ 'หินพลังดิจิทารี่' ดันพลังเป็น 200% และสุ่มออฟชั่น Critical Damage (CD), Hit Rate (HT), Attack (AT) หรือ Skill Damage (SK) ได้ (*หมายเหตุ: ในหน้าต่างพรีเซ็ตภาษาไทย ID 30 แปลคำว่า Earring สลับเป็น 'สร้อยคอ' แต่ช่องจริงคือต่างหู)",
            "stats_note": "CD / HT / AT / HP / DE / BL (สูงสุด 200%)",
            "stone_key": "acc",
            "total_items": cat_counts.get("ต่างหู", 0),
            "examples": mk_items([75544, 46988, 151752, 6561]),
        },
        {
            "key": "necklace",
            "num": 11,
            "tab": 1,
            "rect": [336, 184, 40, 40],
            "side": "ขวา (แถว 2)",
            "type_id": 28,
            "preset_label": "สร้อย",
            "category": "สร้อยคอ",
            "name_th": "สร้อยคอ (Necklace)",
            "name_en": "Necklace",
            "color": "#fbbf24",
            "summary": "เครื่องประดับหลักเพิ่ม AS (Attack Speed) + CD / AT / SK (สูงสุด 4 ออฟชั่น)",
            "details": "ช่องสร้อยคอคือแหล่งหลักในการหาค่า AS (Attack Speed ลดหน่วงตีปกติ) และ Critical Damage (CD) ของเกม DMO เช่น สร้อยแห่งอนันต์ สร้อยไทรคอร์พลังสูง สร้อยของไบฟูมอน และสร้อยศักดิ์สิทธิ์ฟานลองมอน ใช้หินพลังดิจิทารี่ดันได้ถึง 200%",
            "stats_note": "AS (ตีไว) / CD / AT / HP / DS / SK",
            "stone_key": "acc",
            "total_items": cat_counts.get("สร้อยคอ", 0),
            "examples": mk_items([75531, 47096, 47059, 47038]),
        },
        {
            "key": "bracelet",
            "num": 12,
            "tab": 1,
            "rect": [336, 230, 40, 40],
            "side": "ขวา (แถว 3)",
            "type_id": 33,
            "preset_label": "กำไล",
            "category": "Bracelet",
            "name_th": "กำไลข้อมือ (Bracelet)",
            "name_en": "Bracelet",
            "color": "#fb923c",
            "summary": "เครื่องประดับ Endgame ที่ใส่ได้ถึง 5 ออฟชั่น (กำไลรอยัล:ไนท์ / ปาฏิหาริย์ / ซีโร่ยูนิต)",
            "details": "เป็นเครื่องประดับที่เพิ่มพลังให้ดิจิมอนมากที่สุดชิ้นหนึ่ง เพราะกำไลระดับสูงอย่าง 'กำไลของ รอยัล:ไนท์', 'กำไลแห่งปาฏิหาริย์' หรือ 'กำไลซีโร่ยูนิต' มีช่องออฟชั่นสูงสุดถึง 5 แถว (เช่น CD / CD / AT / HT / HT) ปั้นพลัง 200% ด้วยหินพลังดิจิทารี่ได้",
            "stats_note": "CD / AT / HT / CT / HP / DE (สูงสุด 5 ออฟชั่นที่ 200%)",
            "stone_key": "acc",
            "total_items": cat_counts.get("Bracelet", 0),
            "examples": mk_items([47214, 45057, 47228, 151749]),
        },
        {
            "key": "ring",
            "num": 13,
            "tab": 1,
            "rect": [336, 276, 40, 40],
            "side": "ขวา (แถว 4)",
            "type_id": 29,
            "preset_label": "แหวน",
            "category": "แหวน",
            "name_th": "แหวน (Ring)",
            "name_en": "Ring",
            "color": "#f97316",
            "summary": "เครื่องประดับหลัก 4 ออฟชั่น (เช่น AT / AT / SK / HP) สำหรับเริ่มต้นถึง Endgame",
            "details": "ช่องสวมแหวน เช่น แหวนแห่งอนันต์ แหวนควอดคอร์ แหวนไบฟูมอน แหวนปาฏิหาริย์ และแหวนศักดิ์สิทธิ์ฟานลองมอน ใช้หินพลังดิจิทารี่ดันค่าออฟชั่นได้ถึง 200% โดยนิยมรีหาออฟ AT + AT + Skill Damage (SK) หรือ HP/CT",
            "stats_note": "AT / SK / HP / CT / Attribute Damage",
            "stone_key": "acc",
            "total_items": cat_counts.get("แหวน", 0),
            "examples": mk_items([75522, 47094, 45014, 47012]),
        },
        {
            "key": "aura",
            "num": 14,
            "tab": 1,
            "rect": [336, 322, 40, 40],
            "side": "ขวา (แถว 5)",
            "type_id": 31,
            "preset_label": "ออร่า",
            "category": "Aura",
            "name_th": "ดิจิออร่า / แกนพลังงาน (Digiaura)",
            "name_en": "Digiaura / Jogress Aura",
            "color": "#eab308",
            "summary": "ไอเทมเปิดระบบออโต้/บัฟพื้นฐานสำคัญ ลดการกิน DS จาก Jogress และเพิ่มสเตตัส",
            "details": "ช่องใส่ 'ดิจิออร่า' หรือ 'แกนพลังงาน' เมื่อเปิดใช้งานจะมีออร่ารอบตัวดิจิมอน ช่วยปลดล็อกฟังก์ชันเสริมบางประเภท (เช่น ลดการสิ้นเปลือง DS / เปิดระบบดูดของหรือเอฟเฟกต์พิเศษตามเวอร์ชันออร่า) และดิจิออร่าระดับสูงอย่าง 'ดิจิออร่าแห่งความกล้าหาญและมิตรภาพ' ยังเพิ่ม AT / HP / SK อย่างมาก",
            "stats_note": "AT / HP / DS / Skill Damage + เอฟเฟกต์ออร่ารอบดิจิมอน",
            "stone_key": None,
            "total_items": cat_counts.get("Aura", 0),
            "examples": mk_items([47535, 6107, 5125, 181220]),
        },
        {
            "key": "digivice",
            "num": 15,
            "tab": 1,
            "rect": [336, 368, 40, 40],
            "side": "ขวา (แถว 6)",
            "type_id": 53,
            "preset_label": "ดิจิไวซ์",
            "category": "ดิจิไวซ์",
            "name_th": "ดิจิไวซ์ (Digivice)",
            "name_en": "Digivice",
            "color": "#3b82f6",
            "summary": "แกนหลักในการปลดล็อกช่องใส่ 'ชิปเซ็ท' และบวกพลังโจมตีธาตุ / เผ่าพันธุ์ของดิจิมอน",
            "details": "อุปกรณ์คู่กายเทมเมอร์ เริ่มจาก D-Arc/D-Scanner ทั่วไป ไปจนถึง 'ดิจิไวซ์ที่แท้จริงแห่งความรู้/ความกล้าหาญ' (True Digivice) หรือ 'ดาร์กเนส โหลดเดอร์' ยิ่งดิจิไวซ์ระดับสูงยิ่งมีจำนวนช่อง 'ชิปเซ็ท' (สูงสุด 8 ช่องในแท็บที่ 2) และออฟชั่นธาตุ/ตระกูล (Va/Vi/Da + แสง/ไฟ/มืด/ลม ฯลฯ) สูงมาก คลิกแท็บ 'ชิปเซ็ท (Tab 2)' ด้านบนเพื่อดูผังช่องชิปเซ็ทภายในดิจิไวซ์ได้เลย",
            "stats_note": "จำนวนช่องชิปเซ็ท (2–8 ช่อง) + โบนัส Attribute & Element Damage %",
            "stone_key": None,
            "total_items": cat_counts.get("ดิจิไวซ์", 0),
            "examples": mk_items([47457, 76050, 47487, 47267]),
        },
        {
            "key": "keyring",
            "num": 16,
            "tab": 1,
            "rect": [288, 414, 40, 40],
            "side": "ขวา (ช่องในแถว 7)",
            "type_id": 35,
            "preset_label": "คีย์ริง",
            "category": "Key Ring",
            "name_th": "คีย์ริง (Key Ring)",
            "name_en": "Key Ring / Spiral Key Ring",
            "color": "#8b5cf6",
            "summary": "พวงกุญแจเสริมดาเมจตาม 'ตระกูล (Family)' เช่น VB / DS / DR / UK / ME / NS",
            "details": "อุปกรณ์เสริมที่เน้นเพิ่ม Skill Damage / Attack / HP ให้ดิจิมอนที่อยู่ใน Family ตรงกับคีย์ริง (เช่น สไปรอลคีย์ริง [DS], [DR], [UK] หรือ โกสท์คีย์ริง [DA]) มักใช้สลับตามตระกูลของดิจิมอนตัวหลักที่กำลังลงดันเจี้ยน",
            "stats_note": "โบนัส AT / Skill Damage / HP เฉพาะ Family หรือ Attribute",
            "stone_key": None,
            "total_items": cat_counts.get("Key Ring", 0),
            "examples": mk_items([47425, 144107, 144504, 151477]),
        },
        {
            "key": "xai",
            "num": 17,
            "tab": 1,
            "rect": [336, 414, 40, 40],
            "side": "ขวา (แถว 7 มุมล่างขวา)",
            "type_id": 32,
            "preset_label": "ระบบXAI",
            "category": "XAI system",
            "name_th": "ระบบ XAI (X-Antibody Indicator)",
            "name_en": "XAI System",
            "color": "#ef4444",
            "summary": "ไอเทมบังคับสำหรับการแปลงร่าง X-Antibody และเกจ X-Gauge ที่จำเป็น",
            "details": "หากต้องการพัฒนาร่างดิจิมอนสาย X-Antibody (เช่น Alphamon Ouryuken X, Omegamon X, Jesmon X) จำเป็นต้องสวมใส่ XAI (Ver II / III / IV / V ฯลฯ) เพื่อเก็บและใช้ 'X-Gauge' ตามที่ร่าง X-Evolution ต้องการ ยิ่งเวอร์ชันสูงจะให้เกจสูงสุดเยอะขึ้น",
            "stats_note": "เพิ่มความจุ X-Gauge + ปลดล็อก X-Evolution (บางรุ่นมีโบนัสสเตตัส)",
            "stone_key": None,
            "total_items": cat_counts.get("XAI system", 0),
            "examples": mk_items([40034, 40020, 40015, 40094]),
        },
    ]

    # Compose clean blank Tab 2 window with 8 hexagon partner slots + 2 center Jogress/Xros chip slots + 8 bottom Chipsets
    from PIL import Image
    ts_dir = CRACK / "out_images/data/interface/tamerstatus_new"
    TAMER_IMG_OUT.mkdir(parents=True, exist_ok=True)
    hex_centers = [
        (54, 118), (94, 215), (54, 312), (94, 410),
        (352, 118), (312, 215), (352, 312), (312, 410),
    ]
    evo_chip_centers = [(203, 326), (203, 420)]
    if (ts_dir / "tamerstatus_win_02.png").exists() and (ts_dir / "tamerstatus_digimon_disable.png").exists() and (ts_dir / "tamerstatus_win_04.png").exists():
        w2_base = Image.open(ts_dir / "tamerstatus_win_02.png").convert("RGBA")
        w4_src = Image.open(ts_dir / "tamerstatus_win_04.png").convert("RGBA")
        hex_img = Image.open(ts_dir / "tamerstatus_digimon_disable.png").convert("RGBA").resize((84, 88), Image.Resampling.LANCZOS)
        empty_sq = w4_src.crop((34, 337, 72, 375)).resize((40, 40), Image.Resampling.LANCZOS)
        for cx, cy in hex_centers:
            w2_base.paste(hex_img, (cx - 42, cy - 44), hex_img)
        for cx, cy in evo_chip_centers:
            w2_base.paste(empty_sq, (cx - 20, cy - 20), empty_sq)
        w2_base.save(TAMER_IMG_OUT / "status_win_02_comp.png")
        win_images["win2"] = "/images/tamers/status_win_02_comp.png"

    # Tab 2 Part A: 8 Hexagon Digimon Partner / Mercenary Storage Slots (blank slots)
    digimon_slots = {
        "key": "digimon_storage_8",
        "num": 18,
        "tab": 2,
        "rects": [[cx - 38, cy - 40, 76, 80] for cx, cy in hex_centers],
        "side": "แท็บ 2 — ช่องเก็บดิจิมอนพกพา (8 ช่องหกเหลี่ยม D1–D8)",
        "type_id": 0,
        "category": "ช่องเก็บดิจิมอนพกพา (Partner / Mercenary Slots)",
        "name_th": "ช่องเก็บดิจิมอนพกพาทั้ง 8 ช่อง (D1–D8)",
        "name_en": "Digimon Partner Storage Slots (8 Hex Slots)",
        "color": "#38bdf8",
        "summary": "ช่องเก็บดิจิมอนที่พกติดตัวไว้สลับเล่นสูงสุด 8 ตัว (คลิกขวาเลือก เปลี่ยนพาร์ทเนอร์ / ลบ)",
        "details": "ช่องหกเหลี่ยมทั้ง 8 ช่อง (ฝั่งซ้าย 4 ช่อง + ฝั่งขวา 4 ช่อง) มีไว้สำหรับเก็บดิจิมอนที่ฟักและเลี้ยงไว้พกติดตัวไปได้ทุกแผนที่ สามารถคลิกขวาที่ช่องเพื่อกด 'เปลี่ยนพาร์ทเนอร์' สลับนำออกมาเป็นตัวหลักได้ทันที หรือใช้เป็นตัวตั้ง/ตัวรองในการแปลงร่าง Jogress และ DigiXros (ช่วงเริ่มต้นจะเปิดให้ใช้บางช่อง และขยายเพิ่มได้สูงสุดครบ 8 ช่อง)",
        "stats_note": "เก็บดิจิมอนติดตัวสูงสุด 8 ช่อง · สลับพาร์ทเนอร์นอกการต่อสู้ · เป็นเงื่อนไขคู่ผสม Jogress / DigiXros",
        "stone_key": None,
        "total_items": 8,
    }

    # Tab 2 Part B: 2 Center Evo Chip Slots (Jogress / DigiXros ONLY — separate from bottom 8 Chipsets!)
    evo_chip_slots = {
        "key": "evo_chip_2",
        "num": 19,
        "tab": 2,
        "rects": [[cx - 20, cy - 20, 40, 40] for cx, cy in evo_chip_centers],
        "side": "แท็บ 2 — ช่องชิปแปลงร่างตรงกลาง (2 ช่อง J1–J2)",
        "type_id": 52,
        "category": "ชิพโจเกรส / ดิจิครอสชิป (แปลงร่างเท่านั้น)",
        "name_th": "ช่องใส่ชิพโจเกรส / ดิจิครอสชิป (2 ช่องตรงกลาง)",
        "name_en": "Jogress Chip & DigiXros Chip Slots",
        "color": "#f59e0b",
        "summary": "2 ช่องสี่เหลี่ยมตรงกลางสำหรับใส่ ชิพโจเกรส / ดิจิครอสชิป เพื่อแปลงร่างเท่านั้น ไม่เกี่ยวกับชิปเซ็ท 8 ช่องด้านล่าง",
        "details": "ช่องสี่เหลี่ยม 2 ช่องที่วางเรียงแนวตั้งตรงกลางหน้าต่าง (ช่องบน J1 / ช่องล่าง J2) เอาไว้สำหรับสวมใส่ 'ชิพโจเกรส (Jogress Chip)' หรือ 'ดิจิครอสชิป (DigiXros Chip)' เพื่อปลดล็อกและกดแปลงร่างรวมร่างดิจิมอนโดยเฉพาะ ไม่มีส่วนเกี่ยวข้องกับการเพิ่มค่าสเตตัสของช่องชิปเซ็ท 8 ช่องด้านล่างเลย",
        "stats_note": "ใช้สำหรับแปลงร่าง Jogress / DigiXros Evolution เท่านั้น (ไม่บวกสเตตัสแบบชิปเซ็ท)",
        "stone_key": None,
        "total_items": 2,
    }

    # Tab 2 Part C: Bottom 8 Chipset IC Slots (y=543 & y=603)
    chipset_slot = {
        "key": "chipset",
        "num": 20,
        "tab": 2,
        "rects": [
            [34, 543, 38, 38], [134, 543, 38, 38], [234, 543, 38, 38], [334, 543, 38, 38],
            [34, 603, 38, 38], [134, 603, 38, 38], [234, 603, 38, 38], [334, 603, 38, 38],
        ],
        "side": "แท็บ 2 — แผงชิปเซ็ทด้านล่าง (8 ช่อง C1–C8)",
        "type_id": 52,
        "preset_label": "ชิปเซ็ท",
        "category": "ชิปเซ็ทเพิ่มค่าสเตตัส (Chipset)",
        "name_th": "ช่องใส่ชิปเซ็ท 8 ช่องด้านล่าง (C1–C8)",
        "name_en": "Digivice Chipset Slots",
        "color": "#06b6d4",
        "summary": "แผงใส่ชิปเซ็ทเพิ่มค่าสเตตัส 8 ช่อง (คนละส่วนกับช่องชิพโจเกรส/ดิจิครอสตรงกลาง)",
        "details": "แผงชิปเซ็ท 8 ช่องด้านล่างสุดของหน้าต่าง (แถวบน C1–C4, แถวล่าง C5–C8) ใช้สำหรับใส่ชิปเซ็ทเพิ่มค่าสเตตัสโดยตรง เช่น AT / HT / CT / HP / DE หรือดับเบิลชิปเซ็ท (จำนวนช่องที่ใช้งานได้ขึ้นอยู่กับระดับดิจิไวซ์ที่ใส่ในแท็บ 1 ช่อง #15) — แยกจากช่องชิพโจเกรส / ดิจิครอส 2 ช่องตรงกลางชัดเจน",
        "stats_note": "AT / HT / CT / HP / DE / EV (จำนวนช่องเปิดขึ้นกับระดับดิจิไวซ์)",
        "stone_key": None,
        "total_items": cat_counts.get("ชิปเซ็ท", 0),
        "examples": [],
    }

    # Slice Basic Skill + Base Passive icons from CrackDMO sicon01.png (32x32 grid, 16 cols)
    sicon_src = CRACK / "out_images/data/interface/icon/sicon01.png"
    sicon_atlas = Image.open(sicon_src).convert("RGBA") if sicon_src.exists() else None

    def slice_sicon(cell_idx: int, dest_name: str) -> str:
        if sicon_atlas is None:
            return ""
        r, c = divmod(cell_idx, 16)
        box = (c * 32, r * 32, c * 32 + 32, r * 32 + 32)
        if box[2] > sicon_atlas.width or box[3] > sicon_atlas.height:
            return ""
        dest = TAMER_IMG_OUT / dest_name
        if not dest.exists():
            sicon_atlas.crop(box).save(dest)
        return f"/images/tamers/{dest_name}"

    # Remove stale basic_partner_*.png if previously generated so swap slots stay genuinely blank
    for old_f in TAMER_IMG_OUT.glob("basic_partner_*.png"):
        try:
            old_f.unlink()
        except OSError:
            pass

    # Basic Tamer Skills: 4 command skills + 5 BLANK partner swap slots + AFK mode
    basic_skills = [
        {"key": "b1_wait", "code": 1000001, "rect": [34, 131, 38, 38], "name_th": "รออยู่กับที่ (Standby / Wait)", "name_en": "Tamer Standby", "icon": slice_sicon(0, "basic_wait.png"), "desc": "สั่งให้ดิจิมอนคู่หูหยุดรออยู่กับที่ ไม่เดินตามและไม่เข้าไปโจมตีจนกว่าจะเรียก"},
        {"key": "b2_follow", "code": 1000002, "rect": [94, 131, 38, 38], "name_th": "เดินตามเทมเมอร์ (Follow)", "name_en": "Tamer Follow", "icon": slice_sicon(1, "basic_follow.png"), "desc": "เป่านกหวีดเรียกให้ดิจิมอนคู่หูหยุดการกระทำแล้วเดินตามเทมเมอร์กลับมาที่เดิม"},
        {"key": "b3_attack", "code": 1000003, "rect": [154, 131, 38, 38], "name_th": "สั่งโจมตี (Attack)", "name_en": "Normal Attack", "icon": slice_sicon(2, "basic_attack.png"), "desc": "สั่งให้ดิจิมอนคู่หูวิ่งเข้าไปโจมตีธรรมดาใส่ศัตรูที่ล็อกเป้าหมายไว้"},
        {"key": "b4_pickup", "code": 1000004, "rect": [214, 131, 38, 38], "name_th": "เก็บไอเทม (Pick Up)", "name_en": "Pick Up Item", "icon": slice_sicon(19, "basic_pickup.png"), "desc": "สั่งให้เก็บไอเทมหรือกล่องดรอปจากมอนสเตอร์บนพื้นรอบตัว"},
        {"key": "s1_swap", "code": 1000005, "rect": [274, 131, 38, 38], "badge": "S1", "is_blank_swap": True, "name_th": "ช่องเปลี่ยนดิจิมอนที่ 1 (ช่องว่าง)", "name_en": "Swap Slot 1", "icon": "", "desc": "ปุ่มลัดเปลี่ยนดิจิมอนตัวหลักเป็นดิจิมอนที่อยู่ในช่องเก็บที่ 1 (ลากวางลงช่องคีย์ลัดได้ ใช้นอกการต่อสู้)"},
        {"key": "s2_swap", "code": 1000006, "rect": [334, 131, 38, 38], "badge": "S2", "is_blank_swap": True, "name_th": "ช่องเปลี่ยนดิจิมอนที่ 2 (ช่องว่าง)", "name_en": "Swap Slot 2", "icon": "", "desc": "ปุ่มลัดเปลี่ยนดิจิมอนตัวหลักเป็นดิจิมอนที่อยู่ในช่องเก็บที่ 2 (ลากวางลงช่องคีย์ลัดได้)"},
        {"key": "s3_swap", "code": 1000008, "rect": [34, 191, 38, 38], "badge": "S3", "is_blank_swap": True, "name_th": "ช่องเปลี่ยนดิจิมอนที่ 3 (ช่องว่าง)", "name_en": "Swap Slot 3", "icon": "", "desc": "ปุ่มลัดเปลี่ยนดิจิมอนตัวหลักเป็นดิจิมอนที่อยู่ในช่องเก็บที่ 3"},
        {"key": "s4_swap", "code": 1000009, "rect": [94, 191, 38, 38], "badge": "S4", "is_blank_swap": True, "name_th": "ช่องเปลี่ยนดิจิมอนที่ 4 (ช่องว่าง)", "name_en": "Swap Slot 4", "icon": "", "desc": "ปุ่มลัดเปลี่ยนดิจิมอนตัวหลักเป็นดิจิมอนที่อยู่ในช่องเก็บที่ 4 (เมื่อปลดล็อกช่องแล้ว)"},
        {"key": "s5_swap", "code": 1000010, "rect": [154, 191, 38, 38], "badge": "S5", "is_blank_swap": True, "name_th": "ช่องเปลี่ยนดิจิมอนที่ 5 (ช่องว่าง)", "name_en": "Swap Slot 5", "icon": "", "desc": "ปุ่มลัดเปลี่ยนดิจิมอนตัวหลักเป็นดิจิมอนที่อยู่ในช่องเก็บที่ 5 (เมื่อปลดล็อกช่องขยายครบ)"},
        {"key": "b9_afk", "code": 1000007, "rect": [214, 191, 38, 38], "badge": "AFK", "name_th": "โหมดไม่อยู่หน้าจอ (AFK / Away)", "name_en": "Away Mode", "icon": slice_sicon(21, "basic_afk.png"), "desc": "ตั้งสถานะเทมเมอร์เป็นไม่อยู่หน้าจอ (AFK) เพื่อแจ้งผู้เล่นอื่นในแผนที่"},
    ]

    skill_tab = {
        "basic_skills": basic_skills,
        "active_section": {
            "key": "tamer_active_slot",
            "rects": [[34, 337, 38, 38]],
            "title": "สกิลใช้งาน (Active Skill — สูงสุด 1 สกิล)",
            "desc": "แถวกลางของแท็บสกิล ใช้ติดตั้งสกิลกดใช้ (Active) ประจำตัวเทมเมอร์ เช่น บ้าเลือด / อวยพร / หยั่งรู้ (ถอด/เปลี่ยนได้ด้วยกล่องสกิลจาก NPC ซาสึมะ)",
        },
        "passive_section": {
            "key": "tamer_passive_slot",
            "rects": [[34, 543, 38, 38]],
            "base_icon": slice_sicon(16, "basic_passive_ms.png"),
            "title": "สกิลติดตัว (Passive Skill — พื้นฐาน + สูงสุด 2 พาสซีฟ)",
            "desc": "แถวล่างประกอบด้วย P1 สกิลติดตัวพื้นฐาน (รองเท้าปีก: เพิ่มความเร็วในการเคลื่อนที่ให้เทมเมอร์ทุกตัวอัตโนมัติ) และช่องใส่สกิลติดตัวเฉพาะ (Va / Da / Vi / Un) ได้สูงสุด 2 ชนิด",
        },
    }

    friendship_orb = {
        "key": "friendship_orb",
        "num": "สนิท",
        "tab": 1,
        "rect": [173, 515, 60, 60],
        "side": "กลางล่าง — แถบค่าความสนิทสนม (ซ้าย) / ค่าความสามารถเพิ่มเติม (ขวา)",
        "type_id": None,
        "preset_label": "ความสนิท",
        "category": "ค่าความสนิทสนม (Friendship / Intimacy)",
        "name_th": "ค่าความสนิทสนม (ลูกแก้วทาเนมอน)",
        "name_en": "Tamer-Digimon Friendship Orb",
        "color": "#22c55e",
        "summary": "ยิ่งค่าความสนิทสนมมาก ยิ่งทำให้ดิจิมอนคู่หูมีค่าพลังแข็งแกร่งขึ้น (เพิ่มสูงสุด 35 / หรือ 60 เมื่อใช้ไอเทมเฉพาะ)",
        "details": (
            "เทมเมอร์และดิจิมอนที่ผจญภัยมาด้วยกันย่อมก่อเกิดความผูกพันขึ้นมา — หากมีค่าความสนิทที่มากขึ้น จะทำให้ดิจิมอนคู่หูมีค่าพลังที่แข็งแกร่งขึ้น\n\n"
            "[เงื่อนไขการเพิ่มและลดค่าความสนิท]\n"
            "• ทุกๆ 2 นาที เมื่ออยู่ระหว่างการต่อสู้ : ค่าความสนิทเพิ่มขึ้น 1 หน่วย\n"
            "• ทุกๆ 5 นาที เมื่อไม่ได้อยู่ระหว่างการต่อสู้ : ค่าความสนิทลดลง 5 หน่วย\n"
            "• หากพ่ายแพ้การต่อสู้ : ค่าความสนิทจะกลับมาเป็นค่าเริ่มต้น\n"
            "• ค่าความสนิทต่ำสุดและค่าสูงสุดจะเพิ่มขึ้นตามระดับ (Level) ของดิจิมอน\n"
            "• เพิ่มได้สูงสุดจากการนำไปต่อสู้หรือใช้ไอเทมทั่วไปได้ 35 หน่วย\n"
            "• หากใช้คู่กับไอเทมบางชนิด จะสามารถเพิ่มค่าความสนิทได้สูงสุด 60 หน่วย\n\n"
            "(ฝั่งซ้ายใต้แถบเหลืองแสดงตัวเลข 'ค่าความสนิทสนม' และฝั่งขวาใต้แถบเขียวคือ 'ค่าความสามารถเพิ่มเติม' AT / DE / HP / DS ที่บวกเพิ่มจากของสวมใส่และบัฟ)"
        ),
        "stats_note": "เพิ่มปกติสูงสุด 35 หน่วย (ใช้คู่ไอเทมเฉพาะได้สูงสุด 60 หน่วย) — ยิ่งสูง ดิจิมอนคู่หูยิ่งแข็งแกร่งขึ้น",
        "stone_key": None,
        "total_items": 0,
    }

    win_tabs = [
        {"id": 1, "label": "1. สเตตัส & ช่องอุปกรณ์ (17 ช่อง)", "img": win_images["win1"]},
        {"id": 2, "label": "2. ช่องเก็บดิจิมอน · ชิพ · ชิปเซ็ท", "img": win_images["win2"]},
        {"id": 3, "label": "3. สกิลเทมเมอร์ (Basic · Active · Passive)", "img": win_images["win3"]},
    ]

    return {
        "canvas": {"w": 406, "h": 676},
        "win_images": win_images,
        "win_tabs": win_tabs,
        "slots": slots,
        "friendship_orb": friendship_orb,
        "digimon_slots": digimon_slots,
        "evo_chip_slots": evo_chip_slots,
        "chipset_slot": chipset_slot,
        "skill_tab": skill_tab,
        "stones": stone_groups,
    }


def build():
    """Build all 21 Tamer profiles + Thai Patch 25300 skill system from CrackDMO tables (or load cache)."""
    if not CRACK.exists():
        if CACHE_FILE.exists():
            raw = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return raw
            return {"tamers": raw, "skill_system": {}, "tamer_status": {}}
        return {"tamers": [], "skill_system": {}, "tamer_status": {}}
    tamer_str = {x["id"]: x.get("fields", []) for x in E.load_json(CRACK / "out_json/language/tamer_str.json")}
    skill_str = {x["id"]: x.get("fields", []) for x in E.load_json(CRACK / "out_json/language/skill_str.json")}
    buff_str = {x["id"]: x.get("fields", []) for x in E.load_json(CRACK / "out_json/language/buff_str.json")}
    its = E.items()
    E.ICON_OUT.mkdir(parents=True, exist_ok=True)

    createlist = _parse_createlist()
    stats_map = _parse_stats()
    skills_by_pref, upgrades_by_base = _parse_tamerskills(skill_str, buff_str)
    images = _find_tamer_images()
    pack_cnt = _pack01_counts()

    # Pre-copy skill icons keyed by base skill name
    skill_icon_url = {}
    for base_name, iid in SKILL_ICON_ITEM.items():
        it = its.get(iid)
        if it and E.save_icon(iid, it["icon_id"]):
            skill_icon_url[base_name] = f"/images/client_items/{iid}.png"

    # Collect unlock / change items & Magnetic ID Cards per tamer from item_str/itemdata
    unlock_items = {tid: [] for tid in range(80001, 80022)}
    id_cards = {tid: [] for tid in range(80001, 80022)}
    match_tokens = {
        80001: ["มาซารุ"], 80002: ["โทม่า"], 80003: ["โยชิโนะ"], 80004: ["อิคุโตะ"],
        80005: ["ไทจิ"], 80006: ["มีมี่"], 80007: ["ยามาโตะ"], 80008: ["ทาเครุ"],
        80009: ["ฮิคาริ"], 80010: ["โซระ"], 80011: ["ทาคาโตะ"], 80012: ["รูคิ"],
        80013: ["เจินเรีย"], 80014: ["โคจิโร่"], 80015: ["[โจ]", "(โจ)", "ของโจ", "ของ โจ"],
        80016: ["จูริ"], 80017: ["เรียว"],
        80018: ["ฮิโระ"], 80019: ["รูริ"], 80020: ["คิโยชิโร่"], 80021: ["ไกเซอร์"],
    }
    seen_unlock = set()
    seen_card = set()
    for iid, it in sorted(its.items()):
        nm = _clean(it["name"]).replace("\n", " ").replace("\xa0", " ")
        nm = re.sub(r"\s+", " ", nm).strip()
        kind = it.get("kind", "")
        is_unlock = ("เปลี่ยนตัวเทมเมอร์" in nm) or (nm.startswith("แพ็คเกจ") and "การ์ด" not in nm and "แมกเนติก" not in nm)
        is_card = ("แมกเนติก ID Card" in nm) and not nm.startswith("กล่อง")
        if not is_unlock and not is_card:
            continue
        for tid, toks in match_tokens.items():
            if any(tok in nm for tok in toks):
                icon_url = f"/images/client_items/{iid}.png" if E.save_icon(iid, it["icon_id"]) else ""
                if is_unlock:
                    # Deduplicate identical unlock item names per tamer (e.g. legacy + cash duplicate IDs)
                    dkey = (tid, nm)
                    if dkey in seen_unlock:
                        break
                    seen_unlock.add(dkey)
                    tag = "แพ็คเกจ" if "แพ็คเกจ" in nm else "ไอเทมเปลี่ยนตัว"
                    unlock_items[tid].append({
                        "id": iid,
                        "name": nm,
                        "kind": tag,
                        "raw_kind": kind,
                        "icon": icon_url,
                        "event": "[กิจกรรม]" in nm,
                    })
                elif is_card:
                    # Group ID cards by cleaned series name (strip stat tag & duration so list stays tidy)
                    base_card = re.sub(r"\s*\[(?:AT|EXP|HP|HT|CT|EV|DE|กิจกรรม|\d+\s*วัน)\]", "", nm).strip()
                    ckey = (tid, base_card)
                    if ckey in seen_card:
                        break
                    seen_card.add(ckey)
                    id_cards[tid].append({
                        "id": iid,
                        "name": base_card,
                        "icon": icon_url,
                    })
                break

    tamers = []
    for tid in sorted(tamer_str.keys()):
        f = tamer_str[tid]
        name_th = _clean(f[0] if f else "")
        bio = _clean(f[1] if len(f) > 1 else "")
        series_raw = _clean(f[2] if len(f) > 2 else "")
        gender_raw = _clean(f[3] if len(f) > 3 else "")
        series_th = SERIES_TH.get(series_raw, series_raw)
        series_en = SERIES_EN.get(series_th, series_th)
        gender_th = GENDER_TH.get(gender_raw, gender_raw)
        en_name, short_th, partner_hint = TAMER_META.get(tid, (name_th, name_th, ""))

        cl = createlist.get(tid, {"starter": tid <= 80004, "order": tid - 80000, "costumes": []})
        costumes = []
        for ciid in cl["costumes"]:
            cit = its.get(ciid)
            if cit:
                c_icon = f"/images/client_items/{ciid}.png" if E.save_icon(ciid, cit["icon_id"]) else ""
                costumes.append({"id": ciid, "name": _clean(cit["name"]), "icon": c_icon})

        lv_rows = stats_map.get(tid, [])
        milestones = []
        for m_lv in (1, 50, 99, 120, 140, 150, 160, 170, 180):
            if m_lv <= len(lv_rows):
                r = lv_rows[m_lv - 1]
                milestones.append({"lv": r[0], "hp": r[1], "ds": r[2], "ms": r[3], "de": r[4], "at": r[5]})

        # Attach tamer skills & matching Cash/Extreme tiers
        pref = SKILL_PREFIX.get(tid)
        raw_skills = list(skills_by_pref.get(pref, [])) if pref else []
        # Deduplicate skills by code, separate active vs passive
        seen_codes = set()
        active_skills, passive_skills = [], []
        for s in raw_skills:
            if s["code"] in seen_codes:
                continue
            seen_codes.add(s["code"])
            base_nm = re.sub(r"ขั้น(?:สูง|สุดยอด)$", "", s["name"]).strip()
            s_out = {
                "code": s["code"],
                "name": s["name"],
                "desc": s["desc"],
                "icon": skill_icon_url.get(base_nm, ""),
                "tier": "ขั้นสูง" if "ขั้นสูง" in s["name"] else ("พื้นฐาน" if s["code"] % 10 == 1 else "ปรับปรุง"),
            }
            if s["kind"] == "passive":
                passive_skills.append(s_out)
            else:
                active_skills.append(s_out)

        # Find upgraded/extreme variants (80012xx) sharing base skill name of the primary active skill
        extra_tiers = []
        if active_skills:
            primary_base = re.sub(r"ขั้น(?:สูง|สุดยอด)$", "", active_skills[0]["name"]).strip()
            seen_tier_codes = {s["code"] for s in active_skills}
            for u in upgrades_by_base.get(primary_base, []):
                if u["code"] not in seen_tier_codes:
                    seen_tier_codes.add(u["code"])
                    extra_tiers.append({
                        "code": u["code"],
                        "name": u["name"],
                        "desc": u["desc"],
                        "icon": skill_icon_url.get(primary_base, ""),
                        "tier": "ขั้นสุดยอด" if "ขั้นสุดยอด" in u["name"] else "ขั้นสูง",
                    })

        folder = PACK_FOLDERS.get(tid, "")
        p_files = pack_cnt.get(folder, 0)
        img = images.get(tid, {"portrait_lg": "", "portrait_sm": "", "extras": []})
        lv180 = lv_rows[179] if len(lv_rows) >= 180 else (lv_rows[-1] if lv_rows else [1, 0, 0, 0, 0, 0])
        lv1 = lv_rows[0] if lv_rows else [1, 0, 0, 0, 0, 0]
        slug = re.sub(r"[\s/\\?#%&]+", "-", name_th).strip("-") or str(tid)

        tamers.append({
            "id": tid,
            "slug": slug,
            "name_th": name_th,
            "short_th": short_th,
            "name_en": en_name,
            "partner": partner_hint,
            "series": series_th,
            "series_en": series_en,
            "gender": gender_th,
            "bio": bio,
            "starter": cl["starter"],
            "unlock_type": "สร้างตัวเริ่มต้นฟรี" if cl["starter"] else "ปลดล็อก / ไอเทมเปลี่ยนตัว",
            "in_thai": p_files > 0 or bool(img["portrait_lg"]),
            "pack_files": p_files,
            "role": _role_tag(lv180),
            "portrait_lg": img["portrait_lg"],
            "portrait_sm": img["portrait_sm"],
            "extras": img["extras"],
            "stats_lv1": {"lv": lv1[0], "hp": lv1[1], "ds": lv1[2], "ms": lv1[3], "de": lv1[4], "at": lv1[5]},
            "stats_lv180": {"lv": lv180[0], "hp": lv180[1], "ds": lv180[2], "ms": lv180[3], "de": lv180[4], "at": lv180[5]},
            "stats_milestones": milestones,
            "stats_levels": [[r[1], r[2], r[3], r[4], r[5]] for r in lv_rows],
            "active_skills": active_skills,
            "extra_skill_tiers": extra_tiers,
            "passive_skills": passive_skills,
            "unlock_items": unlock_items.get(tid, []),
            "id_cards": id_cards.get(tid, []),
            "costumes": costumes,
        })

    skill_system = _build_skill_system(its)
    tamer_status = _build_tamer_status(its)
    payload = {"tamers": tamers, "skill_system": skill_system, "tamer_status": tamer_status}
    try:
        CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return payload


if __name__ == "__main__":
    payload = build()
    data = payload["tamers"]
    ss = payload["skill_system"]
    print(
        f"Built {len(data)} tamers | skill_system: {len(ss.get('active_skills', []))} active, "
        f"{len(ss.get('passive_skills', []))} passive | satsuma={ss.get('satsuma', {}).get('image')} | gekomon={ss.get('gekomon', {}).get('image')}"
    )
    for t in data:
        print(
            f"  {t['id']} | {t['name_th']:22s} | {t['series']:16s} | {t['gender']} | "
            f"{'Starter' if t['starter'] else 'Unlock ':7s} | pack={t['pack_files']:3d} | "
            f"A={len(t['active_skills'])}+{len(t['extra_skill_tiers'])} P={len(t['passive_skills'])} | "
            f"items={len(t['unlock_items'])} cards={len(t['id_cards'])} | lv180=HP:{t['stats_lv180']['hp']} DS:{t['stats_lv180']['ds']} MS:{t['stats_lv180']['ms']} DE:{t['stats_lv180']['de']} AT:{t['stats_lv180']['at']}"
        )
