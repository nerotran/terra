# Data Sources

Terra is a historical mapping project that will cover all countries and civilizations throughout human history. The current implementation starts with the Roman Empire, but the architecture is designed to support any historical territory data.

Geographic data is not committed to this repo. Download before running imports.

## Roman Empire (500 BC - 117 AD)

**Source:** [siriusbontea/roman-empire](https://github.com/siriusbontea/roman-empire)  
**License:** BSD-3

```bash
curl -L "https://raw.githubusercontent.com/siriusbontea/roman-empire/main/data/CombinedExtentLayers_v6.topojson" \
  -o data/roman-empire.topojson
```

Then import:
```bash
python db/scripts/import_territories.py data/roman-empire.topojson
```

## Adding New Data Sources

Future data sources (e.g., ancient civilizations, medieval kingdoms, colonial empires, modern nation-states) will be documented here as they are added.
