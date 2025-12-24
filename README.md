# Terra - Historical Map Visualization

Interactive map showing territorial changes through history. Drag a time slider, watch borders evolve.

## Quick Start

### 1. Configure Environment
```bash
cp .env.example .env
# Edit .env if needed (defaults work for local development)
```

### 2. Start Database
```bash
docker-compose up -d
```

### 3. Download Data
```bash
curl -L "https://raw.githubusercontent.com/siriusbontea/roman-empire/main/data/CombinedExtentLayers_v6.topojson" \
  -o data/roman-empire.topojson
```

### 4. Import Data
```bash
pip install psycopg2-binary
python db/scripts/import_territories.py data/roman-empire.topojson
python db/scripts/import_basemap.py
```

### 5. Start API
```bash
cd api/Terra.Api
dotnet run
```
API runs at http://localhost:5000

### 6. Start Frontend
```bash
cd web
npm install
npm run dev
```
Frontend runs at http://localhost:5173

### 7. Verify (Optional)
```bash
./db/scripts/verify_db.sh
```

## Project Structure

```
terra/
├── .env.example            # Environment variables template
├── docker-compose.yml      # PostgreSQL + PostGIS
├── terra.sln               # .NET solution file
├── db/
│   ├── init.sql            # Schema
│   └── scripts/
│       ├── import_territories.py
│       ├── import_basemap.py
│       └── verify_db.sh
├── api/                    # .NET Core 8 Web API
├── web/                    # React + TypeScript + Vite + D3.js
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
