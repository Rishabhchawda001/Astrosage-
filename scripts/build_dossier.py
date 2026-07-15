#!/usr/bin/env python3
"""
Build Scripture Dossier — Digital Textual Criticism

For every scripture with GRETIL XML, build a complete dossier.
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from collections import Counter

TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}


def extract_xml_metadata(xml_path):
    """Extract metadata from TEI XML."""
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError:
        return None
    
    root = tree.getroot()
    
    title_el = root.find(".//tei:titleStmt/tei:title", NS)
    title = title_el.text.strip() if title_el is not None and title_el.text else ""
    
    editor_els = root.findall(".//tei:respStmt/tei:name", NS)
    editors = [e.text.strip() for e in editor_els if e.text]
    
    source_el = root.find(".//tei:sourceDesc/tei:bibl", NS)
    source = source_el.text.strip() if source_el is not None and source_el.text else ""
    
    licence_el = root.find(".//tei:availability/tei:licence", NS)
    licence = ""
    if licence_el is not None:
        licence = licence_el.get("target", "") or (licence_el.text or "").strip()
    
    # Count body units
    body = root.find(".//tei:body", NS)
    unit_count = 0
    if body is not None:
        for child in body:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag in ("p", "lg", "l"):
                unit_count += 1
            elif tag == "div":
                for gc in child:
                    gc_tag = gc.tag.split("}")[-1] if "}" in gc.tag else gc.tag
                    if gc_tag in ("p", "lg", "l"):
                        unit_count += 1
    
    return {
        "title": title,
        "editors": editors,
        "source": source,
        "licence": licence,
        "unit_count": unit_count,
    }


def build_dossier(scripture_name, xml_files, txt_files, aku_file=None):
    """Build a complete dossier for a scripture."""
    
    dossier = {
        "canonical_name": scripture_name,
        "witnesses": {
            "gretil_xml": [],
            "publisher_unicode": [],
            "publisher_ocr": [],
            "other": [],
        },
        "total_witnesses": 0,
        "verification_status": "pending",
    }
    
    # Process XML files
    for fn in xml_files:
        fp = os.path.join("knowledge/downloads", fn)
        if not os.path.exists(fp):
            continue
        
        meta = extract_xml_metadata(fp)
        if meta:
            dossier["witnesses"]["gretil_xml"].append({
                "file": fn,
                "title": meta["title"],
                "editors": meta["editors"],
                "source": meta["source"],
                "licence": meta["licence"],
                "unit_count": meta["unit_count"],
                "authority": "High",
            })
    
    # Process TXT files
    for fn in txt_files:
        fp = os.path.join("knowledge/downloads", fn)
        if not os.path.exists(fp):
            continue
        
        size = os.path.getsize(fp)
        
        # Detect script
        with open(fp, encoding="utf-8", errors="replace") as f:
            text = f.read(5000)
        
        devanagari = sum(1 for c in text if "\u0900" <= c <= "\u097F")
        total = max(len(text), 1)
        quality = devanagari / total
        
        # Detect publisher
        publisher = "unknown"
        for pub, keywords in [
            ("Gita Press", ["gita_press", "gitapress"]),
            ("Chowkhamba", ["chowkhamba", "chaukhamba"]),
            ("Anandashram", ["anand"]),
            ("Motilal", ["motilal"]),
            ("Nag", ["nag_publishers"]),
            ("Venkateshwar", ["venkateshwar"]),
        ]:
            if any(k in fn.lower() for k in keywords):
                publisher = pub
                break
        
        witness_type = "publisher_unicode" if quality > 0.5 else "publisher_ocr"
        
        dossier["witnesses"][witness_type].append({
            "file": fn,
            "publisher": publisher,
            "quality": round(quality, 2),
            "size_kb": round(size / 1024),
            "authority": "Medium" if quality > 0.7 else "Low",
        })
    
    # Count totals
    dossier["total_witnesses"] = (
        len(dossier["witnesses"]["gretil_xml"]) +
        len(dossier["witnesses"]["publisher_unicode"]) +
        len(dossier["witnesses"]["publisher_ocr"])
    )
    
    return dossier


def main():
    # Build dossiers for scriptures with GRETIL XML
    xml_dir = "knowledge/downloads"
    aku_dir = "knowledge/cuv/gretil_prose_clean"
    dossier_dir = "knowledge/cuv/dossiers"
    
    os.makedirs(dossier_dir, exist_ok=True)
    
    # Get all GRETIL XML files
    xml_files = [f for f in os.listdir(xml_dir) if f.endswith(".xml") and f.startswith("sa_")]
    txt_files = [f for f in os.listdir(xml_dir) if f.endswith(".txt")]
    
    # Group XML files by scripture
    scriptures = {}
    for fn in xml_files:
        # Extract scripture name from filename
        base = fn.replace("sa_", "").replace(".xml", "")
        scriptures.setdefault(base, {"xml": [], "txt": []})["xml"].append(fn)
    
    # Map txt files to scriptures
    for fn in txt_files:
        base = fn.lower().replace(".txt", "")
        for sci_name in scriptures:
            if sci_name.lower().replace("_", "")[:10] in base.replace("_", ""):
                scriptures[sci_name]["txt"].append(fn)
                break
    
    # Build dossiers
    for sci_name, files in sorted(scriptures.items()):
        dossier = build_dossier(sci_name, files["xml"], files["txt"])
        
        # Save
        out_fn = f"{sci_name.lower().replace(' ', '_')}.json"
        out_path = os.path.join(dossier_dir, out_fn)
        
        with open(out_path, "w") as f:
            json.dump(dossier, f, indent=2, ensure_ascii=False)
        
        witnesses = dossier["total_witnesses"]
        print(f"  {sci_name[:50]:50s} {witnesses:2d} witnesses")
    
    print(f"\nTotal dossiers: {len(scriptures)}")


if __name__ == "__main__":
    main()
