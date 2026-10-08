from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from DataAccess.decorators import responder_required, dispatcher_required, admin_required
from .models import FireReport
from .forms import FireReportForm

@login_required(login_url='login')
def report_fire(request):
    """
    Emergency Fire Report intake workflow.
    Requires an authenticated user session. Unauthenticated users are redirected to login.
    The reporter's phone number is retrieved server-side from the authenticated user's profile.
    Client-side phone number submissions are neither requested nor trusted.
    If the user's phone number is missing, an informative Burmese message directs them
    to complete their profile before submitting.
    """
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")

    user = request.user
    user_phone = (getattr(user, 'phone_number', None) or '').strip()
    phone_missing = not bool(user_phone)

    if request.method == "POST":
        # Server-side validation: ensure verified phone number exists on user account
        if phone_missing:
            return render(request, 'report_form.html', {
                'error': 'မီးသတင်းပေးပို့ရန် သင့်အကောင့်တွင် ဆက်သွယ်ရန် ဖုန်းနံပါတ် ဖြည့်သွင်းထားရန် လိုအပ်ပါသည်။ ကျေးဇူးပြု၍ မိမိအကောင့် Profile တွင် ဖုန်းနံပါတ် အရင်ဖြည့်စွက်ပေးပါ။',
                'phone_missing': True,
                'user_phone': None,
                'latitude': request.POST.get('latitude'),
                'longitude': request.POST.get('longitude'),
                'address': request.POST.get('address', '').strip(),
            })

        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        addr = request.POST.get('address', '').strip()

        # Parse coordinates
        lat_val = float(lat) if (lat and lat.strip()) else None
        lng_val = float(lng) if (lng and lng.strip()) else None

        # Validation: Either GPS (lat & lng) OR address must be provided
        if not addr and (lat_val is None or lng_val is None):
            return render(request, 'report_form.html', {
                'error': 'တည်နေရာ GPS ကိုဩဒိနိတ် သို့မဟုတ် လိပ်စာ အသေးစိတ် ဖော်ပြချက် တစ်ခုခုကို မဖြစ်မနေ ဖြည့်သွင်းပေးရန် လိုအပ်ပါသည်။',
                'phone_missing': False,
                'user_phone': user_phone,
                'latitude': lat,
                'longitude': lng,
                'address': addr,
            })

        FireReport.objects.create(
            user_id=user.id,
            latitude=lat_val,
            longitude=lng_val,
            address=addr if addr else None,
            fire_scale=0,
            reporter_phone=user_phone,
            status='Pending'
        )
        return render(request, 'report_form.html', {
            'success': True,
            'user_phone': user_phone,
            'phone_missing': False,
        })

    return render(request, 'report_form.html', {
        'user_phone': user_phone,
        'phone_missing': phone_missing,
    })


@responder_required
def fire_report_list(request):
    from django.db.models import Q
    from django.utils import timezone
    import datetime

    # Read GET parameters
    query = request.GET.get('q', '').strip()
    date_str = request.GET.get('date', '').strip()
    status_filter = request.GET.get('status', '').strip()
    scale_filter = request.GET.get('scale', '').strip()

    # Base query excluding 'Pending'
    reports = FireReport.objects.exclude(status='Pending')

    # Apply date search or default 7-day window
    if date_str:
        parsed_date = None
        for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
            try:
                parsed_date = datetime.datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                pass
        if parsed_date:
            reports = reports.filter(reported_at__date=parsed_date)
    else:
        seven_days_ago = timezone.now() - datetime.timedelta(days=7)
        reports = reports.filter(reported_at__gte=seven_days_ago)

    # Filter dropdowns
    if status_filter:
        reports = reports.filter(status=status_filter)
    if scale_filter:
        reports = reports.filter(fire_scale=scale_filter)

    # Preserve search query
    if query:
        filters = Q(reporter_phone__icontains=query) | Q(status__icontains=query)
        if query.isdigit():
            filters |= Q(id=int(query))
        reports = reports.filter(filters)

    reports = reports.order_by('-reported_at')

    import json
    reports_json = json.dumps([
        {
            'id': r.id,
            'latitude': r.latitude,
            'longitude': r.longitude,
            'fire_scale': r.fire_scale,
            'status': r.status,
            'reporter_phone': r.reporter_phone or 'Anonymous',
            'reported_at': r.reported_at.strftime('%d-%m-%Y %I:%M %p'),
        }
        for r in reports
        if r.latitude is not None and r.longitude is not None
    ])

    from django.core.paginator import Paginator

    per_page_param = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page_param)
        if per_page not in [5, 10, 20, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(reports, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'fire_reports/incident_list.html', {
        'page_obj': page_obj,
        'reports': page_obj.object_list,
        'paginator': paginator,
        'per_page': per_page,
        'reports_json': reports_json,
        'query': query,
        'selected_date': date_str,
        'selected_status': status_filter,
        'selected_scale': scale_filter
    })


@dispatcher_required
def fire_report_create(request):
    form = FireReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fire report created successfully.")
        return redirect('fire_report_list')
    return render(request, 'fire_reports/form.html', {'form': form, 'title': 'Create Fire Report'})


@dispatcher_required
def fire_report_update(request, pk):
    report = get_object_or_404(FireReport, pk=pk)
    form = FireReportForm(request.POST or None, instance=report)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fire report updated successfully.")
        return redirect('fire_report_list')
    return render(request, 'fire_reports/form.html', {'form': form, 'title': 'Update Fire Report', 'report': report})


@admin_required
def fire_report_delete(request, pk):
    report = get_object_or_404(FireReport, pk=pk)
    if report.status != 'Resolved':
        messages.error(request, "Incident reports cannot be deleted unless they are resolved.")
        return redirect('fire_report_list')
    if request.method == "POST":
        try:
            report.delete()
            messages.success(request, "Fire report deleted successfully.")
        except Exception as e:
            messages.error(request, str(e))
        return redirect('fire_report_list')
    return render(request, 'fire_reports/delete.html', {'report': report})


@dispatcher_required
def triage_queue(request):
    from DataAccess.models import Tbl_Notification
    unread = Tbl_Notification.objects.filter(is_read=False).select_related('report').order_by('-created_at')
    return render(request, 'fire_reports/triage_queue.html', {
        'notifications': unread
    })


from django.views.decorators.http import require_POST
from django.utils import timezone

@require_POST
@dispatcher_required
def confirm_incident(request, notification_id):
    from DataAccess.models import Tbl_Notification
    notification = get_object_or_404(Tbl_Notification, pk=notification_id)
    notification.is_read = True
    notification.save()

    report = notification.report
    report.status = 'Confirmed'
    report.coordinates_confirmed = True
    report.save()

    messages.success(request, f"မီးသတင်း ID {report.id} အား အတည်ပြုပြီးပါပြီ။ Incident Management တွင် Fire Level သတ်မှတ်နိုင်ပါသည်။")
    return redirect('emergency:incident', pk=report.pk)


@require_POST
@dispatcher_required
def reject_incident(request, notification_id):
    from DataAccess.models import Tbl_Notification
    notification = get_object_or_404(Tbl_Notification, pk=notification_id)
    notification.is_read = True
    notification.save()

    report = notification.report
    report.status = 'False Alarm'
    report.closed_at = timezone.now()
    report.save()

    messages.warning(request, f"မီးသတင်း ID {report.id} အား သတင်းမှား / ပယ်ဖျက် (Fake/Rejected) အဖြစ် သတ်မှတ်ပြီးပါပြီ။ စေလွှတ်မှု မပြုလုပ်ပါ။")
    return redirect('triage_queue')
