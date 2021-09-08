import global_var as gv
import cities as ct
from graph_tool.all import *
import random


def get_min_st_largest_city(g, cities):
    print("Largest City : {}".format(ct.get_largest_city(cities)))
    # GET MIN SPANNING TREE ROOTED IN LARGEST CITY
    largest_city_name, _ = ct.get_largest_city(cities)
    tree = min_spanning_tree(
        g, weights=g.ep["distpop"], root=cities[largest_city_name].id)
    g_tree = g.copy()
    g_tree.set_edge_filter(tree)

    return g_tree


def best_ranked_edges_bcomp(full_g, graph, nodes, other_nodes, art, cities):
    min_weight = float('inf')
    min_edge = None
    degrees = list(graph.get_out_degrees(graph.get_vertices()))
    for u in nodes:
        for v in other_nodes:
            dist = graph_tool.topology.shortest_distance(
                full_g, weights=full_g.ep["distance"], source=u, target=v)
            hops = graph_tool.topology.shortest_distance(
                graph, source=u, target=v)
            city1 = ct.City.id_to_city[int(str(u))]
            city2 = ct.City.id_to_city[int(str(v))]
            if hops == 1: continue
            total_pop = (cities[city1].population / ct.highest_population) + \
                (cities[city2].population / ct.highest_population)

            weight = dist#((dist / ct.highest_distance))# *
                      #(degrees[int(str(u))] + degrees[int(str(v))]))
            if weight < min_weight:
                min_weight = weight
                min_edge = (u, v)
    return min_edge


def post_process(graph, cities, triple_cost):
    # return
    done = True
    added = []
    i = 0
    while done:
        min_w = 0
        min_edge = None
        degrees = list(graph.get_out_degrees(graph.get_vertices()))
        for u in graph.vertices():
            for v in graph.vertices():
                if (u, v) in added or int(str(u)) == int(str(v)):
                    continue

                city1 = ct.City.id_to_city[int(str(u))]
                city2 = ct.City.id_to_city[int(str(v))]

                dist = cities[city1].distances[city2]
                dist_g = graph_tool.topology.shortest_distance(
                    graph, weights=graph.ep["distance"], source=u, target=v)

                hops = graph_tool.topology.shortest_distance(
                    graph, source=u, target=v)
                if hops == 1:
                    continue
                cities_are_close = ((dist / ct.highest_distance)
                                    <= gv.POST_PROCESS_CLOSE_ENOUGH)
                distance_is_reduced = (
                    dist_g/dist > gv.POST_PROCESS_REDUCE_DIST)
                degrees_ok = degrees[int(
                    str(u))] <= 4 and degrees[int(str(v))] <= 4

                if cities_are_close and distance_is_reduced:# and degrees_ok:
                    w = dist_g/dist + \
                        (cities[city1].population +
                         cities[city2].population) / (2*ct.highest_population) 
                    if w > min_w:
                        min_w = w
                        min_edge = (u, v, dist)

        if min_edge == None:
            print("Added {} edges".format(i))
            return
        added.append((min_edge[0], min_edge[1]))
        e = graph.add_edge(min_edge[0], min_edge[1])

        if triple_cost:
            add_metric(graph, e, cost=gv.COST_C2C, delay=float(
                min_edge[2] / gv.LIGHT_SPEED)*1000, area=0, distance=min_edge[2])
        else:
            add_metric(graph, e, cost=gv.POST_PROCESS_COST, delay=float(
                min_edge[2] / gv.LIGHT_SPEED)*1000, area=0, distance=min_edge[2])
        i += 1


def edges_g1_minus_g2(g1, g2):
    g_edges = set()
    minus_set = set()
    for x, y in g2.edges():
        minus_set.add((str(x), str(y), g1.ep["distance"][g1.edge(x, y)]))

    for x, y in g1.edges():
        if (str(x), str(y), g1.ep["distance"][g1.edge(x, y)]) not in minus_set:
            g_edges.add((str(x), str(y), g1.ep["distance"][g1.edge(x, y)]))

    return g_edges


def get_articulation_points(graph):
    edges_to_comp, art, _ = graph_tool.topology.label_biconnected_components(
        graph)
    artp = []
    for i, node in enumerate(art):
        if node == 1:
            artp.append(i)
    return edges_to_comp, artp


def add_to_dict(dict1, dict2, node, comp):
    # CUT VERTEX
    if node in dict1:
        if comp not in dict1[node]:
            dict1[node].append(comp)
    else:
        dict1[node] = [comp]

    if comp not in dict2:
        dict2[comp] = [node]
    elif node not in dict2[comp]:
        dict2[comp].append(node)

    return dict1, dict2


def map_nodes_components(graph, artp, comp):
    nodes_cmp = {}
    bi_cmp_to_nodes = {}
    for e in graph.edges():
        src = int(str(e.source()))
        target = int(str(e.target()))
        nodes_cmp, bi_cmp_to_nodes = add_to_dict(
            nodes_cmp, bi_cmp_to_nodes, src, comp[e])
        nodes_cmp, bi_cmp_to_nodes = add_to_dict(
            nodes_cmp, bi_cmp_to_nodes, target, comp[e])
    return nodes_cmp, bi_cmp_to_nodes


def remove_articulation_point(full_g, graph, cities, triple_cost):
    while True:
        # GET BI CONNECTED COMPONENTS & ARTICULATION POINTS
        nb_vertices = len(graph.get_vertices())
        edges_to_comp, art = get_articulation_points(graph)
        if len(art) == 0:
            return
        nodes_to_cmp, cmp_to_nodes = map_nodes_components(
            graph, art, edges_to_comp)

        # GET NODES OF FIRST BCOMP AND NODES IN OTHERS BCOMP
        bcmp = list(cmp_to_nodes)[0]
        nodes = [x for x in cmp_to_nodes[bcmp] if x not in art]
        if len(nodes) == 0:
            nodes = [x for x in cmp_to_nodes[bcmp]]
        other_nodes = [
            x for x in graph.vertices() if x not in cmp_to_nodes[bcmp]]

        # ADD MOST INTERESTING EDGE THAT BRIDGES TWO DIFFERENT BCOMPS
        min_edge = best_ranked_edges_bcomp(
            full_g, graph, nodes, other_nodes, art, cities)

        dist = full_g.ep.distance[full_g.edge(min_edge[0], min_edge[1])]
        distpop = full_g.ep.distpop[full_g.edge(min_edge[0], min_edge[1])]
        delay = full_g.ep.delay[full_g.edge(min_edge[0], min_edge[1])]

        e = graph.add_edge(min_edge[0], min_edge[1])
        cost = gv.COST_C2C
        if triple_cost:
            cost = gv.STANDARD_COST
        add_metric(graph, e, cost=cost, delay=float(dist / gv.LIGHT_SPEED)
                * 1000, area=gv.BACKBONE_AREA, distance=dist, distpop=distpop)


def get_random_delay(min=0.001, max=0.01):
    return random.uniform(min, max)


def add_metric(graph, edge, cost=None, delay=None, area=None, distance=None, distpop=None):
    if cost != None: graph.ep["igpcost"][edge] = cost
    if delay != None: graph.ep["delay"][edge] = delay
    if area != None: graph.ep["area"][edge] = area
    if distance != None: graph.ep["distance"][edge] = distance
    if distpop != None: graph.ep["distpop"][edge] = distpop


def multi_areaize(g_double_core):
    max_delay_c2a = (ct.lowest_distance / gv.LIGHT_SPEED) * 1000
    if max_delay_c2a < gv.MIN_DELAY_C2A:
        print("/ ! \ Hey this is not going to work : Delay between two core nodes is too small")
    g2 = Graph(g_double_core, directed=False)
    graph_union(g_double_core, g2, internal_props=True, include=True)
    # DOUBLE THE CORE AND PUT A LINK BETWEEN EACH CORE ROUTER IN THE SAME CITY
    # g_double_core = graph_union(g, g2, internal_props=True)
    og_nb_vertices = len(g2.get_vertices())
    g_double_core.vp["name"] = g_double_core.new_vertex_property("string")

    for i, v in enumerate(g2.get_vertices()):
        core1 = g_double_core.vertex(i)
        core2 = g_double_core.vertex(i + og_nb_vertices)
        e_bb = g_double_core.add_edge(core1, core2)
        e_area = g_double_core.add_edge(core1, core2)

        d = get_random_delay(gv.MIN_DELAY_CLC, 0.3)
        add_metric(g_double_core, e_bb, gv.COST_CLC, d, gv.BACKBONE_AREA)
        add_metric(g_double_core, e_area, gv.COST_CLC, d, i+1)

        city_name=ct.City.id_to_city[v].replace(" ", "")
        g_double_core.vp["name"][core2]=city_name[:3] +\
            "-ABR0.{}.1".format(i+1)
        g_double_core.vp["name"][core1]=city_name[:3] +\
            "-ABR0.{}.0".format(i+1)


        # CREATE THE AGGREGATION LAYER
        for agg_group in range(gv.NB_AGG_GROUPS):
            agg_routers=[]
            for agg_router in range(gv.NB_ROUTERS_PER_AGG_GROUPS):
                aggr=g_double_core.add_vertex()
                agg_routers.append(aggr)
                # LINK AGG ROUTER TO ALL CORE ROUTERS
                g_double_core.vp["name"][aggr]=city_name[:3] + \
                    "-AGG{}.{}.{}".format(i+1, agg_group, agg_router)
                e1=g_double_core.add_edge(aggr, g_double_core.vertex(i))
                e2=g_double_core.add_edge(
                    aggr, g_double_core.vertex(i + og_nb_vertices))
                # WEIGHTS
                add_metric(g_double_core, e1, gv.COST_C2A, get_random_delay(
                    gv.MIN_DELAY_C2A, max_delay_c2a), i+1)
                add_metric(g_double_core, e2, gv.COST_C2A, get_random_delay(
                    gv.MIN_DELAY_C2A, max_delay_c2a), i+1)
                # CROSS LINK
                if agg_router > 0:
                    e=g_double_core.add_edge(aggr, agg_routers[agg_router - 1])
                    add_metric(g_double_core, e, gv.COST_CLA, get_random_delay(
                        gv.MIN_DELAY_C2A, max_delay_c2a), i+1)


            for edge_router in range(gv.NB_EDGE_ROUTERS):
                er=g_double_core.add_vertex()
                g_double_core.vp["name"][er]=city_name[:3] + \
                    "-ACC{}.{}.{}".format(i+1, agg_group, edge_router)
                for agg_router in agg_routers:
                    e=g_double_core.add_edge(er, agg_router)
                    add_metric(g_double_core, e, gv.COST_A2E, get_random_delay(
                        gv.MIN_DELAY_A2E, gv.MAX_DELAY_A2E), i+1)


    return g_double_core
    # graph_draw(g_double_core,vertex_text=v_prop, edge_text=(g_double_core.edge_properties["distance"]))
    # graph_draw(g_double_core, vertex_text=g_double_core.vertex_index)

def save_to_file(g, name):
    nb_nodes=len(g.get_vertices())
    nb_edges=len(g.get_edges())
    lines_per_area={}
    with open(name+"_full", 'w+') as sf:
        for e in g.edges():
            line="{} {} {:.10f} {}".format(g.vp["name"][e.source(
            )], g.vp["name"][e.target()], g.ep["delay"][e],  int(g.ep["igpcost"][e]))
            if g.ep["area"][e] not in lines_per_area:
                lines_per_area[g.ep["area"][e]]=""
            lines_per_area[g.ep["area"][e]] += line+"\n"
            sf.write(line+" "+str(int(g.ep["area"][e]))+"\n")
    for area, text in lines_per_area.items():
        with open(name+"_area{}".format(int(area)), 'w+') as f:
            f.write(text)
