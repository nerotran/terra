#!/usr/bin/env python3
"""
Import Natural Earth land data into PostgreSQL/PostGIS for base map.

Usage:
    python import_basemap.py
"""

import json
import os
import sys
import urllib.request
import psycopg2
from pathlib import Path

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB', 'terra'),
    'user': os.getenv('POSTGRES_USER', 'terra'),
    'password': os.getenv('POSTGRES_PASSWORD', 'terra_dev')
}

# Natural Earth 50m land data (good balance of detail and performance)
LAND_URL = os.getenv('LAND_URL', 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_land.geojson')


def download_land_data():
    """Download Natural Earth land GeoJSON."""
    print("Downloading land data from Natural Earth...")
    with urllib.request.urlopen(LAND_URL) as response:
        return json.loads(response.read().decode('utf-8'))


def load_file(filepath):
    """Load GeoJSON from a local file."""
    print(f"Loading from {filepath}...")
    with open(filepath) as f:
        return json.load(f)


def import_land_data(data):
    """Import land features into the database."""
    features = data.get('features', [])
    print(f"Found {len(features)} land features")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Clear existing land data
    cur.execute("DELETE FROM base_map WHERE feature_type = 'land'")
    print("Cleared existing land data")

    imported = 0

    for feat in features:
        geometry = feat.get('geometry')
        if not geometry:
            continue

        props = feat.get('properties', {})
        name = props.get('name', props.get('featurecla', 'Land'))
        geometry_json = json.dumps(geometry)

        cur.execute("""
            INSERT INTO base_map (feature_type, name, geometry, properties)
            VALUES (
                'land',
                %s,
                ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)),
                %s
            )
            RETURNING id
        """, (name, geometry_json, json.dumps(props)))

        imported += 1
        print(f"  Imported: {name}")

    conn.commit()
    conn.close()

    print(f"\nDone: {imported} imported")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.exists():
            print(f"Error: {path} not found")
            sys.exit(1)
        data = load_file(path)
    else:
        data = download_land_data()

    import_land_data(data)
