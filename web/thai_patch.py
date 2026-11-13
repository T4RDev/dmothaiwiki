"""Thai-server patch notes (vplay.in.th) -> structured data for the wiki.

    python web/thai_patch.py            # fetch new patch notes + parse + write web/thai_patch_data.json
    python web/thai_patch.py --pages 3  # only walk the first 3 listing pages (quick update)

Raw pages are cached in output/thai_patches/, so re-runs only download new articles.
"""
import html as H
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / "output" / "thai_patches"
OUT = Path(__file__).resolve().parent / "thai_patch_data.json"
LIST_URL = "https://www.vplay.in.th/category/news/patch-note/"
UA = {"User-Agent": "Mozilla/5.0 (DMO Thai Wiki offline cache)"}


def fetch(url, cache_name=None, refresh=False):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / cache_name if cache_name else None
    if p and p.exists() and not refresh:
        return p.read_text(encoding="utf-8")
    for attempt in range(3):
        try:
            h = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode("utf-8", "replace")
            if p:
                p.write_text(h, encoding="utf-8")
            time.sleep(0.7)  # be polite to the site
            return h
        except Exception as e:  # noqa
            if attempt == 2:
                print("  [fail]", url, e)
                return ""
            time.sleep(2)


def article_body(h):
    m = re.search(r'<div class="entry-content[^"]*"[^>]*>(.*?)<(?:footer|div class="(?:sharedaddy|post-tags|entry-footer))', h, re.S)
    return m.group(1) if m else h


def to_lines(body):
    """WordPress blocks -> one text line per paragraph / cell / heading."""
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", body)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(p|td|th|h\d|li|figcaption|tr|div)>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = H.unescape(s).replace("\xa0", " ")
    out = []
    for l in s.split("\n"):
        l = re.sub(r"[ \t]+", " ", l).strip()
        if l and l != ".":
            out.append(l)
    return out


def list_articles(max_pages=None):
    """Walk the patch-note category pages -> [{url, title, date}] newest first."""
    arts, seen, page, last_page = [], set(), 1, 1
    while True:
        url = LIST_URL if page == 1 else f"{LIST_URL}page/{page}/"
        # the first pages change when a patch is posted; older listing pages are cached
        h = fetch(url, f"_list_{page}.html", refresh=page <= 2)
        if not h:
            break
        nums = [int(x) for x in re.findall(r"/category/news/patch-note/page/(\d+)/", h)]
        last_page = max(nums + [last_page])
        for blk in re.split(r'<div class="masonry-item">', h)[1:]:
            m = re.search(r'<a href="(https://www\.vplay\.in\.th/(?!category/)[^"]+)"[^>]*>([^<]{3,200})</a>', blk)
            d = re.search(r'class="post-date">([\d/]+)', blk)
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                arts.append({"url": m.group(1), "title": H.unescape(m.group(2)).strip(), "date": d.group(1) if d else ""})
        page += 1
        if page > last_page or (max_pages and page > max_pages):
            break
    return arts


def slugify(url):
    s = re.sub(r"^https?://[^/]+/", "", url).strip("/")
    s = urllib.request.unquote(s)
    return re.sub(r"[^\w\-]+", "_", s)[:120] + ".html"


def num(s):
    s = s.replace(",", "").strip()
    return int(s) if re.fullmatch(r"\d+", s) else None


def iso_date(d):
    m = re.match(r"(\d+)/(\d+)/(\d{4})", d or "")
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else ""


PROP = {"ระดับ": "rank", "แปลงร่างเลเวล": "mode_level", "คุณสมบัติ": "attribute", "ธาตุ": "element",
        "ตระกูล": "family", "ประเภทการโจมตี": "attacker_type", "ร่าง": "form"}
STOP = re.compile(r"^(ดิจิมอนใหม่|เพิ่มโหมดขับขี่|เพิ่ม|ปรับ|แก้ไข|กิจกรรม|ข้อมูลอุปกรณ์|ไอเทมใหม่|รายละเอียด|สินค้า|ซัมมอน)")


def parse_article(lines):
    """-> {"digimon": [...], "ride": [...], "unlock": [...]}"""
    out = {"digimon": [], "ride": [], "unlock": []}
    i, n = 0, len(lines)
    while i < n:
        l = lines[i]
        m = re.match(r"^ดิจิมอนใหม่\s*[:：]\s*(.+)$", l)
        if m:
            dg = {"name_th": m.group(1).strip(), "props": {}, "stats": {}, "skills": [], "line": []}
            i += 1
            while i < n and not lines[i].startswith("ดิจิมอนใหม่") and not re.match(r"^(เพิ่มโหมดขับขี่|ปลดโหมดขับขี่)", lines[i]):
                x = lines[i]
                pm = re.match(r"^[–\-•]\s*([^:：]+?)\s*[:：]\s*(.+)$", x)
                if pm and pm.group(1).strip() in PROP:
                    dg["props"][PROP[pm.group(1).strip()]] = pm.group(2).strip()
                elif x in ("HP", "DS", "DE", "AT", "AS", "CT", "HT", "EV", "BL") and i + 1 < n and num(lines[i + 1]) is not None:
                    dg["stats"][x] = num(lines[i + 1])
                    i += 1
                elif x == "เงื่อนไขการวิวัฒนาการ":
                    pass
                elif re.search(r"ใช้ไอเทม\s+(.+?)\s+ปลดช่องวิวัฒนาการ\s+(.+?)(?:\s+ของ\s*(.+))?$", x):
                    um = re.search(r"ใช้ไอเทม\s+(.+?)\s+ปลดช่องวิวัฒนาการ\s+(.+?)(?:\s+ของ\s*(.+))?$", x)
                    out["unlock"].append({"item_th": um.group(1).strip(), "digimon_th": um.group(2).strip(),
                                          "from_th": (um.group(3) or "").strip()})
                elif x == "ข้อมูลสกิล":
                    i += 1
                    while i < n and lines[i] in ("สกิล", "รายละเอียด", "ความเสียหาย"):
                        i += 1
                    while i + 2 < n and num(lines[i + 2]) is not None and not STOP.match(lines[i]):
                        sk = {"name_th": lines[i], "description_th": lines[i + 1], "damage": num(lines[i + 2]), "notes": []}
                        i += 3
                        # extra effect lines ("เมื่อใช้งานสกิล ...") until the next skill triplet
                        while i < n and not (i + 2 < n and num(lines[i + 2]) is not None) \
                                and not STOP.match(lines[i]) and not lines[i].startswith("*") and len(lines[i]) < 160 \
                                and lines[i] not in ("เพิ่มโหมดขับขี่",):
                            sk["notes"].append(lines[i])
                            i += 1
                        dg["skills"].append(sk)
                    continue
                i += 1
            out["digimon"].append(dg)
            continue
        rm = re.match(r"^ปลดโหมดขับขี่ของ\s*(.+?)\s+โดยใช้ไอเทม\s+(.+?)\s*$", l)
        if rm:
            out["ride"].append({"digimon_th": rm.group(1).strip(), "item_th": rm.group(2).strip()})
        i += 1
    return out


def cached_articles():
    """Rebuild the article list from already-downloaded HTML files (offline / site-down safe)."""
    arts = []
    for p in sorted(CACHE.glob("*.html")):
        if p.name.startswith(("_list", "_sample")):
            continue
        h = p.read_text(encoding="utf-8")
        t = re.search(r"<h1[^>]*class=\"[^\"]*entry-title[^\"]*\"[^>]*>(.*?)</h1>", h, re.S) \
            or re.search(r"<title>(.*?)(?:\s*[–-]\s*VPlay)?</title>", h, re.S)
        d = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", h)
        arts.append({"url": "https://www.vplay.in.th/" + p.stem.replace("_", "-") + "/",
                     "title": H.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip() if t else p.stem,
                     "date": d.group(1) if d else "", "_cache": p.name})
    return arts


def _load_existing():
    if OUT.exists():
        try:
            return json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _archived_urls():
    idx_file = BASE / "output" / "thai_patch_archive" / "index.json"
    if not idx_file.exists():
        return set()
    try:
        return {a.get("url") for a in json.loads(idx_file.read_text(encoding="utf-8")) if a.get("url")}
    except Exception:
        return set()


def _fetch_and_parse(a, refresh=False):
    cache_name = a.get("_cache") or slugify(a["url"])
    h = fetch(a["url"], cache_name, refresh=refresh)
    if not h:
        return None
    lines = to_lines(article_body(h))
    data = parse_article(lines)
    return {**{k: v for k, v in a.items() if k != "_cache"}, "date_iso": iso_date(a["date"]), **data}


def sync_latest(max_pages=2, refresh_latest=False):
    """Check the newest listing pages on vplay.in.th and merge only new/changed articles.

    Safe to call periodically from the web server without losing older articles.
    """
    existing = _load_existing()
    by_url = {a["url"]: a for a in existing if a.get("url")}
    archived = _archived_urls()

    # Check page 1 first; only walk further pages if page 1 had brand-new articles
    arts, seen, page, last_page = [], set(), 1, 1
    while True:
        url = LIST_URL if page == 1 else f"{LIST_URL}page/{page}/"
        h = fetch(url, f"_list_{page}.html", refresh=True)
        if not h:
            if page == 1:
                return {"ok": False, "updated": False, "new_count": 0, "new_items": [],
                        "total": len(by_url), "error": "ไม่สามารถเชื่อมต่อ vplay.in.th ได้"}
            break
        nums = [int(x) for x in re.findall(r"/category/news/patch-note/page/(\d+)/", h)]
        last_page = max(nums + [last_page])
        page_new = 0
        for blk in re.split(r'<div class="masonry-item">', h)[1:]:
            m = re.search(r'<a href="(https://www\.vplay\.in\.th/(?!category/)[^"]+)"[^>]*>([^<]{3,200})</a>', blk)
            d = re.search(r'class="post-date">([\d/]+)', blk)
            if m and m.group(1) not in seen:
                u = m.group(1)
                seen.add(u)
                if u not in by_url or u not in archived:
                    page_new += 1
                arts.append({"url": u, "title": H.unescape(m.group(2)).strip(), "date": d.group(1) if d else ""})
        page += 1
        if page > last_page or (max_pages and page > max_pages):
            break
        if page_new == 0 and not refresh_latest:
            break

    if not arts:
        return {"ok": False, "updated": False, "new_count": 0, "new_items": [],
                "total": len(by_url), "error": "ไม่พบรายการบทความจากหน้าเว็บ"}

    new_items, touched_urls = [], set()
    for idx, a in enumerate(arts):
        u = a["url"]
        cache_path = CACHE / slugify(u)
        prev = by_url.get(u)
        is_new = prev is None
        title_changed = bool(prev and a["title"] and prev.get("title") != a["title"])
        need_archive = u not in archived or not cache_path.exists()
        check_edit = refresh_latest and idx < 3

        if not (is_new or title_changed or need_archive or check_edit):
            continue

        rec = _fetch_and_parse(a, refresh=(is_new or title_changed or check_edit or not cache_path.exists()))
        if not rec:
            continue

        if is_new:
            by_url[u] = rec
            touched_urls.add(u)
            new_items.append({"title": rec["title"], "date_iso": rec["date_iso"], "url": u,
                              "has_digimon": any(d.get("skills") or d.get("stats") for d in rec.get("digimon", []))})
        elif title_changed or need_archive or rec != prev:
            by_url[u] = rec
            touched_urls.add(u)

    if not new_items and not touched_urls:
        return {"ok": True, "updated": False, "new_count": 0, "new_items": [], "total": len(by_url)}

    results = sorted(by_url.values(), key=lambda r: (r.get("date_iso", ""), "coming" not in r.get("url", "")))
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    import thai_patch_archive  # noqa: E402
    thai_patch_archive.build(only_urls=touched_urls)

    return {
        "ok": True,
        "updated": True,
        "new_count": len(new_items),
        "new_items": new_items,
        "total": len(results),
    }


def crawl(max_pages=None):
    arts = list_articles(max_pages)
    if not arts:
        arts = cached_articles()
        print(f"[patch] listing unavailable, rebuilding from {len(arts)} cached articles")
    else:
        print(f"[patch] {len(arts)} articles on the list")
    by_url = {a["url"]: a for a in _load_existing() if a.get("url")} if max_pages else {}
    parsed = []
    for a in arts:
        rec = _fetch_and_parse(a)
        if rec:
            parsed.append(rec)
            by_url[rec["url"]] = rec
    results = list(by_url.values()) if max_pages else parsed
    if not results and OUT.exists():
        print("[patch] no articles parsed; keeping existing", OUT.name)
        return json.loads(OUT.read_text(encoding="utf-8"))
    results.sort(key=lambda r: (r["date_iso"], "coming" not in r["url"]))  # oldest first, real update after preview
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    nd = sum(len(r["digimon"]) for r in results)
    print(f"[patch] wrote {OUT.name}: {len(results)} articles, {nd} Digimon blocks, "
          f"{sum(len(r['ride']) for r in results)} ride items, {sum(len(r['unlock']) for r in results)} unlock items")
    return results


if __name__ == "__main__":
    if "--dump" in sys.argv:
        h = (CACHE / "_sample.html").read_text(encoding="utf-8")
        print("\n".join(to_lines(article_body(h))))
    elif "--test" in sys.argv:
        h = (CACHE / "_sample.html").read_text(encoding="utf-8")
        print(json.dumps(parse_article(to_lines(article_body(h))), ensure_ascii=False, indent=1))
    else:
        mp = int(sys.argv[sys.argv.index("--pages") + 1]) if "--pages" in sys.argv else None
        crawl(mp)
        import thai_patch_archive  # full article copy + images for the "แพตช์โน้ต" tab
        thai_patch_archive.build()
