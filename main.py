import global_var as gv
import data_request as dr
import graphics as gx
import topo_construction as tc
import cities as ct
import folium
from folium.plugins import Draw
import argparse
import os
import sys


def extract_subzones(l, tz):
    countries = []
    for c in l:
        print(c)
        country_code, nb_cities = c.split(",")
        countries.append((int(nb_cities), country_code, tz))
    return countries


def extract_zones(args):
    countries = []
    if args.countries_cities is not None:
        countries += extract_subzones(args.countries_cities[0], False)
    if args.timezone_cities is not None:
        countries += extract_subzones(args.timezone_cities[0], True)

    return countries


def get_all_largest_cities(countries, reg_merge):
    cities = {}
    for nb_cities, country, tz in countries:
        sub_cities = dr.req_largest_cities2(
            nb_cities, None, country, tz, reg_merge)
        cities.update(sub_cities)
    return cities


def get_all_distances(cities):
    fcities = {}
    nb_cities = len(cities)
    if nb_cities > gv.MAX_CITIES_REQ:
        # Prepare batches
        imin = 0
        imax = gv.BATCH_SIZE_REQ
        batches = []
        while imin < imax:
            keys_to_include = list(cities.keys())[imin:imax]
            batches.append(keys_to_include)
            imin += gv.BATCH_SIZE_REQ
            imax = min(nb_cities, imax+gv.BATCH_SIZE_REQ)
        for i in range(len(batches)):
            for j in range(i, len(batches)):
                sub_dists = dr.req_all_distances(
                    {k: v for k, v in cities.items() if k in batches[i] or k in batches[j]})
                fcities.update(sub_dists)
    else:
        fcities = dr.req_all_distances(cities)
    dr.refresh_min_max_dist(fcities)
    return fcities


def merge_all_cities(fcities, args, scale):
    merge_dist = 0
    if args.merge_dist_abs is None:
        if args.merge_dist_div is not None:
            gv.MERGE_THRESHOLD_DIVIDER = int(args.merge_dist_div)
        merge_dist = ct.highest_distance / gv.MERGE_THRESHOLD_DIVIDER
    else:
        gv.MERGE_THRESHOLD_ABSOLUTE = int(args.merge_dist_abs)
        merge_dist = gv.MERGE_THRESHOLD_ABSOLUTE

    fcities = dr.remove_close_cities(fcities, {}, merge_dist, scale, args.frontier)
    dr.refresh_min_max_dist(fcities)
    return fcities


def save_topo(finalg, countries, fcities):
    country = ""
    for c in countries:
        country += c[1]
    folder = "{}_{}".format(country, len(finalg.get_vertices()))
    if not os.path.isdir(folder):
        os.mkdir(folder)
    tc.save_to_file(finalg, "{}/topo{}_{}_{}_{}_{}-{}-{}".format(folder, country, len(fcities), len(finalg.get_vertices()),
                    len(finalg.get_edges()), gv.NB_AGG_GROUPS, gv.NB_ROUTERS_PER_AGG_GROUPS, gv.NB_EDGE_ROUTERS))
    os.rename("mapa.html", "{}/mapa.html".format(folder))


def create_map(m, g_tree, fcities):
    gx.edges_on_map(g_tree, m, fcities)
    gx.cities_marker_on_map(m, fcities)
    draw = Draw()
    draw.add_to(m)
    m.save("mapa.html")


def main():
    print(sys.argv)
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--countries-cities", action="append", nargs='*')
    parser.add_argument("-t", "--timezone-cities", action="append", nargs='*')
    parser.add_argument("--merge-dist-abs", action="store")
    parser.add_argument("--merge-dist-div", action="store")
    parser.add_argument("--regional-merge", action="store_true", default=False)
    parser.add_argument("--triple-core-cost",
                        action="store_true", default=False)
    parser.add_argument("--big-link-capitals",
                        action="store_true", default=False)
    parser.add_argument("--frontier", action="store_true", default=True)
    parser.add_argument("--admin-merge", action="store_true", default=False)
    args = parser.parse_args()

    m = folium.Map(location=[48.866667, 2.333333], tiles="CartoDB Positron")
    print("Getting largest cities...")

    # Retrieve country/timzone codes from argument
    countries = extract_zones(args)

    # Retrieve Larges Cities
    if args.timezone_cities != None or len(args.countries_cities[0]) > 1: 
        scale = gv.MULTICOUNTRY_SCALE
        print("SCALE : Multi-country")
    else:
        scale = gv.COUNTRY_SCALE
        print("SCALE : Country")
    cities = get_all_largest_cities(countries, args.regional_merge)

    # Merge cities that are too close
    fcities = get_all_distances(cities)
    fcities = merge_all_cities(fcities, args, scale)

    print("Kept only {} cities".format(len(fcities)))
    print("Min Delay is {}".format((ct.lowest_distance / gv.LIGHT_SPEED) * 1000))

    print("Generating skeletal basis...")
    
    g = ct.cities_2_graph(fcities, args.triple_core_cost)
    g_tree = tc.get_min_st_largest_city(g, fcities)

    print("Generating bi-connected topology...")
    non_tree_edges = tc.edges_g1_minus_g2(g, g_tree)
    tc.remove_articulation_point(g, g_tree, fcities, args.triple_core_cost)

    print("Starting post process...")
    tc.post_process(g_tree, fcities, args.triple_core_cost)

    create_map(m, g_tree, fcities)

    print("Adding areas...")
    finalg = tc.multi_areaize(g_tree)
    save_topo(finalg, countries, fcities)


if __name__ == "__main__":
    main()
