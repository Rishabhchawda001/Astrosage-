#!/usr/bin/env python3
"""
Unified OCR Pipeline for Hindi/Devanagari/Sanskrit texts
Supports PDF, DJVU, and image-based extraction with Tesseract
"""
import os
import json
import re
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

try:
    import pytesseract
    from PIL import Image
    import pdfplumber
    import fitz  # pymupdf
    HAS_OCR = True
except ImportError as e:
    print(f"OCR dependencies not fully available: {e}")
    HAS_OCR = False

TESSERACT_LANG = "hin+san+eng"
TESSERACT_CONFIG = "--psm 6 --oem 1"

# Common OCR error patterns for Hindi/Sanskrit
OCR_FIXES = [
    # Visarga fixes
    (r'ः\s*([क-ह])', r'ः\1'),
    (r'([क-ह])\s*ः', r'\1ः'),
    # Anusvara fixes
    (r'ं\s*([क-ह])', r'ं\1'),
    (r'([क-ह])\s*ं', r'\1ं'),
    # Danda fixes
    (r'\|\s*\|', r'||'),
    (r'\s+\|\s+', ' | '),
    (r'\s+\|\|\s+', ' || '),
    # Common character confusions
    (r'द्व', 'द्व'),
    (r'त्त', 'त्त'),
    (r'क्त', 'क्त'),
    (r'ष्ट', 'ष्ट'),
    (r'ज्ञ', 'ज्ञ'),
    (r'श्र', 'श्र'),
    (r'त्र', 'त्र'),
    # Remove page numbers, headers, footers
    (r'^\s*\d+\s*$', ''),
    (r'^\s*Page\s+\d+\s*$', '', re.IGNORECASE),
    (r'^\s*[िविद्या\s]+\d+\s*$', ''),
    # Normalize whitespace
    (r'\n{3,}', '\n\n'),
    (r'[ \t]+', ' '),
]

def normalize_devanagari(text: str) -> str:
    """Apply common OCR fixes for Devanagari text"""
    for pattern, repl, *flags in OCR_FIXES:
        flag = flags[0] if flags else 0
        text = re.sub(pattern, repl, text, flags=flag)
    return text.strip()

def detect_language(text: str) -> str:
    """Detect if text is primarily Devanagari, Latin, or mixed"""
    devanagari = len(re.findall(r'[\u0900-\u097F]', text))
    latin = len(re.findall(r'[a-zA-Z]', text))
    total = devanagari + latin
    if total == 0:
        return 'unknown'
    if devanagari / total > 0.5:
        return 'devanagari'
    if latin / total > 0.5:
        return 'latin'
    return 'mixed'

def score_ocr_quality(text: str) -> Tuple[float, Dict]:
    """Score OCR quality 0-100"""
    metrics = {}
    
    # Replacement chars
    repl = text.count('\ufffd')
    metrics['replacement_chars'] = repl
    
    # Mojibake / private use
    pua = sum(1 for c in text if 0xE000 <= ord(c) <= 0xF8FF)
    metrics['pua_chars'] = pua
    
    # Garbled sequences (repeated same char, or random)
    garbled = len(re.findall(r'(.)\1{4,}', text))
    metrics['garbled_sequences'] = garbled
    
    # Devanagari validity
    devanagari_chars = len(re.findall(r'[\u0900-\u097F]', text))
    total_chars = len([c for c in text if not c.isspace()])
    metrics['devanagari_ratio'] = devanagari_chars / max(1, total_chars)
    
    # Word-like structures
    words = text.split()
    metrics['word_count'] = len(words)
    avg_word_len = sum(len(w) for w in words) / max(1, len(words))
    metrics['avg_word_length'] = avg_word_len
    
    # Score calculation
    score = 100.0
    if total_chars > 0:
        score -= min(50, (repl / total_chars) * 1000)
        score -= min(30, (pua / total_chars) * 1000)
        score -= min(20, garbled * 2)
        if metrics['devanagari_ratio'] < 0.3:
            score -= 20
        if avg_word_len < 2 or avg_word_len > 20:
            score -= 15
    
    metrics['quality_score'] = max(0, min(100, score))
    return metrics['quality_score'], metrics

class OCRPipeline:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = []
    
    def extract_pdf_native(self, pdf_path: str) -> Optional[str]:
        """Try to extract native text from PDF"""
        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text()
                    if txt:
                        text_parts.append(txt)
            if text_parts:
                full = '\n\n'.join(text_parts)
                if len(full.strip()) > 100:
                    return full
        except Exception as e:
            print(f"  Native PDF extraction failed: {e}")
        return None
    
    def extract_pdf_pymupdf(self, pdf_path: str) -> Optional[str]:
        """Try PyMuPDF extraction"""
        try:
            doc = fitz.open(pdf_path)
            text_parts = []
            for page in doc:
                txt = page.get_text()
                if txt:
                    text_parts.append(txt)
            doc.close()
            if text_parts:
                full = '\n\n'.join(text_parts)
                if len(full.strip()) > 100:
                    return full
        except Exception as e:
            print(f"  PyMuPDF extraction failed: {e}")
        return None
    
    def pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[Image.Image]:
        """Convert PDF pages to images"""
        try:
            doc = fitz.open(pdf_path)
            images = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                mat = fitz.Matrix(dpi/72, dpi/72)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            doc.close()
            return images
        except Exception as e:
            print(f"  PDF to images failed: {e}")
            return []
    
    def djvu_to_images(self, djvu_path: str) -> List[Image.Image]:
        """Convert DJVU to images using ddjvu"""
        images = []
        try:
            # Get page count
            result = subprocess.run(['djvused', djvu_path, '-e', 'print-pages'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return images
            
            # Extract each page
            page_count = int(result.stdout.strip())
            for i in range(page_count):
                out_path = f"/tmp/djvu_page_{i}.png"
                result = subprocess.run(['ddjvu', '-format=png', '-page', str(i+1), 
                                       djvu_path, out_path], 
                                      capture_output=True, timeout=60)
                if result.returncode == 0 and os.path.exists(out_path):
                    images.append(Image.open(out_path))
        except Exception as e:
            print(f"  DJVU to images failed: {e}")
        return images
    
    def ocr_image(self, image: Image.Image) -> str:
        """Run Tesseract OCR on image"""
        if not HAS_OCR:
            return ""
        try:
            text = pytesseract.image_to_string(image, lang=TESSERACT_LANG, config=TESSERACT_CONFIG)
            return text
        except Exception as e:
            print(f"  Tesseract OCR failed: {e}")
            return ""
    
    def process_pdf(self, pdf_path: str, scripture_id: str) -> Dict:
        """Process a PDF file through the OCR pipeline"""
        print(f"Processing PDF: {pdf_path}")
        
        # Try native extraction first
        native_text = self.extract_pdf_native(pdf_path)
        if native_text:
            print("  Native text extraction successful")
            text = native_text
            method = "native_pdfplumber"
        else:
            native_text = self.extract_pdf_pymupdf(pdf_path)
            if native_text:
                print("  PyMuPDF extraction successful")
                text = native_text
                method = "native_pymupdf"
            else:
                # Fall back to OCR
                print("  No native text, running OCR...")
                images = self.pdf_to_images(pdf_path)
                if not images:
                    return {"success": False, "error": "No images extracted"}
                
                text_parts = []
                for i, img in enumerate(images):
                    print(f"  OCR page {i+1}/{len(images)}...")
                    page_text = self.ocr_image(img)
                    if page_text:
                        text_parts.append(page_text)
                
                text = '\n\n'.join(text_parts)
                method = "ocr_tesseract"
        
        # Clean and score
        cleaned = normalize_devanagari(text)
        lang = detect_language(cleaned)
        score, metrics = score_ocr_quality(cleaned)
        
        # Save output
        base = Path(pdf_path).stem
        out_path = self.output_dir / f"{base}_ocr.txt"
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        
        result = {
            "input_file": pdf_path,
            "output_file": str(out_path),
            "scripture_id": scripture_id,
            "method": method,
            "language": lang,
            "quality_score": score,
            "metrics": metrics,
            "text_length": len(cleaned),
            "checksum": hashlib.sha256(cleaned.encode()).hexdigest()[:16],
            "processed_at": datetime.utcnow().isoformat() + 'Z'
        }
        self.manifest.append(result)
        return result
    
    def process_djvu(self, djvu_path: str, scripture_id: str) -> Dict:
        """Process a DJVU file"""
        print(f"Processing DJVU: {djvu_path}")
        
        # Try djvutxt first (native text layer)
        try:
            result = subprocess.run(['djvutxt', djvu_path], capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and len(result.stdout.strip()) > 100:
                text = result.stdout
                method = "native_djvutxt"
            else:
                raise Exception("No native text layer")
        except:
            # Fall back to image OCR
            images = self.djvu_to_images(djvu_path)
            if not images:
                return {"success": False, "error": "No images extracted from DJVU"}
            
            text_parts = []
            for i, img in enumerate(images):
                print(f"  OCR page {i+1}/{len(images)}...")
                page_text = self.ocr_image(img)
                if page_text:
                    text_parts.append(page_text)
            
            text = '\n\n'.join(text_parts)
            method = "ocr_tesseract"
        
        cleaned = normalize_devanagari(text)
        lang = detect_language(cleaned)
        score, metrics = score_ocr_quality(cleaned)
        
        base = Path(djvu_path).stem
        out_path = self.output_dir / f"{base}_ocr.txt"
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        
        result = {
            "input_file": djvu_path,
            "output_file": str(out_path),
            "scripture_id": scripture_id,
            "method": method,
            "language": lang,
            "quality_score": score,
            "metrics": metrics,
            "text_length": len(cleaned),
            "checksum": hashlib.sha256(cleaned.encode()).hexdigest()[:16],
            "processed_at": datetime.utcnow().isoformat() + 'Z'
        }
        self.manifest.append(result)
        return result
    
    def process_text(self, txt_path: str, scripture_id: str) -> Dict:
        """Process an existing text file (cleanup only)"""
        with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        cleaned = normalize_devanagari(text)
        lang = detect_language(cleaned)
        score, metrics = score_ocr_quality(cleaned)
        
        base = Path(txt_path).stem
        out_path = self.output_dir / f"{base}_cleaned.txt"
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        
        result = {
            "input_file": txt_path,
            "output_file": str(out_path),
            "scripture_id": scripture_id,
            "method": "text_cleanup",
            "language": lang,
            "quality_score": score,
            "metrics": metrics,
            "text_length": len(cleaned),
            "checksum": hashlib.sha256(cleaned.encode()).hexdigest()[:16],
            "processed_at": datetime.utcnow().isoformat() + 'Z'
        }
        self.manifest.append(result)
        return result
    
    def process_file(self, file_path: str, scripture_id: str) -> Dict:
        """Route to appropriate processor based on file type"""
        ext = Path(file_path).suffix.lower()
        if ext == '.pdf':
            return self.process_pdf(file_path, scripture_id)
        elif ext in ['.djvu', '.djv']:
            return self.process_djvu(file_path, scripture_id)
        elif ext == '.txt':
            return self.process_text(file_path, scripture_id)
        else:
            return {"success": False, "error": f"Unsupported file type: {ext}"}
    
    def save_manifest(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.manifest, f, indent=2)
        print(f"Manifest saved to {path}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input file or directory')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--scripture', required=True, help='Scripture ID')
    parser.add_argument('--manifest', help='Manifest output path')
    args = parser.parse_args()
    
    pipeline = OCRPipeline(args.output)
    
    input_path = Path(args.input)
    if input_path.is_file():
        result = pipeline.process_file(str(input_path), args.scripture)
        print(json.dumps(result, indent=2))
    elif input_path.is_dir():
        for f in input_path.rglob('*'):
            if f.is_file() and not f.name.startswith('.'):
                result = pipeline.process_file(str(f), args.scripture)
                print(json.dumps(result, indent=2))
    else:
        print(f"Input not found: {args.input}")
        return 1
    
    if args.manifest:
        pipeline.save_manifest(args.manifest)
    return 0

if __name__ == '__main__':
    exit(main())
