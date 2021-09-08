
"""
Manage the cities' infos 
"""

import global_var as gv
from graph_tool.all import *

ids = 0
highest_distance = 0
lowest_distance = 9999999999999999999999999999
highest_population = 0
all_populations = []


class City:

    id_to_city = {}

    def __init__(self, name, lat, long, population, distances=None, geo=None, admin_code = None, feature_code = None, country_code = None):
        global highest_distance, highest_population, all_population
        population = int(population)
        self.name = name
        self.lat = lat
        self.long = long
        self.population = population
        self.distances = distances or {}
        self.geo = geo or {}
        self.id = None
        self.country_code = country_code
        self.admin_code = admin_code
        self.feature_code = feature_code
        all_populations.append(population)
        if population > highest_population:
            highest_population = population

    def print(self):
        print("{} / {} / {} / {}".format(self.name,
              self.lat, self.long, self.population))

    def to_str(self):
        return "{} / {} / {} / {} / {}".format(self.name, self.lat, self.long, self.population, self.distances)

    def dist_already_known(self, c2):
        if c2.name in self.distances and self.distances[c2.name] != None:
            if self.name not in c2.distances or c2.distances[self.name] == None:
                c2.distances[self.name] = self.distances[c2.name]
            return True
        elif self.name in c2.distances and c2.distances[self.name] != None:
            self.distances[c2.name] = c2.distances[self.name]
            return True
        return False

    def get_car_distance(self, c2):
        dist = None
        global highest_distance
        global lowest_distance

        # CHECK IF ALREADY COMPUTED, UPDATE SO c1->c2 = c2-> c1 IF NECESSARY
        if self.dist_already_known(c2):
            return self.distances[c2.name]

        # http://router.project-osrm.org/table/v1/driving/%E2%80%8B13.388860,52.517037;13.397634,52.529407;13.428555,52.523219
        # FORGE REQUEST
        base_url = "http://router.project-osrm.org/route/v1/driving/"
        base_url += self.long+","+self.lat + ";" + c2.long+","+c2.lat+"?"
        res = wget.download(base_url)
        # RETRIEVE RESPONSE
        with open(res, 'r') as f:
            obj = json.load(f)
            if obj["code"] != "Ok":
                print("Couldn't find {} to {}".format(self.name, c2.name))
            dist = obj["routes"][0]["distance"]
            geo = obj["routes"][0]["geometry"]
        os.remove("response.json")

        # UPDATE AND RETURN DISTANCE
        if dist != None:
            dist = float(dist)
            self.distances[c2.name] = dist
            c2.distances[self.name] = dist
            self.geo[c2.name] = geo
            c2.geo[self.name] = geo
        if dist > highest_distance:
            highest_distance = dist
        if dist < lowest_distance:
            lowest_distance = dist
        return dist


def save_cities_to_files(cities, filename="save_file"):
    # SAVE TO FILE
    with open(filename, "w+") as f:
        for _, city in cities.items():
            f.write(city.to_str() + "\n")


def important_enough_city(info):
    return info.population >= sorted(all_populations)[int(len(all_populations) / 25)]


def cities_2_graph(cities, triple_cost=False, capitals = False):
    edges_list = set()
    for c1, info1 in cities.items():
        for c2, info2 in cities.items():
            if c1 == c2:
                continue

            c1_pop_ratio = info1.population / highest_population
            c2_pop_ratio = info2.population / highest_population
            cost = gv.COST_C2C

            if c1 == "Paris" and c2 == "Lyon":
                print(info1.distances[c2] < (gv.NOT_TOO_FAR * highest_distance))

            if ((c1_pop_ratio > gv.IMPORTANT_ENOUGH_CITY or (info1.feature_code == gv.CAPITAL_CITY and capitals)) and (c2_pop_ratio > gv.IMPORTANT_ENOUGH_CITY or (info2.feature_code == gv.CAPITAL_CITY and capitals)) and info1.distances[c2] < (gv.NOT_TOO_FAR * highest_distance)):
               # print("Prioritizing {} - {}".format(c1, c2))
                dist_pop = (
                    info1.distances[c2] / highest_distance)  # * 1/(c1_pop_ratio + c2_pop_ratio)
                if triple_cost:
                    cost = gv.BIG_CITIES_COST
            else:
                dist_pop = info1.distances[c2]
                if triple_cost:
                    cost = gv.STANDARD_COST

            if (info2.id, info1.id, info1.distances[c2], dist_pop, float(info1.distances[c2] / gv.LIGHT_SPEED)*1000, cost, gv.BACKBONE_AREA) in edges_list:
                continue
            if (info1.id, info2.id, info1.distances[c2], dist_pop, float(info1.distances[c2] / gv.LIGHT_SPEED)*1000, cost, gv.BACKBONE_AREA) in edges_list:
                continue

            edge = (info1.id, info2.id, info1.distances[c2], dist_pop, float(
                info1.distances[c2] / gv.LIGHT_SPEED)*1000, cost, gv.BACKBONE_AREA)
            edges_list.add(edge)

    g = Graph(directed=False)
    g.ep["distance"] = g.new_ep("double")
    g.ep["distpop"] = g.new_ep("double")
    g.ep["delay"] = g.new_ep("double")
    g.ep["igpcost"] = g.new_ep("double")
    g.ep["area"] = g.new_ep("double")
    eprops = [g.ep["distance"], g.ep["distpop"],
              g.ep["delay"], g.ep["igpcost"], g.ep["area"]]
    pm = g.add_edge_list(edges_list, eprops=eprops)  # , hashed=True)

    return g


def get_largest_city(cities):
    largest = None
    for c, info in cities.items():
        if largest == None or info.population > largest[1].population:
            largest = (c, info)
    return largest
