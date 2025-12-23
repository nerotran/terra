#!/bin/bash
# Verify Terra database setup

echo "=== Project Terra - Database Check ==="

# Check container
if ! docker ps | grep -q terra-db; then
    echo "✗ terra-db not running. Run: docker-compose up -d"
    exit 1
fi
echo "✓ Container running"

# Check PostGIS
POSTGIS=$(docker exec terra-db psql -U terra -d terra -tAc "SELECT PostGIS_Version();" 2>/dev/null)
echo "✓ PostGIS: $POSTGIS"

# Check snapshots
SNAPSHOTS=$(docker exec terra-db psql -U terra -d terra -tAc "SELECT COUNT(*) FROM time_snapshots;")
echo "✓ Time periods: $SNAPSHOTS"

# Check territories per period
echo ""
echo "Territories by period (chronological):"
docker exec terra-db psql -U terra -d terra -c \
    "SELECT ts.year, ts.era, ts.label, COUNT(t.id) as count 
     FROM time_snapshots ts 
     LEFT JOIN territories t ON t.snapshot_id = ts.id 
     GROUP BY ts.id ORDER BY ts.sort_year;"

echo ""
echo "Cumulative territories (area in km²):"
docker exec terra-db psql -U terra -d terra -c \
    "SELECT year, era, label, ROUND(ST_Area(geometry::geography)/1000000) as area_km2
     FROM cumulative_territories
     ORDER BY sort_year;"

echo "=== Done ==="
