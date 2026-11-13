"""D-Unit (Digimon Unit / Union System) of the Thai DMO server.
Read directly from decrypted Thai client binary tables:
  dm_union-effect.bin       Collection effects (4 tiers per group)
  dm_union-group.bin        Digimon member mappings to D-Unit groups (positions 0..7)
  dm_union-hackinginfo.bin  Hacking kit requirements per Digimon rank
  dm_union-reward.bin       Master Tier thresholds & title rewards (Bronze -> Master)
  dm_union-filter_str.json  25 stat category names (Images 3, 4, 5)
  dm_union-group_str.json   235 Group Thai names
  skillcodeunion.json       Skill ID -> Filter ID & Buff value mapping
  skill_str.json            Buff effect text descriptions
"""
import json
import re
import struct
from pathlib import Path

CRACK = Path(r"C:\Users\T4R\Desktop\AllWorks\CrackDMO")

# 25 Filters categorized into 3 sections matching client UI (Images 3, 4, 5)
FILTER_SECTIONS = [
    {
        "id": "basic",
        "title": "สเตตัสพื้นฐาน",
        "icon": "/images/AT.png",
        "filter_ids": [3, 4, 12, 5, 6, 7, 15, 8, 17],
    },
    {
        "id": "scd_attr",
        "title": "SCD แยกตามประเภท",
        "icon": "/images/Vaccine.png",
        "filter_ids": [161, 162, 163, 164],
    },
    {
        "id": "scd_elem",
        "title": "SCD แยกตามธาตุ",
        "icon": "/images/Fire.png",
        "filter_ids": [24, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 160],
    },
]

# Title item buff stats & descriptions
TITLE_BUFFS = {
    1: {
        "buffs": "HP +700",
        "stats": [{"stat": "HP", "val": "+700"}],
        "desc": "ฉายาที่มอบให้กับเทมเมอร์ที่สำเร็จ D-ยูนิตระดับบรอนซ์",
    },
    2: {
        "buffs": "HP +1,000 / DS +1,500",
        "stats": [{"stat": "HP", "val": "+1,000"}, {"stat": "DS", "val": "+1,500"}],
        "desc": "ฉายาที่มอบให้กับเทมเมอร์ที่สำเร็จ D-ยูนิตระดับซิลเวอร์",
    },
    3: {
        "buffs": "HP +1,500 / EXP +700% / AT +300",
        "stats": [{"stat": "HP", "val": "+1,500"}, {"stat": "EXP", "val": "+700%"}, {"stat": "AT", "val": "+300"}],
        "desc": "ฉายาที่มอบให้กับเทมเมอร์ที่สำเร็จ D-ยูนิตระดับโกลด์",
    },
    4: {
        "buffs": "HP +2,500 / SKD +15% / HT +400",
        "stats": [{"stat": "HP", "val": "+2,500"}, {"stat": "SKD", "val": "+15%"}, {"stat": "HT", "val": "+400"}],
        "desc": "ฉายาที่มอบให้กับเทมเมอร์ที่สำเร็จ D-ยูนิตระดับแพลตตินัม",
    },
    5: {
        "buffs": "CT +600 / SKD +20% / HT +600",
        "stats": [{"stat": "CT", "val": "+600"}, {"stat": "SKD", "val": "+20%"}, {"stat": "HT", "val": "+600"}],
        "desc": "ฉายาที่มอบให้กับเทมเมอร์ที่สำเร็จ D-ยูนิตระดับไดมอนด์",
    },
    6: {
        "buffs": "CT +1,000 / SKD +25% / HT +1,000",
        "stats": [{"stat": "CT", "val": "+1,000"}, {"stat": "SKD", "val": "+25%"}, {"stat": "HT", "val": "+1,000"}],
        "desc": "ฉายาที่มอบให้กับเทมเมอร์ที่สำเร็จ D-ยูนิตระดับมาสเตอร์",
    },
}


def _clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("ดิจิมอนใหม่", "")).strip()


def build(dex, profiles):
    import thai_client_evo as E
    from thai_client_match import ClientMatcher

    tbl = CRACK / "out_decrypted" / "data" / "bin" / "table"
    lang = CRACK / "out_json" / "language"

    if not (tbl / "dm_union-effect.bin").exists():
        return {}

    def load_lang(name):
        p = lang / f"{name}.json"
        if not p.exists():
            return {}
        try:
            return {x["id"]: x.get("text") or x.get("fields", [""])[0] for x in json.loads(p.read_text(encoding="utf-8"))}
        except Exception:
            return {}

    filters_str = load_lang("dm_union-filter_str")
    rewards_str = load_lang("dm_union-reward_str")
    groups_str = load_lang("dm_union-group_str")
    dnames = load_lang("digimonname_str")
    items_str = load_lang("item_str")

    # Skillcodeunion: skill_id -> (filter_id, value)
    sc_p = CRACK / "out_json" / "table" / "skillcodeunion.json"
    skill_code_map = {}
    if sc_p.exists():
        try:
            sc_data = json.loads(sc_p.read_text(encoding="utf-8"))
            for r in sc_data.get("rows", []):
                sid = r[0]
                fid = r[3]
                val = r[5]
                skill_code_map[sid] = (fid, val)
        except Exception:
            pass

    # Skills descriptions (field 1 is the effect description e.g. "CT + 30")
    skills_p = lang / "skill_str.json"
    skills_str = {}
    if skills_p.exists():
        try:
            skills_str = {
                x["id"]: x.get("fields", ["", ""])[1] if len(x.get("fields", [])) > 1 else ""
                for x in json.loads(skills_p.read_text(encoding="utf-8"))
            }
        except Exception:
            pass

    matcher = ClientMatcher(dex)
    by_slug = {p["slug"]: p for p in profiles}
    all_icons = getattr(dex, "_all_tree_icons", {})

    # 1. devolutionlist for resolving (parent, slot) -> evolved digimon_id
    lines = E.parse_lines(set(dnames))
    slot_to_did = {}
    for ln in lines:
        slot_to_did[(ln["parent"], ln["slot"])] = ln["type"]

    # 2. Hacking info: digimon_id -> required hacking kit
    hack_p = CRACK / "out_json" / "table" / "dm_union-hackinginfo.json"
    hack_map = {}
    its_all = E.items()
    if hack_p.exists():
        try:
            for r in json.loads(hack_p.read_text(encoding="utf-8")).get("rows", []):
                did, ev_item, item_id, needed, f4, min_lvl = r
                if item_id != 0:
                    it_info = its_all.get(item_id)
                    icon_id = it_info.get("icon_id") if it_info else None
                    E.save_icon(item_id, icon_id)
                    hack_map[did] = {
                        "kit_id": item_id,
                        "kit_name": items_str.get(item_id, "D-ยูนิตแฮกกิ้ง คิท"),
                        "kit_icon": f"/images/client_items/{item_id}.png",
                        "needed": needed,
                        "min_level": min_lvl,
                    }
        except Exception:
            pass

    # 3. Master Tiers from dm_union-reward.bin + title buffs
    tiers = []
    rw_p = CRACK / "out_json" / "table" / "dm_union-reward.json"
    if rw_p.exists():
        try:
            for r in json.loads(rw_p.read_text(encoding="utf-8")).get("rows", []):
                tier_id, req_units, item_id, amount = r
                if tier_id == 0:
                    continue
                tier_name = rewards_str.get(tier_id, f"ระดับ {tier_id}")
                title_reward = items_str.get(item_id, f"[ฉายา] ระดับ {tier_id}")
                tb_info = TITLE_BUFFS.get(tier_id, {})
                tiers.append({
                    "tier_id": tier_id,
                    "tier_name": tier_name,
                    "req_units": req_units,
                    "reward_item_id": item_id,
                    "reward_item_icon": f"/images/client_items/{item_id}.png",
                    "title_reward": title_reward,
                    "amount": amount,
                    "buffs": tb_info.get("buffs", ""),
                    "stats": tb_info.get("stats", []),
                    "desc": tb_info.get("desc", ""),
                })
        except Exception:
            pass

    # 4. Group members from dm_union-group.bin
    b_group = (tbl / "dm_union-group.bin").read_bytes()
    count_group = struct.unpack_from("<i", b_group, 0)[0]
    off = 4
    group_members = {}
    for _ in range(count_group):
        d_id, num_slots = struct.unpack_from("<2i", b_group, off)
        off += 8
        for _ in range(num_slots):
            slot_idx, num_groups = struct.unpack_from("<2i", b_group, off)
            off += 8
            for _ in range(num_groups):
                gid, gval = struct.unpack_from("<2i", b_group, off)
                off += 8
                member_did = d_id if slot_idx == 1 else slot_to_did.get((d_id, slot_idx), d_id)
                group_members.setdefault(gid, []).append((gval, d_id, slot_idx, member_did))

    # Helper to resolve member profile
    def resolve_member(m_info):
        gval, base_id, slot_idx, member_did = m_info
        member_name = _clean(dnames.get(member_did, f"#{member_did}"))
        base_name = _clean(dnames.get(base_id, f"#{base_id}"))

        d = matcher.find(member_did, member_name)
        p = by_slug.get(d["slug"]) if d else None

        icon = ""
        slug = ""
        title = ""
        rank = ""
        rank_color = ""
        form_th = ""

        if p:
            slug = p["slug"]
            title = p["title"]
            member_name = p.get("thai_name") or member_name
            icon = p.get("icon") or all_icons.get(slug) or p.get("image", "")
            rank = p.get("rank", "")
            rank_color = p.get("rank_color", "")
            form_th = p.get("form_th", "")

        from thai_client_apply import ClientEvo
        if not icon:
            icon = ClientEvo.client_picture(member_did)

        hack = hack_map.get(member_did)
        if not rank and hack:
            m = re.search(r"คิท\s+([A-Za-z+]+)", hack["kit_name"])
            if m:
                rank = m.group(1)

        return {
            "pos": gval,
            "digimon_id": member_did,
            "name": member_name,
            "title": title,
            "slug": slug,
            "icon": icon,
            "rank": rank or "N",
            "rank_color": rank_color or "#94a3b8",
            "form_th": form_th or "ร่างทั่วไป",
            "base_id": base_id,
            "base_name": base_name,
            "slot": slot_idx,
            "hacking": hack,
            "max_level": 180,  # Official Thai server client level cap is Lv. 180 (from digimonexp.bin)
        }

    # 5. Parse dm_union-effect.bin (4 collection tiers per group)
    b_eff = (tbl / "dm_union-effect.bin").read_bytes()
    count_eff = struct.unpack_from("<i", b_eff, 0)[0]
    rec_size = (len(b_eff) - 4) // count_eff

    groups_out = []
    filter_counts = {fid: 0 for fid in filters_str}

    for i in range(count_eff):
        row = struct.unpack_from("<14i", b_eff, 4 + i * rec_size)
        gid = row[0]
        gname = _clean(groups_str.get(gid, "กลุ่ม D-ยูนิต"))
        target_members = row[1]

        tiers_list = []
        g_filter_ids = set()

        for t_idx, offset in enumerate([2, 5, 8, 11]):
            ctype = row[offset]
            cval = row[offset + 1]
            sid = row[offset + 2]
            fid, sval = skill_code_map.get(sid, (0, 0))
            stext = skills_str.get(sid, "")
            fname = filters_str.get(fid, "")
            if fid:
                g_filter_ids.add(fid)

            # Condition description exactly matching Image 1
            if ctype == 2:
                cond_desc = f"เมื่อมีครบ {cval} ตัว"
            elif ctype == 1:
                cond_desc = f"เมื่อเลเวลรวมของดิจิมอนถึง {cval}"
            elif ctype == 3:
                cond_desc = f"เมื่อมีดิจิมอนที่ก้าวข้ามขีดจำกัดครบ {cval} ตัว"
            else:
                cond_desc = f"เงื่อนไขขั้นที่ {t_idx + 1} ({cval})"

            tiers_list.append({
                "tier": t_idx + 1,
                "cond_type": ctype,
                "cond_val": cval,
                "cond_desc": cond_desc,
                "skill_id": sid,
                "buff_text": stext,
                "filter_id": fid,
                "filter_name": fname,
                "stat_val": sval,
            })

        for fid in g_filter_ids:
            if fid in filter_counts:
                filter_counts[fid] += 1

        raw_mems = group_members.get(gid, [])
        # Deduplicate members by slug / digimon_id: each Digimon only appears once per group
        seen_keys = set()
        mems = []
        for m_info in sorted(raw_mems, key=lambda x: x[0]):
            res_m = resolve_member(m_info)
            dedup_key = res_m["slug"] if res_m["slug"] else res_m["digimon_id"]
            if dedup_key not in seen_keys:
                seen_keys.add(dedup_key)
                mems.append(res_m)

        # Build cards array: show only actual unique members without empty placeholder slots
        cards = list(mems)

        # In Thai client (e.g. Mode with 11 members: 11 * 180 = 1980), max cumulative level is members * 180
        max_cum_level = len(mems) * 180

        groups_out.append({
            "id": gid,
            "name": gname,
            "target_members": target_members,
            "member_count": len(mems),
            "max_cum_level": max_cum_level,
            "filter_ids": sorted(g_filter_ids),
            "tiers": tiers_list,
            "members": mems,
            "cards": cards,
        })

    # Prepare structured filter categories with group counts
    sections_out = []
    for sec in FILTER_SECTIONS:
        sec_filters = []
        for fid in sec["filter_ids"]:
            fname = filters_str.get(fid, f"Filter #{fid}")
            cnt = filter_counts.get(fid, 0)
            sec_filters.append({
                "id": fid,
                "name": fname,
                "count": cnt,
            })
        sections_out.append({
            "id": sec["id"],
            "title": sec["title"],
            "icon": sec["icon"],
            "filters": sec_filters,
        })

    total_hackable = sum(1 for g in groups_out for m in g["members"] if m.get("hacking"))

    return {
        "groups": groups_out,
        "master_tiers": tiers,
        "filter_sections": sections_out,
        "filters": sections_out,
        "all_filters": [
            {"id": fid, "name": filters_str.get(fid, ""), "count": filter_counts.get(fid, 0)}
            for fid in sorted(filters_str.keys())
        ],
        "total_groups": len(groups_out),
        "total_members": sum(len(g["members"]) for g in groups_out),
        "total_hackable_forms": total_hackable,
    }
