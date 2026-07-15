#!/usr/bin/env python3
"""Resolve each samhita-form word to a concatenation of 1-3 consecutive Padapatha morphemes.
Correct inverse of pada->samhita sandhi join. Per-word local match (no shared global pointer).
If EVERY samhita word resolves, the verse is a pure sandhi/segmentation variant (no lexical diff)."""
import re, json, os
from collections import Counter
import unicodedata

DL="/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/downloads"
ACCENT=dict.fromkeys(c for c in range(0x0300,0x0370))
SANDHI=set('mṃḥhṇnrrttsṭḍṣñṅ')
def strip_acc(s): return unicodedata.normalize('NFKD',s).translate(ACCENT)
def base(w):
    w=strip_acc(w.lower()); w=re.sub(r'[-]','',w)
    return re.sub(r'[^a-zāīūṛḷṃḥṇñṅśṣṭḍ]','',w)
def pada(w):
    w=base(w); return re.sub(r'['+''.join(SANDHI)+r']+$','',w)

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

def split_words(text): return [base(w) for w in re.split(r'[ \-\|]+', text) if base(w)]
def pp_pada_list(tokens): return [pada(t) for t in re.split(r'[ \-\|]+',' '.join(tokens)) if pada(t)]

def word_resolves(sw, pp):
    sw=pada(sw)
    if not sw: return True
    if sw in pp: return True
    # concatenation of 2 consecutive pp morphemes
    for i in range(len(pp)-1):
        if sw==pp[i]+pp[i+1]: return True
    for i in range(len(pp)-2):
        if sw==pp[i]+pp[i+1]+pp[i+2]: return True
    return False

auf=extract_aufrecht(f"{DL}/rigveda_aufrecht_gretil.xml"); lub={}
for b in range(1,11):
    p=f"{DL}/vedaweb/cceh-c-salt_vedaweb_tei-f975755/rv_book_{b:02d}.tei"
    if os.path.exists(p): lub.update(extract_lubotsky(p))
pp=json.load(open('/tmp/padapatha.json'))

a_full=0; l_full=0; al_full=0; single=0; unresolved=[]
for (m,s,v) in sorted(set(auf)|set(lub)|set((int(k.split('.')[0]),int(k.split('.')[1]),int(k.split('.')[2])) for k in pp)):
    key=f"{m}.{s}.{v}"
    a=auf.get((m,s,v)); l=lub.get((m,s,v)); ppt=pp.get(key)
    if ppt is None:
        if a or l: single+=1
        continue
    ppw=pp_pada_list(ppt)
    am = all(word_resolves(w,ppw) for w in split_words(a)) if a else None
    lm = all(word_resolves(w,ppw) for w in split_words(l)) if l else None
    if a and am: a_full+=1
    if l and lm: l_full+=1
    if a and l and am and lm: al_full+=1
    elif (a and not am) or (l and not lm):
        if len(unresolved)<40: unresolved.append((key, am, lm,
            [w for w in split_words(a) if not word_resolves(w,ppw)] if a else [],
            [w for w in split_words(l) if not word_resolves(w,ppw)] if l else []))
summary={"verses_with_padapatha":len(pp),
 "aufrecht_resolves_pure_sandhi":a_full,
 "lubotsky_resolves_pure_sandhi":l_full,
 "both_resolve_equal":al_full,
 "single_family_no_padapatha":single}
print(json.dumps(summary,indent=1))
print("\nGENUINE candidate lexical variants (words not resolvable to Padapatha):")
for u in unresolved: print(" ",u[0],"A_unres:",u[3],"L_unres:",u[4])
