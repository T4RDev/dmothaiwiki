import os
import sys
import json
import sqlite3
import re
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dex_builder import Dex, RANK_ORDER
from effects import parse_effects, GROUPS as EFFECT_GROUPS
from aoe import parse_aoe, load_table as load_aoe_table
from eggs import build_eggs
from decks import build as build_decks
from jogress_quests import build_groups as build_jogress_quests
from tamers_client import build as build_tamers
try:
    from tamer_models import build_all as build_tamer_models
except Exception as _tme:
    def build_tamer_models():
        return {}
from seal_master_client import build_seals
import thai_patch as thai_patch_syncer
from thai_patch_apply import ThaiPatch
from thai_client_apply import ClientEvo

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
DB_PATH = OUTPUT_DIR / "dmowiki.db"
IMAGES_DIR = OUTPUT_DIR / "images"
MODELS_DIR = OUTPUT_DIR / "models"
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Digimon Masters Online - Thai Wiki API", version="2.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# In-memory cached data
CACHE = {
    "digimon": [],
    "digimon_by_slug": {},
    "digimon_by_norm": {},
    "seals": [],
    "seals_by_slug": {},
    "seal_master": {},
    "dungeons": [],
    "crafts": [],
    "tamers": [],
    "tamer_skill_system": {},
    "stats": {},
    "image_lookup": {},
    "image_norm_lookup": {}
}

# Image Indexing for ultra-fast lookup
def build_image_index():
    print("[INIT] Indexing image directory for 100% asset coverage...")
    if not IMAGES_DIR.exists():
        return
    lookup = {}
    norm_lookup = {}
    for f in os.listdir(IMAGES_DIR):
        lookup[f.lower()] = f
        norm_key = re.sub(r'[^a-z0-9]', '', f.lower())
        norm_lookup[norm_key] = f
    CACHE["image_lookup"] = lookup
    CACHE["image_norm_lookup"] = norm_lookup
    print(f"[INIT] Indexed {len(lookup)} unique image files.")

def resolve_image(name: str, slug: str = "") -> str:
    if not name:
        return ""
    lookup = CACHE.get("image_lookup", {})
    norm_lookup = CACHE.get("image_norm_lookup", {})
    
    clean = re.sub(r'[^\w\s-]', '', name).strip().lower().replace(" ", "_")
    slug_clean = (slug or "").strip().lower().replace(" ", "_")

    candidates = [
        f"{clean}_icon.png",
        f"{clean}.png",
        f"{clean}_icon.jpg",
        f"{clean}.jpg",
        f"120px-{clean}_icon.png",
        f"120px-{clean}.png",
        f"115px-{clean}.png",
        f"110px-{clean}.png",
        f"{slug_clean}_icon.png",
        f"{slug_clean}.png"
    ]
    for c in candidates:
        if c and c in lookup:
            return f"/images/{lookup[c]}"

    # Normalized key exact matches
    norm_targets = [
        name + " icon",
        name,
        slug + " icon",
        slug,
        re.sub(r'\(.*?\)', '', name).strip() + " icon",
        re.sub(r'\(.*?\)', '', name).strip()
    ]
    for nt in norm_targets:
        k = re.sub(r'[^a-z0-9]', '', nt.lower())
        if k in norm_lookup:
            return f"/images/{norm_lookup[k]}"

    # Substring search with icon preference
    clean_target = re.sub(r'[^a-z0-9]', '', name.lower())
    for k, real_f in norm_lookup.items():
        if clean_target in k and "icon" in k:
            return f"/images/{real_f}"

    for cand_suffix in [f"_{clean}_icon.png", f"-{clean}_icon.png", f"-{clean}.png", f"_{clean}.png"]:
        for k, real_f in lookup.items():
            if k.endswith(cand_suffix):
                return f"/images/{real_f}"

    for k, real_f in norm_lookup.items():
        if clean_target in k:
            return f"/images/{real_f}"

    return ""

def parse_stat_name(name: str) -> Optional[str]:
    n = name.lower().strip()
    if "health" in n or n == "hp": return "HP"
    if "soul" in n or n == "ds": return "DS"
    if "speed" in n or n == "as": return "AS"
    if "critical" in n or n == "ct": return "CT"
    if "hit rate" in n or n == "ht": return "HT"
    if "evade" in n or "evasion" in n or n == "ev": return "EV"
    if "defense" in n or n == "de": return "DE"
    if n == "attack" or n.startswith("attack") or n == "at": return "AT"
    return None

def clean_stat_val(val_str: str) -> str:
    if not val_str:
        return "-"
    return val_str.replace(" ", "").replace(",", "").strip()

def extract_combat(data: dict) -> dict:
    """Stats (max/base), skills with Lv.1-25 damage, rank passives and lore from a page."""
    tables = data.get("tables", [])
    text = data.get("text", "")

    stats = {k: {"max": "-", "base": "-"} for k in ["HP", "DS", "AT", "AS", "CT", "HT", "DE", "EV"]}
    for t in tables:
        headers = [str(h).lower() for h in t.get("headers", [])]
        if any("stats" in h for h in headers) or any("basevalue" in h for h in headers):
            for row in t.get("rows", []):
                if len(row) >= 3:
                    key = parse_stat_name(str(row[1]).strip())
                    if key:
                        max_v = clean_stat_val(str(row[2]))
                        base_v = clean_stat_val(str(row[3])) if len(row) > 3 else max_v
                        stats[key] = {"max": max_v, "base": base_v}

    meta = {}
    for t in tables:
        rows = t.get("rows", [])
        for i, row in enumerate(rows):
            if len(row) >= 4 and any("cooldown" in str(c).lower() for c in row):
                desc = str(rows[i + 1][1]).strip() if i + 1 < len(rows) and len(rows[i + 1]) >= 2 else ""
                meta[str(row[0]).strip().lower()] = {
                    "element": str(row[1]).strip(),
                    "cooldown": str(row[2]).strip(),
                    "ds": str(row[3]).strip(),
                    "points": str(row[4]).strip() if len(row) > 4 else "",
                    "animation": str(row[5]).strip() if len(row) > 5 else "",
                    "description": desc,
                }

    skills = []
    for t in tables:
        headers = [str(h) for h in t.get("headers", [])]
        if "Lv.1" in headers and "Lv.25" in headers:
            for row in t.get("rows", []):
                if len(row) >= 26 and row != headers and str(row[1]).strip() != "Attack":
                    name = str(row[1]).strip() or str(row[0]).strip()
                    m = meta.get(name.lower(), {})
                    skills.append({
                        "name": name,
                        "element": m.get("element", ""),
                        "cooldown": m.get("cooldown", "-"),
                        "ds_consumed": m.get("ds", "-"),
                        "upgrade_points": m.get("points", "-"),
                        "animation": m.get("animation", "-"),
                        "description": m.get("description", ""),
                        "levels": [str(v).strip() for v in row[2:27]],
                    })

    passives = []
    if "Rank Passives:" in text:
        part = text[text.find("Rank Passives:"):text.find("Categories")]
        part = re.split(r"\n(?:Promo Art|Gallery|Notes?|Trivia|References)\n", part)[0]
        for l in part.split("\n"):
            l = l.strip()
            if len(l) > 3 and not l.startswith(("Categories", "Rank Passives")):
                passives.append(l)

    # First real paragraph after the infobox ("Available:" is its last row)
    lore = ""
    if "Available:" in text:
        after = [l.strip() for l in text.split("Available:", 1)[1].split("\n")[2:80]]
        start = next((i for i, l in enumerate(after) if len(l) > 60 and "was added to" not in l), None)
        if start is not None:
            # Inline links split a paragraph into several lines: re-join until the sentence ends
            parts = []
            for l in after[start:]:
                parts.append(l)
                joined = " ".join(parts)
                if (l.endswith(".") and len(l) > 40) or len(joined) > 1500:
                    break
            # Paragraph opens with the bold page title on its own line ("GeoGreymon" / "is a ...")
            if start > 0 and parts[0][:1].islower() and after[start - 1]:
                parts.insert(0, after[start - 1])
            lore = re.sub(r"\s+([,.)])", r"\1", " ".join(parts))
    if not lore:
        m = re.search(r'(?:[A-Z][a-zA-Z\s\-]+(?:is an?)[\s\S]{50,600}?\.)', text)
        if m:
            lore = re.sub(r"\s*\n\s*", " ", m.group(0)).strip()
    return {"stats": stats, "skills": skills, "passives": passives, "lore": lore}

def build_cache():
    print("[INIT] Building High-Speed Memory Cache from dmowiki.db...")
    if not DB_PATH.exists():
        print(f"[ERROR] Database {DB_PATH} not found!")
        return

    build_image_index()
    conn = get_db()
    c = conn.cursor()

    # 1. Digimon dex (profiles, ranks, icons, per-page evolution trees)
    dex = Dex(DB_PATH, IMAGES_DIR)
    dex.build()
    aoe_table = {}
    row = c.execute("SELECT data_json FROM pages WHERE slug='Area_of_Effect_Skills'").fetchone()
    if row:
        for tb in json.loads(row[0]).get("tables", []):
            if "Effective Area" in tb.get("headers", []) and "Digimon" in tb.get("headers", []):
                aoe_table = load_aoe_table(tb["rows"])
    aoe_overrides = {}
    ov_path = Path(__file__).parent / "aoe_overrides.json"
    if ov_path.exists():
        aoe_overrides = {k: v for k, v in json.loads(ov_path.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    skill_overrides = {}
    sk_path = Path(__file__).parent / "skill_overrides.json"
    if sk_path.exists():
        try:
            skill_overrides = {k: v for k, v in json.loads(sk_path.read_text(encoding="utf-8")).items() if not k.startswith("_")}
        except Exception as e:
            print("[WARN] skill_overrides failed:", e)
    evo_unlocks = {}
    eu_path = Path(__file__).parent / "evolution_unlocks.json"
    if eu_path.exists():
        try:
            evo_unlocks = json.loads(eu_path.read_text(encoding="utf-8"))
            print(f"[INIT] Loaded {len(evo_unlocks)} evolution unlocks from client data")
        except Exception as e:
            print("[WARN] evolution_unlocks failed:", e)
    try:
        thai_patch = ThaiPatch(dex)
        print(f"[INIT] Thai patch notes: {len(thai_patch.articles)} articles, {len(thai_patch.digimon)} Digimon matched, "
              f"{len(thai_patch.unmatched)} Thai names not matched")
    except Exception as e:  # never block the site on the patch-note data
        print("[WARN] Thai patch notes failed:", e)
        thai_patch = None
    CACHE["thai_patch_unmatched"] = sorted(thai_patch.unmatched) if thai_patch else []
    try:
        client_evo = ClientEvo(dex)
        print(f"[INIT] Thai client unlock items: {len(client_evo.by_slug)} Digimon matched, "
              f"{len(client_evo.unmatched)} client ids not matched")
    except Exception as e:  # never block the site
        print("[WARN] Thai client unlock items failed:", e)
        client_evo = None
    digimon_list = []
    for d in dex.digimon:
        p = dex.public(d)
        p.update(extract_combat(d["_data"]))
        # Thai text from web/i18n (empty string = not translated yet -> UI falls back to English)
        for s in p["skills"]:
            s["name_th"] = dex.i18n_skills.get(s["name"], "")
            s["description_th"] = dex.text_th(s["description"])
        # official Thai-server values from vplay.in.th patch notes (hand overrides below still win)
        if thai_patch:
            thai_patch.apply(p)
        d_ov = skill_overrides.get(p["title"]) or skill_overrides.get(p["slug"]) or skill_overrides.get(p.get("thai_name"))
        if d_ov and isinstance(d_ov, dict):
            for i, s in enumerate(p["skills"], 1):
                slot_key = f"F{i}"
                ov = d_ov.get(str(i)) or d_ov.get(slot_key) or d_ov.get(s["name"])
                if ov and isinstance(ov, dict):
                    for k in ["cooldown", "ds_consumed", "upgrade_points", "animation", "description", "name", "name_th", "description_th"]:
                        if k in ov:
                            s[k] = ov[k]
                    if "description_th" in ov and "description" not in ov:
                        s["description"] = ov["description_th"]
                    if "levels" in ov:
                        s["levels"] = [str(x) for x in ov["levels"]]
                    elif "damage" in ov:
                        if isinstance(ov["damage"], list):
                            s["levels"] = [str(x) for x in ov["damage"]]
                        else:
                            s["levels"] = [str(ov["damage"])]
        if p["slug"] in evo_unlocks:
            p["unlock_items"] = evo_unlocks[p["slug"]]
        # real unlock items read from the client's evolution table (devolutionlist.bin): wins over
        # dmowiki, patch notes and evolution_unlocks.json (name-matched catalogue, kept as fallback)
        if client_evo:
            client_evo.apply(p)
        p["passives_th"] = [dex.text_th(x) or x for x in p["passives"]] if any(dex.text_th(x) for x in p["passives"]) else []
        p["lore_th"] = dex.text_th(p["lore"])
        p.update(parse_effects(d["_data"].get("text", "")))
        # Fallback: rebuild "Group: / Label / : value" triples from the passives list
        if not p["rank_passives"] and p["passives"]:
            cur, lab = None, None
            for x in p["passives"]:
                x = x.strip()
                if x.endswith(":") and not x.startswith(":"):
                    cur = None
                    if x[:-1].strip() in EFFECT_GROUPS:
                        cur = {"group": x[:-1].strip(), "fields": []}
                        p["rank_passives"].append(cur)
                    lab = None
                elif x.startswith(":") and cur is not None:
                    cur["fields"].append([lab or "Effect", x.lstrip(": ").strip()])
                    lab = None
                elif cur is not None and len(x) < 25:
                    lab = x
                elif cur is not None:
                    cur["fields"].append(["Effect", x])
            p["rank_passives"] = [g for g in p["rank_passives"] if g["fields"]]
        aoe = parse_aoe(d["_data"].get("text", ""), p["skills"], p["skill_effects"], aoe_table, p["title"])
        ov = aoe_overrides.get(p["title"]) or {}
        for slot, info in (ov.get("add") or {}).items():
            aoe[int(slot)] = {"shape": info.get("shape", ""), "size": info.get("size", ""), "thai": True}
        for slot in ov.get("remove") or []:
            aoe.pop(int(slot), None)
        for i, s in enumerate(p["skills"], 1):
            s["aoe"] = aoe.get(i)
        p["aoe_slots"] = sorted(aoe)
        digimon_list.append(p)

    # Rank passive table: same Rank + attribute/element always gives the same effect on the wiki,
    # so learn it from the pages that list it and fill in every ranked Digimon.
    GROUP_ALIAS = {"Earth": "Land", "Darkness": "Pitch Black"}
    agg = {}
    for p in digimon_list:
        for g in p["rank_passives"]:
            g["fields"] = [f for f in g["fields"] if f[1]]
            g["group"] = GROUP_ALIAS.get(g["group"], g["group"])
            if p["rank"] and g["fields"]:
                key = json.dumps(g["fields"], ensure_ascii=False)
                agg.setdefault((p["rank"], g["group"]), {}).setdefault(key, 0)
                agg[(p["rank"], g["group"])][key] += 1
    rank_table = {}
    for (rank, group), variants in agg.items():
        best = max(variants.items(), key=lambda kv: kv[1])[0]
        rank_table.setdefault(rank, {})[group] = json.loads(best)
    CACHE["rank_table"] = rank_table

    def auto_th(s):
        """Durations / chances follow fixed patterns: translate them by rule."""
        t = s.strip()
        m = re.fullmatch(r"([\d.?]+)\s*(?:s|sec|secs|second|seconds)\.?", t, re.I)
        if m:
            return f"{m.group(1)} วินาที"
        m = re.fullmatch(r"([\d.]+)\s*(?:minute|minutes|min)\.?", t, re.I)
        if m:
            return f"{m.group(1)} นาที"
        m = re.fullmatch(r"([\d.?]+)\s*%\s*(?:chance)?", t, re.I)
        if m:
            return f"{m.group(1)}%" if "chance" not in t.lower() else f"โอกาส {m.group(1)}%"
        m = re.fullmatch(r"([\d.?]+)", t)
        if m:
            return f"{m.group(1)} วินาที"
        return ""

    def th_field(f):
        return [f[0], f[1], dex.text_th(f[1]) or dex.text_th(": " + f[1]).lstrip(": ") or auto_th(f[1])]

    CACHE["rank_table_th"] = {r: {g: [th_field(f) for f in fs] for g, fs in gs.items()} for r, gs in rank_table.items()}

    for p in digimon_list:
        page_groups = {g["group"] for g in p["rank_passives"]}
        for grp in (p["attribute"], p["element"]):
            if p["rank"] in rank_table and grp in rank_table[p["rank"]] and grp not in page_groups:
                p["rank_passives"].append({"group": grp, "fields": rank_table[p["rank"]][grp], "derived": True})
        for g in p["rank_passives"]:
            g["fields"] = [th_field(f) for f in g["fields"]]
        for e in p["skill_effects"]:
            e["fields"] = [th_field(f) for f in e["fields"]]
        p["overview"] = {k: [[x, dex.text_th(x)] for x in v] for k, v in p["overview"].items()}
    # Only Digimon that exist in the Thai client are listed; the rest stay reachable for tree links
    CACHE["digimon"] = [d for d in digimon_list if d.get("in_thai", True)]
    try:
        CACHE["jogress_quests"] = build_jogress_quests(dex, CACHE["digimon"])
        jq_slugs = {g["slug"] for g in CACHE["jogress_quests"]}
        for p in CACHE["digimon"]:
            p["has_jogress_quest"] = p["slug"] in jq_slugs
        print(f"[INIT] Jogress quests: {len(CACHE['jogress_quests'])} Digimon, "
              f"{sum(g['quest_count'] for g in CACHE['jogress_quests'])} quests")
    except Exception as ex:
        print("[WARN] Jogress quests failed, falling back to cache:", ex)
        jq_cache = Path(__file__).resolve().parent / "jogress_quests_cache.json"
        if jq_cache.exists():
            CACHE["jogress_quests"] = json.loads(jq_cache.read_text(encoding="utf-8"))
        else:
            CACHE["jogress_quests"] = []
    try:
        CACHE["decks"] = build_decks(dex, CACHE["digimon"])
        if not CACHE["decks"]:
            dk_cache = Path(__file__).resolve().parent / "decks_cache.json"
            if dk_cache.exists():
                CACHE["decks"] = json.loads(dk_cache.read_text(encoding="utf-8"))
        in_deck = {}
        for dk in CACHE["decks"]:
            for m in dk.get("members", []):
                if m.get("slug") and all(x["id"] != dk["id"] for x in in_deck.get(m["slug"], [])):
                    in_deck.setdefault(m["slug"], []).append({"id": dk["id"], "name": dk["name"]})
        for p in CACHE["digimon"]:
            p["decks"] = in_deck.get(p["slug"], [])
        print(f"[INIT] Digimon Archive decks: {len(CACHE['decks'])}")
    except Exception as ex:
        print("[WARN] Decks failed, falling back to cache:", ex)
        dk_cache = Path(__file__).resolve().parent / "decks_cache.json"
        if dk_cache.exists():
            CACHE["decks"] = json.loads(dk_cache.read_text(encoding="utf-8"))
        else:
            CACHE["decks"] = []
    try:
        CACHE["eggs"] = build_eggs(dex, conn)
        print(f"[INIT] Cached {len(CACHE['eggs'])} DigiEggs")
    except Exception as ex:  # never block the whole site on the egg catalogue
        print("[WARN] DigiEgg catalogue failed, falling back to cache:", ex)
        egg_cache = Path(__file__).resolve().parent / "eggs_cache.json"
        if egg_cache.exists():
            CACHE["eggs"] = json.loads(egg_cache.read_text(encoding="utf-8"))
        else:
            CACHE["eggs"] = []
    CACHE["not_in_thai"] = sorted(d["title"] for d in digimon_list if not d.get("in_thai", True))
    print(f"[INIT] Thai client: {len(CACHE['digimon'])} available, {len(CACHE['not_in_thai'])} hidden (not in Thai client)")
    CACHE["digimon_by_slug"] = {}
    for d in digimon_list:
        CACHE["digimon_by_slug"][d["slug"].lower()] = d
        CACHE["digimon_by_slug"].setdefault(d["title"].lower(), d)
    for alias, d in dex.by_key.items():
        CACHE["digimon_by_slug"].setdefault(alias, CACHE["digimon_by_slug"][d["slug"].lower()])
    print(f"[INIT] Cached {len(digimon_list)} Digimon profiles with evolution trees")

    # 2. Seals Caching (CrackDMO Binary + Thai Strings + Wiki Drop Cross-Ref)
    try:
        sm_payload = build_seals()
        seals = sm_payload.get("seals", [])
        if not seals:
            sm_cache = Path(__file__).resolve().parent / "seals_cache.json"
            if sm_cache.exists():
                sm_payload = json.loads(sm_cache.read_text(encoding="utf-8"))
                seals = sm_payload.get("seals", [])
        CACHE["seal_master"] = sm_payload
        CACHE["seals"] = seals
        CACHE["seals_by_slug"] = {s["slug"]: s for s in seals}
        for s in seals:
            CACHE["seals_by_slug"][str(s["id"])] = s
        print(f"[INIT] Cached {len(seals)} CrackDMO Seal Master records!")
    except Exception as sex:
        print("[WARN] Seal Master build failed, falling back to cache:", sex)
        sm_cache = Path(__file__).resolve().parent / "seals_cache.json"
        if sm_cache.exists():
            sm_payload = json.loads(sm_cache.read_text(encoding="utf-8"))
            seals = sm_payload.get("seals", [])
            CACHE["seal_master"] = sm_payload
            CACHE["seals"] = seals
            CACHE["seals_by_slug"] = {s["slug"]: s for s in seals}
            for s in seals:
                CACHE["seals_by_slug"][str(s["id"])] = s
        else:
            seals = []
            CACHE["seal_master"] = {"seals": [], "stat_totals": [], "worlds": [], "maps": [], "tier_meta": [], "opener_closer_rules": {}}
            CACHE["seals"] = []
            CACHE["seals_by_slug"] = {}

    # 2b. D-Unit Caching (CrackDMO Binary tables + Thai Strings)
    try:
        import dunits
        CACHE["dunits"] = dunits.build(dex, CACHE["digimon"])
        print(f"[INIT] Cached {CACHE['dunits']['total_groups']} D-Unit Groups + {CACHE['dunits']['total_hackable_forms']} Hackable forms!")
    except Exception as dex_err:
        print("[WARN] D-Unit build failed, falling back to cache:", dex_err)
        du_cache = Path(__file__).resolve().parent / "dunits_cache.json"
        if du_cache.exists():
            CACHE["dunits"] = json.loads(du_cache.read_text(encoding="utf-8"))
        else:
            CACHE["dunits"] = {"total_groups": 0, "total_hackable_forms": 0, "master_tiers": [], "filters": [], "stat_totals": {}, "groups": []}

    # 3. Dungeons Caching
    c.execute("""
        SELECT slug, title, data_json FROM pages 
        WHERE (title LIKE '%(Instance Dungeon)%' OR title LIKE '%Dungeon%' OR categories LIKE '%Instance Dungeons%' OR categories LIKE '%Dungeons%' OR title IN ('Royal Base', 'Datamon Maze', 'Datamon Maze (Normal Mode)', 'Datamon Maze (Hard Mode)'))
          AND title NOT LIKE 'Information for%' 
          AND title NOT LIKE 'Talk:%'
          AND title NOT LIKE '%Pass%' 
          AND title NOT LIKE '%Box%'
          AND title NOT LIKE 'File:%'
    """)
    dungeons_dict = {}
    for r in c.fetchall():
        d_slug = r["slug"]
        d_title = r["title"]
        if "Redirect page" in r["data_json"]:
            continue
        try:
            d_data = json.loads(r["data_json"])
        except:
            continue
        
        base_title = d_title.replace(" (Instance Dungeon)", "").strip()
        if base_title in dungeons_dict and len(d_data.get("tables", [])) <= len(dungeons_dict[base_title].get("mobs", [])):
            continue

        d_tables = d_data.get("tables", [])
        mobs = []
        for t in d_tables:
            h = t.get("headers", [])
            rows = t.get("rows", [])
            if h and len(h) == 1 and rows:
                mob_name = h[0]
                hp_val = "-"
                lv_val = "-"
                for row in rows:
                    r_str = " ".join([str(x) for x in row])
                    if "HP:" in r_str:
                        m_hp = re.search(r'HP:\s*([0-9\s,]+)', r_str)
                        if m_hp: hp_val = m_hp.group(1).strip()
                    if "Level(s):" in r_str:
                        m_lv = re.search(r'Level\(s\):\s*([0-9\s+]+)', r_str)
                        if m_lv: lv_val = m_lv.group(1).strip()
                mobs.append({
                    "name": mob_name,
                    "image": resolve_image(mob_name),
                    "hp": hp_val,
                    "level": lv_val
                })
        
        text = d_data.get("text", "")
        drops = []
        entry_req = "ไม่ต้องมีเงื่อนไขพิเศษ"
        if "Entry" in text or "Pass" in text or "Condition" in text:
            for l in text.split("\n"):
                if any(k in l.lower() for k in ["pass", "level more than", "entry", "conditions"]):
                    if len(l.strip()) > 5 and len(l.strip()) < 100:
                        entry_req = l.strip()
                        break

        drop_match = re.search(r'\n(?:Drops|Drops from[^\n]*|Rewards?)\n([\s\S]{1,600}?)(?:\n(?:Loading Screen|Categories|Notes|Note|$)|\n\n\n)', text)
        if drop_match:
            d_lines = [line.strip() for line in drop_match.group(1).split("\n") if line.strip()]
            for item_line in d_lines:
                if len(item_line) > 2 and not item_line.isdigit() and "Loading" not in item_line:
                    drops.append(item_line)

        d_type = "ดันเจี้ยนทั่วไป (Instance)"
        if "Holy Beast" in text or any(hb in d_title for hb in ["Scar of Water", "Uprising Flame", "Trace of Black Steel", "Descending Thunder", "Fanglongmon"]):
            d_type = "ดันเจี้ยน 4 จตุรเทพ (Four Holy Beasts)"
        elif "Royal Base" in d_title:
            d_type = "ดันเจี้ยนรอยัลเบส (Royal Base)"
        elif "Terminal" in d_title:
            d_type = "ดันเจี้ยน D-Terminal"
        elif "Maze" in d_title:
            d_type = "ดันเจี้ยนเขาวงกต (Maze)"

        dungeons_dict[base_title] = {
            "slug": d_slug,
            "title": d_title,
            "display_title": base_title,
            "type": d_type,
            "entry_requirement": entry_req,
            "mobs": mobs,
            "drops": drops[:15],
            "description": text[:350].strip()
        }

    CACHE["dungeons"] = list(dungeons_dict.values())
    # The Thai client is the source for dungeons (list, entry NPCs, monsters + HP, loot, quests, exchange NPCs)
    try:
        dg_cache = Path(__file__).resolve().parent / "dungeons_client_cache.json"
        if dg_cache.exists():
            CACHE["dungeons"] = json.loads(dg_cache.read_text(encoding="utf-8"))
        else:
            from dungeons_client import build as build_client_dungeons
            cd = build_client_dungeons()
            if cd:
                def loose_th(s):
                    return re.sub(r"[่้๊๋์]", "", re.sub(r"\s+", "", s or "")).replace("ร", "ล")
                by_th = {}
                for d in digimon_list:
                    if d.get("thai_name"):
                        by_th.setdefault(loose_th(d["thai_name"]), d)
                for dg in cd:
                    for m in dg["monsters"] + [st["monster"] for st in dg["steps"] if st.get("monster")]:
                        d = by_th.get(loose_th(m["name"]))
                        if d:
                            m["slug"] = d["slug"]
                            m["icon"] = m["icon"] or d.get("icon", "")
                CACHE["dungeons"] = cd
    except Exception as ex:
        print("[WARN] client dungeons failed, keeping dmowiki list:", ex)
    print(f"[INIT] Cached {len(CACHE['dungeons'])} Dungeons")

    # 4. Crafting Caching
    c.execute("""
        SELECT slug, title, data_json FROM pages 
        WHERE title = 'Nanomon (Item Craft)' OR title = 'Digitamamon (Item Make)' OR title LIKE '%(Item Craft)%'
    """)
    crafts = []
    for r in c.fetchall():
        npc_title = r["title"].replace(" (Item Craft)", "").replace(" (Item Make)", "").strip()
        cr_data = json.loads(r["data_json"])
        for t in cr_data.get("tables", []):
            h = t.get("headers", [])
            if any("Production" in str(x) or "Materials" in str(x) for x in h):
                for row in t.get("rows", []):
                    if len(row) >= 4 and row[0] != h[0]:
                        item_name = str(row[1]).strip() if len(row) > 1 else str(row[0]).strip()
                        materials = str(row[2]).strip() if len(row) > 2 else "-"
                        cost = str(row[3]).strip() if len(row) > 3 else "0"
                        rate = str(row[4]).strip() if len(row) > 4 else "100%"
                        crafts.append({
                            "npc": npc_title,
                            "item": item_name,
                            "image": resolve_image(item_name),
                            "materials": materials,
                            "cost": cost,
                            "success_rate": rate
                        })
    CACHE["crafts"] = crafts
    print(f"[INIT] Cached {len(crafts)} Craft recipes!")

    try:
        t_cache = Path(__file__).resolve().parent / "tamers_cache.json"
        if t_cache.exists():
            t_payload = json.loads(t_cache.read_text(encoding="utf-8"))
        else:
            t_payload = build_tamers()
        if isinstance(t_payload, dict):
            CACHE["tamers"] = t_payload.get("tamers", [])
            CACHE["tamer_skill_system"] = t_payload.get("skill_system", {})
            CACHE["tamer_status"] = t_payload.get("tamer_status", {})
        else:
            CACHE["tamers"] = t_payload
            CACHE["tamer_skill_system"] = {}
        try:
            model_map = build_tamer_models()
            for tm in CACHE["tamers"]:
                m = model_map.get(tm["id"])
                if m:
                    tm["model_url"] = m.get("url", f"/models/tamers/{tm['id']}.glb")
                    tm["model_verts"] = m.get("verts", 0)
                    tm["model_tris"] = m.get("tris", 0)
                    tm["model_nif"] = m.get("nif", "")
        except Exception as mex:
            print("[WARN] Tamer 3D models skipped:", mex)
        print(f"[INIT] Cached {len(CACHE['tamers'])} Tamers + revamped skill system from Thai client")
    except Exception as ex:
        print("[WARN] Tamers failed:", ex)
        CACHE["tamers"] = []
        CACHE["tamer_skill_system"] = {}

    # 6. Overall Stats
    c.execute("SELECT count(1) FROM pages")
    total_p = c.fetchone()[0]
    img_count = len(os.listdir(IMAGES_DIR)) if IMAGES_DIR.exists() else 0
    CACHE["stats"] = {
        "total_digimon": len(CACHE["digimon"]),
        "not_in_thai": len(CACHE["not_in_thai"]),
        "total_seals": len(seals),
        "total_dungeons": len(CACHE["dungeons"]),
        "total_crafts": len(crafts),
        "total_tamers": len(CACHE["tamers"]),
        "total_pages": total_p,
        "total_images": img_count
    }
    conn.close()
    print("[INIT] High-Speed Cache Built Successfully!")

# API Endpoints
@app.get("/api/stats")
def get_stats():
    return CACHE["stats"]

@app.get("/api/npc-exchange/{npc_id}")
def get_npc_exchange(npc_id: int):
    """Every item an exchange NPC trades (Thai client itemcreation.bin)."""
    import dungeons_client
    return dungeons_client.EXCHANGES.get(npc_id, [])


@app.get("/api/decks")
def get_decks():
    """Digimon Archive decks of the Thai server: members + the buffs a completed deck gives."""
    return CACHE.get("decks", [])


@app.get("/api/dunits")
def get_dunits():
    """D-Unit system from Thai client binary tables (groups, tiers, stats, hacking requirements)."""
    return CACHE.get("dunits", {})


@app.get("/api/jogress-quests")
def get_jogress_quests():
    """Jogress quest lines from the Thai client, one entry per Jogress Digimon (quests listed in full)."""
    return CACHE.get("jogress_quests", [])


@app.get("/api/eggs")
def get_eggs():
    return CACHE.get("eggs", [])


@app.get("/api/digimon")
def get_digimon(
    q: Optional[str] = Query(None, description="Search by name or Thai name"),
    rank: Optional[str] = Query(None, description="Filter by rank: N, A, A+, S, S+, SS, SS+, SSS, SSS+, U"),
    attribute: Optional[str] = Query(None, description="Filter by attribute"),
    element: Optional[str] = Query(None, description="Filter by element"),
    sort: str = Query("rank", description="rank | name | at | hp"),
    limit: int = 40,
    offset: int = 0
):
    results = CACHE["digimon"]
    def num(d, k):
        try:
            return float(d["stats"][k]["max"].replace("%", ""))
        except (ValueError, KeyError):
            return -1
    if sort == "name":
        results = sorted(results, key=lambda d: d["title"].lower())
    elif sort in ("at", "hp"):
        results = sorted(results, key=lambda d: -num(d, sort.upper()))
    if q:
        q_lower = q.lower().strip()
        results = [
            d for d in results 
            if q_lower in d["title"].lower() 
            or q_lower in d["thai_name"].lower() 
            or q_lower in d["slug"].lower()
        ]
    if rank and rank != "all":
        if rank == "none":
            results = [d for d in results if not d["rank"]]
        else:
            results = [d for d in results if rank.upper() == d["rank"].upper()]
    if attribute and attribute != "all":
        results = [d for d in results if attribute.lower() == d["attribute"].lower()]
    if element and element != "all":
        results = [d for d in results if element.lower() == d["element"].lower()]

    total = len(results)
    light = ("tree", "skills", "passives", "passives_th", "lore", "lore_th", "categories",
             "skill_effects", "rank_passives", "overview")
    paged = [{k: v for k, v in d.items() if k not in light} for d in results[offset:offset+limit]]
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": paged
    }

@app.get("/api/digimon-filters")
def get_digimon_filters():
    """Available ranks / attributes / elements with their icons, for the filter bar."""
    attrs, elems = {}, {}
    for d in CACHE["digimon"]:
        if d["attribute"]:
            attrs.setdefault(d["attribute"], {"name": d["attribute"], "th": d["attribute_th"], "icon": d["attribute_icon"], "count": 0})["count"] += 1
        if d["element"]:
            elems.setdefault(d["element"], {"name": d["element"], "th": d["element_th"], "icon": d["element_icon"], "count": 0})["count"] += 1
    ranks = []
    for r in RANK_ORDER:
        n = sum(1 for d in CACHE["digimon"] if d["rank"] == r)
        if n:
            icon = next((d["rank_icon"] for d in CACHE["digimon"] if d["rank"] == r and d["rank_icon"]), "")
            ranks.append({"name": r, "icon": icon, "count": n})
    return {
        "ranks": ranks,
        "no_rank": sum(1 for d in CACHE["digimon"] if not d["rank"]),
        "attributes": sorted(attrs.values(), key=lambda x: -x["count"]),
        "elements": sorted(elems.values(), key=lambda x: -x["count"]),
    }

@app.get("/api/rank-table")
def get_rank_table():
    """Rank passive effects per Rank (SSS..U) and attribute/element, learned from dmowiki pages."""
    return CACHE.get("rank_table_th", {})

PATCH_ARCH = OUTPUT_DIR / "thai_patch_archive"
_PATCH_IDX = {"mtime": None, "items": []}


def patch_index():
    """index.json is ~6 MB (full text for search): keep it in memory, reload when the file changes."""
    p = PATCH_ARCH / "index.json"
    if not p.exists():
        return []
    m = p.stat().st_mtime
    if _PATCH_IDX["mtime"] != m:
        _PATCH_IDX.update(mtime=m, items=json.loads(p.read_text(encoding="utf-8")))
    return _PATCH_IDX["items"]


_PATCH_SYNC_LOCK = threading.Lock()
_PATCH_THREAD_STARTED = False
PATCH_SYNC_INTERVAL = 1800  # 30 minutes
_PATCH_SYNC_STATE = {
    "running": False,
    "auto_enabled": True,
    "interval_sec": PATCH_SYNC_INTERVAL,
    "last_check": "",
    "last_updated": "",
    "last_error": "",
    "last_source": "",
    "new_count": 0,
    "new_items": [],
}


def run_patch_sync(force_latest: bool = False, source: str = "auto") -> dict:
    if not _PATCH_SYNC_LOCK.acquire(blocking=(source == "manual")):
        return {**_PATCH_SYNC_STATE, "ok": True, "updated": False, "busy": True}
    try:
        _PATCH_SYNC_STATE["running"] = True
        _PATCH_SYNC_STATE["last_source"] = source
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res = thai_patch_syncer.sync_latest(max_pages=2, refresh_latest=force_latest)
        _PATCH_SYNC_STATE["last_check"] = now_str
        if res.get("ok"):
            _PATCH_SYNC_STATE["last_error"] = ""
            _PATCH_SYNC_STATE["new_count"] = res.get("new_count", 0)
            _PATCH_SYNC_STATE["new_items"] = res.get("new_items", [])
            if res.get("updated"):
                _PATCH_SYNC_STATE["last_updated"] = now_str
                _PATCH_IDX["mtime"] = None
                patch_index()
                if any(it.get("has_digimon") for it in res.get("new_items", [])):
                    build_cache()
                print(f"[PATCH SYNC:{source}] Updated archive -> total {res.get('total')} (new={res.get('new_count')})")
            else:
                print(f"[PATCH SYNC:{source}] Up to date ({res.get('total')} patches)")
        else:
            _PATCH_SYNC_STATE["last_error"] = res.get("error", "Sync failed")
            print(f"[PATCH SYNC:{source}] Failed: {_PATCH_SYNC_STATE['last_error']}")
        _PATCH_SYNC_STATE["running"] = False
        return {**_PATCH_SYNC_STATE, **res}
    except Exception as ex:
        _PATCH_SYNC_STATE["last_error"] = str(ex)
        print(f"[PATCH SYNC:{source}] Exception:", ex)
        return {**_PATCH_SYNC_STATE, "ok": False, "updated": False, "error": str(ex)}
    finally:
        _PATCH_SYNC_STATE["running"] = False
        _PATCH_SYNC_LOCK.release()


def _patch_sync_loop():
    time.sleep(3)
    run_patch_sync(force_latest=False, source="startup")
    while True:
        time.sleep(PATCH_SYNC_INTERVAL)
        run_patch_sync(force_latest=False, source="timer")


def start_patch_sync_worker():
    global _PATCH_THREAD_STARTED
    if _PATCH_THREAD_STARTED:
        return
    _PATCH_THREAD_STARTED = True
    t = threading.Thread(target=_patch_sync_loop, name="vplay-patch-sync", daemon=True)
    t.start()
    print(f"[INIT] Auto patch-note sync enabled (every {PATCH_SYNC_INTERVAL // 60} min from vplay.in.th)")


@app.get("/api/patches")
def list_patches():
    """Full offline copy of the Thai-server patch notes (made by web/thai_patch_archive.py)."""
    items = patch_index()
    return {"total": len(items), "items": items, "sync": _PATCH_SYNC_STATE}


@app.get("/api/patches/status")
def get_patch_sync_status():
    items = patch_index()
    latest = items[0] if items else None
    return {
        **_PATCH_SYNC_STATE,
        "total": len(items),
        "latest": {"id": latest["id"], "title": latest["title"], "date_iso": latest.get("date_iso", "")} if latest else None,
    }


@app.get("/api/patches/{pid}")
def get_patch(pid: str):
    if not re.fullmatch(r"[\w\-]{1,60}", pid):
        raise HTTPException(status_code=400, detail="bad id")
    meta = next((a for a in patch_index() if a["id"] == pid), None)
    f = PATCH_ARCH / f"{pid}.html"
    if not meta or not f.exists():
        raise HTTPException(status_code=404, detail="patch not found")
    return {**{k: v for k, v in meta.items() if k != "search"}, "html": f.read_text(encoding="utf-8")}


@app.get("/api/thai-patch-unmatched")
def thai_patch_unmatched():
    """Thai names from vplay.in.th patch notes that are not linked to a Digimon yet (fill web/thai_name_map.json)."""
    return {"total": len(CACHE.get("thai_patch_unmatched", [])), "items": CACHE.get("thai_patch_unmatched", [])}


@app.get("/api/not-in-thai")
def get_not_in_thai():
    """Digimon hidden because no model was found in the Thai client (edit web/thai_overrides.json to fix)."""
    return {"total": len(CACHE["not_in_thai"]), "items": CACHE["not_in_thai"]}

@app.get("/api/digimon/{slug:path}")
def get_digimon_detail(slug: str):
    d = CACHE["digimon_by_slug"].get(slug.lower()) or CACHE["digimon_by_slug"].get(re.sub(r'[^a-z0-9]', '', slug.lower()))
    if not d:
        raise HTTPException(status_code=404, detail="Digimon not found")
    return {"digimon": d}

@app.get("/api/seals")
def get_seals(
    q: Optional[str] = Query(None),
    stat: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    map_id: Optional[int] = Query(None),
):
    payload = CACHE.get("seal_master") or {}
    results = payload.get("seals", [])
    if q:
        q_l = q.lower().strip()
        results = [
            s for s in results
            if q_l in s["name_th"].lower()
            or q_l in s["name_en"].lower()
            or q_l in s["stat_key"].lower()
            or any(q_l in m["map_name"].lower() or q_l in m["world_name"].lower() for m in s.get("hunting_maps", []))
            or any(q_l in c["npc"].lower() or any(q_l in mt["name"].lower() for mt in c.get("materials", [])) for c in s.get("crafts", []))
            or any(q_l in n.lower() for n in s.get("extra_notes", []))
            or q_l in (s.get("wiki_drop_en") or "").lower()
        ]
    if stat and stat != "all":
        st_u = stat.upper().strip()
        results = [s for s in results if s["stat_key"] == st_u]
    if source and source != "all":
        results = [s for s in results if source in s.get("source_categories", [])]
    if map_id:
        results = [s for s in results if any(m["map_id"] == map_id for m in s.get("hunting_maps", []))]
    return {
        "total": len(results),
        "all_total": payload.get("total", len(results)),
        "stat_totals": payload.get("stat_totals", []),
        "worlds": payload.get("worlds", []),
        "maps": payload.get("maps", []),
        "tier_meta": payload.get("tier_meta", []),
        "opener_closer_rules": payload.get("opener_closer_rules", {}),
        "items": results,
    }


@app.get("/api/seals/{ref:path}")
def get_seal_detail(ref: str):
    from urllib.parse import unquote
    key = unquote(ref).strip().strip("/")
    by_slug = CACHE.get("seals_by_slug", {})
    s = by_slug.get(key) or by_slug.get(key.lower())
    if not s:
        # Try case-insensitive match by name_th / name_en
        kl = key.lower()
        for cand in CACHE.get("seals", []):
            if cand["slug"].lower() == kl or cand["name_th"].lower() == kl or cand["name_en"].lower() == kl:
                s = cand
                break
    if not s:
        raise HTTPException(status_code=404, detail="Seal not found")
    payload = CACHE.get("seal_master") or {}
    return {
        "seal": s,
        "opener_closer_rules": payload.get("opener_closer_rules", {}),
        "tier_meta": payload.get("tier_meta", []),
    }

@app.get("/api/tamers")
def get_tamers(
    q: Optional[str] = Query(None),
    series: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    unlock: Optional[str] = Query(None),
):
    results = CACHE.get("tamers", [])
    if q:
        ql = q.lower().strip()
        results = [
            t for t in results
            if ql in t["name_th"].lower()
            or ql in t["name_en"].lower()
            or ql in t["series"].lower()
            or ql in t["partner"].lower()
            or any(ql in s["name"].lower() for s in t["active_skills"] + t["passive_skills"])
        ]
    if series and series != "all":
        results = [t for t in results if t["series"] == series]
    if gender and gender != "all":
        results = [t for t in results if t["gender"] == gender]
    if unlock == "starter":
        results = [t for t in results if t["starter"]]
    elif unlock == "unlock":
        results = [t for t in results if not t["starter"]]
    # Omit 180-level array on list endpoint so payload stays light; /api/tamers/{tid} returns full curve
    summary = [{k: v for k, v in t.items() if k != "stats_levels"} for t in results]
    series_list = sorted({t["series"] for t in CACHE.get("tamers", []) if t.get("series")})
    return {
        "total": len(summary),
        "series": series_list,
        "items": summary,
        "skill_system": CACHE.get("tamer_skill_system", {}),
        "tamer_status": CACHE.get("tamer_status", {}),
    }


@app.get("/api/tamers/{ref}")
def get_tamer_detail(ref: str):
    tamers = CACHE.get("tamers", [])
    ref_norm = ref.strip()
    t = next(
        (
            x for x in tamers
            if x.get("slug") == ref_norm
            or x.get("name_th") == ref_norm
            or x.get("name_en") == ref_norm
            or (ref_norm.isdigit() and x["id"] == int(ref_norm))
        ),
        None,
    )
    if not t:
        raise HTTPException(status_code=404, detail="Tamer not found")
    return {
        "tamer": t,
        "skill_system": CACHE.get("tamer_skill_system", {}),
    }


@app.get("/api/dungeons")
def get_dungeons(q: Optional[str] = Query(None), dtype: Optional[str] = Query(None)):
    results = CACHE["dungeons"]
    if q:
        q_l = q.lower().strip()
        results = [d for d in results if q_l in json.dumps(d, ensure_ascii=False).lower()]
    if dtype and dtype != "all":
        results = [d for d in results if d.get("tier") == dtype]
    return {"total": len(results), "items": results}

@app.get("/api/crafts")
def get_crafts(q: Optional[str] = Query(None), npc: Optional[str] = Query(None)):
    results = CACHE["crafts"]
    if q:
        q_l = q.lower().strip()
        results = [c for c in results if q_l in c["item"].lower() or q_l in c["materials"].lower()]
    if npc and npc != "all":
        results = [c for c in results if npc.lower() in c["npc"].lower()]
    return {"total": len(results), "items": results}

@app.get("/api/currency")
def calculate_currency(
    tera: Optional[float] = Query(None),
    thb: Optional[float] = Query(None),
    rate: float = Query(0.55, description="THB per 1 Tera (default 0.55)")
):
    if rate <= 0:
        rate = 0.55
    if tera is not None:
        thb_val = tera * rate
        return {
            "rate": rate,
            "tera": tera,
            "thb": round(thb_val, 2),
            "mega": round(tera * 10000, 2),
            "bit": round(tera * 100000000, 0)
        }
    elif thb is not None:
        tera_val = thb / rate
        return {
            "rate": rate,
            "thb": thb,
            "tera": round(tera_val, 4),
            "mega": round(tera_val * 10000, 2),
            "bit": round(tera_val * 100000000, 0)
        }
    return {"rate": rate, "message": "Specify ?tera= or ?thb="}

if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

if MODELS_DIR.exists():
    app.mount("/models", StaticFiles(directory=str(MODELS_DIR)), name="models")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/favicon.ico")
def get_favicon():
    fav = STATIC_DIR / "favicon.ico"
    if fav.exists():
        return FileResponse(fav, media_type="image/x-icon")
    raise HTTPException(status_code=404, detail="Favicon not found")

def _render_index_html(status_code: int = 200):
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        # Version the JS/CSS URLs by file mtime so browsers never run a stale cached copy
        html = index_file.read_text(encoding="utf-8")
        for name in ("app.js", "style.css"):
            v = int((STATIC_DIR / name).stat().st_mtime)
            html = re.sub(rf'/static/{re.escape(name)}(\?v=[^"]*)?"', f'/static/{name}?v={v}"', html)
        return HTMLResponse(html, status_code=status_code, headers={"Cache-Control": "no-cache"})
    return HTMLResponse("Digimon Thai Wiki API Online.", status_code=status_code)


@app.get("/")
@app.get("/home")
@app.get("/home/{rest:path}")
@app.get("/digimon")
@app.get("/digimon/{rest:path}")
@app.get("/tamers")
@app.get("/tamer/{rest:path}")
@app.get("/tamer-status")
@app.get("/tamer-equip")
@app.get("/dungeons")
@app.get("/dungeon/{rest:path}")
@app.get("/patches")
@app.get("/patch/{rest:path}")
@app.get("/currency")
@app.get("/eggs")
@app.get("/egg/{rest:path}")
@app.get("/jogress")
@app.get("/jogress/{rest:path}")
@app.get("/decks")
@app.get("/decks/{rest:path}")
@app.get("/seals")
@app.get("/seal/{rest:path}")
@app.get("/dunits")
@app.get("/dunits/{rest:path}")
def spa_routes(rest: str = ""):
    return _render_index_html(200)


@app.get("/{full_path:path}")
def spa_not_found(full_path: str):
    if full_path.startswith("api/") or full_path == "api":
        raise HTTPException(status_code=404, detail="API endpoint not found")
    return _render_index_html(404)

@app.on_event("startup")
def on_startup():
    if not CACHE["digimon"]:
        build_cache()
    start_patch_sync_worker()

if __name__ == "__main__":
    build_cache()
    print("\n=======================================================")
    print(" [DMO WIKI] DIGIMON THAI WIKI SERVER IS RUNNING!")
    print(" [DMO WIKI] URL: http://localhost:8001")
    print(" [DMO WIKI] Ready for Mobile & Desktop (100% Offline Capable)")
    print("=======================================================\n")
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
