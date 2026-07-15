#!/usr/bin/env python3
"""Collate Rigveda Samhita across the 2 collatable independent samhita families
(F-AUFRECHT, F-LUBOTSKY) using the PADAPATHA (F-PADAPATHA) as the sandhi-resolved
reference. For each verse we compare the SET OF PADA-FORM WORDS. Because the padapatha
gives the word-divided (sandhi-resolved) form, comparing pada-word sets eliminates
external-sandhi/segmentation/accent noise and isolates genuine lexical variants.

Output: knowledge/dtc/rigveda/cuid_baseline_3ref.json
"""
import re, json, os
from collections import Counter
import unicodedata

DL="/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/downloads"
ACCENT=dict.fromkeys(c for c in range(0x0300,0x0370))

def strip_acc(s): return unicodedata.normalize('NFKD',s).translate(ACCENT)
def norm(w):
    w=strip_acc(w.lower())
    # canonicalize internal sandhi variants in the PADA form itself:
    # e.g. puraḥ-hitam vs purah-hitam; keep hyphens as morpheme splits
    w=re.sub(r'[^a-zāīūṛḷṃḥṇñṅśṣṭḍ\-]','',w)
    return w

def wordlist_pada(tokens):
    """tokens = padapatha word list (already pada form, hyphens=compound splits)"""
    out=[]
    for tok in tokens:
        for w in re.split(r'[-]', tok):   # split compounds at hyphen
            w=norm(w)
            if w: out.append(w)
    return out

def extract_aufrecht(path):
    txt=open(path,encoding='utf-8',errors='ignore').read(); out={}
    for lg in re.finditer(r'xml:id="RV_(\d+)\.(\d+)\.(\d+)">(.*?)</lg>', txt, re.S):
        m,s,v=int(lg.group(1)),int(lg.group(2)),int(lg.group(3)); padas=[]
        for l in re.finditer(r'n="\d+\.\d+\.(\d+)([acp])">(.*?)</l>', lg.group(4), re.S):
            t=re.sub(r'<orig>(.*?)</orig>',r'\1',l.group(3),flags=re.S); t=re.sub(r'<[^>]+>','',t).strip()
            padas.append(t)
        if padas: out[(m,s,v)]=' '.join(padas)
    return out

def extract_lubotsky(path):
    txt=open(path,encoding='utf-8',errors='ignore').read(); out={}
    for st in re.finditer(r'xml:id="b(\d+)_h(\d+)_(\d+)" type="stanza">(.*?)(?=xml:id="b\d+_h\d+_\d+" type="stanza">|\Z)', txt, re.S):
        m,s,v,blk=int(st.group(1)),int(st.group(2)),int(st.group(3)),st.group(4)
        ml=re.search(r'xml:id="b\d+_h\d+_\d+_lubotsky"[^>]*>(.*?)</lg>', blk, re.S)
        if not ml: continue
        lines=re.findall(r'(?s)<l[^>]*>(.*?)</l>', ml.group(1))
        padas=[re.sub(r'<[^>]+>','',l).strip().replace('-_','') for l in lines]
        if padas: out[(m,s,v)]=' '.join(padas)
    return out

def sa_to_pada_words(samhita_text):
    """Resolve a samhita-form verse to a SET of pada words by matching against padapatha.
    Heuristic: split samhita on spaces, then for each token strip final sandhi consonant
    and compare to padapatha tokens (also final-sandhi-stripped)."""
    return [norm(w) for w in re.split(r'[ \-\|]+', samhita_text) if w.strip()]

auf=extract_aufrecht(f"{DL}/rigveda_aufrecht_gretil.xml")
lub={}
for b in range(1,11):
    p=f"{DL}/vedaweb/cceh-c-salt_vedaweb_tei-f975755/rv_book_{b:02d}.tei"
    if os.path.exists(p): lub.update(extract_lubotsky(p))
pp=json.load(open('/tmp/padapatha.json'))

# Build correct pada-word sets per verse
def pada_set_from_samhita(samhita_text):
    if isinstance(samhita_text,list): samhita_text=" ".join(samhita_text)
    # Resolve external sandhi: remove trailing sandhi finals entirely (pada form)
    words=[]
    for w in re.split(r'[ \-\|]+', samhita_text):
        w=norm(w)
        if not w: continue
        w=re.sub(r'[mṃḥhṇnrrttsṭḍṣñṅ]+$','',w)  # strip trailing sandhi
        if w: words.append(w)
    return words

results=[]
agree_auf_pp=0; agree_lub_pp=0; agree_auf_lub=0
genuine_auf=[]; genuine_lub=[]; single=0
allkeys=sorted(set(auf)|set(lub)|set((int(k.split('.')[0]),int(k.split('.')[1]),int(k.split('.')[2])) for k in pp))
for (m,s,v) in allkeys:
    key=f"{m}.{s}.{v}"
    a=auf.get((m,s,v)); l=lub.get((m,s,v)); ppt=pp.get(key)
    collated=(["F-AUFRECHT"] if a else [])+ (["F-LUBOTSKY"] if l else [])
    pset=set(pada_set_from_samhita(ppt)) if ppt else None
    aset=set(pada_set_from_samhita(a)) if a else None
    lset=set(pada_set_from_samhita(l)) if l else None
    # classify
    if a and l and ppt:
        a_match = (aset==pset)
        l_match = (lset==pset)
        al_match = (aset==lset)
        if a_match and l_match and al_match:
            vclass="full agreement (all 3 families: Aufrecht=Lubotsky=Padapatha pada form)"
        elif al_match:
            vclass="Aufrecht=Lubotsky; Padapatha differs (check resolution)"
        else:
            vclass="CANDIDATE genuine variant (manual review)"
            if len(genuine_auf)<40:
                genuine_auf.append((key, sorted(aset-pset), sorted(pset-aset), sorted(lset-pset), sorted(pset-lset)))
        if a_match: agree_auf_pp+=1
        if l_match: agree_lub_pp+=1
        if al_match: agree_auf_lub+=1
    elif a or l:
        vclass="single samhita family only (padapatha ref present: %s)"%('yes' if ppt else 'no')
        single+=1
    else:
        vclass="missing"
    results.append({"cuid":f"RV-CU-{key}","scripture":"RV","mandala":m,"sukta":s,"verse":v,
        "canonical_text":(a if a else l),"witness_families_independent_collated":collated,
        "independent_family_count":len(collated),"variant_classification":vclass,
        "confidence":{"independent_families":len(collated),"score":(0.98 if ('full agreement' in vclass) else (0.8 if len(collated)==2 else 0.6))}})

summary={"total":len(results),
 "aufrecht_vs_padapatha_agree":agree_auf_pp,
 "lubotsky_vs_padapatha_agree":agree_lub_pp,
 "aufrecht_vs_lubotsky_agree":agree_auf_lub,
 "single_family_only":single}
out={"scripture":"RV","method":"3-way: 2 independent samhita families resolved to pada form vs Padapatha (F-PADAPATHA) reference. Trailing sandhi finals stripped; accents stripped; compounds split at hyphen.",
 "summary":summary,"cuid":results}
json.dump(out,open("knowledge/dtc/rigveda/cuid_baseline_3ref.json","w",encoding='utf-8'),ensure_ascii=False,indent=1)
print("Wrote cuid_baseline_3ref.json:",len(results))
print(json.dumps(summary,indent=1))
print("\nCandidate genuine variants (Aufrecht vs Padapatha word diffs):")
for g in genuine_auf[:25]: print(" ",g[0],"A-only:",g[1],"PP-only:",g[2])
