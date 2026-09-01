from django.shortcuts import render, redirect, get_object_or_404
from .models import FireStation

# ==========================
# READ (Display All)
# ==========================
def firestation_list(request):
    from django.db.models import Q
    query = request.GET.get('q', '').strip()

    if query:
        stations = FireStation.objects.filter(
            Q(name__icontains=query) |
            Q(contact_number__icontains=query) |
            Q(status__icontains=query)
        )
    else:
        stations = FireStation.objects.all()

    from django.core.paginator import Paginator
    stations = stations.order_by('station_id')

    per_page_param = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page_param)
        if per_page not in [5, 10, 20, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(stations, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "stations": page_obj.object_list,
        "paginator": paginator,
        "per_page": per_page,
        "query": query
    }

    return render(request, "firestation/list.html", context)


# ==========================
# CREATE
# ==========================
def firestation_create(request):

    if request.method == "POST":

        FireStation.objects.create(
            name=request.POST.get("name"),
            address=request.POST.get("address"),
            contact_number=request.POST.get("contact_number"),
            latitude=request.POST.get("latitude"),
            longitude=request.POST.get("longitude"),
            status=request.POST.get("status")
        )

        return redirect("firestation_list")

    return render(request, "firestation/create.html")


# ==========================
# UPDATE
# ==========================
def firestation_update(request, station_id):

    station = get_object_or_404(FireStation, pk=station_id)

    if request.method == "POST":

        station.name = request.POST.get("name")
        station.address = request.POST.get("address")
        station.contact_number = request.POST.get("contact_number")
        station.latitude = request.POST.get("latitude")
        station.longitude = request.POST.get("longitude")
        station.status = request.POST.get("status")

        station.save()

        return redirect("firestation_list")

    context = {
        "station": station
    }

    return render(request, "firestation/update.html", context)


# ==========================
# DELETE
# ==========================
def firestation_delete(request, station_id):

    station = get_object_or_404(FireStation, pk=station_id)

    if request.method == "POST":
        station.delete()
        return redirect("firestation_list")

    context = {
        "station": station
    }

    return render(request, "firestation/delete.html", context)
