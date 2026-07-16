#!/usr/bin/env python3
"""
AstroSage Source Discovery Engine
Searches all repositories for Hindu scripture digital editions.
Maintains download queue, verification queue, failed queue.
"""
import json
import os
import time
import urllib.request
import urllib.parse
import hashlib
from pathlib import Path
from datetime import datetime

BASE = Path("/root/Documents/Codex/2026-07-11/astrosage-name-of-this-thread/astrosage")
DTC = BASE / "knowledge" / "dtc"

class DiscoveryEngine:
    def __init__(self):
        self.download_queue = []
        self.verification_queue = []
        self.failed_queue = []
        self.search_log = []
        self.negative_search_log = []
        self.discovered = []
        self.repositories_searched = set()
        
        # Scripture search terms
        self.scripture_terms = {
            "KATHA_UPANISHAD": ["katha upanishad", "kaṭha upaniṣad", "kāṭhopaniṣad", "katha", "kaṭha"],
            "VAISHESHIKA": ["vaisheshika sutra", "vaiśeṣika sūtra", "vaisheshika", "kanada sutra", "kāṇāda"],
            "VYASA_SM": ["vyasa smriti", "vyāsa smṛti", "vyasa samhita", "vyāsa"],
            "SAMAVEDA": ["samaveda samhita", "sāmaveda", "sama veda kauthuma", "sāmaveda saṃhitā"],
            "KALI_PURANA": ["kalika purana", "kālīkā purāṇa", "kalika", "kālī"],
            "MAHABHARATA": ["mahabharata sanskrit", "mahābhārata", "bharata"],
            "RIGVEDA": ["rigveda samhita", "ṛgveda", "rig veda"],
            "YAJURVEDA": ["yajurveda", "yajur veda", "yajurveda samhita"],
            "ATHARVAVEDA": ["atharvaveda", "atharva veda", "atharvaveda samhita"],
            "RAMAYANA": ["ramayana sanskrit", "rāmāyaṇa"],
            "BHAGAVATA": ["bhagavata purana", "bhāgavata purāṇa", "shrimad bhagavatam"],
            "AGNI_PURANA": ["agni purana", "agni purāṇa"],
            "VISHNU_PURANA": ["vishnu purana", "viṣṇu purāṇa"],
            "BRAHMA_PURANA": ["brahma purana", "brahmāṇḍa purāṇa"],
            "SKANDA_PURANA": ["skanda purana", "skanda purāṇa"],
            "MARKANDEYA_PURANA": ["markandeya purana", "mārkaṇḍeya purāṇa"],
            "GARUDA_PURANA": ["garuda purana", "garuḍa purāṇa"],
            "LINGA_PURANA": ["linga purana", "liṅga purāṇa"],
            "VAMANA_PURANA": ["vamana purana", "vāmana purāṇa"],
            "KURMA_PURANA": ["kurma purana", "kūrma purāṇa"],
            "MATSYA_PURANA": ["matsya purana", "matsya purāṇa"],
            "NARADA_PURANA": ["narada purana", "nārada purāṇa"],
            "NARASIMHA_PURANA": ["narasimha purana", "nārasiṃha purāṇa"],
            "YAJNAVALKYA_SM": ["yajnavalkya smriti", "yājñavalkya smṛti", "yajnavalkya"],
            "MANU_SM": ["manusmriti", "manu smriti", "manava dharmashastra"],
            "SHIVA_PURANA": ["shiva purana", "śiva purāṇa"],
            "DEVAGITA": ["devi gita", "devī gītā"],
            "BHAGAVAD_GITA": ["bhagavad gita sanskrit", "bhagavad gītā"],
            "YOGA_SUTRA": ["yoga sutra patanjali", "yoga sūtra", "patañjali yoga"],
            "VEDANTA_SUTRA": ["brahma sutra", "vedanta sutra", "vedānta sūtra"],
            "NYAYA_SUTRA": ["nyaya sutra", "nyāya sūtra", "gaudapada"],
            "YOGA_VASISTHA": ["yoga vasistha", "yoga vāsiṣṭha", "mokshopaya"],
            "DEVI_BHAGAVATA": ["devi bhagavata", "devī bhāgavata"],
            "BRAHMA_VAIVARTA": ["brahma vaivarta purana", "brahma vaivarta"],
            "PARASHARA_SM": ["parashara smriti", "pārāśara smṛti"],
            "SHVETASHVATARA": ["shvetashvatara upanishad", "śvetāśvatara upaniṣad"],
            "CHANDOGYA": ["chandogya upanishad", "chāndogya upaniṣad"],
            "BRIHADARANYAKA": ["brihadaranyaka upanishad", "bṛhadāraṇyaka upaniṣad"],
            "AITAREYA": ["aitareya upanishad", "aitareya"],
            "ISHA": ["isha upanishad", "īśā upaniṣad"],
            "KENA": ["kena upanishad", "kena"],
            "KAUSHITAKI": ["kaushitaki upanishad", "kauṣītaki"],
            "PRASHNA": ["prashna upanishad", "praśna upaniṣad"],
            "MANDUKYA": ["mandukya upanishad", "māṇḍūkya"],
            "MUNDAKA": ["mundaka upanishad", "muṇḍaka"],
            "MAITRI": ["maitri upanishad", "maitrī"],
            "TAITTIRIYA": ["taittiriya upanishad", "taittirīya"],
        }
    
    def search_archive_org(self, query, max_results=20):
        """Search Archive.org advanced search API."""
        try:
            url = f"https://archive.org/advancedsearch.php?q={urllib.parse.quote(query)}&fl[]=identifier,title&output=json&rows={max_results}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read().decode())
            results = data.get("response", {}).get("docs", [])
            self.search_log.append({
                "repository": "archive.org",
                "query": query,
                "results": len(results),
                "timestamp": datetime.now().isoformat(),
            })
            return results
        except Exception as e:
            self.failed_queue.append({
                "repository": "archive.org",
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })
            return []
    
    def search_openalex(self, query, max_results=20):
        """Search OpenAlex for academic works."""
        try:
            url = f"https://api.openalex.org/works?search={urllib.parse.quote(query)}&per_page={max_results}"
            req = urllib.request.Request(url, headers={"User-Agent": "AstroSage/1.0"})
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read().decode())
            results = data.get("results", [])
            self.search_log.append({
                "repository": "openalex",
                "query": query,
                "results": len(results),
                "timestamp": datetime.now().isoformat(),
            })
            return [{"title": r.get("title", ""), "id": r.get("id", ""), "doi": r.get("doi", "")} for r in results]
        except Exception as e:
            self.failed_queue.append({
                "repository": "openalex",
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })
            return []
    
    def search_sanskritdocuments(self, query):
        """Search SanskritDocuments.org."""
        try:
            url = f"https://sanskritdocuments.org/search.php?k1={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "text/html,*/*",
            })
            resp = urllib.request.urlopen(req, timeout=10)
            content = resp.read().decode("utf-8", errors="replace")
            self.search_log.append({
                "repository": "sanskritdocuments.org",
                "query": query,
                "results": len(content),
                "timestamp": datetime.now().isoformat(),
            })
            return content
        except Exception as e:
            self.failed_queue.append({
                "repository": "sanskritdocuments.org",
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })
            return ""
    
    def search_crossref(self, query, max_results=20):
        """Search CrossRef for DOIs."""
        try:
            url = f"https://api.crossref.org/works?query={urllib.parse.quote(query)}&rows={max_results}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "AstroSage/1.0 (mailto:astrosage@knowledge-recovery.org)"
            })
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read().decode())
            items = data.get("message", {}).get("items", [])
            self.search_log.append({
                "repository": "crossref",
                "query": query,
                "results": len(items),
                "timestamp": datetime.now().isoformat(),
            })
            return [{"title": r.get("title", [""])[0], "DOI": r.get("DOI", ""), "publisher": r.get("publisher", "")} for r in items]
        except Exception as e:
            self.failed_queue.append({
                "repository": "crossref",
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })
            return []
    
    def check_already_acquired(self, identifier):
        """Check if this source is already downloaded."""
        for f in os.listdir("knowledge/downloads"):
            if identifier.lower() in f.lower():
                return True
        for f in os.listdir("knowledge/gretil_parsed"):
            if identifier.lower() in f.lower():
                return True
        return False
    
    def run_discovery_cycle(self):
        """Run one full discovery cycle across all repositories."""
        print("=" * 70)
        print(f"DISCOVERY CYCLE — {datetime.now().isoformat()}")
        print("=" * 70)
        
        cycle_results = {
            "timestamp": datetime.now().isoformat(),
            "searches": 0,
            "discovered": 0,
            "already_acquired": 0,
            "new_candidates": [],
        }
        
        # Search each scripture across multiple repositories
        for scripture, terms in self.scripture_terms.items():
            print(f"\n--- {scripture} ---")
            for term in terms[:2]:  # Search top 2 terms per scripture
                # Archive.org
                results = self.search_archive_org(f"{term} sanskrit text", max_results=10)
                cycle_results["searches"] += 1
                for r in results:
                    ident = r.get("identifier", "")
                    title = r.get("title", "")
                    if self.check_already_acquired(ident):
                        cycle_results["already_acquired"] += 1
                    else:
                        cycle_results["new_candidates"].append({
                            "scripture": scripture,
                            "repository": "archive.org",
                            "identifier": ident,
                            "title": title,
                        })
                        cycle_results["discovered"] += 1
                
                # OpenAlex
                oa_results = self.search_openalex(f"{term} sanskrit digital edition", max_results=5)
                cycle_results["searches"] += 1
                for r in oa_results:
                    title = r.get("title", "")
                    if title and not self.check_already_acquired(title[:30]):
                        cycle_results["new_candidates"].append({
                            "scripture": scripture,
                            "repository": "openalex",
                            "title": title,
                            "doi": r.get("doi", ""),
                        })
                        cycle_results["discovered"] += 1
                
                time.sleep(0.5)  # Rate limiting
        
        return cycle_results
    
    def run_extended_search(self):
        """Run extended searches for additional sources."""
        print("\n" + "=" * 70)
        print("EXTENDED SEARCH — Additional repositories")
        print("=" * 70)
        
        extended = {
            "timestamp": datetime.now().isoformat(),
            "new_candidates": [],
        }
        
        # Search for critical editions
        critical_searches = [
            "critical edition sanskrit purana",
            "tei xml sanskrit digital",
            "unicode sanskrit text gretil",
            "sanskrit manuscript digitized",
            "veda sanskrit digital edition",
            "upanishad sanskrit text",
            "smriti sanskrit digital",
            "darshana sanskrit text",
        ]
        
        for query in critical_searches:
            results = self.search_archive_org(query, max_results=10)
            for r in results:
                ident = r.get("identifier", "")
                title = r.get("title", "")
                if not self.check_already_acquired(ident):
                    extended["new_candidates"].append({
                        "repository": "archive.org",
                        "identifier": ident,
                        "title": title,
                    })
            time.sleep(0.5)
        
        return extended

if __name__ == "__main__":
    engine = DiscoveryEngine()
    
    # Run main discovery cycle
    main_results = engine.run_discovery_cycle()
    
    # Run extended search
    extended_results = engine.run_extended_search()
    
    # Save results
    all_results = {
        "main_cycle": main_results,
        "extended_search": extended_results,
        "search_log": engine.search_log,
        "negative_search_log": engine.negative_search_log,
        "failed_queue": engine.failed_queue,
        "total_searches": len(engine.search_log),
        "total_discovered": main_results["discovered"] + len(extended_results["new_candidates"]),
    }
    
    with open(DTC / "discovery_results.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 70}")
    print(f"DISCOVERY CYCLE COMPLETE")
    print(f"  Searches: {all_results['total_searches']}")
    print(f"  Discovered: {all_results['total_discovered']}")
    print(f"  Already acquired: {main_results['already_acquired']}")
    print(f"  Failed: {len(engine.failed_queue)}")
    print(f"{'=' * 70}")
