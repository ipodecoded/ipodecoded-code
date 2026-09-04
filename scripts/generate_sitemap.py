import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from datetime import datetime, timezone
from backend.db import SessionLocal, IPO

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "frontend" / "public"

def generate_sitemap():
    db = SessionLocal()
    ipos = db.query(IPO).all()
    
    site_url = "https://ipodecoded.journaldecoded.in"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f'  <url><loc>{site_url}/</loc><lastmod>{now_iso}</lastmod><changefreq>hourly</changefreq><priority>1.0</priority></url>',
        f'  <url><loc>{site_url}/ipos</loc><lastmod>{now_iso}</lastmod><changefreq>hourly</changefreq><priority>0.9</priority></url>',
    ]

    for ipo in ipos:
        lastmod = ipo.updated_at.strftime("%Y-%m-%d") if ipo.updated_at else now_iso
        xml_lines.append(
            f'  <url><loc>{site_url}/ipo/{ipo.slug}</loc><lastmod>{lastmod}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>'
        )

    xml_lines.append('</urlset>')

    output_file = PUBLIC_DIR / "sitemap.xml"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))

    print(f"Generated sitemap with {len(ipos) + 2} URLs at {output_file}")
    db.close()

if __name__ == "__main__":
    generate_sitemap()
