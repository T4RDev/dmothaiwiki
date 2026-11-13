"""
Parse dmowiki's free-text effect sections into structured data:

  F3 Special Buff - Final Xros Blade        -> skill_effects: [{slot, skill, name, fields:[[label, value]]}]
  Power of Code Crown
  Activation / : 100%
  Duration / : 30 seconds
  Buff Effect / : Absorbs 150000 Damage ...

  Rank Passives:                            -> rank_passives: [{group, fields:[[label, value]]}]
  Data: / Stack Effect: / Attack 10% ... / Duration: / 10s / Activation: / 50% on Normal Attack.

  Overview / Pros: ... / Cons: ...          -> overview: {pros:[...], cons:[...]}
"""
import re

HEAD = re.compile(r"^(F\d)\s+(?:Special\s+)?(Buff|Debuff|Effect)(?:\s+Effect)?\s*(?:[-:]\s*(.*))?$", re.I)
INLINE = re.compile(r"^(F\d)\s+(?:Special\s+)?(?:Buff|Debuff)?\s*Effect\s*:\s*(.+)$", re.I)
LABELS = {
    "activation": "Activation", "duration": "Duration", "buff effect": "Buff Effect",
    "debuff effect": "Debuff Effect", "effect": "Effect", "stack effect": "Stack Effect",
    "obs": "Note", "note": "Note", "cooldown": "Cooldown", "max stack": "Max Stack",
}
STOP = ("Rank Passives:", "Categories", "Overview", "Promo Banner", "Promo Art", "Gallery", "Trivia", "Notes", "Hatching")
GROUPS = {"Vaccine", "Virus", "Data", "Unknown", "Free", "Fire", "Water", "Ice", "Wind", "Thunder", "Land",
          "Earth", "Wood", "Steel", "Light", "Darkness", "Pitch Black", "Neutral"}


def _label(line):
    key = line.rstrip(":").strip().lower()
    return LABELS.get(key)


def _value(lines, i):
    """Value lines after a label: ': 100%' or a plain line; joins continuation fragments."""
    vals = []
    while i < len(lines):
        l = lines[i]
        if _label(l) or HEAD.match(l) or l in STOP or l.rstrip(":") in GROUPS:
            break
        vals.append(l.lstrip(":").strip())
        i += 1
        if vals and len(vals[-1]) > 2 and not vals[-1].endswith((",", "(", "-")):
            break
    return " ".join(v for v in vals if v), i


def parse_effects(text: str) -> dict:
    lines = [re.sub(r"\s+", " ", l.replace("\xa0", " ")).strip() for l in (text or "").split("\n")]
    lines = [l for l in lines if l]
    skill_effects, rank_passives = [], []
    overview = {"pros": [], "cons": []}

    i = 0
    while i < len(lines):
        l = lines[i]
        m_inline = INLINE.match(l)
        m = HEAD.match(l) if len(l) < 90 else None
        if m_inline and not m:
            skill_effects.append({"slot": m_inline.group(1).upper(), "skill": "", "name": "",
                                  "fields": [["Effect", m_inline.group(2).strip()]]})
            i += 1
            continue
        if m:
            skill = (m.group(3) or "").strip(" -:")
            i += 1
            if not skill and i < len(lines) and not _label(lines[i]):
                skill = lines[i]; i += 1
            eff = {"slot": m.group(1).upper(), "skill": skill, "name": "", "fields": []}
            while i < len(lines) and not HEAD.match(lines[i]) and lines[i] not in STOP:
                lab = _label(lines[i])
                if lab:
                    val, i = _value(lines, i + 1)
                    if val:
                        eff["fields"].append([lab, val])
                elif not eff["fields"] and not eff["name"] and len(lines[i]) < 60:
                    eff["name"] = lines[i]; i += 1
                else:
                    break
            if eff["fields"]:
                skill_effects.append(eff)
            continue
        if l == "Rank Passives:":
            i += 1
            group = None
            while i < len(lines) and lines[i] not in STOP:
                g = lines[i].rstrip(":").strip()
                if g in GROUPS:
                    group = {"group": g, "fields": []}
                    rank_passives.append(group)
                    i += 1
                    continue
                lab = _label(lines[i])
                if lab and group is not None:
                    val, i = _value(lines, i + 1)
                    if val:
                        group["fields"].append([lab, val])
                    continue
                if group is not None and lines[i].startswith(":"):
                    group["fields"].append(["Effect", lines[i].lstrip(": ").strip()])
                elif group is not None and not group["fields"] and len(lines[i]) > 8:
                    group["fields"].append(["Effect", lines[i]])
                i += 1
            continue
        if l == "Overview":
            i += 1
            bucket = None
            end_words = ("Categories", "Promo Banner", "Promo Art", "See also", "See also:", "Developer Conceptual Art",
                         "Teaser", "Official Art", "Model changes", "Digimon Preview", "Hatching", "Old Aura Effect",
                         "Mega counterpart", "Best Combo", "Recommended build:", "Gallery", "Trivia")
            while i < len(lines) and lines[i] not in end_words and not lines[i].startswith("It's a "):
                if lines[i] == "Pros:":
                    bucket = "pros"
                elif lines[i] == "Cons:":
                    bucket = "cons"
                elif bucket:
                    cur = overview[bucket]
                    frag = lines[i]
                    # wiki links split sentences into fragments; glue short pieces back on
                    prev = cur[-1].rstrip() if cur else ""
                    joins = (prev.endswith(("(", ",", " of", " through", " from", " the", " and", " to", " in",
                                            " than", " as", " into", " or", " including", " Digivolve into"))
                             or prev in ("Requires", "Require", "Easily obtainable through", "Does not require"))
                    if cur and (frag[:1] in ",.)" or frag[:1].islower() or joins):
                        cur[-1] = (cur[-1] + " " + frag).replace(" ,", ",").replace(" .", ".")
                    else:
                        cur.append(frag)
                i += 1
            continue
        i += 1
    return {"skill_effects": skill_effects, "rank_passives": rank_passives, "overview": overview}
