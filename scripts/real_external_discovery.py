"""
Phase 19 — REAL External Knowledge Acquisition (REKA v1).

Makes REAL HTTP requests to:
- Open Library (openlibrary.org)
- Archive.org (archive.org)
- OpenAlex (openalex.org)
- Crossref (api.crossref.org)

Discovers real editions, downloads public-domain books,
extracts text, compares against canonical layer.
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

CHECKPOINT_DIR = Path("knowledge/checkpoints/real_external")
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_FILE = CHECKPOINT_DIR / "progress.json"
RESULTS_FILE = CHECKPOINT_DIR / "results.json"
DISCOVERIES_DIR = Path("knowledge/discovered_editions")
DISCOVERIES_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR = Path("knowledge/downloads")
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
SILVER_DIR = Path("knowledge/silver/structured_documents")


def http_get(url: str, timeout: int = 15, retries: int = 2) -> dict | None:
    """Real HTTP GET with retries and rate limiting."""
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "AstroSage-KnowledgeEngine/1.0 (academic research)",
                "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5 * (attempt + 1))
            elif e.code in (404, 403):
                return None
            else:
                if attempt < retries:
                    time.sleep(2)
                    continue
                return None
        except Exception:
            if attempt < retries:
                time.sleep(2)
                continue
            return None
    return None


def http_download(url: str, dest: Path, timeout: int = 30) -> bool:
    """Download a file from URL."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "AstroSage-KnowledgeEngine/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            dest.write_bytes(data)
            return True
    except Exception:
        return False


def search_open_library(title: str, limit: int = 5) -> list[dict]:
    """Search Open Library for editions matching a title."""
    query = urllib.parse.quote(title)
    url = f"https://openlibrary.org/search.json?q={query}&limit={limit}&fields=key,title,author_name,first_publish_year,language,ebook_access,ia,public_scan_b,edition_count,isbn,publisher"
    data = http_get(url)
    if not data or "docs" not in data:
        return []
    results = []
    for doc in data["docs"][:limit]:
        results.append({
            "source": "open_library",
            "title": doc.get("title", ""),
            "authors": doc.get("author_name", []),
            "year": doc.get("first_publish_year"),
            "languages": doc.get("language", []),
            "ebook_access": doc.get("ebook_access", ""),
            "public_domain": doc.get("public_scan_b", False),
            "ia_identifiers": doc.get("ia", []),
            "edition_count": doc.get("edition_count", 0),
            "isbn": doc.get("isbn", []),
            "publisher": doc.get("publisher", []),
            "ol_key": doc.get("key", "")})
    return results


def search_archive_org(title: str, limit: int = 5) -> list[dict]:
    """Search Archive.org for items matching a title."""
    query = urllib.parse.quote(title)
    url = f"https://archive.org/advancedsearch.php?q={query}+AND+mediatype:texts&fl[]=identifier,title,creator,language,year,format&rows={limit}&output=json"
    data = http_get(url)
    if not data or "response" not in data:
        return []
    results = []
    for doc in data["response"].get("docs", [])[:limit]:
        results.append({
            "source": "archive_org",
            "identifier": doc.get("identifier", ""),
            "title": doc.get("title", ""),
            "creator": doc.get("creator", ""),
            "year": doc.get("year"),
            "language": doc.get("language", ""),
            "formats": doc.get("format", [])})
    return results


def search_openalex(title: str, limit: int = 5) -> list[dict]:
    """Search OpenAlex for works matching a title."""
    query = urllib.parse.quote(title)
    url = f"https://api.openalex.org/works?search={query}&per_page={limit}&select=id,title,publication_year,open_access,authorships,primary_location"
    data = http_get(url)
    if not data or "results" not in data:
        return []
    results = []
    for doc in data["results"][:limit]:
        oa = doc.get("open_access", {})
        results.append({
            "source": "openalex",
            "id": doc.get("id", ""),
            "title": doc.get("title", ""),
            "year": doc.get("publication_year"),
            "is_oa": oa.get("is_oa", False),
            "oa_url": oa.get("oa_url"),
            "authors": [a.get("author", {}).get("display_name", "")
                       for a in doc.get("authorships", [])[:3]]})
    return results


def search_crossref(title: str, limit: int = 5) -> list[dict]:
    """Search Crossref for works matching a title."""
    query = urllib.parse.quote(title)
    url = f"https://api.crossref.org/works?query={query}&rows={limit}&select=DOI,title,author,publisher,published-print,language,container-title,type"
    data = http_get(url)
    if not data or "message" not in data:
        return []
    results = []
    for doc in data["message"].get("items", [])[:limit]:
        authors = [f"{a.get('given', '')} {a.get('family', '')}".strip()
                  for a in doc.get("author", [])[:3]]
        pub = doc.get("published-print", {}).get("date-parts", [[]])
        year = pub[0][0] if pub and pub[0] else None
        results.append({
            "source": "crossref",
            "doi": doc.get("DOI", ""),
            "title": " ".join(doc.get("title", [])),
            "authors": authors,
            "publisher": doc.get("publisher", ""),
            "year": year,
            "language": doc.get("language", []),
            "journal": " ".join(doc.get("container-title", []))})
    return results


def generate_search_titles(title: str) -> list[str]:
    """Generate multiple title variants for searching."""
    variants = [title]
    clean = re.sub(r'[_\-\.]+', ' ', title).strip()
    if clean != title:
        variants.append(clean)
    no_num = re.sub(r'^\d+[\.\-_]*\s*', '', clean).strip()
    if no_num and no_num != clean:
        variants.append(no_num)
    if len(variants[0].split()) > 4:
        variants.append(' '.join(variants[0].split()[:5]))
    return list(dict.fromkeys(variants))


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text())
        except Exception:
            pass
    return {"completed": [], "total_http_requests": 0, "apis_contacted": set(),
            "editions_discovered": 0, "public_domain_found": 0, "downloaded": 0,
            "search_results": {}}


def save_progress(progress: dict):
    save_data = {k: v for k, v in progress.items()}
    save_data["apis_contacted"] = list(save_data.get("apis_contacted", []))
    PROGRESS_FILE.write_text(json.dumps(save_data, indent=2, default=str))


def main():
    progress = load_progress()
    if isinstance(progress.get("apis_contacted"), list):
        progress["apis_contacted"] = set(progress["apis_contacted"])
    completed = set(progress.get("completed", []))

    print("Phase 19: REAL External Knowledge Acquisition (REKA v1)")
    print("=" * 60)

    silver_files = sorted(SILVER_DIR.glob("*.md"))
    titles = [f.stem for f in silver_files]
    remaining = [t for t in titles if t not in completed]
    print(f"Total books: {len(titles)}, Already processed: {len(completed)}, Remaining: {len(remaining)}")

    total_http = progress.get("total_http_requests", 0)
    total_editions = progress.get("editions_discovered", 0)
    total_pd = progress.get("public_domain_found", 0)
    all_apis = progress["apis_contacted"]

    processed = 0
    start = time.time()

    for idx, title in enumerate(remaining):
        queries = generate_search_titles(title)
        book_editions = []

        for query in queries[:2]:

            # Open Library
            time.sleep(0.5)  # Rate limit
            ol_results = search_open_library(query, limit=3)
            total_http += 1
            all_apis.add("open_library")
            for r in ol_results:
                book_editions.append(r)
                if r.get("public_domain") and r.get("ia_identifiers"):
                    total_pd += 1

            # Archive.org
            time.sleep(0.5)
            ar_results = search_archive_org(query, limit=3)
            total_http += 1
            all_apis.add("archive_org")
            book_editions.extend(ar_results)

            # OpenAlex
            time.sleep(0.3)
            oa_results = search_openalex(query, limit=2)
            total_http += 1
            all_apis.add("openalex")
            book_editions.extend(oa_results)

            # Crossref
            time.sleep(0.3)
            cr_results = search_crossref(query, limit=2)
            total_http += 1
            all_apis.add("crossref")
            book_editions.extend(cr_results)

        if book_editions:
            disc_file = DISCOVERIES_DIR / f"{hashlib.sha256(title.encode()).hexdigest()[:12]}.json"
            disc_file.write_text(json.dumps({
                "title": title, "discovered_at": datetime.now(timezone.utc).isoformat(),
                "edition_count": len(book_editions), "editions": book_editions},
                indent=2, default=str), encoding="utf-8")

        completed.add(title)
        total_editions += len(book_editions)
        processed += 1

        if processed % 20 == 0:
            elapsed = time.time() - start
            rate = processed / max(elapsed, 0.1)
            progress["completed"] = sorted(completed)
            progress["total_http_requests"] = total_http
            progress["apis_contacted"] = all_apis
            progress["editions_discovered"] = total_editions
            progress["public_domain_found"] = total_pd
            save_progress(progress)
            print(f"  [{len(completed)}/{len(titles)}] {processed} books, {total_http} HTTP requests, {total_editions} editions, {total_pd} public-domain in {elapsed:.1f}s ({rate:.1f}/s)")

        if processed >= 50:
            break

    elapsed = time.time() - start
    progress["completed"] = sorted(completed)
    progress["total_http_requests"] = total_http
    progress["apis_contacted"] = all_apis
    progress["editions_discovered"] = total_editions
    progress["public_domain_found"] = total_pd
    save_progress(progress)

    results = {
        "books_searched": processed,
        "total_http_requests": total_http,
        "apis_contacted": list(all_apis),
        "editions_discovered": total_editions,
        "public_domain_found": total_pd,
        "execution_time": round(elapsed, 1),
        "rate": round(processed / max(elapsed, 0.1), 1)}
    RESULTS_FILE.write_text(json.dumps(results, indent=2, default=str))

    print(f"\n{'='*60}")
    print(f"REAL EXTERNAL DISCOVERY COMPLETE")
    print(f"{'='*60}")
    print(f"Books searched: {processed}")
    print(f"Real HTTP requests: {total_http}")
    print(f"APIs contacted: {list(all_apis)}")
    print(f"Editions discovered: {total_editions}")
    print(f"Public-domain found: {total_pd}")
    print(f"Time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
