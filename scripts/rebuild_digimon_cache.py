# -*- coding: utf-8 -*-
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
OUTPUT = ROOT / "output"
DB_PATH = OUTPUT / "dmowiki.db"
IMAGES_DIR = OUTPUT / "images"

if str(WEB) not in sys.path:
    sys.path.insert(0, str(WEB))

import server

def main():
    print("[REBUILD] Running full Digimon profile build...")
    server.DB_PATH = DB_PATH
    server.IMAGES_DIR = IMAGES_DIR
    server.build_image_index()

    conn = server.get_db()
    c = conn.cursor()

    dex = server.Dex(DB_PATH, IMAGES_DIR)
    dex.build()

    aoe_table = {}
    row = c.execute("SELECT data_json FROM pages WHERE slug='Area_of_Effect_Skills'").fetchone()
    if row:
        for tb in json.loads(row[0]).get("tables", []):
            if "Effective Area" in tb.get("headers", []) and "Digimon" in tb.get("headers", []):
                aoe_table = server.load_aoe_table(tb["rows"])

    aoe_overrides = {}
    ov_path = WEB / "aoe_overrides.json"
    if ov_path.exists():
        aoe_overrides = {k: v for k, v in json.loads(ov_path.read_text(encoding="utf-8")).items() if not k.startswith("_")}

    skill_overrides = {}
    sk_path = WEB / "skill_overrides.json"
    if sk_path.exists():
        try:
            skill_overrides = {k: v for k, v in json.loads(sk_path.read_text(encoding="utf-8")).items() if not k.startswith("_")}
        except Exception as e:
            print("[WARN] skill_overrides failed:", e)

    evo_unlocks = {}
    eu_path = WEB / "evolution_unlocks.json"
    if eu_path.exists():
        try:
            evo_unlocks = json.loads(eu_path.read_text(encoding="utf-8"))
        except Exception as e:
            print("[WARN] evo_unlocks failed:", e)

    thai_patch = server.ThaiPatch(dex)
    client_evo = server.ClientEvo(dex)

    digimon_list = []
    for d in dex.digimon:
        p = dex.public(d)
        p.update(server.extract_combat(d["_data"]))
        for s in p["skills"]:
            s["name_th"] = dex.i18n_skills.get(s["name"], "")
            s["description_th"] = dex.text_th(s["description"])
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
        if client_evo:
            client_evo.apply(p)
        p["passives_th"] = [dex.text_th(x) or x for x in p["passives"]] if any(dex.text_th(x) for x in p["passives"]) else []
        p["lore_th"] = dex.text_th(p["lore"])
        p.update(server.parse_effects(d["_data"].get("text", "")))
        if not p["rank_passives"] and p["passives"]:
            cur, lab = None, None
            for x in p["passives"]:
                x = x.strip()
                if x.endswith(":") and not x.startswith(":"):
                    cur = None
                    if x[:-1].strip() in server.EFFECT_GROUPS:
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
        aoe = server.parse_aoe(d["_data"].get("text", ""), p["skills"], p["skill_effects"], aoe_table, p["title"])
        ov = aoe_overrides.get(p["title"]) or {}
        for slot, info in (ov.get("add") or {}).items():
            aoe[int(slot)] = {"shape": info.get("shape", ""), "size": info.get("size", ""), "thai": True}
        for slot in ov.get("remove") or []:
            aoe.pop(int(slot), None)
        for i, s in enumerate(p["skills"], 1):
            s["aoe"] = aoe.get(i)
        p["aoe_slots"] = sorted(aoe)
        digimon_list.append(p)

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

    def auto_th(s):
        import re
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

    rank_table_th = {r: {g: [th_field(f) for f in fs] for g, fs in gs.items()} for r, gs in rank_table.items()}

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

    digimon_in_thai = [d for d in digimon_list if d.get("in_thai", True)]
    not_in_thai = sorted(d["title"] for d in digimon_list if not d.get("in_thai", True))

    cache_payload = {
        "digimon": digimon_in_thai,
        "not_in_thai": not_in_thai,
        "rank_table_th": rank_table_th,
        "stats": {
            "total_digimon": len(digimon_in_thai),
            "not_in_thai": len(not_in_thai),
            "total_pages": 1000,
            "total_images": len(server.CACHE.get("image_lookup", {}))
        }
    }

    cache_file = WEB / "digimon_cache.json"
    cache_file.write_text(json.dumps(cache_payload, ensure_ascii=False), encoding="utf-8")
    print(f"[SUCCESS] WROTE digimon_cache.json successfully! in_thai: {len(digimon_in_thai)}, not_in_thai: {len(not_in_thai)}")

if __name__ == "__main__":
    main()
