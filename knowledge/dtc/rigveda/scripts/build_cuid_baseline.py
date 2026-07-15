#!/usr/bin/env python3
"""Build baseline CUID set for Rigveda Samhita from the TWO collatable independent
witness families: F-AUFRECHT (Aufrecht 1863 -> GRETIL TEI) and F-LUBOTSKY
(VedaWeb Lubotsky layer). All other layers (VNH, aufrecht ref, zurich translit,
oldenberg/geldner/etc. reference notes) are NON-independent and EXCLUDED.

Output: dtc/rigveda/cuid_baseline_2base.json
Each CUID carries: cuid, structural position, canonical reading (Aufrecht),
independent families collated, aligned padas, variant classification,
confidence, evidence chain.
"""
import re, json, os

DL = "/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/downloads"

def strip_accents(s):
    # remove <orig> accent wrappers but keep the combining char they wrap
    s = re.sub(r'<orig>(.*?)</orig>', r'\1', s, flags=re.S)
    s = re.sub(r'<[^>]+>', '', s)
    return s.strip()

def extract_aufrecht(path):
    txt = open(path, encoding='utf-8', errors='ignore').read()
    out = {}
    # sūkta blocks
    for suk in re.finditer(r'<div type="sūkta" n="(\d+)">(.*?)(?=<div type="sūkta" n=|\Z)', txt, re.S):
        m, body = int(suk.group(1)), suk.group(2)
        for lg in re.finditer(r'xml:id="RV_\d+\.(\d+)\.(\d+)">(.*?)</lg>', body, re.S):
            s, v = int(lg.group(1)), int(lg.group(2))
            padas = []
            for l in re.finditer(r'n="\d+\.\d+\.(\d+)([acp])">(.*?)</l>', lg.group(3), re.S):
                padas.append(l.group(1)+l.group(2)+':'+strip_accents(l.group(2)))
            if padas:
                out[(m,s,v)] = padas
    return out

def extract_lubotsky(path):
    txt = open(path, encoding='utf-8', errors='ignore').read()
    out = {}
    for st in re.finditer(r'xml:id="b(\d+)_h(\d+)_(\d+)" type="stanza">(.*?)</div>\s*</div>', txt, re.S):
        m, s, v, blk = int(st.group(1)), int(st.group(2)), int(st.group(3)), st.group(4)
        ml = re.search(r'xml:id="b\d+_h\d+_\d+_lubotsky"[^>]*>(.*?)</lg>', blk, re.S)
        if not ml:
            continue
        lines = re.findall(r'(?s)<l[^>]*>(.*?)</l>', ml.group(1))
        padas = [strip_accents(l).replace('-_','') for l in lines]
        if padas:
            out[(m,s,v)] = padas
    return out

auf = extract_aufrecht(f"{DL}/rigveda_aufrecht_gretil.xml")
lub = {}
for b in range(1,11):
    p = f"{DL}/vedaweb/cceh-c-salt_vedaweb_tei-f975755/rv_book_{b:02d}.tei"
    if os.path.exists(p):
        lub.update(extract_lubotsky(p))

print(f"Aufrecht verses: {len(auf)} | Lubotsky verses: {len(lub)}")

cuid = []
keys = sorted(set(auf)|set(lub), key=lambda k:(k[0],k[1],k[2]))
for (m,s,v) in keys:
    a = auf.get((m,s,v)); l = lub.get((m,s,v))
    collated = (["F-AUFRECHT"] if a else []) + (["F-LUBOTSKY"] if l else [])
    indep = len(collated)
    # canonical reading = Aufrecht normalized text if present else Lubotsky joined
    if a:
        canon = " ".join(t.split(':',1)[1] for t in a)
    elif l:
        canon = " ".join(l)
    else:
        canon = None
    # variant classification: compare normalized pada TEXT (ignore accents/segmentation count)
    def norm(p): return re.sub(r'[^a-zāīūṛḷḹṃḥṇñṅśṣṭḍḷ]','', p.lower())
    a_text = [t.split(':',1)[1] for t in a] if a else []
    l_text = l if l else []
    # compare as multiset of words ignoring segmentation differences
    a_words = set(norm(w) for p in a_text for w in p.split())
    l_words = set(norm(w) for p in l_text for w in p.split())
    if a and l:
        if a_words == l_words:
            vclass = "none (accent/segmentation only)"
        else:
            vclass = "word-level difference (needs manual review)"
    elif a or l:
        vclass = "single-family only (no cross-family variant test)"
    else:
        vclass = "missing"
    cuid.append({
        "cuid": f"RV-CU-{m}.{s}.{v}",
        "scripture":"RV","mandala":m,"sukta":s,"verse":v,
        "canonical_text": canon,
        "witness_families_independent_collated": collated,
        "independent_family_count": indep,
        "aligned_padas": {"aufrecht":a,"lubotsky":l},
        "variant_classification": vclass,
        "confidence": {"independent_families":indep,
                       "score": (0.95 if indep==2 and vclass.startswith('none') else
                                 (0.7 if indep==2 else (0.6 if indep==1 else 0.1)))},
        "evidence_chain": (["Aufrecht 1863 -> GRETIL TEI (F-AUFRECHT)"] if a else []) +
                          (["Lubotsky transcription -> VedaWeb Zenodo 4601264 (F-LUBOTSKY)"] if l else [])
    })

out = {
  "scripture":"RV","base":"F-AUFRECHT + F-LUBOTSKY (2 independent collatable families)",
  "total_cuids":len(cuid),
  "aufrecht_verses":len(auf),"lubotsky_verses":len(lub),
  "note":"Excludes VNH/aufrecht-ref/zurich/oldenberg/geldner/etc. (non-independent). Quality gate: RV remains EVIDENCE INCOMPLETE until >=1 more independent base collated.",
  "cuid":cuid
}
with open("dtc/rigveda/cuid_baseline_2base.json","w",encoding='utf-8') as f:
    json.dump(out,f,ensure_ascii=False,indent=1)
# short summary
from collections import Counter
cnt=Counter(c['variant_classification'] for c in cuid)
print("Wrote cuid_baseline_2base.json with",len(cuid),"CUIDs")
print("Aufrecht coverage:",len(auf),"| Lubotsky coverage:",len(lub))
print("Variant classification distribution:")
for k,v in cnt.most_common(): print(f"  {v:6d}  {k}")
