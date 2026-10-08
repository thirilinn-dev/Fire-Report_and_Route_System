import heapq
import math
from .models import RoadNode, RoadEdge


def distance(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, [*a, *b])
    h = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6371000 * 2 * math.asin(min(1, math.sqrt(h)))


def dijkstra(graph, start, end):
    queue, costs, previous = [(0, start)], {start: 0}, {}
    while queue:
        cost, node = heapq.heappop(queue)
        if cost != costs[node]: continue
        if node == end:
            path = [end]
            while path[-1] != start: path.append(previous[path[-1]])
            return list(reversed(path)), cost
        for target, weight in graph.get(node, []):
            if weight < 0: raise ValueError('Negative road distance')
            candidate = cost + weight
            if candidate < costs.get(target, math.inf):
                costs[target], previous[target] = candidate, node
                heapq.heappush(queue, (candidate, target))
    return [], None


def route_between(station, incident):
    if incident.latitude is None or incident.longitude is None:
        return {'error': 'မီးလောင်ရာ coordinate ကို အတည်ပြုရန်လိုသည်။'}
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
    start_point, end_point = (station.latitude, station.longitude), (incident.latitude, incident.longitude)
    start = min(nodes, key=lambda k: distance(nodes[k], start_point))
    end = min(nodes, key=lambda k: distance(nodes[k], end_point))
    start_conn = distance(nodes[start], start_point)
    end_conn = distance(nodes[end], end_point)
    if start_conn > 15000 or end_conn > 15000:
        return {'error': 'လမ်းကွန်ရက်နှင့် တည်နေရာအလှမ်းဝေးနေသည်။ Map pin ကို စစ်ဆေးပါ။'}
    graph, labels = {}, {}
    for source, target, metres, name in RoadEdge.objects.values_list('source_id', 'target_id', 'metres', 'name'):
        graph.setdefault(source, []).append((target, metres))
        if (source, target) not in labels or metres < labels[source, target][0]:
            labels[source, target] = (metres, name)
    path, metres = dijkstra(graph, start, end)
    if not path:
        return {'error': 'သွားနိုင်သောလမ်းကြောင်း မရှိပါ။'}
    instructions, previous_bearing = [], None
    for a, b in zip(path, path[1:]):
        length, name = labels[a, b]
        dy, dx = nodes[b][0] - nodes[a][0], (nodes[b][1] - nodes[a][1]) * math.cos(math.radians(nodes[a][0]))
        bearing = math.degrees(math.atan2(dx, dy)) % 360
        heading = ['မြောက်', 'အရှေ့', 'တောင်', 'အနောက်'][int((bearing + 45) // 90) % 4]
        turn = 'စတင်သွားပါ'
        if previous_bearing is not None:
            change = (bearing - previous_bearing + 180) % 360 - 180
            turn = 'တည့်တည့်ဆက်သွားပါ' if abs(change) < 30 else ('ညာဘက်ကွေ့ပါ' if change > 0 else 'ဘယ်ဘက်ကွေ့ပါ')
        label = name or 'အမည်မရှိလမ်း'
        if instructions and instructions[-1]['road'] == label and turn == 'တည့်တည့်ဆက်သွားပါ':
            instructions[-1]['metres'] += round(length)
        else:
            instructions.append({'road': label, 'direction': heading, 'turn': turn, 'metres': round(length)})
        previous_bearing = bearing
    raw_coords = [nodes[n] for n in path]
    # Include start station and incident endpoints if not identical
    route_coords = [list(start_point)] + [list(c) for c in raw_coords] + [list(end_point)]
    total_metres = round(metres + start_conn + end_conn)
    return {
        'coordinates': route_coords,
        'metres': round(metres),
        'total_metres': total_metres,
        'instructions': instructions,
        'start_connector_metres': round(start_conn),
        'end_connector_metres': round(end_conn),
        'attribution': '© OpenStreetMap contributors'
    }
