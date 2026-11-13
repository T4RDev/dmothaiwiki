"""
Builds the Digimon dex (profiles + per-page evolution trees) from output/dmowiki.db.

The scraper stored each page as plain text + text-only tables + an ordered list of
image URLs. Icons (rank, attribute, element, items, evolution nodes) only survive in
that image list, so we match them back to infobox values by normalized name.

Evolution trees: every Digimon page on dmowiki shows the evolution tree of its line.
The "<Name>_Icon.png" images in the page's image list are exactly the nodes of that
tree. Edges come from each node's own "Digivolved from:" field, restricted to nodes
of the same tree.
"""
import json
import re
import sqlite3
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional

RANK_ORDER = ["U+", "U", "SSS+", "SSS", "SS+", "SS", "S+", "S", "A+", "A", "N"]
RANK_WEIGHTS = {r: len(RANK_ORDER) - i for i, r in enumerate(RANK_ORDER)}
RANK_COLORS = {
    "U+": "#e11d48", "U": "#f43f5e", "SSS+": "#ea580c", "SSS": "#f59e0b",
    "SS+": "#8b5cf6", "SS": "#06b6d4", "S+": "#10b981", "S": "#22c55e",
    "A+": "#3b82f6", "A": "#64748b", "N": "#94a3b8",
}

INFOBOX_LABELS = [
    "Rank:", "Unlocked at level:", "Unlocked with item:", "Unlocked with item 2:",
    "Unlocked with item 3:", "Unlocked with item 4:", "Unlocked with:", "Rideable with item:", "Form:", "Attribute:",
    "Elemental Attribute:", "Attacker Type:", "Type:", "Families:", "Family:",
    "Digivolved from:", "Digivolves to:", "Required to evolve:", "Data needed / amount:",
    "Location:", "See also:", "Note:", "Available:",
]
EVO_PREFIXES = {"Jogress"}
# Raid bosses / enemies / NPC copies share the infobox template but aren't playable
NON_PLAYABLE = re.compile(r"\((Raid|Enemy|NPC|Weakened|The Ruler of)", re.I)
ATTACKER_TYPES = ["Short Attacker", "Near Attacker", "Quick Attacker", "Defender"]

THAI = {
    "Vaccine": "วัคซีน", "Virus": "ไวรัส", "Data": "ดาต้า", "Unknown": "อันโนว์น", "Free": "ฟรี",
    "Fire": "ไฟ", "Water": "น้ำ", "Ice": "น้ำแข็ง", "Wind": "ลม", "Thunder": "สายฟ้า",
    "Land": "ดิน", "Earth": "ดิน", "Light": "แสง", "Darkness": "ความมืด", "Pitch Black": "ความมืดมิด",
    "Steel": "เหล็ก", "Wood": "ไม้", "Neutral": "ไม่มีธาตุ", "None": "ไม่มีธาตุ",
    "Short Attacker": "โจมตีระยะประชิด", "Near Attacker": "โจมตีระยะใกล้",
    "Quick Attacker": "โจมตีเร็ว", "Defender": "สายป้องกัน",
}


# Thai-server wording confirmed from in-game screenshots ONLY. Add more as they're verified.
FORM_TH = {
    "Rookie": "ร่างเจริญวัย",
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def img_name(url: str) -> str:
    return urllib.parse.unquote(url.rsplit("/", 1)[-1])


def img_stem(url: str) -> str:
    return img_name(url).rsplit(".", 1)[0]


def awaken_th(name: str) -> str:
    """'วอร์เกรย์มอน (อะเวคเค่น)' / '[อะเวคเค่น] X' / 'X [อเวคเค่น]' -> 'X (ชิน)' (Thai-server naming)."""
    if not name:
        return name
    pat = r"\s*[\(\[]\s*อ(?:ะ)?เวค(?:เค่น|เคน|เค้น)\s*[\)\]]\s*"
    if re.search(pat, name):
        name = re.sub(pat, " ", name).strip()
        name = re.sub(r"\s{2,}", " ", name) + " (ชิน)"
    return re.sub(r"\s*\(ชิน\)", " (ชิน)", name).strip()


class Dex:
    def __init__(self, db_path: Path, images_dir: Path):
        self.db_path = db_path
        self.images_dir = images_dir
        self.disk = {}            # lower filename -> real filename
        self.disk_norm = {}       # norm(stem) -> real filename
        if images_dir.exists():
            for f in images_dir.iterdir():
                self.disk[f.name.lower()] = f.name
                self.disk_norm.setdefault(norm(f.name.rsplit(".", 1)[0]), f.name)
        self.digimon: List[dict] = []
        self.by_key: Dict[str, dict] = {}   # norm(title/slug/alias) -> digimon
        self.rank_members: Dict[str, str] = {}

    # ---------- image helpers ----------
    def local(self, url_or_name: str) -> str:
        name = img_name(url_or_name)
        real = self.disk.get(name.lower())
        if not real:
            safe = re.sub(r'[\\/*?:"<>|#]', "_", name).strip(" ._")
            real = self.disk.get(safe.lower())
        return f"/images/{real}" if real else ""

    def icon_for(self, value: str, page_images: List[str], suffixes=("", " icon", " attribute")) -> str:
        """Find the icon for an infobox value: first in this page's images, then on disk."""
        if not value:
            return ""
        base = re.sub(r"\s*[×x]\s*\d+\s*$", "", value).strip()
        keys = [norm(base + s) for s in suffixes]
        for u in page_images:
            if norm(img_stem(u)) in keys:
                p = self.local(u)
                if p:
                    return p
        for k in keys:
            if k in self.disk_norm:
                return f"/images/{self.disk_norm[k]}"
        # Same words in a different order ("X-Antibody Factor: WarGreymon" -> WarGreymon_X-Antibody_Factor.png)
        words = sorted(re.findall(r"[a-z0-9]+", base.lower()))
        for u in page_images:
            if sorted(re.findall(r"[a-z0-9]+", img_stem(u).lower())) == words:
                p = self.local(u)
                if p:
                    return p
        return ""

    # ---------- parsing ----------
    @staticmethod
    def parse_infobox(text: str) -> dict:
        lines = [re.sub(r"\s+:", ":", l.replace("\xa0", " ")).strip() for l in text.split("\n")]
        try:
            start = lines.index("›")
        except ValueError:
            start = 0
        fields: Dict[str, List[str]] = {}
        names = {}
        cur = None
        i = start
        while i < len(lines):
            l = lines[i]
            if l.startswith(("Korean name:", "Chinese name:", "Thai name:", "Japanese name:")):
                k, v = l.split(":", 1)
                names[k.split()[0].lower()] = v.strip()
            elif l in INFOBOX_LABELS:
                if l == "Digivolved from:" and cur and fields[cur] and fields[cur][-1] in EVO_PREFIXES:
                    fields["evo_kind"] = [fields[cur].pop()]
                cur = l[:-1]
                fields.setdefault(cur, [])
                if l == "Available:":
                    if i + 1 < len(lines):
                        fields[cur].append(lines[i + 1])
                    break
            elif l == "Can be" and i + 1 < len(lines):
                cur = "Can be " + lines[i + 1]
                fields.setdefault(cur, [])
                i += 1
            elif cur and l:
                fields[cur].append(l)
            i += 1
        # Japanese name: "(...)" block right after the title, before "›"
        jp = ""
        head = lines[:start]
        if ")" in head:
            close = len(head) - 1 - head[::-1].index(")")
            if "(" in "".join(head[:close]):
                opens = [j for j, x in enumerate(head[:close]) if x.startswith("(")]
                if opens:
                    seg = head[opens[-1]:close]
                    seg[0] = seg[0][1:]
                    jp = " ".join(s for s in seg if s)
        return {"fields": fields, "names": names, "jp": jp}

    @staticmethod
    def join_vals(vals: List[str]) -> List[str]:
        """Merge text fragments like 'Yes (', '× 5)' and split '+' separators."""
        out, buf = [], ""
        for v in vals:
            if v == "+":
                if buf:
                    out.append(buf)
                buf = ""
                continue
            if buf and (buf.endswith("(") or v.startswith((")", "×"))):
                buf += v
            else:
                if buf:
                    out.append(buf)
                buf = v
        if buf:
            out.append(buf)
        return out

    # ---------- build ----------
    def build(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT slug, title, categories, data_json FROM pages").fetchall()

        # Rank membership from category pages (fallback when the page has no rank icon)
        for r in rows:
            m = re.match(r"Category:Digimon Rank (\S+)$", r["title"])
            if not m:
                continue
            rank = m.group(1)
            txt = json.loads(r["data_json"]).get("text", "")
            seg = txt.split('Pages in category', 1)[-1]
            for l in seg.split("\n"):
                l = l.strip()
                if l and len(l) < 60:
                    self.rank_members.setdefault(norm(l), rank)

        best: Dict[str, dict] = {}
        aliases: Dict[str, str] = {}
        for r in rows:
            title = r["title"]
            if title.startswith(("Information for", "File:", "Category:", "Template:", "Talk:", "User:", "Special:")):
                continue
            try:
                data = json.loads(r["data_json"])
            except Exception:
                continue
            tables = data.get("tables") or []
            if not tables:
                continue
            labels = [row[0] for row in tables[0].get("rows", []) if row]
            if "Form:" not in labels or "Attribute:" not in labels or NON_PLAYABLE.search(title):
                continue
            key = norm(title)
            aliases[norm(r["slug"].replace("_", " "))] = key
            aliases[key] = key
            score = len(r["data_json"]) + (100000 if r["slug"].replace("_", " ") == title else 0)
            if key not in best or score > best[key]["score"]:
                best[key] = {"score": score, "row": r, "data": data}

        for key, b in best.items():
            if b["row"]["title"] in ("Templates",):
                continue
            d = self.make_profile(b["row"], b["data"])
            self.digimon.append(d)
            self.by_key[key] = d
        for a, key in aliases.items():
            if key in self.by_key:
                self.by_key.setdefault(a, self.by_key[key])

        self.apply_riding(rows)
        self.apply_thai()
        self.apply_i18n()

        # Collect icon URLs from all pages to ensure full icon coverage across lines
        self._all_tree_icons = {}
        for d in self.digimon:
            for k, url in d.get("_tree_icons", []):
                nd = self.by_key.get(k)
                if nd and url:
                    self._all_tree_icons.setdefault(nd["slug"], url)
                    self._all_tree_icons.setdefault(norm(nd["title"]), url)

        # Resolve evolution lines + trees from Thai client tables
        self.load_client_lines()
        for d in self.digimon:
            d["tree"] = self.build_tree(d)

        self.digimon.sort(key=lambda d: (-d["rank_weight"], d["title"]))
        conn.close()

    # ---------- riding (dmowiki "Riding Mode" page + Thai client ride animations) ----------
    def apply_riding(self, rows):
        page = next((r for r in rows if r["slug"] == "Riding_Mode"), None)
        ride_map = {}
        if page:
            data = json.loads(page["data_json"])
            imgs = data.get("images", [])
            generic_icon = self.icon_for("Riderwing", imgs)
            for t in data.get("tables", []):
                for row in t.get("rows", [])[1:]:
                    if len(row) < 3:
                        continue
                    name, item = row[0].strip(), re.sub(r"\s+", " ", row[2]).strip()
                    if item.startswith("×"):
                        qty = re.findall(r"×\s*(\d+)", item)
                        label = "Riderwing / Mode Selector" + (f" × {qty[0]}" if qty else "")
                        entry = [{"name": label, "icon": generic_icon}]
                    else:
                        entry = [{"name": item, "icon": self.icon_for(item, imgs)}]
                    ride_map[norm(name)] = entry
        self.ride_map = ride_map
        for d in self.digimon:
            if not d["ride_items"]:
                hit = ride_map.get(norm(d["title"])) or ride_map.get(norm(d["slug"]))
                if hit:
                    d["ride_items"] = hit
                    d["ride_source"] = "dmowiki Riding Mode"
            elif not d.get("ride_source"):
                d["ride_source"] = "dmowiki"

    # ---------- Thai server availability ----------
    def apply_thai(self):
        try:
            from thai_client import ThaiIndex, load
        except ImportError:
            return
        data = load()
        overrides_path = Path(__file__).resolve().parent / "thai_overrides.json"
        ov = json.loads(overrides_path.read_text(encoding="utf-8")) if overrides_path.exists() else {}
        inc = {norm(x) for x in ov.get("include", [])}
        exc = {norm(x) for x in ov.get("exclude", [])}
        self.thai_loaded = bool(data)
        if not data:
            for d in self.digimon:
                d["in_thai"] = True
            return
        ti = ThaiIndex(data)
        names_by_slug: Dict[str, set] = {}
        for k, d in self.by_key.items():
            names_by_slug.setdefault(d["slug"], set()).add(k)
        generic = self.icon_for("Riderwing", [])
        for d in self.digimon:
            r = ti.lookup(d["title"], list(names_by_slug.get(d["slug"], [])))
            t = norm(d["title"])
            # Long-standing low forms (no Rank) are trusted from the wiki even without client files;
            # Mega+ (ranked) and Awaken/Extreme forms need evidence in the Thai client.
            special = bool(re.search(r"awaken|extreme", d["title"], re.I))
            trusted = not d["rank"] and not special
            d["in_thai"] = (bool(r["folder"]) or trusted or t in inc) and t not in exc
            d["thai_evidence"] = r["folder"] or ("dmowiki (ร่างต่ำ ไม่มี Rank)" if trusted else "")
            d["thai_model"] = r["folder"] or ""
            d["can_ride_thai"] = r["can_ride_thai"]
            if r["can_ride_thai"]:
                if not d["can_ride"].startswith("Yes"):
                    d["can_ride"] = "Yes"
                if not d["ride_items"]:
                    d["ride_items"] = [{"name": "Riderwing / Mode Selector", "icon": generic}]
                    d["ride_source"] = "ไฟล์เกมเซิร์ฟไทย"

    # ---------- Thai translations (web/i18n/*.json) ----------
    def apply_i18n(self):
        i18n_dir = Path(__file__).resolve().parent / "i18n"

        def load(name):
            p = i18n_dir / name
            if not p.exists():
                return {}
            data = json.loads(p.read_text(encoding="utf-8"))
            return {k: v for k, v in data.items() if not k.startswith("_")}

        voc = load("th_vocab.json")
        items = load("th_items.json")
        self.i18n_text = load("th_text.json")      # long English text -> Thai (skills, passives, lore)
        self.i18n_skills = load("th_skills.json")  # skill name -> Thai
        names = voc.get("names", {})
        sect = lambda k: voc.get(k, {})

        def thai_of_digimon(name):
            d = self.by_key.get(norm(name))
            return (d.get("thai_name") or names.get(d["title"], "")) if d else ""

        def item_th(name):
            m = re.match(r"^(.*?)\s*(×\s*\d+)$", name)
            base, qty = (m.group(1), " " + m.group(2)) if m else (name, "")
            if base in items:
                return items[base] + qty
            x = re.match(r"^X-Antibody Factor\s*[-:]?\s*(.+)$", base) or re.match(r"^(.+?)\s+X-Antibody Factor$", base)
            if x:
                target = x.group(1).strip()
                parts = re.split(r"\s*[–-]\s*(?=Alpha|Beta)", target)
                who = thai_of_digimon(parts[0]) or parts[0]
                suffix = {"Alpha": " – อัลฟ่า", "Beta": " – เบต้า"}.get(parts[1].strip(), "") if len(parts) > 1 else ""
                return f"เอ็กซ์-แอนติบอดี้ แฟคเตอร์: {who}{suffix}{qty}"
            return ""

        self.vocab = voc
        self.item_th = item_th
        self.thai_of_digimon = thai_of_digimon
        junk = re.compile(r"^(Default Stats|Digivolves)$|\[\[|link=|^is ")
        # Names are karaoke (transliteration) only: undo meaning-translations found in wiki names
        name_override = voc.get("name_override", {})
        suffix_karaoke = voc.get("suffix_karaoke", {})
        for d in self.digimon:
            if not d["thai_name"] and names.get(d["title"]):
                d["thai_name"] = names[d["title"]]
                d["thai_name_unofficial"] = True
            if d["title"] in name_override:
                d["thai_name"] = name_override[d["title"]]
            else:
                for a, b in suffix_karaoke.items():
                    d["thai_name"] = d["thai_name"].replace(a, b)
            d["form_th"] = FORM_TH.get(d["form"]) or sect("form").get(d["form"], "")
            d["attribute_th"] = sect("attribute").get(d["attribute"], d.get("attribute_th", ""))
            d["element_th"] = sect("element").get(d["element"], d.get("element_th", ""))
            d["attacker_type_th"] = sect("attacker_type").get(d["attacker_type"], d.get("attacker_type_th", ""))
            d["type_th"] = sect("type").get(d["type"], "")
            d["location_th"] = sect("location").get(d["location"], "")
            d["families"] = [f for f in d["families"] if not junk.search(f["name"]) and len(f["name"]) < 40]
            for f in d["families"]:
                f["th"] = sect("family").get(f["name"], "")
            for it in d["unlock_items"] + d["ride_items"]:
                it["th"] = item_th(it["name"])
            d["evo_from_th"] = [thai_of_digimon(n) for n in d["evo_from_names"]]
        # Thai server calls the Awaken forms "(ชิน)"
        for d in self.digimon:
            d["thai_name"] = awaken_th(d["thai_name"])
        for d in self.digimon:
            d["evo_from_th"] = [thai_of_digimon(n) for n in d["evo_from_names"]]

    def text_th(self, s: str) -> str:
        return getattr(self, "i18n_text", {}).get(s.strip(), "") if s else ""

    def make_profile(self, row, data) -> dict:
        title, slug = row["title"], row["slug"]
        cats = json.loads(row["categories"] or "[]")
        text = data.get("text", "")
        imgs = data.get("images", [])
        ib = self.parse_infobox(text)
        f = ib["fields"]
        first = lambda k: (self.join_vals(f.get(k, [])) or [""])[0]

        # Rank: icon in page > category on page > category page listing. Only Mega+ have ranks.
        rank = ""
        for u in imgs:
            st = img_stem(u)
            if st in RANK_WEIGHTS:
                rank = st
                break
        if not rank:
            for c in cats:
                m = re.match(r"Digimon Rank (\S+)$", c)
                if m and m.group(1) in RANK_WEIGHTS:
                    rank = m.group(1)
                    break
        if not rank:
            rank = self.rank_members.get(norm(title), "")

        canon = {k.lower(): k for k in THAI}
        attribute = first("Attribute")
        attribute = canon.get(attribute.lower(), attribute)
        element = first("Elemental Attribute")
        element = canon.get(element.lower(), element)
        attacker = next((a for a in ATTACKER_TYPES if a in cats), "")
        form = first("Form")

        def items(label):
            return [{"name": v, "icon": self.icon_for(v, imgs)} for v in self.join_vals(f.get(label, []))]

        unlock = sum((items(l) for l in ("Unlocked with item", "Unlocked with item 2",
                                         "Unlocked with item 3", "Unlocked with item 4")), [])
        unlock += [i for i in items("Unlocked with") if i["name"].lower() != "already unlocked"]
        ride = items("Rideable with item")
        families = [{"name": v, "icon": self.icon_for(v, imgs, (" icon", ""))} for v in self.join_vals(f.get("Families", []) + f.get("Family", []))]

        # Main portrait: page image named like the title (not the _Icon)
        portrait = ""
        icon = ""
        for u in imgs:
            st = norm(img_stem(u))
            if not portrait and st == norm(title):
                portrait = self.local(u)
            if not icon and st == norm(title) + "icon":
                icon = self.local(u)
        if not icon:
            k = norm(title) + "icon"
            icon = f"/images/{self.disk_norm[k]}" if k in self.disk_norm else ""
        if not portrait:
            k = norm(title)
            portrait = f"/images/{self.disk_norm[k]}" if k in self.disk_norm else ""
        if not portrait:
            # "Rosemon (Original)" shows the shared "Rosemon.png" model on its own page
            base = norm(re.sub(r"\s*\([^)]*\)\s*$", "", title))
            for u in imgs:
                if base and norm(img_stem(u)) == base:
                    portrait = self.local(u)
                    break
        portrait = portrait or icon

        tree_icons = []  # ordered node keys appearing as *_Icon images
        for u in imgs:
            st = img_stem(u)
            if st.lower().endswith("_icon"):
                tree_icons.append((norm(st[:-5]), self.local(u)))

        can_ride = first("Can be ridden")
        return {
            "slug": slug,
            "title": title,
            "thai_name": ib["names"].get("thai", ""),
            "kr_name": ib["names"].get("korean", ""),
            "cn_name": ib["names"].get("chinese", ""),
            "jp_name": ib["jp"],
            "rank": rank,
            "rank_weight": RANK_WEIGHTS.get(rank, 0),
            "rank_color": RANK_COLORS.get(rank, "#475569"),
            "rank_icon": self.local(rank + ".png") if rank else "",
            "form": form,
            "form_th": FORM_TH.get(form, ""),
            "attribute": attribute,
            "attribute_th": THAI.get(attribute, ""),
            "attribute_icon": self.icon_for(attribute, imgs, ("", " attribute")),
            "element": element,
            "element_th": THAI.get(element, ""),
            "element_icon": self.icon_for(element, imgs, ("", " attribute")),
            "attacker_type": attacker,
            "attacker_type_th": THAI.get(attacker, ""),
            "attacker_icon": self.icon_for(attacker, imgs),
            "type": first("Type"),
            "families": families,
            "unlock_level": first("Unlocked at level"),
            "unlock_items": unlock,
            "ride_items": ride,
            "required_to_evolve": " ".join(f.get("Required to evolve", [])),
            "evo_kind": first("evo_kind"),
            "evo_from_names": self.join_vals(f.get("Digivolved from", [])),
            "evo_to_names": self.join_vals(f.get("Digivolves to", [])),
            "location": first("Location"),
            "can_ride": can_ride,
            "can_hatch": first("Can be hatched"),
            "hatch_data_raw": list(f.get("Data needed / amount", [])),
            "available": first("Available"),
            "image": portrait,
            "icon": icon,
            "categories": cats,
            "_tree_icons": tree_icons,
            "_data": data,
        }

    def resolve(self, name: str, pool: Optional[set] = None) -> Optional[dict]:
        k = norm(name)
        d = self.by_key.get(k)
        if pool is None:
            return d
        if d and norm(d["title"]) in pool:
            return d
        # "Agumon" inside a tree that contains "Agumon (Classic)"
        base = norm(re.sub(r"\(.*?\)", "", name))
        for p in pool:
            pd = self.by_key.get(p)
            if pd and norm(re.sub(r"\(.*?\)", "", pd["title"])) == base:
                return pd
        return None

    def load_client_lines(self):
        """Parse all mercenary lines from CrackDMO devolutionlist.bin into clean DAG trees.
        Every mercenary line in DMO is keyed by parent ID (Slot 1), with subsequent slots
        linked strictly within that line so no two mercenary lines bleed into each other."""
        try:
            try:
                import thai_client_evo as E
                from thai_client_match import ClientMatcher
            except ImportError:
                from web import thai_client_evo as E
                from web.thai_client_match import ClientMatcher
            names = E.digimon_names()
            lines = E.parse_lines(set(names))
            matcher = ClientMatcher(self)
        except Exception as ex:
            print("[DEX] client evolution lines unavailable:", ex)
            self._client_lines = []
            self._slug_to_lines = {}
            return

        by_parent = {}
        for ln in lines:
            if 76000 <= ln["parent"] < 77000:  # event/jumping copies
                continue
            by_parent.setdefault(ln["parent"], []).append(ln)

        line_trees = []
        for pid, lns in by_parent.items():
            root_dex = matcher.find(pid, names.get(pid, ""))
            if not root_dex:
                continue

            reach = {pid: set(ln["type"] for ln in lns)}
            for ln in lns:
                reach[ln["type"]] = set(ln["to"])

            all_types = [pid] + [ln["type"] for ln in sorted(lns, key=lambda x: x["slot"])]
            nodes = []
            for t in all_types:
                if t not in nodes:
                    nodes.append(t)

            slot_dex = {}
            slot_map = {}
            for ln in lns:
                d = matcher.find(ln["type"], names.get(ln["type"], ""))
                if d:
                    slot_dex[ln["type"]] = d
                    slot_map[ln["type"]] = ln["slot"]

            parents = {}
            for B in nodes[1:]:
                cand = [A for A in nodes if B in reach.get(A, set())]
                direct = []
                for A in cand:
                    is_direct = True
                    for C in cand:
                        if C != A and B in reach.get(C, set()) and C in reach.get(A, set()):
                            is_direct = False
                            break
                    if is_direct:
                        direct.append(A)
                if len(direct) > 1:
                    # Prefer base form over side/x form when ambiguous
                    if B == 75902 and 71072 in direct:       # Omegamon X -> Omegamon
                        direct = [71072]
                    elif B == 75900 and 71075 in direct:     # AOX -> AO
                        direct = [71075]
                    elif B == 71041 and 61043 in direct:     # Millenniummon -> Machinedramon
                        direct = [61043]
                    else:
                        direct = [direct[0]]
                if direct:
                    parents[B] = direct[0]

            children = {}
            for c, p in parents.items():
                children.setdefault(p, []).append(c)

            # Sort children by slot number so main line stays straight (first child)
            for p in children:
                children[p].sort(key=lambda c: slot_map.get(c, 999))

            all_slugs = {root_dex["slug"]} | {d["slug"] for d in slot_dex.values()}
            line_trees.append({
                "pid": pid,
                "root_dex": root_dex,
                "slot_dex": slot_dex,
                "nodes": nodes,
                "parents": parents,
                "children": children,
                "all_slugs": all_slugs,
            })

        # Drop obsolete / truncated subset lines (e.g. older versions of mercenary eggs)
        filtered_trees = []
        for i, t1 in enumerate(line_trees):
            is_subset = False
            for j, t2 in enumerate(line_trees):
                if i != j and t1["root_dex"]["slug"] == t2["root_dex"]["slug"]:
                    if t1["all_slugs"] < t2["all_slugs"]:
                        is_subset = True
                        break
            if not is_subset:
                filtered_trees.append(t1)

        slug_to_lines = {}
        for lt in filtered_trees:
            for slug in lt["all_slugs"]:
                slug_to_lines.setdefault(slug, []).append(lt)

        self._client_lines = filtered_trees
        self._slug_to_lines = slug_to_lines
        print(f"[DEX] Loaded {len(filtered_trees)} clean client mercenary lines covering {len(slug_to_lines)} Digimon")

    def build_client_tree(self, d: dict) -> Optional[List[dict]]:
        lines = getattr(self, "_slug_to_lines", {}).get(d["slug"])
        if not lines:
            return None

        me_slug = d["slug"]
        all_icons = getattr(self, "_all_tree_icons", {})

        def to_node(typ, lt, path):
            if typ == lt["pid"]:
                nd = lt["root_dex"]
            else:
                nd = lt["slot_dex"].get(typ)
            if not nd:
                return None
            kids = []
            if typ not in path:
                for c in lt["children"].get(typ, []):
                    kn = to_node(c, lt, path | {typ})
                    if kn:
                        kids.append(kn)
            icon = nd.get("icon") or all_icons.get(nd["slug"]) or all_icons.get(norm(nd["title"])) or nd.get("image", "")
            return {
                "slug": nd["slug"],
                "title": nd["title"],
                "thai": nd.get("thai_name") or nd["title"],
                "icon": icon,
                "rank": nd.get("rank", ""),
                "form": nd.get("form", ""),
                "current": nd["slug"] == me_slug,
                "in_thai": nd.get("in_thai", True),
                "jogress": nd.get("evo_kind") == "Jogress",
                "children": kids,
            }

        trees = []
        for lt in lines:
            r = to_node(lt["pid"], lt, frozenset())
            if r:
                trees.append(r)
        return trees if trees else None

    def build_tree(self, d: dict) -> List[dict]:
        client_tree = self.build_client_tree(d)
        if client_tree:
            return client_tree
        return self.build_wiki_tree(d)

    def build_wiki_tree(self, d: dict) -> List[dict]:
        # Nodes = digimon whose icon appears on this page (dmowiki's tree for this line)
        nodes = []
        page_icon = {}
        for k, url in d["_tree_icons"]:
            nd = self.by_key.get(k)
            if nd and norm(nd["title"]) not in nodes:
                nodes.append(norm(nd["title"]))
                page_icon[norm(nd["title"])] = url
        me = norm(d["title"])
        if me not in nodes:
            nodes.append(me)
        # The wiki reuses one icon for same-named forms of different lines (Palmon's tree shows the "Rosemon"
        # icon for "Rosemon (Original)"). If a node does not come from anything in this tree but a namesake
        # form does, use the namesake.
        pool0 = set(nodes)
        if not hasattr(self, "_by_base"):
            self._by_base = {}
            for x in self.digimon:
                self._by_base.setdefault(norm(re.sub(r"\s*\([^)]*\)\s*$", "", x["title"])), []).append(x)

        def comes_from_pool(x, pool, skip=None):
            return any((p := self.resolve(n, pool)) and norm(p["title"]) not in (norm(x["title"]), skip)
                       for n in x["evo_from_names"])

        for i, k in enumerate(list(nodes)):
            nd = self.by_key[k]
            if k == me or not nd["evo_from_names"] or comes_from_pool(nd, pool0):
                continue
            base = norm(re.sub(r"\s*\([^)]*\)\s*$", "", nd["title"]))
            alts = [x for x in self._by_base.get(base, [])
                    if norm(x["title"]) != k and norm(x["title"]) not in pool0 and comes_from_pool(x, pool0, k)]
            if len(alts) == 1:
                ak = norm(alts[0]["title"])
                nodes[i] = ak
                page_icon[ak] = alts[0].get("icon") or page_icon.pop(k, "")
        # Add Awaken / Extreme forms of anything in the tree even if the wiki page omitted their icon
        for k in list(nodes):
            t = self.by_key[k]["title"]
            for suffix in (" (Awaken)", " (Extreme)"):
                v = self.by_key.get(norm(t + suffix))
                if v and v.get("in_thai", True) and norm(v["title"]) not in nodes:
                    nodes.append(norm(v["title"]))
                    if v["icon"]:
                        page_icon.setdefault(norm(v["title"]), v["icon"])
        # lines the wiki page left out: an egg Digimon (line root in the client) that evolves into a form in
        # this tree joins the tree (DarknessBagramon <- DarkKnightmon <- Deadly Axemon)
        cp = getattr(self, "_client_parents", {})
        roots = {p for ps in cp.values() for p in ps if p not in cp}
        for k in list(nodes):
            for p in cp.get(k, []):
                if p in roots and p not in nodes and p in self.by_key:
                    nodes.append(p)
                    page_icon.setdefault(p, self.by_key[p].get("icon", ""))
        pool = set(nodes)

        parents: Dict[str, List[str]] = {k: [] for k in nodes}
        for k in nodes:
            nd = self.by_key[k]
            for pname in nd["evo_from_names"]:
                p = self.resolve(pname, pool)
                if p:
                    pk = norm(p["title"])
                    if pk != k and pk not in parents[k]:
                        parents[k].append(pk)

        # the client's links between forms that are both in this tree
        for k in nodes:
            for pk in cp.get(k, []):
                if pk in pool and pk != k and pk not in parents[k] and (not parents[k] or pk in roots):
                    parents[k].append(pk)

        # "Digivolves to" on the parent's page fills gaps when the child page lacks "Digivolved from"
        for k in nodes:
            for cname in self.by_key[k]["evo_to_names"]:
                ch = self.resolve(cname, pool)
                if ch:
                    ck = norm(ch["title"])
                    if ck != k and not parents[ck]:
                        parents[ck].append(k)
        # Awaken / Extreme / mode forms often have no "Digivolved from": hang them under their base form
        # (dmowiki draws them as a branch of the base form, so this overrides "Digivolved from")
        for k in nodes:
            title = self.by_key[k]["title"]
            base = re.sub(r"\s*\((awaken|extreme)\)\s*$|\s+(awaken|extreme)$", "", title, flags=re.I)
            if base != title and norm(base) in pool and norm(base) != k:
                parents[k] = [norm(base)]
        # No relations recorded at all: the wiki tree is a plain chain in icon order
        if len(nodes) > 1 and not any(parents.values()):
            for a, b in zip(nodes, nodes[1:]):
                parents[b].append(a)

        # Drop parents that are ancestors of another listed parent (wiki lists line root + direct parent)
        def ancestors(k, seen=None):
            seen = seen or set()
            for p in parents.get(k, []):
                if p not in seen:
                    seen.add(p)
                    ancestors(p, seen)
            return seen
        for k in nodes:
            ps = parents[k]
            if len(ps) > 1:
                parents[k] = [p for p in ps if not any(p in ancestors(q) for q in ps if q != p)]

        # Upgraded Jogress forms ("Omegamon - Merciful Mode") hang under their base Jogress ("Omegamon")
        # when both share the same parents, like dmowiki draws them.
        jog = [k for k in nodes if self.by_key[k]["evo_kind"] == "Jogress" or "jogress" in self.by_key[k]["form"].lower()]
        for a in jog:
            for b in jog:
                if a == b or not parents[a]:
                    continue
                ta, tb = self.by_key[a]["title"], self.by_key[b]["title"]
                if (ta.startswith(tb + " ") and set(parents[a]) <= set(parents[b]) | {b}
                        and self.by_key[a]["rank_weight"] >= self.by_key[b]["rank_weight"]):
                    parents[a] = [b]

        children: Dict[str, List[str]] = {k: [] for k in nodes}
        for k in nodes:
            for p in parents[k]:
                children[p].append(k)

        # Lone nodes with no relation to anything (mode selectors, unrelated icons) are skipped
        def node(k, path):
            nd = self.by_key[k]
            kids = [] if k in path else [node(c, path | {k}) for c in children[k]]
            return {
                "slug": nd["slug"], "title": nd["title"], "thai": nd["thai_name"],
                "icon": nd["icon"] or page_icon.get(k) or nd["image"],
                "rank": nd["rank"], "form": nd["form"], "current": k == me,
                "in_thai": nd.get("in_thai", True),
                "jogress": nd["evo_kind"] == "Jogress", "children": kids,
            }

        roots = [k for k in nodes if not parents[k] and (children[k] or k == me)]

        # Only the lines this Digimon is on: Deadly Axemon's page shows Deadly Axemon > DarkKnightmon >
        # DarknessBagramon, not the SkullKnightmon / Bagramon lines that meet it at DarknessBagramon.
        def reaches(r, seen=frozenset()):
            return r == me or any(reaches(c, seen | {r}) for c in children[r] if c not in seen)
        mine = [r for r in roots if reaches(r)]
        if mine:
            roots = mine
        return [node(r, frozenset()) for r in roots]

    def public(self, d: dict) -> dict:
        return {k: v for k, v in d.items() if not k.startswith("_")}
