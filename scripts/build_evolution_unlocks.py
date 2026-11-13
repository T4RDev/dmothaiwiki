r"""
Build authentic evolution unlock items and icons for Digimon Thai Wiki.
Uses cracked client data from C:\Users\T4R\Desktop\AllWorks\CrackDMO:
  - out_json/index/item_catalog.json (Thai names & descriptions)
  - out_decrypted/data/bin/table/itemdata.bin (IconId per item)
  - out_images/data/interface/icon/icon*.png (Atlas texture sheets)
  - out_item_icons/*.png (Pre-sliced icons)

Outputs:
  - web/evolution_unlocks.json (authoritative mapping for all Digimon)
  - output/images/items/{item_id}.png (authentic sliced 32x32 RGBA in-game icons)
"""
import os, sys, json, struct, re, shutil
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

CRACK_DIR = Path(r"C:\Users\T4R\Desktop\AllWorks\CrackDMO")
OUTPUT_ITEMS_DIR = BASE_DIR / "output" / "images" / "items"
OUTPUT_ITEMS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load item icon mapping from itemdata.bin
print("[1/5] Loading itemdata.bin for icon mapping...")
itemdata_buf = (CRACK_DIR / "out_decrypted" / "data" / "bin" / "table" / "itemdata.bin").read_bytes()
item_icon_map = {}
o = 0
while o + 12 <= len(itemdata_buf):
    f0, f1, f2 = struct.unpack_from('<III', itemdata_buf, o)
    if f0 > 0 and f0 == f1 and 1000 <= f2 <= 49999:
        item_icon_map.setdefault(f0, f2)
    o += 1
print(f"Mapped {len(item_icon_map)} items to in-game icon coordinates.")

# 2. Atlas slicer
icon_dir = CRACK_DIR / "out_images" / "data" / "interface" / "icon"
out_item_icons_dir = CRACK_DIR / "out_item_icons"
atl_cache = {}

def get_and_save_item_icon(item_id):
    dest = OUTPUT_ITEMS_DIR / f"{item_id}.png"
    if dest.exists() and dest.stat().st_size > 0:
        return f"/images/items/{item_id}.png"

    # Check pre-sliced in CrackDMO
    src_pre = out_item_icons_dir / f"{item_id}.png"
    if src_pre.exists():
        shutil.copy2(src_pre, dest)
        return f"/images/items/{item_id}.png"

    ic_id = item_icon_map.get(item_id)
    if not ic_id:
        return None

    atl_num = ic_id // 1000
    if atl_num not in atl_cache:
        fn = icon_dir / f"icon{atl_num:02d}.png"
        if fn.exists():
            atl_cache[atl_num] = Image.open(fn).convert('RGBA')
        else:
            atl_cache[atl_num] = None

    atl = atl_cache[atl_num]
    if atl is None:
        return None

    cell = ic_id % 1000
    cols = atl.width // 32
    r, c = divmod(cell, cols)
    crop = atl.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32))
    crop.save(dest)
    return f"/images/items/{item_id}.png"

# Save default Evoluter icon (item 9004)
evoluter_icon = get_and_save_item_icon(9004)
# Also copy to output/images/Evoluter.png for compatibility
shutil.copy2(OUTPUT_ITEMS_DIR / "9004.png", BASE_DIR / "output" / "images" / "Evoluter.png")

# 3. Load item catalog
print("[2/5] Loading item_catalog.json...")
catalog = json.loads((CRACK_DIR / "out_json" / "index" / "item_catalog.json").read_text(encoding="utf-8"))
items_by_id = {it["id"]: it for it in catalog}

# Build catalog search maps
items_by_name_clean = {}
for it in catalog:
    nm = it.get("name", "").strip()
    if nm and "[กิจกรรม]" not in nm and "[จัมปิ้ง]" not in nm:
        items_by_name_clean[nm.lower()] = it
        # without space
        items_by_name_clean[re.sub(r"\s+", "", nm).lower()] = it

# 4. Load wiki Digimon
print("[3/5] Loading wiki Digimon database...")
from web.dex_builder import Dex
dex = Dex(BASE_DIR / "output" / "dmowiki.db", BASE_DIR / "output" / "images")
dex.build()
wiki_digimon = [dex.public(d) for d in dex.digimon]
print(f"Loaded {len(wiki_digimon)} Digimon from dex_builder.")

# 5. Build official evolution mappings
print("[4/5] Matching evolution unlock items...")

# Official direct mappings for Patch 74 Rework & Special Digimon
# (Item ID -> Digimon Slug / Keys)
DIRECT_OVERRIDES = {
    # Mega Reworks
    "Sakuyamon": [41839],              # วิล ออฟ ก็อด
    "WarGreymon": [41823],             # เบรฟ ชีลด์
    "MetalGarurumon": [41821],         # เลเซอร์ ไซท์
    "Gallantmon": [41883],             # เอจิส
    "MegaGargomon": [41841],           # ไจแอนท์ มิสไซล์
    "Dynasmon": [41845],               # ชิฟวัลรี
    "Crusadermon": [41843],            # ไพล์ บังเกอร์
    "Beelzemon": [41847],              # โนเบิล บีอิง
    "Piedmon": [41749],                # ทรัมป์ ซอร์ด
    "Phoenixmon": [41769],             # ไลฟ์ ฟอร์ส
    "SaberLeomon": [41761],            # คิง แฟง
    "MetalEtemon": [41745],            # คิง ออฟ ดิจิมอน
    "Puppetmon": [41779],              # วูด ครอส
    "GranKuwagamon": [41783],          # อัลติเมท อินเซค
    "Sleipmon": [41849],               # เรด ดิจิซอยด์
    "DarkDramon": [41753],             # ดี - บริเกด
    "Zanbamon": [41759],               # โกลด์เด้น อาร์เมอร์
    "DoruGoramon": [41831],            # อวทาร์ ออฟ ดิซทรัคชั่น
    "Gulfmon": [41833],                # อะบิสซัล ดิจิมอน
    "BlitzGreymon": [41835],           # พลาสม่า สเต็ก
    "CresGarurumon": [41837],          # ฮวังชวล เซเบอร์
    "BlackWarGreymon": [41791],        # ดาร์ค ดรากอน วอรีเยอร์
    "BlackMetalGarurumon": [41789],    # เมทัล เฮาล์ลิง
    "Boltmon": [41737],                # โทมาฮอค
    "Gryphonmon": [41739],             # ซูเปอร์โซนิค
    "MarineAngemon": [41723],          # โอเชี่ยน เลิฟ
    "KingChessmon": [41717],           # เอสเคป บัท วิน!
    "QueenChessmon": [41707],          # โอ้ ก็อด ออฟ เชส, ฟอร์กิฟว์ มี!
    "MetalSeadramon": [41719],         # คิง ออฟ เดอะ ซี
    "HiAndromon": [41713],             # ไบโอ ไซแนปส์
    "GrandisKuwagamon": [41715],       # ดีมอน ออฟ เดอะ ดีพ ฟอร์เรสท์
    "JumboGamemon": [41777],           # ออฟเฟนส์ อีส เดอะ เบสท์ ดีเฟนส์
    "Machinedramon": [41781],          # อินฟินิตี้ แคนนอน
    "Parasimon": [41829],              # พาราไซต์
    "Murmukusmon": [41825],            # เคาท์ ดิจิมอน
    "Vikemon": [41751],                # มิยอลล์นีร์
    "HerculesKabuterimon": [41765],    # ฮอร์น บัสเตอร์
    "SkullMammothmon": [41767],        # สปิริต บอล
    "Gankoomon": [41514],              # ไอรอน ฟิสท์
    "Jesmon": [41519],                 # อาโต้,เรเน่,พอล
    "Plesiomon": [41609],              # เอสเซ้นส์ ออฟ มารีน ดรากอน
    "ChaosGallantmon": [41871],        # กอร์กอน

    # Burst Modes / BM Items
    "Beelzemon_(Blast_Mode)": [41003],        # ปืนของเล่น
    "Gallantmon_(Crimson_Mode)": [41008],    # กุงเนียร์
    "Ophanimon": [41004],                    # โฮลี่สเปียร์
    "VictoryGreymon": [41005],               # ดรามอนเบรคเกอร์
    "Z'dGarurumon": [41006],                 # Z'd-hou (ซีดโฮ)
    "KingEtemon": [41007],                   # ชุดเกราะราชาดิจิมอน
    "BanchouLeomon": [41009],                # กักคุรัน
    "Cherubimon": [41010],                   # แองเจิลริง
    "Cherubimon_(White)": [41010],           # แองเจิลริง
    "Kuzuhamon": [41011],                    # คฑานักพรต
    "SlashAngemon": [41012],                 # โคลมฮ์ โซลาอิส
    "TyrantKabuterimon": [41014],            # ไทแรน โครว์
    "AncientTroiamon": [41015],              # ม้าโทรจัน
    "Valdurmon": [41016],                    # โฮลี่วิง
    "GigaSeadramon": [41017],                # กีก้า สเกล
    "Ornismon": [41018],                     # โอนิสวิง
    "ShadowSeraphimon": [41019],             # ชาโดว์ วิง
    "BlackSeraphimon": [41020],              # แบล็คเซนต์วิง
    "Chaosdramon": [41021],                  # ไฮเปอร์แคนนอน
    "ChaosPiedmon": [41022],                 # ทรัมพ์ซอร์ด
    "GranDracmon": [41023],                  # แบล็คเทนตาเคิล
    "Imperialdramon_(Paladin_Mode)": [41024],# โอเมกาเบลด
    "Demon_(Beast_Mode)": [41030],           # ฟิวเรียส คลอว์
    "MaloMyotismon": [41031],                # โซดอมและกอมโมร่า
    "Lucemon_(Satan_Mode)": [41032],         # เกเฮนน่า
    "Dexmon": [41033],                       # เดธ X แอนติบอดี้

    # Special / Jogress / Awaken
    "Abbadomon": [190062, 9004],             # คอร์รัปเต็ด ดาต้า + อีโวลูเตอร์ x 6
    "Abbadomon_Core": ["Source_of_Destruction"],
    "Susanoomon_(Awaken)": [41578, 41579],   # โอเวอร์เซียร์ ออฟ ดิซทรัคชั่น + โอเวอร์เซียร์ ออฟ รีเจเนอเรชัน
    "Susanoomon_(Extreme)": [190048, 190050],# ก็อด : ออร่า ออฟ เดสทรัคชัน + ก็อด : ออร่า ออฟ รีเบิร์ธ
    "Omegamon_Alter-S": [41500, 41501],      # ข้อมูลโจเกรส A/B
    "Omegamon_Zwart_D": [41502, 41503],      # D . แอนติ ไวรัส A/B
    "Omegamon_Alter-B": [41504, 41505],      # แบล็คดิจิตรอน- Sample A/B
    "ZeedMillenniummon": [41510, 41511],     # Cross Data-ช่องว่าง / เวลา
    "Millenniummon": [41506, 41507],         # มินเลนเนียมมอน : Data Code
    "MoonMillenniummon": [41508, 41509],     # มูนมิลเลนเนียมมอน : Data Code
    "Mastemon": [41516, 41517],              # โฮลี่ อามูเล็ต + ดาร์ค อามูเล็ต
    "Sakuyamon_(Awaken)": [41651],           # แม็ททริกส์ อีโวลูชั่น - ซาคุยามอน
    "Gallantmon_(Awaken)": [41643],          # แม็ททริกส์ อีโวลูชั่น - ดุ๊คมอน
    "MegaGargomon_(Awaken)": [41647],        # แม็ททริกส์ อีโวลูชั่น - เซนต์การ์โกมอน
    "Lucemon:_Satan_Mode_(Extreme)": [41639],# ดาต้าแห่งความชั่วร้าย ดิจิทามะ
    "Beelzemon_(Blast_Mode)_(Awaken)": [41703], # เดธ สลิงเกอร์
    "Belphemon_(Rage_Mode)_(Awaken)": [41700],  # โบรคเค่น อะลาร์ม
    "Agumon_-_Bonds_of_Courage": [41655],    # ลาสต์ อีโวลูชัน : ความกล้าหาญ
    "Gabumon_-_Bonds_of_Friendship": [41659],# ลาสต์ อีโวลูชัน : มิตรภาพ
    "Shoutmon_X7": [41612, 41613],           # เกรทครอส - อัลฟ่า + เบต้า
    "Shoutmon_DX": [41601, 41602],           # ดับเบิ้ลครอส - DX - อัลฟา + เบต้า
    "ZekeGreymon": [41597, 41598],           # วิวัฒนาการในตำนาน - Z อัลฟา + เบต้า
    "OmegaShoutmon": [41591],                # วิวัฒนาการในตำนาน - Ω
    "DarknessBagramon": [41677, 41679],      # อิมพีเรียม วิชเชส(B) + (D)
    "Bagramon": [41683],                     # อุดมการณ์และความเชื่อของบากรามอน
    "Fanglongmon_(Awaken)": [41553],         # ปลุกพลังด้านลบ : จินลอนมอน
}

# Pre-slice and build lookup
results = {}
stat_special = 0
stat_evoluter = 0
stat_none = 0

for d in wiki_digimon:
    slug = d["slug"]
    title = d.get("title", slug)
    form = d.get("form", "").lower()
    thai_name = d.get("thai_name") or ""
    
    # Check if Rookie / In-training
    if "in-training" in form or form == "rookie":
        results[slug] = []
        stat_none += 1
        continue

    # 1. Direct Override
    override_ids = DIRECT_OVERRIDES.get(slug) or DIRECT_OVERRIDES.get(title)
    if override_ids:
        items_list = []
        for iid in override_ids:
            if iid == "Source_of_Destruction":
                items_list.append({"name": "Source of Destruction", "th": "ซอร์ส ออฟ ดีสตรัคชั่น", "icon": "/images/Source_of_Destruction.png"})
                continue
            it = items_by_id.get(iid)
            if it:
                ic_url = get_and_save_item_icon(iid)
                nm = it["name"]
                # Clean event tag if any
                nm = re.sub(r"\[.+?\]", "", nm).strip()
                # If evoluter
                if "อีโวลูเตอร์" in nm:
                    cnt = "6" if "abbadomon" in slug.lower() else "8"
                    items_list.append({"name": f"Evoluter × {cnt}", "th": f"อีโวลูเตอร์ × {cnt}", "icon": ic_url or "/images/items/9004.png"})
                else:
                    items_list.append({"name": nm, "th": nm, "icon": ic_url or ""})
            elif iid == 47557: # Source of Destruction
                items_list.append({"name": "Source of Destruction", "th": "ซอร์ส ออฟ ดีสตรัคชั่น", "icon": "/images/Source_of_Destruction.png"})
        results[slug] = items_list
        stat_special += 1
        continue

    # 2. Existing dmowiki unlock items matching
    existing = d.get("unlock_items") or []
    if existing:
        matched_items = []
        has_special = False
        for ex in existing:
            ex_name = ex.get("name", "")
            if not ex_name or ex_name.lower() == "already unlocked":
                continue
            # Check if Evoluter
            if "evoluter" in ex_name.lower():
                m_cnt = re.search(r"(\d+)", ex_name)
                cnt = m_cnt.group(1) if m_cnt else ("3" if "champion" in form else ("6" if "ultimate" in form else "8"))
                matched_items.append({
                    "name": f"Evoluter × {cnt}",
                    "th": f"อีโวลูเตอร์ × {cnt}",
                    "icon": "/images/items/9004.png"
                })
            else:
                # Try finding Thai item by name match
                c_clean = re.sub(r"[^a-zA-Z0-9\u0e00-\u0e7f]", "", ex_name).lower()
                matched_cat = items_by_name_clean.get(ex_name.lower()) or items_by_name_clean.get(c_clean)
                if not matched_cat:
                    # search catalog
                    for it in catalog:
                        if c_clean and len(c_clean) >= 4 and c_clean in re.sub(r"[^a-zA-Z0-9\u0e00-\u0e7f]", "", it.get("name", "")).lower():
                            matched_cat = it
                            break
                if matched_cat:
                    has_special = True
                    ic_url = get_and_save_item_icon(matched_cat["id"])
                    nm = re.sub(r"\[.+?\]", "", matched_cat["name"]).strip()
                    matched_items.append({
                        "name": ex_name,
                        "th": nm,
                        "icon": ic_url or (ex.get("icon") if ex.get("icon") and Path("output" + ex.get("icon")).exists() else "/images/items/9004.png")
                    })
                else:
                    # Fallback keep existing with clean Evoluter or existing icon
                    has_special = True
                    ic_path = ex.get("icon") or ""
                    if not ic_path or not (BASE_DIR / "output" / ic_path.lstrip("/")).exists():
                        ic_path = "/images/items/9004.png"
                    matched_items.append({
                        "name": ex_name,
                        "th": ex.get("th") or ex_name,
                        "icon": ic_path
                    })
        if matched_items:
            results[slug] = matched_items
            if has_special:
                stat_special += 1
            else:
                stat_evoluter += 1
            continue

    # 3. Default Evoluter for Champion / Ultimate / Mega
    if "champion" in form or "armor" in form:
        results[slug] = [{"name": "Evoluter × 3", "th": "อีโวลูเตอร์ × 3", "icon": "/images/items/9004.png"}]
        stat_evoluter += 1
    elif "ultimate" in form:
        results[slug] = [{"name": "Evoluter × 6", "th": "อีโวลูเตอร์ × 6", "icon": "/images/items/9004.png"}]
        stat_evoluter += 1
    elif "mega" in form:
        results[slug] = [{"name": "Evoluter × 8", "th": "อีโวลูเตอร์ × 8", "icon": "/images/items/9004.png"}]
        stat_evoluter += 1
    else:
        results[slug] = []
        stat_none += 1

# 5. Save output
out_file = BASE_DIR / "web" / "evolution_unlocks.json"
out_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[5/5] Successfully built web/evolution_unlocks.json!")
print(f"Stats:")
print(f"  - Digimon with Special In-Game Items: {stat_special}")
print(f"  - Digimon with Standard Evoluter:     {stat_evoluter}")
print(f"  - Digimon with No Unlock (Rookie):    {stat_none}")
print(f"  - Total Digimon Processed:             {len(results)}")
print(f"  - Total In-Game Icons Saved in output/images/items/: {len(list(OUTPUT_ITEMS_DIR.glob('*.png')))}")
