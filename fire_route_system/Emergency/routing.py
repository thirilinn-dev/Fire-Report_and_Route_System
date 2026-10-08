import heapq
import math
from .models import RoadNode, RoadEdge


def distance(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, [*a, *b])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371000 * 2 * math.asin(min(1.0, math.sqrt(h)))


def project_point_to_segment(p, a, b):
    """
    Projects point p=(lat, lon) onto line segment from a=(lat, lon) to b=(lat, lon).
    Returns (projected_point, t, distance_in_metres) where t in [0.0, 1.0].
    """
    mid_lat = math.radians((a[0] + b[0]) / 2.0)
    cos_lat = math.cos(mid_lat)

    ax, ay = a[1] * cos_lat, a[0]
    bx, by = b[1] * cos_lat, b[0]
    px, py = p[1] * cos_lat, p[0]

    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay

    len_sq = vx * vx + vy * vy
    if len_sq <= 1e-12:
        t = 0.0
    else:
        t = max(0.0, min(1.0, (wx * vx + wy * vy) / len_sq))

    proj_lat = a[0] + t * (b[0] - a[0])
    proj_lon = a[1] + t * (b[1] - a[1])
    proj_point = (proj_lat, proj_lon)
    dist = distance(p, proj_point)
    return proj_point, t, dist


def dijkstra(graph, start, end):
    queue, costs, previous = [(0, start)], {start: 0}, {}
    while queue:
        cost, node = heapq.heappop(queue)
        if cost != costs[node]:
            continue
        if node == end:
            path = [end]
            while path[-1] != start:
                path.append(previous[path[-1]])
            return list(reversed(path)), cost
        for target, weight in graph.get(node, []):
            if weight < 0:
                raise ValueError('Negative road distance')
            candidate = cost + weight
            if candidate < costs.get(target, math.inf):
                costs[target], previous[target] = candidate, node
                heapq.heappush(queue, (candidate, target))
    return [], None


def clean_coordinate_sequence(points):
    """
    Deduplicates consecutive coordinates that are within 1 meter of each other.
    """
    cleaned = []
    for pt in points:
        if not cleaned or distance(cleaned[-1], pt) > 1.0:
            cleaned.append([round(pt[0], 6), round(pt[1], 6)])
    return cleaned


def route_between(station, incident):
    if incident.latitude is None or incident.longitude is None:
        return {'error': 'မီးလောင်ရာ coordinate ကို အတည်ပြုရန်လိုသည်။'}
    if station.latitude is None or station.longitude is None:
        return {'error': 'မီးသတ်စခန်း coordinate မရှိပါ။'}

    nodes = {n.pk: (n.latitude, n.longitude) for n in RoadNode.objects.all()}
    if not nodes:
        from django.core.management import call_command
        try:
            call_command('seed_roads')
            nodes = {n.pk: (n.latitude, n.longitude) for n in RoadNode.objects.all()}
        except Exception:
            pass

    if not nodes:
        return {'error': 'လမ်းဒေတာ မထည့်သွင်းရသေးပါ။'}

    start_point = (station.latitude, station.longitude)
    end_point = (incident.latitude, incident.longitude)

    # Fetch all edge segments
    all_edges = list(RoadEdge.objects.values_list('source_id', 'target_id', 'metres', 'name'))
    if not all_edges:
        return {'error': 'လမ်းကြောင်း ကွန်ရက် မရှိပါ။'}

    # 1. Edge-Snapping: Find closest road segment for start_point and end_point
    best_start_edge = None
    best_start_proj = None
    best_start_t = 0.0
    best_start_dist = math.inf

    best_end_edge = None
    best_end_proj = None
    best_end_t = 0.0
    best_end_dist = math.inf

    for u, v, metres, name in all_edges:
        if u not in nodes or v not in nodes:
            continue
        p_u = nodes[u]
        p_v = nodes[v]

        # Snap start_point
        proj_s, t_s, d_s = project_point_to_segment(start_point, p_u, p_v)
        if d_s < best_start_dist:
            best_start_dist = d_s
            best_start_edge = (u, v, metres, name)
            best_start_proj = proj_s
            best_start_t = t_s

        # Snap end_point
        proj_e, t_e, d_e = project_point_to_segment(end_point, p_u, p_v)
        if d_e < best_end_dist:
            best_end_dist = d_e
            best_end_edge = (u, v, metres, name)
            best_end_proj = proj_e
            best_end_t = t_e

    if best_start_dist > 25000 or best_end_dist > 25000:
        return {'error': 'လမ်းကွန်ရက်နှင့် တည်နေရာအလှမ်းဝေးနေသည်။ Map pin ကို စစ်ဆေးပါ။'}

    u_s, v_s, len_s, name_s = best_start_edge
    u_e, v_e, len_e, name_e = best_end_edge

    # Case A: Start and End project onto the exact same road segment
    if {u_s, v_s} == {u_e, v_e}:
        # Calculate distance along this street
        if u_s == u_e:
            road_distance = abs(best_start_t - best_end_t) * len_s
        else:
            road_distance = abs(best_start_t - (1.0 - best_end_t)) * len_s

        total_metres = round(road_distance + best_start_dist + best_end_dist)
        route_coords = clean_coordinate_sequence([start_point, best_start_proj, best_end_proj, end_point])

        # Direction calculation
        dy = best_end_proj[0] - best_start_proj[0]
        dx = (best_end_proj[1] - best_start_proj[1]) * math.cos(math.radians(best_start_proj[0]))
        bearing = math.degrees(math.atan2(dx, dy)) % 360
        heading = ['မြောက်', 'အရှေ့', 'တောင်', 'အနောက်'][int((bearing + 45) // 90) % 4]

        instructions = [{
            'road': name_s or 'လမ်းမကြီး',
            'direction': heading,
            'turn': 'စတင်သွားပါ',
            'metres': round(road_distance)
        }]

        return {
            'coordinates': route_coords,
            'metres': round(road_distance),
            'total_metres': total_metres,
            'instructions': instructions,
            'start_connector_metres': round(best_start_dist),
            'end_connector_metres': round(best_end_dist),
            'attribution': '© OpenStreetMap contributors'
        }

    # Case B: Standard routing via Dijkstra graph with virtual snapped endpoints
    graph = {}
    labels = {}
    for source, target, metres, name in all_edges:
        graph.setdefault(source, []).append((target, metres))
        if (source, target) not in labels or metres < labels[source, target][0]:
            labels[(source, target)] = (metres, name)

    V_START = -1001
    V_END = -1002

    # Connect virtual start to edge endpoints
    w_s_u = best_start_t * len_s
    w_s_v = (1.0 - best_start_t) * len_s
    graph[V_START] = [(u_s, w_s_u), (v_s, w_s_v)]
    labels[(V_START, u_s)] = (w_s_u, name_s)
    labels[(V_START, v_s)] = (w_s_v, name_s)

    # Connect edge endpoints to virtual end
    w_u_e = best_end_t * len_e
    w_v_e = (1.0 - best_end_t) * len_e
    graph.setdefault(u_e, []).append((V_END, w_u_e))
    graph.setdefault(v_e, []).append((V_END, w_v_e))
    labels[(u_e, V_END)] = (w_u_e, name_e)
    labels[(v_e, V_END)] = (w_v_e, name_e)

    path, metres = dijkstra(graph, V_START, V_END)
    if not path or metres is None:
        return {'error': 'သွားနိုင်သောလမ်းကြောင်း မရှိပါ။'}

    # Build sequence of coordinates and turn-by-turn instructions
    path_nodes = path[1:-1]  # Exclude V_START and V_END
    raw_coords = [start_point, best_start_proj]
    for n in path_nodes:
        raw_coords.append(nodes[n])
    raw_coords.append(best_end_proj)
    raw_coords.append(end_point)

    route_coords = clean_coordinate_sequence(raw_coords)

    instructions = []
    previous_bearing = None

    # Step through transitions to build human navigation guidance
    full_path_steps = list(zip(path, path[1:]))
    for idx, (a, b) in enumerate(full_path_steps):
        step_len, name = labels.get((a, b), (0, 'လမ်း'))
        coord_a = best_start_proj if a == V_START else (best_end_proj if a == V_END else nodes[a])
        coord_b = best_start_proj if b == V_START else (best_end_proj if b == V_END else nodes[b])

        dy = coord_b[0] - coord_a[0]
        dx = (coord_b[1] - coord_a[1]) * math.cos(math.radians(coord_a[0]))
        bearing = math.degrees(math.atan2(dx, dy)) % 360
        heading = ['မြောက်', 'အရှေ့', 'တောင်', 'အနောက်'][int((bearing + 45) // 90) % 4]

        turn = 'စတင်သွားပါ'
        if previous_bearing is not None:
            change = (bearing - previous_bearing + 180) % 360 - 180
            turn = 'တည့်တည့်ဆက်သွားပါ' if abs(change) < 30 else ('ညာဘက်ကွေ့ပါ' if change > 0 else 'ဘယ်ဘက်ကွေ့ပါ')

        label = name or 'လမ်းမကြီး'
        if instructions and instructions[-1]['road'] == label and turn == 'တည့်တည့်ဆက်သွားပါ':
            instructions[-1]['metres'] += round(step_len)
        else:
            instructions.append({
                'road': label,
                'direction': heading,
                'turn': turn,
                'metres': round(step_len)
            })
        previous_bearing = bearing

    total_metres = round(metres + best_start_dist + best_end_dist)
    return {
        'coordinates': route_coords,
        'metres': round(metres),
        'total_metres': total_metres,
        'instructions': instructions,
        'start_connector_metres': round(best_start_dist),
        'end_connector_metres': round(best_end_dist),
        'attribution': '© OpenStreetMap contributors'
    }
