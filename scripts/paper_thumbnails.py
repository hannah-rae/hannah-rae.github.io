#!/usr/bin/env python3
"""Generate paper thumbnails by cropping a figure out of each paper's PDF.

For every selected entry in _data/publications.yml this script:
  1. finds a PDF: from the entry's `paper` link (arXiv, CVF, OpenReview,
     Nature, Frontiers, MDPI, direct PDFs), else an open-access copy listed by
     OpenAlex, else an arXiv preprint with a matching title. A downloaded PDF
     is only used if the paper's title appears on its first pages,
  2. finds the "Figure 1" / "Fig. 1" caption in the first few pages and crops
     the graphics directly above it (falling back to the largest embedded
     image when no caption is found),
  3. saves images/papers/<id>.jpg and adds `thumb_image` to the entry.

By default it processes entries with `recent: true` that have no thumb_image.

Usage (from the repo root):
  pip install -r scripts/requirements.txt
  python scripts/paper_thumbnails.py                 # recent papers missing a thumbnail
  python scripts/paper_thumbnails.py --all           # every paper missing a thumbnail
  python scripts/paper_thumbnails.py ID [ID ...]     # specific entries
  python scripts/paper_thumbnails.py --force ID      # regenerate even if one exists
  python scripts/paper_thumbnails.py --figure 2 ID   # use Figure 2 instead
  python scripts/paper_thumbnails.py --dry-run ...   # write images to /tmp, don't touch the YAML
  python scripts/paper_thumbnails.py --pdf FILE ID   # use a PDF you downloaded yourself

Always look at the result: automatic crops are usually right but not always.
"""
import argparse
import difflib
import io
import json
import re
import sys
import tempfile
import time
import unicodedata
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

import fitz  # PyMuPDF
import yaml
from PIL import Image, ImageChops

REPO = Path(__file__).resolve().parent.parent
PUBS = REPO / "_data" / "publications.yml"
OUT_DIR = REPO / "images" / "papers"
MAX_PAGES = 8          # search for the figure caption in the first N pages
TARGET_WIDTH = 640     # rendered thumbnail width in px (displayed at <=~400px)
UA = "Mozilla/5.0 (compatible; paper-thumbnail-script; +https://hannah-rae.github.io)"


# ---------------------------------------------------------------- PDF lookup
ARXIV_DELAY = 3.5      # seconds between arXiv API calls (arXiv's guidance is >= 3)
_last_arxiv_call = 0.0


def http_get(url, accept=None, timeout=60):
    headers = {"User-Agent": UA}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            # Back off on rate limiting / temporary unavailability, then give up.
            if e.code not in (429, 503) or attempt == 2:
                raise
            retry = e.headers.get("Retry-After", "")
            time.sleep(min(int(retry), 60) if retry.isdigit() else 10 * (attempt + 1))


def norm(s):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).lower())


def doi_of(url):
    m = re.search(r"(10\.\d{4,9}/[^\s?#]+)", url or "")
    return m.group(1).rstrip("/.") if m else None


def direct_candidates(url):
    """Direct-PDF URLs derivable from the paper's own link."""
    if not url:
        return []
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([\w.\-/]+?)(?:\.pdf)?$", url)
    if m:
        return [f"https://arxiv.org/pdf/{m.group(1)}"]
    if "openaccess.thecvf.com" in url and url.endswith(".html"):
        return [url.replace("/html/", "/papers/").replace(".html", ".pdf")]
    m = re.search(r"openreview\.net/forum\?id=([\w\-]+)", url)
    if m:
        return [f"https://openreview.net/pdf?id={m.group(1)}"]
    if re.search(r"nature\.com/articles/[\w.\-]+$", url):
        return [url + ".pdf"]
    if "frontiersin.org" in url:
        return [re.sub(r"/full/?$", "", url) + "/pdf"]
    m = re.search(r"(https?://proceedings\.mlr\.press/v\d+/)([\w\-]+)\.html$", url)
    if m:
        return [f"{m.group(1)}{m.group(2)}/{m.group(2)}.pdf"]
    if "mdpi.com" in url:
        return [url.rstrip("/") + "/pdf"]
    if "climatechange.ai/papers" in url and not url.endswith(".pdf"):
        return [url.rstrip("/") + "/paper.pdf", url]
    return [url]


def openalex_candidates(p):
    """Open-access PDF links from OpenAlex: the DOI's record, plus any record
    with a matching title (preprints such as arXiv copies are separate records)."""
    doi = doi_of(p.get("paper"))
    works = []
    if doi:
        try:
            works.append(json.loads(http_get(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}")))
        except Exception:  # noqa: BLE001
            pass
    try:
        q = urllib.parse.quote(re.sub(r"[^\w\s-]", " ", p["title"])[:200])
        found = json.loads(http_get(f"https://api.openalex.org/works?search={q}&per-page=8"))["results"]
        works += [w for w in found
                  if difflib.SequenceMatcher(None, norm(w.get("title") or ""), norm(p["title"])).ratio() >= 0.9]
    except Exception:  # noqa: BLE001
        pass
    urls = []
    for w in works:
        locs = [w.get("best_oa_location") or {}] + (w.get("locations") or [])
        for loc in locs:
            for k in ("pdf_url", "landing_page_url"):
                u = (loc or {}).get(k)
                if u and (k == "pdf_url" or "arxiv.org" in u) and u not in urls:
                    urls.append(u)
    out = []
    for u in urls:
        out += direct_candidates(u)
    return out


def arxiv_candidates(p):
    """arXiv PDFs whose title closely matches the paper's title."""
    global _last_arxiv_call
    # arXiv does not index stopwords, so AND-ing them matches nothing.
    stop = {"the", "and", "for", "with", "from", "into", "using", "via", "that", "this",
            "are", "our", "its", "how", "does", "what", "when", "where", "toward", "towards"}
    words = [w for w in re.findall(r"[A-Za-z0-9]+", p["title"]) if len(w) > 3 and w.lower() not in stop][:8]
    if not words:
        return []
    q = urllib.parse.quote(" AND ".join(f"ti:{w}" for w in words))
    feed = None
    for attempt in range(4):
        # arXiv asks API clients to wait ~3 s between requests.
        time.sleep(max(0.0, ARXIV_DELAY - (time.time() - _last_arxiv_call)))
        _last_arxiv_call = time.time()
        try:
            feed = http_get(f"https://export.arxiv.org/api/query?search_query={q}&max_results=5").decode()
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 3:
                wait = 10 * (attempt + 1)
                print(f"    arXiv search: rate limited, retrying in {wait}s")
                time.sleep(wait)
                continue
            print(f"    arXiv search failed ({e})")
            return []
        except Exception as e:  # noqa: BLE001
            print(f"    arXiv search failed ({e})")
            return []
    if feed is None:
        return []
    out = []
    for entry in re.findall(r"<entry>(.*?)</entry>", feed, re.S):
        t = re.search(r"<title>(.*?)</title>", entry, re.S)
        i = re.search(r"<id>https?://arxiv\.org/abs/(.*?)</id>", entry)
        if t and i and difflib.SequenceMatcher(None, norm(t.group(1)), norm(p["title"])).ratio() >= 0.9:
            arxiv_id = re.sub(r"v\d+$", "", i.group(1))
            out.append(f"https://arxiv.org/pdf/{arxiv_id}")
    return out


def title_on_first_pages(path, title):
    """Guard against wrong PDFs: the title must appear on the first page(s)."""
    try:
        doc = fitz.open(path)
    except Exception:  # noqa: BLE001
        return False
    text = norm(" ".join(doc[i].get_text() for i in range(min(2, len(doc)))))
    t = norm(title)
    # allow for line-break hyphenation / special characters: require a long prefix
    return t[:40] in text or t[-40:] in text


def fetch_pdf(p, dest, override=None):
    """Try each source in turn; return a description of the source used, or None."""
    if override:
        src = Path(override)
        if src.exists():
            dest.write_bytes(src.read_bytes())
            return f"local file {src}"
        sources = [("--pdf", [override])]
    else:
        sources = [("paper link", direct_candidates(p.get("paper"))),
                   ("OpenAlex", None), ("arXiv search", None)]
    tried = set()
    for name, cands in sources:
        if cands is None:
            cands = openalex_candidates(p) if name == "OpenAlex" else arxiv_candidates(p)
        for cand in cands:
            if cand in tried:
                continue
            tried.add(cand)
            try:
                data = http_get(cand, accept="application/pdf")
            except Exception as e:  # noqa: BLE001
                print(f"    {name}: could not fetch {cand} ({e})")
                continue
            if data[:5] != b"%PDF-":
                print(f"    {name}: {cand} is not a PDF")
                continue
            dest.write_bytes(data)
            if override or title_on_first_pages(dest, p["title"]):
                return f"{name}: {cand}"
            print(f"    {name}: {cand} does not look like this paper (title not on page 1)")
    return None


# ---------------------------------------------------------- figure locating
GAP = 22  # max vertical gap (pt) between pieces of the same figure


def caption_regex(n):
    return re.compile(rf"^\s*(Figure|Fig\.?)\s*{n}\s*[:.|\-–]", re.I)


def area(r):
    return max(r.width, 0) * max(r.height, 0)


def text_lines(page):
    """(rect, text, max font size) for every text line on the page."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            spans = [s for s in ln["spans"] if s["text"].strip()]
            if spans:
                out.append((fitz.Rect(ln["bbox"]), "".join(s["text"] for s in spans),
                            max(s["size"] for s in spans)))
    return out


def find_captions(page, fig_no):
    """Yield (caption rect, caption font size) for 'Figure N' captions."""
    rx = caption_regex(fig_no)
    lines = text_lines(page)
    for i, (r, t, size) in enumerate(lines):
        if rx.match(t):
            cap = fitz.Rect(r)
            for r2, _, s2 in lines[i + 1:]:  # following caption lines
                if abs(s2 - size) < 0.6 and 0 <= r2.y0 - cap.y1 < size * 0.8 and r2.x0 < cap.x1 and r2.x1 > cap.x0:
                    cap |= r2
            yield cap, size


def graphics(page):
    pw = page.rect.width
    items = []
    for d in page.get_drawings():
        r = fitz.Rect(d["rect"])
        if r.is_empty and r.width < 1 and r.height < 1:
            continue
        if r.height < 2 and r.width > 0.5 * pw:  # horizontal page rules
            continue
        if r.width > 0.9 * pw and r.height > 0.9 * page.rect.height:  # page background
            continue
        items.append(r)
    items += [fitz.Rect(i["bbox"]) for i in page.get_image_info()]
    return [r & page.rect for r in items if area(r & page.rect) > 0 or (r.width > 3 or r.height > 3)]


def grow(seed, items):
    """Union `seed` with every item reachable within GAP (repeat until stable)."""
    region = fitz.Rect(seed)
    changed = True
    while changed:
        changed = False
        for r in items:
            if r in region:
                continue
            near = (r.y1 >= region.y0 - GAP and r.y0 <= region.y1 + GAP and
                    r.x1 >= region.x0 - GAP and r.x0 <= region.x1 + GAP)
            if near and not (region.contains(r)):
                new = region | r
                if new != region:
                    region, changed = new, True
    return region


def add_labels(page, region, cap, cap_size):
    """Add small text (axis labels, legends) touching the figure region."""
    base = fitz.Rect(region)  # compare against the graphics only, so text can't chain
    for r, _, size in text_lines(page):
        if r.intersects(cap):
            continue
        inside = base.contains(r)
        touching = r.intersects(base + (-6, -6, 6, 6))
        label_like = size <= cap_size + 0.5 and r.width < 0.4 * base.width
        if inside or (touching and label_like):
            region |= r
    return trim_text_edges(page, region + (-3, -3, 3, 3), base, cap_size)


def trim_text_edges(page, region, base, cap_size):
    """Pull the top/bottom edge back from body text the region cuts into.

    Vector shapes can report bounding boxes larger than what is drawn, which
    stretches the region into neighbouring paragraphs, titles or URLs.
    """
    for r, _, size in text_lines(page):
        if base.contains(r) or not r.intersects(region):
            continue
        # Ignore text that only grazes the region sideways (e.g. the other column
        # of a two-column paper next to a figure that pokes past its column).
        if area(r & region) < 0.6 * area(r):
            continue
        if not (size > cap_size + 0.5 or r.width >= 0.4 * base.width):
            continue
        if r.y1 <= region.y0 + 0.25 * region.height:
            region.y0 = max(region.y0, r.y1 + 1)
        elif r.y0 >= region.y1 - 0.25 * region.height:
            region.y1 = min(region.y1, r.y0 - 1)
    return region


def figure_clip(page, cap, cap_size):
    region = _figure_clip(page, cap, cap_size)
    if region is None:
        return None
    # Keep running headers (text in the top ~9.5% of the page) out of the crop.
    header = [r for r, _, _ in text_lines(page) if r.y1 < page.rect.y0 + 0.095 * page.rect.height]
    if header:
        region.y0 = max(region.y0, max(r.y1 for r in header) + 1)
    return region if region.height > 40 else None


def _figure_clip(page, cap, cap_size):
    pw = page.rect.width
    items = graphics(page)
    full = cap.width > 0.6 * pw
    span = (page.rect.x0, page.rect.x1) if full else (cap.x0 - 15, cap.x1 + 15)

    # 1) Figure above the caption (the usual layout).
    above = [r for r in items if r.y1 <= cap.y0 + 2 and r.x1 > span[0] and r.x0 < span[1]]
    seeds = [r for r in above if cap.y0 - r.y1 < GAP * 2]
    if seeds:
        region = fitz.Rect()
        for s in seeds:
            region |= s
        region = grow(region, [r for r in above if r.y1 <= cap.y0 + 2])
        if not full:
            # A column-width caption means a column-width figure: don't let shapes
            # that poke past the column edge pull in the neighbouring column.
            region.x0, region.x1 = max(region.x0, span[0]), min(region.x1, span[1])
        region = add_labels(page, region, cap, cap_size)
        if not full:
            region.x0, region.x1 = max(region.x0, span[0]), min(region.x1, span[1])
        if region.height > 40 and region.width > 80:
            return region & fitz.Rect(page.rect.x0, page.rect.y0, page.rect.x1, cap.y0 - 1)

    # 2) Side caption: graphics alongside the caption.
    beside = [r for r in items if r.y1 > cap.y0 - GAP and r.y0 < cap.y1 + GAP and not cap.contains(r)]
    if beside:
        region = fitz.Rect()
        for s in beside:
            region |= s
        region = grow(region, [r for r in items if not cap.intersects(r)])
        region = add_labels(page, region, cap, cap_size)
        region = region & page.rect
        if cap.x0 >= region.x0 + region.width / 2:   # caption on the right
            region.x1 = min(region.x1, cap.x0 - 1)
        elif cap.x1 <= region.x1 - region.width / 2:  # caption on the left
            region.x0 = max(region.x0, cap.x1 + 1)
        if region.height > 40 and region.width > 80:
            return region
    return None


def find_figure(doc, fig_no):
    for pno in range(min(MAX_PAGES, len(doc))):
        page = doc[pno]
        for cap, size in find_captions(page, fig_no):
            clip = figure_clip(page, cap, size)
            if clip:
                return page, clip, f"Figure {fig_no} on page {pno + 1}"
    # Fallback 1: largest embedded raster image in the first pages.
    best = None
    for pno in range(min(MAX_PAGES, len(doc))):
        for info in doc[pno].get_image_info():
            r = fitz.Rect(info["bbox"]) & doc[pno].rect
            if best is None or area(r) > area(best[1]):
                best = (doc[pno], r, f"largest image on page {pno + 1}")
    if best and area(best[1]) > 0.05 * area(doc[0].rect):
        return best
    # Fallback 2: the top of the first page (title and start of the abstract),
    # for papers without figures (e.g. table-only papers) or scanned PDFs.
    page = doc[0]
    r = page.rect
    return page, fitz.Rect(r.x0 + 0.06 * r.width, r.y0 + 0.05 * r.height,
                           r.x1 - 0.06 * r.width, r.y0 + 0.42 * r.height), "top of first page"


def render(page, clip):
    zoom = TARGET_WIDTH / max(clip.width, 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    # Trim surrounding whitespace, keep a small margin.
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bbox = ImageChops.difference(img, bg).convert("L").point(lambda v: 255 if v > 12 else 0).getbbox()
    if bbox:
        pad = 12
        bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0),
                min(bbox[2] + pad, img.width), min(bbox[3] + pad, img.height))
        img = img.crop(bbox)
    return img


# ------------------------------------------------------------- YAML update
def set_thumb(yml_text, pid, path):
    """Insert/replace `thumb_image` in entry `pid`, preserving file layout."""
    lines = yml_text.split("\n")
    start = next(i for i, l in enumerate(lines) if l == f"- id: {pid}")
    end = start + 1
    while end < len(lines) and lines[end].startswith("  "):
        end += 1
    entry = lines[start:end]
    new = f'  thumb_image: "{path}"'
    for i, l in enumerate(entry):
        if l.startswith("  thumb_image:"):
            entry[i] = new
            break
    else:
        at = next((i for i, l in enumerate(entry) if l.startswith("  bibtex:")), len(entry))
        entry.insert(at, new)
    return "\n".join(lines[:start] + entry + lines[end:])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="publication ids (default: recent papers)")
    ap.add_argument("--all", action="store_true", help="every paper")
    ap.add_argument("--force", action="store_true", help="overwrite existing thumbnails")
    ap.add_argument("--figure", type=int, default=1, help="figure number to use (default 1)")
    ap.add_argument("--dry-run", action="store_true", help="write to a temp dir, don't edit YAML")
    ap.add_argument("--pdf", help="PDF to use (local path or URL); requires exactly one id")
    args = ap.parse_args()
    if args.pdf and len(args.ids) != 1:
        sys.exit("--pdf needs exactly one publication id")

    pubs = yaml.safe_load(PUBS.read_text())
    if args.ids:
        sel = [p for p in pubs if p["id"] in args.ids]
        missing = set(args.ids) - {p["id"] for p in sel}
        if missing:
            sys.exit(f"unknown ids: {', '.join(sorted(missing))}")
    else:
        sel = [p for p in pubs if args.all or p.get("recent")]
    if not args.force:
        sel = [p for p in sel if not p.get("thumb_image")]
    if not sel:
        print("Nothing to do (use --force to regenerate existing thumbnails).")
        return

    out_dir = Path(tempfile.mkdtemp(prefix="thumbs-")) if args.dry_run else OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    yml_text = PUBS.read_text()
    skipped = []
    with tempfile.TemporaryDirectory(prefix="paper-pdfs-") as tmp:
        for p in sel:
            print(f"{p['id']}: {p.get('paper') or '(no link)'}")
            pdf = Path(tmp) / f"{p['id']}.pdf"
            source = fetch_pdf(p, pdf, args.pdf)
            if not source:
                print("    skipped: no PDF found (pass one with --pdf)")
                skipped.append(p["id"])
                continue
            print(f"    using {source}")
            try:
                doc = fitz.open(pdf)
            except Exception as e:  # noqa: BLE001
                print(f"    skipped: unreadable PDF ({e})")
                continue
            try:
                found = find_figure(doc, args.figure)
                if not found:
                    print("    skipped: no figure found (try --figure 2)")
                    skipped.append(p["id"])
                    continue
                page, clip, how = found
                out = out_dir / f"{p['id']}.jpg"
                render(page, clip).save(out, "JPEG", quality=85, optimize=True, progressive=True)
            except Exception as e:  # noqa: BLE001
                print(f"    skipped: {e}")
                continue
            print(f"    saved {out} ({how})")
            if not args.dry_run:
                yml_text = set_thumb(yml_text, p["id"], f"/images/papers/{p['id']}.jpg")
    if skipped:
        print(f"\nNo thumbnail for {len(skipped)}: {' '.join(skipped)}")
    if not args.dry_run:
        PUBS.write_text(yml_text)
        print(f"Updated {PUBS.relative_to(REPO)}. Review the images before committing.")
    else:
        print(f"Dry run: images in {out_dir}")


if __name__ == "__main__":
    main()
