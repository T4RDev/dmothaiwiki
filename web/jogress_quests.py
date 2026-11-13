"""Jogress quest lines (web/thai_jogress_quests.json from thai_client_quest.py) grouped per Jogress Digimon.

Every group is split into one "side" per partner Digimon (the quests that require that partner, plus the
quests that follow on from them), so a two-partner Jogress shows two separate step lists. Quests that come
after both sides (or before either) are "shared" and appear in every side, flagged.
"""
import heapq
import json
import re
from pathlib import Path

from thai_client_match import ClientMatcher

HERE = Path(__file__).resolve().parent
SHARED = "shared"


def _topo(qs):
    """order quests along their "previous quest" links (ties: by id)"""
    ids = {q["id"] for q in qs}
    by_id = {q["id"]: q for q in qs}
    indeg = {q["id"]: sum(1 for p in q["prev"] if p in ids) for q in qs}
    nxt = {}
    for q in qs:
        for p in q["prev"]:
            if p in ids:
                nxt.setdefault(p, []).append(q["id"])
    heap = [i for i, n in indeg.items() if n == 0]
    heapq.heapify(heap)
    out = []
    while heap:
        i = heapq.heappop(heap)
        out.append(by_id[i])
        for j in nxt.get(i, []):
            indeg[j] -= 1
            if indeg[j] == 0:
                heapq.heappush(heap, j)
    seen = {q["id"] for q in out}
    return out + sorted((q for q in qs if q["id"] not in seen), key=lambda q: q["id"])


def _sides(qs):
    """quest id -> side key (partner client id, or SHARED)"""
    order = _topo(qs)
    side = {}
    for q in order:
        own = {d["client_id"] for d in q["need_digimon"]}
        if len(own) == 1:
            side[q["id"]] = next(iter(own))
            continue
        if len(own) > 1:
            side[q["id"]] = SHARED
            continue
        ps = {side.get(p) for p in q["prev"] if p in side} - {None}
        side[q["id"]] = next(iter(ps)) if len(ps) == 1 else (SHARED if ps else None)
    # quests at the start of a line with no requirement: take the side of what follows them
    for q in reversed(order):
        if side[q["id"]] is None:
            after = {side[x["id"]] for x in order if q["id"] in x["prev"]} - {None}
            side[q["id"]] = next(iter(after)) if len(after) == 1 else SHARED
    return order, side


def _rewards(qs):
    out = {}
    for q in qs:
        for w in q["rewards"]:
            if w["kind"] == "item":
                it = w["item"]
                r = out.setdefault(it["id"], {**it, "count": 0, "unlock": bool(it.get("unlocks"))})
                r["count"] = max(r["count"], it.get("count") or 1)
    return sorted(out.values(), key=lambda r: (not r["unlock"], r["name_th"]))


def build_groups(dex, profiles):
    p = HERE / "thai_jogress_quests.json"
    if not p.exists():
        return []
    lines = json.loads(p.read_text(encoding="utf-8"))
    rules = json.loads((HERE / "jogress_quest_map.json").read_text(encoding="utf-8")).get("rules", [])
    by_slug = {x["slug"]: x for x in profiles}
    matcher = ClientMatcher(dex)
    import thai_client_evo
    names = thai_client_evo.digimon_names()
    cache = {}

    def link(cid, name):
        if cid not in cache:
            d = matcher.find(cid, name) if cid else None
            if d and d["slug"] in by_slug:
                q = by_slug[d["slug"]]
                cache[cid] = {"slug": q["slug"], "name": q.get("thai_name") or q["title"], "icon": q.get("icon", "")}
            else:
                cache[cid] = {"slug": "", "name": re.sub(r"\s+", " ", name or "").strip(), "icon": ""}
        return {**cache[cid], "client_id": cid}

    groups = {}
    for ln in lines:
        target = next((t for rx, t in rules if re.search(rx, ln["line"]) or re.search(rx, ln.get("named", ""))), None)
        d = dex.by_key.get(re.sub(r"[^a-z0-9]", "", (target or "").lower())) if target else None
        slugs = [d["slug"]] if d and d["slug"] in by_slug else []
        if not slugs:  # lines found through the unlock items they reward
            for cid in ln.get("targets") or []:
                m = matcher.find(cid, names.get(cid, ""))
                if m and m["slug"] in by_slug and m["slug"] not in slugs:
                    slugs.append(m["slug"])
        if not slugs:
            continue
        for q in ln["quests"]:
            q["line"] = ln["line"]
            q["need_digimon"] = [link(x["client_id"], x["name_th"]) for x in q["need_digimon"]]
            q["need_form"] = [{**link(f["client_id"], f["name_th"]), "slot": f["slot"]} for f in q.get("need_form", [])]
            q["opens"] = [link(o["client_id"], o["name_th"]) for o in q.get("opens", [])]
        for sl in slugs:
            g = groups.setdefault(sl, {"slug": sl, "quests": {}})
            for q in ln["quests"]:
                g["quests"].setdefault(q["id"], q)

    out = []
    for slug, g in groups.items():
        prof = by_slug[slug]
        qs = list(g["quests"].values())
        order, side = _sides(qs)
        keys = []
        for q in order:
            k = side[q["id"]]
            if k != SHARED and k not in keys:
                keys.append(k)
        sides = []
        for k in keys or [SHARED]:
            steps = [{**q, "shared": side[q["id"]] == SHARED and bool(keys)} for q in order
                     if side[q["id"]] in (k, SHARED)]
            partner = next((d for q in steps for d in q["need_digimon"] if d["client_id"] == k), None) if keys else None
            form = next((f for q in steps for f in q["need_form"]
                         if partner and any(d["client_id"] == k for d in q["need_digimon"])), None)
            opens = []
            for q in steps:
                for o in q["opens"]:
                    if o["name"] not in [x["name"] for x in opens]:
                        opens.append(o)
            sides.append({
                "key": str(k), "partner": partner, "form": form, "opens": opens, "quests": steps,
                "quest_count": len(steps),
                "max_tamer_level": max((q["tamer_level"] for q in steps), default=0),
                "max_digimon_level": max((q["digimon_level"] for q in steps), default=0),
                "reward_items": _rewards(steps),
            })
        # two partner variants with the same Thai name (e.g. two "กาบูมอน" ids): number them
        seen = {}
        for s in sides:
            if s["partner"]:
                n = s["partner"]["name"]
                seen[n] = seen.get(n, 0) + 1
                if seen[n] > 1:
                    s["variant"] = seen[n]
        rewards = _rewards(qs)
        out.append({
            "slug": slug, "title": prof["title"], "thai_name": prof.get("thai_name") or prof["title"],
            "icon": prof.get("icon", ""), "image": prof.get("image", ""), "rank": prof.get("rank", ""),
            "rank_color": prof.get("rank_color", ""), "rank_icon": prof.get("rank_icon", ""),
            "rank_weight": prof.get("rank_weight") or 0,
            "partners": [s["partner"] for s in sides if s["partner"]],
            "sides": sides,
            "quest_count": len(qs),
            "unlocks_by_quest": any(q["opens"] for q in qs),
            "max_tamer_level": max((q["tamer_level"] for q in qs), default=0),
            "max_digimon_level": max((q["digimon_level"] for q in qs), default=0),
            "reward_items": rewards,
            "unlock_from_quest": [r for r in rewards if r["unlock"]],
        })
    out.sort(key=lambda x: x["thai_name"])
    return out
