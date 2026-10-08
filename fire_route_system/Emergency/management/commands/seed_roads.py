from django.core.management.base import BaseCommand
from django.db import transaction
from DataAccess.models import FireStation
from Emergency.models import RoadNode, RoadEdge
from Emergency.routing import distance, project_point_to_segment

class Command(BaseCommand):
    help = 'Seeds a comprehensive, realistic road network graph for Mandalay connecting all stations and street corridors.'

    def handle(self, *args, **options):
        # East-West Streets (lat, name)
        ew_streets = [
            (22.0650, 'မြောက်ပိုင်း အဝေးပြေးလမ်း (North Highway)'),
            (22.0350, 'ပုသိမ်ကြီးလမ်း (Patheingyi Road)'),
            (22.0120, '၁၀ လမ်း (10th Street)'),
            (22.0040, '၁၂ လမ်း (12th Street)'),
            (22.0000, '၁၄ လမ်း (14th Street)'),
            (21.9960, '၁၆ လမ်း (16th Street)'),
            (21.9930, '၁၈ လမ်း (18th Street)'),
            (21.9905, '၁၉ လမ်း (19th Street)'),
            (21.9880, '၂၀ လမ်း (20th Street)'),
            (21.9860, '၂၁ လမ်း (21st Street)'),
            (21.9840, '၂၂ လမ်း (22nd Street)'),
            (21.9820, '၂၃ လမ်း (23rd Street)'),
            (21.9800, '၂၄ လမ်း (24th Street)'),
            (21.9780, '၂၅ လမ်း (25th Street)'),
            (21.9760, '၂၆ လမ်း / ဗိုလ်ချုပ်လမ်း (26th Bogyoke Road)'),
            (21.9740, '၂၇ လမ်း (27th Street)'),
            (21.9720, '၂၈ လမ်း (28th Street)'),
            (21.9700, '၂၉ လမ်း (29th Street)'),
            (21.9680, '၃၀ လမ်း (30th Street)'),
            (21.9660, '၃၁ လမ်း (31st Street)'),
            (21.9640, '၃၂ လမ်း (32nd Street)'),
            (21.9620, '၃၃ လမ်း (33rd Street)'),
            (21.9600, '၃၄ လမ်း (34th Street)'),
            (21.9580, '၃၅ လမ်း (35th Street)'),
            (21.9560, '၃၆ လမ်း (36th Street)'),
            (21.9540, '၃၇ လမ်း (37th Street)'),
            (21.9520, '၃၈ လမ်း (38th Street)'),
            (21.9500, '၃၉ လမ်း (39th Street)'),
            (21.9480, '၄၀ လမ်း (40th Street)'),
            (21.9460, '၄၁ လမ်း (41st Street)'),
            (21.9440, '၄၂ လမ်း (42nd Street)'),
            (21.9400, 'မနော်ဟရီလမ်း (Manawhari Road)'),
            (21.9330, 'သိပ္ပံလမ်း (Theikpan Road)'),
            (21.9250, 'ငုရွှေဝါလမ်း (Ngu Shwe Wah Road)'),
            (21.9180, 'မင်္ဂလာမန္တလေးလမ်း (Mingalar Mandalay Road)'),
            (21.9100, 'ချမ်းမြသာစည် လေဆိပ်လမ်း (Airport Road)'),
            (21.8950, 'အမရပူရလမ်းမကြီး (Amarapura Main Road)'),
            (21.8650, 'စစ်ကိုင်း-မန္တလေးလမ်း (Sagaing-Mandalay Road)'),
            (21.8400, 'စက်မှုဇုန် တောင်ပိုင်းလမ်း (Industrial South Road)'),
        ]

        # North-South Streets (lon, name)
        ns_streets = [
            (96.0600, 'ဧရာဝတီ ကမ်းနားလမ်း (Strand Road)'),
            (96.0660, '၈၉ လမ်း (89th Street)'),
            (96.0690, '၈၈ လမ်း (88th Street)'),
            (96.0720, '၈၇ လမ်း (87th Street)'),
            (96.0745, '၈၆ လမ်း (86th Street)'),
            (96.0770, '၈၅ လမ်း (85th Street)'),
            (96.0795, '၈၄ လမ်း (84th Street)'),
            (96.0820, '၈၃ လမ်း (83rd Street)'),
            (96.0840, '၈၂ လမ်း (82nd Street)'),
            (96.0860, '၈၁ လမ်း (81st Street)'),
            (96.0880, '၈၀ လမ်း (80th Street)'),
            (96.0905, '၇၉ လမ်း (79th Street)'),
            (96.0930, '၇၈ လမ်း (78th Street)'),
            (96.0955, '၇၇ လမ်း (77th Street)'),
            (96.0980, '၇၆ လမ်း (76th Street)'),
            (96.1005, '၇၅ လမ်း (75th Street)'),
            (96.1030, '၇၄ လမ်း (74th Street)'),
            (96.1055, '၇၃ လမ်း (73rd Street)'),
            (96.1080, '၇၂ လမ်း (72nd Street)'),
            (96.1105, '၇၁ လမ်း (71st Street)'),
            (96.1130, '၇၀ လမ်း (70th Street)'),
            (96.1180, '၆၈ လမ်း (68th Street)'),
            (96.1240, '၆၅ လမ်း (65th Street)'),
            (96.1300, '၆၂ လမ်း (62nd Street)'),
            (96.1380, '၅၈ လမ်း (58th Street)'),
            (96.1480, 'စက်မှုဇုန် အလယ်လမ်း (Industrial Central Avenue)'),
            (96.1600, 'အရှေ့မြို့ပတ်လမ်း (Eastern Ring Road)'),
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

            if station_nodes:
                RoadNode.objects.bulk_create([sn[1] for sn in station_nodes])
                reloaded_st = {n.osm_id: n for n in RoadNode.objects.filter(osm_id__gt=1000000 + len(ew_streets) * len(ns_streets))}

                for station, st_node in station_nodes:
                    actual_node = reloaded_st[st_node.osm_id]
                    # Find closest grid nodes to connect this station
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
