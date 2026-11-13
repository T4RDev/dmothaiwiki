"""Evolution unlock items straight from the Thai game client (web/thai_evo_unlock.json, made by thai_client_evo.py).

The client is the authority: it replaces dmowiki's (often outdated, e.g. "Evoluter x 6") unlock item with the
real Thai-server item, its official Thai name, amount and icon. Digimon the client unlocks by level only lose
the dmowiki item.
"""
import json
import re
from pathlib import Path

from thai_client_match import ClientMatcher

HERE = Path(__file__).resolve().parent


def clean_item_name(s):
    s = re.sub(r"\s*\[?กิจกรรม\]", "", (s or "").replace("ดิจิมอนใหม่", ""))
    s = re.sub(r"\s+", " ", s).strip()
    if s.count("(") > s.count(")"):  # the client has typos like "อิมพีเรียม วิชเชส(B"
        s += ")"
    return re.sub(r"\s+:", " :", s)


class ClientEvo:
    def __init__(self, dex):
        p = HERE / "thai_evo_unlock.json"
        self.records = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        m = ClientMatcher(dex)
        self.by_slug, self.unmatched = {}, []
        for cid, r in self.records.items():
            d = m.find(cid, r["name_th"])
            if not d:
                self.unmatched.append((cid, r["name_th"]))
                continue
            prev = self.by_slug.get(d["slug"])
            # several client slots can point at one wiki page (other evolution trees): keep the one with an item
            if prev is None or (not prev.get("item") and r.get("item")):
                self.by_slug[d["slug"]] = {**r, "client_id": int(cid)}

    _pics = None

    @classmethod
    def client_picture(cls, cid):
        """/images/client_digimon/<id>.png from the client's own Digimon picture (<7-digit id>_<name>l.png)."""
        if cls._pics is None:
            import thai_client_evo as E
            cls._pics = {}
            root = E.CRACK / "out_images" / "data" / "digimon"
            if root.exists():
                for f in root.glob("*/*.png"):
                    m = re.match(r"0(\d{6})_.*l\.png$", f.name, re.I)
                    if m:
                        cls._pics.setdefault(int(m.group(1)), f)
        src = cls._pics.get(int(cid))
        if not src:
            return ""
        out = HERE.parent / "output" / "images" / "client_digimon"
        out.mkdir(parents=True, exist_ok=True)
        dest = out / f"{int(cid)}.png"
        if not dest.exists():
            import shutil
            shutil.copyfile(src, dest)
        return f"/images/client_digimon/{int(cid)}.png"

    def apply(self, p):
        r = self.by_slug.get(p["slug"])
        if not r:
            return
        p["client_id"] = r["client_id"]
        if not p.get("icon") or not p.get("image"):  # dmowiki has no picture (e.g. Omegamon): use the client's
            pic = self.client_picture(r["client_id"])
            old = HERE.parent / "output" / "images" / f"{p['title']}(delete).png"
            if not p.get("image"):
                p["image"] = f"/images/{p['title']}(delete).png" if old.exists() else pic
            if not p.get("icon"):
                p["icon"] = pic or p.get("image", "")
        multi = [x for x in (r.get("items") or []) if x.get("item")]
        if len(multi) > 1:  # Jogress: one item from each partner's line
            out = []
            for x in multi:
                name = clean_item_name(x["item"]["name_th"])
                amt = x.get("amount") or 1
                out.append({"name": f"ฝั่ง{clean_item_name(x.get('parent_th', ''))}" if x.get("parent_th") else "",
                            "th": f"{name} × {amt}" if amt > 1 else name, "icon": x["item"].get("icon", ""),
                            "qty": amt, "client_item_id": x["item"].get("id"), "source": "thai_client"})
            p["unlock_items"] = out
            if r.get("unlock_level"):
                p["unlock_level"] = str(r["unlock_level"])
            return
        it = r.get("item")
        if it:
            name = clean_item_name(it["name_th"])
            amt = r.get("amount") or 1
            label = f"{name} × {amt}" if amt > 1 else name
            wiki = (p.get("unlock_items") or [{}])[0].get("name", "") if p.get("unlock_items") else ""
            same_as_wiki = bool(wiki) and "อีโวลูเตอร์" in name and wiki.lower().startswith("evoluter")
            p["unlock_items"] = [{"name": wiki if same_as_wiki else "", "th": label, "icon": it.get("icon", ""),
                                  "qty": amt, "client_item_id": it.get("id"), "source": "thai_client"}]
            if r.get("unlock_level"):
                p["unlock_level"] = str(r["unlock_level"])
        else:
            p["unlock_items"] = []
