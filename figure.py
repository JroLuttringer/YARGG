from opencage.geocoder import OpenCageGeocode
import folium
import wget
import json
import polyline
import os
from folium.plugins import Draw
geocoder = OpenCageGeocode("2b608eafd3764df99f71a3a08d2cef9e")
LIGHT_SPEED = 299792458 * 0.60

class City:
    def __init__(self, name, lat, lng):
        self.name = name 
        self.lat = lat 
        self.lng = lng


# cities = [
#     'Manchester, England', 
#     "Leeds, England", 
#     "Hull, England",
#     "Carlisle, England", 
#     "Sunderland, England", 
#     "Liverpool, England",
#     "Shefield, England",
# ]

cities = [
    "Frankfurt, Germany",
    "Genève, Suisse",
    "Milan, Italy",
    "Budapest, Hongrie",
    "Vienne, Autriche"
]

# big_link_cities = [("Sunderland", "Carlisle"), ("Carlisle", "Liverpool"), ("Hull", "Sunderland")]

# medium_link_cities = [("Shefield", "Leeds"), ("Manchester", "Shefield")]
big_link = [("Frankfurt", "Genève"), ("Genève", "Milan"), ("Milan","Vienne") ]
medium_link = [("Vienne","Budapest"), ("Budapest","Frankfurt")]



shift_down = [("Vienne", "Frankfurt")]
shift_up = [("Budapest", "Frankfurt")]


green_dashed = [("Vienne", "Milan"), ("Milan", "Genève"), ("Genève", "Frankfurt")]
yellow_dot = [("Vienne", "Budapest"), ("Budapest", "Frankfurt")]
red_plain = [("Vienne", "Frankfurt")]


dists = {}

all_cities = {}

for c in cities: 
    result = geocoder.geocode(c)
    lat = result[0]['geometry']['lat']
    lng = result[0]['geometry']['lng']
    name = c.split(",")[0]
   
    all_cities[name] = City(name, lat, lng)



# for c1 in cities:
#     for c2 in cities: 
#         if (c1.split(",")[0], c2.split(",")[0]) in big_link_cities or (c2.split(",")[0], c1.split(",")[0]) in  big_link_cities:
#             big_link.append(
#                 ((cities_coord[c1.split(",")[0]][0], cities_coord[c1.split(",")[0]][1]),
#                 (cities_coord[c2.split(",")[0]][0], cities_coord[c2.split(",")[0]][1]))
#             )
#             big_link.append(
#                 ((cities_coord[c2.split(",")[0]][0], cities_coord[c2.split(",")[0]][1]),
#                 (cities_coord[c1.split(",")[0]][0], cities_coord[c1.split(",")[0]][1]))
#             )

# for c1 in cities:
#     for c2 in cities: 
#         if (c1.split(",")[0], c2.split(",")[0]) in medium_link_cities or (c2.split(",")[0], c1.split(",")[0]) in  medium_link_cities:
#             medium_link.append(
#                 ((cities_coord[c1.split(",")[0]][0], cities_coord[c1.split(",")[0]][1]),
#                 (cities_coord[c2.split(",")[0]][0], cities_coord[c2.split(",")[0]][1]))
#             )
#             medium_link.append(
#                 ((cities_coord[c2.split(",")[0]][0], cities_coord[c2.split(",")[0]][1]),
#                 (cities_coord[c1.split(",")[0]][0], cities_coord[c1.split(",")[0]][1]))
#             )

# for c1 in cities:
#     for c2 in cities: 
#         if (c1.split(",")[0], c2.split(",")[0]) in shift_down_link or (c2.split(",")[0], c1.split(",")[0]) in  shift_down_link:
#             shift_down.append(
#                 ((cities_coord[c1.split(",")[0]][0], cities_coord[c1.split(",")[0]][1]),
#                 (cities_coord[c2.split(",")[0]][0], cities_coord[c2.split(",")[0]][1]))
#             )
#             shift_down.append(
#                 ((cities_coord[c2.split(",")[0]][0], cities_coord[c2.split(",")[0]][1]),
#                 (cities_coord[c1.split(",")[0]][0], cities_coord[c1.split(",")[0]][1]))
#             )

# for c1 in cities:
#     for c2 in cities: 
#         if (c1.split(",")[0], c2.split(",")[0]) in shift_up_link or (c2.split(",")[0], c1.split(",")[0]) in shift_up_link:
#             shift_up.append(
#                 ((cities_coord[c1.split(",")[0]][0], cities_coord[c1.split(",")[0]][1]),
#                 (cities_coord[c2.split(",")[0]][0], cities_coord[c2.split(",")[0]][1]))
#             )
#             shift_up.append(
#                 ((cities_coord[c2.split(",")[0]][0], cities_coord[c2.split(",")[0]][1]),
#                 (cities_coord[c1.split(",")[0]][0], cities_coord[c1.split(",")[0]][1]))
#             )


def plot_road(c1, c2, m):
    base_url = "http://router.project-osrm.org/route/v1/driving/"
    base_url += str(all_cities[c1].lng)+","+ str(all_cities[c1].lat) + ";" + str(all_cities[c2].lng)+","+str(all_cities[c2].lat)+"?"
    print(base_url)
    res = wget.download(base_url)
    # RETRIEVE RESPONSE
    with open(res, 'r') as f:
        obj = json.load(f)
        if obj["code"] != "Ok":
            print("Couldn't find ")
        dist = obj["routes"][0]["distance"]
        
        if c1 not in dists: 
            dists[c1] = {}
        dists[c1][c2] = dist

        if c2 not in dists: 
            dists[c2] = {}
        dists[c2][c1] = dist

        geo = obj["routes"][0]["geometry"]
        geopoly = polyline.decode(geo)

        if (c1,c2) in shift_up or (c2,c1) in shift_up:
            for x in range(1,len(geopoly)-1):
                    geopoly[x] = (geopoly[x][0] + 0.3, geopoly[x][1])
        elif (c1,c2) in shift_up or (c2,c1) in shift_down:
            for x in range(1,len(geopoly)-1):
                    geopoly[x] = (geopoly[x][0] - 0.08, geopoly[x][1])
        
        dash_array = '1'
        weight = 4
        color = "#C70039"
        if (c1,c2) in yellow_dot or (c2,c1) in yellow_dot:
            color = "#FFC300"
            dash_array = "50 20 10 20"
        if (c1,c2) in green_dashed or (c2,c1) in green_dashed:
            color = "#2F9156"
            dash_array = "30 50"




        if (c1,c2) in big_link or (c2,c1) in big_link:  
            weight = 20
        elif (c1, c2) in medium_link or (c2,c1) in medium_link:
            weight = 13

        folium.PolyLine(locations=geopoly, weight = weight, dash_array=dash_array, color=color).add_to(m)
        


        # folium.PolyLine([p1, p2], color=color,
        #                 dash_array='10').add_to(map)
    os.remove("response.json")


m = folium.Map(location=[48.866667, 2.333333],tiles="CartoDB Positron")

# plot_road(cities_coord["Manchester"], cities_coord["Leeds"], m)
# plot_road(cities_coord["Hull"], cities_coord["Leeds"], m)
# plot_road(cities_coord["Liverpool"], cities_coord["Carlisle"], m)
# plot_road(cities_coord["Carlisle"], cities_coord["Sunderland"], m)
# plot_road(cities_coord["Hull"], cities_coord["Sunderland"], m)
# plot_road(cities_coord["Manchester"], cities_coord["Liverpool"], m)
# plot_road(cities_coord["Manchester"], cities_coord["Shefield"], m)
# plot_road(cities_coord["Leeds"], cities_coord["Shefield"], m)




plot_road("Frankfurt", "Genève", m)
plot_road("Frankfurt", "Vienne", m)
plot_road("Frankfurt", "Budapest", m)

plot_road("Genève", "Milan", m)

plot_road("Vienne", "Milan", m)
plot_road("Vienne", "Budapest", m)


source = "Frankfurt"
dest = "Vienne"


for key, info in all_cities.items():
    lat = info.lat 
    lng = info.lng
    radius = 10000
    if key == source or key == dest: 
        radius = 7000
    folium.Circle(
        radius=radius,
        location=[lat, lng],
        color="black",
        fill=True,
        fill_opacity=1
    ).add_to(m)
    if key == source or key == dest:
        folium.Circle(
        radius=15000,
        location=[lat, lng],
        color="black",
        fill=True,
        
    ).add_to(m)

print()
d = dists["Frankfurt"]["Genève"] + dists["Genève"]["Milan"] + dists["Milan"]["Vienne"] 
print("Green = {}j km = {} ms".format(d, d/LIGHT_SPEED*1000))
print("F-G = {}, G-M = {}, M-V = {}".format(dists["Frankfurt"]["Genève"], dists["Genève"]["Milan"],dists["Vienne"]["Milan"] ))

print()
d = dists["Frankfurt"]["Budapest"] + dists["Budapest"]["Vienne"] 
print("Orange = {}j km = {} ms".format(d, d/LIGHT_SPEED*1000))
print("F-B = {}, B-V = {}".format(dists["Frankfurt"]["Budapest"], dists["Budapest"]["Vienne"] ))

print()
d = dists["Frankfurt"]["Vienne"]
print("Red = {}j km = {} ms".format(d, d/LIGHT_SPEED*1000))

# print()
# p1 = dists[cities_coord["Liverpool"]][cities_coord["Carlisle"]] + dists[cities_coord["Carlisle"]][cities_coord["Sunderland"]] + \
# dists[cities_coord["Sunderland"]][cities_coord["Hull"]] 
# print(p1 / LIGHT_SPEED * 1000)

# p2 = dists[cities_coord["Liverpool"]][cities_coord["Manchester"]] + dists[cities_coord["Manchester"]][cities_coord["Leeds"]] + \
# dists[cities_coord["Leeds"]][cities_coord["Hull"]] 
# print(p2 / LIGHT_SPEED * 1000)

# p3 = dists[cities_coord["Liverpool"]][cities_coord["Manchester"]] + dists[cities_coord["Manchester"]][cities_coord["Shefield"]] + \
# dists[cities_coord["Shefield"]][cities_coord["Leeds"]] +  dists[cities_coord["Leeds"]][cities_coord["Hull"]]
# print(p3 / LIGHT_SPEED * 1000)

draw = Draw()
draw.add_to(m)
m.save("mapa_test.html")
