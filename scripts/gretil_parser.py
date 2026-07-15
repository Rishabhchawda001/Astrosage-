#!/usr/bin/env python3
"""
GRETIL TEI XML Parser v3 - Extract canonical structure from scholarly digital editions.
Simple, robust approach: divs = chapters, <p> elements provide chapter numbers.
"""

import json
import os
import re
import sys
from pathlib import Path

try:
    import lxml.etree as ET
    HAS_LXML = True
except ImportError:
    import xml.etree.ElementTree as ET
    HAS_LXML = False

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate
    HAS_TRANSLITERATION = True
except ImportError:
    HAS_TRANSLITERATION = False

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}


def _tag(el):
    t = el.tag
    return t.split('}')[-1] if '}' in t else t


def _text(el):
    return (el.text or '').strip() if el is not None else ''


def _all_text(el):
    if el is None:
        return ''
    if HAS_LXML:
        return ''.join(el.itertext())
    parts = []
    for n in el.iter():
        if n.text: parts.append(n.text)
        if n.tail: parts.append(n.tail)
    return ''.join(parts)


def _children(el, tag=None):
    result = list(el)
    if tag:
        return [c for c in result if _tag(c) == tag]
    return result


def _find(el, path):
    if HAS_LXML:
        return el.find(path, namespaces=NS)
    return el.find(path)


def _findall(el, path):
    if HAS_LXML:
        return el.findall(path, namespaces=NS)
    return el.findall(path)


def extract_chapter_num_from_p(text):
    """Extract chapter number from prose/colophon text."""
    if not text:
        return None

    # Numeric patterns first (most reliable)
    # % chapter {N}
    m = re.search(r'%\s*chapter\s*\{(\d+)\}', text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    # BhP_SK.CH.VERSE pattern
    m = re.search(r'[A-Za-z]+[_\s]\d+\.(\d+)\.\d+', text)
    if m:
        return int(m.group(1))

    # /PREFIX_SK.VERSE/ pattern
    m = re.search(r'/[A-Za-z]+_(\d+)\.\d+', text)
    if m:
        return int(m.group(1))

    # PREFIX_SK.CH.rest pattern
    m = re.search(r'[A-Za-z]+[_\s](\d+)\.\d+[a-z]', text)
    if m:
        return int(m.group(1))

    # chapter N
    m = re.search(r'chapter\s+(\d+)', text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    # adhyaya N
    m = re.search(r'adhy[ae]y[ae]\s+(\d+)', text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    # N adhyaya
    m = re.search(r'(\d+)\s+adhy[ae]y', text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    # Sanskrit ordinal before adhyaya - match the word just before 'adhy'
    # This handles: "prathamo 'dhyāyaḥ", "dvitīyo 'dhyāyaḥ", etc.
    m = re.search(r'(\w+)\s*[\u2018\u2019\'"]?\s*adhy', text, re.IGNORECASE)
    if m:
        word = m.group(1).lower()
        # Map common IAST ordinal forms
        ord_map = {
            'prathama': 1, 'prathamo': 1, 'prathamam': 1, 'prathamah': 1,
            'dvitiiya': 2, 'dvitiiyo': 2, 'dvitiiyam': 2, 'dvitiiyah': 2,
            'tritiiya': 3, 'tRtiiya': 3, 'tRtiiyo': 3,
            'chaturtha': 4, 'caturtha': 4, 'caturtho': 4, 'caturtham': 4,
            'panchama': 5, 'pa~jama': 5, 'panchamo': 5, 'pa~jamo': 5,
            'shashtha': 6, 'SaSTha': 6, 'SaSTho': 6, 'shashtho': 6,
            'saptama': 7, 'saptamo': 7, 'saptamam': 7,
            'ashtama': 8, 'aSTama': 8, 'aSTamo': 8, 'ashtamam': 8,
            'navama': 9, 'navamo': 9, 'navamam': 9,
            'dashama': 10, 'dazama': 10, 'dazamo': 10, 'dashamam': 10,
            'ekadasha': 11, 'ekAdaza': 11, 'ekAdazo': 11,
            'dvadasha': 12, 'dvAdaza': 12, 'dvAdazo': 12,
            'trayodasha': 13, 'trayodaZa': 13, 'trayodaZo': 13,
            'chaturdasha': 14, 'caturdaza': 14, 'caturdazo': 14,
            'panchadasha': 15, 'pa~jadaZa': 15, 'pa~jadaZo': 15,
            'shodasha': 16, 'SoDaZa': 16, 'SoDaZo': 16,
            'saptadasha': 17, 'saptadaZa': 17, 'saptadaZo': 17,
            'ashtadasha': 18, 'aSTAdaza': 18, 'aSTAdazo': 18,
            'ekonavimsha': 19, 'ekoNavima': 19,
            'vimshati': 20, 'vimzati': 20, 'vimshatih': 20,
            'ekavimsha': 21, 'ekavi': 21,
            'dvavimsha': 22, 'dvA': 22,
            'trayovimsha': 23, 'trayo': 23,
            'chaturvimsha': 24, 'catu': 24,
            'panchavimsha': 25, 'pa~ca': 25,
            'shadvimsha': 26, 'ShaD': 26, 'SaT': 26,
            'saptavimsha': 27, 'sapta': 27,
            'ashtavimsha': 28, 'aSTA': 28,
            'ekonatrimsha': 29, 'Navama': 29,
            'trimsha': 30, 'trimzat': 30, 'triMzat': 30,
            'ekatrimsha': 31, 'ekatri': 31,
            'dvatrimsha': 32,
            'chatustimsha': 34, 'catur': 34,
            'panchatrimsha': 35, 'pa~ca': 35,
            'shattrimsha': 36, 'ShaT': 36,
            'saptatrimsha': 37,
            'ashtatrimsha': 38,
            'chaturshashti': 44,
            'panchashashti': 55,
            'shatshashti': 66,
            'saptashashti': 77,
            'ashtashashti': 88,
            'navashashti': 99,
            'shata': 100,
        }
        if word in ord_map:
            return ord_map[word]

    # Roman numeral
    m = re.search(r'\b([ivxlcdm]+)\b', text, re.IGNORECASE)
    if m:
        rn = m.group(1).upper()
        roman = {
            'I':1,'II':2,'III':3,'IV':4,'V':5,'VI':6,'VII':7,'VIII':8,'IX':9,'X':10,
            'XI':11,'XII':12,'XIII':13,'XIV':14,'XV':15,'XVI':16,'XVII':17,'XVIII':18,'XIX':19,'XX':20,
            'XXI':21,'XXII':22,'XXIII':23,'XXIV':24,'XXV':25,'XXVI':26,'XXVII':27,'XXVIII':28,'XXIX':29,'XXX':30,
        }
        if rn in roman:
            return roman[rn]

    return None


def parse_tei_xml(filepath):
    try:
        if HAS_LXML:
            parser = ET.XMLParser(recover=True, no_network=True)
            return ET.parse(filepath, parser).getroot()
        return ET.parse(filepath).getroot()
    except Exception as e:
        print(f"  Warning: parse error: {e}")
        return None


def extract_lines_from_lg(lg_elem):
    """Extract verse lines from an <lg> element."""
    l_elems = _children(lg_elem, 'l')
    lines = []
    for l_el in l_elems:
        t = _text(l_el)
        if t:
            lines.append(t)
    if lines:
        return lines
    # Fallback: text in lg itself
    full = _all_text(lg_elem).strip()
    if full:
        parts = re.split(r'\s*//\s*|\s*/\s*', full)
        parts = [p.strip() for p in parts if p.strip()]
        return parts if parts else [full]
    return []


def parse_gretil_file(filepath):
    """Parse a GRETIL TEI XML file."""
    fname = os.path.basename(filepath)
    root = parse_tei_xml(filepath)
    if root is None:
        return None

    xml_id = root.get('{http://www.w3.org/XML/1998/namespace}id', 'unknown')
    title_el = _find(root, './/tei:title')
    title = title_el.text if title_el is not None else 'unknown'

    body = _find(root, './/tei:body')
    if body is None:
        return None

    # Strategy: Process document order, using divs as chapter boundaries
    chapters = []
    current = {'num': 0, 'verses': [], 'prose': [], 'speakers': []}

    def process(elem):
        nonlocal current
        for child in elem:
            tag = _tag(child)

            if tag == 'div':
                # Check if this div has many children with lg/l elements
                # If so, it's a chapter
                inner_lg = _children(child, 'lg')
                inner_l = _children(child, 'l')
                inner_p = _children(child, 'p')

                if inner_lg or inner_l:
                    # This div contains verse content — treat as chapter
                    # Save previous chapter if it has content
                    if current['verses'] or current['prose']:
                        chapters.append(current)

                    # Try to extract chapter number from first <p> in div
                    ch_num = 0
                    for p in inner_p:
                        t = _text(p)
                        if t.strip():
                            n = extract_chapter_num_from_p(t)
                            if n:
                                ch_num = n
                                break

                    current = {'num': ch_num, 'verses': [], 'prose': [], 'speakers': []}

                    # Process the div's children
                    for subchild in child:
                        stag = _tag(subchild)
                        if stag == 'lg':
                            lines = extract_lines_from_lg(subchild)
                            if lines:
                                current['verses'].append({'lines': lines})
                        elif stag == 'l':
                            t = _text(subchild)
                            if t.strip():
                                current['verses'].append({'lines': [t.strip()]})
                        elif stag == 'p':
                            t = _text(subchild)
                            if t.strip():
                                n = extract_chapter_num_from_p(t)
                                if n and n != current['num']:
                                    if current['verses'] or current['prose']:
                                        chapters.append(current)
                                    current = {'num': n, 'verses': [], 'prose': [t.strip()], 'speakers': []}
                                else:
                                    current['prose'].append(t.strip())
                        elif stag == 'milestone':
                            n = subchild.get('n', '')
                            if n:
                                current['speakers'].append(n)
                        elif stag == 'div':
                            # Nested div (e.g., Ramayana kandas)
                            process(subchild)
                else:
                    # Div without verse content (e.g., intro div)
                    # Process children but don't create a new chapter
                    process(child)
            elif tag == 'lg':
                lines = extract_lines_from_lg(child)
                if lines:
                    current['verses'].append({'lines': lines})
            elif tag == 'l':
                t = _text(child)
                if t.strip():
                    current['verses'].append({'lines': [t.strip()]})
            elif tag == 'p':
                t = _text(child)
                if t.strip():
                    n = extract_chapter_num_from_p(t)
                    if n and n != current['num']:
                        # Save previous chapter
                        if current['verses'] or current['prose']:
                            chapters.append(current)
                        current = {'num': n, 'verses': [], 'prose': [t.strip()], 'speakers': []}
                    elif n and n == current['num']:
                        current['prose'].append(t.strip())
                    else:
                        current['prose'].append(t.strip())
            elif tag == 'milestone':
                n = child.get('n', '')
                if n:
                    current['speakers'].append(n)

    process(body)

    # Save last chapter
    if current['verses'] or current['prose']:
        chapters.append(current)

    # Assign sequential numbers
    seq = 0
    for ch in chapters:
        if ch['num'] == 0:
            seq += 1
            ch['num'] = seq
        else:
            seq = ch['num']

    # Build result
    total_verses = sum(len(ch['verses']) for ch in chapters)

    result = {
        'file': fname,
        'xml_id': xml_id,
        'title': title,
        'total_chapters': len(chapters),
        'total_verses': total_verses,
        'chapters': [],
    }

    for ch in chapters:
        ch_data = {
            'chapter_num': ch['num'],
            'verse_count': len(ch['verses']),
            'verse_groups': [],
        }
        if ch['speakers']:
            ch_data['speakers'] = list(dict.fromkeys(ch['speakers']))
        if ch['prose']:
            ch_data['prose_sample'] = ch['prose'][:3]
        for v in ch['verses']:
            ch_data['verse_groups'].append({
                'lines': v['lines'],
                'line_count': len(v['lines']),
            })
        result['chapters'].append(ch_data)

    return result


def iast_to_devanagari(text):
    if not HAS_TRANSLITERATION or not text:
        return text
    try:
        return transliterate(text, sanscript.IAST, sanscript.DEVANAGARI)
    except Exception:
        return text


def main():
    base_dir = Path(__file__).parent.parent
    downloads_dir = base_dir / 'knowledge' / 'downloads'
    output_dir = base_dir / 'knowledge' / 'gretil_parsed'
    output_dir.mkdir(parents=True, exist_ok=True)

    xml_files = sorted(
        list(downloads_dir.glob('*gretil*.xml')) +
        list(downloads_dir.glob('sa_brahmANDapurANa.xml')) +
        list(downloads_dir.glob('sa_bAdarAyaNa*.xml')) +
        list(downloads_dir.glob('sa_brahmagupta*.xml')) +
        list(downloads_dir.glob('sa_brahmabindUpaniSad.xml'))
    )

    seen = set()
    unique = []
    for f in xml_files:
        if f.name not in seen:
            seen.add(f.name)
            unique.append(f)
    xml_files = unique

    print(f"Found {len(xml_files)} GRETIL XML files\n")

    all_structures = {}
    summary = []

    for filepath in xml_files:
        fname = filepath.name
        print(f"Parsing {fname}...")
        structure = parse_gretil_file(str(filepath))
        if structure is None:
            print(f"  FAILED")
            continue

        out_name = fname.replace('.xml', '_structure.json')
        with open(output_dir / out_name, 'w', encoding='utf-8') as f:
            json.dump(structure, f, ensure_ascii=False, indent=2)

        lines = []
        for ch in structure['chapters']:
            lines.append(f"\n=== Chapter {ch['chapter_num']} ===\n")
            for prose in ch.get('prose_sample', []):
                lines.append(prose)
            for vg in ch['verse_groups']:
                for line in vg['lines']:
                    lines.append(line)
                lines.append('')
        iast_text = '\n'.join(lines)
        with open(output_dir / fname.replace('.xml', '_iast.txt'), 'w', encoding='utf-8') as f:
            f.write(iast_text)

        if HAS_TRANSLITERATION:
            dev = iast_to_devanagari(iast_text)
            with open(output_dir / fname.replace('.xml', '_devanagari.txt'), 'w', encoding='utf-8') as f:
                f.write(dev)

        all_structures[fname] = structure
        summary.append({
            'file': fname, 'title': structure['title'],
            'chapters': structure['total_chapters'], 'verses': structure['total_verses'],
        })
        print(f"  {structure['title']}: {structure['total_chapters']} chapters, {structure['total_verses']} verses")

    with open(output_dir / 'gretil_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*80}")
    print(f"{'File':<45} {'Title':<30} {'Ch':>4} {'V':>6}")
    print("-"*80)
    tc = tv = 0
    for s in summary:
        print(f"{s['file']:<45} {s['title'][:29]:<30} {s['chapters']:>4} {s['verses']:>6}")
        tc += s['chapters']
        tv += s['verses']
    print("-"*80)
    print(f"{'TOTAL':<75} {tc:>4} {tv:>6}")

    return all_structures


if __name__ == '__main__':
    main()
