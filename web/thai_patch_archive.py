"""Full offline copy of every Thai-server patch note (vplay.in.th) for the wiki's "แพตช์โน้ต" tab.

    python web/thai_patch_archive.py     # uses the HTML cache made by thai_patch.py, downloads images

Output:
    output/thai_patch_archive/index.json      list of articles (newest first)
    output/thai_patch_archive/<post_id>.html  cleaned article body (dark-theme friendly classes)
    output/images/patch/<file>                every image used in the articles
"""
import concurrent.futures as cf
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup, Comment

sys.path.insert(0, str(Path(__file__).resolve().parent))
import thai_patch as T  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
ARCH = BASE / "output" / "thai_patch_archive"
IMG_DIR = BASE / "output" / "images" / "patch"
IMG_URL = "/images/patch/"

COLOR = {"vivid-purple": "c-purple", "vivid-red": "c-red", "luminous-vivid-orange": "c-orange",
         "luminous-vivid-amber": "c-amber", "vivid-cyan-blue": "c-blue", "pale-cyan-blue": "c-cyan",
         "vivid-green-cyan": "c-green", "light-green-cyan": "c-green", "pale-pink": "c-pink",
         "cyan-bluish-gray": "c-gray"}
DROP_BLOCKS = ("bp-bottom-meta", "seil-more-posts", "seil-share", "sharedaddy", "seil-related")
KEEP_ATTR = {
    "a": ["href"],
    "img": ["src", "alt"],
    "video": ["src", "poster", "controls", "autoplay", "loop", "muted", "playsinline", "preload"],
    "source": ["src", "type"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
}


def img_name(url):
    p = urllib.parse.urlparse(url).path
    m = re.search(r"/uploads/(.+)$", p)
    name = (m.group(1) if m else p.strip("/")).replace("/", "_")
    return re.sub(r"[^\w.\-]", "_", urllib.parse.unquote(name))


def classes_for(el):
    out = []
    cls = el.get("class") or []
    style = el.get("style") or ""
    for c in cls:
        m = re.match(r"has-(.+)-color$", c)
        if m and m.group(1) in COLOR:
            out.append(COLOR[m.group(1)])
        m = re.match(r"has-(.+)-background-color$", c)
        if m:
            out.append("band" if m.group(1) in ("black", "contrast", "vivid-purple") else "band-soft")
        if c == "has-text-align-center" or c == "aligncenter":
            out.append("ta-c")
        if c == "has-text-align-right":
            out.append("ta-r")
        if c in ("has-large-font-size", "has-x-large-font-size"):
            out.append("fs-l")
        if c == "has-medium-font-size":
            out.append("fs-m")
        if c == "wp-block-columns":
            out.append("cols")
        if c == "wp-block-column":
            out.append("col")
        if c == "wp-block-table":
            out.append("pt-table")
    fs = re.search(r"font-size:\s*(\d+)px", style)
    if fs and int(fs.group(1)) >= 24:
        out.append("fs-xl")
    elif fs and int(fs.group(1)) >= 18:
        out.append("fs-l")
    if el.name == "td" and "has-text-align-center" in cls:
        out.append("ta-c")
    return out


def clean(post, images):
    for c in post.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    for bad in post.find_all(["script", "style", "noscript", "form", "button", "svg"]):
        bad.decompose()
    for blk in post.find_all(True, class_=lambda c: c and any(x in c for x in DROP_BLOCKS)):
        blk.decompose()
    for ifr in post.find_all("iframe"):
        src = ifr.get("src") or ""
        a = post.new_tag("a", href=src)
        a.string = "▶ เปิดวิดีโอ (ต้องต่ออินเทอร์เน็ต)"
        p = post.new_tag("p")
        p.append(a)
        ifr.replace_with(p)
    for img in post.find_all("img"):
        src = img.get("data-src") or img.get("data-lazy-src") or img.get("src") or ""
        if src.startswith("//"):
            src = "https:" + src
        if src.startswith("http"):
            name = img_name(src)
            images[name] = src
            img["src"] = IMG_URL + name
            img["loading"] = "lazy"
    for vid in post.find_all("video"):
        for attr in ("src", "poster"):
            src = vid.get(attr) or ""
            if src.startswith("//"):
                src = "https:" + src
            if src.startswith("http"):
                name = img_name(src)
                images[name] = src
                vid[attr] = IMG_URL + name
        vid["controls"] = ""
        vid["playsinline"] = ""
        if "preload" not in vid.attrs:
            vid["preload"] = "metadata"
    for src_el in post.find_all("source"):
        src = src_el.get("src") or ""
        if src.startswith("//"):
            src = "https:" + src
        if src.startswith("http"):
            name = img_name(src)
            images[name] = src
            src_el["src"] = IMG_URL + name
    for el in post.find_all(True):
        new_cls = classes_for(el)
        style = el.get("style") or ""
        fb = re.search(r"flex-basis:\s*([\d.]+%)", style)
        keep = {k: el.get(k) for k in KEEP_ATTR.get(el.name, []) if k in el.attrs and el.get(k) is not None}
        if el.name == "img":
            keep["loading"] = "lazy"
        if el.name == "a" and keep.get("href", "").startswith("http"):
            keep["target"] = "_blank"
            keep["rel"] = "noopener"
        el.attrs = keep
        if new_cls:
            el["class"] = " ".join(dict.fromkeys(new_cls))
        if fb and "col" in new_cls:
            el["style"] = f"flex-basis:{fb.group(1)}"
    # empty "." spacer paragraphs
    for p in post.find_all("p"):
        if p.get_text(strip=True) in ("", ".") and not p.find(["img", "video"]):
            p.decompose()
    return "".join(str(c) for c in post.contents).strip()


def kind_of(title, url):
    t = title.lower()
    if "coming soon" in t:
        return "coming"
    if "รายละเอียดการอัพเดท" in title or "อัพเดท" in title:
        return "update"
    if "แก้ไข" in title or "fix" in t:
        return "fix"
    return "other"


def download(name, url):
    dest = IMG_DIR / name
    if dest.exists() and dest.stat().st_size > 0:
        return True
    is_vid = name.lower().endswith((".mp4", ".webm", ".mov", ".m4v"))
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    try:
        u = urllib.parse.urlsplit(url)  # Thai file names must be percent-encoded
        url = urllib.parse.urlunsplit((u.scheme, u.netloc, urllib.parse.quote(urllib.parse.unquote(u.path)), u.query, ""))
        with urllib.request.urlopen(urllib.request.Request(url, headers=T.UA), timeout=120 if is_vid else 40) as resp:
            tmp.write_bytes(resp.read())
        tmp.replace(dest)
        return True
    except Exception as e:  # noqa
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        print("  [media fail]", url, e)
        return False


def build(only_urls=None):
    ARCH.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(T.OUT.read_text(encoding="utf-8")) if T.OUT.exists() else []
    meta_by_url = {a["url"]: a for a in data}
    arts = list(meta_by_url.values()) or T.cached_articles()

    idx_path = ARCH / "index.json"
    existing_idx = {}
    if only_urls and idx_path.exists():
        try:
            existing_idx = {x["url"]: x for x in json.loads(idx_path.read_text(encoding="utf-8")) if x.get("url")}
        except Exception:
            existing_idx = {}

    images, index = {}, []
    for a in arts:
        u = a["url"]
        if only_urls is not None and u not in only_urls and u in existing_idx:
            old = existing_idx[u]
            if old.get("id") and (ARCH / f"{old['id']}.html").exists():
                index.append(old)
                continue
        cache = a.get("_cache") or T.slugify(u)
        p = T.CACHE / cache
        if not p.exists():
            continue
        soup = BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser")
        post = soup.select_one("div.seil-blog-post")
        if not post:
            continue
        pid = (post.get("id") or "").replace("post-", "") or re.sub(r"\W", "", cache)[:40]
        title = re.sub(r"\s*[–-]\s*VPlay\s*$", "", a.get("title") or "").strip()
        body = clean(post, images)
        (ARCH / f"{pid}.html").write_text(body, encoding="utf-8")
        text = BeautifulSoup(body, "html.parser").get_text(" ", strip=True)
        index.append({
            "id": pid, "title": title, "date": a.get("date", ""), "date_iso": a.get("date_iso") or T.iso_date(a.get("date", "")),
            "url": u, "kind": kind_of(title, u),
            "digimon": [d["name_th"] for d in a.get("digimon", []) if d.get("skills") or d.get("stats")],
            "chars": len(text), "images": body.count("<img"), "videos": body.count("<video"), "search": text,
        })
    index.sort(key=lambda x: (x["date_iso"], x["kind"] != "coming"), reverse=True)
    idx_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    print(f"[archive] {len(index)} articles -> {ARCH}")
    todo = list(images.items())
    if todo:
        print(f"[archive] {len(todo)} media files -> {IMG_DIR}")
        ok = 0
        with cf.ThreadPoolExecutor(max_workers=6) as ex:
            for r in ex.map(lambda kv: download(*kv), todo):
                ok += bool(r)
        print(f"[archive] media ok {ok}/{len(todo)}")


if __name__ == "__main__":
    build()
