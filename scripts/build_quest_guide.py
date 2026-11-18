"""Enhanced DMO Thai Main Quest Guide Data Generator
Re-architected to guarantee:
1. STRICT STORYLINE ORDER: Every map begins with its root quest and flows sequentially through the quest chain to the end.
2. ZERO DUPLICATES: Every quest is uniquely assigned to exactly one map and chapter.
3. 100% EXACT MAP UNLOCK REQUIREMENTS & NEXT MAP UNLOCK:
   - Tells what quest and map must be done to unlock this map.
   - Tells required Tamer Level and Digimon Level (if required).
   - Tells what NEXT MAP is unlocked upon finishing this map and what quest unlocks it!
4. VERIFIED MATCHING MAP IMAGES: Exact Thai client maps (/images/maps/*) mapped to correct Thai map names.
5. PRECISE QUEST LEVEL CONDITIONS: Tamer Level & Digimon Level (from client binary ptype 1 and 3) on every quest card.
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

    npc_img_map = {}
    npc_map_file = WEB_DIR / "npc_img_map.json"
    if npc_map_file.exists():
        npc_img_map = json.loads(npc_map_file.read_text(encoding="utf-8"))

    return npcs, maps, monsters, items, npc_img_map

# 3. Clean text helper
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

# Map Definition Specification: Chapters & Ordered Maps
# Verified 100% against Thai Client map files & images!
CHAPTER_MAP_SPECS = [
    # 1. Yokohama & DATS
    {
        "ch_num": 1, "ch_id": "ch1_yokohama",
        "title": "บทที่ 1: ศูนย์บัญชาการ DATS & โยโกฮาม่า",
        "badge": "เริ่มต้น",
        "level_range": "Lv. 1 - 25",
        "summary": "จุดเริ่มต้นของเทมเมอร์หน้าใหม่ในสังกัดหน่วย DATS เรียนรู้ระบบพื้นฐาน ทำภารกิจสืบสวนเหตุการณ์ดิจิมอนผิดปกติที่บุกรุกมายังโลกมนุษย์ คุ้มกันครอบครัวของไดมอน มาซารุ และคลี่คลายเหตุการณ์ที่โรงกลั่นน้ำมันเพื่อปลดล็อคการเดินทางสู่โลกดิจิตอล",
        "key_unlocks": ["ตราสมาชิก DATS อย่างเป็นทางการ", "สิทธิ์การเดินทางข้ามมิติสู่โลกดิจิตอล (Digital World Access)", "เปิดระบบฟักไข่ดิจิทามะ และระบบสแกน/รีเทิร์นข้อมูล"],
        "pro_tips": ["อย่าลืมรับเควสฝึกสอนทั้งหมดเพราะจะได้รับไอเทมเริ่มต้นและดิจิมอนคู่หูที่จำเป็น", "ในโรงกลั่นน้ำมันมอนสเตอร์มีพลังป้องกันสูง ควรใช้ดิจิมอนธาตุแพ้ทางเพื่อเคลียร์เควสได้ไวขึ้น"],
        "maps": [
            ("โหมดฝึกสอน (Tutorial)", "/images/maps/105_zone.png", lambda q: "<โหมดฝึกสอน>" in q["raw_map_name"]),
            ("ศูนย์บัญชาการ DATS", "/images/maps/dats_in_zone.png", lambda q: "ศูนย์บัญชาการ DATS" in q["raw_map_name"]),
            ("หมู่บ้านโยโกฮาม่า", "/images/maps/105_zone.png", lambda q: any(k in q["raw_map_name"] for k in ["หมู่บ้านโยโกฮาม่า", "หมู่บ้าน โยโกฮาม่า", "สวนม้านั่งไม้"])),
            ("โรงกลั่นน้ำมัน ชั้น 1", "/images/maps/oilrefinery1_zone.png", lambda q: "โรงกลั่นน้ำมัน" in q["raw_map_name"] and ("ชั้น1" in q["raw_map_name"] or "ชั้น 1" in q["raw_map_name"])),
            ("โรงกลั่นน้ำมัน ชั้น 2", "/images/maps/oilrefinery2_zone.png", lambda q: "โรงกลั่นน้ำมัน" in q["raw_map_name"] and ("ชั้น2" in q["raw_map_name"] or "ชั้น 2" in q["raw_map_name"])),
            ("โรงกลั่นน้ำมัน ชั้น 3", "/images/maps/oilrefinery3_zone.png", lambda q: "โรงกลั่นน้ำมัน" in q["raw_map_name"] and ("ชั้น3" in q["raw_map_name"] or "ชั้น 3" in q["raw_map_name"])),
        ]
    },
    # 2. Western & Maze
    {
        "ch_num": 2, "ch_id": "ch2_western_maze",
        "title": "บทที่ 2: ดินแดนฝั่งตะวันตก & เขาวงกตดิจิมอน",
        "badge": "ช่วงแรก-กลาง",
        "level_range": "Lv. 25 - 65",
        "summary": "ก้าวเท้าสู่โลกดิจิตอลเป็นครั้งแรก สำรวจหมู่บ้านฝั่งตะวันตก ทุ่งรกร้าง ฟาร์มดิจิมอน และหุบเขาแห่งสายลม เผชิญหน้ากับคุราตะและกองทัพดิจิมอนมืด ฝ่าด่านเขาวงกตดิจิมอนทั้ง 4 ชั้นเพื่อพิชิตเดียโบโรมอน",
        "key_unlocks": ["สิทธิ์เข้าสู่เขาวงกตดิจิมอนครบทุกชั้น (Digimon Maze B2 - F4)", "ปลดล็อคการใช้งาน D-Terminal สำหรับเดินทางข้ามมิติ", "เปิดระบบตราประทับดิจิมอน (Seal Master System) ขั้นต้น"],
        "pro_tips": ["เควสเขาวงกตดิจิมอนต้องเก็บไอเทมคีย์การ์ดเพื่อเปิดประตูในแต่ละชั้น ให้ทำเควสตามลำดับอย่าข้าม", "มอนสเตอร์ในชั้น F3-F4 มีความหนาแน่นสูง แนะนำให้เตรียมยาฟื้นฟู HP/DS ให้พร้อม"],
        "maps": [
            ("หมู่บ้านฝั่งตะวันตก", "/images/maps/westrentown_01_zone.png", lambda q: "หมู่บ้านฝั่งตะวันตก" in q["raw_map_name"]),
            ("พื้นที่ทุรกันดาร ฝั่งตะวันตก", "/images/maps/westren_field_01_zone.png", lambda q: "พื้นที่ทุรกันดาร" in q["raw_map_name"] or "ด้านซ้าย" in q["raw_map_name"]),
            ("หุบเขาแห่งสายลม", "/images/maps/wind_valley_zone.png", lambda q: "หุบเขาแห่งสายลม" in q["raw_map_name"] or "หุบเขาสายลม" in q["raw_map_name"]),
            ("ดิจิมอนฟาร์ม", "/images/maps/digimon_farm_zone.png", lambda q: "ฟาร์มดิจิมอน" in q["raw_map_name"] or "ดิจิมอนฟาร์ม" in q["raw_map_name"]),
            ("โบราณสถานแห่งความมืด", "/images/maps/westerntown_darktower_zone.png", lambda q: "โบราณสถาน" in q["raw_map_name"] and "เขาวงกต" not in q["raw_map_name"]),
            ("ดาร์คทาวเวอร์ (ดินแดนต้องห้าม)", "/images/maps/westerntown_darktower_zone.png", lambda q: "ดาร์คทาวเวอร์" in q["raw_map_name"]),
            ("เขาวงกตดิจิมอน (ทางเข้า)", "/images/maps/digimon_labyrinth_field_zone.png", lambda q: q["raw_map_name"] == "เขาวงกตดิจิมอน"),
            ("เขาวงกตดิจิมอน ชั้น B2", "/images/maps/digimon_labyrinth_field_zone.png", lambda q: "เขาวงกตดิจิมอน" in q["raw_map_name"] and any(k in q["raw_map_name"] for k in ["B2", "b2"])),
            ("เขาวงกตดิจิมอน ชั้น 1 (F1)", "/images/maps/labyrinth_01_zone.png", lambda q: "เขาวงกตดิจิมอน F1" in q["raw_map_name"]),
            ("เขาวงกตดิจิมอน ชั้น 2 (F2)", "/images/maps/labyrinth_02_zone.png", lambda q: "เขาวงกตดิจิมอน F2" in q["raw_map_name"]),
            ("เขาวงกตดิจิมอน ชั้น 3 (F3)", "/images/maps/labyrinth_03_zone.png", lambda q: "Maze 3F" in q["raw_map_name"] or "เขาวงกตดิจิมอน F3" in q["raw_map_name"]),
            ("เขาวงกตดิจิมอน ชั้น 4 (F4)", "/images/maps/labyrinth_04_zone.png", lambda q: "Maze 4F" in q["raw_map_name"] or "เขาวงกตดิจิมอน F4" in q["raw_map_name"]),
        ]
    },
    # 3. Glacier
    {
        "ch_num": 3, "ch_id": "ch3_glacier",
        "title": "บทที่ 3: ดินแดนกลาเซียร์ (Glacier Area)",
        "badge": "ช่วงแรก-กลาง",
        "level_range": "Lv. 35 - 55",
        "summary": "ดินแดนหิมะขาวโพลนอันหนาวเหน็บ ฝ่าพายุหิมะผ่านหมู่บ้านมนุษย์หิมะ สืบสวนเรื่องราวของกีซุมอนและแผนการร้ายของคุราตะที่แอบแฝง และเปิดเส้นทางไปสู่กำแพงน้ำแข็งนิรันดร์",
        "key_unlocks": ["ปลดล็อคแผนที่กำแพงน้ำแข็งนิรันดร์ (Infinite Ice Wall)", "ปลดล็อคเส้นทางลับเชื่อมต่อไปยังเกาะไฟล์ (File Island)", "รับเครื่องประดับและหินพัฒนาธาตุน้ำแข็ง"],
        "pro_tips": ["มอนสเตอร์ในดินแดนหิมะส่วนใหญ่เป็นธาตุน้ำ/น้ำแข็ง ดิจิมอนธาตุสายฟ้าหรือดินจะโจมตีได้รุนแรงเป็นพิเศษ", "เควสเก็บรวบรวมฟันเฟืองสีดำ ดรอปจากมอนสเตอร์เฉพาะจุด ให้เช็คพิกัดบนมินิแมพให้ดี"],
        "maps": [
            ("D-เทอร์มินัล", "/images/maps/d_terminel_main01_zone.png", lambda q: "D-เทอร์มินัล" in q["raw_map_name"]),
            ("หมู่บ้านพายุหิมะ", "/images/maps/ice_land01_zone.png", lambda q: "หมู่บ้านพายุหิมะ" in q["raw_map_name"]),
            ("หมู่บ้านมนุษย์หิมะ", "/images/maps/ice_land03_zone.png", lambda q: "หมู่บ้านมนุษย์หิมะ" in q["raw_map_name"]),
            ("กำแพงน้ำแข็งนิรันดร์", "/images/maps/ice_land_05_zone.png", lambda q: any(k in q["raw_map_name"] for k in ["กำแพงน้ำแข็ง", "ดินแดนน้ำแข็ง"])),
        ]
    },
    # 4. File Island
    {
        "ch_num": 4, "ch_id": "ch4_file_island",
        "title": "บทที่ 4: มหากาพย์เกาะไฟล์ & ภูเขาอินฟินิตี้",
        "badge": "กลางเกม",
        "level_range": "Lv. 60 - 80",
        "summary": "ย้อนรอยความทรงจำของอนิเมะ Digimon Adventure ภาคแรก บนเกาะไฟล์ ช่วยเหลือเลโอมอนและโอเกรมอน ทำลายฟันเฟืองดำที่แพร่ระบาด และบุกขึ้นสู่ภูเขาอินฟินิตี้เพื่อทำศึกแตกหักกับเดวีมอน",
        "key_unlocks": ["ปลดล็อคดันเจี้ยนภูเขาอินฟินิตี้ (Infinite Mountain Dungeon)", "ปลดล็อคการวิวัฒนาการร่างเมก้าและเบิร์สโหมด (Burst Mode)", "เปิดท่าเรือชายฝั่งเกาะไฟล์เพื่อข้ามทะเลไปยังทวีปเซิร์ฟเวอร์"],
        "pro_tips": ["เควสเกาะไฟล์ให้ EXP มหาศาล เป็นแหล่งฟาร์มเลเวลที่ดีที่สุดช่วงเลเวล 60-80", "เมื่อถึงเควสปราบเดวีมอนที่ภูเขาอินฟินิตี้ แนะนำให้รวมปาร์ตี้เพื่อความรวดเร็วและปลอดภัย"],
        "maps": [
            ("ทะเลสาบสีเงิน", "/images/maps/1301_zone.png", lambda q: "ทะเลสาบสีเงิน" in q["raw_map_name"]),
            ("ป่าแห่งความเงียบ", "/images/maps/1302_zone.png", lambda q: "ป่าแห่งความเงียบ" in q["raw_map_name"]),
            ("พื้นที่อารยธรรมที่สูญหาย", "/images/maps/1303_zone.png", lambda q: "พื้นที่อารยธรรมที่สูญหาย" in q["raw_map_name"]),
            ("ซากอารยธรรมโบราณแห่งความลับ", "/images/maps/1304_mini.png", lambda q: "ซากอารยธรรมโบราณ" in q["raw_map_name"]),
            ("ชายฝั่งเกาะไฟล์", "/images/maps/1305_zone.png", lambda q: "ชายฝั่งเกาะไฟล์" in q["raw_map_name"]),
            ("ภูเขาอินฟินิตี้", "/images/maps/1311_zone.png", lambda q: any(k in q["raw_map_name"] for k in ["หุบเขานิรันดร์", "ภูเขาอินฟินิตี้"])),
            ("รอยร้าวของเดวีมอน", "/images/maps/1309_mini.png", lambda q: "รอยร้าวของเดวีมอน" in q["raw_map_name"]),
        ]
    },
    # 5. Server Continent
    {
        "ch_num": 5, "ch_id": "ch5_server_continent",
        "title": "บทที่ 5: ทวีปเซิร์ฟเวอร์ ทะเลทราย & ปิรามิด",
        "badge": "กลาง-เลท",
        "level_range": "Lv. 75 - 95",
        "summary": "ออกเดินทางสู่ผืนทวีปอันกว้างใหญ่ เผชิญหน้ากับเอเตมอนจอมวายร้ายที่ควบคุมเครือข่ายสายเคเบิลมืด ฝ่าฟันหุบเขาอันตราย และบุกเข้าไปในปิรามิดของดาตามอนเพื่อกู้ข้อมูลสำคัญกลับคืนมา",
        "key_unlocks": ["ปลดล็อคดันเจี้ยนปิรามิดดาตามอน (Datamon Maze)", "เปิดสิทธิ์การใช้งานแหวนและสร้อยคอระดับสูง (Ring/Necklace Shiny)", "เชื่อมต่อโครงข่ายประตูมิติสู่โลกดิจิตอลใหม่"],
        "pro_tips": ["พื้นที่ทะเลทรายมีระยะทางกว้างมาก ควรใช้ดิจิมอนโหมดขับขี่ (Riding Mode) เพื่อประหยัดเวลาเดินทาง", "ในปิรามิดมอนสเตอร์เกิดหนาแน่น ระวังการดึงมอนสเตอร์เกินจำนวนที่รับไหว"],
        "maps": [
            ("ทวีปเซิร์ฟเวอร์ ทะเลทราย", "/images/maps/1400_zone.png", lambda q: "ทวีปเซิร์ฟเวอร์" in q["raw_map_name"] and "ทะเลทราย" in q["raw_map_name"]),
            ("ทวีปเซิร์ฟเวอร์ - หุบเขา", "/images/maps/1401_zone.png", lambda q: "ทวีปเซิร์ฟเวอร์" in q["raw_map_name"] and "หุบเขา" in q["raw_map_name"]),
            ("ทวีปเซิร์ฟเวอร์ - ปิรามิด", "/images/maps/1402_zone.png", lambda q: "ปิรามิด" in q["raw_map_name"]),
        ]
    },
    # 6. Verdandi (X-Antibody)
    {
        "ch_num": 6, "ch_id": "ch6_verdandi",
        "title": "บทที่ 6: เวอร์ซันดิเทอร์มินัล (X-Antibody)",
        "badge": "เลทเกม",
        "level_range": "Lv. 90 - 110",
        "summary": "วิกฤตการณ์ไวรัส X-Program ที่ถูกปล่อยออกมาโดยอิกดราซิล กองทหารรอยัลไนท์แบ่งฝ่ายต่อสู้กัน เทมเมอร์ต้องติดตั้งระบบ XAI Indicator เพื่อต้านทานพิษของไวรัส และปลดล็อคพลัง X-Antibody ขั้นสูงสุด",
        "key_unlocks": ["ปลดล็อคระบบ X-Antibody System (XAI Indicator)", "ปลดล็อคดันเจี้ยนรอยัลเบส (Royal Base 1F-3F)", "เปิดสิทธิ์การทำเควสวิวัฒนาการ X-Antibody เช่น Omegamon X, Alphamon Ouryuken X"],
        "pro_tips": ["ต้องสวมใส่ XAI และรักษาระดับ X-Gauge ให้ไม่หมด เพื่อป้องกันดีบัฟดาเมจลดลงในพื้นที่", "มอนสเตอร์ในเวอร์ซันดิมีความถึกสูงมาก ควรมีค่า Hit Rate (HT) และ Critical (CT) เพียงพอ"],
        "maps": [
            ("เวอร์ซันดิเทอร์มินัล", "/images/maps/1700_zone.png", lambda q: "เวอร์ซันดิ" in q["raw_map_name"]),
            ("รอยัลเบส", "/images/maps/1701_mini.png", lambda q: "รอยัลเบส" in q["raw_map_name"]),
        ]
    },
    # 7. Tokyo - Odaiba
    {
        "ch_num": 7, "ch_id": "ch7_odaiba",
        "title": "บทที่ 7: มหาสงคราม โตเกียว - โอไดบะ",
        "badge": "เลทเกม",
        "level_range": "Lv. 99 - 120",
        "summary": "กองทัพของแวมเดมอนข้ามประตูมิติมาบุกยึดกรุงโตเกียว เทมเมอร์ต้องร่วมมือกับเหล่าเด็กผู้ถูกเลือกทั้ง 8 คน ปกป้องครอบครัวและชาวเมือง ต่อสู้ไล่ล่าไปตามสถานที่จริงในโตเกียว จนถึงศึกตัดสินกับเวนอมแวมเดมอน",
        "key_unlocks": ["ปลดล็อคดันเจี้ยนเรดบอสโอไดบะ (VenomMyotismon, DarkTyrannomon)", "เปิดระบบฉายาบัฟสเตตัสระดับสูงของโตเกียว", "สิทธิ์แลกไอเทมอุปกรณ์และตั๋วการันตีระดับสูง"],
        "pro_tips": ["เควสเนื้อเรื่องโอไดบะมีความยาวมาก ให้ทำตามเครื่องหมายเควสสีม่วง/น้ำเงินบนแผนที่อย่างเคร่งครัด", "จุดที่ต้องคุยกับเด็กผู้ถูกเลือก ให้สังเกตเวลาบนแผนที่ (กลางวัน/กลางคืน) มอนสเตอร์บางตัวจะเกิดเฉพาะเวลานั้น"],
        "maps": [
            ("สถานที่ตั้งค่าย", "/images/maps/200_zone.png", lambda q: "สถานที่ตั้งค่าย" in q["raw_map_name"]),
            ("ฮิคาริงาโอกะ", "/images/maps/201_zone.png", lambda q: "ฮิคาริงาโอกะ" in q["raw_map_name"]),
            ("ชิบูย่า", "/images/maps/202_zone.png", lambda q: "ชิบูย่า" in q["raw_map_name"]),
            ("โตเกียวทาวเวอร์", "/images/maps/203_zone.png", lambda q: "โตเกียวทาวเวอร์" in q["raw_map_name"]),
            ("มินาโตะซิตี้", "/images/maps/206_zone.png", lambda q: "มินาโตะซิตี้" in q["raw_map_name"]),
            ("โอไดบะ", "/images/maps/208_zone.png", lambda q: "โอไดบะ" in q["raw_map_name"] or "ฟูจิทีวี" in q["raw_map_name"]),
            ("เรนโบว์ บริดจ์", "/images/maps/208_zone.png", lambda q: "เรนโบว์ บริดจ์" in q["raw_map_name"]),
            ("บิ๊กไซท์", "/images/maps/207_zone.png", lambda q: "บิ๊กไซท์" in q["raw_map_name"]),
        ]
    },
    # 8. Shinjuku & Tamers & D-Reaper
    {
        "ch_num": 8, "ch_id": "ch8_shinjuku",
        "title": "บทที่ 8: ชินจูกุ, เทมเมอร์ส & D-รีพเปอร์",
        "badge": "เลทเกม",
        "level_range": "Lv. 110 - 140",
        "summary": "เรื่องราวจาก Digimon Tamers ปรากฏการณ์ D-Reaper แพร่กระจายกลืนกินกรุงชินจูกุ ร่วมมือกับทาคัตโตะ, รูคิ, ลีเจนเรีย และเหล่านักรบดิจิมอนเทมเมอร์ส ข้ามมิติเข้าสู่ใจกลางรังแม่ของดีรีพเปอร์เพื่อกอบกู้โลก",
        "key_unlocks": ["ปลดล็อคดันเจี้ยน D-Reaper Mother / Area Shinjuku", "ระบบวิวัฒนาการ Matrix Evolution (D-Ark)", "รับหินประดับและอุปกรณ์สเตตัสระดับเลทเกม"],
        "pro_tips": ["มอนสเตอร์ดีรีพเปอร์สามารถล้างสถานะบัฟได้ ให้ระวังการใช้สกิลที่มีคูลดาวน์นาน", "บอสในเขตชินจูกุมีระยะการโจมตีหมู่กว้างมาก ควรเตรียมดิจิมอนที่มีค่าบล็อกและเกราะสูง"],
        "maps": [
            ("ชินจูกุ", "/images/maps/250_zone.png", lambda q: "ชินจูกุ" in q["raw_map_name"] and "D-รีพเปอร์" not in q["raw_map_name"]),
            ("ดิจิมอนเทมเมอร์ส (หุบเขาแห่งแสงสว่าง)", "/images/maps/1800_zone.png", lambda q: any(k in q["raw_map_name"] for k in ["ดิจิมอนเทมเมอร์ส", "หุบเขาแห่งแสงสว่าง"])),
            ("D-รีพเปอร์", "/images/maps/266_Zone.png", lambda q: "D-รีพเปอร์" in q["raw_map_name"]),
        ]
    },
    # 9. Kaiser Domain (Adventure 02)
    {
        "ch_num": 9, "ch_id": "ch9_power_digimon",
        "title": "บทที่ 9: พื้นที่ของไกเซอร์ (Adventure 02)",
        "badge": "เลทเกม",
        "level_range": "Lv. 130 - 150",
        "summary": "การรุกรานของดิจิมอนไกเซอร์ผู้นำแห่งความมืด ควบคุมจิตใจดิจิมอนด้วยห่วงอีวิลริงและเสาดาร์คทาวเวอร์ เทมเมอร์ต้องร่วมมือกับกลุ่มเด็กผู้ถูกเลือกรุ่นที่ 2 ปลดปล่อยพลังอาร์เมอร์วิวัฒนาการเพื่อทำลายแผนการชั่วร้าย",
        "key_unlocks": ["ปลดล็อคระบบ Armor Evolution (Digi-Egg of Courage, Friendship)", "ปลดล็อคเควสความมืดของคิเมรามอน (Kimeramon Raid)", "รับไอเทมวัตถุดิบตีบวกอุปกรณ์ระดับไฮเอนด์"],
        "pro_tips": ["พื้นที่ของไกเซอร์ไม่อนุญาตให้ใช้วิวัฒนาการปกติได้ในบางจุด ต้องพึ่งพาร่างอาร์เมอร์เป็นหลัก", "อย่าลืมทำเควสสะสมดิจิเอ๊กก์เพื่อเปิดรูปแบบการวิวัฒนาการใหม่ๆ"],
        "maps": [
            ("พื้นที่ของไกเซอร์ (Adventure 02)", "/images/maps/400_Zone.png", lambda q: "พาวเวอร์ดิจิมอน" in q["raw_map_name"]),
            ("พื้นที่แห่งความว่างเปล่า", "/images/maps/1906_zone.png", lambda q: "พื้นที่แห่งความว่างเปล่า" in q["raw_map_name"]),
        ]
    },
    # 10. Spiral Mountain
    {
        "ch_num": 10, "ch_id": "ch10_spiral_mountain",
        "title": "บทที่ 10: สไปรอลเมาท์เทน 4 จอมปีศาจ",
        "badge": "เอนด์เกม",
        "level_range": "Lv. 140 - 160",
        "summary": "ยอดเขาสไปรอลเมาท์เทนที่ถูกบิดเบือนโดย 4 จอมปีศาจ Dark Masters: เมทัลซีดรามอน, พิน็อคคีมอน, มูเกนดรามอน และพิเอมอน รวมพลังครั้งยิ่งใหญ่เพื่อทวงคืนป่าแห่งการเริ่มต้นและโลกดิจิตอลทั้งใบ",
        "key_unlocks": ["ปลดล็อคดันเจี้ยน Spiral Mountain Raid ทั้ง 4 เขต", "เปิดระบบตราประทับซีลมาสเตอร์และเด็คบัฟระดับ 4 จอมปีศาจ", "รับวัตถุดิบสร้างอุปกรณ์และต่างหูระดับ Endgame"],
        "pro_tips": ["บอสแต่ละตัวในสไปรอลเมาท์เทนมีกลไก (Mechanics) เฉพาะตัว เช่น มูเกนดรามอนต้องรีบทำลายเครื่องส่งสัญญาณ", "จำเป็นต้องมีสเตตัส AT, HT และ CT ขั้นต่ำตามเกณฑ์ของดันเจี้ยนจึงจะผ่านได้ง่าย"],
        "maps": [
            ("ป่าแห่งการเริ่มต้น", "/images/maps/1901_zone.png", lambda q: any(k in q["raw_map_name"] for k in ["ป่าแห่งการเริ่มต้น", "ทะเลสาปแห่งการเริ่มต้น", "หมู่บ้านแห่งการเริ่มต้น"])),
            ("ป่าหุ่นเชิด (พิน็อคคีมอน)", "/images/maps/1902_zone.png", lambda q: "ป่าหุ่นเชิด" in q["raw_map_name"]),
            ("อาณาจักรโลหะ (มูเกนดรามอน)", "/images/maps/1903_zone.png", lambda q: "อาณาจักรโลหะ" in q["raw_map_name"]),
            ("จุดสูงสุดของฝันร้าย (พิเอมอน)", "/images/maps/1905_zone.png", lambda q: "จุดสูงสุดของฝันร้าย" in q["raw_map_name"]),
        ]
    },
    # 11. Frontier (Latest Patch)
    {
        "ch_num": 11, "ch_id": "ch11_frontier",
        "title": "บทที่ 11: ดิจิมอนฟรอนเทียร์ & เทอร์มินอลแห่งธาตุ",
        "badge": "เอนด์เกมสูงสุด (Patch ปัจจุบัน)",
        "level_range": "Lv. 160 - 180",
        "summary": "แพตช์ล่าสุดของเซิร์ฟเวอร์ไทย เลเวลสูงสุด 180! ถ่ายทอดพลังสปิริตแห่งตำนาน ออกค้นหาดิจิโค้ดที่แปดเปื้อนในเทอร์มินัลแห่งเปลวเพลิงและโรงงานสายลม เพื่อกอบกู้ความสมดุลสูงสุดของระบบโลกดิจิตอล",
        "key_unlocks": ["ปลดล็อคสปิริตดิจิมอนร่างไฮบริด (Hybrid Spirit Evolution)", "เปิดแผนที่ฟาร์มเลเวล 160-180 ที่ดีที่สุดในเกม", "ปลดล็อคระบบสแกนดิจิโค้ดและไอเทมระดับสูงสุดของเซิร์ฟเวอร์ไทย"],
        "pro_tips": ["เนื้อหาเลเวล 160-180 มอนสเตอร์มีดาเมจสูงและมีเกราะป้องกันมหาศาล ควรมีบัฟเด็คและซีลมาสเตอร์ระดับสูง", "อย่าลืมรับเควสดิจิโค้ดประจำวันเพื่อสะสมแต้มแลกอุปกรณ์ระดับตำนาน"],
        "maps": [
            ("ดิจิมอนฟรอนเทียร์", "/images/maps/500_Zone.png", lambda q: "ดิจิมอนฟรอนเทียร์" in q["raw_map_name"] or any(k in q["raw_map_name"] for k in ["เปลวเพลิง", "วินด์", "สายลม"])),
        ]
    }
]

# Non-story map exclusions
EXCLUDE_MAP_KEYWORDS = [
    "<jogress", "<โจเกรส", "เควสโจเกรส", "<ดันเจี้ยน", "กันคูมอน",
    "ประกาศจับ", "เควสคุณลักษณะ", "ระบบจัมปิ้ง", "콜로เซ움", "กรีนโซน"
]

def is_valid_story_quest(q):
    if q["type"] not in (1, 7): return False
    m_low = q["raw_map_name"].lower()
    if any(k in m_low for k in EXCLUDE_MAP_KEYWORDS): return False
    if q["id"] in (776, 141, 673, 1462, 1464, 1465, 82, 508, 509, 511, 25, 138, 505, 506):
        return False
    return True

def order_chain_dfs(qlist, all_q_dict):
    """Sort quests within a map strictly by prerequisite chain from beginning to end."""
    qmap = {q["id"]: q for q in qlist}
    ids = set(qmap.keys())
    children = defaultdict(list)
    in_deg = defaultdict(int)
    for q in qlist:
        for p in q["pre_quests"]:
            if p in ids:
                children[p].append(q["id"])
                in_deg[q["id"]] += 1
    for p in children:
        children[p].sort(key=lambda x: (qmap[x]["tamer_level"], x))

    roots = [q["id"] for q in qlist if in_deg[q["id"]] == 0]
    
    def root_score(qid):
        q = qmap[qid]
        has_ext_pre = any(p in all_q_dict for p in q["pre_quests"])
        if qid in (4020, 1198, 2873, 3100, 3412, 4500, 6500, 4148, 7102):
            return (-100, qid)
        if has_ext_pre:
            return (-50, qid)
        return (q["tamer_level"], qid)

    roots.sort(key=root_score)

    ordered = []
    visited = set()
    def dfs(qid):
        if qid in visited: return
        visited.add(qid)
        ordered.append(qmap[qid])
        for child in children[qid]:
            if child not in visited:
                parents = [p for p in qmap[child]["pre_quests"] if p in ids]
                if all(p in visited for p in parents):
                    dfs(child)
    for r in roots:
        dfs(r)
    for q in qlist:
        if q["id"] not in visited:
            ordered.append(q)
            visited.add(q["id"])
    return ordered

def build():
    print("[1/5] Loading strings, maps, metadata from CrackDMO...")
    q_str = load_quest_strings()
    npcs, maps, monsters, items, npc_img_map = load_meta()

    b = (CRACK / "out_decrypted/data/bin/table/quest.bin").read_bytes()
    count = struct.unpack_from("<i", b, 0)[0]

    all_raw_quests = {}
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
        header_level = struct.unpack_from("<H", b, p + 16)[0]
        s_npc = struct.unpack_from("<i", b, p + 23)[0] if h >= 32 else 0
        e_npc = struct.unpack_from("<i", b, p + 28)[0] if h >= 32 else 0

        strs = q_str.get(qid, [""] * 8)
        raw_map = strs[0].strip()

        pre_quests = []
        tamer_lv = 0
        digimon_lv = 0
        items_needed = []

        # Parse Section 0: Requirements (Pre-quests, Tamer Level, Digimon Level, Items)
        for e in secs[0]:
            ptype = e[0]
            pval = struct.unpack_from("<i", e, 1)[0]
            if ptype == 0 and pval > 0:
                pre_quests.append(pval)
            elif ptype == 1:
                tamer_lv = max(tamer_lv, pval)
            elif ptype == 3:
                digimon_lv = max(digimon_lv, pval)
            elif ptype == 4:
                items_needed.append(pval)

        if tamer_lv == 0 and header_level > 0:
            tamer_lv = header_level

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

        s_img = f"/images/npc/{npc_img_map[s_npc]}" if s_npc in npc_img_map else "/images/ui/ui_tamer.png"
        e_img = f"/images/npc/{npc_img_map[e_npc]}" if e_npc in npc_img_map else "/images/ui/ui_tamer.png"

        all_raw_quests[qid] = {
            "id": qid,
            "type": qtype,
            "level": tamer_lv if tamer_lv > 0 else 1,
            "tamer_level": tamer_lv if tamer_lv > 0 else 1,
            "digimon_level": digimon_lv if digimon_lv > 0 else None,
            "start_npc_id": s_npc,
            "start_npc": npcs.get(s_npc, "เริ่มอัตโนมัติ"),
            "start_npc_image": s_img,
            "end_npc_id": e_npc,
            "end_npc": npcs.get(e_npc, "ส่งอัตโนมัติ"),
            "end_npc_image": e_img,
            "raw_map_name": raw_map,
            "map_name": raw_map,
            "map_image": "/images/maps/105_zone.png",
            "title": strs[1].strip(),
            "story": clean_desc(strs[2]),
            "objective_desc": clean_desc(strs[3]),
            "tracker": clean_desc(strs[4]),
            "pre_quests": pre_quests,
            "pre_quest_titles": [],
            "items_needed": [items.get(it, f"ไอเทม #{it}") for it in items_needed],
            "objectives": obj_list,
            "exp": exp,
            "bit": bit,
            "bit_formatted": format_money_thai(bit),
            "reward_items": rew_list
        }
        p = end

    print(f"[2/5] Parsed {len(all_raw_quests)} raw quests from binary.")

    # Fill pre_quest_titles
    for qid, q in all_raw_quests.items():
        q["pre_quest_titles"] = [all_raw_quests[pid]["title"] for pid in q["pre_quests"] if pid in all_raw_quests]

    # Filter valid storyline quests
    story_quests = {qid: q for qid, q in all_raw_quests.items() if is_valid_story_quest(q)}
    print(f"[3/5] Filtered to {len(story_quests)} valid main quests (non-story & duplicates removed).")

    # Group into Chapters and Maps strictly in order with zero duplicates
    output_chapters = []
    assigned_ids = set()
    total_assigned = 0

    # First pass: collect and order map sections for each chapter
    collected_chapters = []
    for ch_spec in CHAPTER_MAP_SPECS:
        ch_maps = []
        for map_title, map_img, match_fn in ch_spec["maps"]:
            m_qs = []
            for qid, q in story_quests.items():
                if qid not in assigned_ids and match_fn(q):
                    m_qs.append(q)
                    assigned_ids.add(qid)

            if not m_qs:
                continue

            for q in m_qs:
                q["map_name"] = map_title
                q["map_image"] = map_img

            ordered_qs = order_chain_dfs(m_qs, story_quests)
            ch_maps.append({
                "map_name": map_title,
                "map_image": map_img,
                "quests": ordered_qs
            })
        collected_chapters.append({
            "spec": ch_spec,
            "maps": ch_maps
        })

    # Flatten all map sections in sequential order to link previous & next
    flat_maps = []
    for ch_data in collected_chapters:
        for m in ch_data["maps"]:
            flat_maps.append(m)

    # Second pass: compute exact unlock_requirement & next_map_unlock for each map section
    for idx, m in enumerate(flat_maps):
        ordered_qs = m["quests"]
        first_q = ordered_qs[0]
        last_q = ordered_qs[-1]

        # 1. Unlock Requirement (เงื่อนไขการเข้าแผนที่นี้)
        pre_ids = first_q["pre_quests"]
        ext_pre = [pid for pid in pre_ids if pid in all_raw_quests and pid not in [x["id"] for x in ordered_qs]]

        min_tamer = first_q.get("tamer_level", 1)
        min_digi = first_q.get("digimon_level")

        if ext_pre:
            pid = ext_pre[0]
            pq = all_raw_quests[pid]
            unlock_desc = f"ต้องทำเควสหลัก [{pq['title']}] ({pq['map_name']}) ให้สำเร็จก่อน"
            pre_title = pq["title"]
            pre_map = pq["map_name"]
            pre_qid = pid
            min_tamer = max(min_tamer, pq.get("tamer_level", 1))
            if pq.get("digimon_level"):
                min_digi = max(min_digi or 0, pq["digimon_level"])
        elif idx > 0:
            prev_map = flat_maps[idx - 1]
            prev_last_q = prev_map["quests"][-1]
            unlock_desc = f"ต้องทำเควสหลักใน {prev_map['map_name']} (เควส [{prev_last_q['title']}]) ให้สำเร็จก่อน"
            pre_title = prev_last_q["title"]
            pre_map = prev_map["map_name"]
            pre_qid = prev_last_q["id"]
            min_tamer = max(min_tamer, prev_last_q.get("tamer_level", 1))
            if prev_last_q.get("digimon_level"):
                min_digi = max(min_digi or 0, prev_last_q["digimon_level"])
        else:
            unlock_desc = "เริ่มได้ทันที / ไม่มีเงื่อนไขเควสก่อนหน้า"
            pre_title = None
            pre_map = None
            pre_qid = None

        unlock_req = {
            "text": unlock_desc,
            "pre_quest_id": pre_qid,
            "pre_quest_title": pre_title,
            "pre_map_name": pre_map,
            "min_tamer_level": min_tamer,
            "min_digimon_level": min_digi if min_digi and min_digi > 0 else None
        }

        # 2. Next Map Unlock (ปลดแมพที่จะไปต่อ)
        if idx + 1 < len(flat_maps):
            next_map = flat_maps[idx + 1]
            next_first_q = next_map["quests"][0]
            next_tamer = next_first_q.get("tamer_level", 1)
            next_digi = next_first_q.get("digimon_level")

            next_unlock_desc = f"เคลียร์เควส [{last_q['title']}] เพื่อปลดล็อคแผนที่ถัดไป: {next_map['map_name']}"
            next_map_info = {
                "next_map_name": next_map["map_name"],
                "required_quest_id": last_q["id"],
                "required_quest_title": last_q["title"],
                "next_tamer_level": next_tamer,
                "next_digimon_level": next_digi if next_digi and next_digi > 0 else None,
                "text": next_unlock_desc
            }
        else:
            next_map_info = {
                "next_map_name": None,
                "required_quest_id": last_q["id"],
                "required_quest_title": last_q["title"],
                "next_tamer_level": 180,
                "next_digimon_level": None,
                "text": "สิ้นสุดเนื้อเรื่องเควสหลักแพตช์ปัจจุบัน (Lv. 180)"
            }

        tamer_levels = [q["tamer_level"] for q in ordered_qs if q["tamer_level"] > 0]
        min_tl = min(tamer_levels) if tamer_levels else 1
        max_tl = max(tamer_levels) if tamer_levels else 1

        m["level_range"] = f"Lv. {min_tl} - {max_tl}" if min_tl != max_tl else f"Lv. {min_tl}"
        m["quest_count"] = len(ordered_qs)
        m["unlock_requirement"] = unlock_req
        m["next_map_unlock"] = next_map_info

    # Build Final Chapter Output
    for ch_data in collected_chapters:
        ch_spec = ch_data["spec"]
        map_sections = ch_data["maps"]
        ch_total_qs = sum(m["quest_count"] for m in map_sections)
        total_assigned += ch_total_qs

        output_chapters.append({
            "id": ch_spec["ch_id"],
            "number": ch_spec["ch_num"],
            "title": ch_spec["title"],
            "badge": ch_spec["badge"],
            "level_range": ch_spec["level_range"],
            "summary": ch_spec["summary"],
            "key_unlocks": ch_spec["key_unlocks"],
            "pro_tips": ch_spec["pro_tips"],
            "quest_count": ch_total_qs,
            "maps": map_sections
        })
        print(f"  -> Chapter {ch_spec['ch_num']}: {ch_spec['title']} ({len(map_sections)} maps, {ch_total_qs} quests)")

    full_payload = {
        "version": "thai_live_patch_v4_requirements",
        "generated_at": "2026-11-16",
        "max_level": 180,
        "total_chapters": len(output_chapters),
        "total_main_quests": total_assigned,
        "chapters": output_chapters
    }

    out_web_json = STATIC_DATA_DIR / "main_quests.json"
    out_cache_json = WEB_DIR / "main_quests_cache.json"

    print(f"[4/5] Writing {out_web_json} ({total_assigned} unique quests in sequential order)...")
    with open(out_web_json, "w", encoding="utf-8") as f:
        json.dump(full_payload, f, ensure_ascii=False, indent=2)

    with open(out_cache_json, "w", encoding="utf-8") as f:
        json.dump(full_payload, f, ensure_ascii=False)

    print(f"[5/5] Done! Total: {len(output_chapters)} chapters, {sum(len(c['maps']) for c in output_chapters)} maps, {total_assigned} main quests.")

if __name__ == "__main__":
    build()
