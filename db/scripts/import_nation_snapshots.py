#!/usr/bin/env python3
"""
Import Roman rulers from Wikidata into nation_snapshots table.
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
LOG_BUFFER = []  # Buffer for log messages


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

# SPARQL query for Roman emperors with portraits
ROMAN_EMPERORS_QUERY = """
SELECT DISTINCT ?ruler ?rulerLabel ?startYear ?endYear ?article ?image WHERE {
  # Roman Emperors
  ?ruler wdt:P39 wd:Q842606.  # position held: Roman emperor

  # Get reign start/end
  ?ruler p:P39 ?statement.
  ?statement ps:P39 wd:Q842606.
  OPTIONAL { ?statement pq:P580 ?start. }
  OPTIONAL { ?statement pq:P582 ?end. }

  # Get Wikipedia article
  OPTIONAL {
    ?article schema:about ?ruler;
             schema:isPartOf <https://en.wikipedia.org/>.
  }

  # Get portrait image
  OPTIONAL { ?ruler wdt:P18 ?image. }

  # Extract years
  BIND(YEAR(?start) AS ?startYear)
  BIND(YEAR(?end) AS ?endYear)

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?startYear
"""

# SPARQL query for Roman consuls (Republic era, before 27 BC)
ROMAN_CONSULS_QUERY = """
SELECT DISTINCT ?ruler ?rulerLabel ?startYear ?endYear ?article ?image WHERE {
  # Roman Consuls
  ?ruler wdt:P39 wd:Q40779.  # position held: Roman consul

  # Get term start/end (required - only consuls with known dates)
  ?ruler p:P39 ?statement.
  ?statement ps:P39 wd:Q40779.
  ?statement pq:P580 ?start.  # Required: must have start date
  OPTIONAL { ?statement pq:P582 ?end. }

  # Get Wikipedia article
  OPTIONAL {
    ?article schema:about ?ruler;
             schema:isPartOf <https://en.wikipedia.org/>.
  }

  # Get portrait image
  OPTIONAL { ?ruler wdt:P18 ?image. }

  # Extract years
  BIND(YEAR(?start) AS ?startYear)
  BIND(YEAR(?end) AS ?endYear)

  # Filter to Republic era (before 27 BC = year <= -27)
  FILTER(?startYear <= -27)

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?startYear
"""

# Consuls of the Roman Republic (simplified - key figures)
ROMAN_REPUBLIC_DATA = [
    # Early Republic - just placeholder data for key periods
    {
        'ruler_name': 'Lucius Junius Brutus',
        'ruler_title': 'Consul',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Lucius_Junius_Brutus',
        'reign_start_year': 509, 'reign_start_era': 'BC',
        'reign_end_year': 509, 'reign_end_era': 'BC',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Marcus Furius Camillus',
        'ruler_title': 'Dictator',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Marcus_Furius_Camillus',
        'reign_start_year': 396, 'reign_start_era': 'BC',
        'reign_end_year': 365, 'reign_end_era': 'BC',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Scipio Africanus',
        'ruler_title': 'Consul',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Scipio_Africanus',
        'reign_start_year': 205, 'reign_start_era': 'BC',
        'reign_end_year': 201, 'reign_end_era': 'BC',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Gaius Marius',
        'ruler_title': 'Consul',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Gaius_Marius',
        'reign_start_year': 107, 'reign_start_era': 'BC',
        'reign_end_year': 86, 'reign_end_era': 'BC',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Lucius Cornelius Sulla',
        'ruler_title': 'Dictator',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Sulla',
        'reign_start_year': 82, 'reign_start_era': 'BC',
        'reign_end_year': 79, 'reign_end_era': 'BC',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Gnaeus Pompeius Magnus',
        'ruler_title': 'Consul',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Pompey',
        'reign_start_year': 70, 'reign_start_era': 'BC',
        'reign_end_year': 48, 'reign_end_era': 'BC',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Gaius Julius Caesar',
        'ruler_title': 'Dictator',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Julius_Caesar',
        'reign_start_year': 49, 'reign_start_era': 'BC',
        'reign_end_year': 44, 'reign_end_era': 'BC',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
]

# Fallback emperor data if Wikidata fails
ROMAN_EMPERORS_FALLBACK = [
    {
        'ruler_name': 'Augustus',
        'ruler_title': 'Emperor',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Augustus',
        'reign_start_year': 27, 'reign_start_era': 'BC',
        'reign_end_year': 14, 'reign_end_era': 'AD',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Tiberius',
        'ruler_title': 'Emperor',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Tiberius',
        'reign_start_year': 14, 'reign_start_era': 'AD',
        'reign_end_year': 37, 'reign_end_era': 'AD',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Caligula',
        'ruler_title': 'Emperor',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Caligula',
        'reign_start_year': 37, 'reign_start_era': 'AD',
        'reign_end_year': 41, 'reign_end_era': 'AD',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Claudius',
        'ruler_title': 'Emperor',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Claudius',
        'reign_start_year': 41, 'reign_start_era': 'AD',
        'reign_end_year': 54, 'reign_end_era': 'AD',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Nero',
        'ruler_title': 'Emperor',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Nero',
        'reign_start_year': 54, 'reign_start_era': 'AD',
        'reign_end_year': 68, 'reign_end_era': 'AD',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Vespasian',
        'ruler_title': 'Emperor',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Vespasian',
        'reign_start_year': 69, 'reign_start_era': 'AD',
        'reign_end_year': 79, 'reign_end_era': 'AD',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Titus',
        'ruler_title': 'Emperor',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Titus',
        'reign_start_year': 79, 'reign_start_era': 'AD',
        'reign_end_year': 81, 'reign_end_era': 'AD',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Domitian',
        'ruler_title': 'Emperor',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Domitian',
        'reign_start_year': 81, 'reign_start_era': 'AD',
        'reign_end_year': 96, 'reign_end_era': 'AD',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Nerva',
        'ruler_title': 'Emperor',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Nerva',
        'reign_start_year': 96, 'reign_start_era': 'AD',
        'reign_end_year': 98, 'reign_end_era': 'AD',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
    {
        'ruler_name': 'Trajan',
        'ruler_title': 'Emperor',
        'ruler_wiki_url': 'https://en.wikipedia.org/wiki/Trajan',
        'reign_start_year': 98, 'reign_start_era': 'AD',
        'reign_end_year': 117, 'reign_end_era': 'AD',
        'capital': 'Rome',
        'language': 'Latin',
        'religion': 'Roman Polytheism'
    },
]


def ensure_dirs():
    """Create asset directories if they don't exist."""
    PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)


def get_image_url_from_api(file_url, width=200):
    """Get downloadable image URL using MediaWiki API."""
    # Extract filename from URL
    if 'Special:FilePath/' in file_url:
        filename = urllib.parse.unquote(file_url.split('Special:FilePath/')[-1])
    else:
        filename = urllib.parse.unquote(file_url.split('/')[-1])

    # Query Commons API for image info
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
    headers = {
        'User-Agent': 'TerraHistoricalMap/1.0 (https://github.com/nerotran/terra)'
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            imageinfo = page.get('imageinfo', [{}])[0]
            # Prefer thumbnail URL, fall back to full URL
            return imageinfo.get('thumburl') or imageinfo.get('url')
    except Exception as e:
        print(f"    API error for {filename}: {e}")

    return None


def get_image_from_wikipedia_url(wiki_url):
    """Fetch image URL from Wikidata given a Wikipedia article URL."""
    if not wiki_url or 'wikipedia.org' not in wiki_url:
        return None

    # Query Wikidata using the Wikipedia URL directly
    query = f"""
    SELECT ?image WHERE {{
      <{wiki_url}> schema:about ?item.
      ?item wdt:P18 ?image.
    }}
    LIMIT 1
    """

    result = query_wikidata(query)
    if result:
        bindings = result.get('results', {}).get('bindings', [])
        if bindings:
            return bindings[0].get('image', {}).get('value')

    return None


def enrich_rulers_with_images(rulers):
    """Fetch images for rulers that have wiki URLs but no image."""
    for ruler in rulers:
        if ruler.get('image_url'):
            continue
        if ruler.get('ruler_wiki_url'):
            image_url = get_image_from_wikipedia_url(ruler['ruler_wiki_url'])
            if image_url:
                ruler['image_url'] = image_url


def get_flag_from_wikipedia_url(wiki_url):
    """Fetch flag/emblem image URL using multiple sources."""
    if not wiki_url or 'wikipedia.org' not in wiki_url:
        return None

    # Extract article title from URL
    try:
        title = wiki_url.split('/wiki/')[-1]
        title_decoded = urllib.parse.unquote(title)
    except Exception:
        return None

    # Try 1: DBpedia for structured infobox data (has flag property)
    dbpedia_url = f"http://dbpedia.org/data/{title}.json"
    headers = {
        'User-Agent': 'TerraHistoricalMap/1.0 (https://github.com/nerotran/terra)',
        'Accept': 'application/json'
    }

    try:
        req = urllib.request.Request(dbpedia_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        resource_uri = f"http://dbpedia.org/resource/{title}"
        resource = data.get(resource_uri, {})

        # Look for flag properties
        flag_props = [
            'http://dbpedia.org/ontology/flag',
            'http://dbpedia.org/property/flag',
            'http://dbpedia.org/property/flagImage',
            'http://dbpedia.org/property/imageFlag',
        ]

        for prop in flag_props:
            if prop in resource:
                values = resource[prop]
                for v in values:
                    if v.get('type') == 'uri':
                        flag_url = v.get('value')
                        log(f"  DBpedia found: {flag_url}")
                        # Convert DBpedia file reference to Commons URL
                        if 'dbpedia.org/resource/File:' in flag_url:
                            filename = flag_url.split('File:')[-1]
                            return f"http://commons.wikimedia.org/wiki/Special:FilePath/{filename}"
                        return flag_url
                    elif v.get('type') == 'literal':
                        filename = v.get('value')
                        if filename:
                            log(f"  DBpedia found filename: {filename}")
                            return f"http://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(filename)}"
    except Exception as e:
        log(f"  DBpedia error: {e}")

    # Try 2: Wikipedia API - get all images and find flag-related ones
    try:
        api_url = 'https://en.wikipedia.org/w/api.php'
        params = {
            'action': 'query',
            'titles': title_decoded,
            'prop': 'images',
            'format': 'json',
            'imlimit': 50
        }
        url = api_url + '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            images = page.get('images', [])
            # Look for flag-related images specific to this nation
            # Extract nation name from title for matching
            nation_keywords = title_decoded.lower().replace('_', ' ').split()

            for img in images:
                img_title = img.get('title', '').lower()
                # Skip flags of other modern nations
                if 'flag of' in img_title and not any(kw in img_title for kw in nation_keywords):
                    continue
                # Look for vexillum, banner, standard, emblem (ancient flags/symbols)
                ancient_keywords = ['vexillum', 'banner', 'standard', 'labarum', 'aquila', 'spqr', 'emblem', 'seal', 'coat of arms', 'insignia']
                if any(kw in img_title for kw in ancient_keywords):
                    filename = img.get('title', '').replace('File:', '')
                    log(f"  Wikipedia found ancient flag: {filename}")
                    return f"http://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(filename)}"

            # Second pass: look for flag images that match nation name
            for img in images:
                img_title = img.get('title', '').lower()
                if 'flag' in img_title and any(kw in img_title for kw in nation_keywords):
                    filename = img.get('title', '').replace('File:', '')
                    log(f"  Wikipedia found nation flag: {filename}")
                    return f"http://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(filename)}"
    except Exception as e:
        log(f"  Wikipedia images API error: {e}")

    return None


def import_nation_flags():
    """Fetch and download flags for all nations with wiki URLs."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT id, name, wiki_url, flag_url FROM nations WHERE wiki_url IS NOT NULL")
    nations = cur.fetchall()

    updated = 0
    for nation_id, name, wiki_url, existing_flag in nations:
        log(f"Processing flag for {name}: {wiki_url}")
        if existing_flag:
            log(f"  Already has flag: {existing_flag}")
            continue

        flag_image_url = get_flag_from_wikipedia_url(wiki_url)
        log(f"  Wikidata flag URL: {flag_image_url}")
        if flag_image_url:
            local_path = download_image(flag_image_url, FLAGS_DIR, name)
            log(f"  Downloaded to: {local_path}")
            if local_path:
                cur.execute(
                    "UPDATE nations SET flag_url = %s WHERE id = %s",
                    (local_path, nation_id)
                )
                updated += 1
        else:
            log(f"  No flag found in Wikidata")

    conn.commit()
    conn.close()
    return updated


def download_image(url, dest_dir, filename):
    """Download an image from URL to destination directory."""
    if not url:
        return None

    # Clean filename
    safe_filename = re.sub(r'[^\w\-.]', '_', filename)

    # Check for existing files with any extension
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        existing = dest_dir / f"{safe_filename}{ext}"
        if existing.exists():
            return f"/assets/{dest_dir.name}/{existing.name}"

    # Get downloadable URL from MediaWiki API
    download_url = get_image_url_from_api(url, width=200)
    if not download_url:
        return None

    headers = {
        'User-Agent': 'TerraHistoricalMap/1.0 (https://github.com/nerotran/terra)'
    }

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


def parse_wikidata_results(results):
    """Parse Wikidata SPARQL results into ruler records."""
    rulers = []

    for binding in results.get('results', {}).get('bindings', []):
        start_year = binding.get('startYear', {}).get('value')
        end_year = binding.get('endYear', {}).get('value')

        if not start_year:
            continue

        start_year = int(float(start_year))
        end_year = int(float(end_year)) if end_year else None

        # Determine era (negative years are BC in Wikidata)
        if start_year <= 0:
            reign_start_year = abs(start_year) if start_year != 0 else 1
            reign_start_era = 'BC'
        else:
            reign_start_year = start_year
            reign_start_era = 'AD'

        if end_year is not None:
            if end_year <= 0:
                reign_end_year = abs(end_year) if end_year != 0 else 1
                reign_end_era = 'BC'
            else:
                reign_end_year = end_year
                reign_end_era = 'AD'
        else:
            reign_end_year = None
            reign_end_era = None

        wiki_url = binding.get('article', {}).get('value')
        image_url = binding.get('image', {}).get('value')

        rulers.append({
            'ruler_name': binding.get('rulerLabel', {}).get('value', 'Unknown'),
            'ruler_title': 'Emperor',
            'ruler_wiki_url': wiki_url,
            'image_url': image_url,  # Wikimedia Commons URL
            'reign_start_year': reign_start_year,
            'reign_start_era': reign_start_era,
            'reign_end_year': reign_end_year,
            'reign_end_era': reign_end_era,
            'capital': 'Rome',
            'language': 'Latin',
            'religion': 'Roman Polytheism'
        })

    return rulers


def parse_consul_results(results):
    """Parse Wikidata SPARQL results into consul records."""
    rulers = []
    seen = set()  # Track seen rulers to avoid duplicates

    for binding in results.get('results', {}).get('bindings', []):
        start_year = binding.get('startYear', {}).get('value')
        end_year = binding.get('endYear', {}).get('value')

        if not start_year:
            continue

        start_year = int(float(start_year))
        end_year = int(float(end_year)) if end_year else None

        # Determine era (negative years are BC in Wikidata)
        if start_year <= 0:
            reign_start_year = abs(start_year) if start_year != 0 else 1
            reign_start_era = 'BC'
        else:
            reign_start_year = start_year
            reign_start_era = 'AD'

        if end_year is not None:
            if end_year <= 0:
                reign_end_year = abs(end_year) if end_year != 0 else 1
                reign_end_era = 'BC'
            else:
                reign_end_year = end_year
                reign_end_era = 'AD'
        else:
            # For consuls, term was typically 1 year
            reign_end_year = reign_start_year
            reign_end_era = reign_start_era

        wiki_url = binding.get('article', {}).get('value')
        image_url = binding.get('image', {}).get('value')
        name = binding.get('rulerLabel', {}).get('value', 'Unknown')

        # Create unique key for deduplication (name + start year)
        key = (name, reign_start_year, reign_start_era)
        if key in seen:
            continue
        seen.add(key)

        rulers.append({
            'ruler_name': name,
            'ruler_title': 'Consul',
            'ruler_wiki_url': wiki_url,
            'image_url': image_url,
            'reign_start_year': reign_start_year,
            'reign_start_era': reign_start_era,
            'reign_end_year': reign_end_year,
            'reign_end_era': reign_end_era,
            'capital': 'Rome',
            'language': 'Latin',
            'religion': 'Roman Polytheism'
        })

    return rulers


def year_to_sort_year(year, era):
    """Convert year/era to sort_year (BC negative, AD positive)."""
    if era == 'BC':
        return -year
    return year


def find_matching_snapshot(cur, year, era):
    """Find the time snapshot that best matches a given year."""
    sort_year = year_to_sort_year(year, era)

    # Find closest snapshot
    cur.execute("""
        SELECT id, year, era, sort_year
        FROM time_snapshots
        WHERE sort_year <= %s
        ORDER BY sort_year DESC
        LIMIT 1
    """, (sort_year,))

    return cur.fetchone()


def build_ruler_index(rulers):
    """Build sorted index of rulers by reign period for fast lookup."""
    indexed = []
    for ruler in rulers:
        start = year_to_sort_year(ruler['reign_start_year'], ruler['reign_start_era'])
        end = year_to_sort_year(
            ruler['reign_end_year'] or ruler['reign_start_year'],
            ruler['reign_end_era'] or ruler['reign_start_era']
        )
        indexed.append((start, end, ruler))
    # Sort by start year for binary search
    indexed.sort(key=lambda x: x[0])
    return indexed


def find_ruler_for_year(ruler_index, sort_year):
    """Find ruler in power during given sort_year using indexed lookup."""
    # Find rulers whose reign started before or at this year
    pos = bisect.bisect_right(ruler_index, (sort_year, float('inf'), None))

    # Check rulers from this position backwards
    for i in range(pos - 1, -1, -1):
        start, end, ruler = ruler_index[i]
        if start <= sort_year <= end:
            return ruler
        # If we've gone too far back, stop
        if end < sort_year - 100:  # No ruler reigns 100+ years
            break
    return None


def import_rulers(rulers, nation_name):
    """Import rulers into nation_snapshots table."""
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

    # Build indexed lookup for O(log n) ruler search
    ruler_index = build_ruler_index(rulers)

    # Log all rulers
    log(f"\n{'='*60}")
    log(f"NATION: {nation_name}")
    log(f"{'='*60}")
    log(f"\nRulers ({len(rulers)} total):")
    for i, (start, end, r) in enumerate(ruler_index):
        log(f"  {i+1}. {r['ruler_name']}: {r['reign_start_year']} {r['reign_start_era']} - {r.get('reign_end_year')} {r.get('reign_end_era')} (sort: {start} to {end})")

    # Get all snapshots for this nation
    cur.execute("""
        SELECT DISTINCT ts.id, ts.year, ts.era, ts.sort_year
        FROM time_snapshots ts
        JOIN territories t ON t.snapshot_id = ts.id
        JOIN nations n ON t.nation_id = n.id
        WHERE n.name = %s
        ORDER BY ts.sort_year
    """, (nation_name,))
    snapshots = cur.fetchall()

    if not snapshots:
        print(f"No snapshots found for nation: {nation_name}")
        conn.close()
        return 0

    log(f"\nSnapshots ({len(snapshots)} total):")
    for s in snapshots:
        log(f"  {s[1]} {s[2]} (sort_year: {s[3]})")

    # Collect all records for batch insert
    records = []
    portrait_cache = {}  # Cache downloaded portraits by ruler name

    for snapshot in snapshots:
        snapshot_id, snap_year, snap_era, snap_sort_year = snapshot

        log(f"\n--- Matching for {snap_year} {snap_era} (sort_year: {snap_sort_year}) ---")

        # Find ruler using indexed lookup (O(log n) instead of O(n))
        best_ruler = find_ruler_for_year(ruler_index, snap_sort_year)

        if not best_ruler:
            log(f"  NO MATCH FOUND")
            continue

        log(f"  SELECTED: {best_ruler['ruler_name']}")

        # Download portrait if available (with caching)
        portrait_url = None
        ruler_name = best_ruler['ruler_name']
        if ruler_name in portrait_cache:
            portrait_url = portrait_cache[ruler_name]
        elif best_ruler.get('image_url'):
            portrait_url = download_image(
                best_ruler['image_url'],
                PORTRAITS_DIR,
                ruler_name
            )
            portrait_cache[ruler_name] = portrait_url

        records.append((
            nation_id, snapshot_id,
            best_ruler['ruler_title'], best_ruler['ruler_name'], best_ruler['ruler_wiki_url'],
            portrait_url,
            best_ruler['reign_start_year'], best_ruler['reign_start_era'],
            best_ruler['reign_end_year'], best_ruler['reign_end_era'],
            best_ruler['capital'], best_ruler['language'], best_ruler['religion']
        ))

    # Batch insert all records
    if records:
        execute_values(cur, """
            INSERT INTO nation_snapshots (
                nation_id, snapshot_id, ruler_title, ruler_name, ruler_wiki_url,
                ruler_portrait_url, reign_start_year, reign_start_era, reign_end_year, reign_end_era,
                capital, language, religion
            ) VALUES %s
            ON CONFLICT (nation_id, snapshot_id) DO UPDATE SET
                ruler_title = EXCLUDED.ruler_title,
                ruler_name = EXCLUDED.ruler_name,
                ruler_wiki_url = EXCLUDED.ruler_wiki_url,
                ruler_portrait_url = EXCLUDED.ruler_portrait_url,
                reign_start_year = EXCLUDED.reign_start_year,
                reign_start_era = EXCLUDED.reign_start_era,
                reign_end_year = EXCLUDED.reign_end_year,
                reign_end_era = EXCLUDED.reign_end_era,
                capital = EXCLUDED.capital,
                language = EXCLUDED.language,
                religion = EXCLUDED.religion
        """, records)

    conn.commit()
    conn.close()
    flush_logs()  # Write buffered logs

    return len(records)


def main():
    print("Importing nation snapshots from Wikidata...\n")

    # Initialize logging
    init_logging()
    print(f"Logging to: {LOG_FILE}")

    # Ensure asset directories exist
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
        emperors = parse_wikidata_results(emperor_results)
        print(f"Found {len(emperors)} emperors from Wikidata")
    else:
        print("Using fallback emperor data...")
        emperors = ROMAN_EMPERORS_FALLBACK

    # Combine consuls and emperors
    all_rulers = consuls + emperors

    # Sort by reign start
    all_rulers.sort(key=lambda r: year_to_sort_year(r['reign_start_year'], r['reign_start_era']))

    print(f"\nTotal rulers: {len(all_rulers)}")

    # Note: Skipping enrich_rulers_with_images() - SPARQL already fetches images (P18)
    # Enrichment makes individual HTTP requests per ruler which is too slow for large datasets

    # Import for Roman Republic
    print("\n--- Roman Republic ---")
    republic_rulers = [r for r in all_rulers if year_to_sort_year(r['reign_start_year'], r['reign_start_era']) < -27]
    imported = import_rulers(republic_rulers, 'rome_republic')
    print(f"Imported {imported} snapshots for Roman Republic")

    # Import for Roman Empire
    print("\n--- Roman Empire ---")
    empire_rulers = [r for r in all_rulers if year_to_sort_year(r['reign_start_year'], r['reign_start_era']) >= -27]
    imported = import_rulers(empire_rulers, 'rome')
    print(f"Imported {imported} snapshots for Roman Empire")

    # TODO: Flag import disabled - needs better API approach
    # print("\n--- Nation Flags ---")
    # flags_updated = import_nation_flags()
    # print(f"Updated {flags_updated} nation flags")

    print("\nDone!")


if __name__ == '__main__':
    main()
