"""Enhanced DMO Thai Main Quest Guide Data Generator
Builds map-grouped quest guideline with:
- Exact Thai client map names
- In-game map images (/images/maps/*)
- Exact map unlock requirements (prerequisite quest & map)
- NPC portraits (/images/npc/*) for start & end NPCs
- Clean EXP and Money Bit rewards (using ui_exp.png and ui_money.png)
"""

import struct
import json
from pathlib import Path
from collections import defaultdict

CRACK = Path("G:/DMOWiki/CrackDMO")
BASE_DIR = Path("G:/DMOWiki/Web_Scraper")
WEB_DIR = BASE_DIR / "web"
STATIC_DATA_DIR = WEB_DIR / "static" / "data"
OUT_MAPS_DIR = BASE_DIR / "output" / "images" / "maps"
OUT_NPCS_DIR = BASE_DIR / "output" / "images" / "npc"

STATIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT_MAPS_DIR.mkdir(parents=True, exist_ok=True)
OUT_NPCS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load Quest Strings
def load_quest_strings():
    p = CRACK / "out_decrypted/data/bin/language/thailand/quest_str.bin"
    b = p.read_bytes()
    cnt = struct.unpack_from("<i", b, 0)[0]
    out = {}
    o = 4
    for _ in range(cnt):
        qid = struct.unpack_from("<i", b, o)[0]
        o += 4
        strs = []
        for _f in range(8):
            ln = struct.unpack_from("<i", b, o)[0]
            o += 4
            strs.append(b[o:o + 2 * ln].decode("utf-16le", "replace"))
            o += 2 * ln
        out[qid] = strs
    return out

# 2. Load helper metadata
def load_meta():
    npcs = {}
    npc_path = CRACK / "out_json/language/npc_str.json"
    if npc_path.exists():
        for item in json.loads(npc_path.read_text(encoding="utf-8")):
            f = item.get("fields", [])
            title = f[0].strip() if len(f) > 0 else ""
            name = f[1].strip() if len(f) > 1 else ""
            full = f"{title} {name}".strip() if title else name
            npcs[item["id"]] = full

    maps = {}
    map_path = CRACK / "out_json/language/mapname_str.json"
    if map_path.exists():
        for item in json.loads(map_path.read_text(encoding="utf-8")):
            maps[item["id"]] = item.get("text", "").strip()

    monsters = {}
    mon_path = CRACK / "out_json/language/monstername_str.json"
    if mon_path.exists():
        for item in json.loads(mon_path.read_text(encoding="utf-8")):
            monsters[item["id"]] = item.get("fields", [""])[0]

    items = {}
    item_path = CRACK / "out_json/language/item_str.json"
    if item_path.exists():
        for item in json.loads(item_path.read_text(encoding="utf-8")):
            items[item["id"]] = item.get("fields", [""])[0]

    # Load NPC Image Map
    npc_img_map = {}
    npc_map_file = WEB_DIR / "npc_img_map.json"
    if npc_map_file.exists():
        npc_img_map = json.loads(npc_map_file.read_text(encoding="utf-8"))

    return npcs, maps, monsters, items, npc_img_map

# 3. Clean string tags
def clean_desc(text):
    if not text: return ""
    import re
    t = re.sub(r"@<tc:[^>]*>", "", text)
    t = t.replace("@</tc>", "")
    t = re.sub(r"%qs\d+", "", t)
    t = re.sub(r"%qe%cc\d+:%mc\d+[a-zA-Z]?", "", t)
    t = t.replace("%qe", "").replace("%s", "")
    t = "\n".join([line.strip() for line in t.split("\n") if line.strip()])
    return t.strip()

# 4. Binary section parser
def parse_sections(b, o):
    secs = []
    for size in (9, 21, 10):
        if o + 4 > len(b): return None
        n = struct.unpack_from("<i", b, o)[0]
        if not 0 <= n <= 30: return None
        o += 4
        secs.append([b[o + i * size:o + (i + 1) * size] for i in range(n)])
        o += n * size
    return secs, o

def record_end_ok(b, end):
    return end == len(b) or (end + 8 <= len(b) and b[end:end + 4] == b[end + 4:end + 8] and 0 < struct.unpack_from("<i", b, end)[0] < 100000)

# Exact Map Images mapping
MAP_IMAGE_MAP = {
    # Ch 1: Yokohama & DATS
    "ศูนย์บัญชาการ DATS": "/images/maps/3_zone.png",
    "<โหมดฝึกสอน>": "/images/maps/105_zone.png",
    "หมู่บ้านโยโกฮาม่า": "/images/maps/105_zone.png",
    "หมู่บ้าน โยโกฮาม่า": "/images/maps/105_zone.png",
    "โยโกฮาม่า สวนม้านั่งไม้": "/images/maps/realtown1_2_zone.png",
    "สวนม้านั่งไม้ โยโกฮาม่า": "/images/maps/realtown1_2_zone.png",
    "ทางเข้าโรงกลั่นน้ำมัน": "/images/maps/oilrefinery1_zone.png",
    "โรงกลั่นน้ำมัน ชั้น1": "/images/maps/oilrefinery1_zone.png",
    "โรงกลั่นน้ำมันชั้น 1": "/images/maps/oilrefinery1_zone.png",
    "โรงกลั่นน้ำมัน ชั้น2": "/images/maps/oilrefinery2_zone.png",
    "โรงกลั่นน้ำมัน ชั้น3": "/images/maps/oilrefinery3_zone.png",

    # Ch 2: Western & Maze
    "หมู่บ้านฝั่งตะวันตก": "/images/maps/westrentown_01_zone.png",
    "โลกดิจิตอล หมู่บ้านฝั่งตะวันตก": "/images/maps/westrentown_01_zone.png",
    "โลกดิจิตอล หมู่บ้านฝั่งตะวันตก ด้านนอก": "/images/maps/westerntown_west_zone.png",
    "โลกดิจิตอล หมู่บ้านฝั่งตะวันตก ฝั่งตะวันออก": "/images/maps/westrentown_01_zone.png",
    "โลกดิจิตอล พื้นที่ทุรกันดาร": "/images/maps/westren_field_01_zone.png",
    "พื้นที่ทุรกันดาร": "/images/maps/westren_field_01_zone.png",
    "โลกดิจิตอล ฟาร์มดิจิมอน": "/images/maps/westren_field_02_zone.png",
    "ฟาร์มดิจิมอน": "/images/maps/westren_field_02_zone.png",
    "โลกดิจิตอล หุบเขาแห่งสายลม": "/images/maps/wind_valley_zone.png",
    "หุบเขาสายลม": "/images/maps/wind_valley_zone.png",
    "โลกดิจิตอล โบราณสถาน": "/images/maps/westerntown_darktower_zone.png",
    "ดาร์คทาวเวอร์ ดินแดนต้องห้าม": "/images/maps/westerntown_darktower_zone.png",
    "ฝั่งตะวันตก : ด้านซ้าย": "/images/maps/westren_field_02_zone.png",
    "เขาวงกตดิจิมอน": "/images/maps/labyrinth_01_mini.png",
    "เขาวงกตดิจิมอน ชั้น B2": "/images/maps/labyrinth_01_mini.png",
    "เขาวงกตดิจิมอน F1": "/images/maps/labyrinth_02_mini.png",
    "เขาวงกตดิจิมอน F2": "/images/maps/labyrinth_03_mini.png",
    "Digimon Maze 3F": "/images/maps/labyrinth_04_mini.png",
    "Digimon Maze 4F": "/images/maps/labyrinth_04_mini.png",

    # Ch 3: Glacier
    "D-เทอร์มินัล": "/images/maps/d_terminel_main01_zone.png",
    "หมู่บ้านพายุหิมะ": "/images/maps/ice_land01_zone.png",
    "ดินแดนน้ำแข็ง": "/images/maps/ice_land02_zone.png",
    "หมู่บ้านมนุษย์หิมะ": "/images/maps/ice_land03_zone.png",
    "กำแพงน้ำแข็งนิรันดร์": "/images/maps/ice_land_05_zone.png",

    # Ch 4: File Island
    "ทะเลสาบสีเงิน": "/images/maps/1301_zone.png",
    "ป่าแห่งความเงียบ": "/images/maps/1302_zone.png",
    "พื้นที่อารยธรรมที่สูญหาย": "/images/maps/1303_zone.png",
    "ซากอารยธรรมโบราณแห่งความลับ": "/images/maps/1304_mini.png",
    "ชายฝั่งเกาะไฟล์": "/images/maps/1305_zone.png",
    "ภูเขาอินฟินิตี้": "/images/maps/1308_mini.png",
    "รอยร้าวของเดวีมอน": "/images/maps/1311_zone.png",
    "หุบเขานิรันดร์": "/images/maps/1308_mini.png",

    # Ch 5: Server Continent
    "ทวีปเซิร์ฟเวอร์ - ทะเลทราย": "/images/maps/1300_zone.png",
    "ทวีปเซิร์ฟเวอร์ - หุบเขา": "/images/maps/1301_zone.png",
    "ทวีปเซิร์ฟเวอร์ - ปิรามิด": "/images/maps/1302_zone.png",
    "ทวีปเซิร์ฟเวอร์-ปิรามิด": "/images/maps/1302_zone.png",

    # Ch 6: Verdandi
    "เวอร์ซันดิเทอร์มินัล": "/images/maps/1700_zone.png",
    "รอยัลเบส": "/images/maps/1701_mini.png",

    # Ch 7: Tokyo - Odaiba
    "ฮิคาริงาโอกะ": "/images/maps/201_zone.png",
    "ชิบูย่า": "/images/maps/202_zone.png",
    "โตเกียวทาวเวอร์": "/images/maps/203_zone.png",
    "มินาโตะซิตี้": "/images/maps/206_zone.png",
    "บิ๊กไซท์": "/images/maps/207_zone.png",
    "โอไดบะ": "/images/maps/208_zone.png",
    "เรนโบว์ บริดจ์": "/images/maps/208_zone.png",
    "ดาดฟ้าสถานีโทรทัศน์ฟูจิทีวี": "/images/maps/209_zone.png",
    "สถานที่ตั้งค่าย": "/images/maps/200_zone.png",

    # Ch 8: Shinjuku & D-Reaper
    "ชินจูกุ": "/images/maps/250_zone.png",
    "ชินจูกุ(กลางคืน)": "/images/maps/254_zone.png",
    "ชินจูกุตะวันตก (กลางวัน)": "/images/maps/250_zone.png",
    "ชินจูกุตะวันออก (กลางวัน)": "/images/maps/251_zone.png",
    "ชินจูกุตะวันตก (กลางคืน)": "/images/maps/254_zone.png",
    "ชินจูกุตะวันออก (กลางคืน)": "/images/maps/255_zone.png",
    "ดิจิมอนเทมเมอร์ส": "/images/maps/1800_zone.png",
    "หุบเขาแห่งแสงสว่าง": "/images/maps/1800_zone.png",
    "D-รีพเปอร์": "/images/maps/266_zone.png",

    # Ch 9: Power Digimon / Kaiser Domain
    "พาวเวอร์ดิจิมอน": "/images/maps/400_zone.png",
    "พื้นที่ของไกเซอร์": "/images/maps/400_zone.png",
    "พื้นที่แห่งความว่างเปล่า": "/images/maps/1906_zone.png",

    # Ch 10: Spiral Mountain
    "ป่าแห่งการเริ่มต้น": "/images/maps/1901_zone.png",
    "ป่าหุ่นเชิด": "/images/maps/1902_zone.png",
    "อาณาจักรโลหะ": "/images/maps/1903_zone.png",
    "จุดสูงสุดของฝันร้าย": "/images/maps/1905_zone.png",
    "ทะเลสาปแห่งการเริ่มต้น": "/images/maps/1901_zone.png",
    "หมู่บ้านแห่งการเริ่มต้น": "/images/maps/1901_zone.png",

    # Ch 11: Frontier (Exact Thai Client Map Names)
    "ดิจิมอนฟรอนเทียร์": "/images/maps/500_zone.png",
    "เทอร์มินัลแห่งเปลวเพลิง": "/images/maps/500_zone.png",
    "วินด์ แฟคทอรี่": "/images/maps/502_zone.png",
    "หมู่บ้านสายลมอ่อน": "/images/maps/503_zone.png",
    "โรงงานสายลม": "/images/maps/502_zone.png",
    "หมู่บ้านสายลม": "/images/maps/503_zone.png",
}

# Standardized Map Display Names (Exact Thai Patch)
CANONICAL_MAP_NAMES = {
    "<โหมดฝึกสอน>": "โหมดฝึกสอน (Tutorial)",
    "หมู่บ้าน โยโกฮาม่า": "หมู่บ้านโยโกฮาม่า",
    "โยโกฮาม่า สวนม้านั่งไม้": "สวนม้านั่งไม้ โยโกฮาม่า",
    "โรงกลั่นน้ำมันชั้น 1": "โรงกลั่นน้ำมัน ชั้น 1",
    "โรงกลั่นน้ำมัน ชั้น1": "โรงกลั่นน้ำมัน ชั้น 1",
    "โรงกลั่นน้ำมัน ชั้น2": "โรงกลั่นน้ำมัน ชั้น 2",
    "โรงกลั่นน้ำมัน ชั้น3": "โรงกลั่นน้ำมัน ชั้น 3",
    "โลกดิจิตอล หมู่บ้านฝั่งตะวันตก": "หมู่บ้านฝั่งตะวันตก",
    "โลกดิจิตอล หมู่บ้านฝั่งตะวันตก ด้านนอก": "หมู่บ้านฝั่งตะวันตก (รอบนอก)",
    "โลกดิจิตอล หมู่บ้านฝั่งตะวันตก ฝั่งตะวันออก": "หมู่บ้านฝั่งตะวันตก (ฝั่งตะวันออก)",
    "โลกดิจิตอล พื้นที่ทุรกันดาร": "พื้นที่ทุรกันดาร ฝั่งตะวันตก",
    "โลกดิจิตอล ฟาร์มดิจิมอน": "ดิจิมอนฟาร์ม",
    "โลกดิจิตอล หุบเขาแห่งสายลม": "หุบเขาแห่งสายลม",
    "โลกดิจิตอล โบราณสถาน": "โบราณสถานแห่งความมืด",
    "ดาร์คทาวเวอร์ ดินแดนต้องห้าม": "ดาร์คทาวเวอร์ (ดินแดนต้องห้าม)",
    "เขาวงกตดิจิมอน ชั้น B2": "เขาวงกตดิจิมอน (ชั้น B2)",
    "เขาวงกตดิจิมอน": "เขาวงกตดิจิมอน (ทางเข้า)",
    "เขาวงกตดิจิมอน F1": "เขาวงกตดิจิมอน ชั้น 1 (F1)",
    "เขาวงกตดิจิมอน F2": "เขาวงกตดิจิมอน ชั้น 2 (F2)",
    "Digimon Maze 3F": "เขาวงกตดิจิมอน ชั้น 3 (F3)",
    "Digimon Maze 4F": "เขาวงกตดิจิมอน ชั้น 4 (F4)",
    "ทวีปเซิร์ฟเวอร์-ปิรามิด": "ทวีปเซิร์ฟเวอร์ - ปิรามิด",
    "พาวเวอร์ดิจิมอน": "พื้นที่ของไกเซอร์ (Adventure 02)",
    "โรงงานสายลม": "วินด์ แฟคทอรี่",
    "หมู่บ้านสายลม": "หมู่บ้านสายลมอ่อน",
    "ดิจิมอนฟรอนเทียร์": "เทอร์มินัลแห่งเปลวเพลิง (ฟรอนเทียร์)",
    "ดาดฟ้าสถานีโทรทัศน์ฟูจิทีวี": "ดาดฟ้าสถานีโทรทัศน์ฟูจิ (Fuji TV)",
}

def format_money_thai(bits):
    if not bits or bits <= 0: return "0 Bit"
    t = bits // 10000000
    rem = bits % 10000000
    m = rem // 10000
    rem = rem % 10000
    b = rem
    parts = []
    if t > 0: parts.append(f"{t} T")
    if m > 0: parts.append(f"{m} M")
    if b > 0 or not parts: parts.append(f"{b} Bit")
    return " ".join(parts)

def build():
    print("[1/5] Loading strings, maps, metadata from CrackDMO...")
    q_str = load_quest_strings()
    npcs, maps, monsters, items, npc_img_map = load_meta()

    b = (CRACK / "out_decrypted/data/bin/table/quest.bin").read_bytes()
    count = struct.unpack_from("<i", b, 0)[0]

    quests = {}
    p = 4
    for _ in range(count):
        if p + 36 > len(b): break
        qid = struct.unpack_from("<i", b, p)[0]
        n_sup = struct.unpack_from("<i", b, p + 32)[0]
        hit = None
        guesses = ([36 + 9 * n_sup] if 0 <= n_sup <= 10 else []) + list(range(28, 80))
        for h in guesses:
            r = parse_sections(b, p + h)
            if r and record_end_ok(b, r[1]):
                hit = (h, *r)
                break
        if not hit: break
        h, secs, end = hit

        qtype = b[p + 21]
        level = struct.unpack_from("<H", b, p + 16)[0]
        s_npc = struct.unpack_from("<i", b, p + 23)[0] if h >= 32 else 0
        e_npc = struct.unpack_from("<i", b, p + 28)[0] if h >= 32 else 0

        strs = q_str.get(qid, [""] * 8)
        raw_map = strs[0].strip()

        pre_quests = []
        for e in secs[0]:
            ptype = e[0]
            pval = struct.unpack_from("<i", e, 1)[0]
            if ptype == 0 and pval > 0:
                pre_quests.append(pval)

        obj_list = []
        for e in secs[1]:
            otype = e[0]
            target = struct.unpack_from("<i", e, 1)[0]
            cnt_val = struct.unpack_from("<i", e, 5)[0]
            target_name = ""
            type_label = "เป้าหมาย"
            if otype == 0:
                type_label = "กำจัด"
                target_name = monsters.get(target, f"มอนสเตอร์ #{target}")
            elif otype == 1:
                type_label = "รวบรวม"
                target_name = items.get(target, f"ไอเทม #{target}")
            elif otype == 4:
                type_label = "พูดคุย"
                target_name = npcs.get(target, f"NPC #{target}")
            elif otype == 2:
                type_label = "ใช้งาน"
                target_name = items.get(target, f"ไอเทม #{target}")
            obj_list.append({
                "type": otype,
                "type_label": type_label,
                "target_id": target,
                "target_name": target_name,
                "count": max(cnt_val, 1) if otype in (0, 1) else 1
            })

        rew_list = []
        exp = 0
        bit = 0
        for e in secs[2]:
            rtype = e[1]
            rval = struct.unpack_from("<i", e, 2)[0]
            rcnt = struct.unpack_from("<i", e, 6)[0]
            if rtype == 1: exp = rval
            elif rtype == 0: bit = rval
            elif rtype == 2:
                rew_list.append({
                    "item_id": rval,
                    "name": items.get(rval, f"ไอเทม #{rval}"),
                    "count": max(rcnt, 1)
                })

        # NPC Image URLs
        s_img = f"/images/npc/{npc_img_map[s_npc]}" if s_npc in npc_img_map else "/images/ui/ui_tamer.png"
        e_img = f"/images/npc/{npc_img_map[e_npc]}" if e_npc in npc_img_map else "/images/ui/ui_tamer.png"

        canon_map = CANONICAL_MAP_NAMES.get(raw_map, raw_map)
        map_img = MAP_IMAGE_MAP.get(raw_map) or MAP_IMAGE_MAP.get(canon_map) or "/images/maps/105_zone.png"

        quests[qid] = {
            "id": qid,
            "type": qtype,
            "level": level,
            "start_npc_id": s_npc,
            "start_npc": npcs.get(s_npc, "เริ่มอัตโนมัติ"),
            "start_npc_image": s_img,
            "end_npc_id": e_npc,
            "end_npc": npcs.get(e_npc, "ส่งอัตโนมัติ"),
            "end_npc_image": e_img,
            "raw_map_name": raw_map,
            "map_name": canon_map,
            "map_image": map_img,
            "title": strs[1].strip(),
            "story": clean_desc(strs[2]),
            "objective_desc": clean_desc(strs[3]),
            "tracker": clean_desc(strs[4]),
            "pre_quests": pre_quests,
            "next_quests": [],
            "objectives": obj_list,
            "exp": exp,
            "bit": bit,
            "bit_formatted": format_money_thai(bit),
            "reward_items": rew_list
        }
        p = end

    print(f"[2/5] Parsed {len(quests)} quests.")

    # Calculate forward links
    for qid, q in quests.items():
        for pre in q["pre_quests"]:
            if pre in quests:
                if qid not in quests[pre]["next_quests"]:
                    quests[pre]["next_quests"].append(qid)

    # Chapters Definitions
    chapters_def = [
        {
            "id": "ch1_yokohama",
            "number": 1,
            "title": "บทที่ 1: ศูนย์บัญชาการ DATS & โยโกฮาม่า",
            "badge": "เริ่มต้น",
            "level_range": "Lv. 1 - 25",
            "area_keywords": ["โหมดฝึกสอน", "ศูนย์บัญชาการ dats", "หมู่บ้านโยโกฮาม่า", "หมู่บ้าน โยโกฮาม่า", "โยโกฮาม่า สวนม้านั่งไม้", "สวนม้านั่งไม้ โยโกฮาม่า", "ทางเข้าโรงกลั่นน้ำมัน", "โรงกลั่นน้ำมัน"],
            "summary": "จุดเริ่มต้นของเทมเมอร์หน้าใหม่ในสังกัดหน่วย DATS เรียนรู้ระบบพื้นฐาน ทำภารกิจสืบสวนเหตุการณ์ดิจิมอนผิดปกติที่บุกรุกมายังโลกมนุษย์ คุ้มกันครอบครัวของไดมอน มาซารุ และคลี่คลายเหตุการณ์ที่โรงกลั่นน้ำมันเพื่อปลดล็อคการเดินทางสู่โลกดิจิตอล",
            "key_unlocks": ["ตราสมาชิก DATS อย่างเป็นทางการ", "สิทธิ์การเดินทางข้ามมิติสู่โลกดิจิตอล (Digital World Access)", "เปิดระบบฟักไข่ดิจิทามะ และระบบสแกน/รีเทิร์นข้อมูล"],
            "pro_tips": ["อย่าลืมรับเควสฝึกสอนทั้งหมดเพราะจะได้รับไอเทมเริ่มต้นและดิจิมอนคู่หูที่จำเป็น", "ในโรงกลั่นน้ำมันมอนสเตอร์มีพลังป้องกันสูง ควรใช้ดิจิมอนธาตุแพ้ทางเพื่อเคลียร์เควสได้ไวขึ้น"]
        },
        {
            "id": "ch2_western_maze",
            "number": 2,
            "title": "บทที่ 2: ดินแดนฝั่งตะวันตก & เขาวงกตดิจิมอน",
            "badge": "กลางช่วงแรก",
            "level_range": "Lv. 25 - 60",
            "area_keywords": ["หมู่บ้านฝั่งตะวันตก", "พื้นที่ทุรกันดาร", "ฟาร์มดิจิมอน", "ดิจิมอนฟาร์ม", "หุบเขาแห่งสายลม", "หุบเขาสายลม", "พื้นที่รกร้าง ฝั่งตะวันตก", "พื้นที่ซากปรักหักพัง", "ดาร์คทาวเวอร์", "เขาวงกตดิจิมอน", "digimon maze"],
            "summary": "ก้าวเข้าสู่โลกดิจิตอลฝั่งตะวันตก ออกค้นหาร่องรอยของอิคุโตะและฟอลโคมอน สืบสวนแผนการลับของดร.คุราตะ และเผชิญหน้ากับความลึกลับของเขาวงกตดิจิมอน (Digimon Maze) ที่เต็มไปด้วยมอนสเตอร์อันทรงพลัง",
            "key_unlocks": ["ปลดล็อคประตูเข้าสู่เขาวงกตดิจิมอน B2, B1, F1, F2, F3 และ F4", "เปิดจุดวาร์ปสถานีรถไฟฝั่งตะวันตก เชื่อมต่อหลายพื้นที่สำคัญ", "ปลดล็อคเควสโจเกรสและไอเทมวิวัฒนาการระดับสูง"],
            "pro_tips": ["เควสเขาวงกตดิจิมอน F1-F4 ต้องส่งเควสต่อเนื่องเป็นลูกโซ่ ห้ามทิ้งเควสใดเควสหนึ่งเด็ดขาดเพราะจะทำให้ติดบัคเควสเดินต่อไม่ได้", "เตรียมไอเทมฟื้นฟู HP/DS และจั๊มบูสเตอร์ไว้เสมอเนื่องจากทางเดินในเมซมีความซับซ้อนมาก"]
        },
        {
            "id": "ch3_glacier",
            "number": 3,
            "title": "บทที่ 3: กลาเซียร์ ดินแดนหิมะนิรันดร์",
            "badge": "กลางเกม",
            "level_range": "Lv. 50 - 65",
            "area_keywords": ["หมู่บ้านพายุหิมะ", "หมู่บ้านมนุษย์หิมะ", "ดินแดนน้ำแข็ง", "ทุ่งหิมะ", "กำแพงน้ำแข็งนิรันดร์", "d-เทอร์มินัล"],
            "summary": "มุ่งหน้าสู่ดินแดนเยือกแข็งอันหนาวเหน็บ ช่วยเหลือมนุษย์หิมะมอนและเหล่าดิจิมอนที่ถูกครอบงำด้วยฟันเฟืองสีดำ รวบรวมข้อมูลเพื่อตามหาต้นตอความผิดปกติ และเปิดเส้นทางไปสู่กำแพงน้ำแข็งนิรันดร์",
            "key_unlocks": ["ปลดล็อคแผนที่กำแพงน้ำแข็งนิรันดร์ (Infinite Ice Wall)", "ปลดล็อคเส้นทางลับเชื่อมต่อไปยังเกาะไฟล์ (File Island)", "รับเครื่องประดับและหินพัฒนาธาตุน้ำแข็ง"],
            "pro_tips": ["มอนสเตอร์ในดินแดนหิมะส่วนใหญ่เป็นธาตุน้ำ/น้ำแข็ง ดิจิมอนธาตุสายฟ้าหรือดินจะโจมตีได้รุนแรงเป็นพิเศษ", "เควสเก็บรวบรวมฟันเฟืองสีดำ ดรอปจากมอนสเตอร์เฉพาะจุด ให้เช็คพิกัดบนมินิแมพให้ดี"]
        },
        {
            "id": "ch4_file_island",
            "number": 4,
            "title": "บทที่ 4: มหากาพย์เกาะไฟล์ & ภูเขาอินฟินิตี้",
            "badge": "กลางเกม",
            "level_range": "Lv. 60 - 80",
            "area_keywords": ["ทะเลสาบสีเงิน", "ป่าแห่งความเงียบ", "พื้นที่อารยธรรมที่สูญหาย", "ชายฝั่งเกาะไฟล์", "ภูเขาอินฟินิตี้", "รอยร้าวของเดวีมอน", "หุบเขานิรันดร์", "ซากอารยธรรมโบราณแห่งความลับ"],
            "summary": "ย้อนรอยความทรงจำของอนิเมะ Digimon Adventure ภาคแรก บนเกาะไฟล์ ช่วยเหลือเลโอมอนและโอเกรมอน ทำลายฟันเฟืองดำที่แพร่ระบาด และบุกขึ้นสู่ภูเขาอินฟินิตี้เพื่อทำศึกแตกหักกับเดวีมอน",
            "key_unlocks": ["ปลดล็อคดันเจี้ยนภูเขาอินฟินิตี้ (Infinite Mountain Dungeon)", "ปลดล็อคการวิวัฒนาการร่างเมก้าและเบิร์สโหมด (Burst Mode)", "เปิดท่าเรือชายฝั่งเกาะไฟล์เพื่อข้ามทะเลไปยังทวีปเซิร์ฟเวอร์"],
            "pro_tips": ["เควสเกาะไฟล์ให้ EXP มหาศาล เป็นแหล่งฟาร์มเลเวลที่ดีที่สุดช่วงเลเวล 60-80", "เมื่อถึงเควสปราบเดวีมอนที่ภูเขาอินฟินิตี้ แนะนำให้รวมปาร์ตี้เพื่อความรวดเร็วและปลอดภัย"]
        },
        {
            "id": "ch5_server_continent",
            "number": 5,
            "title": "บทที่ 5: ทวีปเซิร์ฟเวอร์ ทะเลทราย & ปิรามิด",
            "badge": "กลาง-เลท",
            "level_range": "Lv. 75 - 95",
            "area_keywords": ["ทวีปเซิร์ฟเวอร์ - ทะเลทราย", "ทวีปเซิร์ฟเวอร์ - หุบเขา", "ทวีปเซิร์ฟเวอร์ - ปิรามิด", "ทวีปเซิร์ฟเวอร์-ปิรามิด"],
            "summary": "ออกเดินทางสู่ผืนทวีปอันกว้างใหญ่ เผชิญหน้ากับเอเตมอนจอมวายร้ายที่ควบคุมเครือข่ายสายเคเบิลมืด ฝ่าฟันหุบเขาอันตราย และบุกเข้าไปในปิรามิดของดาตามอนเพื่อกู้ข้อมูลสำคัญกลับคืนมา",
            "key_unlocks": ["ปลดล็อคดันเจี้ยนปิรามิดดาตามอน (Datamon Maze)", "เปิดสิทธิ์การใช้งานแหวนและสร้อยคอระดับสูง (Ring/Necklace Shiny)", "เชื่อมต่อโครงข่ายประตูมิติสู่โลกดิจิตอลใหม่"],
            "pro_tips": ["พื้นที่ทะเลทรายมีระยะทางกว้างมาก ควรใช้ดิจิมอนโหมดขับขี่ (Riding Mode) เพื่อประหยัดเวลาเดินทาง", "ในปิรามิดมอนสเตอร์เกิดหนาแน่น ระวังการดึงมอนสเตอร์เกินจำนวนที่รับไหว"]
        },
        {
            "id": "ch6_verdandi",
            "number": 6,
            "title": "บทที่ 6: เวอร์ซันดิเทอร์มินัล (X-Antibody)",
            "badge": "เลทเกม",
            "level_range": "Lv. 90 - 110",
            "area_keywords": ["เวอร์ซันดิเทอร์มินัล", "รอยัลเบส"],
            "summary": "วิกฤตการณ์ไวรัส X-Program ที่ถูกปล่อยออกมาโดยอิกดราซิล กองทหารรอยัลไนท์แบ่งฝ่ายต่อสู้กัน เทมเมอร์ต้องติดตั้งระบบ XAI Indicator เพื่อต้านทานพิษของไวรัส และปลดล็อคพลัง X-Antibody ขั้นสูงสุด",
            "key_unlocks": ["ปลดล็อคระบบ X-Antibody System (XAI Indicator)", "ปลดล็อคดันเจี้ยนรอยัลเบส (Royal Base 1F-3F)", "เปิดสิทธิ์การทำเควสวิวัฒนาการ X-Antibody เช่น Omegamon X, Alphamon Ouryuken X"],
            "pro_tips": ["ต้องสวมใส่ XAI และรักษาระดับ X-Gauge ให้ไม่หมด เพื่อป้องกันดีบัฟดาเมจลดลงในพื้นที่", "มอนสเตอร์ในเวอร์ซันดิมีความถึกสูงมาก ควรมีค่า Hit Rate (HT) และ Critical (CT) เพียงพอ"]
        },
        {
            "id": "ch7_odaiba",
            "number": 7,
            "title": "บทที่ 7: มหาสงคราม โตเกียว - โอไดบะ",
            "badge": "เลทเกม",
            "level_range": "Lv. 99 - 120",
            "area_keywords": ["ฮิคาริงาโอกะ", "ชิบูย่า", "โตเกียวทาวเวอร์", "มินาโตะซิตี้", "โอไดบะ", "บิ๊กไซท์", "เรนโบว์ บริดจ์", "ดาดฟ้าสถานีโทรทัศน์ฟูจิทีวี", "สถานที่ตั้งค่าย"],
            "summary": "กองทัพของแวมเดมอนข้ามประตูมิติมาบุกยึดกรุงโตเกียว เทมเมอร์ต้องร่วมมือกับเหล่าเด็กผู้ถูกเลือกทั้ง 8 คน ปกป้องครอบครัวและชาวเมือง ต่อสู้ไล่ล่าไปตามสถานที่จริงในโตเกียว จนถึงศึกตัดสินกับเวนอมแวมเดมอน",
            "key_unlocks": ["ปลดล็อคดันเจี้ยนเรดบอสโอไดบะ (VenomMyotismon, DarkTyrannomon)", "เปิดระบบฉายาบัฟสเตตัสระดับสูงของโตเกียว", "สิทธิ์แลกไอเทมอุปกรณ์และตั๋วการันตีระดับสูง"],
            "pro_tips": ["เควสเนื้อเรื่องโอไดบะมีความยาวมาก ให้ทำตามเครื่องหมายเควสสีม่วง/น้ำเงินบนแผนที่อย่างเคร่งครัด", "จุดที่ต้องคุยกับเด็กผู้ถูกเลือก ให้สังเกตเวลาบนแผนที่ (กลางวัน/กลางคืน) มอนสเตอร์บางตัวจะเกิดเฉพาะเวลานั้น"]
        },
        {
            "id": "ch8_shinjuku",
            "number": 8,
            "title": "บทที่ 8: ชินจูกุ, เทมเมอร์ส & D-รีพเปอร์",
            "badge": "เลทเกม",
            "level_range": "Lv. 110 - 140",
            "area_keywords": ["ชินจูกุ", "ชินจูกุ(กลางคืน)", "ชินจูกุตะวันตก (กลางวัน)", "ชินจูกุตะวันออก (กลางวัน)", "ชินจูกุตะวันตก (กลางคืน)", "ชินจูกุตะวันออก (กลางคืน)", "ดิจิมอนเทมเมอร์ส", "หุบเขาแห่งแสงสว่าง", "d-รีพเปอร์"],
            "summary": "ดำดิ่งสู่โลกของ Digimon Tamers พบกับมัตสึดะ ทาคาโตะ, กิลมอน, ลี และรูคิ เผชิญหน้ากับการลุกลามของโปรแกรมลบข้อมูล 'D-Reaper' ที่กลืนกินย่านชินจูกุ ต่อสู้กับ ADR Agents เพื่อหยุดยั้งวันสิ้นโลก",
            "key_unlocks": ["ปลดล็อคดันเจี้ยน D-Reaper Zone และ Mother D-Reaper", "เปิดระบบ D-Unit System ระดับสูง", "ปลดล็อคสกิลเสริมและชิปเซ็ตระดับเลทเกม"],
            "pro_tips": ["ADR Agents ใน D-Reaper มีการสะท้อนดาเมจและดีบัฟลดคูลดาวน์สกิล ควรเตรียมดิจิมอนสายซัพพอร์ต", "แบ่งการทำเควสเป็นช่วงกลางวันและกลางคืนตามสายเนื้อเรื่องของทาคาโตะและลี"]
        },
        {
            "id": "ch9_kaiser",
            "number": 9,
            "title": "บทที่ 9: พื้นที่ของไกเซอร์ (Adventure 02)",
            "badge": "เลท-เอนด์",
            "level_range": "Lv. 130 - 155",
            "area_keywords": ["พาวเวอร์ดิจิมอน", "พื้นที่ของไกเซอร์", "พื้นที่แห่งความว่างเปล่า"],
            "summary": "เรื่องราวจาก Digimon Adventure 02 การผงาดขึ้นมาของดิจิมอนไกเซอร์ (อิจิโจจิ เคน) ผู้ใช้ดาร์คสไปรัลควบคุมจิตใจดิจิมอนและสร้างคิเมรามอนขึ้นมา เทมเมอร์ต้องนำพาแสงสว่างกลับคืนสู่อาณาจักร",
            "key_unlocks": ["ปลดล็อคดันเจี้ยนฐานทัพเรือดำน้ำและคิเมรามอน (Kimeramon Hard/Hero)", "เปิดสิทธิ์รับดาร์คสไปรัลและสร้อยคอไกเซอร์", "ปลดล็อคสายวิวัฒนาการของอาร์เมอร์และโจเกรส 02"],
            "pro_tips": ["ในเขตหอคอยความมืด ดิจิมอนจะไม่สามารถวิวัฒนาการได้ตามปกติ ให้เตรียมดิจิมอนร่าง Armor หรือใช้ไอเทมแก้สถานะ", "บอสคิเมรามอนมีสกิล AoE รุนแรง ให้คอยหลบวงแดงบนพื้นอย่างรวดเร็ว"]
        },
        {
            "id": "ch10_spiral_mountain",
            "number": 10,
            "title": "บทที่ 10: สไปรอลเมาท์เทน & 4 จอมปีศาจ",
            "badge": "เอนด์เกม",
            "level_range": "Lv. 140 - 165",
            "area_keywords": ["อาณาจักรโลหะ", "ป่าหุ่นเชิด", "เน็ตโอเชียน", "จุดสูงสุดของฝันร้าย", "ป่าแห่งการเริ่มต้น", "ทะเลสาปแห่งการเริ่มต้น", "หมู่บ้านแห่งการเริ่มต้น"],
            "summary": "ยอดเขาสไปรอลเมาท์เทนที่ถูกบิดเบือนโดย 4 จอมปีศาจ Dark Masters: เมทัลซีดรามอน, พิน็อคคีมอน, มูเกนดรามอน และพิเอมอน รวมพลังครั้งยิ่งใหญ่เพื่อทวงคืนป่าแห่งการเริ่มต้นและโลกดิจิตอลทั้งใบ",
            "key_unlocks": ["ปลดล็อคดันเจี้ยน Spiral Mountain Raid ทั้ง 4 เขต", "เปิดระบบตราประทับซีลมาสเตอร์และเด็คบัฟระดับ 4 จอมปีศาจ", "รับวัตถุดิบสร้างอุปกรณ์และต่างหูระดับ Endgame"],
            "pro_tips": ["บอสแต่ละตัวในสไปรอลเมาท์เทนมีกลไก (Mechanics) เฉพาะตัว เช่น มูเกนดรามอนต้องรีบทำลายเครื่องส่งสัญญาณ", "จำเป็นต้องมีสเตตัส AT, HT และ CT ขั้นต่ำตามเกณฑ์ของดันเจี้ยนจึงจะผ่านได้ง่าย"]
        },
        {
            "id": "ch11_frontier",
            "number": 11,
            "title": "บทที่ 11: ดิจิมอนฟรอนเทียร์ & เทอร์มินอลแห่งธาตุ",
            "badge": "เอนด์เกมสูงสุด (Patch ปัจจุบัน)",
            "level_range": "Lv. 160 - 180",
            "area_keywords": ["ดิจิมอนฟรอนเทียร์", "เทอร์มินัลแห่งเปลวเพลิง", "วินด์ แฟคทอรี่", "หมู่บ้านสายลมอ่อน", "โรงงานสายลม", "หมู่บ้านสายลม"],
            "summary": "แพตช์ล่าสุดของเซิร์ฟเวอร์ไทย เลเวลสูงสุด 180! ถ่ายทอดพลังสปิริตแห่งตำนาน ออกค้นหาดิจิโค้ดที่แปดเปื้อนในเทอร์มินัลแห่งเปลวเพลิงและโรงงานสายลม เพื่อกอบกู้ความสมดุลสูงสุดของระบบโลกดิจิตอล",
            "key_unlocks": ["ปลดล็อคสปิริตดิจิมอนร่างไฮบริด (Hybrid Spirit Evolution)", "เปิดแผนที่ฟาร์มเลเวล 160-180 ที่ดีที่สุดในเกม", "ปลดล็อคระบบสแกนดิจิโค้ดและไอเทมระดับสูงสุดของเซิร์ฟเวอร์ไทย"],
            "pro_tips": ["เนื้อหาเลเวล 160-180 มอนสเตอร์มีดาเมจสูงและมีเกราะป้องกันมหาศาล ควรมีบัฟเด็คและซีลมาสเตอร์ระดับสูง", "อย่าลืมรับเควสดิจิโค้ดประจำวันเพื่อสะสมแต้มแลกอุปกรณ์ระดับตำนาน"]
        }
    ]

    print("[3/5] Grouping quests by Map Section with exact unlock criteria...")

    def sort_chain(q_list):
        q_map = {q["id"]: q for q in q_list}
        ids = set(q_map.keys())
        graph = defaultdict(list)
        in_degree = {qid: 0 for qid in ids}
        for q in q_list:
            for pre in q.get("pre_quests", []):
                if pre in ids:
                    graph[pre].append(q["id"])
                    in_degree[q["id"]] += 1
        queue = [qid for qid in ids if in_degree[qid] == 0]
        queue.sort(key=lambda x: (q_map[x].get("level", 0), x))
        res = []
        visited = set()
        while queue:
            curr = queue.pop(0)
            res.append(q_map[curr])
            visited.add(curr)
            nxts = []
            for nxt in graph[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    nxts.append(nxt)
            nxts.sort(key=lambda x: (q_map[x].get("level", 0), x))
            queue.extend(nxts)
        leftovers = [q_map[qid] for qid in ids if qid not in visited]
        leftovers.sort(key=lambda x: (x.get("level", 0), x["id"]))
        res.extend(leftovers)
        return res

    output_chapters = []
    total_assigned_quests = 0

    for ch in chapters_def:
        ch_quests = []
        for qid, q in quests.items():
            if q["type"] in (1, 7):
                raw_m = q["raw_map_name"].lower()
                canon_m = q["map_name"].lower()
                if any(k.lower() in raw_m or k.lower() in canon_m for k in ch["area_keywords"]):
                    ch_quests.append(q)

        # Group quests in chapter by map
        map_groups = defaultdict(list)
        for q in ch_quests:
            map_groups[q["map_name"]].append(q)

        # For each map, sort quests, determine unlock requirements
        map_sections = []
        for map_title, m_quests in map_groups.items():
            sorted_m_qs = sort_chain(m_quests)
            if not sorted_m_qs: continue

            first_q = sorted_m_qs[0]
            pre_ids = first_q.get("pre_quests", [])
            
            unlock_req = {
                "text": "เริ่มได้ทันที / ไม่มีเงื่อนไขเควสก่อนหน้า",
                "pre_quest_id": None,
                "pre_quest_title": None,
                "pre_map_name": None,
                "min_level": max(first_q.get("level", 1), 1)
            }
            if pre_ids:
                pid = pre_ids[0]
                if pid in quests:
                    pq = quests[pid]
                    unlock_req = {
                        "text": f"ต้องทำเควสหลัก [{pq['title']}] ({pq['map_name']}) ให้สำเร็จก่อน",
                        "pre_quest_id": pid,
                        "pre_quest_title": pq["title"],
                        "pre_map_name": pq["map_name"],
                        "min_level": max(first_q.get("level", 1), pq.get("level", 1))
                    }
                else:
                    unlock_req["text"] = f"ต้องทำเควส #{pid} ให้สำเร็จก่อน"
                    unlock_req["pre_quest_id"] = pid

            m_levels = [q["level"] for q in sorted_m_qs if q["level"] > 0]
            min_l = min(m_levels) if m_levels else 1
            max_l = max(m_levels) if m_levels else 1
            
            map_sections.append({
                "map_name": map_title,
                "map_image": sorted_m_qs[0]["map_image"],
                "level_range": f"Lv. {min_l} - {max_l}" if min_l != max_l else f"Lv. {min_l}",
                "quest_count": len(sorted_m_qs),
                "unlock_requirement": unlock_req,
                "quests": sorted_m_qs
            })

        # Sort map sections by min level
        map_sections.sort(key=lambda m: (m["unlock_requirement"]["min_level"], m["map_name"]))

        ch_total_qs = sum(m["quest_count"] for m in map_sections)
        total_assigned_quests += ch_total_qs

        output_chapters.append({
            "id": ch["id"],
            "number": ch["number"],
            "title": ch["title"],
            "badge": ch["badge"],
            "level_range": ch["level_range"],
            "summary": ch["summary"],
            "key_unlocks": ch["key_unlocks"],
            "pro_tips": ch["pro_tips"],
            "quest_count": ch_total_qs,
            "maps": map_sections
        })
        print(f"  -> Chapter {ch['number']}: {ch['title']} ({len(map_sections)} maps, {ch_total_qs} quests)")

    full_payload = {
        "version": "thai_live_patch_v2",
        "generated_at": "2026-11-16",
        "max_level": 180,
        "total_chapters": len(output_chapters),
        "total_main_quests": total_assigned_quests,
        "chapters": output_chapters
    }

    print("[4/5] Saving main_quests.json...")
    out_file = STATIC_DATA_DIR / "main_quests.json"
    out_file.write_text(json.dumps(full_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> Wrote {out_file} ({out_file.stat().st_size:,} bytes)")

    cache_file = WEB_DIR / "main_quests_cache.json"
    cache_file.write_text(json.dumps(full_payload, ensure_ascii=False), encoding="utf-8")
    print(f"  -> Wrote {cache_file} ({cache_file.stat().st_size:,} bytes)")

    print("[5/5] Done! Guide dataset generated successfully.")

if __name__ == "__main__":
    build()
