#!/usr/bin/env python3
"""
Import Roman rulers from Wikidata into rulers and nation_snapshots tables.
Downloads portrait images and stores them locally.

Usage:
    python import_nation_snapshots.py
"""

import bisect
import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB', 'terra'),
    'user': os.getenv('POSTGRES_USER', 'terra'),
    'password': os.getenv('POSTGRES_PASSWORD', 'terra_dev')
}

WIKIDATA_ENDPOINT = 'https://query.wikidata.org/sparql'

# Asset directories
ASSETS_DIR = Path(__file__).parent.parent.parent / 'data' / 'assets'
PORTRAITS_DIR = ASSETS_DIR / 'portraits'
FLAGS_DIR = ASSETS_DIR / 'flags'

# Log directory
LOGS_DIR = Path(__file__).parent.parent.parent / 'logs'
LOG_FILE = None
LOG_BUFFER = []


def init_logging():
    """Initialize log file."""
    global LOG_FILE
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    LOG_FILE = LOGS_DIR / f'import_nation_snapshots_{timestamp}.log'


def log(message):
    """Buffer log message for batch writing."""
    LOG_BUFFER.append(message)


def flush_logs():
    """Write all buffered log messages to file."""
    if LOG_FILE and LOG_BUFFER:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write('\n'.join(LOG_BUFFER) + '\n')
        LOG_BUFFER.clear()


def year_to_display(year):
    """Convert signed year to display string (e.g., -500 -> '500 BC')."""
    if year < 0:
        return f'{abs(year)} BC'
    elif year > 0:
        return f'{year} AD'
    else:
        return '1 BC'


# SPARQL query for Roman emperors with portraits
ROMAN_EMPERORS_QUERY = """
SELECT DISTINCT ?ruler ?rulerLabel ?startYear ?endYear ?article ?image WHERE {
  ?ruler wdt:P39 wd:Q842606.  # position held: Roman emperor

  ?ruler p:P39 ?statement.
  ?statement ps:P39 wd:Q842606.
  OPTIONAL { ?statement pq:P580 ?start. }
  OPTIONAL { ?statement pq:P582 ?end. }

  OPTIONAL {
    ?article schema:about ?ruler;
             schema:isPartOf <https://en.wikipedia.org/>.
  }

  OPTIONAL { ?ruler wdt:P18 ?image. }

  BIND(YEAR(?start) AS ?startYear)
  BIND(YEAR(?end) AS ?endYear)

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?startYear
"""

# SPARQL query for Roman consuls (Republic era, before 27 BC)
ROMAN_CONSULS_QUERY = """
SELECT DISTINCT ?ruler ?rulerLabel ?startYear ?endYear ?article ?image WHERE {
  ?ruler wdt:P39 wd:Q40779.  # position held: Roman consul

  ?ruler p:P39 ?statement.
  ?statement ps:P39 wd:Q40779.
  ?statement pq:P580 ?start.  # Required: must have start date
  OPTIONAL { ?statement pq:P582 ?end. }

  OPTIONAL {
    ?article schema:about ?ruler;
             schema:isPartOf <https://en.wikipedia.org/>.
  }

  OPTIONAL { ?ruler wdt:P18 ?image. }

  BIND(YEAR(?start) AS ?startYear)
  BIND(YEAR(?end) AS ?endYear)

  FILTER(?startYear <= -27)

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?startYear
"""

# Fallback data (already in signed year format)
ROMAN_REPUBLIC_DATA = [
    {'name': 'Lucius Junius Brutus', 'title': 'Consul', 'wiki_url': 'https://en.wikipedia.org/wiki/Lucius_Junius_Brutus',
     'reign_start': -509, 'reign_end': -509, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Marcus Furius Camillus', 'title': 'Dictator', 'wiki_url': 'https://en.wikipedia.org/wiki/Marcus_Furius_Camillus',
     'reign_start': -396, 'reign_end': -365, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Scipio Africanus', 'title': 'Consul', 'wiki_url': 'https://en.wikipedia.org/wiki/Scipio_Africanus',
     'reign_start': -205, 'reign_end': -201, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Gaius Marius', 'title': 'Consul', 'wiki_url': 'https://en.wikipedia.org/wiki/Gaius_Marius',
     'reign_start': -107, 'reign_end': -86, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Lucius Cornelius Sulla', 'title': 'Dictator', 'wiki_url': 'https://en.wikipedia.org/wiki/Sulla',
     'reign_start': -82, 'reign_end': -79, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Gnaeus Pompeius Magnus', 'title': 'Consul', 'wiki_url': 'https://en.wikipedia.org/wiki/Pompey',
     'reign_start': -70, 'reign_end': -48, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Gaius Julius Caesar', 'title': 'Dictator', 'wiki_url': 'https://en.wikipedia.org/wiki/Julius_Caesar',
     'reign_start': -49, 'reign_end': -44, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
]

ROMAN_EMPERORS_FALLBACK = [
    {'name': 'Augustus', 'title': 'Emperor', 'wiki_url': 'https://en.wikipedia.org/wiki/Augustus',
     'reign_start': -27, 'reign_end': 14, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Tiberius', 'title': 'Emperor', 'wiki_url': 'https://en.wikipedia.org/wiki/Tiberius',
     'reign_start': 14, 'reign_end': 37, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Caligula', 'title': 'Emperor', 'wiki_url': 'https://en.wikipedia.org/wiki/Caligula',
     'reign_start': 37, 'reign_end': 41, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Claudius', 'title': 'Emperor', 'wiki_url': 'https://en.wikipedia.org/wiki/Claudius',
     'reign_start': 41, 'reign_end': 54, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Nero', 'title': 'Emperor', 'wiki_url': 'https://en.wikipedia.org/wiki/Nero',
     'reign_start': 54, 'reign_end': 68, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Vespasian', 'title': 'Emperor', 'wiki_url': 'https://en.wikipedia.org/wiki/Vespasian',
     'reign_start': 69, 'reign_end': 79, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Titus', 'title': 'Emperor', 'wiki_url': 'https://en.wikipedia.org/wiki/Titus',
     'reign_start': 79, 'reign_end': 81, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Domitian', 'title': 'Emperor', 'wiki_url': 'https://en.wikipedia.org/wiki/Domitian',
     'reign_start': 81, 'reign_end': 96, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Nerva', 'title': 'Emperor', 'wiki_url': 'https://en.wikipedia.org/wiki/Nerva',
     'reign_start': 96, 'reign_end': 98, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
    {'name': 'Trajan', 'title': 'Emperor', 'wiki_url': 'https://en.wikipedia.org/wiki/Trajan',
     'reign_start': 98, 'reign_end': 117, 'capital': 'Rome', 'language': 'Latin', 'religion': 'Roman Polytheism'},
]


def ensure_dirs():
    """Create asset directories if they don't exist."""
    PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)


def get_image_url_from_api(file_url, width=200):
    """Get downloadable image URL using MediaWiki API."""
    if 'Special:FilePath/' in file_url:
        filename = urllib.parse.unquote(file_url.split('Special:FilePath/')[-1])
    else:
        filename = urllib.parse.unquote(file_url.split('/')[-1])

    api_url = 'https://commons.wikimedia.org/w/api.php'
    params = {
        'action': 'query',
        'titles': f'File:{filename}',
        'prop': 'imageinfo',
        'iiprop': 'url',
        'iiurlwidth': width,
        'format': 'json'
    }

    url = api_url + '?' + urllib.parse.urlencode(params)
    headers = {'User-Agent': 'TerraHistoricalMap/1.0 (https://github.com/nerotran/terra)'}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            imageinfo = page.get('imageinfo', [{}])[0]
            return imageinfo.get('thumburl') or imageinfo.get('url')
    except Exception as e:
        print(f"    API error for {filename}: {e}")

    return None


def download_image(url, dest_dir, filename):
    """Download an image from URL to destination directory."""
    if not url:
        return None

    safe_filename = re.sub(r'[^\w\-.]', '_', filename)

    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        existing = dest_dir / f"{safe_filename}{ext}"
        if existing.exists():
            return f"/assets/{dest_dir.name}/{existing.name}"

    download_url = get_image_url_from_api(url, width=200)
    if not download_url:
        return None

    headers = {'User-Agent': 'TerraHistoricalMap/1.0 (https://github.com/nerotran/terra)'}

    try:
        req = urllib.request.Request(download_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            if 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                ext = '.jpg'

            dest_path = dest_dir / f"{safe_filename}{ext}"
            with open(dest_path, 'wb') as f:
                f.write(response.read())

        return f"/assets/{dest_dir.name}/{dest_path.name}"
    except Exception as e:
        print(f"    Download failed for {filename}: {e}")
        return None


def query_wikidata(query):
    """Execute SPARQL query against Wikidata."""
    url = WIKIDATA_ENDPOINT + '?' + urllib.parse.urlencode({
        'query': query,
        'format': 'json'
    })

    headers = {
        'User-Agent': 'TerraHistoricalMap/1.0 (https://github.com/nerotran/terra)',
        'Accept': 'application/json'
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Wikidata query failed: {e}")
        return None


def parse_wikidata_results(results, title='Emperor'):
    """Parse Wikidata SPARQL results into ruler records with signed years."""
    rulers = []

    for binding in results.get('results', {}).get('bindings', []):
        start_year = binding.get('startYear', {}).get('value')
        end_year = binding.get('endYear', {}).get('value')

        if not start_year:
            continue

        # Wikidata returns signed years (negative for BC)
        reign_start = int(float(start_year))
        reign_end = int(float(end_year)) if end_year else None

        wiki_url = binding.get('article', {}).get('value')
        image_url = binding.get('image', {}).get('value')

        rulers.append({
            'name': binding.get('rulerLabel', {}).get('value', 'Unknown'),
            'title': title,
            'wiki_url': wiki_url,
            'image_url': image_url,
            'reign_start': reign_start,
            'reign_end': reign_end,
            'capital': 'Rome',
            'language': 'Latin',
            'religion': 'Roman Polytheism'
        })

    return rulers


def parse_consul_results(results):
    """Parse Wikidata SPARQL results into consul records with signed years."""
    rulers = []
    seen = set()

    for binding in results.get('results', {}).get('bindings', []):
        start_year = binding.get('startYear', {}).get('value')
        end_year = binding.get('endYear', {}).get('value')

        if not start_year:
            continue

        reign_start = int(float(start_year))
        reign_end = int(float(end_year)) if end_year else reign_start  # Consuls typically 1 year

        wiki_url = binding.get('article', {}).get('value')
        image_url = binding.get('image', {}).get('value')
        name = binding.get('rulerLabel', {}).get('value', 'Unknown')

        key = (name, reign_start)
        if key in seen:
            continue
        seen.add(key)

        rulers.append({
            'name': name,
            'title': 'Consul',
            'wiki_url': wiki_url,
            'image_url': image_url,
            'reign_start': reign_start,
            'reign_end': reign_end,
            'capital': 'Rome',
            'language': 'Latin',
            'religion': 'Roman Polytheism'
        })

    return rulers


def build_ruler_index(rulers):
    """Build sorted index of rulers by reign period for fast lookup."""
    indexed = []
    for ruler in rulers:
        start = ruler['reign_start']
        end = ruler['reign_end'] if ruler['reign_end'] else ruler['reign_start']
        indexed.append((start, end, ruler))
    indexed.sort(key=lambda x: x[0])
    return indexed


def find_ruler_for_year(ruler_index, year):
    """Find ruler in power during given year using indexed lookup."""
    pos = bisect.bisect_right(ruler_index, (year, float('inf'), None))

    for i in range(pos - 1, -1, -1):
        start, end, ruler = ruler_index[i]
        if start <= year <= end:
            return ruler
        if end < year - 100:
            break
    return None


def import_rulers_and_snapshots(rulers, nation_name):
    """Import rulers into rulers table and create nation_snapshots."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get nation ID
    cur.execute("SELECT id FROM nations WHERE name = %s", (nation_name,))
    result = cur.fetchone()
    if not result:
        print(f"Nation not found: {nation_name}")
        conn.close()
        return 0

    nation_id = result[0]

    # Build indexed lookup
    ruler_index = build_ruler_index(rulers)

    log(f"\n{'='*60}")
    log(f"NATION: {nation_name}")
    log(f"{'='*60}")
    log(f"\nRulers ({len(rulers)} total):")
    for i, (start, end, r) in enumerate(ruler_index):
        log(f"  {i+1}. {r['name']}: {year_to_display(start)} - {year_to_display(end)}")

    # Insert rulers into rulers table and get their IDs
    ruler_ids = {}  # Map ruler name+start to ID
    portrait_cache = {}

    for ruler in rulers:
        # Download portrait if available
        portrait_url = None
        if ruler['name'] in portrait_cache:
            portrait_url = portrait_cache[ruler['name']]
        elif ruler.get('image_url'):
            portrait_url = download_image(ruler['image_url'], PORTRAITS_DIR, ruler['name'])
            portrait_cache[ruler['name']] = portrait_url

        cur.execute("""
            INSERT INTO rulers (nation_id, name, title, wiki_url, portrait_url, reign_start, reign_end)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (nation_id, ruler['name'], ruler['title'], ruler.get('wiki_url'),
              portrait_url, ruler['reign_start'], ruler['reign_end']))

        result = cur.fetchone()
        if result:
            ruler_ids[(ruler['name'], ruler['reign_start'])] = result[0]
        else:
            # Already exists, get ID
            cur.execute("""
                SELECT id FROM rulers
                WHERE nation_id = %s AND name = %s AND reign_start = %s
            """, (nation_id, ruler['name'], ruler['reign_start']))
            result = cur.fetchone()
            if result:
                ruler_ids[(ruler['name'], ruler['reign_start'])] = result[0]

    conn.commit()

    # Get all snapshots for this nation
    cur.execute("""
        SELECT DISTINCT ts.id, ts.year
        FROM time_snapshots ts
        JOIN territories t ON t.snapshot_id = ts.id
        JOIN nations n ON t.nation_id = n.id
        WHERE n.name = %s
        ORDER BY ts.year
    """, (nation_name,))
    snapshots = cur.fetchall()

    if not snapshots:
        print(f"No snapshots found for nation: {nation_name}")
        conn.close()
        return 0

    log(f"\nSnapshots ({len(snapshots)} total):")
    for s in snapshots:
        log(f"  {year_to_display(s[1])}")

    # Create nation_snapshots linking to rulers
    records = []

    for snapshot_id, year in snapshots:
        log(f"\n--- Matching for {year_to_display(year)} ---")

        best_ruler = find_ruler_for_year(ruler_index, year)

        if not best_ruler:
            log(f"  NO MATCH FOUND")
            continue

        log(f"  SELECTED: {best_ruler['name']}")

        # Get ruler ID
        ruler_id = ruler_ids.get((best_ruler['name'], best_ruler['reign_start']))

        records.append((
            nation_id, snapshot_id, ruler_id,
            best_ruler['capital'], best_ruler['language'], best_ruler['religion']
        ))

    # Batch insert nation_snapshots
    if records:
        execute_values(cur, """
            INSERT INTO nation_snapshots (nation_id, snapshot_id, ruler_id, capital, language, religion)
            VALUES %s
            ON CONFLICT (nation_id, snapshot_id) DO UPDATE SET
                ruler_id = EXCLUDED.ruler_id,
                capital = EXCLUDED.capital,
                language = EXCLUDED.language,
                religion = EXCLUDED.religion
        """, records)

    conn.commit()
    conn.close()
    flush_logs()

    return len(records)


def main():
    print("Importing nation snapshots from Wikidata...\n")

    init_logging()
    print(f"Logging to: {LOG_FILE}")

    ensure_dirs()

    # Query Wikidata for Roman consuls (Republic era)
    print("Querying Wikidata for Roman consuls...")
    consul_results = query_wikidata(ROMAN_CONSULS_QUERY)

    if consul_results:
        consuls = parse_consul_results(consul_results)
        print(f"Found {len(consuls)} consuls from Wikidata")
    else:
        print("Using fallback Republic data...")
        consuls = ROMAN_REPUBLIC_DATA

    # Query Wikidata for Roman emperors
    print("Querying Wikidata for Roman emperors...")
    emperor_results = query_wikidata(ROMAN_EMPERORS_QUERY)

    if emperor_results:
        emperors = parse_wikidata_results(emperor_results, 'Emperor')
        print(f"Found {len(emperors)} emperors from Wikidata")
    else:
        print("Using fallback emperor data...")
        emperors = ROMAN_EMPERORS_FALLBACK

    # Combine consuls and emperors
    all_rulers = consuls + emperors
    all_rulers.sort(key=lambda r: r['reign_start'])

    print(f"\nTotal rulers: {len(all_rulers)}")

    # Import for Roman Republic
    print("\n--- Roman Republic ---")
    republic_rulers = [r for r in all_rulers if r['reign_start'] < -27]
    imported = import_rulers_and_snapshots(republic_rulers, 'rome_republic')
    print(f"Imported {imported} snapshots for Roman Republic")

    # Import for Roman Empire
    print("\n--- Roman Empire ---")
    empire_rulers = [r for r in all_rulers if r['reign_start'] >= -27]
    imported = import_rulers_and_snapshots(empire_rulers, 'rome')
    print(f"Imported {imported} snapshots for Roman Empire")

    print("\nDone!")


if __name__ == '__main__':
    main()
