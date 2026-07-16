#!/usr/bin/env python3
"""
Search Archive.org for Hindu scripture editions
"""
import json
import requests
import time
from pathlib import Path
from urllib.parse import quote_plus

BASE_URL = "https://archive.org/advancedsearch.php"

SCRIPTURE_SEARCH_TERMS = {
    "RV": ["rigveda", "rgveda", "ऋग्वेद", "ऋग्वेदसंहिता", "rig veda samhita", "rigveda samhita"],
    "SV": ["samaveda", "samaveda samhita", "सामवेद"],
    "YVK": ["yajurveda krishna", "yajurveda krsna", "कृष्ण यजुर्वेद", "taittiriya samhita"],
    "YVS": ["yajurveda shukla", "yajurveda sukla", "शुक्ल यजुर्वेद", "vajasaneyi samhita"],
    "AV": ["atharvaveda", "atharva veda", "अथर्ववेद"],
    "BG": ["bhagavad gita", "bhagavadgita", "भगवद्गीता", "gita press bhagavad gita"],
    "MBH": ["mahabharata", "mahabharat", "महाभारत", "bori mahabharata", "critical edition mahabharata"],
    "RM": ["ramayana", "ramayan", "रामायण", "valmiki ramayana"],
    "HV": ["harivamsha", "harivamsa", "हरिवंश"],
    "BHAG": ["bhagavata purana", "bhagavat purana", "भागवत पुराण", "srimad bhagavatam"],
    "VISH": ["vishnu purana", "विष्णु पुराण"],
    "SHIV": ["shiva purana", "शिव पुराण"],
    "DEVI": ["devi bhagavata", "devi bhagavat", "देवी भागवत"],
    "AGNI": ["agni purana", "अग्नि पुराण"],
    "MATS": ["matsya purana", "मत्स्य पुराण"],
    "KURM": ["kurma purana", "कूर्म पुराण"],
    "LING": ["linga purana", "लिङ्ग पुराण"],
    "MARK": ["markandeya purana", "मार्कण्डेय पुराण"],
    "NARADA": ["narada purana", "नारद पुराण"],
    "VAMAN": ["vamana purana", "वामन पुराण"],
    "VARAH": ["varaha purana", "वराह पुराण"],
    "VYU": ["vayu purana", "वायु पुराण"],
    "SKAND": ["skanda purana", "स्कन्द पुराण"],
    "BRAHMD": ["brahmanda purana", "ब्रह्माण्ड पुराण"],
    "KALI": ["kalika purana", "कालिका पुराण"],
    "GARUDA": ["garuda purana", "गरुड पुराण"],
}

def search_archive_org(query: str, rows: int = 50, page: int = 1) -> dict:
    """Search Archive.org"""
    params = {
        'q': query,
        'fl[]': 'identifier,title,creator,date,mediatype,collection,format,subject,language',
        'rows': rows,
        'page': page,
        'output': 'json',
        'sort[]': 'downloads desc'
    }
    url = BASE_URL + '?' + '&'.join(f"{k}={quote_plus(str(v))}" for k, v in params.items())
    try:
        resp = requests.get(url, timeout=30)
        return resp.json()
    except Exception as e:
        print(f"Search error: {e}")
        return {"response": {"numFound": 0, "docs": []}}

def search_scripture(scripture_id: str, rows: int = 100) -> list:
    """Search for a specific scripture"""
    terms = SCRIPTURE_SEARCH_TERMS.get(scripture_id, [scripture_id.lower()])
    all_results = []
    
    for term in terms:
        # Search in title
        query = f"title:({term}) OR subject:({term})"
        result = search_archive_org(query, rows=rows)
        docs = result.get('response', {}).get('docs', [])
        for doc in docs:
            doc['search_term'] = term
            doc['scripture_id'] = scripture_id
        all_results.extend(docs)
        
        # Search in text for Devanagari terms
        if any('\u0900' <= c <= '\u097F' for c in term):
            query = f"text:({term})"
            result = search_archive_org(query, rows=rows)
            docs = result.get('response', {}).get('docs', [])
            for doc in docs:
                doc['search_term'] = term
                doc['scripture_id'] = scripture_id
            all_results.extend(docs)
        
        time.sleep(0.5)  # Rate limiting
    
    # Deduplicate by identifier
    seen = set()
    unique = []
    for doc in all_results:
        ident = doc.get('identifier')
        if ident and ident not in seen:
            seen.add(ident)
            unique.append(doc)
    
    return unique

def filter_relevant(docs: list, scripture_id: str) -> list:
    """Filter results for relevance"""
    relevant = []
    for doc in docs:
        title = doc.get('title', '')
        if isinstance(title, list):
            title = ' '.join(title)
        title = (title or '').lower()
        
        subject = doc.get('subject', [])
        if isinstance(subject, list):
            subject = ' '.join(subject)
        subject = (subject or '').lower()
        
        creator = doc.get('creator', '')
        if isinstance(creator, list):
            creator = ' '.join(creator)
        creator = (creator or '').lower()
        
        mediatype = doc.get('mediatype', '')
        formats = doc.get('format', [])
        if isinstance(formats, list):
            formats = ' '.join(formats)
        formats = (formats or '').lower()
        
        # Must have downloadable format
        has_pdf = 'pdf' in formats
        has_djvu = 'djvu' in formats
        has_txt = 'text' in formats
        
        if not (has_pdf or has_djvu or has_txt):
            continue
        
        # Score relevance
        score = 0
        scripture_terms = [t.lower() for t in SCRIPTURE_SEARCH_TERMS.get(scripture_id, [])]
        for term in scripture_terms:
            if term in title:
                score += 10
            if term in subject:
                score += 5
            if term in creator:
                score += 3
        
        # Publisher bonuses
        for pub in ['gita press', 'chowkhamba', 'chaukhamba', 'motilal', 'banarsidass', 
                    'anandashram', 'venkateshwar', 'gorakhpur', 'nag prakashan']:
            if pub in title or pub in creator:
                score += 5
        
        # Format bonuses
        if has_pdf:
            score += 2
        if has_djvu:
            score += 1
        
        # Penalize non-text media
        if mediatype in ['audio', 'video', 'image']:
            score -= 10
        
        doc['relevance_score'] = score
        if score > 0:
            relevant.append(doc)
    
    relevant.sort(key=lambda x: x['relevance_score'], reverse=True)
    return relevant

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--scripture', required=True, help='Scripture ID (e.g., RV, BG, BHAG)')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--rows', type=int, default=100, help='Results per search')
    parser.add_argument('--all', action='store_true', help='Search all scriptures')
    args = parser.parse_args()
    
    if args.all:
        scriptures = list(SCRIPTURE_SEARCH_TERMS.keys())
    else:
        scriptures = [args.scripture.upper()]
    
    all_results = {}
    for sid in scriptures:
        print(f"Searching for {sid}...")
        results = search_scripture(sid, rows=args.rows)
        filtered = filter_relevant(results, sid)
        all_results[sid] = filtered
        print(f"  Found {len(results)} total, {len(filtered)} relevant")
        
        # Save per scripture
        if args.output:
            out_path = Path(args.output).parent / f"{sid}_archive_results.json"
        else:
            out_path = Path(f"/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/acquisition/{sid}_archive_results.json")
        
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w') as f:
            json.dump(filtered, f, indent=2)
    
    print("Done!")

if __name__ == '__main__':
    main()
