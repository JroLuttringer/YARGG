def graph_remains_planar(g, u, v):
    e = g.add_edge(u, v)
    ans = graph_tool.topology.is_planar(g)
    g.remove_edge(e)
    return ans

def impact_on_diameter(g, u, v):
    before, edge = graph_tool.topology.pseudo_diameter(g)
    e = g.add_edge(u, v)
    after, edge = graph_tool.topology.pseudo_diameter(g)
    g.remove_edge(e)
    return float(after/before)


def connect_leaves(g, g_tree, non_tree_edges):
    while True:
        best_edge, still_leaves = best_ranked_edge_leaves(
            g_tree, non_tree_edges)
        if not still_leaves:
            break
        g_tree.add_edge(best_edge[0], best_edge[1])
        g_tree.ep["distance"][g.edge(
            best_edge[0], best_edge[1])] = best_edge[2]

def best_ranked_edge_leaves(g_tree, g_edges):
    _, art, _ = graph_tool.topology.label_biconnected_components(g_tree)
    degrees = list(g_tree.get_out_degrees(g_tree.get_vertices()))
    if 1 not in degrees:
        return [], False
    g_new_edges = set()
    for u, v, w in g_edges:
        if (degrees[int(u)] != 1) and (degrees[int(v)] != 1):
            continue

        arts = 1
        if art[int(u)]:
            arts += 0
        if art[int(v)]:
            arts += 0
        nb_nodes_in_path = graph_tool.topology.shortest_distance(
            g_tree, source=int(u), target=int(v))
        if nb_nodes_in_path == 1:
            continue
        weight = (w / highest_distance *
                  (degrees[int(u)] + degrees[int(v)]) * arts)
        g_new_edges.add((int(u), int(v), w))

    sorted_edges = sorted(g_new_edges, key=lambda x: x[2])
    return sorted_edges[0], True

def req_all_distances_one_by_one(cities):
    # GET DISTANCES FROM ALL CITIES TO ALL OTHERS
    filtered_cities = {}
    for n1, city1 in cities.items():
        add = True
        for n2, city2 in cities.items():
            if n1 == n2:
                continue
            dist = city1.get_car_distance(city2)
            # FILTER CITIES TOO CLOSE TO EACH OTHER
            if dist < 500000 and (city1.population < city2.population):
                add = False
                break
        if add:
            filtered_cities[n1] = city1
    # SAVE CITIES AND DIST IN FILE
    save_cities_to_files(filtered_cities)
    return filtered_cities
