"""
Thai DMO client check: which Digimon have a model in the Thai client's pack01.pf.

pack01.pf layout (per entry): header, 260-byte file name XOR'd with 0xD0, 8 bytes
(the last 4 = name length), then the raw file. Only file *names* are needed here:
every playable Digimon has a model folder data\\digimon\\<folder>\\ and Digimon that
can be ridden also ship ride_* animations in that folder.

Folder names use Japanese / internal spellings (graymon, dukemon, vamdemon...), so
they are normalised through ROOTS before matching against dmowiki titles.

Run directly to (re)build web/thai_client.json:
    python web/thai_client.py "G:\\DigimonMastersOnline(Tailand)\\Data\\pack01.pf"
"""
import difflib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / "thai_client.json"
BS = chr(92)

# internal/JP spelling -> dmowiki (EN) spelling, applied as substring replacements
ROOTS = [
    ("metal greymon_black", "blackmetalgreymon"), ("wargrey_black", "blackwargreymon"),
    ("weregarurumon_black", "blackweregarurumon"), ("metalgarurumon_black", "blackmetalgarurumon"),
    ("garurumon_black", "blackgarurumon"), ("graymon_black", "blackgreymon"),
    ("gabumon_black", "blackgabumon"), ("agumon_black", "blackagumon"), ("agumon_cls", "agumonclassic"),
    ("agumon_yuki_no_kizuna", "agumonbondofbravery"), ("shiebm", "shinegreymonburstmode"),
    ("shiegrey", "shinegreymon"), ("risegraymon", "rizegreymon"), ("geograymon", "geogreymon"),
    ("metalgraymon", "metalgreymon"), ("graymon", "greymon"), ("megarograumon", "wargrowlmon"),
    ("megalogrowmon", "wargrowlmon"), ("graumon", "growlmon"), ("growmon", "growlmon"),
    ("chaosdukemon", "chaosgallantmon"), ("medievaldukemon", "medievalgallantmon"),
    ("dukemon_crimsonmode", "gallantmoncrimsonmode"), ("dukemon", "gallantmon"),
    ("belialvamdemon", "malomyotismon"), ("vamdemon", "myotismon"), ("chaospiedmon", "chaospiedmon"),
    ("piemon", "piedmon"), ("pinokimon", "puppetmon"), ("blackgatomon", "blackgatomon"),
    ("tailmon", "gatomon"), ("piyomon", "biyomon"), ("ulforcevdramon", "ulforceveedramon"),
    ("aerov-dramon", "aeroveedramon"), ("v-dramon", "veedramon"), ("vmon", "veemon"),
    ("beelzebumonblaster", "beelzemonblastmode"), ("beelzebumon", "beelzemon"),
    ("mugendramon", "machinedramon"), ("millenniumon", "millenniummon"), ("ofanimon_falldown", "ophanimonfalldownmode"),
    ("tentamon", "tentomon"), ("teriamon", "terriermon"), ("tocanmon", "toucanmon"), ("lilimon", "lillymon"),
    ("lilymon", "lillymon"), ("tyranomon", "tyrannomon"), ("dexdorughoramon", "dexdorugoramon"),
    ("dorughoramon", "dorugoramon"), ("dexdolgamon", "dexdorugamon"), ("dolgamon", "dorugamon"),
    ("dexdorugreymon", "dexdorugreymon"), ("dorugrevmon", "dorugreymon"), ("hisharyuumon", "hisyaryuumon"),
    ("craniummon", "craniamon"), ("anibismon", "anubismon"), ("silffymon", "silphymon"),
    ("saviorhuckmon", "saviorhackmon"), ("mudfigimon", "mudfrigimon"), ("zephrymon", "zephyrmon"),
    ("syatskohmon", "shakkoumon"), ("wargarrurumon", "weregarurumon"), ("metalgaru", "metalgarurumon"),
    ("metalgarurumonrumon", "metalgarurumon"), ("mirage_bm", "miragegaogamonburstmode"),
    ("mirage", "miragegaogamon"), ("rosemonbm", "rosemonburstmode"), ("ravemonbm", "ravemonburstmode"),
    ("yashamon", "yasyamon"), ("okugawamon", "okuwamon"), ("deadlyaxeman", "deadlyaxemon"),
    ("kuzhamon", "kuzuhamon"), ("giamonat", "gizumonat"), ("giamonxt", "gizumonxt"),
    ("tykabterimon", "tyrantkabuterimon"), ("atrarkabuterimon", "megakabuterimon"),
    ("kubuterimon", "kabuterimon"), ("hercules", "herculeskabuterimon"),
    ("skullmommothmon", "skullmammothmon"), ("varodurumon", "valdurmon"), ("antroiamon", "ancienttroiamon"),
    ("marineangelmon", "marineangemon"), ("mysticmon", "mystimon"), ("banchyo", "banchouleomon"),
    ("susanomon", "susanoomon"), ("redveggiemon", "redvegiemon"), ("veggiemon", "vegiemon"),
    ("saintgargomon", "megagargomon"), ("blacksaintgalgomon", "blackmegagargomon"),
    ("darknightmon", "darkknightmon"), ("cherubimonvaccinemon", "cherubimonwhite"),
    ("imperialdramonfightermode", "imperialdramonfightermode"), ("imperialfighterorigin", "imperialdramonfightermode"),
    ("imperialpaladinorigin", "imperialdramonpaladinmode"), ("impedraorigin", "imperialdramondragonmode"),
    ("impedra", "imperialdramondragonmode"), ("paildramonorigin", "paildramon"),
    ("lucemonfalldown", "lucemonfalldownmode"), ("lucemon_satanmode_bustmode", "lucemonsatanmode"),
    ("meicrackmon_vicious", "meicrackmonviciousmode"), ("omegamon_alter_b", "omegamonalterb"),
    ("omegamon_alter_s", "omegamonalters"), ("omegamonzwartd", "omegamonzwartd"),
    ("toyagumon_child", "toyagumonrookie"), ("toyagumon_perfect", "toyagumonultimate"),
    ("sparrowmon_ultimate", "sparrowmon"), ("plutomon", "plutomon"),
    ("prince_mamemon", "princemamemon"), ("knightchessmon_b", "knightchessmonblack"),
    ("pawnchessmon_b", "pawnchessmonblack"), ("leomon_white", "leomon"), ("apocalymon_origin", "apocalymon"),
    ("armagemon", "armageddemon"), ("rusttyranomon", "rusttyrannomon"), ("metaltyranomon", "metaltyrannomon"),
    ("darktyranomon", "darktyrannomon"), ("candmon", "candlemon"), ("phoenixmon2", "phoenixmon"),
    ("coredramon_blue", "coredramonblue"), ("coredramon_green", "coredramongreen"),
    ("ouryuumon", "ouryuumon"), ("ginryuumon", "ginryumon"), ("ryuudamon", "ryudamon"),
    ("lighdramon", "lighdramon"), ("shoutmondx", "shoutmonx7superiormode"),
    ("arumajimon", "armadillomon"), ("pico_venom", "venomdemidevimon"), ("pico", "demidevimon"),
    ("kyubimon", "kyuubimon"), ("grizzmon", "grizzlymon"), ("mammon", "mammothmon"), ("shakomon", "syakomon"),
    ("pummon", "pumpkinmon"), ("petitmeramon", "demimeramon"), ("garummon", "garmmon"),
    ("mercuremon", "merukurimon"), ("dorumon_dex", "dexdorumon"),
    ("fladramon", "flamedramon"), ("holyangemon", "magnaangemon"), ("deathxmon", "dexmon"),
    ("blackseraphimon", "shadowseraphimon"), ("qinglongmon", "azulongmon"), ("xuanwumon", "ebonwumon"),
    ("jyureimon", "cherrymon"), ("hanumon", "apemon"), ("insekimon", "meteormon"), ("dogmon", "doggymon"),
    ("gawappamon", "gwappamon"), ("deathmeramon", "skullmeramon"), ("hinadromon", "hiandromon"),
    ("lanamon", "ranamon"), ("algomonultimate", "argomonultimate"), ("algomon", "argomon"),
    ("huanglongmon", "fanglongmon"), ("crownmon", "crowmon"), ("okuwamon", "okuwamon"),
    ("gabumon_yujo no kizuna", "gabumonbondoffriendship"), ("last_evolusion_kizuna", "lastevolutionkizuna"),
    ("saintgalgomon", "megagargomon"), ("d-reaper_adr-01", "dreaperadr01"), ("beelzubumon", "beelzemon"),
    ("beelzebumon_blast mode", "beelzemonblastmode"), ("betel_gammamon", "betelgammamon"),
    ("imperialdramon_fightermode", "imperialdramonfightermode"),
    ("imperialdramon_paladinmode", "imperialdramonpaladinmode"),
    ("lucemon_satanmode", "lucemonsatanmode"),
    ("griffonmon", "gryphonmon"), ("chackmon", "kumamon"),
]
ROOTS.sort(key=lambda r: -len(r[0]))   # longest rule wins; only one rule per name
EXTRA = {"knightchessmon": ["knightchessmonwhite"], "pawnchessmon": ["pawnchessmonwhite"],
         "rosemon_new": ["rosemonoriginal"]}
STRIP = re.compile(r"_(re|t|c|p|r|02|new|bike|move|jiji|musya|murmukus|gurane|minor|re_grani|fanal|weaked|raidtest|perfect|ultimate|adult|champion|larva|sleep_mode|ragemode)$")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def folder_keys(folder):
    """All normalised names a model folder can stand for."""
    f = folder.lower()
    keys = {norm(f), *EXTRA.get(f, [])}
    for base in {f, STRIP.sub("", f)}:
        g = base
        for a, b in ROOTS:
            if a in g:
                g = g.replace(a, b)
                break
        keys.add(norm(g))
        if norm(g).endswith("x"):          # "...monx" = X-Antibody form
            keys.add(norm(g) + "antibodysystem")
    # "<name>_re" / "<name>_awake" are the Awaken (renewal) models
    m = re.match(r"(.+?)_(re|awake)$", f)
    if m:
        g = m.group(1)
        for a, b in ROOTS:
            if a in g:
                g = g.replace(a, b)
                break
        keys.add(norm(g) + "awaken")
    return keys


def scan_pack(pf_path):
    # Names start with "data\" or "Data\" (any casing) -> anchor on the xor'd backslash
    import itertools
    pats = {bytes(x ^ 0xD0 for x in "".join(c).encode() + bytes([0x5C]))
            for c in itertools.product(*[(ch.lower(), ch.upper()) for ch in "data"])}
    anchor = bytes([0x5C ^ 0xD0])
    chunk = 64 << 20
    size = os.path.getsize(pf_path)
    names = []
    with open(pf_path, "rb") as f:
        pos = 0
        while pos < size:
            f.seek(pos)
            buf = f.read(chunk + 300)
            i = buf.find(anchor, 4)
            while i != -1 and i < chunk + 4:
                s = i - 4
                if s < chunk and buf[s:i + 1] in pats:
                    raw = bytes(x ^ 0xD0 for x in buf[s:s + 260])
                    m = re.match(rb"[\x20-\x7e]+", raw)
                    hdr = buf[s + 260:s + 268]
                    if m and len(hdr) == 8:
                        n = int.from_bytes(hdr[4:8], "little")
                        if 0 < n <= len(m.group(0)):
                            names.append(m.group(0)[:n].decode("latin-1").lower())
                i = buf.find(anchor, i + 1)
            pos += chunk
    folders = {}
    seals, slots = set(), set()
    for n in names:
        p = n.split(BS)
        if len(p) > 3 and p[0] == "data" and p[1] == "digimon":
            folders.setdefault(p[2], set()).add(p[3])
        elif "sealmaster" + BS + "sealimage" + BS in n:
            seals.add(re.sub(r"^sealmaster_img_", "", p[-1].rsplit(".", 1)[0]))
        elif "random_box" + BS + "slot_image" + BS in n:
            slots.add(re.sub(r"_slot(_\d+)?$", "", p[-1].rsplit(".", 1)[0]))
    return {
        "source": str(pf_path),
        "pack_mtime": os.path.getmtime(pf_path),
        "folders": {k: sorted(v) for k, v in sorted(folders.items())},
        "seal_images": sorted(seals),
        "slot_images": sorted(slots),
    }


GENERIC_STEMS = {"arun", "idle", "run", "walk", "die", "block", "buff", "miss", "hre", "shk", "msk", "lqua", "rqua"}


def model_stems(files):
    """Digimon names hidden in a folder's model files: '1731028_drimogemon.kfm' -> 'drimogemon'."""
    out = set()
    for fn in files:
        if not fn.endswith((".kfm", ".nif")):
            continue
        s = re.sub(r"^\d+_", "", fn.rsplit(".", 1)[0])
        s = re.sub(r"(_skin\d*|\d+)$", "", s)
        if s and s not in GENERIC_STEMS and len(s) > 3:
            out.add(s)
    return out


def load():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return None


class ThaiIndex:
    """Lookup: does a dmowiki Digimon have a model (and ride animations) in the Thai client?"""

    # Forms that reuse the base model. Awaken / Extreme are NOT here: they ship their own
    # model folders, so a missing folder means the form isn't in the Thai client.
    VARIANT = re.compile(r"\s*\((jogress|mega|ss\+|c|armor|final mode)\)", re.I)

    def __init__(self, data):
        self.folders = data["folders"]
        self.key2folder = {}
        playable = [f for f in self.folders if not ("raidboss" in f or f.endswith("_boss"))]
        # 1) folder names, 2) model file names inside folders (plutomon/ -> salamon.nif)
        for folder in playable:
            for k in folder_keys(folder):
                self.key2folder.setdefault(k, folder)
        for folder in playable:
            for stem in model_stems(self.folders[folder]):
                for k in folder_keys(stem):
                    self.key2folder.setdefault(k, folder)
        # 3) random-box slot art and Seal Master card art (no model folder of their own)
        for stem in data.get("slot_images", []):
            for k in folder_keys(stem.replace("-", "")):
                self.key2folder.setdefault(k, "slot:" + stem)
        for stem in data.get("seal_images", []):
            for k in folder_keys(stem):
                self.key2folder.setdefault(k, "seal:" + stem)
        # 4) raid/field boss models: the Digimon exists in the Thai game as a monster
        for folder in self.folders:
            if folder not in playable:
                base = re.sub(r"_(raidboss|boss)(_?re)*\d*$", "", folder)
                for k in folder_keys(base):
                    self.key2folder.setdefault(k, "boss:" + folder)
        self.keys = list(self.key2folder)

    def folder_for(self, names):
        cands = [norm(n) for n in names if n]
        for k in cands:
            if k in self.key2folder:
                return self.key2folder[k], "exact"
        for k in cands:
            if "awaken" in k or "extreme" in k:
                continue   # never guess these: Awaken vs Extreme differ by one word
            m = difflib.get_close_matches(k, self.keys, n=1, cutoff=0.9)
            # only accept spelling noise, not a different Digimon that shares most letters
            if m and abs(len(m[0]) - len(k)) <= 2 and m[0][:4] == k[:4]:
                return self.key2folder[m[0]], "fuzzy"
        return None, None

    def lookup(self, title, aliases=()):
        names = [title, *aliases]
        folder, how = self.folder_for(names)
        base_of = None
        if not folder:
            # (Awaken) / (Extreme) / X forms reuse the base model with new textures
            base = self.VARIANT.sub("", title).strip()
            if base != title:
                folder, how = self.folder_for([base])
                base_of = base if folder else None
        ride = bool(folder) and any(x.startswith("ride") for x in self.folders.get(folder, []))
        return {"folder": folder, "match": how, "via_base": base_of, "can_ride_thai": ride}


if __name__ == "__main__":
    pf = sys.argv[1] if len(sys.argv) > 1 else r"G:\DigimonMastersOnline(Tailand)\Data\pack01.pf"
    data = scan_pack(pf)
    CACHE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"saved {len(data['folders'])} digimon folders -> {CACHE}")
