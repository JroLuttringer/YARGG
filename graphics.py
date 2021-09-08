from global_var import *
from cities import * 
import folium

def cities_marker_on_map(map, cities):
    for c, info in cities.items():
        folium.Circle(radius = 15000,
        location=[info.lat, info.long], 
        color = "black",
        fill = True).add_to(map)
        #folium.Marker([info.lat, info.long]).add_to(map)


def edges_on_map(g, map, cities, color="red"):
    for x, y in g.edges():
        c1 = cities[City.id_to_city[x]]
        c2 = cities[City.id_to_city[y]]
        p1 = (float(c1.lat), float(c1.long))
        p2 = (float(c2.lat), float(c2.long))
        edge = g.edge(x,y)
        color = None
        dash_array = None
        weight = None
        if g.ep["igpcost"][edge] == gv.POST_PROCESS_COST:
            color = "orange"
            dash_array = "1"
            weight = 2
        elif g.ep["igpcost"][edge] == gv.STANDARD_COST:
            color = "red"
            dash_array = "1"
            weight = 5
        elif g.ep["igpcost"][edge] == gv.BIG_CITIES_COST:
            color = "black"
            dash_array = "1"
            weight = 10
        if len(c1.geo) != 0 and len(c2.geo) != 0:
            geometry = c1.geo[City.id_to_city[y]]
            folium.PolyLine(locations=polyline.decode(geometry)).add_to(map)
        folium.PolyLine([p1, p2], color=color, weight = weight,
                        dash_array=dash_array).add_to(map)