# Terra Project Summary

## Overview
Interactive historical map visualization showing territorial changes through time for all countries and civilizations throughout human history. User drags a time slider, borders evolve on the map.

The current implementation starts with the Roman Empire, but the architecture is designed to support any historical territory data.

**GitHub:** https://github.com/nerotran/terra

## Current State (Phase 1 Complete)
- Working website with time slider showing Roman Empire territories (500 BC - 117 AD)
- Map displays land/geography projection
- Hover highlighting on territories implemented

## Tech Stack
- **Database:** PostgreSQL 16 + PostGIS 3.4 (Docker)
- **API:** .NET Core 8 Web API
- **Frontend:** React + TypeScript + Vite + D3.js
- **Data Sources:**
  - Territories: siriusbontea/roman-empire repository (BSD license)
  - Rulers: Wikidata SPARQL API (consuls Q40779, emperors Q842606)

## Repo Structure
```
terra/
├── docker-compose.yml
├── terra.sln
├── .env.example
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

### Tables
- `nations` - Political entities (Rome, etc.) with name, display_name, color, founded_year, founded_era, description, wiki_url
- `time_snapshots` - Time periods with year, era (BC/AD), sort_year (computed), label
- `territories` - Individual territory boundaries (incremental additions per period)
  - `nation_id`: Foreign key to nations table (territories reference nations, don't store nation data)
  - `geometry`: PostGIS GEOMETRY(MultiPolygon, 4326)
  - `geojson`: JSONB copy for API responses
  - `properties`: JSONB metadata from source
- `nation_snapshots` - Time-varying nation data (rulers, capitals, etc.)
  - `nation_id`, `snapshot_id`: Foreign keys
  - `ruler_title`, `ruler_name`, `ruler_wiki_url`, `reign_start_year/era`, `reign_end_year/era`
  - `capital`, `language`, `religion`, `population`

### Key View
- `cumulative_territories` - Materialized view that unions all territories up to each time period
  - Returns `nation_id` reference (color/nation data fetched via join)
  - Uses ST_MakeValid() to fix self-intersecting polygons before ST_Union()
  - Refresh after import: `REFRESH MATERIALIZED VIEW cumulative_territories;`

### Sort Year Logic
- BC years stored as negative: 500 BC → sort_year = -500
- AD years stored as positive: 117 AD → sort_year = 117
- Enables simple chronological ORDER BY

## Data Model Notes

### Incremental Territory Data
Source TopoJSON contains incremental territorial additions, NOT complete snapshots:
- 500 BC: Just Rome
- 218 BC: Italy + Sicily (new additions only)
- 117 AD: Just Mesopotamia (Trajan's conquests)

The `cumulative_territories` view unions everything up to each period to show total empire extent.

## API Endpoints
- `GET /api/territories` - All cumulative territories (for time slider)
- `GET /api/territories/{snapshotId}` - Single territory by snapshot
- `GET /api/snapshots` - All time periods

### Territory Response Structure
Territories include nested nation object (not just color):
```json
{
  "snapshot_id": 1,
  "year": 500,
  "era": "BC",
  "sort_year": -500,
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

## Completed Features

### Issue #2: Show nation info on territory click (Phase 2 - Complete)

Display panel with: Name, Current ruler, Founded on, Language, Religion, Description
Data changes dynamically based on selected date.

**UI Design:**
- Side panel slides in from right, dark theme matching map
- Layout: Header (nation name + year), Ruler section, Info grid (Founded, Capital, Language, Religion), Description
- Component: `NationPanel.tsx`

**Database Changes (all complete):**
- ✅ Table rename: `controllers` → `nations`
- ✅ C# model rename: `Empire` → `Nation`, `EmpireId` → `NationId`
- ✅ Territories reference nations via `nation_id`, don't store color directly
- ✅ `nations` table extended with `founded_year`, `founded_era`, `description`
- ✅ `nation_snapshots` table for time-varying data (rulers, capitals, etc.)

**Data Import:**
- ✅ `import_nation_snapshots.py` - Queries Wikidata for Roman consuls (Republic) and emperors (Empire)
- ✅ Added to Docker importer service
- ✅ Performance optimized for large-scale imports (batch inserts, binary search, buffered logging)

**API Endpoint:**
- `GET /api/nations/{nationId}/snapshot/{snapshotId}` - Returns nation + current ruler snapshot

## Open Issues

### Asset Storage

**Portraits (working):**
- Uses MediaWiki API to get downloadable thumbnail URLs (avoids 403 Forbidden errors from direct Wikimedia URLs)
- Downloaded to `data/assets/portraits/` during import
- Cached by ruler name to avoid duplicate downloads

**Flags (disabled):**
Historical nations like the Roman Republic/Empire don't have traditional "flags" in the modern sense, which creates challenges:

| Approach Tried | Result |
|----------------|--------|
| Wikidata P41 (flag image) | Roman entities don't have P41 property |
| DBpedia flag properties | Returns wrong/unrelated images |
| Wikipedia pageimages API | Returns modern Flag of Italy or map images |
| Keyword search (vexillum, banner, aquila, SPQR) | Inconsistent results, often wrong images |

The fundamental issue is that ancient civilizations used symbols (eagles, standards, vexilla) rather than flags, and these aren't consistently tagged in structured data sources. A better approach might be:
- Curated asset library for historical nations
- Manual mapping of nation → symbol image
- Or accept that some nations won't have flag/emblem images

Code for flag fetching exists in `import_nation_snapshots.py` (`get_flag_from_wikipedia_url()`) but is disabled in `main()`.

### Nations for future
Adding more nations (Carthage, Ptolemaic Egypt, Seleucid Empire, etc.) is a separate issue. The import scripts are designed to scale.

## Import Scripts Performance

All import scripts are optimized to scale for many nations:

### import_nation_snapshots.py
| Optimization | Description |
|--------------|-------------|
| Wikidata SPARQL | Fetches consuls (Q40779) and emperors (Q842606) in bulk queries |
| Binary search | O(log n) ruler lookup using `bisect` instead of O(n) linear scan |
| Batch inserts | `execute_values()` for single DB round-trip |
| Buffered logging | Collects log messages, writes once at end |
| Portrait caching | Avoids re-downloading same ruler's portrait |

### import_territories.py & import_basemap.py
| Optimization | Description |
|--------------|-------------|
| Batch inserts | `executemany()` instead of individual INSERTs |
| Two-pass import | Collect records first, then batch insert |

### Logs
Import logs are written to `logs/` directory (gitignored).

## Future Scaling Notes
- Data files kept separate (auto-downloaded by import scripts, cached locally, not committed)
- `data/README.md` documents data sources
- Goal: One contiguous world timeline, not separate scenarios
- Import scripts designed for bulk imports of many nations

## Key Technical Decisions
1. PostGIS for spatial queries (faster than JS-based geometry operations)
2. Materialized view for cumulative territories (computed once, not per request)
3. ST_MakeValid() to fix invalid geometries from source data
4. TopoJSON decoded server-side during import, stored as GeoJSON
5. D3.js + SVG for map rendering (not Leaflet/Mapbox)
6. Territories reference nations (FK), don't embed nation data (color, name) — single source of truth

## Commands Reference

```bash
# Start database
docker-compose up -d

# Import all data via Docker (recommended)
docker compose --profile import up

# Or run importer on-demand
docker compose run --rm importer

# Manual import (without Docker)
pip install psycopg2-binary
python db/scripts/import_basemap.py           # Downloads Natural Earth land data
python db/scripts/import_territories.py       # Downloads Roman Empire territories
python db/scripts/import_nation_snapshots.py  # Imports rulers from Wikidata

# Or use custom data file
python db/scripts/import_territories.py path/to/custom.topojson

# Run API
cd api/Terra.Api && dotnet run

# Run frontend
cd web && npm install && npm run dev

# Verify database
./db/scripts/verify_db.sh
```

### Environment Variables (optional)
Data source URLs are configurable via `.env`:
- `ROMAN_EMPIRE_URL` - Roman Empire TopoJSON data URL
- `LAND_URL` - Natural Earth land GeoJSON URL

## Database Credentials (Local Dev)
- Host: localhost
- Database: terra
- User: terra
- Password: terra_dev
- Port: 5432
