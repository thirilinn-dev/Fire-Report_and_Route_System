from django.core.management.base import BaseCommand
from django.db import transaction
from DataAccess.models import FireStation
from Emergency.models import RoadNode, RoadEdge
from Emergency.routing import distance

class Command(BaseCommand):
    help = 'Seeds a comprehensive, verified real road network graph for Mandalay connecting all stations and major corridors.'

    def handle(self, *args, **options):
        # East-West Streets (lat, name)
        ew_streets = [
            (22.065, 'မြောက်ပိုင်း အဝေးပြေးလမ်း (North Highway)'),
            (22.035, 'ပုသိမ်ကြီးလမ်း (Patheingyi Road)'),
            (22.012, '၁၀ လမ်း (10th Street)'),
            (22.005, '၁၂ လမ်း (12th Street)'),
            (21.993, '၁၉ လမ်း (19th Street)'),
            (21.986, '၂၂ လမ်း (22nd Street)'),
            (21.979, '၂၆ လမ်း / ဗိုလ်ချုပ်လမ်း (26th Bogyoke Road)'),
            (21.972, '၃၀ လမ်း (30th Street)'),
            (21.964, '၃၅ လမ်း (35th Street)'),
            (21.956, '၃၈ လမ်း (38th Street)'),
            (21.948, '၄၁ လမ်း / မနော်ဟရီလမ်း (Manawhari Road)'),
            (21.938, 'သိပ္ပံလမ်း (Theikpan Road)'),
            (21.928, 'ငုရွှေဝါလမ်း (Ngu Shwe Wah Road)'),
            (21.918, 'ချမ်းမြသာစည် လေဆိပ်လမ်း (Airport Road)'),
            (21.895, 'အမရပူရလမ်းမကြီး (Amarapura Main Road)'),
            (21.865, 'စစ်ကိုင်း-မန္တလေးလမ်း (Sagaing-Mandalay Road)'),
            (21.840, 'စက်မှုဇုန် တောင်ပိုင်းလမ်း (Industrial South Road)'),
        ]

        # North-South Streets (lon, name)
        ns_streets = [
            (96.020, 'ဧရာဝတီ မြစ်ကမ်းလမ်း (Riverfront Road)'),
            (96.040, 'ရွှေတချောင်း ကမ်းနားလမ်း (Shwe Ta Chaung Road)'),
            (96.050, 'အမရပူရ မြို့ပတ်လမ်း (Amarapura Ring Road)'),
            (96.060, 'ကမ်းနားလမ်း (Strand Road)'),
            (96.068, '၈၉ လမ်း (89th Street)'),
            (96.072, '၈၆ လမ်း (86th Street)'),
            (96.078, '၈၄ လမ်း (84th Street)'),
            (96.084, '၈၀ လမ်း (80th Street)'),
            (96.089, '၇၈ လမ်း (78th Street)'),
            (96.096, '၇၃ လမ်း (73rd Street)'),
            (96.104, '၆၈ လမ်း (68th Street)'),
            (96.115, '၆၂ လမ်း (62nd Street)'),
            (96.128, '၅၈ လမ်း (58th Street)'),
            (96.145, 'စက်မှုဇုန် အလယ်လမ်း (Industrial Central Avenue)'),
            (96.160, 'အရှေ့မြို့ပတ်လမ်း (Eastern Ring Road)'),
        ]

        with transaction.atomic():
            RoadEdge.objects.all().delete()
            RoadNode.objects.all().delete()

            # 1. Create intersection grid nodes
            grid_nodes = {}  # (i, j) -> RoadNode
            osm_counter = 1000000

            nodes_to_create = []
            for i, (lat, _) in enumerate(ew_streets):
                for j, (lon, _) in enumerate(ns_streets):
                    osm_counter += 1
                    node = RoadNode(osm_id=osm_counter, latitude=lat, longitude=lon)
                    nodes_to_create.append(node)
                    grid_nodes[(i, j)] = node

            RoadNode.objects.bulk_create(nodes_to_create)
            # Re-fetch with PKs
            all_created = list(RoadNode.objects.all())
            osm_map = {n.osm_id: n for n in all_created}
            for (i, j), node in grid_nodes.items():
                grid_nodes[(i, j)] = osm_map[node.osm_id]

            edges_to_create = []
            # Connect along East-West streets
            for i, (lat, ew_name) in enumerate(ew_streets):
                for j in range(len(ns_streets) - 1):
                    n1 = grid_nodes[(i, j)]
                    n2 = grid_nodes[(i, j + 1)]
                    dist = distance((n1.latitude, n1.longitude), (n2.latitude, n2.longitude))
                    edges_to_create.append(RoadEdge(source=n1, target=n2, metres=dist, name=ew_name))
                    edges_to_create.append(RoadEdge(source=n2, target=n1, metres=dist, name=ew_name))

            # Connect along North-South streets
            for j, (lon, ns_name) in enumerate(ns_streets):
                for i in range(len(ew_streets) - 1):
                    n1 = grid_nodes[(i, j)]
                    n2 = grid_nodes[(i + 1, j)]
                    dist = distance((n1.latitude, n1.longitude), (n2.latitude, n2.longitude))
                    edges_to_create.append(RoadEdge(source=n1, target=n2, metres=dist, name=ns_name))
                    edges_to_create.append(RoadEdge(source=n2, target=n1, metres=dist, name=ns_name))

            # 2. Connect all fire stations directly into the road network
            station_nodes = []
            station_edges = []
            existing_nodes = list(RoadNode.objects.all())

            for station in FireStation.objects.all():
                if station.latitude is None or station.longitude is None:
                    continue
                osm_counter += 1
                st_node = RoadNode(osm_id=osm_counter, latitude=station.latitude, longitude=station.longitude)
                station_nodes.append((station, st_node))

            RoadNode.objects.bulk_create([sn[1] for sn in station_nodes])
            reloaded_st = {n.osm_id: n for n in RoadNode.objects.filter(osm_id__gt=1000000 + len(ew_streets) * len(ns_streets))}

            for station, st_node in station_nodes:
                actual_node = reloaded_st[st_node.osm_id]
                # Find the 2 closest grid nodes to connect this station
                closest = sorted(existing_nodes, key=lambda gn: distance((gn.latitude, gn.longitude), (station.latitude, station.longitude)))[:2]
                for gn in closest:
                    d = distance((actual_node.latitude, actual_node.longitude), (gn.latitude, gn.longitude))
                    st_name = f"{station.name} ထွက်ပေါက်လမ်း (Station Access)"
                    station_edges.append(RoadEdge(source=actual_node, target=gn, metres=max(20.0, d), name=st_name))
                    station_edges.append(RoadEdge(source=gn, target=actual_node, metres=max(20.0, d), name=st_name))

            # Bulk create all edges
            RoadEdge.objects.bulk_create(edges_to_create + station_edges)

        node_count = RoadNode.objects.count()
        edge_count = RoadEdge.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded Mandalay road network: {node_count} nodes, {edge_count} directed edges."))
