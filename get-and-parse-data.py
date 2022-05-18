# %%
import requests 
import geopandas as gpd
import pandas as pd
import fiona
import subprocess
import os
from glob import glob
import wget
# %%

# All US states currnetly included in geofabrik's OSM extracts
states = [
    {"state":"Alabama", "fips":"01"},
    {"state":"Alaska", "fips":"02"},
    {"state":"Arizona", "fips":"04"},
    {"state":"Arkansas", "fips":"05"},
    {"state":"California", "fips":"06"},
    {"state":"Colorado", "fips":"08"},
    {"state":"Connecticut", "fips":"09"},
    {"state":"Delaware", "fips":"10"},
    {"state":"District of Columbia", "fips":"11"},
    {"state":"Florida", "fips":"12"},
    {"state":"Georgia", "fips":"13"},
    {"state":"Hawaii", "fips":"15"},
    {"state":"Idaho", "fips":"16"},
    {"state":"Illinois", "fips":"17"},
    {"state":"Indiana", "fips":"18"},
    {"state":"Iowa", "fips":"19"},
    {"state":"Kansas", "fips":"20"},
    {"state":"Kentucky", "fips":"21"},
    {"state":"Louisiana", "fips":"22"},
    {"state":"Maine", "fips":"23"},
    {"state":"Maryland", "fips":"24"},
    {"state":"Massachusetts", "fips":"25"},
    {"state":"Michigan", "fips":"26"},
    {"state":"Minnesota", "fips":"27"},
    {"state":"Mississippi", "fips":"28"},
    {"state":"Missouri", "fips":"29"},
    {"state":"Montana", "fips":"30"},
    {"state":"Nebraska", "fips":"31"},
    {"state":"Nevada", "fips":"32"},
    {"state":"New Hampshire", "fips":"33"},
    {"state":"New Jersey", "fips":"34"},
    {"state":"New Mexico", "fips":"35"},
    {"state":"New York", "fips":"36"},
    {"state":"North Carolina", "fips":"37"},
    {"state":"North Dakota", "fips":"38"},
    {"state":"Ohio", "fips":"39"},
    {"state":"Oklahoma", "fips":"40"},
    {"state":"Oregon", "fips":"41"},
    {"state":"Pennsylvania", "fips":"42"},
    {"state":"Puerto Rico", "fips":"72"},
    {"state":"Rhode Island", "fips":"44"},
    {"state":"South Carolina", "fips":"45"},
    {"state":"South Dakota", "fips":"46"},
    {"state":"Tennessee", "fips":"47"},
    {"state":"Texas", "fips":"48"},
    {"state":"US Virgin Islands", "fips":"78"},
    {"state":"Utah", "fips":"49"},
    {"state":"Vermont", "fips":"50"},
    {"state":"Virginia", "fips":"51"},
    {"state":"Washington", "fips":"53"},
    {"state":"West Virginia", "fips":"54"},
    {"state":"Wisconsin", "fips":"55"},
    {"state":"Wyoming", "fips":"56"}
]

# Format state name for use in URL
def clean_state(state):
    return state.replace(" ", "-").lower()

# Helper function for cleaned state name to URL
def get_url(state):
    return f"http://download.geofabrik.de/north-america/us/{state}-latest.osm.pbf"

# Download data
def get_state_data(state):
    # Fetch the data from geofabric's OSM extracts
    url = get_url(clean_state(state))
    print(f"Fetching data for {state}: {url}")
    filename = wget.download(url)
    return filename

# Extract osm query
def extract_data(state):
    command = f'''osmium tags-filter -o {state}_green.osm.pbf {state}-latest.osm.pbf \
        natural=wood \        
        leisure=nature_reserve \
        landuse=recreation_ground \
        landuse=grass \
        landuse=forest \
        landuse=cemetery \
        leisure=garden'''
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

# convert to gpkg
def convert_data(state):
    command = f'''ogr2ogr -f GPKG {state}.gpkg {state}_green.osm.pbf'''
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

# buffer to correct bad geoms, the dissolve
def dissolve_data(state):
    layers = []
    for layername in fiona.listlayers(f'./{state}.gpkg'):
        with fiona.open(f'./{state}.gpkg', layer=layername) as src:
            if 'polygon' in layername:
                layers.append(layername)
    gdf = pd.concat([gpd.read_file(f'./{state}.gpkg', driver="GPKG", layer=layername) for layername in layers]).reset_index()
    gdf['dissolve_on'] = True
    gdf['geometry'] = gdf['geometry'].buffer(0)
    gdf = gdf.dissolve(by='dissolve_on')
    gdf.to_file(f"{state}_dissolved.gpkg", driver="GPKG")


# finall all relevant files, dissolve
def combine_all_states():
    all_files = glob("./*_dissolved.gpkg")
    gdfs = pd.concat([gpd.read_file(file, driver="GPKG") for file in all_files])
    gdfs['dissolve_on'] = True
    return gdfs.dissolve(by='dissolve_on')

# remove stale files
def clean_up(state, filename):
    os.remove(f"./{state}-latest.osm.pbf")
    os.remove(f"./{state}_green.osm.pbf")
    os.remove(f"./{state}.gpkg")

def clean_up_all_states():
    for state in states:
        clean_up(state.state)
# %%
if __name__ == "__main__":
    for idx, stateInfo in enumerate(states):
        state = clean_state(stateInfo["state"])
        print(f"{idx}/{len(states)}: {state}")

        filename = get_state_data(state)
        print(f"Downloaded {state}")

        extract_data(state)
        print(f"{state} extracted")

        convert_data(state)
        print(f"{state} converted")

        dissolve_data(state)
        print(f"{state} dissolved")

        # clean_up(state, filename)

    # full_gdf = combine_all_states()
    # full_gdf.to_file("all_states_dissolved.gpkg", driver="GPKG")