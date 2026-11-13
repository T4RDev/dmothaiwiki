"""Apply Thai-server patch-note data (web/thai_patch_data.json, made by thai_patch.py) to the wiki profiles.

Matching Thai names -> Digimon: dex Thai name, karaoke vocab, then web/thai_name_map.json (manual, Thai -> English title).
Newest patch wins. Hand-made web/skill_overrides.json is applied after this, so it always has the last word.
"""
import json
import re
from pathlib import Path

from dex_builder import awaken_th

HERE = Path(__file__).resolve().parent


def tnorm(s):
    s = (s or "").replace("ฺ", "").replace("์", "")  # thanthakhat varies between sources
    return re.sub(r"[\s\-–:()\[\]·.,'\"]+", "", s).lower()


class ThaiPatch:
    def __init__(self, dex):
        self.dex = dex
        p = HERE / "thai_patch_data.json"
        self.articles = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
        mp = HERE / "thai_name_map.json"
        manual = {k: v for k, v in json.loads(mp.read_text(encoding="utf-8")).items() if not k.startswith("_")} \
            if mp.exists() else {}
        # Thai name -> dex entry
        self.by_th = {}
        names = dex.vocab.get("names", {}) if hasattr(dex, "vocab") else {}
        for d in dex.digimon:
            for t in (d.get("thai_name"), names.get(d["title"])):
                if t:
                    self.by_th.setdefault(tnorm(t), d)
        for th, en in manual.items():
            d = dex.by_key.get(re.sub(r"[^a-z0-9]", "", en.lower()))
            if d:
                self.by_th[tnorm(th)] = d
        self.unmatched = set()
        # merge all articles (oldest -> newest): latest block per Digimon wins
        self.digimon, self.ride, self.unlock = {}, {}, {}
        for a in self.articles:
            for dg in a.get("digimon", []):
                # section headers that list several Digimon carry no skills/stats -> nothing to apply
                if not dg.get("skills") and not dg.get("stats"):
                    continue
                d = self.find(dg["name_th"])
                if not d:
                    self.unmatched.add(dg["name_th"])
                    continue
                prev = self.digimon.get(d["slug"], {})
                merged = {**prev, **{k: v for k, v in dg.items() if v}}
                merged["source"] = {"title": a["title"], "url": a["url"], "date": a.get("date_iso", "")}
                self.digimon[d["slug"]] = merged
            for r in a.get("ride", []):
                d = self.find(r["digimon_th"])
                if d:
                    self.ride[d["slug"]] = r["item_th"]
                else:
                    self.unmatched.add(r["digimon_th"])
            for u in a.get("unlock", []):
                d = self.find(u["digimon_th"])
                if d:
                    self.unlock[d["slug"]] = u["item_th"]
                else:
                    self.unmatched.add(u["digimon_th"])

    def find(self, th):
        k = tnorm(th)
        if k in self.by_th:
            return self.by_th[k]
        # "ดันเดวีมอน" vs "ดันเดวิมอน": compare without vowel length / tone marks
        loose = lambda s: re.sub(r"[่้๊๋ีืูัิุึ]", "", s)
        lk = loose(k)
        hits = [d for t, d in self.by_th.items() if loose(t) == lk]
        return hits[0] if len(hits) == 1 else None

    def apply(self, p):
        """Mutates a public profile (after extract_combat) with Thai-server data."""
        slug = p["slug"]
        dg = self.digimon.get(slug)
        if dg:
            # "[อะเวคเค่น] วอร์เกรย์มอน" -> "วอร์เกรย์มอน (อะเวคเค่น)"
            nm = re.sub(r"^\[(.+?)\]\s*(.+)$", r"\2 (\1)", dg["name_th"]).strip()
            nm = awaken_th(nm)
            if "(awaken)" in p["title"].lower() and "ชิน" not in nm:  # note gave the plain name of the Awaken form
                nm += " (ชิน)"
            p["thai_name"] = nm
            p["thai_name_unofficial"] = False
            p["thai_source"] = dg.get("source")
            props = dg.get("props", {})
            if props.get("rank") and re.fullmatch(r"[A-Z+]{1,4}", props["rank"]):
                p["rank"] = props["rank"]
            # base stats from the Thai notes (Lv.1 / 100% size)
            for k, v in (dg.get("stats") or {}).items():
                st = p.get("stats", {}).get(k)
                if isinstance(st, dict):
                    st["base"] = f"{v:,}".replace(",", "") if isinstance(v, int) else str(v)
                    st["base_th_server"] = True
            skills = dg.get("skills") or []
            for i, sk in enumerate(skills):
                if i < len(p.get("skills", [])):
                    s = p["skills"][i]
                else:  # Digimon / skill not on dmowiki yet
                    s = {"name": sk["name_th"], "element": "", "cooldown": "", "ds_consumed": "", "upgrade_points": "",
                         "animation": "", "description": "", "levels": []}
                    p.setdefault("skills", []).append(s)
                s["name_th"] = sk["name_th"]
                desc = sk["description_th"]
                if sk.get("notes"):
                    desc += " (" + " ".join(sk["notes"]) + ")"
                s["description_th"] = desc
                wiki = [int(x) for x in s.get("levels", []) if re.fullmatch(r"\d+", str(x))]
                lv1 = sk["damage"]
                if len(wiki) >= 2:
                    steps = [b - a for a, b in zip(wiki, wiki[1:])]
                    lv = [lv1]
                    for st in steps:
                        lv.append(lv[-1] + st)
                    s["levels"] = [str(x) for x in lv]
                else:
                    s["levels"] = [str(lv1)]
                s["th_server"] = True
        # the notes name one item per Digimon: only rename when the wiki also lists exactly one
        if slug in self.ride:
            items = p.get("ride_items") or []
            if len(items) == 1:
                items[0]["th"] = self.ride[slug]
            elif not items:
                p["ride_items"] = [{"name": self.ride[slug], "th": self.ride[slug], "icon": ""}]
        if slug in self.unlock:
            items = p.get("unlock_items") or []
            if len(items) == 1:
                items[0]["th"] = self.unlock[slug]
            elif not items:
                p["unlock_items"] = [{"name": self.unlock[slug], "th": self.unlock[slug], "icon": ""}]
