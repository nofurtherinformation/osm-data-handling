import geopandas as gpd
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool

states = gpd.read_file("https://raw.githubusercontent.com/GeoDaCenter/covid/master/public/geojson/state_usafacts.geojson")[["GEOID","NAME"]]
states["NAME"] = states["NAME"].str.replace(' ', '-').str.lower()
state_dict = states.to_dict(orient="Records")

# format of the state dict
state_dict[0]

counties = gpd.read_file('./counties/cb_2018_us_county_500k.shp')
counties = counties.to_crs("EPSG:5070")

def main():
    results = []
    counter = 1
    for state in state_dict:
        print(f"Parsing {state['NAME']} ({(counter/len(state_dict))*100}%)...")
        county_data = counties[counties.STATEFP == state['GEOID']]
        try:
            state_data = gpd.read_file(f"./{state['NAME']}_dissolved.gpkg").to_crs("EPSG:5070")
            for i in tqdm(range(0, len(county_data))):
                results.append({
                    'GEOID': county_data.iloc[i].GEOID,
                    'area': gpd.clip(state_data, county_data.iloc[i].geometry).area.sum()
                })
        except:
            print('could not find file')
        counter += 1
            
    pd.DataFrame(results).to_csv('./area_results.csv', index=False)

if __name__ == "__main__":
    main()