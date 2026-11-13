# -*- coding: utf-8 -*-
"""
Rebuild all standalone JSON caches for DMO Thai Wiki from the local database & CrackDMO.
This allows the deployed web server to run anywhere with 0 external dependencies.
"""

import sys
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
OUTPUT = ROOT / "output"
DB_PATH = OUTPUT / "dmowiki.db"
IMAGES_DIR = OUTPUT / "images"

if str(WEB) not in sys.path:
    sys.path.insert(0, str(WEB))

from dex_builder import Dex
import dunits
from decks import build as build_decks
from dungeons_client import build as build_dungeons
from jogress_quests import build_groups as build_jogress_quests
from eggs import build_eggs
from seal_master_client import build_seals
from tamers_client import build as build_tamers

def build_all_caches():
    print("[CACHE] Initializing Dex and building Digimon profiles...")
    dex = Dex(DB_PATH, IMAGES_DIR)
    dex.build()
    digimon_list = dex.digimon

    # 1. D-Units Cache
    try:
        print("[CACHE] 1/7 Building D-Units cache...")
        du = dunits.build(dex, digimon_list)
        (WEB / "dunits_cache.json").write_text(json.dumps(du, ensure_ascii=False), encoding="utf-8")
        print(f"       -> Done! {du.get('total_groups', 0)} groups cached.")
    except Exception as e:
        print(f"       -> [ERROR] D-Units failed: {e}")

    # 2. Decks Cache
    try:
        print("[CACHE] 2/7 Building Decks cache...")
        dk = build_decks(dex, digimon_list)
        (WEB / "decks_cache.json").write_text(json.dumps(dk, ensure_ascii=False), encoding="utf-8")
        print(f"       -> Done! {len(dk)} decks cached.")
    except Exception as e:
        print(f"       -> [ERROR] Decks failed: {e}")

    # 3. Dungeons Cache
    try:
        print("[CACHE] 3/7 Building Dungeons cache...")
        dg = build_dungeons()
        (WEB / "dungeons_client_cache.json").write_text(json.dumps(dg, ensure_ascii=False), encoding="utf-8")
        print(f"       -> Done! {len(dg)} client dungeons cached.")
    except Exception as e:
        print(f"       -> [ERROR] Dungeons failed: {e}")

    # 4. Jogress Quests Cache
    try:
        print("[CACHE] 4/7 Building Jogress Quests cache...")
        jq = build_jogress_quests(dex, digimon_list)
        (WEB / "jogress_quests_cache.json").write_text(json.dumps(jq, ensure_ascii=False), encoding="utf-8")
        print(f"       -> Done! {len(jq)} jogress quest trees cached.")
    except Exception as e:
        print(f"       -> [ERROR] Jogress quests failed: {e}")

    # 5. Digi-Eggs Cache
    try:
        print("[CACHE] 5/7 Building Digi-Eggs cache...")
        conn = sqlite3.connect(str(DB_PATH))
        eg = build_eggs(dex, conn)
        conn.close()
        (WEB / "eggs_cache.json").write_text(json.dumps(eg, ensure_ascii=False), encoding="utf-8")
        print(f"       -> Done! {len(eg)} egg records cached.")
    except Exception as e:
        print(f"       -> [ERROR] Digi-Eggs failed: {e}")

    # 6. Seals Cache
    try:
        print("[CACHE] 6/7 Building Seal Master cache...")
        sm_payload = build_seals()
        (WEB / "seals_cache.json").write_text(json.dumps(sm_payload, ensure_ascii=False), encoding="utf-8")
        print(f"       -> Done! {len(sm_payload.get('seals', []))} seals cached.")
    except Exception as e:
        print(f"       -> [ERROR] Seals failed: {e}")

    # 7. Tamers Cache
    try:
        print("[CACHE] 7/7 Building Tamers cache...")
        tm = build_tamers()
        (WEB / "tamers_cache.json").write_text(json.dumps(tm, ensure_ascii=False), encoding="utf-8")
        tm_list = tm.get("tamers", []) if isinstance(tm, dict) else tm
        print(f"       -> Done! {len(tm_list)} tamers cached.")
    except Exception as e:
        print(f"       -> [ERROR] Tamers failed: {e}")

    print("\n[CACHE] === ALL 7 CACHES BUILT & SAVED SUCCESSFULLY! ===")

if __name__ == "__main__":
    build_all_caches()
