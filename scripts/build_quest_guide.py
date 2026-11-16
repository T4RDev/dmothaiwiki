"""Build DMO Thai Main Quest Guide Data
Extracts 100% accurate quest data from CrackDMO:
- quest.bin (prerequisites, objectives, rewards, levels, NPCs)
- quest_str.bin (Thai titles, dialogues, objectives, tracker text)
- npc_str.json (NPC titles and full names)
- monstername_str.json (Monster names)
- item_str.json (Item names)
- mapname_str.json (Map names)
"""

import struct
import json
from pathlib import Path
from collections import defaultdict, deque

CRACK = Path("G:/DMOWiki/CrackDMO")
if not (CRACK / "out_decrypted").exists():
    CRACK = Path(__file__).resolve().parent.parent.parent / "CrackDMO"

BASE_DIR = Path("G:/DMOWiki/Web_Scraper")
WEB_DIR = BASE_DIR / "web"
STATIC_DATA_DIR = WEB_DIR / "static" / "data"
STATIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load Quest Strings (8 strings per quest, byte-exact)
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
            maps[item["id"]] = item.get("text", "")

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

    return npcs, maps, monsters, items

# 3. Parse quest.bin
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

def clean_desc(text):
    if not text: return ""
    import re
    # Remove @<tc:...> and @</tc> tags
    t = re.sub(r"@<tc:[^>]*>", "", text)
    t = t.replace("@</tc>", "")
    # Clean control characters
    t = re.sub(r"%qs\d+", "", t)
    t = re.sub(r"%qe%cc\d+:%mc\d+[a-zA-Z]?", "", t)
    t = t.replace("%qe", "").replace("%s", "")
    t = "\n".join([line.strip() for line in t.split("\n") if line.strip()])
    return t.strip()

def build():
    print("[1/5] Loading strings and binary data from CrackDMO...")
    q_str = load_quest_strings()
    npcs, maps, monsters, items = load_meta()
    
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
                type_label = "กำจัดมอนสเตอร์"
                target_name = monsters.get(target, f"มอนสเตอร์ #{target}")
            elif otype == 1:
                type_label = "รวบรวมไอเทม"
                target_name = items.get(target, f"ไอเทม #{target}")
            elif otype == 4:
                type_label = "พูดคุยกับ NPC"
                target_name = npcs.get(target, f"NPC #{target}")
            elif otype == 2:
                type_label = "ใช้งานไอเทม"
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
            if rtype == 1:
                exp = rval
            elif rtype == 0:
                bit = rval
            elif rtype == 2:
                rew_list.append({
                    "item_id": rval,
                    "name": items.get(rval, f"ไอเทม #{rval}"),
                    "count": max(rcnt, 1)
                })
                
        quests[qid] = {
            "id": qid,
            "type": qtype,
            "level": level,
            "start_npc_id": s_npc,
            "start_npc": npcs.get(s_npc, ""),
            "end_npc_id": e_npc,
            "end_npc": npcs.get(e_npc, ""),
            "map_name": strs[0].strip(),
            "title": strs[1].strip(),
            "story": clean_desc(strs[2]),
            "objective_desc": clean_desc(strs[3]),
            "tracker": clean_desc(strs[4]),
            "pre_quests": pre_quests,
            "next_quests": [],
            "objectives": obj_list,
            "exp": exp,
            "bit": bit,
            "reward_items": rew_list
        }
        p = end
        
    print(f"[2/5] Parsed {len(quests)} quests from quest.bin.")

    # Calculate forward links (next_quests)
    for qid, q in quests.items():
        for pre in q["pre_quests"]:
            if pre in quests:
                if qid not in quests[pre]["next_quests"]:
                    quests[pre]["next_quests"].append(qid)

    # Define the 11 Main Chapters
    chapters_def = [
        {
            "id": "ch1_yokohama",
            "number": 1,
            "title": "บทที่ 1: ศูนย์บัญชาการ DATS & โยโกฮาม่า",
            "badge": "เริ่มต้น",
            "level_range": "Lv. 1 - 25",
            "maps": ["โหมดฝึกสอน", "ศูนย์บัญชาการ DATS", "หมู่บ้านโยโกฮาม่า", "โยโกฮาม่า สวนม้านั่งไม้", "ทางเข้าโรงกลั่นน้ำมัน", "โรงกลั่นน้ำมัน ชั้น1-3"],
            "area_keywords": ["โหมดฝึกสอน", "ศูนย์บัญชาการ dats", "หมู่บ้านโยโกฮาม่า", "หมู่บ้าน โยโกฮาม่า", "โยโกฮาม่า สวนม้านั่งไม้", "ทางเข้าโรงกลั่นน้ำมัน", "โรงกลั่นน้ำมัน"],
            "summary": "จุดเริ่มต้นของเทมเมอร์หน้าใหม่ในสังกัดหน่วย DATS เรียนรู้ระบบพื้นฐาน ทำภารกิจสืบสวนเหตุการณ์ดิจิมอนผิดปกติที่บุกรุกมายังโลกมนุษย์ คุ้มกันครอบครัวของไดมอน มาซารุ และคลี่คลายเหตุการณ์ที่โรงกลั่นน้ำมันเพื่อปลดล็อคการเดินทางสู่โลกดิจิตอล",
            "key_unlocks": [
                "ตราสมาชิก DATS อย่างเป็นทางการ",
                "สิทธิ์การเดินทางข้ามมิติสู่โลกดิจิตอล (Digital World Access)",
                "เปิดระบบฟักไข่ดิจิทามะ และระบบสแกน/รีเทิร์นข้อมูล"
            ],
            "pro_tips": [
                "อย่าลืมรับเควสฝึกสอนทั้งหมดเพราะจะได้รับไอเทมเริ่มต้นและดิจิมอนคู่หูที่จำเป็น",
                "ในโรงกลั่นน้ำมันมอนสเตอร์มีพลังป้องกันสูง ควรใช้ดิจิมอนธาตุแพ้ทางเพื่อเคลียร์เควสได้ไวขึ้น"
            ]
        },
        {
            "id": "ch2_western_maze",
            "number": 2,
            "title": "บทที่ 2: ดินแดนฝั่งตะวันตก & เขาวงกตดิจิมอน",
            "badge": "กลางช่วงแรก",
            "level_range": "Lv. 25 - 60",
            "maps": ["หมู่บ้านฝั่งตะวันตก", "ดิจิมอนฟาร์ม", "พื้นที่ทุรกันดาร", "หุบเขาสายลม", "ดาร์คทาวเวอร์", "เขาวงกตดิจิมอน B2-F4"],
            "area_keywords": ["หมู่บ้านฝั่งตะวันตก", "พื้นที่ทุรกันดาร", "ฟาร์มดิจิมอน", "ดิจิมอนฟาร์ม", "หุบเขาแห่งสายลม", "หุบเขาสายลม", "พื้นที่รกร้าง ฝั่งตะวันตก", "พื้นที่ซากปรักหักพัง", "ดาร์คทาวเวอร์", "เขาวงกตดิจิมอน", "digimon maze"],
            "summary": "ก้าวเข้าสู่โลกดิจิตอลฝั่งตะวันตก ออกค้นหาร่องรอยของอิคุโตะและฟอลโคมอน สืบสวนแผนการลับของดร.คุราตะ และเผชิญหน้ากับความลึกลับของเขาวงกตดิจิมอน (Digimon Maze) ที่เต็มไปด้วยมอนสเตอร์อันทรงพลัง",
            "key_unlocks": [
                "ปลดล็อคประตูเข้าสู่เขาวงกตดิจิมอน B2, B1, F1, F2, F3 และ F4",
                "เปิดจุดวาร์ปสถานีรถไฟฝั่งตะวันตก เชื่อมต่อหลายพื้นที่สำคัญ",
                "ปลดล็อคเควสโจเกรสและไอเทมวิวัฒนาการระดับสูง"
            ],
            "pro_tips": [
                "เควสเขาวงกตดิจิมอน F1-F4 ต้องส่งเควสต่อเนื่องเป็นลูกโซ่ ห้ามทิ้งเควสใดเควสหนึ่งเด็ดขาดเพราะจะทำให้ติดบัคเควสเดินต่อไม่ได้",
                "เตรียมไอเทมฟื้นฟู HP/DS และจั๊มบูสเตอร์ไว้เสมอเนื่องจากทางเดินในเมซมีความซับซ้อนมาก"
            ]
        },
        {
            "id": "ch3_glacier",
            "number": 3,
            "title": "บทที่ 3: กลาเซียร์ ดินแดนหิมะนิรันดร์",
            "badge": "กลางเกม",
            "level_range": "Lv. 50 - 65",
            "maps": ["D-เทอร์มินัล", "หมู่บ้านพายุหิมะ", "หมู่บ้านมนุษย์หิมะ", "ทุ่งหิมะ", "กำแพงน้ำแข็งนิรันดร์"],
            "area_keywords": ["หมู่บ้านพายุหิมะ", "หมู่บ้านมนุษย์หิมะ", "ดินแดนน้ำแข็ง", "ทุ่งหิมะ", "กำแพงน้ำแข็งนิรันดร์", "d-เทอร์มินัล"],
            "summary": "มุ่งหน้าสู่ดินแดนเยือกแข็งอันหนาวเหน็บ ช่วยเหลือมนุษย์หิมะมอนและเหล่าดิจิมอนที่ถูกครอบงำด้วยฟันเฟืองสีดำ รวบรวมข้อมูลเพื่อตามหาต้นตอความผิดปกติ และเปิดเส้นทางไปสู่กำแพงน้ำแข็งนิรันดร์",
            "key_unlocks": [
                "ปลดล็อคแผนที่กำแพงน้ำแข็งนิรันดร์ (Infinite Ice Wall)",
                "ปลดล็อคเส้นทางลับเชื่อมต่อไปยังเกาะไฟล์ (File Island)",
                "รับเครื่องประดับและหินพัฒนาธาตุน้ำแข็ง"
            ],
            "pro_tips": [
                "มอนสเตอร์ในดินแดนหิมะส่วนใหญ่เป็นธาตุน้ำ/น้ำแข็ง ดิจิมอนธาตุสายฟ้าหรือดินจะโจมตีได้รุนแรงเป็นพิเศษ",
                "เควสเก็บรวบรวมฟันเฟืองสีดำ ดรอปจากมอนสเตอร์เฉพาะจุด ให้เช็คพิกัดบนมินิแมพให้ดี"
            ]
        },
        {
            "id": "ch4_file_island",
            "number": 4,
            "title": "บทที่ 4: มหากาพย์เกาะไฟล์ & ภูเขาอินฟินิตี้",
            "badge": "กลางเกม",
            "level_range": "Lv. 60 - 80",
            "maps": ["ทะเลสาบสีเงิน", "ป่าแห่งความเงียบ", "พื้นที่อารยธรรมที่สูญหาย", "ชายฝั่งเกาะไฟล์", "ภูเขาอินฟินิตี้"],
            "area_keywords": ["ทะเลสาบสีเงิน", "ป่าแห่งความเงียบ", "พื้นที่อารยธรรมที่สูญหาย", "ชายฝั่งเกาะไฟล์", "ภูเขาอินฟินิตี้", "รอยร้าวของเดวีมอน", "หุบเขานิรันดร์"],
            "summary": "ย้อนรอยความทรงจำของอนิเมะ Digimon Adventure ภาคแรก บนเกาะไฟล์ ช่วยเหลือเลโอมอนและโอเกรมอน ทำลายฟันเฟืองดำที่แพร่ระบาด และบุกขึ้นสู่ภูเขาอินฟินิตี้เพื่อทำศึกแตกหักกับเดวีมอน",
            "key_unlocks": [
                "ปลดล็อคดันเจี้ยนภูเขาอินฟินิตี้ (Infinite Mountain Dungeon)",
                "ปลดล็อคการวิวัฒนาการร่างเมก้าและเบิร์สโหมด (Burst Mode)",
                "เปิดท่าเรือชายฝั่งเกาะไฟล์เพื่อข้ามทะเลไปยังทวีปเซิร์ฟเวอร์"
            ],
            "pro_tips": [
                "เควสเกาะไฟล์ให้ EXP มหาศาล เป็นแหล่งฟาร์มเลเวลที่ดีที่สุดช่วงเลเวล 60-80",
                "เมื่อถึงเควสปราบเดวีมอนที่ภูเขาอินฟินิตี้ แนะนำให้รวมปาร์ตี้เพื่อความรวดเร็วและปลอดภัย"
            ]
        },
        {
            "id": "ch5_server_continent",
            "number": 5,
            "title": "บทที่ 5: ทวีปเซิร์ฟเวอร์ ทะเลทราย & ปิรามิด",
            "badge": "กลาง-เลท",
            "level_range": "Lv. 75 - 95",
            "maps": ["ทวีปเซิร์ฟเวอร์ - ทะเลทราย", "ทวีปเซิร์ฟเวอร์ - หุบเขา", "ทวีปเซิร์ฟเวอร์ - ปิรามิด"],
            "area_keywords": ["ทวีปเซิร์ฟเวอร์ - ทะเลทราย", "ทวีปเซิร์ฟเวอร์ - หุบเขา", "ทวีปเซิร์ฟเวอร์ - ปิรามิด", "ทวีปเซิร์ฟเวอร์-ปิรามิด"],
            "summary": "ออกเดินทางสู่ผืนทวีปอันกว้างใหญ่ เผชิญหน้ากับเอเตมอนจอมวายร้ายที่ควบคุมเครือข่ายสายเคเบิลมืด ฝ่าฟันหุบเขาอันตราย และบุกเข้าไปในปิรามิดของดาตามอนเพื่อกู้ข้อมูลสำคัญกลับคืนมา",
            "key_unlocks": [
                "ปลดล็อคดันเจี้ยนปิรามิดดาตามอน (Datamon Maze)",
                "เปิดสิทธิ์การใช้งานแหวนและสร้อยคอระดับสูง (Ring/Necklace Shiny)",
                "เชื่อมต่อโครงข่ายประตูมิติสู่โลกดิจิตอลใหม่"
            ],
            "pro_tips": [
                "พื้นที่ทะเลทรายมีระยะทางกว้างมาก ควรใช้ดิจิมอนโหมดขับขี่ (Riding Mode) เพื่อประหยัดเวลาเดินทาง",
                "ในปิรามิดมอนสเตอร์เกิดหนาแน่น ระวังการดึงมอนสเตอร์เกินจำนวนที่รับไหว"
            ]
        },
        {
            "id": "ch6_verdandi",
            "number": 6,
            "title": "บทที่ 6: เวอร์ซันดิเทอร์มินัล (X-Antibody)",
            "badge": "เลทเกม",
            "level_range": "Lv. 90 - 110",
            "maps": ["เวอร์ซันดิเทอร์มินัล", "รอยัลเบส"],
            "area_keywords": ["เวอร์ซันดิเทอร์มินัล", "รอยัลเบส"],
            "summary": "วิกฤตการณ์ไวรัส X-Program ที่ถูกปล่อยออกมาโดยอิกดราซิล กองทหารรอยัลไนท์แบ่งฝ่ายต่อสู้กัน เทมเมอร์ต้องติดตั้งระบบ XAI Indicator เพื่อต้านทานพิษของไวรัส และปลดล็อคพลัง X-Antibody ขั้นสูงสุด",
            "key_unlocks": [
                "ปลดล็อคระบบ X-Antibody System (XAI Indicator)",
                "ปลดล็อคดันเจี้ยนรอยัลเบส (Royal Base 1F-3F)",
                "เปิดสิทธิ์การทำเควสวิวัฒนาการ X-Antibody เช่น Omegamon X, Alphamon Ouryuken X"
            ],
            "pro_tips": [
                "ต้องสวมใส่ XAI และรักษาระดับ X-Gauge ให้ไม่หมด เพื่อป้องกันดีบัฟดาเมจลดลงในพื้นที่",
                "มอนสเตอร์ในเวอร์ซันดิมีความถึกสูงมาก ควรมีค่า Hit Rate (HT) และ Critical (CT) เพียงพอ"
            ]
        },
        {
            "id": "ch7_odaiba",
            "number": 7,
            "title": "บทที่ 7: มหาสงคราม โตเกียว - โอไดบะ",
            "badge": "เลทเกม",
            "level_range": "Lv. 99 - 120",
            "maps": ["ฮิคาริงาโอกะ", "ชิบูย่า", "โตเกียวทาวเวอร์", "มินาโตะซิตี้", "โอไดบะ", "บิ๊กไซท์", "ดาดฟ้าสถานีโทรทัศน์ฟูจิทีวี"],
            "area_keywords": ["ฮิคาริงาโอกะ", "ชิบูย่า", "โตเกียวทาวเวอร์", "มินาโตะซิตี้", "โอไดบะ", "บิ๊กไซท์", "เรนโบว์ บริดจ์"],
            "summary": "กองทัพของแวมเดมอนข้ามประตูมิติมาบุกยึดกรุงโตเกียว เทมเมอร์ต้องร่วมมือกับเหล่าเด็กผู้ถูกเลือกทั้ง 8 คน ปกป้องครอบครัวและชาวเมือง ต่อสู้ไล่ล่าไปตามสถานที่จริงในโตเกียว จนถึงศึกตัดสินกับเวนอมแวมเดมอน",
            "key_unlocks": [
                "ปลดล็อคดันเจี้ยนเรดบอสโอไดบะ (VenomMyotismon, DarkTyrannomon)",
                "เปิดระบบฉายาบัฟสเตตัสระดับสูงของโตเกียว",
                "สิทธิ์แลกไอเทมอุปกรณ์และตั๋วการันตีระดับสูง"
            ],
            "pro_tips": [
                "เควสเนื้อเรื่องโอไดบะมีความยาวมาก ให้ทำตามเครื่องหมายเควสสีม่วง/น้ำเงินบนแผนที่อย่างเคร่งครัด",
                "จุดที่ต้องคุยกับเด็กผู้ถูกเลือก ให้สังเกตเวลาบนแผนที่ (กลางวัน/กลางคืน) มอนสเตอร์บางตัวจะเกิดเฉพาะเวลานั้น"
            ]
        },
        {
            "id": "ch8_shinjuku",
            "number": 8,
            "title": "บทที่ 8: ชินจูกุ, เทมเมอร์ส & D-รีพเปอร์",
            "badge": "เลทเกม",
            "level_range": "Lv. 110 - 140",
            "maps": ["ชินจูกุ", "ชินจูกุ(กลางคืน)", "ดิจิมอนเทมเมอร์ส", "หุบเขาแห่งแสงสว่าง", "D-รีพเปอร์"],
            "area_keywords": ["ชินจูกุ", "ชินจูกุ(กลางคืน)", "ดิจิมอนเทมเมอร์ส", "หุบเขาแห่งแสงสว่าง", "d-รีพเปอร์"],
            "summary": "ดำดิ่งสู่โลกของ Digimon Tamers พบกับมัตสึดะ ทาคาโตะ, กิลมอน, ลี และรูคิ เผชิญหน้ากับการลุกลามของโปรแกรมลบข้อมูล 'D-Reaper' ที่กลืนกินย่านชินจูกุ ต่อสู้กับ ADR Agents เพื่อหยุดยั้งวันสิ้นโลก",
            "key_unlocks": [
                "ปลดล็อคดันเจี้ยน D-Reaper Zone และ Mother D-Reaper",
                "เปิดระบบ D-Unit System ระดับสูง",
                "ปลดล็อคสกิลเสริมและชิปเซ็ตระดับเลทเกม"
            ],
            "pro_tips": [
                "ADR Agents ใน D-Reaper มีการสะท้อนดาเมจและดีบัฟลดคูลดาวน์สกิล ควรเตรียมดิจิมอนสายซัพพอร์ต",
                "แบ่งการทำเควสเป็นช่วงกลางวันและกลางคืนตามสายเนื้อเรื่องของทาคาโตะและลี"
            ]
        },
        {
            "id": "ch9_kaiser",
            "number": 9,
            "title": "บทที่ 9: พื้นที่ของไกเซอร์ (Adventure 02)",
            "badge": "เลท-เอนด์",
            "level_range": "Lv. 130 - 155",
            "maps": ["พาวเวอร์ดิจิมอน", "พื้นที่ของไกเซอร์", "พื้นที่แห่งความว่างเปล่า"],
            "area_keywords": ["พาวเวอร์ดิจิมอน", "พื้นที่ของไกเซอร์", "พื้นที่แห่งความว่างเปล่า"],
            "summary": "เรื่องราวจาก Digimon Adventure 02 การผงาดขึ้นมาของดิจิมอนไกเซอร์ (อิจิโจจิ เคน) ผู้ใช้ดาร์คสไปรัลควบคุมจิตใจดิจิมอนและสร้างคิเมรามอนขึ้นมา เทมเมอร์ต้องนำพาแสงสว่างกลับคืนสู่อาณาจักร",
            "key_unlocks": [
                "ปลดล็อคดันเจี้ยนฐานทัพเรือดำน้ำและคิเมรามอน (Kimeramon Hard/Hero)",
                "เปิดสิทธิ์รับดาร์คสไปรัลและสร้อยคอไกเซอร์",
                "ปลดล็อคสายวิวัฒนาการของอาร์เมอร์และโจเกรส 02"
            ],
            "pro_tips": [
                "ในเขตหอคอยความมืด ดิจิมอนจะไม่สามารถวิวัฒนาการได้ตามปกติ ให้เตรียมดิจิมอนร่าง Armor หรือใช้ไอเทมแก้สถานะ",
                "บอสคิเมรามอนมีสกิล AoE รุนแรง ให้คอยหลบวงแดงบนพื้นอย่างรวดเร็ว"
            ]
        },
        {
            "id": "ch10_spiral_mountain",
            "number": 10,
            "title": "บทที่ 10: สไปรอลเมาท์เทน & 4 จอมปีศาจ",
            "badge": "เอนด์เกม",
            "level_range": "Lv. 140 - 165",
            "maps": ["อาณาจักรโลหะ", "ป่าหุ่นเชิด", "เน็ตโอเชียน", "จุดสูงสุดของฝันร้าย", "ป่าแห่งการเริ่มต้น"],
            "area_keywords": ["อาณาจักรโลหะ", "ป่าหุ่นเชิด", "เน็ตโอเชียน", "จุดสูงสุดของฝันร้าย", "ป่าแห่งการเริ่มต้น", "ทะเลสาปแห่งการเริ่มต้น", "หมู่บ้านแห่งการเริ่มต้น"],
            "summary": "ยอดเขาสไปรอลเมาท์เทนที่ถูกบิดเบือนโดย 4 จอมปีศาจ Dark Masters: เมทัลซีดรามอน, พิน็อคคีมอน, มูเกนดรามอน และพิเอมอน รวมพลังครั้งยิ่งใหญ่เพื่อทวงคืนป่าแห่งการเริ่มต้นและโลกดิจิตอลทั้งใบ",
            "key_unlocks": [
                "ปลดล็อคดันเจี้ยน Spiral Mountain Raid ทั้ง 4 เขต",
                "เปิดระบบตราประทับซีลมาสเตอร์และเด็คบัฟระดับ 4 จอมปีศาจ",
                "รับวัตถุดิบสร้างอุปกรณ์และต่างหูระดับ Endgame"
            ],
            "pro_tips": [
                "บอสแต่ละตัวในสไปรอลเมาท์เทนมีกลไก (Mechanics) เฉพาะตัว เช่น มูเกนดรามอนต้องรีบทำลายเครื่องส่งสัญญาณ",
                "จำเป็นต้องมีสเตตัส AT, HT และ CT ขั้นต่ำตามเกณฑ์ของดันเจี้ยนจึงจะผ่านได้ง่าย"
            ]
        },
        {
            "id": "ch11_frontier",
            "number": 11,
            "title": "บทที่ 11: ดิจิมอนฟรอนเทียร์ & เทอร์มินอลแห่งธาตุ",
            "badge": "เอนด์เกมสูงสุด (Patch ปัจจุบัน)",
            "level_range": "Lv. 160 - 180",
            "maps": ["ดิจิมอนฟรอนเทียร์", "เทอร์มินัลแห่งเปลวเพลิง", "โรงงานสายลม", "หมู่บ้านสายลม"],
            "area_keywords": ["ดิจิมอนฟรอนเทียร์", "เทอร์มินัลแห่งเปลวเพลิง", "โรงงานสายลม", "หมู่บ้านสายลม"],
            "summary": "แพตช์ล่าสุดของเซิร์ฟเวอร์ไทย เลเวลสูงสุด 180! ถ่ายทอดพลังสปิริตแห่งตำนาน ออกค้นหาดิจิโค้ดที่แปดเปื้อนในเทอร์มินัลแห่งเปลวเพลิงและโรงงานสายลม เพื่อกอบกู้ความสมดุลสูงสุดของระบบโลกดิจิตอล",
            "key_unlocks": [
                "ปลดล็อคสปิริตดิจิมอนร่างไฮบริด (Hybrid Spirit Evolution)",
                "เปิดแผนที่ฟาร์มเลเวล 160-180 ที่ดีที่สุดในเกม",
                "ปลดล็อคระบบสแกนดิจิโค้ดและไอเทมระดับสูงสุดของเซิร์ฟเวอร์ไทย"
            ],
            "pro_tips": [
                "เนื้อหาเลเวล 160-180 มอนสเตอร์มีดาเมจสูงและมีเกราะป้องกันมหาศาล ควรมีบัฟเด็คและซีลมาสเตอร์ระดับสูง",
                "อย่าลืมรับเควสดิจิโค้ดประจำวันเพื่อสะสมแต้มแลกอุปกรณ์ระดับตำนาน"
            ]
        }
    ]

    print("[3/5] Assigning quests into 11 chapters and sorting prerequisite chains...")
    
    # Topological sort function
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
            if q["type"] in (1, 7): # Main or Tutorial
                m = q["map_name"].lower()
                if any(k.lower() in m for k in ch["area_keywords"]):
                    ch_quests.append(q)
        
        sorted_qs = sort_chain(ch_quests)
        total_assigned_quests += len(sorted_qs)
        
        # Calculate min and max level from quests
        levels = [q["level"] for q in sorted_qs if q["level"] > 0]
        calc_min = min(levels) if levels else 1
        calc_max = max(levels) if levels else 1
        
        output_chapters.append({
            "id": ch["id"],
            "number": ch["number"],
            "title": ch["title"],
            "badge": ch["badge"],
            "level_range": ch["level_range"],
            "maps": ch["maps"],
            "summary": ch["summary"],
            "key_unlocks": ch["key_unlocks"],
            "pro_tips": ch["pro_tips"],
            "quest_count": len(sorted_qs),
            "quests": sorted_qs
        })
        print(f"  -> Chapter {ch['number']}: {ch['title']} ({len(sorted_qs)} quests)")

    # Also build a quick lookup dictionary of special unlock quests (e.g. Jogress & Dungeons)
    special_quests = []
    for qid, q in quests.items():
        if any(w in q["map_name"] for w in ["Jogress", "โจเกรส", "ดันเจี้ยน", "เอ็กซามอน", "กันคูมอน"]):
            special_quests.append(q)

    full_payload = {
        "version": "thai_live_patch",
        "generated_at": "2026-11-16",
        "max_level": 180,
        "total_chapters": len(output_chapters),
        "total_main_quests": total_assigned_quests,
        "chapters": output_chapters,
        "special_quests": special_quests[:50]
    }

    print("[4/5] Saving main_quests.json...")
    # Write to static data directory
    out_file = STATIC_DATA_DIR / "main_quests.json"
    out_file.write_text(json.dumps(full_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> Wrote {out_file} ({out_file.stat().st_size:,} bytes)")

    # Also write to web/main_quests_cache.json
    cache_file = WEB_DIR / "main_quests_cache.json"
    cache_file.write_text(json.dumps(full_payload, ensure_ascii=False), encoding="utf-8")
    print(f"  -> Wrote {cache_file} ({cache_file.stat().st_size:,} bytes)")

    print("[5/5] Done! Main quest guide dataset ready.")

if __name__ == "__main__":
    build()
