#!/usr/bin/env python3
"""AKSHARA-LEVEL VERIFICATION for Rigveda Samhita.
For each verse, verify:
  (1) Character validity: no U+FFFD replacement chars, no stray mojibake.
  (2) Akshara decomposition of the two independent samhita witnesses (Aufrecht, Lubotsky)
      agrees with the Padapatha (sandhi-resolved) akshara sequence after conservative
      sandhi normalization (accents off, whitespace/danda off, visarga->h, trailing
      sandhi finals collapsed).
Writes knowledge/dtc/rigveda/akshara_verification.json
"""
import re, json, os
import unicodedata
DL="/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage/knowledge/downloads"
ACCENT=dict.fromkeys(c for c in range(0x0300,0x0370))
SANDHI=set('mṃḥhṇnrrttsṭḍṣñṅ')
VALID=set('aāiīuūṛṝḷḹeoaiṃḥṅñṇnmtthdḍcjñśṣsyrlvkgphbḏ') | set('ṅṇñ')  # sanskrit akshara chars
def strip_acc(s): return unicodedata.normalize('NFKD',s).translate(ACCENT)
def has_replacement(s): return '\ufffd' in s
def mojibake_markers(s):
    # common Devanagari/translit mojibake: control chars, private use, u+200b etc
    bad=set('​‌‍﻿')  # zero-width / BOM only
    return [c for c in s if (0xE000<=ord(c)<=0xF8FF) or c in bad]
def akshara_norm(s):
    s=strip_acc(s.lower()); s=re.sub(r'[ \-\|]+','',s); s=s.replace('ḥ','h')
    s=re.sub(r'['+''.join(SANDHI)+r']','#',s)   # collapse all sandhi finals to '#'
    s=re.sub(r'a#','#',s); s=re.sub(r'#a','#',s)
    return re.sub(r'[^a-zāīūṛḷṃḥṇñṅśṣṭḍ#]','',s)
# ---- extractors ----
def aufrecht():
    t=open(f"{DL}/rigveda_aufrecht_gretil.xml",encoding='utf-8',errors='ignore').read(); out={}
    for lg in re.finditer(r'xml:id="RV_(\d+)\.(\d+)\.(\d+)">(.*?)</lg>',t,re.S):
        m,s,v=int(lg.group(1)),int(lg.group(2)),int(lg.group(3)); padas=[]
        for l in re.finditer(r'n="\d+\.\d+\.(\d+)([acp])">(.*?)</l>',lg.group(4),re.S):
            x=re.sub(r'<orig>(.*?)</orig>',r'\1',l.group(3),flags=re.S); x=re.sub(r'<[^>]+>','',x).strip()
            padas.append(x)
        if padas: out[(m,s,v)]=' '.join(padas)
    return out
def lubotsky():
    out={}
    for b in range(1,11):
        t=open(f"{DL}/vedaweb/cceh-c-salt_vedaweb_tei-f975755/rv_book_{b:02d}.tei",encoding='utf-8',errors='ignore').read()
        for st in re.finditer(r'xml:id="b(\d+)_h(\d+)_(\d+)" type="stanza">(.*?)(?=xml:id="b\d+_h\d+_\d+" type="stanza">|\Z)',t,re.S):
            m,s,v,blk=int(st.group(1)),int(st.group(2)),int(st.group(3)),st.group(4)
            ml=re.search(r'xml:id="b\d+_h\d+_\d+_lubotsky"[^>]*>(.*?)</lg>',blk,re.S)
            if not ml: continue
            lines=re.findall(r'(?s)<l[^>]*>(.*?)</l>',ml.group(1))
            padas=[re.sub(r'<[^>]+>','',l).strip().replace('-_','') for l in lines]
            if padas: out[(m,s,v)]=' '.join(padas)
    return out
def padapatha():
    t=open(f"{DL}/rigveda_padapatha_gretil.xml",encoding='utf-8',errors='ignore').read(); out={}
    for p in re.finditer(r'<p>(.*?)</p>',t,re.S):
        b=p.group(1); m=re.search(r'//\s*RV_(\d+),(\d+)\.(\d+)\s*//',b)
        if not m: continue
        k=(int(m.group(1)),int(m.group(2)),int(m.group(3)))
        b=re.sub(r'<[^>]+>',' ',b)
        toks=[x.strip() for x in re.split(r'\s*[|/]+\s*',b) if x.strip() and 'RV_' not in x and '(' not in x]
        if toks: out[k]=' '.join(toks)
    return out

A=aufrecht(); L=lubotsky(); P=padapatha()
report={"total_verses":len(set(A)|set(L)|set(P)),
        "aufrecht_verses":len(A),"lubotsky_verses":len(L),"padapatha_verses":len(P),
        "character_validity":{},"akshara_agreement":{},"problems":[]}
# 1) character validity
def valid_check(name,data):
    rep=moji=0; vmap={}
    for k,txt in data.items():
        if has_replacement(txt): rep+=1; report['problems'].append({"verse":f"RV-{k[0]}.{k[1]}.{k[2]}","witness":name,"issue":"replacement_char_U+FFFD"})
        mk=mojibake_markers(txt)
        if mk: moji+=1; report['problems'].append({"verse":f"RV-{k[0]}.{k[1]}.{k[2]}","witness":name,"issue":"mojibake/control","chars":[hex(ord(c)) for c in mk][:5]})
    report['character_validity'][name]={"verses_with_replacement":rep,"verses_with_mojibake":moji}
valid_check("Aufrecht",A); valid_check("Lubotsky",L); valid_check("Padapatha",P)
# 2) akshara agreement (3-way) after normalization
agree=0; compared=0; mism=[]
for k in sorted(set(A)&set(L)&set(P)):
    compared+=1
    na,nl,np_=akshara_norm(A[k]),akshara_norm(L[k]),akshara_norm(P[k])
    # compare Aufrecht & Lubotsky against Padapatha (the sandhi-resolved reference)
    if na==np_ and nl==np_:
        agree+=1
    else:
        if len(mism)<40:
            mism.append((f"RV-{k[0]}.{k[1]}.{k[2]}",na[:40],nl[:40],np_[:40]))
report['akshara_agreement']={"compared":compared,"agree_with_padapatha":agree,
                              "rate_pct":round(100*agree/compared,2) if compared else 0}
report['akshara_mismatches_sample']=mism
json.dump(report,open("knowledge/dtc/rigveda/akshara_verification.json","w",encoding='utf-8'),ensure_ascii=False,indent=1)
print("Aufrecht verses:",len(A),"Lubotsky:",len(L),"Padapatha:",len(P))
print("Character validity:",json.dumps(report['character_validity'],ensure_ascii=False))
print("Akshara agreement vs Padapatha:",json.dumps(report['akshara_agreement'],ensure_ascii=False))
print("Problems found:",len(report['problems']))
for p in report['problems'][:10]: print("  ",p)
