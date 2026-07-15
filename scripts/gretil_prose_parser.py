#!/usr/bin/env python3
"""
GRETIL Prose AKU Parser.

The standard GRETIL parser (gretil_parser.py) extracts only <lg>/<l> verse groups.
Many canonical texts (Sutras, Brahmanas, grammatical works) store their atomic
knowledge units (AKUs) inside <p> paragraphs, with one or more embedded reference
markers such as:
  SSS_1.1.1:          -> Shankhayana Shrauta Sutra
  Va.1.1              -> Vasistha Dharmasutra
  Ap1.1.1.1/          -> Apastamba Dharmasutra
  1,1:                -> Nirukta
  (PB 1.1.1)          -> Pancavimsha Brahmana
  (AVPr_1.1:71/1)     -> Atharva Prayashchittani

This parser recovers those prose AKUs so they become addressable canonical units
(Chapter -> AKU). It never invents text; it tokenises existing <p> content and uses
the reference token that is already present in the GRETIL source to open a new AKU.
"""

import json
import os
import re
from pathlib import Path

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}


def _all_text(el):
    return ''.join(el.itertext()).strip()


# A reference token begins with a Unicode letter, contains at least one digit, and
# uses _ . , as internal separators. Trailing : / ( ) [ ] are marker punctuation and
# are stripped before matching. This covers every known GRETIL prose reference style.
_LETTER = r'[A-Za-zĀ-ɏ]'
# A reference token has a numeric core, optionally preceded by a letter prefix (incl.
# diacritics) and/or introduced by _ . , separators. Parens/brackets and trailing : /
# are marker punctuation handled by _is_ref_token. Covers:
#   SSS_1.1.1   Va.1.1   1,1   Ap1.1.1.1   (PB 1.1.1)   (AVPr_1.1:71/1)
REF_TOKEN = re.compile(
    r'^[A-Za-zĀ-ɏ]*?'                       # optional letter prefix (incl. diacritics)
    r'(?:[0-9]+|[._,][0-9]+)'               # numeric core (direct or separator-led)
    r'(?:[._,][A-Za-z0-9]+)*'               # subsequent separator+alnum runs
    r'[A-Za-z0-9_]*'                        # trailing alnum/underscore
    r'$'
)
_DIGIT = re.compile(r'\d')


def _is_ref_token(tok):
    """Return the cleaned ref if tok is a GRETIL reference token, else None.

    Handles: trailing : / ; wrapping ( ) or [ ]; leading letters (incl. diacritics);
    a numeric core introduced by _ . , or directly. Examples:
      SSS_1.1.1:  Va.1.1  1,1:  Ap1.1.1.1/  (PB 1.1.1)  (AVPr_1.1:71/1)
    """
    t = tok.strip()
    if not t:
        return None
    cand = t.rstrip(':/')
    # Strip any number of surrounding parentheses/brackets
    prev = None
    while prev != cand:
        prev = cand
        cand = cand.strip('()[]')
    if not cand or not _DIGIT.search(cand):
        return None
    if REF_TOKEN.match(cand):
        return cand
    return None


def split_prose_akus(text):
    """Split a <p> paragraph into (ref, body) segments on reference tokens.

    Each reference token opens a new AKU; all following words belong to that AKU's body
    until the next reference token. Text with no reference token becomes a single
    unreferenced AKU. No text is invented or dropped.

    Handles paren-wrapped multi-token refs like (PB 1.1.1) by merging them into a
    single ref token before the standard split.
    """
    if not text:
        return []
    text = text.replace('\n', ' ').strip()
    # Merge paren-wrapped refs: (PB 1.1.1) -> (PB_1.1.1) so whitespace split keeps them together
    text = re.sub(r'\(\s*([A-Za-zĀ-ɏ][A-Za-zĀ-ɏ0-9]*)\s+([^)]+)\s*\)',
                  lambda m: '(' + m.group(1).replace(' ', '_') + '_' + m.group(2).replace(' ', '_') + ')',
                  text)
    tokens = text.split()
    if not tokens:
        return [{'ref': None, 'body': text}]
    akus = []
    cur_ref = None
    cur_body = []
    for tok in tokens:
        ref = _is_ref_token(tok)
        if ref is not None:
            if cur_ref is not None or cur_body:
                akus.append({'ref': cur_ref, 'body': ' '.join(cur_body)})
            cur_ref = ref
            cur_body = []
        else:
            cur_body.append(tok)
    if cur_ref is not None or cur_body:
        akus.append({'ref': cur_ref, 'body': ' '.join(cur_body)})
    return akus


def parse_prose_file(filepath):
    import xml.etree.ElementTree as ET
    fname = os.path.basename(filepath)
    tree = ET.parse(filepath)
    root = tree.getroot()
    title_el = root.find('.//tei:title', NS)
    title = title_el.text if title_el is not None else fname
    body = root.find('.//tei:body', NS)
    if body is None:
        return None

    paras = body.findall('.//tei:p', NS)

    akus = []
    for p in paras:
        txt = _all_text(p)
        if not txt.strip():
            continue
        if 'GRETIL' in txt[:200] or 'e-text was provided' in txt[:200] or 'transliteration' in txt[:200].lower():
            continue
        segs = split_prose_akus(txt)
        if not segs:
            akus.append({'ref': None, 'body': txt})
        else:
            akus.extend(segs)

    def chapter_of(ref):
        if not ref:
            return 0
        nums = re.findall(r'\d+', ref)
        return int(nums[0]) if nums else 0

    chapters = {}
    order = []
    for aku in akus:
        ch = chapter_of(aku['ref'])
        if ch not in chapters:
            chapters[ch] = []
            order.append(ch)
        chapters[ch].append(aku)

    ordered = sorted(order) if all(c > 0 for c in order) else order
    chapter_list = []
    for ch in ordered:
        units = chapters[ch]
        chapter_list.append({
            'chapter_num': ch,
            'aku_count': len(units),
            'akus': units,
        })

    total_akus = sum(len(c['akus']) for c in chapter_list)
    return {
        'file': fname,
        'title': title,
        'total_chapters': len(chapter_list),
        'total_akus': total_akus,
        'chapters': chapter_list,
    }


def main():
    base_dir = Path(__file__).parent.parent
    downloads_dir = base_dir / 'knowledge' / 'downloads'
    output_dir = base_dir / 'knowledge' / 'gretil_prose'
    output_dir.mkdir(parents=True, exist_ok=True)

    xml_files = sorted(downloads_dir.glob('*gretil*.xml'))
    xml_files += sorted(downloads_dir.glob('sa_*.xml'))
    seen = set()
    uniq = []
    for f in xml_files:
        if f.name not in seen:
            seen.add(f.name)
            uniq.append(f)
    xml_files = uniq

    results = {}
    for fp in xml_files:
        struct = parse_prose_file(str(fp))
        if struct is None:
            continue
        if struct['total_akus'] == 0:
            continue
        out = fp.name.replace('.xml', '_prose.json')
        with open(output_dir / out, 'w', encoding='utf-8') as f:
            json.dump(struct, f, ensure_ascii=False, indent=2)
        results[fp.name] = struct['total_akus']
        print(f"  {fp.name}: {struct['total_chapters']} chapters, {struct['total_akus']} prose AKUs")

    print(f"\nRecovered prose AKUs across {len(results)} files")
    return results


if __name__ == '__main__':
    main()
