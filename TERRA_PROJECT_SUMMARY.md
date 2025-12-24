# Terra Project Summary

## Overview
Interactive historical map visualization showing territorial changes through time. User drags a time slider, borders evolve on the map.

**GitHub:** https://github.com/nerotran/terra

## Current State (Phase 1 Complete)
- Working website with time slider showing Roman Empire territories (500 BC - 117 AD)
- Map displays land/geography projection
- Hover highlighting on territories implemented

## Tech Stack
- **Database:** PostgreSQL 16 + PostGIS 3.4 (Docker)
- **API:** .NET Core 8 Web API
- **Frontend:** React + TypeScript + Vite + D3.js
- **Data Source:** siriusbontea/roman-empire repository (BSD license)

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
│       └── verify_db.sh
├── api/Terra.Api/
│   ├── Controllers/ (TerritoriesController, SnapshotsController)
│   ├── Services/TerritoryService.cs
│   ├── Data/TerraDbContext.cs
│   └── Models/ (Entities.cs, Dtos.cs)
├── web/src/
│   ├── App.tsx
│   ├── components/ (Map.tsx, TimeSlider.tsx)
│   ├── api/client.ts
│   └── types/index.ts
└── data/ (not committed, download separately)
```

## Database Schema

### Tables
- `nations` - Political entities (Rome, etc.) with name, display_name, color
- `time_snapshots` - Time periods with year, era (BC/AD), sort_year (computed), label
- `territories` - Individual territory boundaries (incremental additions per period)
  - `nation_id`: Foreign key to nations table (territories reference nations, don't store nation data)
  - `geometry`: PostGIS GEOMETRY(MultiPolygon, 4326)
  - `geojson`: JSONB copy for API responses
  - `properties`: JSONB metadata from source

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

## Open Issues

### Issue #2: Show nation info on territory click (Phase 2 - In Progress)

Display panel with: Name, Current ruler, Founded on, Language, Religion, Description
Data should change dynamically based on selected date.

**UI Design:**
- Side panel slides in from right, dark theme matching map
- Layout (top to bottom):
  - Header: Nation flag/standard + nation name (hyperlinked to Wikipedia) + current year
  - Ruler section: Circular portrait + title + ruler name (hyperlinked to Wikipedia) + reign dates
  - Info grid: 2x2 layout with Founded, Capital, Language, Religion
  - Description: Scrollable text area
  - Footer: "Data changes with time slider"
- Prototype: See `NationPanel.jsx` in chat history

**Database Changes:**
- ✅ Table rename: `controllers` → `nations` (done)
- ✅ C# model rename: `Empire` → `Nation`, `EmpireId` → `NationId` (done)
- ✅ Territories reference nations via `nation_id`, don't store color directly (done)
- New table: `nation_snapshots` for time-varying data (pending)

```sql
-- nations table (static metadata)
nations: id, name, display_name, color, founded_year, wiki_url, description, flag_url

-- nation_snapshots table (time-varying data)
nation_snapshots: id, nation_id, start_year, end_year, ruler_name, ruler_title, ruler_wiki_url, ruler_portrait_url, capital, language, religion
```

**Dynamic Data Pattern:**
```sql
-- API filters by slider year (same pattern as cumulative_territories)
SELECT * FROM nation_snapshots
WHERE nation_id = :nationId
  AND start_year <= :sliderYear
  AND end_year >= :sliderYear
```

**Data Sourcing Strategy:**
- **Source:** Wikidata via SPARQL queries (one-time import, not runtime)
- **Why not live queries:** Latency (500ms-2s vs <50ms), reliability, rate limits, curation needs
- **Import script:** Query Wikidata for nations + rulers + reign dates + wiki URLs, insert into DB
- **About section:** Pull Wikipedia article intro (first paragraph), store in `nations.description`. Not time-varying for V1 — users can click wiki link for full context.
- **Manual curation:** Review imported data, fill gaps, add flag/portrait assets

**Nations for V1:** Rome only (existing data). Adding more nations (Carthage, Ptolemaic Egypt, etc.) is a separate issue.

**Asset Storage (flags, portraits):**
- **Store locally**, not Wikimedia hotlinks (they discourage/block hotlinking, URLs can change, latency)
- Scale is small: ~15 flags + ~75-150 portraits ≈ 50MB total
- Workflow:
  1. During Wikidata import, grab Wikimedia image URL
  2. Download image to `/data/assets/flags/` and `/data/assets/portraits/`
  3. Store local path in DB (`flag_url: /assets/flags/rome.png`)
  4. Serve via API static file endpoint or separate static hosting
- Fallback: Use placeholder silhouettes for missing portraits

**New API Endpoint:**
- `GET /api/nations/{nationId}?year={sliderYear}` - Returns nation + current ruler snapshot for given year

## Future Scaling Notes
- Data files kept separate (auto-downloaded by import scripts, cached locally, not committed)
- `data/README.md` documents data sources
- Goal: One contiguous world timeline, not separate scenarios

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

# Import data (auto-downloads if not cached)
pip install psycopg2-binary
python db/scripts/import_territories.py   # Downloads Roman Empire data automatically
python db/scripts/import_basemap.py       # Downloads Natural Earth land data automatically

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
