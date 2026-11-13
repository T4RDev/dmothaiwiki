"""Digimon Archive decks of the Thai server, read from the (already decrypted) client in CrackDMO.

dbookcompositiondata.bin : u32 count | per deck: u32 deck id, u32 n, n * (u32 base Digimon, u16 slot, u32 form)
                           a member = "the Digimon line <base> with evolution slot <slot> opened" (= <form>)
dbookdeckdata.bin        : u32 count | per deck: u32 deck id, u32 n, n * 16 bytes
                           (u16 trigger, u16 on, u16 option, u16 value, i32 chance x100, i32 seconds)
                           trigger 1 = always, 2 = chance (instant), 3 = chance (timed buff); on 1 = normal attack, 2 = skill
dbookdeck_str / dbookopt_str : Thai deck names + descriptions / option names
"""
import json
import re
import struct

TRIGGER_ON = {1: "เมื่อโจมตีธรรมดา", 2: "เมื่อใช้สกิล"}
OPT_ICON = {
    1: "/images/AT.png",
    2: "/images/DS.png",
    3: "/images/CT.png",
    4: "/images/AS.png",
    5: "/images/HP.png",
    6: "/images/AS.png",
    7: "/images/HT.png",
    8: "/images/AT.png",
    9: "/images/Fire.png",
    10: "/images/AT.png",
    11: "/images/AT.png",
}


def _clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("ดิจิมอนใหม่", "")).strip()


def _read(path, entry, size):
    b = path.read_bytes()
    n, o, out = struct.unpack_from("<i", b, 0)[0], 4, {}
    for _ in range(n):
        did, k = struct.unpack_from("<ii", b, o)
        o += 8
        out[did] = [struct.unpack_from(entry, b, o + i * size) for i in range(k)]
        o += k * size
    if o != len(b):
        raise ValueError(f"{path.name}: parsed {o} of {len(b)} bytes")
    return out


def build(dex, profiles):
    import thai_client_evo as E
    from thai_client_match import ClientMatcher
    tdir = E.CRACK / "out_decrypted" / "data" / "bin" / "table"
    lang = E.CRACK / "out_json" / "language"
    if not (tdir / "dbookdeckdata.bin").exists():
        return []
    comp = _read(tdir / "dbookcompositiondata.bin", "<iHi", 10)
    effs = _read(tdir / "dbookdeckdata.bin", "<HHHHii", 16)
    deck_str = {x["id"]: x["fields"] for x in json.loads((lang / "dbookdeck_str.json").read_text(encoding="utf-8"))}
    opt_str = {x["id"]: x["fields"] for x in json.loads((lang / "dbookopt_str.json").read_text(encoding="utf-8"))}
    names = E.digimon_names()
    matcher = ClientMatcher(dex)
    by_slug = {p["slug"]: p for p in profiles}

    def digi(cid):
        d = matcher.find(cid, names.get(cid, ""))
        p = by_slug.get(d["slug"]) if d else None
        if p:
            return {"slug": p["slug"], "title": p["title"], "name": p.get("thai_name") or p["title"],
                    "icon": p.get("icon") or p.get("image", ""), "rank": p.get("rank", ""),
                    "rank_color": p.get("rank_color", ""), "form_th": p.get("form_th", "")}
        from thai_client_apply import ClientEvo
        return {"slug": "", "title": "", "name": _clean(names.get(cid, f"#{cid}")), "icon": ClientEvo.client_picture(cid),
                "rank": "", "rank_color": "", "form_th": ""}

    out = []
    for did in sorted(comp):
        title, desc = (deck_str.get(did) or ["", ""])[:2]
        title = _clean(title)
        if not comp[did] or not title or title.startswith("Title"):
            continue
        members, seen = [], set()
        for base, slot, form in comp[did]:
            m = digi(form)
            k = m["slug"] or m["name"]
            if k in seen:   # the same Digimon opened from another line counts once
                continue
            seen.add(k)
            m["line"] = _clean(names.get(base, ""))
            m["line_slug"] = digi(base)["slug"] if base != form else m["slug"]
            m["slot"] = slot
            members.append(m)
        effects = []
        for trig, on, opt, val, chance, sec in effs.get(did, []):
            o = opt_str.get(opt) or [f"ผล #{opt}", ""]
            e = {"option": opt, "icon": OPT_ICON.get(opt, "/images/AT.png"), "name": o[0], "desc": o[1],
                 "value": val, "always": trig == 1, "chance": chance / 100 if trig != 1 else 0,
                 "on": TRIGGER_ON.get(on, "") if trig != 1 else "", "seconds": sec}
            amount = "" if opt == 4 else f" +{val}%"
            if trig == 1:
                e["text"] = f"{o[0]}{amount} (ตลอดเวลา)"
            else:
                e["text"] = (f"{e['on']} มีโอกาส {e['chance']:g}% {o[0]}{amount}"
                             + (f" เป็นเวลา {sec} วินาที" if sec else ""))
            effects.append(e)
        out.append({"id": did, "name": title, "desc": _clean(desc), "members": members, "effects": effects,
                    "max_rank": max((by_slug[m["slug"]].get("rank_weight", 0) for m in members if m["slug"] in by_slug),
                                    default=0)})
    return out
