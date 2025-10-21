import geopandas as gpd
import pandas as pd
import os
import json
from shapely.geometry import mapping

# Paths
geojson_path = os.path.join('VTDs', 'tl_2020_29_vtd20', 'tl_2020_29_vtd20.geojson')
data_dir = 'Data'
output_path = os.path.join('VTDs', 'tl_2020_29_vtd20', 'tl_2020_29_vtd20_joined_all_years.json')

# Load GeoJSON
gdf = gpd.read_file(geojson_path)

# Prepare a dict to collect results by year/contest
year_results = {}

# List all relevant CSVs
csv_files = [f for f in os.listdir(data_dir) if f.endswith('__precinct.csv') or f.endswith('__county.csv')]

for csv_file in csv_files:
    csv_path = os.path.join(data_dir, csv_file)
    df = pd.read_csv(csv_path, dtype=str)
    # Filter for statewide/federal offices only, but INCLUDE US Senate
    exclude_keywords = ['House', 'State Senate', 'State House']
    # Keep rows where office does NOT contain exclude_keywords OR contains 'Senate' but is 'US Senate'
    mask = ~df['office'].str.contains('|'.join(exclude_keywords), case=False, na=False) | df['office'].str.contains('US Senate', case=False, na=False)
    df_filtered = df[mask] if 'office' in df.columns else df
    # Get year from filename
    year = csv_file.split('__')[0]
    # Group by precinct_code/county and office, aggregate votes by candidate
    if 'precinct_code' in df_filtered.columns:
        grs = ['precinct_code', 'office', 'candidate', 'party']
    elif 'county' in df_filtered.columns:
        group_keys = ['county', 'office', 'candidate', 'party']
    else:
        continue
    grouped = df_filtered.groupby(group_keys, as_index=False)['votes'].sum()
    year_results[year] = grouped

# Merge all years' results into GeoJSON
features = []
for idx, row in gdf.iterrows():
    props = row.to_dict()
    precinct_code = props.get('VTDST20')
    county_name = props.get('COUNTYFP20')
    precinct_data = {}
    for year, df in year_results.items():
        # Get all contests for this precinct or county
        if 'precinct_code' in df.columns:
            contests = df[df['precinct_code'] == precinct_code]
        elif 'county' in df.columns:
            contests = df[df['county'] == county_name]
        else:
            contests = pd.DataFrame()
        office_dict = {}
        for office in contests['office'].unique():
            office_df = contests[contests['office'] == office]
            # Sum votes by party
            dem_mask = office_df['party'].str.upper().str.startswith('DEM')
            rep_mask = office_df['party'].str.upper().str.startswith('REP')
            dem_votes = office_df[dem_mask]['votes'].astype(float).sum()
            rep_votes = office_df[rep_mask]['votes'].astype(float).sum()
            other_votes = office_df[~(dem_mask | rep_mask)]['votes'].astype(float).sum()
            total_votes = dem_votes + rep_votes + other_votes
            two_party_total = dem_votes + rep_votes
            margin = abs(rep_votes - dem_votes)
            if two_party_total > 0:
                margin_pct = round(margin / two_party_total * 100, 2)
                margin_pct_str = f"{margin_pct:.2f}"
            else:
                margin_pct = None
                margin_pct_str = None
            winner = 'REP' if rep_votes > dem_votes else ('DEM' if dem_votes > rep_votes else 'TIE')
            # Get DEM and REP candidate names (first listed for each)
            dem_candidate = office_df[dem_mask]['candidate'].iloc[0] if dem_mask.any() else None
            rep_candidate = office_df[rep_mask]['candidate'].iloc[0] if rep_mask.any() else None
            # Competitiveness categorization
            def get_competitiveness(margin_pct, winner):
                if margin_pct is None:
                    return None
                if winner == 'REP':
                    if margin_pct >= 40:
                        return {"category": "Annihilation", "party": "Republican", "code": "R_ANNIHILATION", "color": "#67000d"}
                    elif margin_pct >= 30:
                        return {"category": "Dominant", "party": "Republican", "code": "R_DOMINANT", "color": "#a50f15"}
                    elif margin_pct >= 20:
                        return {"category": "Stronghold", "party": "Republican", "code": "R_STRONGHOLD", "color": "#cb181d"}
                    elif margin_pct >= 10:
                        return {"category": "Safe", "party": "Republican", "code": "R_SAFE", "color": "#ef3b2c"}
                    elif margin_pct >= 5.5:
                        return {"category": "Likely", "party": "Republican", "code": "R_LIKELY", "color": "#fb6a4a"}
                    elif margin_pct >= 1:
                        return {"category": "Lean", "party": "Republican", "code": "R_LEAN", "color": "#fcae91"}
                    elif margin_pct >= 0.5:
                        return {"category": "Tilt", "party": "Republican", "code": "R_TILT", "color": "#fee8c8"}
                elif winner == 'DEM':
                    if margin_pct >= 40:
                        return {"category": "Annihilation", "party": "Democratic", "code": "D_ANNIHILATION", "color": "#08306b"}
                    elif margin_pct >= 30:
                        return {"category": "Dominant", "party": "Democratic", "code": "D_DOMINANT", "color": "#08519c"}
                    elif margin_pct >= 20:
                        return {"category": "Stronghold", "party": "Democratic", "code": "D_STRONGHOLD", "color": "#3182bd"}
                    elif margin_pct >= 10:
                        return {"category": "Safe", "party": "Democratic", "code": "D_SAFE", "color": "#6baed6"}
                    elif margin_pct >= 5.5:
                        return {"category": "Likely", "party": "Democratic", "code": "D_LIKELY", "color": "#9ecae1"}
                    elif margin_pct >= 1:
                        return {"category": "Lean", "party": "Democratic", "code": "D_LEAN", "color": "#c6dbef"}
                    elif margin_pct >= 0.5:
                        return {"category": "Tilt", "party": "Democratic", "code": "D_TILT", "color": "#e1f5fe"}
                if margin_pct < 0.5:
                    return {"category": "Tossup", "party": "Tossup", "code": "TOSSUP", "color": "#f7f7f7"}
                return None
            competitiveness = get_competitiveness(margin_pct, winner)
            # Structure output
            # Ensure all results are serializable
            results_list = []
            for r in office_df[['candidate', 'party', 'votes']].to_dict('records'):
                results_list.append({
                    "candidate": str(r["candidate"]),
                    "party": str(r["party"]),
                    "votes": int(float(r["votes"])) if r["votes"] is not None and r["votes"] != '' else 0
                })
            office_dict[office] = {
                "results": results_list,
                "dem_candidate": str(dem_candidate) if dem_candidate is not None else None,
                "rep_candidate": str(rep_candidate) if rep_candidate is not None else None,
                "dem_votes": int(dem_votes),
                "rep_votes": int(rep_votes),
                "other_votes": int(other_votes),
                "total_votes": int(total_votes),
                "two_party_total": int(two_party_total),
                "margin": int(margin) if margin is not None else None,
                "margin_pct": margin_pct_str,
                "winner": str(winner),
                "competitiveness": competitiveness
            }
        if office_dict:
            precinct_data[year] = office_dict
    props['election_results'] = precinct_data
    # Remove geometry from props to avoid serialization error
    if 'geometry' in props:
        del props['geometry']
    feature = {
        'type': 'Feature',
        'geometry': row['geometry'].__geo_interface__,
        'properties': props
    }
    features.append(feature)

geojson_dict = {
    'type': 'FeatureCollection',
    'features': features
}

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(geojson_dict, f, ensure_ascii=False, indent=2)

print(f"Joined JSON created: {output_path}")
