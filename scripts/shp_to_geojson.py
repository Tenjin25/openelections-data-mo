
import geopandas as gpd
import sys

def main():
	if len(sys.argv) != 3:
		print("Usage: python shp_to_geojson.py <input_shp> <output_geojson>")
		sys.exit(1)
	shp_path = sys.argv[1]
	geojson_path = sys.argv[2]
	gdf = gpd.read_file(shp_path)
	gdf.to_file(geojson_path, driver='GeoJSON')
	print(f"GeoJSON created: {geojson_path}")

if __name__ == "__main__":
	main()
