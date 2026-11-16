import os
import shutil
from pathlib import Path
import json

CRACK = Path("G:/DMOWiki/CrackDMO")
OUT_MAPS = Path("G:/DMOWiki/Web_Scraper/output/images/maps")
OUT_NPCS = Path("G:/DMOWiki/Web_Scraper/output/images/npc")

OUT_MAPS.mkdir(parents=True, exist_ok=True)
OUT_NPCS.mkdir(parents=True, exist_ok=True)

# 1. Copy Map images
# Priority 1: out_images/data/interface/map/__map_thai/*.png
# Priority 2: out_images/data/interface/map/*.png
thai_map_dir = CRACK / "out_images/data/interface/map/__map_thai"
std_map_dir = CRACK / "out_images/data/interface/map"

copied_maps = 0
for f in std_map_dir.glob("*.png"):
    dst = OUT_MAPS / f.name.lower()
    if not dst.exists() or dst.stat().st_size != f.stat().st_size:
        shutil.copy2(f, dst)
        copied_maps += 1

if thai_map_dir.exists():
    for f in thai_map_dir.glob("*.png"):
        dst = OUT_MAPS / f.name.lower()
        shutil.copy2(f, dst)
        copied_maps += 1

print(f"Copied/verified {copied_maps} map images to output/images/maps")

# 2. Copy NPC images from out_images/data/npc/**/*.png
npc_dir = CRACK / "out_images/data/npc"
copied_npcs = 0
npc_id_map = {}

if npc_dir.exists():
    for f in npc_dir.rglob("*.png"):
        # name like 0090001_carryl.png
        dst = OUT_NPCS / f.name.lower()
        if not dst.exists() or dst.stat().st_size != f.stat().st_size:
            shutil.copy2(f, dst)
            copied_npcs += 1
            
        import re
        m = re.match(r"^0*(\d+)", f.stem)
        if m:
            nid = int(m.group(1))
            # prefer 's' (small portrait) or 'l'
            if nid not in npc_id_map or "s" in f.stem:
                npc_id_map[nid] = f.name.lower()

print(f"Copied/verified {copied_npcs} NPC images to output/images/npc (mapped {len(npc_id_map)} NPC IDs)")

# Save npc_id_map for fast lookup
(Path("G:/DMOWiki/Web_Scraper/web") / "npc_img_map.json").write_text(json.dumps(npc_id_map, ensure_ascii=False), encoding="utf-8")
