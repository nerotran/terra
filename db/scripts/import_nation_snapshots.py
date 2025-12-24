#!/usr/bin/env python3
"""
Import Roman rulers from Wikidata into nation_snapshots table.

Usage:
    python import_nation_snapshots.py
"""

import json
import os
import re
import urllib.request
import urllib.parse
import psycopg2

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB', 'terra'),
    'user': os.getenv('POSTGRES_USER', 'terra'),
    'password': os.getenv('POSTGRES_PASSWORD', 'terra_dev')
}

WIKIDATA_ENDPOINT = 'https://query.wikidata.org/sparql'

# SPARQL query for Roman emperors and their reign dates
ROMAN_EMPERORS_QUERY = """
SELECT DISTINCT ?ruler ?rulerLabel ?startYear ?endYear ?article WHERE {
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

  # Extract years
  BIND(YEAR(?start) AS ?startYear)
  BIND(YEAR(?end) AS ?endYear)

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

        rulers.append({
            'ruler_name': binding.get('rulerLabel', {}).get('value', 'Unknown'),
            'ruler_title': 'Emperor',
            'ruler_wiki_url': wiki_url,
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

    imported = 0

    for snapshot in snapshots:
        snapshot_id, snap_year, snap_era, snap_sort_year = snapshot

        # Find the ruler for this time period
        best_ruler = None
        for ruler in rulers:
            ruler_start = year_to_sort_year(ruler['reign_start_year'], ruler['reign_start_era'])
            ruler_end = year_to_sort_year(
                ruler['reign_end_year'] or ruler['reign_start_year'],
                ruler['reign_end_era'] or ruler['reign_start_era']
            )

            # Check if this ruler was in power during this snapshot
            if ruler_start <= snap_sort_year <= ruler_end:
                best_ruler = ruler
                break
            # Or find the most recent ruler before this snapshot
            elif ruler_end <= snap_sort_year:
                best_ruler = ruler

        if best_ruler:
            cur.execute("""
                INSERT INTO nation_snapshots (
                    nation_id, snapshot_id, ruler_title, ruler_name, ruler_wiki_url,
                    reign_start_year, reign_start_era, reign_end_year, reign_end_era,
                    capital, language, religion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (nation_id, snapshot_id) DO UPDATE SET
                    ruler_title = EXCLUDED.ruler_title,
                    ruler_name = EXCLUDED.ruler_name,
                    ruler_wiki_url = EXCLUDED.ruler_wiki_url,
                    reign_start_year = EXCLUDED.reign_start_year,
                    reign_start_era = EXCLUDED.reign_start_era,
                    reign_end_year = EXCLUDED.reign_end_year,
                    reign_end_era = EXCLUDED.reign_end_era,
                    capital = EXCLUDED.capital,
                    language = EXCLUDED.language,
                    religion = EXCLUDED.religion
            """, (
                nation_id, snapshot_id,
                best_ruler['ruler_title'], best_ruler['ruler_name'], best_ruler['ruler_wiki_url'],
                best_ruler['reign_start_year'], best_ruler['reign_start_era'],
                best_ruler['reign_end_year'], best_ruler['reign_end_era'],
                best_ruler['capital'], best_ruler['language'], best_ruler['religion']
            ))
            imported += 1
            print(f"  {snap_year} {snap_era}: {best_ruler['ruler_name']} ({best_ruler['ruler_title']})")

    conn.commit()
    conn.close()

    return imported


def main():
    print("Importing nation snapshots from Wikidata...\n")

    # Try Wikidata first
    print("Querying Wikidata for Roman emperors...")
    results = query_wikidata(ROMAN_EMPERORS_QUERY)

    if results:
        emperors = parse_wikidata_results(results)
        print(f"Found {len(emperors)} emperors from Wikidata")
    else:
        print("Using fallback emperor data...")
        emperors = ROMAN_EMPERORS_FALLBACK

    # Combine with Republic data
    all_rulers = ROMAN_REPUBLIC_DATA + emperors

    # Sort by reign start
    all_rulers.sort(key=lambda r: year_to_sort_year(r['reign_start_year'], r['reign_start_era']))

    print(f"\nTotal rulers: {len(all_rulers)}")

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

    print("\nDone!")


if __name__ == '__main__':
    main()
