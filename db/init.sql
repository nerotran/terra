-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- HELPER FUNCTIONS for year display (negative = BC, positive = AD)
-- ============================================================================

-- Convert signed year to display string (e.g., -500 -> '500 BC', 117 -> '117 AD')
CREATE OR REPLACE FUNCTION year_to_display(p_year INTEGER)
RETURNS VARCHAR AS $$
BEGIN
    IF p_year < 0 THEN
        RETURN ABS(p_year)::VARCHAR || ' BC';
    ELSIF p_year > 0 THEN
        RETURN p_year::VARCHAR || ' AD';
    ELSE
        RETURN '1 BC';  -- Year 0 doesn't exist historically
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Convert display string to signed year (e.g., '500 BC' -> -500, '117 AD' -> 117)
CREATE OR REPLACE FUNCTION display_to_year(p_display VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    v_year INTEGER;
    v_era VARCHAR(2);
BEGIN
    -- Parse "500 BC" or "117 AD" format
    v_year := (regexp_match(p_display, '(\d+)'))[1]::INTEGER;
    v_era := UPPER((regexp_match(p_display, '(BC|AD)', 'i'))[1]);

    IF v_era = 'BC' THEN
        RETURN -v_year;
    ELSE
        RETURN v_year;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Nations table (Rome, Carthage, etc.)
CREATE TABLE nations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200),
    color VARCHAR(7) DEFAULT '#8B0000',
    wiki_url VARCHAR(500),
    flag_url VARCHAR(500),
    founded_year INTEGER,  -- Signed: negative for BC, positive for AD
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rulers table (emperors, consuls, kings, etc.)
CREATE TABLE rulers (
    id SERIAL PRIMARY KEY,
    nation_id INTEGER NOT NULL REFERENCES nations(id),
    name VARCHAR(200) NOT NULL,
    title VARCHAR(100),  -- Emperor, Consul, King, etc.
    wiki_url VARCHAR(500),
    portrait_url VARCHAR(500),
    reign_start INTEGER NOT NULL,  -- Signed year
    reign_end INTEGER,  -- Signed year (NULL if still reigning or unknown)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rulers_nation ON rulers(nation_id);
CREATE INDEX idx_rulers_reign ON rulers(reign_start, reign_end);

-- Time snapshots table
CREATE TABLE time_snapshots (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL UNIQUE,  -- Signed: negative for BC, positive for AD
    label VARCHAR(100),
    description TEXT
);

CREATE INDEX idx_snapshots_year ON time_snapshots(year);

-- Nation snapshots table (time-varying data like capitals, language)
CREATE TABLE nation_snapshots (
    id SERIAL PRIMARY KEY,
    nation_id INTEGER NOT NULL REFERENCES nations(id),
    snapshot_id INTEGER NOT NULL REFERENCES time_snapshots(id),
    ruler_id INTEGER REFERENCES rulers(id),  -- Current ruler at this snapshot
    capital VARCHAR(200),
    language VARCHAR(200),
    religion VARCHAR(200),
    population VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nation_id, snapshot_id)
);

CREATE INDEX idx_nation_snapshots_nation ON nation_snapshots(nation_id);
CREATE INDEX idx_nation_snapshots_snapshot ON nation_snapshots(snapshot_id);
CREATE INDEX idx_nation_snapshots_ruler ON nation_snapshots(ruler_id);

-- Base map features (land, lakes, etc.)
CREATE TABLE base_map (
    id SERIAL PRIMARY KEY,
    feature_type VARCHAR(50) NOT NULL,
    name VARCHAR(200),
    geometry GEOMETRY(Geometry, 4326),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_base_map_geometry ON base_map USING GIST(geometry);
CREATE INDEX idx_base_map_type ON base_map(feature_type);

-- Territories table
CREATE TABLE territories (
    id SERIAL PRIMARY KEY,
    nation_id INTEGER NOT NULL REFERENCES nations(id),
    snapshot_id INTEGER NOT NULL REFERENCES time_snapshots(id),
    name VARCHAR(200),
    geometry GEOMETRY(MultiPolygon, 4326),
    geojson JSONB,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nation_id, snapshot_id, name)
);

CREATE INDEX idx_territories_geometry ON territories USING GIST(geometry);
CREATE INDEX idx_territories_snapshot ON territories(snapshot_id);
CREATE INDEX idx_territories_nation ON territories(nation_id);

-- ============================================================================
-- SEED DATA
-- ============================================================================

INSERT INTO nations (name, display_name, color, wiki_url, founded_year, description) VALUES
    ('rome', 'Roman Empire', '#8B0000', 'https://en.wikipedia.org/wiki/Roman_Empire', -27,
     'The Roman Empire was one of the largest and most influential civilizations in world history, known for its military prowess, engineering achievements, and lasting cultural legacy.'),
    ('rome_republic', 'Roman Republic', '#CD5C5C', 'https://en.wikipedia.org/wiki/Roman_Republic', -509,
     'The Roman Republic was the era of classical Roman civilization beginning with the overthrow of the Roman Kingdom and ending with the establishment of the Roman Empire.');

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for easy GeoJSON export (sorted chronologically)
CREATE OR REPLACE VIEW territories_geojson AS
SELECT
    t.id,
    ts.year,
    year_to_display(ts.year) as era_display,
    ts.label as period_label,
    n.display_name as nation_name,
    n.color,
    t.name,
    ST_AsGeoJSON(t.geometry)::jsonb as geometry,
    t.properties
FROM territories t
JOIN time_snapshots ts ON t.snapshot_id = ts.id
JOIN nations n ON t.nation_id = n.id
ORDER BY ts.year;

-- Cumulative territories (union of all territories up to each time period)
CREATE MATERIALIZED VIEW cumulative_territories AS
SELECT
    ts.id as snapshot_id,
    ts.year,
    ts.label,
    (SELECT t.nation_id FROM territories t
     WHERE t.snapshot_id = ts.id LIMIT 1) as nation_id,
    ST_Multi(ST_Union(ST_MakeValid(t2.geometry)))::geometry(MultiPolygon, 4326) as geometry
FROM time_snapshots ts
JOIN time_snapshots ts2 ON ts2.year <= ts.year
JOIN territories t2 ON t2.snapshot_id = ts2.id
GROUP BY ts.id, ts.year, ts.label
ORDER BY ts.year
WITH NO DATA;

CREATE INDEX idx_cumulative_year ON cumulative_territories(year);
CREATE INDEX idx_cumulative_geom ON cumulative_territories USING GIST(geometry);

-- View for cumulative territories as GeoJSON
CREATE OR REPLACE VIEW cumulative_territories_geojson AS
SELECT
    snapshot_id,
    year,
    year_to_display(year) as era_display,
    label,
    nation_id,
    ST_AsGeoJSON(geometry)::jsonb as geometry
FROM cumulative_territories
ORDER BY year;

-- ============================================================================
-- HELPER FUNCTION for importing
-- ============================================================================

CREATE OR REPLACE FUNCTION import_geojson_feature(
    p_nation_name VARCHAR,
    p_year INTEGER,
    p_geojson JSONB
) RETURNS INTEGER AS $$
DECLARE
    v_nation_id INTEGER;
    v_snapshot_id INTEGER;
    v_territory_id INTEGER;
    v_geometry GEOMETRY;
    v_name VARCHAR;
BEGIN
    SELECT id INTO v_nation_id FROM nations WHERE name = p_nation_name;
    IF v_nation_id IS NULL THEN
        RAISE EXCEPTION 'Nation not found: %', p_nation_name;
    END IF;

    SELECT id INTO v_snapshot_id FROM time_snapshots WHERE year = p_year;
    IF v_snapshot_id IS NULL THEN
        RAISE EXCEPTION 'Snapshot not found: %', p_year;
    END IF;

    v_geometry := ST_SetSRID(ST_GeomFromGeoJSON(p_geojson->>'geometry'), 4326);

    IF ST_GeometryType(v_geometry) = 'ST_Polygon' THEN
        v_geometry := ST_Multi(v_geometry);
    END IF;

    v_name := COALESCE(p_geojson->'properties'->>'name', 'Territory');

    INSERT INTO territories (nation_id, snapshot_id, name, geometry, geojson, properties)
    VALUES (v_nation_id, v_snapshot_id, v_name, v_geometry, p_geojson, p_geojson->'properties')
    RETURNING id INTO v_territory_id;

    RETURN v_territory_id;
END;
$$ LANGUAGE plpgsql;

-- Function to find ruler for a given nation and year
CREATE OR REPLACE FUNCTION get_ruler_for_year(p_nation_id INTEGER, p_year INTEGER)
RETURNS TABLE(
    id INTEGER,
    name VARCHAR,
    title VARCHAR,
    wiki_url VARCHAR,
    portrait_url VARCHAR,
    reign_start INTEGER,
    reign_end INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT r.id, r.name, r.title, r.wiki_url, r.portrait_url, r.reign_start, r.reign_end
    FROM rulers r
    WHERE r.nation_id = p_nation_id
      AND r.reign_start <= p_year
      AND (r.reign_end IS NULL OR r.reign_end >= p_year)
    ORDER BY r.reign_start DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;
