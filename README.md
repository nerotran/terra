# Terra - Historical Map Visualization

Interactive map showing territorial changes through history. Drag a time slider, watch borders evolve.

Currently features the Roman Republic and Empire (500 BC - 117 AD) with dynamic ruler information. Click on a territory to see details about the nation and its current ruler for that time period.

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Configure environment
cp .env.example .env

# Start database and import all data
docker-compose up -d
docker compose --profile import up

# Start API
cd api/Terra.Api && dotnet run

# Start frontend (in another terminal)
cd web && npm install && npm run dev
```

### Option 2: Manual Setup

```bash
# 1. Configure environment
cp .env.example .env

# 2. Start database
docker-compose up -d

# 3. Install Python dependencies
pip install psycopg2-binary

# 4. Import data (scripts auto-download from sources)
python db/scripts/import_basemap.py
python db/scripts/import_territories.py
python db/scripts/import_nation_snapshots.py

# 5. Start API (http://localhost:5025)
cd api/Terra.Api && dotnet run

# 6. Start frontend (http://localhost:5173)
cd web && npm install && npm run dev
```

## Features

- **Time Slider**: Drag to see territorial changes across centuries
- **Interactive Map**: Hover to highlight territories, click for details
- **Nation Panel**: Shows ruler, capital, language, religion for selected time period
- **Dynamic Data**: Rulers change based on selected year (fetched from Wikidata)

## Project Structure

```
terra/
├── docker-compose.yml      # PostgreSQL + PostGIS + Importer
├── terra.sln               # .NET solution file
├── db/
│   ├── init.sql            # Database schema
│   └── scripts/
│       ├── import_basemap.py           # Natural Earth land data
│       ├── import_territories.py       # Territory boundaries
│       ├── import_nation_snapshots.py  # Rulers from Wikidata
│       └── verify_db.sh
├── api/                    # .NET Core 8 Web API
├── web/                    # React + TypeScript + Vite + D3.js
├── logs/                   # Import script logs (gitignored)
└── data/                   # Downloaded data & assets (gitignored)
    └── assets/portraits/   # Ruler portrait images
```

## Tech Stack

- **Database:** PostgreSQL 16 + PostGIS 3.4
- **API:** .NET Core 8 Web API + Entity Framework + NetTopologySuite
- **Frontend:** React 19 + TypeScript + Vite + D3.js

## Data Sources

| Data | Source | License |
|------|--------|---------|
| Roman territories | [siriusbontea/roman-empire](https://github.com/siriusbontea/roman-empire) | BSD |
| Land geography | [Natural Earth](https://www.naturalearthdata.com/) | Public Domain |
| Rulers | [Wikidata](https://www.wikidata.org/) (consuls Q40779, emperors Q842606) | CC0 |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/territories` | All cumulative territories |
| `GET /api/snapshots` | All time periods |
| `GET /api/nations/{id}/snapshot/{snapshotId}` | Nation details with ruler |
| `GET /api/basemap` | Land geography |

## Development

```bash
# Verify database
./db/scripts/verify_db.sh

# Build frontend
cd web && npm run build

# Lint frontend
cd web && npm run lint
```

## License

MIT
