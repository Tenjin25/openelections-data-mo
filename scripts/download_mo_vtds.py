import os
import requests
import zipfile
import geopandas as gpd
import pandas as pd

# FIPS to county name mapping for Missouri (from Census TIGER/Line 2008)
# Format: '29001': 'Adair_County', ...
county_fips_names = {
    '29001': 'Adair_County', '29003': 'Andrew_County', '29005': 'Atchison_County', '29007': 'Audrain_County',
    '29009': 'Barry_County', '29011': 'Barton_County', '29013': 'Bates_County', '29015': 'Benton_County',
    '29017': 'Bollinger_County', '29019': 'Boone_County', '29021': 'Buchanan_County', '29023': 'Butler_County',
    '29025': 'Caldwell_County', '29027': 'Callaway_County', '29029': 'Camden_County', '29031': 'Cape_Girardeau_County',
    '29033': 'Carroll_County', '29035': 'Carter_County', '29037': 'Cass_County', '29039': 'Cedar_County',
    '29041': 'Chariton_County', '29043': 'Christian_County', '29045': 'Clark_County', '29047': 'Clay_County',
    '29049': 'Clinton_County', '29051': 'Cole_County', '29053': 'Cooper_County', '29055': 'Crawford_County',
    '29057': 'Dade_County', '29059': 'Dallas_County', '29061': 'Daviess_County', '29063': 'De_Kalb_County',
    '29065': 'Dent_County', '29067': 'Douglas_County', '29069': 'Dunklin_County', '29071': 'Franklin_County',
    '29073': 'Gasconade_County', '29075': 'Gentry_County', '29077': 'Greene_County', '29079': 'Grundy_County',
    '29081': 'Harrison_County', '29083': 'Henry_County', '29085': 'Hickory_County', '29087': 'Holt_County',
    '29089': 'Howard_County', '29091': 'Howell_County', '29093': 'Iron_County', '29095': 'Jackson_County',
    '29097': 'Jasper_County', '29099': 'Jefferson_County', '29101': 'Johnson_County', '29103': 'Knox_County',
    '29105': 'Laclede_County', '29107': 'Lafayette_County', '29109': 'Lawrence_County', '29111': 'Lewis_County',
    '29113': 'Lincoln_County', '29115': 'Linn_County', '29117': 'Livingston_County', '29119': 'McDonald_County',
    '29121': 'Macon_County', '29123': 'Madison_County', '29125': 'Maries_County', '29127': 'Marion_County',
    '29129': 'Mercer_County', '29131': 'Miller_County', '29133': 'Mississippi_County', '29135': 'Moniteau_County',
    '29137': 'Monroe_County', '29139': 'Montgomery_County', '29141': 'Morgan_County', '29143': 'New_Madrid_County',
    '29145': 'Newton_County', '29147': 'Nodaway_County', '29149': 'Oregon_County', '29151': 'Osage_County',
    '29153': 'Ozark_County', '29155': 'Pemiscot_County', '29157': 'Perry_County', '29159': 'Pettis_County',
    '29161': 'Phelps_County', '29163': 'Pike_County', '29165': 'Platte_County', '29167': 'Polk_County',
    '29169': 'Pulaski_County', '29171': 'Putnam_County', '29173': 'Ralls_County', '29175': 'Randolph_County',
    '29177': 'Ray_County', '29179': 'Reynolds_County', '29181': 'Ripley_County', '29183': 'St._Charles_County',
    '29185': 'St._Clair_County', '29186': 'Ste._Genevieve_County', '29187': 'St._Francois_County', '29189': 'St._Louis_County',
    '29195': 'Saline_County', '29197': 'Schuyler_County', '29199': 'Scotland_County', '29201': 'Scott_County',
    '29203': 'Shannon_County', '29205': 'Shelby_County', '29207': 'Stoddard_County', '29209': 'Stone_County',
    '29211': 'Sullivan_County', '29213': 'Taney_County', '29215': 'Texas_County', '29217': 'Vernon_County',
    '29219': 'Warren_County', '29221': 'Washington_County', '29223': 'Wayne_County', '29225': 'Webster_County',
    '29227': 'Worth_County', '29229': 'Wright_County'
}

base_url = "https://www2.census.gov/geo/tiger/TIGER2008/29_MISSOURI"
output_dir = "MO_VTDs"
merged_geojson = os.path.join(output_dir, "MO_VTDs_merged.geojson")

os.makedirs(output_dir, exist_ok=True)

all_gdfs = []

for fips, county_name in county_fips_names.items():
    county_folder = f"{fips}_{county_name}"
    zip_url = f"{base_url}/{county_folder}/tl_2008_{fips}_vtd00.zip"
    zip_path = os.path.join(output_dir, f"tl_2008_{fips}_vtd00.zip")
    extract_path = os.path.join(output_dir, fips)
    print(f"Downloading {zip_url} ...")
    try:
        r = requests.get(zip_url)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            f.write(r.content)
        print(f"Extracting {zip_path} ...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
        os.remove(zip_path)
        # Find the shapefile in the extracted folder
        shp_files = [f for f in os.listdir(extract_path) if f.endswith('.shp')]
        if shp_files:
            shp_path = os.path.join(extract_path, shp_files[0])
            gdf = gpd.read_file(shp_path)
            all_gdfs.append(gdf)
    except Exception as e:
        print(f"Failed for {fips}: {e}")

# Merge all county GeoDataFrames and save as one GeoJSON
if all_gdfs:
    print("Merging all counties into one GeoJSON...")
    merged = gpd.GeoDataFrame(pd.concat(all_gdfs, ignore_index=True), crs=all_gdfs[0].crs)
    merged.to_file(merged_geojson, driver="GeoJSON")
    print(f"Merged GeoJSON saved to {merged_geojson}")
else:
    print("No shapefiles were successfully downloaded and read.")

print("All done!")
