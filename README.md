# Terra - Historical Map Visualization

Interactive map showing territorial changes through history. Drag a time slider, watch borders evolve.

## Quick Start

### 1. Start Database
```bash
docker-compose up -d
```

### 2. Download Data
```bash
curl -L "https://raw.githubusercontent.com/siriusbontea/roman-empire/main/data/CombinedExtentLayers_v6.topojson" \
  -o data/roman-empire.topojson
```

### 3. Import
```bash
pip install psycopg2-binary
python db/scripts/import_territories.py data/roman-empire.topojson
```

### 4. Verify
```bash
./db/scripts/verify_db.sh
```

## Project Structure

```
terra/
├── docker-compose.yml      # PostgreSQL + PostGIS
├── db/
│   ├── init.sql            # Schema
│   └── scripts/
│       ├── import_territories.py
│       └── verify_db.sh
├── api/                    # .NET Core 8 Web API
├── web/                    # React + TypeScript + Vite
└── data/                   # GeoJSON/TopoJSON (not committed)
```

## Stack

- **Database:** PostgreSQL 16 + PostGIS 3.4
- **API:** .NET Core 8 Web API
- **Frontend:** React + TypeScript + Vite + D3.js

## Current Data

| Scenario | Time Range | Source |
|----------|------------|--------|
| Roman Empire | 500 BC - 117 AD | [siriusbontea/roman-empire](https://github.com/siriusbontea/roman-empire) |

## License

MIT
