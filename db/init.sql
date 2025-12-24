-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Nations table (Rome, Carthage, etc.)
CREATE TABLE nations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200),
    color VARCHAR(7) DEFAULT '#8B0000',  -- Default Roman red
    wiki_url VARCHAR(500),
    founded_year INTEGER,
    founded_era VARCHAR(2) CHECK (founded_era IN ('BC', 'AD')),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Nation snapshots table (time-varying data like rulers, capitals)
CREATE TABLE nation_snapshots (
    id SERIAL PRIMARY KEY,
    nation_id INTEGER NOT NULL REFERENCES nations(id),
    snapshot_id INTEGER NOT NULL REFERENCES time_snapshots(id),
    ruler_title VARCHAR(100),
    ruler_name VARCHAR(200),
    ruler_wiki_url VARCHAR(500),
    reign_start_year INTEGER,
    reign_start_era VARCHAR(2) CHECK (reign_start_era IN ('BC', 'AD')),
    reign_end_year INTEGER,
    reign_end_era VARCHAR(2) CHECK (reign_end_era IN ('BC', 'AD')),
    capital VARCHAR(200),
    language VARCHAR(200),
    religion VARCHAR(200),
    population VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nation_id, snapshot_id)
);

CREATE INDEX idx_nation_snapshots_nation ON nation_snapshots(nation_id);
CREATE INDEX idx_nation_snapshots_snapshot ON nation_snapshots(snapshot_id);

-- Base map features (land, lakes, etc.)
CREATE TABLE base_map (
    id SERIAL PRIMARY KEY,
    feature_type VARCHAR(50) NOT NULL,  -- 'land', 'lakes', 'rivers'
    name VARCHAR(200),
    geometry GEOMETRY(Geometry, 4326),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_base_map_geometry ON base_map USING GIST(geometry);
CREATE INDEX idx_base_map_type ON base_map(feature_type);

-- Time snapshots table
CREATE TABLE time_snapshots (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    era VARCHAR(2) NOT NULL CHECK (era IN ('BC', 'AD')),
    sort_year INTEGER GENERATED ALWAYS AS (CASE WHEN era = 'BC' THEN -year ELSE year END) STORED,
    label VARCHAR(100),
    description TEXT,
    UNIQUE(year, era)
);

-- Territories table with GeoJSON stored as JSONB
CREATE TABLE territories (
    id SERIAL PRIMARY KEY,
    nation_id INTEGER NOT NULL REFERENCES nations(id),
    snapshot_id INTEGER NOT NULL REFERENCES time_snapshots(id),
    name VARCHAR(200),
    geometry GEOMETRY(MultiPolygon, 4326),  -- PostGIS geometry column
    geojson JSONB,  -- Original GeoJSON for reference
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nation_id, snapshot_id, name)
);

-- Create spatial index for fast geographic queries
CREATE INDEX idx_territories_geometry ON territories USING GIST(geometry);
CREATE INDEX idx_territories_snapshot ON territories(snapshot_id);
CREATE INDEX idx_territories_nation ON territories(nation_id);
CREATE INDEX idx_snapshots_sort_year ON time_snapshots(sort_year);

-- Seed data: Roman nations
INSERT INTO nations (name, display_name, color, wiki_url, founded_year, founded_era, description) VALUES
    ('rome', 'Roman Empire', '#8B0000', 'https://en.wikipedia.org/wiki/Roman_Empire', 27, 'BC',
     'The Roman Empire was one of the largest and most influential civilizations in world history, known for its military prowess, engineering achievements, and lasting cultural legacy.'),
    ('rome_republic', 'Roman Republic', '#CD5C5C', 'https://en.wikipedia.org/wiki/Roman_Republic', 509, 'BC',
     'The Roman Republic was the era of classical Roman civilization beginning with the overthrow of the Roman Kingdom and ending with the establishment of the Roman Empire.');

-- Time snapshots will be created dynamically during import

-- Function to import GeoJSON feature
CREATE OR REPLACE FUNCTION import_geojson_feature(
    p_nation_name VARCHAR,
    p_year INTEGER,
    p_era VARCHAR,
    p_geojson JSONB
) RETURNS INTEGER AS $$
DECLARE
    v_nation_id INTEGER;
    v_snapshot_id INTEGER;
    v_territory_id INTEGER;
    v_geometry GEOMETRY;
    v_name VARCHAR;
BEGIN
    -- Get nation ID
    SELECT id INTO v_nation_id FROM nations WHERE name = p_nation_name;
    IF v_nation_id IS NULL THEN
        RAISE EXCEPTION 'Nation not found: %', p_nation_name;
    END IF;
    
    -- Get snapshot ID
    SELECT id INTO v_snapshot_id FROM time_snapshots WHERE year = p_year AND era = p_era;
    IF v_snapshot_id IS NULL THEN
        RAISE EXCEPTION 'Snapshot not found: % %', p_year, p_era;
    END IF;
    
    -- Extract geometry from GeoJSON
    v_geometry := ST_SetSRID(ST_GeomFromGeoJSON(p_geojson->>'geometry'), 4326);
    
    -- Make sure it's a MultiPolygon
    IF ST_GeometryType(v_geometry) = 'ST_Polygon' THEN
        v_geometry := ST_Multi(v_geometry);
    END IF;
    
    -- Get name from properties
    v_name := COALESCE(p_geojson->'properties'->>'name', 'Territory');
    
    -- Insert territory
    INSERT INTO territories (nation_id, snapshot_id, name, geometry, geojson, properties)
    VALUES (v_nation_id, v_snapshot_id, v_name, v_geometry, p_geojson, p_geojson->'properties')
    RETURNING id INTO v_territory_id;
    
    RETURN v_territory_id;
END;
$$ LANGUAGE plpgsql;

-- View for easy GeoJSON export (sorted chronologically)
CREATE OR REPLACE VIEW territories_geojson AS
SELECT
    t.id,
    ts.year,
    ts.era,
    ts.sort_year,
    ts.label as period_label,
    n.display_name as nation_name,
    n.color,
    t.name,
    ST_AsGeoJSON(t.geometry)::jsonb as geometry,
    t.properties
FROM territories t
JOIN time_snapshots ts ON t.snapshot_id = ts.id
JOIN nations n ON t.nation_id = n.id
ORDER BY ts.sort_year;

-- Cumulative territories (union of all territories up to each time period)
-- Run REFRESH MATERIALIZED VIEW cumulative_territories; after importing data
CREATE MATERIALIZED VIEW cumulative_territories AS
SELECT
    ts.id as snapshot_id,
    ts.year,
    ts.era,
    ts.sort_year,
    ts.label,
    (SELECT t.nation_id FROM territories t
     WHERE t.snapshot_id = ts.id LIMIT 1) as nation_id,
    ST_Multi(ST_Union(ST_MakeValid(t2.geometry)))::geometry(MultiPolygon, 4326) as geometry
FROM time_snapshots ts
JOIN time_snapshots ts2 ON ts2.sort_year <= ts.sort_year
JOIN territories t2 ON t2.snapshot_id = ts2.id
GROUP BY ts.id, ts.year, ts.era, ts.sort_year, ts.label
ORDER BY ts.sort_year
WITH NO DATA;

-- Indexes for cumulative view (created after refresh)
CREATE INDEX idx_cumulative_sort ON cumulative_territories(sort_year);
CREATE INDEX idx_cumulative_geom ON cumulative_territories USING GIST(geometry);

-- View for cumulative territories as GeoJSON
CREATE OR REPLACE VIEW cumulative_territories_geojson AS
SELECT
    snapshot_id,
    year,
    era,
    sort_year,
    label,
    nation_id,
    ST_AsGeoJSON(geometry)::jsonb as geometry
FROM cumulative_territories
ORDER BY sort_year;
