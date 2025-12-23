# Data Sources

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

## Adding New Scenarios

Future data sources will be documented here.
