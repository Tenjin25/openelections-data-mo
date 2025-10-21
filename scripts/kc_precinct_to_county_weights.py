import json
from collections import defaultdict
from shapely.geometry import shape
import pandas as pd

# Path to the merged VTDs GeoJSON
GEOJSON_PATH = 'MO_VTDs/MO_VTDs_merged.geojson'
# Path to a precinct-level election results CSV (example year)
PRECINCT_CSV_PATH = 'Data/20201103__mo__general__precinct.csv'

# Load GeoJSON
with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
    geojson = json.load(f)

# Build a mapping: precinct name/id -> county FIPS
precinct_to_county = {}
for feature in geojson['features']:
    props = feature['properties']
    # Use VTD name or ID as the precinct key
    precinct_key = props.get('NAME00') or props.get('VTDIDFP00')
    county_fips = props.get('COUNTYFP00')
    if precinct_key and county_fips:
        precinct_to_county[precinct_key.strip().upper()] = county_fips

# Load the precinct-level results
results_df = pd.read_csv(PRECINCT_CSV_PATH, dtype=str)


# Filter for Kansas City pseudo-county, handling missing values
results_df = results_df[results_df['county'].notna()]
kc_mask = results_df['county'].str.upper().str.contains('KANSAS CITY')
kc_precincts = results_df[kc_mask]

# Count precincts per county (Jackson, Clay, Platte, Cass)
county_precinct_counts = defaultdict(int)
county_precinct_votes = defaultdict(float)

for _, row in kc_precincts.iterrows():
    precinct = row['precinct'].strip().upper() if 'precinct' in row and pd.notna(row['precinct']) else None
    votes = float(row['votes']) if 'votes' in row and pd.notna(row['votes']) else 0
    county_fips = precinct_to_county.get(precinct)
    if county_fips in ['095', '047', '165', '037']:
        county_precinct_counts[county_fips] += 1
        county_precinct_votes[county_fips] += votes

# Calculate weights by precinct count and by total votes
precinct_total = sum(county_precinct_counts.values())
votes_total = sum(county_precinct_votes.values())

print('Kansas City precincts by county FIPS:')
for fips, count in county_precinct_counts.items():
    print(f'  County FIPS {fips}: {count} precincts, {county_precinct_votes[fips]:.0f} votes')

print('\nWeighted split (by precinct count):')
for fips, count in county_precinct_counts.items():
    print(f'  County FIPS {fips}: {count/precinct_total:.2%}')

print('\nWeighted split (by votes):')
for fips, votes in county_precinct_votes.items():
    print(f'  County FIPS {fips}: {votes/votes_total:.2%}')

# You can now use these weights to split Kansas City results in your aggregation script.
