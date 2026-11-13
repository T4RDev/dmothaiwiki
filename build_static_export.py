import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"
DATA_DIR = STATIC_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

print("[EXPORT] Starting static data extraction from cache files...")

# 1. Load digimon_cache.json
d_cache_file = WEB_DIR / "digimon_cache.json"
if not d_cache_file.exists():
    print("[ERROR] digimon_cache.json not found!")
    sys.exit(1)

d_cached = json.loads(d_cache_file.read_text(encoding="utf-8"))
digimon_list = d_cached.get("digimon", [])
not_in_thai = d_cached.get("not_in_thai", [])
rank_table_th = d_cached.get("rank_table_th", {})

print(f"[EXPORT] Digimon count: {len(digimon_list)}")

# Write digimon.json
(DATA_DIR / "digimon.json").write_text(json.dumps(digimon_list, ensure_ascii=False), encoding="utf-8")
print("  -> Wrote data/digimon.json")

# Write rank_table.json
(DATA_DIR / "rank_table.json").write_text(json.dumps(rank_table_th, ensure_ascii=False), encoding="utf-8")
print("  -> Wrote data/rank_table.json")

# 2. Build filters.json
RANK_ORDER = ["U", "SSS+", "SSS", "SS+", "SS", "S+", "S", "A+", "A", "N"]
attrs, elems = {}, {}
for d in digimon_list:
    if d.get("attribute"):
        attrs.setdefault(d["attribute"], {"name": d["attribute"], "th": d.get("attribute_th"), "icon": d.get("attribute_icon"), "count": 0})["count"] += 1
    if d.get("element"):
        elems.setdefault(d["element"], {"name": d["element"], "th": d.get("element_th"), "icon": d.get("element_icon"), "count": 0})["count"] += 1

ranks = []
for r in RANK_ORDER:
    n = sum(1 for d in digimon_list if d.get("rank") == r)
    if n:
        icon = next((d.get("rank_icon") for d in digimon_list if d.get("rank") == r and d.get("rank_icon")), "")
        ranks.append({"name": r, "icon": icon, "count": n})

filters_data = {
    "ranks": ranks,
    "no_rank": sum(1 for d in digimon_list if not d.get("rank")),
    "attributes": sorted(attrs.values(), key=lambda x: -x["count"]),
    "elements": sorted(elems.values(), key=lambda x: -x["count"]),
}
(DATA_DIR / "filters.json").write_text(json.dumps(filters_data, ensure_ascii=False), encoding="utf-8")
print("  -> Wrote data/filters.json")

# 3. Simple copy / export for other cache files
caches = [
    ("decks_cache.json", "decks.json"),
    ("dungeons_client_cache.json", "dungeons.json"),
    ("jogress_quests_cache.json", "jogress.json"),
    ("eggs_cache.json", "eggs.json"),
    ("dunits_cache.json", "dunits.json"),
    ("npc_exchanges_cache.json", "npc_exchanges.json"),
    ("seals_cache.json", "seals.json"),
    ("tamers_cache.json", "tamers.json"),
]

for src_name, dst_name in caches:
    src_file = WEB_DIR / src_name
    if src_file.exists():
        content = src_file.read_text(encoding="utf-8")
        # Ensure it's valid JSON
        parsed = json.loads(content)
        (DATA_DIR / dst_name).write_text(json.dumps(parsed, ensure_ascii=False), encoding="utf-8")
        print(f"  -> Wrote data/{dst_name}")
    else:
        print(f"  [WARN] {src_name} not found, writing empty list")
        (DATA_DIR / dst_name).write_text("[]", encoding="utf-8")

# 4. Patches
patch_arch_idx = BASE_DIR / "output" / "thai_patch_archive" / "index.json"
if patch_arch_idx.exists():
    try:
        raw_idx = json.loads(patch_arch_idx.read_text(encoding="utf-8"))
        p_items = []
        for p in raw_idx:
            item = {k: v for k, v in p.items() if k != "search"}
            item["id"] = str(item["id"])
            p_items.append(item)
        (DATA_DIR / "patches.json").write_text(json.dumps(p_items, ensure_ascii=False), encoding="utf-8")
        print(f"  -> Wrote data/patches.json ({len(p_items)} articles with valid IDs)")
    except Exception as e:
        print(f"  [WARN] Failed to load patch archive index: {e}")
        (DATA_DIR / "patches.json").write_text("[]", encoding="utf-8")
else:
    patch_json_file = WEB_DIR / "thai_patch_data.json"
    if patch_json_file.exists():
        try:
            p_raw = json.loads(patch_json_file.read_text(encoding="utf-8"))
            p_items = p_raw if isinstance(p_raw, list) else p_raw.get("items", [])
            (DATA_DIR / "patches.json").write_text(json.dumps(p_items, ensure_ascii=False), encoding="utf-8")
            print(f"  -> Wrote data/patches.json ({len(p_items)} articles)")
        except Exception as e:
            print(f"  [WARN] Failed to load thai_patch_data.json: {e}")
            (DATA_DIR / "patches.json").write_text("[]", encoding="utf-8")

# 5. Stats
stats_data = {
    "digimon": len(digimon_list),
    "seals": 0,
    "dungeons": 0,
    "crafts": 0,
    "tamers": 0
}
seals_file = DATA_DIR / "seals.json"
if seals_file.exists():
    try:
        s_data = json.loads(seals_file.read_text(encoding="utf-8"))
        if isinstance(s_data, dict):
            stats_data["seals"] = len(s_data.get("seals", []))
        elif isinstance(s_data, list):
            stats_data["seals"] = len(s_data)
    except:
        pass

dungeons_file = DATA_DIR / "dungeons.json"
if dungeons_file.exists():
    try:
        d_data = json.loads(dungeons_file.read_text(encoding="utf-8"))
        stats_data["dungeons"] = len(d_data) if isinstance(d_data, list) else len(d_data.get("dungeons", []))
    except:
        pass

tamers_file = DATA_DIR / "tamers.json"
if tamers_file.exists():
    try:
        t_data = json.loads(tamers_file.read_text(encoding="utf-8"))
        stats_data["tamers"] = len(t_data) if isinstance(t_data, list) else len(t_data.get("tamers", []))
    except:
        pass

(DATA_DIR / "stats.json").write_text(json.dumps(stats_data, ensure_ascii=False), encoding="utf-8")
print(f"  -> Wrote data/stats.json {stats_data}")

print("\n[SUCCESS] Static data extraction completed successfully!")
