from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect


class LegacyAccessMiddleware:
    """Keep legacy management endpoints from bypassing station-level permissions."""
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        path = request.path
        if path == '/map/': return redirect('emergency:map')
        if path == '/report/': return redirect('emergency:report')
        if path.startswith(('/create/', '/update/', '/delete/')):
            return redirect('emergency:list',kind='stations')
        if path in ['/', '/dashboard/'] and request.user.is_authenticated:
            return redirect('emergency:dashboard')
        protected = ('/api/', '/roles/', '/users/', '/dispatch', '/firestations', '/fire-stations', '/report/fire-reports/', '/dashboard/report-portal/', '/admin/')
        if path.startswith(protected):
            if not request.user.is_authenticated: return redirect('login')
            if not getattr(request.user, 'is_admin', False): return HttpResponseForbidden('စီမံခန့်ခွဲသူသာ အသုံးပြုနိုင်ပါသည်။')
            if request.method not in ['GET','HEAD','OPTIONS']:
                return HttpResponseForbidden('Demo console မှ လုပ်ဆောင်ပါ။')
        if path.startswith('/report/api/'):
            from .api import incidents, incident_detail
            if path.rstrip('/') == '/report/api/fire-reports': return incidents(request)
            try: return incident_detail(request, int(path.rstrip('/').split('/')[-1]))
            except ValueError: return JsonResponse({'error':'Not found'},status=404)
        return self.get_response(request)
