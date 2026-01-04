"""
Color Correction Script for Missouri Election Data
Ensures all races have correctly assigned colors based on winner and margin
"""

import json

# Load the aggregated results
with open('Data/mo_county_aggregated_results.json', 'r') as f:
    data = json.load(f)

def get_correct_color(margin, winner_party):
    """
    Calculate the correct color based on margin and winner
    Returns color hex code
    """
    abs_margin = abs(margin)
    
    # Republican colors (red scale)
    rep_colors = {
        'Annihilation': '#67000d',    # R+40%+
        'Dominant': '#a50f15',        # R+30-40%
        'Stronghold': '#cb181d',      # R+20-30%
        'Safe': '#ef3b2c',            # R+10-20%
        'Likely': '#fb6a4a',          # R+5.5-10%
        'Lean': '#fc9272',            # R+1-5.49%
        'Tilt': '#fcbba1',            # R+0.5-0.99%
        'Tossup': '#fee5d9'           # R+0-0.49%
    }
    
    # Democratic colors (blue scale)
    dem_colors = {
        'Annihilation': '#08306b',    # D+40%+
        'Dominant': '#08519c',        # D+30-40%
        'Stronghold': '#2171b5',      # D+20-30%
        'Safe': '#4292c6',            # D+10-20%
        'Likely': '#6baed6',          # D+5.5-10%
        'Lean': '#9ecae1',            # D+1-5.49%
        'Tilt': '#c6dbef',            # D+0.5-0.99%
        'Tossup': '#deebf7'           # D+0-0.49%
    }
    
    # Determine category based on margin
    if abs_margin >= 40:
        category = 'Annihilation'
    elif abs_margin >= 30:
        category = 'Dominant'
    elif abs_margin >= 20:
        category = 'Stronghold'
    elif abs_margin >= 10:
        category = 'Safe'
    elif abs_margin >= 5.5:
        category = 'Likely'
    elif abs_margin >= 1:
        category = 'Lean'
    elif abs_margin >= 0.5:
        category = 'Tilt'
    else:
        category = 'Tossup'
    
    # Return appropriate color based on winner
    if winner_party == 'REP':
        return rep_colors[category]
    else:  # DEM
        return dem_colors[category]

def get_competitiveness_label(margin):
    """Get the competitiveness category label"""
    abs_margin = abs(margin)
    
    if abs_margin >= 40:
        return 'Annihilation'
    elif abs_margin >= 30:
        return 'Dominant'
    elif abs_margin >= 20:
        return 'Stronghold'
    elif abs_margin >= 10:
        return 'Safe'
    elif abs_margin >= 5.5:
        return 'Likely'
    elif abs_margin >= 1:
        return 'Lean'
    elif abs_margin >= 0.5:
        return 'Tilt'
    else:
        return 'Tossup'

# Track corrections
corrections_made = 0
races_checked = 0

# Process all races in the results_by_year structure
if 'results_by_year' in data:
    for year, year_data in data['results_by_year'].items():
        for contest_name, contest_data in year_data.items():
            if not isinstance(contest_data, dict):
                continue
            
            for county_name, county_data in contest_data.items():
                if not isinstance(county_data, dict):
                    continue
                    
                races_checked += 1
                
                # Get the margin and winner
                margin_pct = county_data.get('margin_pct', '0')
                try:
                    margin = float(margin_pct) if isinstance(margin_pct, (int, float)) else float(str(margin_pct).replace('%', ''))
                except:
                    margin = 0
                
                winner = county_data.get('winner', '')
                
                # Determine winner party
                if winner == 'REP' or winner.endswith('(REP)') or winner.endswith('(R)'):
                    winner_party = 'REP'
                elif winner == 'DEM' or winner.endswith('(DEM)') or winner.endswith('(D)'):
                    winner_party = 'DEM'
                else:
                    # Try to infer from margin sign
                    if margin > 0:
                        winner_party = 'REP'
                    else:
                        winner_party = 'DEM'
                        margin = abs(margin)
                
                # Calculate correct color
                correct_color = get_correct_color(abs(margin), winner_party)
                
                # Update competitiveness object if it exists
                if 'competitiveness' in county_data and isinstance(county_data['competitiveness'], dict):
                    current_color = county_data['competitiveness'].get('color', '')
                    
                    # Update if different
                    if current_color != correct_color:
                        county_data['competitiveness']['color'] = correct_color
                        corrections_made += 1
                    
                    # Also ensure competitiveness label is correct
                    correct_label = get_competitiveness_label(abs(margin))
                    current_label = county_data['competitiveness'].get('category', '')
                    
                    if current_label != correct_label:
                        county_data['competitiveness']['category'] = correct_label
                        corrections_made += 1

print(f"Checked {races_checked} county race results")
print(f"Made {corrections_made} corrections")

# Save corrected data
with open('Data/mo_county_aggregated_results.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"✓ Saved corrected data to Data/mo_county_aggregated_results.json")
