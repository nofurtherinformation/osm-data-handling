# %%
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool

states = gpd.read_file("https://raw.githubusercontent.com/GeoDaCenter/covid/master/public/geojson/state_usafacts.geojson")[["GEOID","NAME"]]
states["NAME"] = states["NAME"].str.replace(' ', '-').str.lower()
state_dict = states.to_dict(orient="Records")
counties = gpd.read_file('./counties/cb_2018_us_county_500k.shp')
counties = counties.to_crs("EPSG:5070")


def clip_counties(index):
    state = state_dict[index]
    county_data = counties[counties.STATEFP == state['GEOID']]
    results = []
    try:
        state_data = gpd.read_file(f"./{state['NAME']}_dissolved.gpkg").to_crs("EPSG:5070")
        state_data['geometry'] = state_data['geometry'].buffer(0)
        for i in range(0, len(county_data)):
            try:
                results.append({
                    'GEOID': county_data.iloc[i].GEOID,
                    'area': gpd.clip(state_data, county_data.iloc[i].geometry).area.sum()
                })
            except Exception as e:
                print(e)
    except:
        print('could not find file')
    
    df = pd.DataFrame(results)
    df.to_csv(f'./areas/{state["GEOID"]}.csv', index=False)
    print(f"Parsed {state['NAME']}...")

# %%
def main():
    state_range = [i for i in range(0, len(state_dict))]
    # with Pool(processes=12) as pool:
    #     pool.map(init_geoms, state_range)
    with Pool(processes=12) as pool:
        pool.map(clip_counties, state_range)
    # print(results)
    # df = pd.DataFrame(results)
    # df.to_csv('./area_results_new.csv', index=False)

if __name__ == "__main__":
    main()
# %%
