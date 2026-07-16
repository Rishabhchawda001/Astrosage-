#!/usr/bin/env python3
"""
Extract Bhagavad Gita verses from the Gita Press DjVuTXT OCR
"""
import json
import re
from pathlib import Path

INPUT_FILE = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/downloads/bg_gita_press_djvu.txt"
OUTPUT_DIR = Path("/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/dtc/bg_gitapress")

def extract_verses(text):
    """Extract verses from DjVuTXT OCR text"""
    verses = []
    
    # Find all verse markers: ॥ number ॥
    # Pattern: Sanskrit text followed by ॥ number ॥
    pattern = r'([^\n॥]*?)॥\s*(\d+)\s*॥'
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    
    current_chapter = 0
    chapter_positions = {}
    
    # Find chapter markers
    chapter_patterns = [
        r'(\d+)(?:वां?\s*)?अध्याय',
        r'अध्याय\s*(\d+)',
        r'Chapter\s*(\d+)',
        r'पहला\s*अध्याय',
        r'दूसरा\s*अध्याय',
        r'तीसरा\s*अध्याय',
        r'चौथा\s*अध्याय',
        r'पच्या\s*अध्याय',
        r'छठा\s*अध्याय',
        r'सातां\s*अध्याय',
        r'आवा\s*अध्याय',
        r'नवां\s*अध्याय',
        r'दसवां\s*अध्याय',
        r'ग्यारहवां\s*अध्याय',
        r'बारहवां\s*अध्याय',
        r'तेरहवां\s*अध्याय',
        r'चौदहवां\s*अध्याय',
        r'पंद्रहवां\s*अध्याय',
        r'सोलहवां\s*अध्याय',
        r'सत्रहवां\s*अध्याय',
        r'अठारहवां\s*अध्याय',
    ]
    
    chapter_map = {
        'पहला': 1, 'दूसरा': 2, 'तीसरा': 3, 'चौथा': 4,
        'पच्या': 5, 'छठा': 6, 'सातां': 7, 'आवा': 8,
        'नवां': 9, 'दसवां': 10, 'ग्यारहवां': 11, 'बारहवां': 12,
        'तेरहवां': 13, 'चौदहवां': 14, 'पंद्रहवां': 15, 'सोलहवां': 16,
        'सत्रहवां': 17, 'अठारहवां': 18,
    }
    
    for line_no, line in enumerate(text.split('\n')):
        # Check for chapter markers
        for pattern in chapter_patterns:
            m = re.search(pattern, line)
            if m:
                # Extract chapter number
                if m.group(1).isdigit():
                    current_chapter = int(m.group(1))
                else:
                    for key, val in chapter_map.items():
                        if key in line:
                            current_chapter = val
                            break
                chapter_positions[current_chapter] = line_no
    
    # Now extract verses
    for match in matches:
        verse_text = match.group(1).strip()
        verse_num = int(match.group(2))
        
        # Clean verse text
        verse_text = re.sub(r'\s+', ' ', verse_text).strip()
        verse_text = re.sub(r'^[॥\s]+', '', verse_text)
        verse_text = re.sub(r'[॥\s]+$', '', verse_text)
        
        if verse_text and len(verse_text) > 10:
            verses.append({
                'chapter': current_chapter,
                'verse': verse_num,
                'text': verse_text,
                'source': 'gita_press_djvu_ocr'
            })
    
    return verses

def main():
    text = Path(INPUT_FILE).read_text(encoding='utf-8', errors='ignore')
    print(f"Read {len(text)} characters from DjVuTXT")
    
    # Find chapter boundaries by searching for known patterns
    lines = text.split('\n')
    chapter_starts = {}
    
    for i, line in enumerate(lines):
        for key, num in [
            ('पहला अध्याय', 1), ('दूसरा अध्याय', 2), ('तीसरा अध्याय', 3),
            ('चौथा अध्याय', 4), ('पच्या अध्याय', 5), ('छठा अध्याय', 6),
            ('सातां अध्याय', 7), ('आवा अध्याय', 8), ('नवां अध्याय', 9),
            ('दसवां अध्याय', 10), ('ग्यारहवां अध्याय', 11), ('बारहवां अध्याय', 12),
            ('तेरहवां अध्याय', 13), ('चौदहवां अध्याय', 14), ('पंद्रहवां अध्याय', 15),
            ('सोलहवां अध्याय', 16), ('सत्रहवां अध्याय', 17), ('अठारहवां अध्याय', 18),
        ]:
            if key in line:
                chapter_starts[num] = i
    
    print(f"Found chapter markers at: {chapter_starts}")
    
    # Extract all verse patterns: ॥ number ॥
    all_matches = list(re.finditer(r'॥\s*(\d{1,3})\s*॥', text))
    print(f"Found {len(all_matches)} verse number markers")
    
    # Map each verse to its chapter based on position
    chapters = sorted(chapter_starts.keys())
    verses = []
    
    for m in all_matches:
        verse_num = int(m.group(1))
        pos = m.start()
        
        # Find which chapter this verse belongs to
        chapter = 0
        for ch in reversed(chapters):
            if chapter_starts[ch] * 100 < pos:  # rough line-to-char mapping
                chapter = ch
                break
        
        # Get text before the verse marker
        start = max(0, pos - 500)
        context = text[start:pos]
        
        # Clean context
        context = re.sub(r'\n+', ' ', context)
        context = re.sub(r'\s+', ' ', context).strip()
        
        # Take last meaningful chunk as verse text
        parts = context.split('।')
        verse_text = parts[-1].strip() if parts else context[-200:]
        
        if verse_text and len(verse_text) > 5:
            verses.append({
                'chapter': chapter,
                'verse': verse_num,
                'text': verse_text,
                'ref': f'BG_{chapter:02d}.{verse_num:03d}'
            })
    
    print(f"Extracted {len(verses)} verses")
    
    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "bg_gitapress_ocr_verses.json", 'w') as f:
        json.dump({
            'scripture': 'Bhagavad Gita',
            'source': 'Gita Press Tattva Vivecana (DjVuTXT OCR)',
            'editor': 'Jay Dayal Goyandaka',
            'publisher': 'Gita Press Gorakhpur',
            'total_extracted': len(verses),
            'verses': verses
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Saved to {OUTPUT_DIR / 'bg_gitapress_ocr_verses.json'}")
    
    # Show sample
    for v in verses[:5]:
        print(f"  {v.get('ref', '??')}: {v['text'][:80]}...")

if __name__ == '__main__':
    main()
