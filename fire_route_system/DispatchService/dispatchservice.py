from .models import Dispatch
from .forms import DispatchForm
from django.shortcuts import render, redirect, get_object_or_404

def dispatch_list(request):
    from django.core.paginator import Paginator
    dispatches = Dispatch.objects.all().order_by('-dispatched_at')

    per_page_param = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page_param)
        if per_page not in [5, 10, 20, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(dispatches, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'dispatch/list.html', {
        'page_obj': page_obj,
        'dispatches': page_obj.object_list,
        'paginator': paginator,
        'per_page': per_page
    })


def dispatch_create(request):
    form = DispatchForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('dispatch_list')

    return render(request, 'dispatch/form.html', {
        'form': form
    })


def dispatch_update(request, pk):
    dispatch = get_object_or_404(Dispatch, pk=pk)

    form = DispatchForm(request.POST or None, instance=dispatch)

    if form.is_valid():
        form.save()
        return redirect('dispatch_list')

    return render(request, 'dispatch/form.html', {
        'form': form
    })


def dispatch_delete(request, pk):
    dispatch = get_object_or_404(Dispatch, pk=pk)

    if request.method == "POST":
        dispatch.delete()
        return redirect('dispatch_list')

    return render(request, 'dispatch/delete.html', {
        'dispatch': dispatch
    })
