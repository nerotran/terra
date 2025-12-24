#!/usr/bin/env python3
"""
Import Roman Empire territories from TopoJSON/GeoJSON into PostgreSQL/PostGIS

Usage:
    python import_territories.py data/CombinedExtentLayers_v6.topojson
"""

import json
import os
import sys
import re
import psycopg2
from pathlib import Path

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB', 'terra'),
    'user': os.getenv('POSTGRES_USER', 'terra'),
    'password': os.getenv('POSTGRES_PASSWORD', 'terra_dev')
}


def parse_year_string(props):
    """Extract year and era from properties.year_string like '298 B.C.' or 'A.D. 117'"""
    year_str = props.get('year_string', '')
    if not year_str:
        return None
    
    # Format: "298 B.C." (year first)
    match = re.search(r'(\d+)\s*(B\.?C\.?|A\.?D\.?)', year_str, re.IGNORECASE)
    if match:
        year = int(match.group(1))
        era = 'BC' if 'B' in match.group(2).upper() else 'AD'
        return (year, era)
    
    # Format: "A.D. 117" (era first)
    match = re.search(r'(B\.?C\.?|A\.?D\.?)\s*(\d+)', year_str, re.IGNORECASE)
    if match:
        year = int(match.group(2))
        era = 'BC' if 'B' in match.group(1).upper() else 'AD'
        return (year, era)
    
    return None


def decode_topojson(data):
    """Convert TopoJSON to GeoJSON features."""
    arcs = data['arcs']
    transform = data.get('transform')
    
    # Pre-decode all arcs (apply delta encoding + transform)
    decoded_arcs = []
    for arc in arcs:
        coords = []
        x, y = 0, 0
        for dx, dy in arc:
            x += dx
            y += dy
            if transform:
                coords.append([
                    x * transform['scale'][0] + transform['translate'][0],
                    y * transform['scale'][1] + transform['translate'][1]
                ])
            else:
                coords.append([x, y])
        decoded_arcs.append(coords)
    
    def get_arc(idx):
        """Get arc by index, reversing if negative."""
        if idx >= 0:
            return list(decoded_arcs[idx])
        else:
            return list(reversed(decoded_arcs[~idx]))
    
    def decode_ring(arc_indices):
        """Stitch arcs into a closed ring."""
        coords = []
        for idx in arc_indices:
            arc = get_arc(idx)
            if coords:
                # Skip duplicate point at junction
                if arc[0] == coords[-1]:
                    arc = arc[1:]
            coords.extend(arc)
        # Close ring
        if coords and coords[0] != coords[-1]:
            coords.append(coords[0])
        return coords
    
    def decode_geometry(geom):
        """Decode a TopoJSON geometry to GeoJSON."""
        gtype = geom.get('type')
        
        if gtype == 'Polygon':
            return {
                'type': 'Polygon',
                'coordinates': [decode_ring(ring) for ring in geom['arcs']]
            }
        elif gtype == 'MultiPolygon':
            return {
                'type': 'MultiPolygon',
                'coordinates': [
                    [decode_ring(ring) for ring in polygon]
                    for polygon in geom['arcs']
                ]
            }
        return None
    
    # Extract features from all objects
    features = []
    for obj_name, obj in data.get('objects', {}).items():
        if obj.get('type') == 'GeometryCollection':
            for geom in obj.get('geometries', []):
                geometry = decode_geometry(geom)
                if geometry:
                    features.append({
                        'type': 'Feature',
                        'properties': {**geom.get('properties', {}), '_layer': obj_name},
                        'geometry': geometry
                    })
        else:
            geometry = decode_geometry(obj)
            if geometry:
                features.append({
                    'type': 'Feature',
                    'properties': {**obj.get('properties', {}), '_layer': obj_name},
                    'geometry': geometry
                })
    
    return features


def load_file(filepath):
    """Load GeoJSON or TopoJSON file."""
    with open(filepath) as f:
        data = json.load(f)
    
    if 'arcs' in data:
        print("Detected TopoJSON, converting...")
        return decode_topojson(data)
    
    if data.get('type') == 'FeatureCollection':
        return data['features']
    elif data.get('type') == 'Feature':
        return [data]
    
    return [{'type': 'Feature', 'geometry': data, 'properties': {}}]


def import_file(filepath):
    """Import GeoJSON or TopoJSON file."""
    features = load_file(filepath)
    print(f"Found {len(features)} features")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Cache controllers
    cur.execute("SELECT name, id FROM controllers")
    controllers = dict(cur.fetchall())
    
    # Cache snapshots (will grow as we insert)
    cur.execute("SELECT year, era, id FROM time_snapshots")
    snapshots = {(r[0], r[1]): r[2] for r in cur.fetchall()}
    
    imported, skipped = 0, 0
    
    for feat in features:
        props = feat.get('properties', {})
        
        parsed = parse_year_string(props)
        if not parsed:
            layer = props.get('_layer', props.get('year_string', 'unknown'))
            print(f"  Skip: {layer} (unknown period)")
            skipped += 1
            continue
        
        year, era = parsed
        
        # Create snapshot if it doesn't exist
        if (year, era) not in snapshots:
            label = props.get('title_header', props.get('long_name', f'{year} {era}'))
            cur.execute("""
                INSERT INTO time_snapshots (year, era, label, description)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (year, era, label, props.get('long_name', '')))
            snapshot_id = cur.fetchone()[0]
            snapshots[(year, era)] = snapshot_id
            print(f"  Created snapshot: {year} {era}")
        
        snapshot_id = snapshots[(year, era)]
        
        # Republic before 27 BC, Empire after
        controller = 'rome_republic' if era == 'BC' and year > 27 else 'rome'
        controller_id = controllers[controller]
        
        name = props.get('long_name', props.get('name', f'Roman Territory {year} {era}'))
        geometry = json.dumps(feat['geometry'])
        
        cur.execute("""
            INSERT INTO territories (controller_id, snapshot_id, name, geometry, geojson, properties)
            VALUES (%s, %s, %s, ST_Multi(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))), %s, %s)
            ON CONFLICT (controller_id, snapshot_id, name) 
            DO UPDATE SET geometry = EXCLUDED.geometry, geojson = EXCLUDED.geojson
            RETURNING id
        """, (controller_id, snapshot_id, name, geometry, json.dumps(feat), json.dumps(props)))
        
        imported += 1
        print(f"  {year} {era}: {name}")
    
    conn.commit()
    
    # Refresh cumulative territories view
    print("\nRefreshing cumulative territories view...")
    cur.execute("REFRESH MATERIALIZED VIEW cumulative_territories;")
    conn.commit()
    
    conn.close()
    
    print(f"\nDone: {imported} imported, {skipped} skipped")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_territories.py <file.topojson|geojson>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: {path} not found")
        sys.exit(1)
    
    import_file(path)
