import cities as ct
import wget
import json
import os
import global_var as gv
import math

import haversine as hs


def req_largest_cities(number_of_cities=1000, request=None, refine_country=None, refine_misc=None):
    # FORGE REQUEST
    base_url = "https://public.opendatasoft.com/api/records/1.0/search/?dataset=geonames-all-cities-with-a-population-1000"
    if request:
        base_url += "&q={}".format(request)
    base_url += "&rows={}".format(number_of_cities)
    base_url += "&sort=population"
    if refine_country:
        base_url += "&refine.country={}".format(refine_country)
    if refine_misc:
        base_url += "&{}".format(refine_misc)

    # RETRIEVE REQUEST
    res = wget.download(base_url)
    with open(res, 'r') as f:
        obj = json.load(f)
    os.remove("download.wget")

    # PARSE REQUEST
    cities = {}
    for city in obj["records"]:
        name = city["fields"]["name"]
        lat = str(city["fields"]["latitude"])
        long = str(city["fields"]["longitude"])
        population = city["fields"]["population"]
        cities[name] = ct.City(name, lat, long, population)
    if len(cities.keys()) != number_of_cities:
        print("\n[WARNING] Only returned {} cities".format(len(cities.keys())))

    return cities


def req_largest_cities2(number_of_cities=1000, request=None, refine_country="FR", timezone=False, reg_merge=False):
    # FORGE REQUEST
    base_url = "https://documentation-resources.opendatasoft.com/api/records/1.0/search/?dataset=doc-geonames-cities-5000"
    if request:
        base_url += "&q={}".format(request)

    if not timezone:
        base_url += "&q=country_code+%3D+{}".format(refine_country)
    else:
        base_url += "&q=timezone+%3D+{}".format(refine_country)
    base_url += "&rows={}".format(number_of_cities)
    base_url += "&sort=population"

    # RETRIEVE REQUEST
    res = wget.download(base_url)
    with open(res, 'r') as f:
        obj = json.load(f)
    os.remove("download.wget")

    # PARSE REQUEST
    cities = {}
    for city in obj["records"]:
        name = city["fields"]["name"]
        fc = city["fields"]["feature_code"]
        # print(city["fields"])
        cc = city["fields"]["country_code"]
        lat = str(city["geometry"]["coordinates"][1])
        long = str(city["geometry"]["coordinates"][0])
        population = city["fields"]["population"]
        if reg_merge:
            admin_code = city["fields"]["admin1_code"]
        else: 
            admin_code = 1
        cities[name] = ct.City(name, lat, long, population, admin_code=admin_code, feature_code=fc, country_code = cc)
    print("\nReturned {} cities".format(len(cities.keys())))

    return cities


def populate(cities, distances):
    i = 0
    for n1, city1 in cities.items():
        j = 0
        for n2, city2 in cities.items():
            if n1 != n2:
                dist = distances[i][j]
                if dist == None:
                    dist = hs.haversine((float(city1.lat), float(city1.long)), ((
                        float(city2.lat), float(city2.long)))) * 1000

                city1.distances[n2] = math.ceil(float(dist))
                city2.distances[n1] = math.ceil(float(dist))
            j += 1
        i += 1


def refresh_min_max_dist(cities):
    min_dist = 99999999
    max_dist = 0
    for n1, city1 in cities.items():
        for n2, city2 in cities.items():
            if n1 == n2:
                continue
            dist = city1.distances[n2]
            max_dist = max(max_dist, dist)
            min_dist = min(min_dist, dist)
    ct.lowest_distance = min_dist
    ct.highest_distance = max_dist


def mergeable(city1, city2, scale, frontier):
    if not frontier:
        return True
    condition = True
    if scale == gv.COUNTRY_SCALE and frontier: 
        condition = (city1.admin_code == city2.admin_code)
    elif scale > gv.COUNTRY_SCALE and frontier: 
        condition = (city2.country_code == city2.country_code)
    return condition

def remove_close_cities(cities, old_cities, merge_dist, scale, frontier, admin=None):
    filtered_cities = {}
    print("merge {}".format(merge_dist))
    not_add = []
    for n1, city1 in cities.items():
        add = True
        for n2, city2 in cities.items():
            if n1 == n2:
                continue
            dist = city1.distances[n2]
            if mergeable(city1, city2, scale, frontier) and dist < merge_dist and city1.population < city2.population:
                #print("Merging {} and {}".format(city1.name, city2.name))
                add = False
                city2.population += city1.population
                if n1 in filtered_cities:
                    del filtered_cities[n1]
                    not_add.append(n1)

            if mergeable(city1, city2, scale, frontier) and dist < merge_dist and city2.population < city1.population and n2 in filtered_cities:
                print("Merging {} and {}".format(city1.name, city2.name))
                del filtered_cities[n2]
                not_add.append(n2)
                city1.population += city2.population

        if add and not n1 in not_add:
            filtered_cities[n1] = city1

    old_cities = list(old_cities.keys())
    for n1, c1 in filtered_cities.items():
        if n1 in old_cities:
            continue
        c1.id = ct.ids
        ct.City.id_to_city[ct.ids] = n1
        ct.ids += 1
    return filtered_cities


def req_all_distances(cities):
    # TODO : BATCHES if > 100
    base_url = "http://router.project-osrm.org/table/v1/driving/"
    for n, city in cities.items():
        base_url += city.long + "," + city.lat + ";"
    base_url = base_url[:-1]

    base_url += "?annotations=distance"
    res = wget.download(base_url)
    distances = None
    with open(res, 'r') as f:
        obj = json.load(f)
        if obj["code"] != "Ok":
            print("Couldn't find {} to {}".format(self.name, c2.name))
        distances = obj["distances"]
    os.remove("response.json")
    if distances == None:
        return

    populate(cities, distances)
    return cities


def load_cities_from_file(file):
    cities = {}
    max_dist = 0
    min_dist = 9999999999999999999999999
    with open(file) as f:
        for l in f.readlines():
            name, lat, long, population, distances = l.strip().split("/")
            city = ct.City(name.replace(" ", ""), lat.replace(" ", ""), long.replace(
                " ", ""), population.strip(" "), json.loads(distances.replace("\'", "\"")))
            cities[name.replace(" ", "")] = city
            for _, d in json.loads(distances.replace("\'", "\"")).items():
                max_dist = max(max_dist, int(d))
                min_dist = min(min_dist, int(d))
    ct.highest_distance = max_dist
    ct.lowest_distance = min_dist

    fcities = remove_close_cities(cities, {})
    refresh_min_max_dist(fcities)
    while (ct.lowest_dist / LIGHT_SPEED) * 1000 < 0.3:
        gv.MERGE_THRESHOLD += 10000
        fcities = remove_close_cities(fcities, fcities)
        refresh_min_max_dist(fcities)
    return fcities
