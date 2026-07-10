from .models import Dispatch
from .forms import DispatchForm
from django.shortcuts import render, redirect, get_object_or_404


def dispatch_list(request):
    dispatches = Dispatch.objects.all()
    return render(request, 'dispatch/list.html', {
        'dispatches': dispatches
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