#!/usr/bin/env python3
"""
Phase 4: HTML Dashboard Generator
Creates an interactive dashboard for monitoring corpus coverage.
"""
import json
import os
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
DTC_DIR = BASE / 'knowledge' / 'dtc'
COVERAGE_DIR = DTC_DIR / 'coverage'
DASHBOARD_DIR = BASE / 'dashboard'
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}


def generate_dashboard():
    """Generate the Phase 4 HTML dashboard."""
    report = load_json(COVERAGE_DIR / 'phase4_coverage_report.json')
    gaps = load_json(COVERAGE_DIR / 'phase4_gap_report.json')
    
    if not report:
        print("No coverage report found. Run phase4_coverage_report.py first.")
        return
    
    scripts_data = report.get('scriptures', {})
    summary = report.get('summary', {})
    
    # Group by category
    categories = {}
    for sid, data in scripts_data.items():
        cat = data.get('category', 'Other')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((sid, data))
    
    # Build HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AstroSage DTC Phase 4 — Canonical Knowledge Dashboard</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #0a0a0f; color: #e0e0e0; padding: 20px; }}
.header {{ text-align: center; padding: 30px 0; border-bottom: 1px solid #333; margin-bottom: 30px; }}
.header h1 {{ font-size: 2em; color: #ff6b35; margin-bottom: 10px; }}
.header .subtitle {{ color: #888; font-size: 1.1em; }}
.header .timestamp {{ color: #666; font-size: 0.9em; margin-top: 8px; }}

.summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 30px; }}
.summary-card {{ background: #1a1a2e; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #333; }}
.summary-card .number {{ font-size: 2.5em; font-weight: bold; }}
.summary-card .label {{ color: #888; font-size: 0.9em; margin-top: 5px; }}
.verified .number {{ color: #4ade80; }}
.incomplete .number {{ color: #fbbf24; }}
.parsed .number {{ color: #60a5fa; }}
.no-witnesses .number {{ color: #f87171; }}
.total .number {{ color: #ff6b35; }}
.confidence .number {{ color: #a78bfa; }}

.section {{ margin-bottom: 30px; }}
.section h2 {{ color: #ff6b35; margin-bottom: 15px; font-size: 1.4em; border-bottom: 1px solid #333; padding-bottom: 8px; }}

.category {{ margin-bottom: 25px; }}
.category h3 {{ color: #60a5fa; margin-bottom: 10px; font-size: 1.1em; }}

.scripture-table {{ width: 100%; border-collapse: collapse; background: #1a1a2e; border-radius: 8px; overflow: hidden; }}
.scripture-table th {{ background: #16213e; padding: 10px 12px; text-align: left; font-size: 0.85em; color: #888; text-transform: uppercase; }}
.scripture-table td {{ padding: 8px 12px; border-bottom: 1px solid #222; font-size: 0.9em; }}
.scripture-table tr:hover {{ background: #1f2b47; }}

.status {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }}
.status-verified {{ background: #064e3b; color: #4ade80; }}
.status-incomplete {{ background: #713f12; color: #fbbf24; }}
.status-acquired {{ background: #1e3a5f; color: #60a5fa; }}
.status-none {{ background: #4c1d1d; color: #f87171; }}

.confidence-bar {{ width: 100%; height: 6px; background: #333; border-radius: 3px; overflow: hidden; }}
.confidence-fill {{ height: 100%; border-radius: 3px; transition: width 0.3s; }}

.gap-list {{ background: #1a1a2e; border-radius: 8px; padding: 15px; }}
.gap-item {{ padding: 8px 0; border-bottom: 1px solid #222; display: flex; align-items: center; gap: 10px; }}
.gap-item:last-child {{ border-bottom: none; }}
.gap-priority {{ font-size: 0.75em; padding: 2px 8px; border-radius: 8px; font-weight: bold; }}
.gap-critical {{ background: #4c1d1d; color: #f87171; }}
.gap-high {{ background: #713f12; color: #fbbf24; }}
.gap-medium {{ background: #1e3a5f; color: #60a5fa; }}

.footer {{ text-align: center; padding: 20px; color: #555; font-size: 0.85em; border-top: 1px solid #333; margin-top: 30px; }}
</style>
</head>
<body>
<div class="header">
<h1>🕉️ AstroSage Digital Critical Edition</h1>
<div class="subtitle">Phase 4 — Canonical Knowledge Dashboard</div>
<div class="timestamp">Generated: {report.get("generated", "N/A")}</div>
</div>

<div class="summary-grid">
<div class="summary-card total"><div class="number">{summary.get("total", 0)}</div><div class="label">Total Scriptures</div></div>
<div class="summary-card verified"><div class="number">{summary.get("verified", 0)}</div><div class="label">Verified</div></div>
<div class="summary-card incomplete"><div class="number">{summary.get("evidence_incomplete", 0)}</div><div class="label">Evidence Incomplete</div></div>
<div class="summary-card parsed"><div class="number">{summary.get("acquired_not_parsed", 0)}</div><div class="label">Acquired Not Parsed</div></div>
<div class="summary-card no-witnesses"><div class="number">{summary.get("no_witnesses", 0)}</div><div class="label">No Witnesses</div></div>
<div class="summary-card confidence"><div class="number">{summary.get("average_confidence", 0)}%</div><div class="label">Avg Confidence</div></div>
</div>

<div class="section">
<h2>📊 Scripture Coverage by Category</h2>
'''
    
    category_order = ['Veda', 'Itihasa', 'Purana', 'Upanishad', 'Smriti', 'Sutra', 'Darshana']
    for cat in category_order:
        if cat not in categories:
            continue
        items = categories[cat]
        html += f'<div class="category"><h3>{cat} ({len(items)} scriptures)</h3>\n'
        html += '<table class="scripture-table"><thead><tr>'
        html += '<th>ID</th><th>Name</th><th>Status</th><th>Confidence</th>'
        html += '<th>Verses</th><th>CUIDs</th><th>Families</th><th>Collation</th>'
        html += '</tr></thead><tbody>\n'
        
        for sid, data in sorted(items, key=lambda x: x[1].get('priority', 99)):
            status = data.get('status', 'UNKNOWN')
            status_class = {
                'VERIFIED': 'status-verified',
                'EVIDENCE_INCOMPLETE': 'status-incomplete',
                'ACQUIRED_NOT_PARSED': 'status-acquired',
                'NO_WITNESSES': 'status-none',
            }.get(status, 'status-none')
            
            conf = data.get('confidence', 0)
            conf_color = '#4ade80' if conf >= 70 else '#fbbf24' if conf >= 40 else '#f87171'
            
            exp = data.get('expected_verses', 0)
            cuds = data.get('extracted_cuids', 0)
            fams = data.get('independent_families', 0)
            coll = data.get('collation_status', 'N/A')
            
            html += f'''<tr>
<td><strong>{sid}</strong></td>
<td>{data.get("name", "")[:40]}</td>
<td><span class="status {status_class}">{status}</span></td>
<td><div class="confidence-bar"><div class="confidence-fill" style="width:{conf}%;background:{conf_color}"></div></div>{conf}%</td>
<td>{cuds:,} / {exp:,}</td>
<td>{cuds:,}</td>
<td>{fams}</td>
<td>{coll}</td>
</tr>\n'''
        
        html += '</tbody></table></div>\n'
    
    # Gap analysis section
    html += '''
</div>

<div class="section">
<h2>🔍 Gap Analysis — Acquisition Priorities</h2>
<div class="gap-list">
'''
    
    for gap in gaps.get('gaps', []):
        priority_class = f"gap-{gap.get('priority', 'medium').lower()}"
        html += f'''<div class="gap-item">
<span class="gap-priority {priority_class}">{gap.get("priority", "")}</span>
<strong>{gap.get("scripture", "")}</strong>
<span>{gap.get("name", "")[:40]}</span>
<span style="color:#888">— {gap.get("reason", "")}</span>
</div>\n'''
    
    html += '''
</div>
</div>

<div class="footer">
<p>AstroSage Digital Critical Edition — Phase 4: Canonical Knowledge Reconstruction</p>
<p>Evidence before AI. Corpus before retrieval. Critical editions before embeddings.</p>
<p>Generated by Phase 4 DTC Pipeline</p>
</div>
</body>
</html>'''
    
    # Save dashboard
    dashboard_path = DASHBOARD_DIR / 'phase4_dashboard.html'
    with open(dashboard_path, 'w') as f:
        f.write(html)
    
    print(f"Dashboard saved to: {dashboard_path}")
    print(f"Open in browser: file://{dashboard_path.absolute()}")
    
    return dashboard_path


if __name__ == '__main__':
    generate_dashboard()
