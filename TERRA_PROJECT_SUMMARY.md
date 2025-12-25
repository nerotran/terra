# Terra Project Summary

## Overview

Interactive historical map visualization showing territorial changes through time for all countries and civilizations throughout human history. User drags a time slider, borders evolve on the map.

The current implementation starts with the Roman Empire, but the architecture is designed to support any historical territory data. A separate geodata builder service is planned to aggregate data from multiple sources.

**GitHub:** https://github.com/nerotran/terra

## Current State

### Completed
- **Phase 1:** Working website with time slider showing Roman Empire territories (500 BC - 200 AD)
- **Phase 2:** Nation info panel with ruler data, dynamic based on selected year
- **Issue #3:** Database schema refactor - rulers table, signed years throughout

### In Progress
- **Issue #4:** Year-by-year timeline with event-based schema
- **Terra Geodata Builder:** Separate API for aggregating territory data (see `docs/terra-geodata-builder-design.md`)

## Tech Stack

- **Database:** PostgreSQL 16 + PostGIS 3.4 (Docker)
- **API:** .NET Core 8 Web API (port 5025)
- **Frontend:** React 19 + TypeScript + Vite + D3.js
- **Data Sources:**
  - Territories: siriusbontea/roman-empire repository (13 snapshots, BSD license)
  - Rulers: Wikidata SPARQL API (consuls Q40779, emperors Q842606)

## Repo Structure

```
terra/
├── docker-compose.yml
├── terra.sln
├── .env.example
├── docs/
│   └── terra-geodata-builder-design.md  # Design for geodata aggregation service
├── db/
│   ├── init.sql
│   └── scripts/
│       ├── import_territories.py
│       ├── import_basemap.py
│       ├── import_nation_snapshots.py
│       └── verify_db.sh
├── api/Terra.Api/
│   ├── Controllers/ (TerritoriesController, SnapshotsController, NationsController)
│   ├── Services/TerritoryService.cs
│   ├── Data/TerraDbContext.cs
│   └── Models/ (Entities.cs, Dtos.cs)
├── web/src/
│   ├── App.tsx
│   ├── components/ (Map.tsx, TimeSlider.tsx, NationPanel.tsx)
│   ├── api/client.ts
│   └── types/index.ts
├── logs/ (gitignored, import script logs)
└── data/ (gitignored)
    └── assets/portraits/ (downloaded ruler images)
```

## Database Schema

### Signed Year Convention

All years are stored as signed integers:
- BC years are negative: 500 BC → -500
- AD years are positive: 117 AD → 117
- Enables simple chronological ORDER BY
- Helper functions: `year_to_display()`, `display_to_year()`, `get_ruler_for_year()`

### Tables

- **`nations`** - Political entities (Rome, etc.)
  - `name`, `display_name`, `color`, `wiki_url`, `flag_url`
  - `founded_year` (signed int), `description`

- **`rulers`** - Historical rulers (emperors, consuls, kings)
  - `nation_id`: Foreign key to nations
  - `name`, `title`, `wiki_url`, `portrait_url`
  - `reign_start`, `reign_end`: Signed integers

- **`time_snapshots`** - Time periods
  - `year` (signed int), `label`, `description`

- **`territories`** - Individual territory boundaries (incremental per period)
  - `nation_id`, `snapshot_id`: Foreign keys
  - `geometry`: PostGIS GEOMETRY(MultiPolygon, 4326)
  - `geojson`: JSONB copy for API responses
  - `properties`: JSONB metadata from source

- **`nation_snapshots`** - Time-varying nation data
  - `nation_id`, `snapshot_id`, `ruler_id`: Foreign keys
  - `capital`, `language`, `religion`, `population`

### Key View

- **`cumulative_territories`** - Materialized view that unions all territories up to each time period
  - Returns `nation_id` reference (color/nation data fetched via join)
  - Uses ST_MakeValid() to fix self-intersecting polygons before ST_Union()
  - Refresh after import: `REFRESH MATERIALIZED VIEW cumulative_territories;`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/territories` | All cumulative territories (for time slider) |
| `GET /api/territories/{snapshotId}` | Single territory by snapshot |
| `GET /api/snapshots` | All time periods |
| `GET /api/nations/{nationId}/snapshot/{snapshotId}` | Nation + ruler for time period |
| `GET /api/basemap` | Land geography |

### Response Structures

**Territory:**
```json
{
  "snapshot_id": 1,
  "year": -500,
  "label": "500 BC",
  "nation": {
    "id": 1,
    "name": "rome",
    "display_name": "Roman Empire",
    "color": "#8B0000"
  },
  "geometry": { "type": "MultiPolygon", ... }
}
```

**Nation Details:**
```json
{
  "id": 1,
  "name": "rome",
  "display_name": "Roman Empire",
  "founded_year": -27,
  "ruler": {
    "id": 42,
    "name": "Trajan",
    "title": "Emperor",
    "reign_start": 98,
    "reign_end": 117,
    "wiki_url": "...",
    "portrait_url": "/assets/portraits/trajan.jpg"
  },
  "capital": "Rome",
  "language": "Latin",
  ...
}
```

## Completed Features

### Issue #2: Nation Info Panel (Complete)

Display panel with: Name, Current ruler, Founded, Language, Religion, Description. Data changes dynamically based on selected date.

- Side panel slides in from right, dark theme matching map
- Ruler section with portrait, title, reign dates
- Info grid (Founded, Capital, Language, Religion)
- Component: `NationPanel.tsx`

### Issue #3: Schema Refactor (Complete)

Simplified the database schema for better maintainability:

- ✅ Created separate `rulers` table (was embedded in nation_snapshots)
- ✅ Removed `era` columns - all years now signed integers
- ✅ Removed `sort_year` computed column (no longer needed)
- ✅ Added SQL helper functions for year display conversion
- ✅ Updated API models and DTOs
- ✅ Updated frontend to use `yearToDisplay()` helper

## Open Issues

### Asset Storage

**Portraits (working):**
- Uses MediaWiki API to get downloadable thumbnail URLs
- Downloaded to `data/assets/portraits/` during import
- Cached by ruler name to avoid duplicate downloads

**Flags (disabled):**
Historical nations don't have traditional "flags". Approaches tried:

| Approach | Result |
|----------|--------|
| Wikidata P41 | Roman entities don't have P41 property |
| DBpedia flag properties | Returns wrong/unrelated images |
| Wikipedia pageimages API | Returns modern Flag of Italy or map images |

Better approach: Curated asset library or manual mapping.

### Issue #4: Year-by-year Timeline (Planned)

**Problem:** Need continuous yearly timeline. Current data provides 13 snapshots:

| Year | Period |
|------|--------|
| 500 BC | Early Republic |
| 338 BC | Post-Latin Wars |
| 298 BC | Mid-Republic |
| 290 BC | Post-Samnite Wars |
| 272 BC | After Pyrrhic Wars |
| 264 BC | Pre-First Punic War |
| 218 BC | Second Punic War |
| 133 BC | Late Republic |
| 60 BC | Late Republic |
| 14 AD | Early Imperial |
| 69 AD | Flavian era |
| 117 AD | Maximum extent (Trajan) |
| 200 AD | Later Imperial |

**Approach:** Event-based schema with `start_year`/`end_year` columns. See full design in Issue #4 section below.

## Terra Geodata Builder (New Project)

A separate service to aggregate, normalize, and process historical territory data from multiple sources. This enables scaling to all countries and civilizations throughout history.

**Design document:** `docs/terra-geodata-builder-design.md`

### Why a Separate Service?

- Massive data aggregation from hundreds of sources
- Complex GIS processing (different formats, resolutions, conventions)
- Separation of concerns from main Terra app
- Potential for community data contributions

### Target Scope

1. **Phase 1:** Ancient Mediterranean (Rome, Carthage, Egypt, etc.)
2. **Phase 2:** Ancient World (Persia, Greece, India, China)
3. **Phase 3:** Medieval Period (Byzantium, Caliphates, Mongols)
4. **Phase 4:** Early Modern (Colonial empires, Ottomans)
5. **Phase 5:** Modern Era (Nation-states 1648 - present)

### Data Sources Investigated

| Source | Useful? | Notes |
|--------|---------|-------|
| [Sirius Bontea](https://github.com/siriusbontea/roman-empire) | ✅ Yes | Primary source, 13 Roman snapshots |
| [Historical Basemaps](https://github.com/aourednik/historical-basemaps) | ✅ Yes | World boundaries 3000 BC - present |
| [Project MERCURY](https://projectmercury.eu/datasets/) | ✅ Yes | Roman provinces, multiple formats |
| [CShapes](https://icr.ethz.ch/data/cshapes/) | ✅ Yes | Modern states post-1886 |
| AWMC | ❌ No | Less data than Sirius Bontea |
| DARMC | ❌ No | Roads only, no territories |
| Pelagios | ❌ No | Places only, no territories |

### Proposed Tech Stack

- **Python** with FastAPI, GeoPandas, Shapely
- PostgreSQL + PostGIS for storage
- REST API for Terra integration

## Issue #4 Technical Details

### Schema Changes

```sql
ALTER TABLE territories
  ADD COLUMN start_year INT NOT NULL,
  ADD COLUMN end_year INT;

CREATE INDEX idx_territories_range ON territories
  USING GIST (int4range(start_year, COALESCE(end_year, 2100)));
```

### Query Pattern

```sql
-- "What did Rome control in 50 BC?"
SELECT ST_Union(geometry) FROM territories
WHERE nation_id = 1
  AND start_year <= -50
  AND (end_year IS NULL OR end_year >= -50);
```

### API Changes

- Current: `GET /api/territories/{snapshotId}`
- New: `GET /api/territories?year=-300`

### Gap-filling Priorities

Major events missing between snapshots:
- 241 BC: End of First Punic War (Sicily)
- 146 BC: Destruction of Carthage (Africa province)
- 58-50 BC: Caesar's Gallic Wars
- 30 BC: Annexation of Egypt
- 43 AD: Conquest of Britain

## Import Scripts

All scripts are optimized for scale:

| Script | Optimizations |
|--------|---------------|
| `import_nation_snapshots.py` | Wikidata SPARQL, binary search, batch inserts, portrait caching |
| `import_territories.py` | Batch inserts, two-pass import |
| `import_basemap.py` | Batch inserts |

Logs written to `logs/` directory (gitignored).

## Key Technical Decisions

1. PostGIS for spatial queries (faster than JS-based geometry)
2. Materialized view for cumulative territories (computed once, not per request)
3. ST_MakeValid() to fix invalid geometries from source data
4. TopoJSON decoded server-side during import, stored as GeoJSON
5. D3.js + SVG for map rendering (not Leaflet/Mapbox)
6. Territories reference nations via FK (single source of truth)
7. Signed integers for years (no separate era column)
8. Separate rulers table (normalized, not embedded in snapshots)

## Commands Reference

```bash
# Start database
docker-compose up -d

# Import all data via Docker (recommended)
docker compose --profile import up

# Manual import
pip install psycopg2-binary
python db/scripts/import_basemap.py
python db/scripts/import_territories.py
python db/scripts/import_nation_snapshots.py

# Run API (http://localhost:5025)
cd api/Terra.Api && dotnet run

# Run frontend (http://localhost:5173)
cd web && npm install && npm run dev

# Verify database
./db/scripts/verify_db.sh
```

## Database Credentials (Local Dev)

- Host: localhost
- Database: terra
- User: terra
- Password: terra_dev
- Port: 5432
